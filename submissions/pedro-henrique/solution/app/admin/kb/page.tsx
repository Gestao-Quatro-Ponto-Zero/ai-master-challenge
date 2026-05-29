"use client";

import { useEffect, useRef, useState } from "react";

type KbItem = {
  id: number;
  source_ticket_id?: string;
  description: string;
  resolution: string;
  category: string;
  priority: string;
  channel: string;
  created_at: string;
};

const CATEGORIES = ["Hardware", "Software", "Access", "Storage", "HR", "Purchase", "Network", "Other"];
const PRIORITIES = ["low", "medium", "high", "critical"];
const CHANNELS = ["Web", "Email", "Phone", "Chat"];

function Badge({ text }: { text: string }) {
  const colors: Record<string, string> = {
    Hardware: "#3b82f6", Software: "#8b5cf6", Access: "#f59e0b",
    Storage: "#06b6d4", HR: "#ec4899", Purchase: "#10b981",
    Network: "#f97316", Other: "#64748b",
    low: "#10b981", medium: "#f59e0b", high: "#ef4444", critical: "#7c3aed",
  };
  const color = colors[text] ?? "#64748b";
  return (
    <span style={{
      display: "inline-block", padding: "2px 8px", borderRadius: 99,
      fontSize: "0.6875rem", fontWeight: 600, letterSpacing: "0.04em",
      background: `${color}20`, color,
    }}>
      {text}
    </span>
  );
}

function ArticleRow({
  item,
  onEdit,
  onDelete,
}: {
  item: KbItem;
  onEdit: (item: KbItem) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <div className="ad-tr" style={{ padding: "0.875rem 1rem", display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
        <p style={{ margin: 0, fontSize: "0.875rem", fontWeight: 600, color: "var(--ad-text)", lineHeight: 1.4, flex: 1 }}>
          {item.description.length > 120 ? item.description.slice(0, 120) + "…" : item.description}
        </p>
        <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
          <button
            onClick={() => onEdit(item)}
            style={{
              padding: "4px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 500,
              border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
              color: "var(--ad-text)", cursor: "pointer",
            }}
          >
            Editar
          </button>
          <button
            onClick={() => onDelete(item.id)}
            style={{
              padding: "4px 12px", borderRadius: 6, fontSize: "0.75rem", fontWeight: 500,
              border: "1px solid #ef444440", background: "#ef444410",
              color: "#ef4444", cursor: "pointer",
            }}
          >
            Excluir
          </button>
        </div>
      </div>
      <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--ad-text-muted)", lineHeight: 1.5 }}>
        {item.resolution.length > 160 ? item.resolution.slice(0, 160) + "…" : item.resolution}
      </p>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
        <Badge text={item.category} />
        <Badge text={item.priority} />
        <span style={{ fontSize: "0.6875rem", color: "var(--ad-text-dim)" }}>{item.channel}</span>
        <span style={{ fontSize: "0.6875rem", color: "var(--ad-text-dim)", marginLeft: "auto" }}>
          {new Date(item.created_at).toLocaleDateString("pt-BR")}
        </span>
      </div>
    </div>
  );
}

function ArticleModal({
  item,
  onClose,
  onSave,
}: {
  item: Partial<KbItem> | null;
  onClose: () => void;
  onSave: (data: Partial<KbItem>) => Promise<void>;
}) {
  const [form, setForm] = useState<Partial<KbItem>>(
    item ?? { category: "Other", priority: "medium", channel: "Web" }
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.description?.trim() || !form.resolution?.trim()) {
      setError("Descrição e resolução são obrigatórios");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await onSave(form);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  const isEdit = !!item?.id;
  const fieldStyle: React.CSSProperties = {
    width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
    border: "1px solid var(--ad-border)", background: "var(--ad-bg)",
    color: "var(--ad-text)", fontSize: "0.875rem", boxSizing: "border-box",
    outline: "none",
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 50,
      background: "rgba(0,0,0,0.5)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "1rem",
    }} onClick={onClose}>
      <div
        className="ad-card"
        style={{ width: "100%", maxWidth: 600, maxHeight: "90vh", overflowY: "auto", padding: "1.5rem" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.125rem", fontWeight: 600, color: "var(--ad-text)" }}>
          {isEdit ? "Editar artigo" : "Novo artigo"}
        </h2>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>
              Descrição / Problema *
            </label>
            <textarea
              rows={3}
              value={form.description ?? ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Descreva o problema ou pergunta frequente"
              style={{ ...fieldStyle, resize: "vertical" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>
              Resolução / Resposta *
            </label>
            <textarea
              rows={5}
              value={form.resolution ?? ""}
              onChange={(e) => setForm({ ...form, resolution: e.target.value })}
              placeholder="Descreva a solução ou resposta para o problema"
              style={{ ...fieldStyle, resize: "vertical" }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>
                Categoria
              </label>
              <select value={form.category ?? "Other"} onChange={(e) => setForm({ ...form, category: e.target.value })} style={fieldStyle}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>
                Prioridade
              </label>
              <select value={form.priority ?? "medium"} onChange={(e) => setForm({ ...form, priority: e.target.value })} style={fieldStyle}>
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>
                Canal
              </label>
              <select value={form.channel ?? "Web"} onChange={(e) => setForm({ ...form, channel: e.target.value })} style={fieldStyle}>
                {CHANNELS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          {error && <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--ad-danger)" }}>{error}</p>}

          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end", marginTop: "0.25rem" }}>
            <button type="button" onClick={onClose} style={{
              padding: "0.5rem 1.25rem", borderRadius: 8, fontWeight: 500, fontSize: "0.875rem",
              border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
              color: "var(--ad-text)", cursor: "pointer",
            }}>
              Cancelar
            </button>
            <button type="submit" disabled={saving} style={{
              padding: "0.5rem 1.25rem", borderRadius: 8, fontWeight: 600, fontSize: "0.875rem",
              border: "none", background: "#021E35", color: "#fff", cursor: saving ? "not-allowed" : "pointer",
              opacity: saving ? 0.7 : 1,
            }}>
              {saving ? "Salvando…" : isEdit ? "Salvar alterações" : "Criar artigo"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function UploadModal({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState("Other");
  const [priority, setPriority] = useState("medium");
  const [channel, setChannel] = useState("Web");
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{ inserted: number; errors?: string[] } | null>(null);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const fieldStyle: React.CSSProperties = {
    width: "100%", padding: "0.5rem 0.75rem", borderRadius: 8,
    border: "1px solid var(--ad-border)", background: "var(--ad-bg)",
    color: "var(--ad-text)", fontSize: "0.875rem", boxSizing: "border-box",
  };

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("category", category);
      fd.append("priority", priority);
      fd.append("channel", channel);
      const res = await fetch("/api/kb/upload", { method: "POST", body: fd });
      const json = await res.json();
      if (!res.ok) { setError(json.error ?? "Erro no upload"); return; }
      setResult(json);
      onDone();
    } catch {
      setError("Erro ao enviar arquivo");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 50, background: "rgba(0,0,0,0.5)",
      display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem",
    }} onClick={onClose}>
      <div
        className="ad-card"
        style={{ width: "100%", maxWidth: 480, padding: "1.5rem" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.125rem", fontWeight: 600, color: "var(--ad-text)" }}>
          Importar arquivo
        </h2>

        {result ? (
          <div>
            <p style={{ color: "var(--ad-success)", fontWeight: 600, fontSize: "0.9375rem" }}>
              {result.inserted} artigo(s) importado(s) com sucesso!
            </p>
            {result.errors && result.errors.length > 0 && (
              <p style={{ color: "var(--ad-warning)", fontSize: "0.8125rem", marginTop: 8 }}>
                {result.errors.length} erro(s): {result.errors.join("; ")}
              </p>
            )}
            <button onClick={onClose} style={{
              marginTop: "1rem", padding: "0.5rem 1.25rem", borderRadius: 8,
              background: "#021E35", color: "#fff", border: "none",
              fontWeight: 600, fontSize: "0.875rem", cursor: "pointer",
            }}>
              Fechar
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div
              onClick={() => inputRef.current?.click()}
              style={{
                border: `2px dashed var(--ad-border)`, borderRadius: 10,
                padding: "2rem 1rem", textAlign: "center", cursor: "pointer",
                background: file ? "#021E3510" : "transparent",
              }}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,.doc,.docx,.txt,.md"
                style={{ display: "none" }}
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {file ? (
                <p style={{ margin: 0, fontSize: "0.875rem", color: "#021E35", fontWeight: 600 }}>
                  📄 {file.name}
                </p>
              ) : (
                <>
                  <p style={{ margin: "0 0 0.25rem", fontSize: "0.875rem", color: "var(--ad-text)", fontWeight: 600 }}>
                    Clique para selecionar
                  </p>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--ad-text-muted)" }}>
                    PDF, DOC, DOCX, TXT, MD
                  </p>
                </>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>Categoria</label>
                <select value={category} onChange={(e) => setCategory(e.target.value)} style={fieldStyle}>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>Prioridade</label>
                <select value={priority} onChange={(e) => setPriority(e.target.value)} style={fieldStyle}>
                  {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--ad-text-muted)", marginBottom: 4 }}>Canal</label>
                <select value={channel} onChange={(e) => setChannel(e.target.value)} style={fieldStyle}>
                  {CHANNELS.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            {error && <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--ad-danger)" }}>{error}</p>}

            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
              <button onClick={onClose} style={{
                padding: "0.5rem 1.25rem", borderRadius: 8, fontWeight: 500, fontSize: "0.875rem",
                border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
                color: "var(--ad-text)", cursor: "pointer",
              }}>
                Cancelar
              </button>
              <button onClick={handleUpload} disabled={!file || uploading} style={{
                padding: "0.5rem 1.25rem", borderRadius: 8, fontWeight: 600, fontSize: "0.875rem",
                border: "none", background: "#021E35", color: "#fff",
                cursor: !file || uploading ? "not-allowed" : "pointer",
                opacity: !file || uploading ? 0.7 : 1,
              }}>
                {uploading ? "Processando…" : "Importar"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AdminKbPage() {
  const [items, setItems] = useState<KbItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [editItem, setEditItem] = useState<Partial<KbItem> | null | undefined>(undefined);
  const [showUpload, setShowUpload] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch("/api/kb");
      const json = await res.json();
      setItems(json.items ?? []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;

    void (async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/kb");
        const json = await res.json();
        if (active) {
          setItems(json.items ?? []);
        }
      } catch {
        if (active) {
          setItems([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  async function handleSave(data: Partial<KbItem>) {
    if (data.id) {
      const res = await fetch(`/api/kb/${data.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) { const j = await res.json(); throw new Error(j.error); }
    } else {
      const res = await fetch("/api/kb", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!res.ok) { const j = await res.json(); throw new Error(j.error); }
    }
    await load();
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir este artigo da base de conhecimento?")) return;
    await fetch(`/api/kb/${id}`, { method: "DELETE" });
    await load();
  }

  const filtered = items.filter((item) => {
    const matchCat = categoryFilter === "all" || item.category === categoryFilter;
    const q = search.toLowerCase();
    const matchSearch = !q || item.description.toLowerCase().includes(q) || item.resolution.toLowerCase().includes(q);
    return matchCat && matchSearch;
  });

  return (
    <>
      <header className="admin-header">
        <nav style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}>
          <span style={{ color: "var(--ad-text-dim)" }}>Painel</span>
          <span style={{ color: "var(--ad-text-dim)" }}>/</span>
          <span style={{ color: "var(--ad-text)", fontWeight: 500 }}>Base de Conhecimento</span>
        </nav>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            onClick={() => setShowUpload(true)}
            style={{
              padding: "0.5rem 1rem", borderRadius: 8, fontWeight: 500, fontSize: "0.875rem",
              border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
              color: "var(--ad-text)", cursor: "pointer",
            }}
          >
            Importar arquivo
          </button>
          <button
            onClick={() => setEditItem(null)}
            style={{
              padding: "0.5rem 1rem", borderRadius: 8, fontWeight: 600, fontSize: "0.875rem",
              border: "none", background: "#021E35", color: "#fff", cursor: "pointer",
            }}
          >
            + Novo artigo
          </button>
        </div>
      </header>

      <div className="admin-content">
        <div style={{ marginBottom: "1.75rem" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800, letterSpacing: "-0.03em", color: "var(--ad-text)", lineHeight: 1.15 }}>Base de Conhecimento</h1>
          <p style={{ margin: "0.375rem 0 0", fontSize: "0.9375rem", color: "var(--ad-text-muted)" }}>
            Gerencie artigos e resoluções para deflexão de tickets
          </p>
        </div>

      <div style={{ display: "flex", gap: "0.75rem", marginBottom: "1.25rem", flexWrap: "wrap" }}>
        <input
          type="text"
          placeholder="Pesquisar na base…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1, minWidth: 200, padding: "0.5rem 0.875rem", borderRadius: 8,
            border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
            color: "var(--ad-text)", fontSize: "0.875rem",
          }}
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          style={{
            padding: "0.5rem 0.75rem", borderRadius: 8,
            border: "1px solid var(--ad-border)", background: "var(--ad-surface)",
            color: "var(--ad-text)", fontSize: "0.875rem",
          }}
        >
          <option value="all">Todas as categorias</option>
          {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div className="ad-card" style={{ overflow: "hidden" }}>
        {loading ? (
          <p style={{ padding: "2rem", textAlign: "center", color: "var(--ad-text-muted)", fontSize: "0.875rem" }}>
            Carregando…
          </p>
        ) : filtered.length === 0 ? (
          <p style={{ padding: "2rem", textAlign: "center", color: "var(--ad-text-muted)", fontSize: "0.875rem" }}>
            {items.length === 0 ? "Nenhum artigo na base. Adicione o primeiro artigo." : "Nenhum resultado para a pesquisa."}
          </p>
        ) : (
          filtered.map((item) => (
            <ArticleRow key={item.id} item={item} onEdit={setEditItem} onDelete={handleDelete} />
          ))
        )}
      </div>

      <p style={{ marginTop: "0.75rem", fontSize: "0.75rem", color: "var(--ad-text-dim)" }}>
        {filtered.length} de {items.length} artigo(s)
      </p>

      {editItem !== undefined && (
        <ArticleModal
          item={editItem}
          onClose={() => setEditItem(undefined)}
          onSave={handleSave}
        />
      )}

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onDone={() => { setShowUpload(false); load(); }}
        />
      )}
      </div>
    </>
  );
}
