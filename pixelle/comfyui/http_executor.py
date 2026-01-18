# Copyright (C) 2025 AIDC-AI
# This project is licensed under the MIT License (SPDX-License-identifier: MIT).

import os
import json
import time
import uuid
import asyncio
import copy
from typing import Optional, Dict, Any

from pixelle.comfyui.base_executor import ComfyUIExecutor, COMFYUI_API_KEY, logger
from pixelle.comfyui.models import ExecuteResult


class HttpExecutor(ComfyUIExecutor):
    """HTTP executor for ComfyUI"""
    
    def __init__(self, base_url: str = None):
        super().__init__(base_url)

    async def _queue_prompt(self, workflow: Dict[str, Any], client_id: str, prompt_ext_params: Optional[Dict[str, Any]] = None) -> str:
        """Submit workflow to queue"""
        prompt_data = {
            "prompt": workflow,
            "client_id": client_id
        }
        
        # Update all parameters of prompt_data and prompt_ext_params
        if prompt_ext_params:
            prompt_data.update(prompt_ext_params)
        
        json_data = json.dumps(prompt_data)
        
        # Use aiohttp to send request
        prompt_url = f"{self.base_url}/prompt"
        async with self.get_comfyui_session() as session:
            async with session.post(
                    prompt_url, 
                    data=json_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise Exception(f"Submit workflow failed: [{response.status}] {response_text}")
                
                result = await response.json()
                prompt_id = result.get("prompt_id")
                if not prompt_id:
                    raise Exception(f"Get prompt_id failed: {result}")
                logger.info(f"Task submitted: {prompt_id}")
                return prompt_id

    async def _wait_for_results(self, prompt_id: str, client_id: str, timeout: Optional[int] = None, output_id_2_var: Optional[Dict[str, str]] = None) -> ExecuteResult:
        """Wait for workflow execution result (HTTP way)"""
        start_time = time.time()
        logger.info(f"HTTP way to wait for execution result, prompt_id: {prompt_id}, client_id: {client_id}")
        result = ExecuteResult(
            status="processing",
            prompt_id=prompt_id
        )

        # Get base URL
        base_url = self.base_url

        while True:
            # Check timeout
            if timeout is not None and timeout > 0:
                duration = time.time() - start_time
                if duration > timeout:
                    # logger.warning(f"Timeout: {duration} seconds") # Optional logging
                    result.status = "timeout"
                    result.duration = duration
                    return result

            # Use HTTP API to get history
            history_url = f"{self.base_url}/history/{prompt_id}"
            async with self.get_comfyui_session() as session:
                async with session.get(history_url) as response:
                    if response.status != 200:
                        await asyncio.sleep(1.0)
                        continue
                    history_data = await response.json()
                    if prompt_id not in history_data:
                        await asyncio.sleep(1.0)
                        continue
                    
                    prompt_history = history_data[prompt_id]
                    status = prompt_history.get("status")
                    if status and status.get("status_str") == "error":
                        result.status = "error"
                        messages = status.get("messages")
                        if messages:
                            errors = [
                                body.get("exception_message")
                                for type, body in messages
                                if type == "execution_error"
                            ]
                            error_message = "\n".join(errors)
                        else:
                            error_message = "Unknown error"
                        result.msg = error_message
                        result.duration = time.time() - start_time
                        return result
                    
                    if "outputs" in prompt_history:
                        result.outputs = prompt_history["outputs"]
                        result.status = "completed"

                        # Collect all images, videos, audios and texts outputs by file extension
                        output_id_2_images = {}
                        output_id_2_videos = {}
                        output_id_2_audios = {}
                        output_id_2_texts = {}
                        
                        for node_id, node_output in prompt_history["outputs"].items():
                            images, videos, audios = self._split_media_by_suffix(node_output, base_url)
                            if images:
                                output_id_2_images[node_id] = images
                            if videos:
                                output_id_2_videos[node_id] = videos
                            if audios:
                                output_id_2_audios[node_id] = audios
                            
                            # Collect text outputs
                            if "text" in node_output:
                                texts = node_output["text"]
                                if isinstance(texts, str):
                                    texts = [texts]
                                elif not isinstance(texts, list):
                                    texts = [str(texts)]
                                output_id_2_texts[node_id] = texts

                        # If there is a mapping, map by variable name
                        if output_id_2_images:
                            result.images_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_images)
                            result.images = self._extend_flat_list_from_dict(result.images_by_var)

                        if output_id_2_videos:
                            result.videos_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_videos)
                            result.videos = self._extend_flat_list_from_dict(result.videos_by_var)

                        if output_id_2_audios:
                            result.audios_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_audios)
                            result.audios = self._extend_flat_list_from_dict(result.audios_by_var)

                        # Process texts/texts_by_var
                        if output_id_2_texts:
                            result.texts_by_var = self._map_outputs_by_var(output_id_2_var or {}, output_id_2_texts)
                            result.texts = self._extend_flat_list_from_dict(result.texts_by_var)

                        # Set execution duration
                        result.duration = time.time() - start_time
                        return result
            await asyncio.sleep(1.0)


    async def _is_task_active(self, prompt_id: str) -> bool:
        """Prüft, ob ein Task noch existiert (Queue oder History)"""
        try:
            # 1. Prüfen ob ComfyUI überhaupt antwortet (Server Check)
            stats_url = f"{self.base_url}/system_stats"
            async with self.get_comfyui_session() as session:
                async with session.get(stats_url, timeout=2) as response:
                    if response.status != 200:
                        return False # Server ist wohl down

            # 2. Prüfen ob Task in der Queue ist (Running oder Pending)
            queue_url = f"{self.base_url}/queue"
            async with self.get_comfyui_session() as session:
                async with session.get(queue_url) as response:
                    if response.status == 200:
                        queue_data = await response.json()
                        for task in queue_data.get("queue_running", []):
                            if task[1] == prompt_id: return True
                        for task in queue_data.get("queue_pending", []):
                            if task[1] == prompt_id: return True

            # 3. Prüfen ob Task in History ist (schon fertig?)
            history_url = f"{self.base_url}/history/{prompt_id}"
            async with self.get_comfyui_session() as session:
                async with session.get(history_url) as response:
                    if response.status == 200:
                        hist = await response.json()
                        if prompt_id in hist: return True
            
            return False
        except Exception as e:
            return False


    def _get_formatted_logs(self, lines=20) -> str:
        """Liest die letzten Zeilen des Logs für die Anzeige"""
        try:
            from pixelle.logger import LOG_FILE
            if not os.path.exists(LOG_FILE):
                return ""
            
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:]
            
            log_content = "".join(last_lines).replace("<", "&lt;").replace(">", "&gt;")
            
            return f"""
\n\n
<details>
<summary>🛠️ <b>Server-Konsole anzeigen (Letzte {lines} Zeilen)</b></summary>
<pre><code>
{log_content}
</code></pre>
</details>
"""
        except Exception as e:
            return f"\n(Logs konnten nicht geladen werden: {e})"

    async def execute_workflow(self, workflow_file: str, params: Dict[str, Any] = None) -> ExecuteResult:
        """Execute workflow mit Auto-Retry bei Server-Absturz"""
        
        # --- LADE WORKFLOW DATEN ---
        if not os.path.exists(workflow_file):
            return ExecuteResult(status="error", msg=f"Workflow file missing")
        
        metadata = self.get_workflow_metadata(workflow_file)
        if not metadata: return ExecuteResult(status="error", msg="Invalid metadata")

        with open(workflow_file, 'r', encoding='utf-8') as f:
            original_workflow_data = json.load(f)

        # Parameter anwenden
        workflow_data = await self._apply_params_to_workflow(original_workflow_data, metadata, params or {})
        output_id_2_var = self._extract_output_nodes(metadata)
        
        # --- RETRY SCHLEIFE ---
        max_retries = 2
        current_try = 0
        
        while current_try < max_retries:
            current_try += 1
            try:
                # Seed neu würfeln bei jedem Versuch
                workflow_to_send, _ = self._randomize_seed_in_workflow(copy.deepcopy(workflow_data))
                
                client_id = str(uuid.uuid4())
                prompt_ext_params = {}
                if COMFYUI_API_KEY:
                    prompt_ext_params = {"extra_data": {"api_key_comfy_org": COMFYUI_API_KEY}}

                # 1. Versuch: Senden
                logger.info(f"Versuch {current_try}/{max_retries}: Sende Workflow an ComfyUI...")
                try:
                    prompt_id = await self._queue_prompt(workflow_to_send, client_id, prompt_ext_params)
                except Exception as e:
                    logger.warning(f"Konnte nicht senden (Server down?): {e}")
                    await asyncio.sleep(5)
                    continue 

                # 2. Warten mit intelligenter Überwachung
                start_wait = time.time()
                while True:
                    # Timeout Schutz (z.B. 20 Minuten)
                    if time.time() - start_wait > 10800:
                        raise Exception("Global Timeout")

                    # Prüfen: Ist der Task noch da?
                    is_active = await self._is_task_active(prompt_id)
                    
                    if not is_active:
                        # ALARM: Task ist weg -> Retry
                        logger.warning(f"⚠️ Task {prompt_id} ist verschwunden! Server-Neustart vermutet. Starte Retry...")
                        break 
                    
                    # Prüfen: Ist er fertig?
                    try:
                        # Ergebnis abrufen, bevor wir es prüfen
                        result = await self._wait_for_results(prompt_id, client_id, timeout=1, output_id_2_var=output_id_2_var)
                        
                        if result.status == "completed":
                            # 1. Dateien übertragen
                            final_result = await self.transfer_result_files(result)
                            
                            # 2. Logs holen und anhängen
                           # try:
                            #    logs_html = self._get_formatted_logs(lines=30)
                            #    if final_result.texts:
                            #        final_result.texts.append(logs_html)
                             #   else:
                             #       final_result.texts = [logs_html]
                          #  except Exception:
                             pass

                            # 3. Fertig
                            return final_result
                        
                        elif result.status == "error":
                            return result # Echter Fehler, kein Retry
                            
                    except Exception:
                        # Noch nicht fertig oder Timeout beim Check -> weitermachen
                        pass 
                    
                    await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Fehler im Versuch {current_try}: {e}")
                await asyncio.sleep(2)
        
        return ExecuteResult(status="error", msg="Max retries exceeded")
