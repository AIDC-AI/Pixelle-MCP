"use client";

import { useEffect, useMemo, useState } from "react";

export default function McpDemoPage() {
  const apiBase = process.env.NEXT_PUBLIC_PY_API_URL || "http://localhost:9004";
  const [url, setUrl] = useState(
    process.env.NEXT_PUBLIC_MCP_SERVER_URL || "http://localhost:9004/pixelle/mcp",
  );
  const [auth, setAuth] = useState("");
  const [tools, setTools] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<string>("");
  const [argsText, setArgsText] = useState("{}");
  const argsObject = useMemo(() => {
    try {
      return JSON.parse(argsText || "{}");
    } catch {
      return {} as Record<string, unknown>;
    }
  }, [argsText]);
  const [result, setResult] = useState<any | null>(null);

  useEffect(() => {
    void fetchTools();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchTools() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${apiBase}/mcp-tools?url=${encodeURIComponent(url)}`, {
        headers: auth ? { Authorization: auth } : undefined,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load tools");
      setTools(data.tools?.tools ?? data.tools ?? []);
      if (!selectedTool && (data.tools?.tools?.[0]?.name || data.tools?.[0]?.name)) {
        setSelectedTool(data.tools.tools?.[0]?.name || data.tools[0].name);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function callTool() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${apiBase}/mcp-tools`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(auth ? { Authorization: auth } : {}),
        },
        body: JSON.stringify({ url, tool: selectedTool, args: argsObject }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to call tool");
      setResult(data.result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-semibold">FastMCP Client Demo</h1>

      <div className="space-y-3">
        <label className="block text-sm font-medium">MCP HTTP URL</label>
        <input
          className="w-full border rounded p-2"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="http://localhost:8080/mcp"
        />

        <label className="block text-sm font-medium">Authorization header (optional)</label>
        <input
          className="w-full border rounded p-2"
          value={auth}
          onChange={(e) => setAuth(e.target.value)}
          placeholder="Bearer xxx"
        />

        <div className="flex gap-2">
          <button
            onClick={fetchTools}
            className="px-3 py-2 rounded bg-black text-white disabled:opacity-50"
            disabled={loading}
          >
            Refresh Tools
          </button>
        </div>
      </div>

      {error && (
        <div className="text-red-600 text-sm">Error: {error}</div>
      )}

      <div className="space-y-3">
        <label className="block text-sm font-medium">Available tools</label>
        <select
          className="w-full border rounded p-2"
          value={selectedTool}
          onChange={(e) => setSelectedTool(e.target.value)}
        >
          <option value="" disabled>
            {tools.length ? "Select a tool" : loading ? "Loading..." : "No tools"}
          </option>
          {tools.map((t: any) => (
            <option key={t.name} value={t.name}>
              {t.name}
            </option>
          ))}
        </select>

        <label className="block text-sm font-medium">Arguments (JSON)</label>
        <textarea
          className="w-full border rounded p-2 font-mono min-h-[120px]"
          value={argsText}
          onChange={(e) => setArgsText(e.target.value)}
        />

        <button
          onClick={callTool}
          className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
          disabled={loading || !selectedTool}
        >
          Call Tool
        </button>
      </div>

      {result && (
        <div className="space-y-2">
          <div className="text-sm font-medium">Result</div>
          <pre className="whitespace-pre-wrap break-words text-sm bg-gray-50 p-3 rounded border">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}


