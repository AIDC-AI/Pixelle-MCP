import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

export interface ConnectOptions {
  headers?: Record<string, string>;
  endpointPath?: string; // default: /mcp
}

export async function connectToMcp(
  baseUrl: string,
  options: ConnectOptions = {},
) {
  const client = new Client(
    {
      name: "pixelle-frontend-demo",
      version: "1.0.0",
    },
    {
      capabilities: {},
    },
  );

  const transport = new StreamableHTTPClientTransport(new URL(baseUrl));

  await client.connect(transport);
  return client;
}

export async function listServerTools(
  baseUrl: string,
  options: ConnectOptions = {},
) {
  const client = await connectToMcp(baseUrl, options);
  try {
    const tools = await client.listTools();
    return tools;
  } finally {
    await safeClose(client);
  }
}

export async function callServerTool(
  baseUrl: string,
  toolName: string,
  args: Record<string, unknown> = {},
  options: ConnectOptions = {},
) {
  const client = await connectToMcp(baseUrl, options);
  try {
    const result = await client.callTool({ name: toolName, arguments: args });
    return result;
  } finally {
    await safeClose(client);
  }
}

function ensureTrailingSlash(url: string): string {
  return url.endsWith("/") ? url : `${url}/`;
}

async function safeClose(client: any) {
  try {
    if (typeof client.close === "function") {
      await client.close();
    }
  } catch {
    // ignore
  }
}


