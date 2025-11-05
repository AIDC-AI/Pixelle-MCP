import { NextRequest } from "next/server";
import { callServerTool, listServerTools } from "@/shared/mcp/createClient";

const DEFAULT_URL = process.env.MCP_SERVER_URL || "http://localhost:8080/mcp";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const url = searchParams.get("url") || DEFAULT_URL;
  console.log('GET--->')
  try {
    console.log('url', url)
    const tools = await listServerTools(url, {
      headers: buildAuthHeaders(req),
    } as any);
    
    return Response.json({ url, tools });
  } catch (error: any) {
    console.log('-->', error?.message)
    return Response.json(
      { error: error?.message || "Failed to list tools" },
      { status: 500 },
    );
  }
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const url: string = body.url || DEFAULT_URL;
  const tool: string = body.tool;
  const args: Record<string, unknown> = body.args || {};
  const headers: Record<string, string> | undefined = body.headers;

  if (!tool) {
    return Response.json({ error: "Missing 'tool' in body" }, { status: 400 });
  }

  try {
    const result = await callServerTool(url, tool, args, {
      headers: headers ?? buildAuthHeaders(req),
    } as any);

    return Response.json({ url, tool, args, result });
  } catch (error: any) {
    return Response.json(
      { error: error?.message || "Failed to call tool" },
      { status: 500 },
    );
  }
}

function buildAuthHeaders(req: NextRequest): Record<string, string> {
  const auth = req.headers.get("authorization");
  const role = req.headers.get("x-role");
  const headers: Record<string, string> = {};
  if (auth) headers["authorization"] = auth;
  if (role) headers["x-role"] = role;
  return headers;
}


