# 🎛️ Pixelle CLI 完整命令手册

本文档详细介绍 Pixelle MCP 的所有 CLI 命令和参数。

## 📋 目录

- [基础使用](#基础使用)
- [服务管理命令](#服务管理命令)
- [配置管理命令](#配置管理命令)
- [信息查看命令](#信息查看命令)
- [交互模式](#交互模式)
- [高级选项](#高级选项)

## 🚀 基础使用

### 安装方式与调用方法

#### pip install 方式
```bash
# 安装
pip install -U pixelle

# 使用
pixelle [命令] [选项]
```

#### uvx 方式
```bash
# 直接使用，无需安装
uvx pixelle@latest [命令] [选项]
```

#### uv run 方式
```bash
# 在项目目录下使用
uv run pixelle [命令] [选项]
```

### 默认行为
```bash
# 无参数时自动进入交互模式
pixelle
uvx pixelle@latest
uv run pixelle
```

## 🔧 服务管理命令

### `start` - 启动服务
```bash
pixelle start [选项]
```

**选项：**
- `--daemon, -d`：后台运行模式
- `--force, -f`：强制启动（终止冲突进程）

**示例：**
```bash
# 前台启动
pixelle start

# 后台启动
pixelle start --daemon
pixelle start -d            # 简写

# 强制启动（如果端口被占用）
pixelle start --force
pixelle start -f            # 简写

# 后台强制启动
pixelle start --daemon --force
pixelle start -d -f         # 简写
pixelle start -df           # 简写组合
```

### `stop` - 停止服务
```bash
pixelle stop
```

停止所有 Pixelle MCP 相关进程。

### `status` - 查看状态
```bash
pixelle status
```

显示：
- 服务运行状态
- 进程信息
- 端口占用情况
- 配置状态

## 📄 日志管理

### `logs` - 查看日志
```bash
pixelle logs [选项]
```

**选项：**
- `--follow, -f`：实时跟踪日志
- `--lines N, -n N`：显示最后 N 行（默认50行）

**示例：**
```bash
# 查看最近50行日志
pixelle logs

# 查看最近100行日志
pixelle logs --lines 100
pixelle logs -n 100         # 简写

# 实时跟踪日志
pixelle logs --follow
pixelle logs -f             # 简写

# 实时跟踪最近200行日志
pixelle logs --follow --lines 200
pixelle logs -f -n 200      # 简写
pixelle logs -fn 200        # 简写组合
```

## ⚙️ 配置管理命令

### `init` - 初始化配置
```bash
pixelle init
```

运行配置向导，设置：
- ComfyUI 连接
- LLM 提供商
- 服务配置

### `edit` - 编辑配置
```bash
pixelle edit
```

提供配置文件编辑选项：
- 直接编辑配置文件
- 使用向导重新配置特定部分

## 📊 信息查看命令

### `workflow` - 工作流信息
```bash
pixelle workflow
```

显示：
- 已加载的工作流
- 可用的 MCP 工具
- 工作流文件路径
- 工具统计信息

### `dev` - 开发信息
```bash
pixelle dev
```

显示详细的系统信息：
- 系统环境
- 依赖版本
- 服务详细状态
- 调试信息

## 🎯 交互模式

### `interactive` - 显式进入交互模式
```bash
pixelle interactive
```

进入交互模式后的菜单选项：

- 🚀 **[start]** 启动 Pixelle MCP 服务
- 🔄 **[init]** 初始化/重新配置 Pixelle MCP
- 📝 **[edit]** 编辑配置文件
- 🔧 **[workflow]** 查看工作流信息和已加载的工具
- 🐛 **[dev]** 开发模式和系统状态详情
- ❓ **[help]** 显示帮助信息
- ❌ **退出** 退出程序

## 🛠️ 高级选项

### 全局选项
```bash
pixelle --help    # 显示帮助信息
pixelle -h        # 简写
```


## 📝 使用技巧

### 1. 快速启动流程
```bash
# 第一次使用
pixelle            # 进入交互模式，完成配置
# 选择 [init] 完成初始化
# 选择 [start] 启动服务

# 后续使用
pixelle start      # 直接启动
```

### 2. 调试问题
```bash
# 查看详细状态
pixelle status

# 查看开发信息
pixelle dev

# 查看实时日志
pixelle logs --follow
pixelle logs -f             # 简写
```

### 3. 配置管理
```bash
# 重新配置
pixelle init

# 编辑特定配置
pixelle edit
```

### 4. 工作流管理
```bash
# 查看已加载的工作流
pixelle workflow

# 查看工作流统计
pixelle status
```

## ❓ 常见问题

### Q: 如何重置所有配置？
```bash
# 重新运行初始化向导
pixelle init
```

### Q: 服务启动失败怎么办？
```bash
# 查看详细状态
pixelle status

# 强制启动
pixelle start --force
pixelle start -f            # 简写

# 查看错误日志
pixelle logs
```

### Q: 如何更新工作流？
```bash
# 重启服务自动重新加载
pixelle stop
pixelle start

# 或查看工作流状态
pixelle workflow
```

### Q: 如何查看所有可用命令？
```bash
pixelle --help
pixelle -h              # 简写
```

## 🔗 相关链接

- [项目主页](../README_CN.md)
- [工作流开发指南](../README_CN.md#comfyui-workflow-自定义规范)
- [问题反馈](https://github.com/AIDC-AI/Pixelle-MCP/issues)
