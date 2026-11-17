"use client";

import { useEffect, useState } from "react";
import { Modal } from "../Modal";

/** Dispatch this from anywhere to open the dialog. */
export function openConnect(): void {
  window.dispatchEvent(new CustomEvent("veta:connect"));
}

const MCP_CONFIG = `{
  "mcpServers": {
    "veta": {
      "command": "node",
      "args": ["--import", "tsx", "src/mcp/server.ts"],
      "cwd": "/path/to/veta"
    }
  }
}`;

const API_EXAMPLE = `curl -N -X POST https://<your-deploy>/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"question":"What is our total ARR by segment?"}'`;

const TOOLS = ["query_warehouse", "run_metric", "list_metrics", "make_chart", "describe_schema"];

function Copy({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setDone(true);
          setTimeout(() => setDone(false), 1500);
        } catch {
          /* clipboard blocked — no-op */
        }
      }}
      className="shrink-0 rounded-md border border-edge px-2 py-1 text-[11px] text-muted transition-colors hover:border-edge-strong hover:text-foreground"
    >
      {done ? "Copied" : "Copy"}
    </button>
  );
}

function CodeBlock({ code }: { code: string }) {
  return (
    <div className="rounded-md border border-edge bg-background/60">
      <div className="flex items-center justify-end border-b border-edge px-2 py-1.5">
        <Copy text={code} />
      </div>
      <pre className="overflow-x-auto px-3 py-2.5 text-[11.5px] leading-relaxed">
        <code className="font-mono text-muted">{code}</code>
      </pre>
    </div>
  );
}

export function ConnectDialog() {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<"mcp" | "api">("mcp");

  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener("veta:connect", onOpen);
    return () => window.removeEventListener("veta:connect", onOpen);
  }, []);

  if (!open) return null;

  return (
    <Modal
      title="Open the engine"
      subtitle="Veta is agent-native: drive it programmatically through the same tool layer the chat uses."
      width="max-w-2xl"
      onClose={() => setOpen(false)}
    >
      <div className="p-4">
        <div className="mb-4 flex gap-1 rounded-lg border border-edge bg-background/60 p-1">
          {(["mcp", "api"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 rounded-md px-3 py-1.5 text-[12px] font-medium transition-colors ${
                tab === t ? "bg-panel text-foreground" : "text-faint hover:text-muted"
              }`}
            >
              {t === "mcp" ? "MCP server" : "REST API"}
            </button>
          ))}
        </div>

        {tab === "mcp" ? (
          <div className="space-y-3">
            <p className="text-[13px] leading-relaxed text-muted">
              Veta exposes a stdio <span className="text-foreground">MCP server</span> over the exact same tool layer the
              chat consumes — one engine, two faces. Point any MCP client (Claude Desktop, the inspector) at it:
            </p>
            <CodeBlock code={MCP_CONFIG} />
            <div>
              <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-faint">Tools exposed</div>
              <div className="flex flex-wrap gap-1.5">
                {TOOLS.map((t) => (
                  <span key={t} className="rounded-md border border-edge bg-background/60 px-2 py-1 font-mono text-[11px] text-muted">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <p className="text-[11.5px] leading-relaxed text-faint">
              Every tool runs read-only SQL against the warehouse and returns the rows + the exact query — the agent
              grounds its answers the same way a human does.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-[13px] leading-relaxed text-muted">
              The chat is a streaming HTTP endpoint. POST a question and read a server-sent event stream of grounded
              steps (the SQL, the row counts) followed by the answer:
            </p>
            <CodeBlock code={API_EXAMPLE} />
            <p className="text-[11.5px] leading-relaxed text-faint">
              Events: <span className="font-mono text-muted">step</span> (a grounded tool call) then{" "}
              <span className="font-mono text-muted">answer</span> (the synthesis with cited SQL). Same engine as the MCP
              surface and the UI.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}
