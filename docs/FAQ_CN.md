# 🙋‍♀️ Pixelle-MCP 常见问题解答

### Pixelle MCP 与传统 ComfyUI 有什么区别？

- **传统 ComfyUI**：需要手动在界面中操作，工作流相对独立
- **Pixelle MCP**：通过 LLM 智能调用工作流，支持对话式操作，工作流可以自动组合使用

### 支持哪些安装方式？

Pixelle MCP 提供三种主要安装方式：

1. **一键体验**：
   - 临时运行：`uvx pixelle@latest`
   - 持久安装：`pip install -U pixelle`

2. **本地开发部署**：
   - 克隆源码后使用 `uv run pixelle`

3. **Docker部署**：
   - 使用 `docker compose up -d` (需要先配置.env文件)

### 默认端口是什么？如何修改？

- **默认端口**：9004
- **修改方式**：修改`.env`中`PORT`变量的配置
- **访问地址**：
  - Web界面：http://localhost:9004
  - MCP端点：http://localhost:9004/pixelle/mcp

### 如何添加自定义 MCP 工具？

1. 在 ComfyUI 中创建工作流
2. 按照 DSL 语法规范设置节点标题（如 `$image.image!:输入图片`）
3. 导出为 API 格式文件
4. 在 Web 界面中提交工作流文件，并说：“添加Tool”，LLM 会自动转换为 MCP 工具
5. 刷新页面，即可使用

### 工作流支持哪些输出节点？

系统自动识别以下输出节点：
- `SaveImage` - 图片保存节点
- `SaveVideo` - 视频保存节点  
- `SaveAudio` - 音频保存节点
- `VHS_SaveVideo` - VHS视频保存节点
- `VHS_SaveAudio` - VHS音频保存节点

也可以手动标记：在节点标题中使用 `$output.变量名`

### 工作流执行失败怎么办？

1. **先在 ComfyUI 中测试**：确保工作流在原生 ComfyUI 中能正常运行
2. **检查参数设置**：确认节点标题中的参数定义语法正确
3. **检查文件路径**：确认输入文件路径正确且文件存在
4. **查看执行日志**：检查详细的错误信息

### 支持哪些 MCP 客户端？

理论上支持所有符合 MCP 协议的客户端，包括但不限于：
- Cursor
- Claude Desktop
- 其他支持 MCP 协议的 AI 助手

### 如何配置多个 LLM 提供商？

可以在配置文件`.env`中同时配置多个 LLM 提供商作为备选，系统会自动选择可用的服务。

### 如何批量导入工作流？

可以将多个工作流文件放置在 `data/custom_workflows/` 目录中，系统会自动加载并转换为 MCP 工具。
注：该方式需要重启 Pixelle-MCP 服务

### 如何支持局域网/外部访问？

1. 更改`.env`中`HOST`为`0.0.0.0`
2. 更改`.env`中`PUBLIC_READ_URL`为局域网/公网地址，如：http://192.168.1.xx:9004 或 http://www.xxx.com

### 如何设置随机种子每次可变？

- 将 `seed` 设为 `0` 表示每次随机。
- 将采样器节点的 `seed` 设置为大于 0 的整数（例如 `123456`）则固定。

---

💡 **提示**：如果您的问题在此 FAQ 中未找到答案，欢迎加入我们的社区群组或在 GitHub 上提交问题。我们会持续更新这份 FAQ 来帮助更多用户。