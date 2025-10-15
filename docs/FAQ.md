# 🙋‍♀️ Pixelle-MCP Frequently Asked Questions

### What's the difference between Pixelle MCP and traditional ComfyUI?

- **Traditional ComfyUI**: Requires manual operations in the interface, workflows are relatively independent
- **Pixelle MCP**: Intelligently invokes workflows through LLM, supports conversational operations, workflows can be automatically combined

### What installation methods are supported?

Pixelle MCP provides three main installation methods:

1. **One-click Experience**:
   - Temporary run: `uvx pixelle@latest`
   - Persistent installation: `pip install -U pixelle`

2. **Local Development Deployment**:
   - Clone the source code and use `uv run pixelle`

3. **Docker Deployment**:
   - Use `docker compose up -d` (requires configuring .env file first)

### What is the default port? How to modify it?

- **Default Port**: 9004
- **Modification Method**: Modify the `PORT` variable configuration in `.env`
- **Access URLs**:
  - Web Interface: http://localhost:9004
  - MCP Endpoint: http://localhost:9004/pixelle/mcp

### How to add custom MCP tools?

1. Create a workflow in ComfyUI
2. Set node titles according to DSL syntax specifications (e.g., `$image.image!:Input image`)
3. Export as API format file
4. Submit the workflow file in the Web interface and say: "Add Tool", LLM will automatically convert it to MCP tool
5. Refresh the page to use it

### Which output nodes are supported for workflow?

The system automatically recognizes the following output nodes:
- `SaveImage` - Image save node
- `SaveVideo` - Video save node
- `SaveAudio` - Audio save node
- `VHS_SaveVideo` - VHS video save node
- `VHS_SaveAudio` - VHS audio save node

You can also manually mark: Use `$output.variable_name` in the node title

### What to do if workflow execution fails?

1. **Test in ComfyUI first**: Ensure the workflow runs normally in native ComfyUI
2. **Check parameter settings**: Confirm the parameter definition syntax in node titles is correct
3. **Check file paths**: Confirm input file paths are correct and files exist
4. **View execution logs**: Check detailed error information

### Which MCP clients are supported?

Theoretically supports all clients that comply with the MCP protocol, including but not limited to:
- Cursor
- Claude Desktop
- Other AI assistants that support MCP protocol

### How to configure multiple LLM providers?

You can configure multiple LLM providers as alternatives in the configuration file `.env`, and the system will automatically select available services.

### How to batch import workflows?

You can place multiple workflow files in the `data/custom_workflows/` directory, and the system will automatically load and convert them to MCP tools.
Note: This method requires restarting the Pixelle-MCP service

### How to support LAN/external access?

1. Change `HOST` in `.env` to `0.0.0.0`
2. Change `PUBLIC_READ_URL` in `.env` to LAN/public address, such as: http://192.168.1.xx:9004 or http://www.xxx.com

### How to make the random seed change every time?

- Set `seed` to `0` to randomize on each run.
- Set `seed` to a positive integer (e.g., `123456`) to keep it fixed.

---

💡 **Tip**: If your question is not answered in this FAQ, feel free to join our community groups or submit issues on GitHub. We will continuously update this FAQ to help more users.
