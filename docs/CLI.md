# 🎛️ Pixelle CLI Complete Command Reference

This document provides detailed information about all Pixelle MCP CLI commands and options.

## 📋 Table of Contents

- [Basic Usage](#basic-usage)
- [Service Management Commands](#service-management-commands)
- [Configuration Management Commands](#configuration-management-commands)
- [Information Commands](#information-commands)
- [Interactive Mode](#interactive-mode)
- [Advanced Options](#advanced-options)

## 🚀 Basic Usage

### Installation Methods & Invocation

#### pip install Method
```bash
# Install
pip install -U pixelle

# Use
pixelle [command] [options]
```

#### uvx Method
```bash
# Use directly without installation
uvx pixelle@latest [command] [options]
```

#### uv run Method
```bash
# Use in project directory
uv run pixelle [command] [options]
```

### Default Behavior
```bash
# Enter interactive mode when no parameters
pixelle
uvx pixelle@latest
uv run pixelle
```

## 🔧 Service Management Commands

### `start` - Start Service
```bash
pixelle start [options]
```

**Options:**
- `--daemon, -d`: Run in background daemon mode
- `--force, -f`: Force start (terminate conflicting processes)

**Examples:**
```bash
# Start in foreground
pixelle start

# Start in background
pixelle start --daemon
pixelle start -d            # Short form

# Force start (if port is occupied)
pixelle start --force
pixelle start -f            # Short form

# Background force start
pixelle start --daemon --force
pixelle start -d -f         # Short form
pixelle start -df           # Combined short form
```

### `stop` - Stop Service
```bash
pixelle stop
```

Stops all Pixelle MCP related processes.

### `status` - Check Status
```bash
pixelle status
```

Displays:
- Service running status
- Process information
- Port usage
- Configuration status

## 📄 Log Management

### `logs` - View Logs
```bash
pixelle logs [options]
```

**Options:**
- `--follow, -f`: Follow log output in real-time
- `--lines N, -n N`: Show last N lines (default: 50)

**Examples:**
```bash
# View last 50 lines
pixelle logs

# View last 100 lines
pixelle logs --lines 100
pixelle logs -n 100         # Short form

# Follow logs in real-time
pixelle logs --follow
pixelle logs -f             # Short form

# Follow last 200 lines in real-time
pixelle logs --follow --lines 200
pixelle logs -f -n 200      # Short form
pixelle logs -fn 200        # Combined short form
```

## ⚙️ Configuration Management Commands

### `init` - Initialize Configuration
```bash
pixelle init
```

Runs configuration wizard to set up:
- ComfyUI connection
- LLM providers
- Service configuration

### `edit` - Edit Configuration
```bash
pixelle edit
```

Provides configuration editing options:
- Direct configuration file editing
- Wizard-based reconfiguration of specific parts

## 📊 Information Commands

### `workflow` - Workflow Information
```bash
pixelle workflow
```

Displays:
- Loaded workflows
- Available MCP tools
- Workflow file paths
- Tool statistics

### `dev` - Development Information
```bash
pixelle dev
```

Shows detailed system information:
- System environment
- Dependency versions
- Detailed service status
- Debug information

## 🎯 Interactive Mode

### `interactive` - Explicitly Enter Interactive Mode
```bash
pixelle interactive
```

Menu options in interactive mode:

- 🚀 **[start]** Start Pixelle MCP service
- 🔄 **[init]** Initialize/reconfigure Pixelle MCP
- 📝 **[edit]** Edit configuration files
- 🔧 **[workflow]** View workflow information and loaded tools
- 🐛 **[dev]** Development mode and detailed system status
- ❓ **[help]** Show help information
- ❌ **Exit** Exit the program

## 🛠️ Advanced Options

### Global Options
```bash
pixelle --help    # Show help information
pixelle -h        # Short form
```


## 📝 Usage Tips

### 1. Quick Start Process
```bash
# First time use
pixelle            # Enter interactive mode, complete configuration
# Select [init] to complete initialization
# Select [start] to start service

# Subsequent use
pixelle start      # Start directly
```

### 2. Debugging Issues
```bash
# View detailed status
pixelle status

# View development information
pixelle dev

# View real-time logs
pixelle logs --follow
pixelle logs -f             # Short form
```

### 3. Configuration Management
```bash
# Reconfigure
pixelle init

# Edit specific configuration
pixelle edit
```

### 4. Workflow Management
```bash
# View loaded workflows
pixelle workflow

# View workflow statistics
pixelle status
```

## ❓ Frequently Asked Questions

### Q: How to reset all configuration?
```bash
# Re-run initialization wizard
pixelle init
```

### Q: What to do if service fails to start?
```bash
# Check detailed status
pixelle status

# Force start
pixelle start --force
pixelle start -f            # Short form

# View error logs
pixelle logs
```

### Q: How to update workflows?
```bash
# Restart service to automatically reload
pixelle stop
pixelle start

# Or check workflow status
pixelle workflow
```

### Q: How to see all available commands?
```bash
pixelle --help
pixelle -h              # Short form
```

## 🔗 Related Links

- [Project Homepage](../README.md)
- [Workflow Development Guide](../README.md#comfyui-workflow-custom-specification)
- [Issue Reporting](https://github.com/AIDC-AI/Pixelle-MCP/issues)
