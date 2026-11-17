"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Modal } from "../Modal";

/** Open the data-source picker from anywhere (the TopBar dataset chip fires this). */
export function openDataSource(): void {
  window.dispatchEvent(new CustomEvent("veta:datasource"));
}

interface Dataset {
  id: string;
  label: string;
  filename: string | null;
  is_default: number;
  is_active: number;
  table_count: number | null;
  size_bytes: number | null;
  created_at: string;
}

const msg = (e: unknown): string => (e instanceof Error ? e.message : String(e));

function formatBytes(n: number | null): string {
  if (!n) return "";
  if (n >= 1024 * 1024) return `${Math.round(n / 1024 / 1024)} MB`;
  if (n >= 1024) return `${Math.round(n / 1024)} KB`;
  return `${n} B`;
}

export function DataSourceDialog() {
  const [open, setOpen] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null); // id being activated/removed, or "upload"
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/datasets");
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Failed to load datasets.");
      setDatasets(json.datasets ?? []);
      setActiveId(json.activeId ?? "");
    } catch (e) {
      setError(msg(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const onOpen = () => {
      setOpen(true);
      setError(null);
      setFile(null);
      void refresh();
    };
    window.addEventListener("veta:datasource", onOpen);
    return () => window.removeEventListener("veta:datasource", onOpen);
  }, [refresh]);

  if (!open) return null;

  async function activate(id: string) {
    setBusy(id);
    setError(null);
    try {
      const res = await fetch("/api/datasets/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Failed to switch.");
      window.location.reload(); // server re-renders the dashboard against the new warehouse
    } catch (e) {
      setError(msg(e));
      setBusy(null);
    }
  }

  async function upload() {
    if (!file) return;
    setBusy("upload");
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("activate", "1");
      const res = await fetch("/api/datasets", { method: "POST", body: form });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Upload failed.");
      window.location.reload();
    } catch (e) {
      setError(msg(e));
      setBusy(null);
    }
  }

  async function remove(d: Dataset) {
    setBusy(d.id);
    setError(null);
    try {
      const res = await fetch(`/api/datasets/${d.id}`, { method: "DELETE" });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error ?? "Delete failed.");
      if (d.id === activeId) {
        window.location.reload(); // it was live — fall back to the built-in
        return;
      }
      setBusy(null);
      void refresh();
    } catch (e) {
      setError(msg(e));
      setBusy(null);
    }
  }

  return (
    <Modal
      title="Data source"
      subtitle="Point Veta at a different warehouse — the built-in demo, or your own SQLite."
      width="max-w-lg"
      onClose={() => setOpen(false)}
    >
      <div className="space-y-4 p-4">
        {/* The connectable warehouses. */}
        <ul className="space-y-2">
          {datasets.map((d) => {
            const active = d.id === activeId;
            return (
              <li
                key={d.id}
                className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 ${
                  active ? "border-accent/50 bg-accent/5" : "border-edge bg-background/40"
                }`}
              >
                <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${active ? "bg-accent" : "bg-faint/50"}`} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-[13px] font-medium text-foreground">{d.label}</span>
                    {d.is_default === 1 && (
                      <span className="shrink-0 rounded border border-edge px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-faint">
                        Built-in
                      </span>
                    )}
                    {active && (
                      <span className="shrink-0 rounded border border-accent/40 px-1.5 py-0.5 text-[9px] uppercase tracking-wider text-accent">
                        Live
                      </span>
                    )}
                  </div>
                  <div className="mt-0.5 font-mono text-[10.5px] text-faint">
                    {d.table_count != null ? `${d.table_count} tables` : "—"}
                    {d.size_bytes ? ` · ${formatBytes(d.size_bytes)}` : ""}
                  </div>
                </div>

                {!active && (
                  <button
                    onClick={() => activate(d.id)}
                    disabled={busy !== null}
                    className="shrink-0 rounded-md border border-edge px-2.5 py-1 text-[11px] text-muted transition-colors hover:border-edge-strong hover:text-foreground disabled:opacity-50"
                  >
                    {busy === d.id ? "Connecting…" : "Connect"}
                  </button>
                )}
                {d.is_default === 0 && (
                  <button
                    onClick={() => remove(d)}
                    disabled={busy !== null}
                    aria-label={`Delete ${d.label}`}
                    className="shrink-0 rounded-md p-1.5 text-faint transition-colors hover:bg-surface hover:text-red-300 disabled:opacity-50"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5">
                      <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6" />
                    </svg>
                  </button>
                )}
              </li>
            );
          })}
          {loading && datasets.length === 0 && <li className="px-1 text-[12px] text-faint">Loading…</li>}
        </ul>

        {/* Upload your own warehouse. */}
        <div className="rounded-lg border border-dashed border-edge bg-background/40 p-3.5">
          <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-faint">Upload a warehouse</div>
          <input
            ref={fileRef}
            type="file"
            accept=".sqlite,.db,.sqlite3"
            onChange={(e) => {
              setError(null);
              setFile(e.target.files?.[0] ?? null);
            }}
            className="block w-full text-[12px] text-muted file:mr-3 file:rounded-md file:border file:border-edge file:bg-panel file:px-3 file:py-1.5 file:text-[12px] file:text-foreground hover:file:border-edge-strong"
          />
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={upload}
              disabled={!file || busy !== null}
              className="rounded-lg bg-accent px-3 py-1.5 text-[12.5px] font-medium text-[#1a1406] transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              {busy === "upload" ? "Uploading…" : "Upload & connect"}
            </button>
            {file && <span className="truncate text-[11px] text-faint">{file.name}</span>}
          </div>
          <p className="mt-2 text-[11px] leading-relaxed text-faint">
            Opened strictly <span className="text-muted">read-only</span>. The agent discovers your schema and writes
            its own SQL — nothing is hand-tuned. The curated dashboard reads the RavenStack views; your data lives in
            the chat.
          </p>
        </div>

        {error && <p className="text-[12px] text-red-300">{error}</p>}
      </div>
    </Modal>
  );
}
