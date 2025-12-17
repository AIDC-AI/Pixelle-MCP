[![MSeeP.ai Security Assessment Badge](https://mseep.net/pr/aidc-ai-pixelle-mcp-badge.png)](https://mseep.ai/app/aidc-ai-pixelle-mcp)

<h1 align="center">🎨 Pixelle MCP - Omnimodal Agent Framework</h1>

<p align="center"><b>English</b> | <a href="README_CN.md">中文</a></p>

<p align="center">✨ An AIGC solution based on the MCP protocol, supporting both local ComfyUI and cloud ComfyUI (RunningHub) modes, seamlessly converting workflows into MCP tools with zero code.</p>

![](docs/readme-1.png)

https://github.com/user-attachments/assets/65422cef-96f9-44fe-a82b-6a124674c417


## 📋 Recent Updates

- ✅ **2025-09-29**: Added RunningHub cloud ComfyUI support, enabling workflow execution without local GPU and ComfyUI environment
- ✅ **2025-09-03**: Architecture refactoring from three services to unified application; added CLI tool support; published to [PyPI](https://pypi.org/project/pixelle/)
- ✅ **2025-08-12**: Integrated the LiteLLM framework, adding multi-model support for Gemini, DeepSeek, Claude, Qwen, and more


## 🚀 Features

- ✅ 🔄 **Full-modal Support**: Supports TISV (Text, Image, Sound/Speech, Video) full-modal conversion and generation
- ✅ 🚀 **Dual Execution Modes**: Local ComfyUI self-hosted environment + RunningHub cloud ComfyUI service, users can flexibly choose based on their needs
- ✅ 🧩 **ComfyUI Ecosystem**: Built on [ComfyUI](https://github.com/comfyanonymous/ComfyUI), inheriting all capabilities from the open ComfyUI ecosystem
- ✅ 🔧 **Zero-code Development**: Defines and implements the Workflow-as-MCP Tool solution, enabling zero-code development and dynamic addition of new MCP Tools
- ✅ 🗄️ **MCP Server**: Based on the [MCP](https://modelcontextprotocol.io/introduction) protocol, supporting integration with any MCP client (including but not limited to Cursor, Claude Desktop, etc.)
- ✅ 🌐 **Web Interface**: Developed based on the [Chainlit](https://github.com/Chainlit/chainlit) framework, inheriting Chainlit's UI controls and supporting integration with more MCP Servers
- ✅ 📦 **One-click Deployment**: Supports PyPI installation, CLI commands, Docker and other deployment methods, ready to use out of the box
- ✅ ⚙️ **Simplified Configuration**: Uses environment variable configuration scheme, simple and intuitive configuration
- ✅ 🤖 **Multi-LLM Support**: Supports multiple mainstream LLMs, including OpenAI, Ollama, Gemini, DeepSeek, Claude, Qwen, and more


## 📁 Project Architecture

Pixelle MCP adopts a **unified architecture design**, integrating MCP server, web interface, and file services into one application, providing:

- 🌐 **Web Interface**: Chainlit-based chat interface supporting multimodal interaction
- 🔌 **MCP Endpoint**: For external MCP clients (such as Cursor, Claude Desktop) to connect
- 📁 **File Service**: Handles file upload, download, and storage
- 🛠️ **Workflow Engine**: Supports both local ComfyUI and cloud ComfyUI (RunningHub) workflows, automatically converts workflows into MCP tools

![](docs/%20mcp_structure.png)

<div id="tutorial-start" />

## 🏃‍♂️ Quick Start

Choose the deployment method that best suits your needs, from simple to complex:

### 🎯 Method 1: One-click Experience

> 💡 **Zero configuration startup, perfect for quick experience and testing**

#### 🚀 Temporary Run

```bash
# First you need to install the uv environment
# Start with one command, no system installation required
uvx pixelle@latest
```

📚 **[View uvx CLI Reference →](docs/CLI.md#uvx-method)**

#### 📦 Persistent Installation

```bash
# Here you need to install it in the python3.11 environment
# Install to system
pip install -U pixelle

# Start service
pixelle
```

📚 **[View pip CLI Reference →](docs/CLI.md#pip-install-method)**

After startup, it will automatically enter the **configuration wizard** to guide you through execution engine selection (ComfyUI/RunningHub) and LLM configuration.

### 🛠️ Method 2: Local Development Deployment

> 💡 **Supports custom workflows and secondary development**

#### 📥 1. Get Source Code

```bash
git clone https://github.com/AIDC-AI/Pixelle-MCP.git
cd Pixelle-MCP
```

#### 🚀 2. Start Service

```bash
# Interactive mode (recommended)
uv run pixelle
```

📚 **[View Complete CLI Reference →](docs/CLI.md#uv-run-method)**

#### 🔧 3. Add Custom Workflows (Optional)

```bash
# Copy example workflows to data directory (run this in your desired project directory)
cp -r workflows/* ./data/custom_workflows/
```

**⚠️ Important**: Make sure to test workflows in ComfyUI first to ensure they run properly, otherwise execution will fail.

### 🐳 Method 3: Docker Deployment

> 💡 **Suitable for production environments and containerized deployment**

#### 📋 1. Prepare Configuration

```bash
git clone https://github.com/AIDC-AI/Pixelle-MCP.git
cd Pixelle-MCP

# Create environment configuration file
cp .env.example .env
# Edit .env file to configure your ComfyUI address and LLM settings
```

#### 🚀 2. Start Container

```bash
# Start all services in background
docker compose up -d

# View logs
docker compose logs -f
```

### 🌐 Access Services

Regardless of which method you use, after startup you can access via:

- **🌐 Web Interface**: http://localhost:9004  
  *Default username and password are both `dev`, can be modified after startup*
- **🔌 MCP Endpoint**: http://localhost:9004/pixelle/mcp  
  *For MCP clients like Cursor, Claude Desktop to connect*

**💡 Port Configuration**: Default port is 9004, can be customized via environment variable `PORT=your_port`.

### ⚙️ Initial Configuration

On first startup, the system will automatically detect configuration status:

1. **🚀 Execution Engine Selection**: Choose between local ComfyUI or RunningHub cloud service
2. **🤖 LLM Configuration**: Configure at least one LLM provider (OpenAI, Ollama, etc.)
3. **📁 Workflow Directory**: System will automatically create necessary directory structure

### 🌐 RunningHub Cloud Mode Advantages
- ✅ **Zero Hardware Requirements**: No need for local GPU or high-performance hardware
- ✅ **No Environment Setup**: No need to install and configure ComfyUI locally
- ✅ **Ready to Use**: Register and get API key to start immediately
- ✅ **Stable Performance**: Professional cloud infrastructure ensures stable execution
- ✅ **Auto Scaling**: Automatically handles concurrent requests and resource allocation

### 🏠 Local ComfyUI Mode Advantages
- ✅ **Full Control**: Complete control over execution environment and model versions
- ✅ **Privacy Protection**: All data processing happens locally, ensuring data privacy
- ✅ **Custom Models**: Support for custom models and nodes not available in cloud
- ✅ **No Network Dependency**: Can work offline without internet connection
- ✅ **Cost Control**: No cloud service fees for high-frequency usage

**🆘 Need Help?** Join community groups for support (see Community section below)

## 🛠️ Add Your Own MCP Tool

⚡ One workflow = One MCP Tool, supports two addition methods:

📋 **Method 1: Local ComfyUI Workflow** - Export API format workflow files
📋 **Method 2: RunningHub Workflow ID** - Use cloud workflow IDs directly

![](docs/workflow_to_mcp_tool.png)

### 🎯 1. Add the Simplest MCP Tool

* 📝 Build a workflow in ComfyUI for image Gaussian blur ([Get it here](docs/i_blur_ui.json)), then set the `LoadImage` node's title to `$image.image!` as shown below:
![](docs/easy-workflow.png)

* 📤 Export it as an API format file and rename it to `i_blur.json`. You can export it yourself or use our pre-exported version ([Get it here](docs/i_blur.json))

* 📋 Copy the exported API workflow file (must be API format), input it on the web page, and let the LLM add this Tool

  ![](docs/ready_to_send_en.png)

* ✨ After sending, the LLM will automatically convert this workflow into an MCP Tool

  ![](docs/added_mcp_en.png)

* 🎨 Now, refresh the page and send any image to perform Gaussian blur processing via LLM

  ![](docs/use_mcp_tool_en.png)

### 🔌 2. Add a Complex MCP Tool

The steps are the same as above, only the workflow part differs (Download workflow: [UI format](docs/t2i_by_flux_turbo_ui.json) and [API format](docs/t2i_by_flux_turbo.json))

> **Note:** When using RunningHub, you only need to input the corresponding workflow ID, no need to download and upload workflow files.

![](docs/t2i_by_flux_turbo.png)


## 🔧 ComfyUI Workflow Custom Specification

### 🎨 Workflow Format
The system supports ComfyUI workflows. Just design your workflow in the canvas and export it as API format. Use special syntax in node titles to define parameters and outputs.

### 📝 Parameter Definition Specification

In the ComfyUI canvas, double-click the node title to edit, and use the following DSL syntax to define parameters:

```
$<param_name>.[~]<field_name>[!][:<description>]
```

#### 🔍 Syntax Explanation:
- `param_name`: The parameter name for the generated MCP tool function
- `~`: Optional, indicates URL parameter upload processing, returns relative path
- `field_name`: The corresponding input field in the node
- `!`: Indicates this parameter is required
- `description`: Description of the parameter

#### 💡 Example:

**Required parameter example:**

- Set LoadImage node title to: `$image.image!:Input image URL`
- Meaning: Creates a required parameter named `image`, mapped to the node's `image` field

**URL upload processing example:**

- Set any node title to: `$image.~image!:Input image URL`
- Meaning: Creates a required parameter named `image`, system will automatically download URL and upload to ComfyUI, returns relative path

> 📝 Note: `LoadImage`, `VHS_LoadAudioUpload`, `VHS_LoadVideo` and other nodes have built-in functionality, no need to add `~` marker


### 🎯 Type Inference Rules

The system automatically infers parameter types based on the current value of the node field:
- 🔢 `int`: Integer values (e.g. 512, 1024)
- 📊 `float`: Floating-point values (e.g. 1.5, 3.14)
- ✅ `bool`: Boolean values (e.g. true, false)
- 📝 `str`: String values (default type)

### 📤 Output Definition Specification

#### 🤖 Method 1: Auto-detect Output Nodes
The system will automatically detect the following common output nodes:
- 🖼️ `SaveImage` - Image save node
- 🎬 `SaveVideo` - Video save node
- 🔊 `SaveAudio` - Audio save node
- 📹 `VHS_SaveVideo` - VHS video save node
- 🎵 `VHS_SaveAudio` - VHS audio save node

#### 🎯 Method 2: Manual Output Marking
> Usually used for multiple outputs
Use `$output.var_name` in any node title to mark output:
- Set node title to: `$output.result`
- The system will use this node's output as the tool's return value


### 📄 Tool Description Configuration (Optional)

You can add a node titled `MCP` in the workflow to provide a tool description:

1. Add a `String (Multiline)` or similar text node (must have a single string property, and the node field should be one of: value, text, string)
2. Set the node title to: `MCP`
3. Enter a detailed tool description in the value field


### ⚠️ Important Notes

1. **🔒 Parameter Validation**: Optional parameters (without !) must have default values set in the node
2. **🔗 Node Connections**: Fields already connected to other nodes will not be parsed as parameters
3. **🏷️ Tool Naming**: Exported file name will be used as the tool name, use meaningful English names
4. **📋 Detailed Descriptions**: Provide detailed parameter descriptions for better user experience
5. **🎯 Export Format**: Must export as API format, do not export as UI format

<div id="tutorial-end" />
 
## 💬 Community

Scan the QR codes below to join our communities for latest updates and technical support:

|                      Discord Community                       |                         WeChat Group                         |
| :----------------------------------------------------------: | :----------------------------------------------------------: |
| <img src="docs/discord.png" alt="Discord Community" width="250" /> | <img src="docs/wechat.png" alt="WeChat Group" width="250" /> |

## 🤝 How to Contribute

We welcome all forms of contribution! Whether you're a developer, designer, or user, you can participate in the project in the following ways:

### 🐛 Report Issues
* 📋 Submit bug reports on the [Issues](https://github.com/AIDC-AI/Pixelle-MCP/issues) page
* 🔍 Please search for similar issues before submitting
* 📝 Describe the reproduction steps and environment in detail

### 💡 Feature Suggestions
* 🚀 Submit feature requests in [Issues](https://github.com/AIDC-AI/Pixelle-MCP/issues)
* 💭 Describe the feature you want and its use case
* 🎯 Explain how it improves user experience

### 🔧 Code Contributions

#### 📋 Contribution Process
1. 🍴 Fork this repo to your GitHub account
2. 🌿 Create a feature branch: `git checkout -b feature/your-feature-name`
3. 💻 Develop and add corresponding tests
4. 📝 Commit changes: `git commit -m "feat: add your feature"`
5. 📤 Push to your repo: `git push origin feature/your-feature-name`
6. 🔄 Create a Pull Request to the main repo

#### 🎨 Code Style
* 🐍 Python code follows [PEP 8](https://pep8.org/) style guide
* 📖 Add appropriate documentation and comments for new features

### 🧩 Contribute Workflows
* 📦 Share your ComfyUI workflows with the community
* 🛠️ Submit tested workflow files
* 📚 Add usage instructions and examples for workflows

## 🙏 Acknowledgements

❤️ Sincere thanks to the following organizations, projects, and teams for supporting the development and implementation of this project.

* 🧩 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
* 💬 [Chainlit](https://github.com/Chainlit/chainlit)

* 🔌 [MCP](https://modelcontextprotocol.io/introduction)
* 🎬 [WanVideo](https://github.com/Wan-Video/Wan2.1)
* ⚡ [Flux](https://github.com/black-forest-labs/flux)
* 🤖 [LiteLLM](https://github.com/BerriAI/litellm)

## License
This project is released under the MIT License ([LICENSE](LICENSE), SPDX-License-identifier: MIT).

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=AIDC-AI/Pixelle-MCP&type=Date)](https://star-history.com/#AIDC-AI/Pixelle-MCP&Date)
