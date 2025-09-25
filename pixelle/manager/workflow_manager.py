# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

from datetime import datetime
import os
import time
import re
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import Field
from pixelle.logger import logger
from pixelle.mcp_core import mcp
from pixelle.utils.os_util import get_data_path
from pixelle.comfyui.workflow_parser import WorkflowParser, WorkflowMetadata
from pixelle.comfyui.facade import execute_workflow
from pixelle.utils.runninghub_util import is_runninghub_workflow, fetch_runninghub_workflow_metadata

CUSTOM_WORKFLOW_DIR = get_data_path("custom_workflows")
os.makedirs(CUSTOM_WORKFLOW_DIR, exist_ok=True)

class WorkflowManager:
    """Workflow manager, support dynamic loading and hot update"""
    
    def __init__(self, workflows_dir: str = CUSTOM_WORKFLOW_DIR):
        self.workflows_dir = Path(workflows_dir)
        self.loaded_workflows = {}

    
    def parse_workflow_metadata(self, workflow_path: Path, tool_name: str = None) -> Optional[WorkflowMetadata]:
        """Parse workflow metadata using new workflow parser"""
        try:
            # Check if this is a RunningHub workflow file
            if is_runninghub_workflow(workflow_path):
                # Import asyncio for running async function
                import asyncio

                tool_name = tool_name or workflow_path.stem
                # Run the async function
                try:
                    loop = asyncio.get_running_loop()
                    # If we're already in an async context, create a new task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, fetch_runninghub_workflow_metadata(workflow_path, tool_name))
                        return future.result()
                except RuntimeError:
                    # No running loop, we can use asyncio.run
                    return asyncio.run(fetch_runninghub_workflow_metadata(workflow_path, tool_name))
            else:
                # Standard ComfyUI workflow
                parser = WorkflowParser()
                metadata = parser.parse_workflow_file(str(workflow_path), tool_name)
                return metadata
        except Exception as e:
            logger.error(f"Failed to parse workflow metadata for {workflow_path}: {e}")
            return None
    
    
    def _generate_params_str(self, params: Dict[str, Any]) -> str:
        """Generate function parameter string"""
        # Separate required parameters and optional parameters, ensure parameter order is correct
        required_params = []
        optional_params = []
        
        for param_name, param in params.items():
            # Directly use user-provided description
            description = param.description or ''
            
            # Generate Field parameter list
            field_args = [f"description={repr(description)}"]
            if param.default is not None:
                field_args.append(f"default={repr(param.default)}")
            
            # Generate complete parameter definition
            param_str = f"{param_name}: {param.type} = Field({', '.join(field_args)})"
            
            # Classify parameters based on whether they have default values
            if param.default is not None:
                optional_params.append(param_str)
            else:
                required_params.append(param_str)
        
        # Required parameters first, optional parameters last
        return ", ".join(required_params + optional_params)
    
    def _generate_workflow_function(self, title: str, params_str: str) -> tuple[str, str]:
        """Generate the workflow execution function code
        
        Returns:
            tuple: (function_code, workflow_path) - Function code and workflow path
        """
        final_workflow_path = os.path.join(CUSTOM_WORKFLOW_DIR, f"{title}.json")
        
        template = '''async def {title}({params_str}):
    try:
        # Get the passed parameters (excluding special parameters)
        params = {{k: v for k, v in locals().items() if not k.startswith('_')}}
        
        # Execute the workflow - workflow_path is retrieved from the external environment
        result = await execute_workflow(WORKFLOW_PATH, params)
        
        # Convert the result to a format friendly to LLM
        if result.status == "completed":
            return result.to_llm_result()
        else:
            return "Workflow execution failed: " + str(result.msg or result.status)
            
    except Exception as e:
        logger.error("Workflow execution failed {title_safe}: " + str(e), exc_info=True)
        return "Workflow execution exception: " + str(e)
'''

        function_code = template.format(
            title=title,
            params_str=params_str,
            title_safe=repr(title)
        )
        
        return function_code, final_workflow_path


    def _register_workflow(self, title: str, workflow_handler, metadata: WorkflowMetadata) -> None:
        """Register and record workflow"""
        
        # Register as MCP tool
        mcp.tool(workflow_handler)
        
        # Record workflow information
        self.loaded_workflows[title] = {
            "function": workflow_handler,
            "metadata": metadata.model_dump(),
            "loaded_at": datetime.now()
        }
        
        logger.info(f"Successfully loaded workflow: {title}")
    
    def _save_workflow_if_needed(self, workflow_path: Path, title: str):
        """If needed, save workflow file to workflow directory"""
        target_workflow_path = self.workflows_dir / f"{title}.json"
        try:
            # Ensure workflow directory exists
            self.workflows_dir.mkdir(parents=True, exist_ok=True)

            # Skip if source and target file are the same
            if os.path.abspath(str(workflow_path)) == os.path.abspath(str(target_workflow_path)):
                logger.debug(f"Workflow file already exists and path is the same, no need to copy: {target_workflow_path}")
                return

            # Copy workflow file to workflow directory
            import shutil
            shutil.copy2(workflow_path, target_workflow_path)
            logger.info(f"Workflow file saved to: {target_workflow_path}")
        except Exception as e:
            logger.warning(f"Failed to save workflow file: {e}")
        

    def load_workflow(self, workflow_path: Path | str, tool_name: str = None) -> Dict:
        """Load single workflow
        
        Args:
            workflow_path: Workflow file path
            tool_name: Tool name, priority higher than workflow file name
            save_workflow_if_not_exists: Whether to save workflow file to workflow directory (if target file does not exist)
        """
        try:
            if isinstance(workflow_path, str):
                workflow_path = Path(workflow_path)
            
            # Check if file exists
            if not workflow_path.exists():
                logger.error(f"Workflow file does not exist: {workflow_path}")
                return {
                    "success": False,
                    "error": f"Workflow file does not exist: {workflow_path}"
                }
            
            # Use new parser to parse workflow metadata
            metadata = self.parse_workflow_metadata(workflow_path, tool_name)
            if not metadata:
                logger.error(f"Cannot parse workflow metadata: {workflow_path}")
                return {
                    "success": False,
                    "error": f"Cannot parse workflow metadata: {workflow_path}"
                }

            title = metadata.title
            
            
            # Verify title format
            if not re.match(r'^[a-zA-Z0-9_\.-]+$', title):
                logger.error(f"Tool name '{title}' format is invalid. Only letters, digits, underscores, dots, and hyphens are allowed.")
                return {
                    "success": False,
                    "error": f"Tool name '{title}' format is invalid. Only letters, digits, underscores, dots, and hyphens are allowed."
                }
            
            # Generate parameter string
            params_str = self._generate_params_str(metadata.params)
            
            # Create tool handler function
            exec_locals = {}
            
            # Generate workflow execution function
            func_def, target_workflow_path = self._generate_workflow_function(title, params_str)
            # Execute function definition, pass workflow path as variable to execution environment
            exec(func_def, {
                "metadata": metadata, 
                "logger": logger, 
                "Field": Field,
                "execute_workflow": execute_workflow,
                "WORKFLOW_PATH": target_workflow_path,
            }, exec_locals)
            
            dynamic_function = exec_locals[title]
            if metadata.description:
                dynamic_function.__doc__ = metadata.description
            
            # Register and record workflow
            self._register_workflow(title, dynamic_function, metadata)
            
            # Save workflow file to workflow directory
            self._save_workflow_if_needed(workflow_path, title)
            
            logger.debug(f"Workflow '{title}' successfully loaded as MCP tool")
            return {
                "success": True,
                "workflow": title,
                "metadata": metadata.model_dump(),
                "message": f"Workflow '{title}' successfully loaded as MCP tool"
            }
            
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_path}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to load workflow: {str(e)}"
            }
            
    
    def unload_workflow(self, workflow_name: str) -> Dict:
        """Unload workflow"""
        if workflow_name not in self.loaded_workflows:
            return {
                "success": False,
                "error": f"Workflow '{workflow_name}' does not exist or not loaded"
            }
        
        try:
            # Remove from MCP server
            mcp.remove_tool(workflow_name)
            
            # Delete workflow file
            workflow_path = os.path.join(CUSTOM_WORKFLOW_DIR, f"{workflow_name}.json")
            if os.path.exists(workflow_path):
                os.remove(workflow_path)
            
            # Delete from record
            del self.loaded_workflows[workflow_name]
            
            logger.info(f"Successfully unloaded workflow: {workflow_name}")
            
            return {
                "success": True,
                "workflow": workflow_name,
                "message": f"Workflow '{workflow_name}' successfully unloaded"
            }
                
        except Exception as e:
            logger.error(f"Failed to unload workflow {workflow_name}: {e}")
            return {
                "success": False,
                "error": f"Failed to unload workflow: {str(e)}"
            }
    
    
    def load_all_workflows(self) -> Dict:
        """Load all workflows"""
        results = {
            "success": [],
            "failed": []
        }
        
        # Ensure directory exists
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all JSON files
        for json_file in self.workflows_dir.glob("*.json"):
            result = self.load_workflow(json_file)
            if result["success"]:
                results["success"].append(result["workflow"])
            else:
                results["failed"].append({
                    "file": json_file.name,
                    "error": result["error"]
                })
        
        return results
    
    def get_workflow_status(self) -> Dict:
        """Get all workflow status"""
        return {
            "total_loaded": len(self.loaded_workflows),
            "workflows": {
                name: {
                    "metadata": info["metadata"],
                    "loaded_at": info["loaded_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(info["loaded_at"], datetime) else str(info["loaded_at"])
                }
                for name, info in self.loaded_workflows.items()
            }
        }
    
    def reload_all_workflows(self) -> Dict:
        """Manually reload all workflows"""
        logger.info("Start manually reloading all workflows")
        
        # Clear all loaded workflows
        for workflow_name in list(self.loaded_workflows.keys()):
            try:
                mcp.remove_tool(workflow_name)
            except:
                pass  # Ignore remove failure
        
        self.loaded_workflows.clear()
        
        # Reload all workflows
        results = self.load_all_workflows()
        
        logger.info(f"Manually reloading completed: success {len(results['success'])}, failed {len(results['failed'])}")
        
        return {
            "success": True,
            "message": f"Manually reloading completed: success {len(results['success'])}, failed {len(results['failed'])}",
            "results": results
        }
    




# Create workflow manager instance
workflow_manager = WorkflowManager()

# Initial load all workflows
load_results = workflow_manager.load_all_workflows()
logger.info(f"Initial workflow load results: {load_results}")

# Export module-level variables and instance
__all__ = ['workflow_manager', 'WorkflowManager', 'CUSTOM_WORKFLOW_DIR'] 