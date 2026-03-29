"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { Navbar } from "../components/Navbar";

interface Stats { total: number; active: number; won: number; lost: number }
interface Meta  { agents: string[]; products: string[]; stages: string[] }

type Tab = "upload" | "add" | "manage" | "agents" | "slack";

// ── Reusable field components ──────────────────────────────────────────────────
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-gray-500 uppercase tracking-wider">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:border-blue-500 focus:outline-none w-full";
const selectCls = inputCls;

// ── Upload Tab ─────────────────────────────────────────────────────────────────
function UploadTab({ onDone }: { onDone: () => void }) {
  const [mode, setMode]       = useState<"replace" | "append">("append");
  const [status, setStatus]   = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [message, setMessage] = useState("");
  const [fileName, setFileName] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    setFileName(file.name);
    setStatus("loading");
    const csv = await file.text();
    try {
      const res = await fetch("/api/admin/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csv, mode }),
      });
      const data = await res.json();
      if (!res.ok) {
        setStatus("error");
        setMessage(data.error ?? "Erro desconhecido.");
      } else {
        setStatus("ok");
        setMessage(`${data.rows} linhas ${mode === "replace" ? "importadas" : "adicionadas"} com sucesso.`);
        onDone();
      }
    } catch {
      setStatus("error");
      setMessage("Falha na requisição.");
    }
  }, [mode, onDone]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="space-y-6">
      {/* Mode selector */}
      <div className="flex gap-3">
        {(["append", "replace"] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-3 rounded-xl border text-sm font-medium transition-colors ${
              mode === m
                ? "bg-blue-500/15 border-blue-500 text-blue-400"
                : "border-gray-700 text-gray-400 hover:border-gray-600"
            }`}
          >
            {m === "append" ? "➕ Adicionar ao pipeline" : "🔄 Substituir pipeline completo"}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-500">
        {mode === "append"
          ? "Os novos leads serão adicionados ao pipeline existente. Use quando importar dados incrementais do seu CRM."
          : "O pipeline atual será completamente substituído pelo arquivo enviado. Use quando quiser sincronizar do zero com seu CRM."}
      </p>

      {/* Drop zone */}
      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-700 hover:border-blue-500/60 rounded-2xl p-10 text-center transition-colors cursor-pointer"
        onClick={() => fileRef.current?.click()}
      >
        <div className="text-3xl mb-3">📂</div>
        <p className="text-gray-400 text-sm font-medium">
          {fileName ? fileName : "Arraste o arquivo CSV aqui ou clique para selecionar"}
        </p>
        <p className="text-gray-600 text-xs mt-2">
          Colunas obrigatórias: opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value
        </p>
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />
      </div>

      {/* Status feedback */}
      {status === "loading" && (
        <div className="flex items-center gap-2 text-blue-400 text-sm">
          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          Processando...
        </div>
      )}
      {status === "ok" && (
        <div className="bg-emerald-500/10 border border-emerald-500/25 rounded-xl p-4 text-emerald-400 text-sm">
          ✅ {message}
        </div>
      )}
      {status === "error" && (
        <div className="bg-red-500/10 border border-red-500/25 rounded-xl p-4 text-red-400 text-sm">
          ❌ {message}
        </div>
      )}

      {/* CSV template download hint */}
      <div className="text-xs text-gray-600 border-t border-gray-800 pt-4">
        <strong className="text-gray-500">Formato esperado:</strong>{" "}
        <code className="bg-gray-900 px-1.5 py-0.5 rounded text-gray-400">
          opportunity_id,sales_agent,product,account,deal_stage,engage_date,close_date,close_value
        </code>
      </div>
    </div>
  );
}

// ── Add Lead Tab ───────────────────────────────────────────────────────────────
function AddLeadTab({ meta, onDone }: { meta: Meta; onDone: () => void }) {
  const today = new Date().toISOString().split("T")[0];
  const [form, setForm] = useState({
    sales_agent: "",
    product: "",
    account: "",
    deal_stage: "Engaging",
    engage_date: today,
    close_date: "",
    close_value: "",
  });
  const [status, setStatus]   = useState<"idle" | "loading" | "ok" | "error">("idle");
  const [message, setMessage] = useState("");

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async () => {
    if (!form.sales_agent || !form.product) {
      setStatus("error"); setMessage("Vendedor e Produto são obrigatórios."); return;
    }
    setStatus("loading");
    const res = await fetch("/api/admin/pipeline", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus("error"); setMessage(data.error ?? "Erro ao adicionar.");
    } else {
      setStatus("ok");
      setMessage(`Lead adicionado com ID ${data.opportunity_id}.`);
      setForm({ sales_agent: "", product: "", account: "", deal_stage: "Engaging", engage_date: today, close_date: "", close_value: "" });
      onDone();
    }
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Vendedor *">
          <select value={form.sales_agent} onChange={(e) => set("sales_agent", e.target.value)} className={selectCls}>
            <option value="">Selecione...</option>
            {meta.agents.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </Field>
        <Field label="Produto *">
          <select value={form.product} onChange={(e) => set("product", e.target.value)} className={selectCls}>
            <option value="">Selecione...</option>
            {meta.products.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </Field>
        <Field label="Conta (empresa)">
          <input value={form.account} onChange={(e) => set("account", e.target.value)} placeholder="Ex: Acme Corp" className={inputCls} />
        </Field>
        <Field label="Stage">
          <select value={form.deal_stage} onChange={(e) => set("deal_stage", e.target.value)} className={selectCls}>
            <option value="Engaging">Engaging</option>
            <option value="Prospecting">Prospecting</option>
          </select>
        </Field>
        <Field label="Data de engajamento">
          <input type="date" value={form.engage_date} onChange={(e) => set("engage_date", e.target.value)} className={inputCls} />
        </Field>
        <Field label="Valor fechado (opcional)">
          <input type="number" value={form.close_value} onChange={(e) => set("close_value", e.target.value)} placeholder="0" className={inputCls} />
        </Field>
      </div>

      <button
        onClick={submit}
        disabled={status === "loading"}
        className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors disabled:opacity-50"
      >
        {status === "loading" ? "Salvando..." : "➕ Adicionar Lead"}
      </button>

      {status === "ok"    && <div className="bg-emerald-500/10 border border-emerald-500/25 rounded-xl p-3 text-emerald-400 text-sm">✅ {message}</div>}
      {status === "error" && <div className="bg-red-500/10 border border-red-500/25 rounded-xl p-3 text-red-400 text-sm">❌ {message}</div>}
    </div>
  );
}

// ── Manage Leads Tab ───────────────────────────────────────────────────────────
function ManageTab({ onDone }: { onDone: () => void }) {
  interface Lead { opportunity_id: string; account: string; sales_agent: string; product: string; deal_stage: string; days_in_stage: number; score: number }
  const [leads, setLeads]     = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetch("/api/deals", { cache: "no-store" });
    const data = await res.json();
    setLeads(data.slice(0, 200)); // show top 200 scored deals
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const deleteLead = async (id: string) => {
    setDeleting(id);
    await fetch("/api/admin/pipeline", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    setLeads((prev) => prev.filter((l) => l.opportunity_id !== id));
    setDeleting(null);
    onDone();
  };

  const filtered = leads.filter((l) =>
    !search || l.account?.toLowerCase().includes(search.toLowerCase()) ||
    l.sales_agent?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return (
    <div className="flex justify-center py-16">
      <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-4">
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Buscar por conta ou vendedor..."
        className={inputCls}
      />
      <p className="text-xs text-gray-500">Mostrando os 200 deals com maior score. Use busca para filtrar.</p>

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/80 text-gray-400">
              <th className="text-left px-4 py-2 font-medium">Conta</th>
              <th className="text-left px-4 py-2 font-medium">Produto</th>
              <th className="text-left px-4 py-2 font-medium">Vendedor</th>
              <th className="text-left px-4 py-2 font-medium">Stage</th>
              <th className="text-center px-4 py-2 font-medium">Score</th>
              <th className="text-center px-4 py-2 font-medium">Ação</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((lead) => (
              <tr key={lead.opportunity_id} className="border-b border-gray-800/50 hover:bg-gray-900/40">
                <td className="px-4 py-2.5 text-white font-medium">
                  {lead.account || <span className="text-gray-600 italic">Sem conta</span>}
                  <div className="text-[10px] text-gray-600">{lead.opportunity_id}</div>
                </td>
                <td className="px-4 py-2.5 text-gray-300">{lead.product}</td>
                <td className="px-4 py-2.5 text-gray-400">{lead.sales_agent}</td>
                <td className="px-4 py-2.5">
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${
                    lead.deal_stage === "Engaging"
                      ? "bg-blue-500/15 text-blue-400 border-blue-500/30"
                      : "bg-gray-500/15 text-gray-400 border-gray-500/30"
                  }`}>{lead.deal_stage}</span>
                </td>
                <td className="px-4 py-2.5 text-center tabular-nums font-bold text-white">{lead.score}</td>
                <td className="px-4 py-2.5 text-center">
                  <button
                    onClick={() => deleteLead(lead.opportunity_id)}
                    disabled={deleting === lead.opportunity_id}
                    className="text-xs px-2.5 py-1 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-40"
                  >
                    {deleting === lead.opportunity_id ? "..." : "Remover"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Agents Tab ────────────────────────────────────────────────────────────────
interface Agent { sales_agent: string; manager: string; regional_office: string }

function AgentsTab({ onDone }: { onDone: () => void }) {
  const [agents, setAgents]   = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [msg, setMsg]         = useState<{ ok: boolean; text: string } | null>(null);

  // Add-agent form
  const [name,   setName]   = useState("");
  const [mgr,    setMgr]    = useState("");
  const [region, setRegion] = useState("Central");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetch("/api/admin/agents", { cache: "no-store" });
    const data = await res.json();
    setAgents(data.agents ?? []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function addAgent() {
    if (!name.trim()) return;
    setSaving(true); setMsg(null);
    const res = await fetch("/api/admin/agents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sales_agent: name.trim(), manager: mgr.trim(), regional_office: region }),
    });
    const data = await res.json();
    setSaving(false);
    if (res.ok) { setMsg({ ok: true, text: `Vendedor "${name.trim()}" adicionado.` }); setName(""); setMgr(""); load(); onDone(); }
    else setMsg({ ok: false, text: data.error ?? "Erro ao adicionar." });
  }

  async function deleteAgent(agentName: string) {
    setDeleting(agentName); setMsg(null);
    const res = await fetch("/api/admin/agents", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sales_agent: agentName }),
    });
    const data = await res.json();
    setDeleting(null);
    if (res.ok) { setMsg({ ok: true, text: `"${agentName}" removido.` }); load(); onDone(); }
    else setMsg({ ok: false, text: data.error ?? "Erro ao remover." });
  }

  const regions = ["Central", "West", "East"];

  return (
    <div className="space-y-6">
      {/* Feedback */}
      {msg && (
        <div className={`rounded-xl px-4 py-3 text-sm border ${msg.ok ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400" : "bg-red-500/10 border-red-500/25 text-red-400"}`}>
          {msg.text}
        </div>
      )}

      {/* Add form */}
      <div className="bg-gray-800/40 rounded-xl p-5 border border-gray-700 space-y-4">
        <p className="text-white text-sm font-semibold">➕ Adicionar vendedor</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Field label="Nome do vendedor *">
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex: João Silva"
              className={inputCls} />
          </Field>
          <Field label="Manager">
            <input value={mgr} onChange={(e) => setMgr(e.target.value)} placeholder="Ex: Dustin Brinkmann"
              className={inputCls} />
          </Field>
          <Field label="Região">
            <select value={region} onChange={(e) => setRegion(e.target.value)} className={selectCls}>
              {regions.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </Field>
        </div>
        <button onClick={addAgent} disabled={!name.trim() || saving}
          className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors disabled:opacity-40">
          {saving ? "Salvando..." : "Adicionar vendedor"}
        </button>
      </div>

      {/* List */}
      {loading ? (
        <p className="text-gray-500 text-sm">Carregando...</p>
      ) : (
        <div>
          <p className="text-gray-500 text-xs mb-2">{agents.length} vendedores cadastrados</p>
          <div className="rounded-xl border border-gray-800 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-900/80 border-b border-gray-800 text-gray-500 text-xs uppercase tracking-wider">
                  <th className="text-left px-4 py-2">Vendedor</th>
                  <th className="text-left px-4 py-2">Manager</th>
                  <th className="text-left px-4 py-2">Região</th>
                  <th className="text-center px-4 py-2">Ação</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((a) => (
                  <tr key={a.sales_agent} className="border-b border-gray-800/50 hover:bg-gray-900/40">
                    <td className="px-4 py-2.5 text-white font-medium">{a.sales_agent}</td>
                    <td className="px-4 py-2.5 text-gray-400">{a.manager || "—"}</td>
                    <td className="px-4 py-2.5 text-gray-400">{a.regional_office || "—"}</td>
                    <td className="px-4 py-2.5 text-center">
                      <button onClick={() => deleteAgent(a.sales_agent)} disabled={deleting === a.sales_agent}
                        className="text-xs px-2.5 py-1 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-40">
                        {deleting === a.sales_agent ? "..." : "Remover"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Slack Tab ──────────────────────────────────────────────────────────────────
const SETUP_SQL = `create table if not exists app_settings (
  key        text primary key,
  value      text not null,
  updated_at timestamptz default now()
);
alter table app_settings enable row level security;`;

function SlackTab() {
  type Status = "idle" | "loading" | "ok" | "error";

  const [config, setConfig]           = useState<{ slack_configured: boolean; slack_webhook_masked?: string; table_missing?: boolean } | null>(null);
  const [webhookInput, setWebhookInput] = useState("");
  const [saveStatus, setSaveStatus]   = useState<Status>("idle");
  const [saveMsg, setSaveMsg]         = useState("");
  const [morningStatus, setMorningStatus] = useState<Status>("idle");
  const [eveningStatus, setEveningStatus] = useState<Status>("idle");
  const [morningMsg, setMorningMsg]   = useState("");
  const [eveningMsg, setEveningMsg]   = useState("");
  const [copied, setCopied]           = useState(false);

  useEffect(() => {
    fetch("/api/admin/settings", { cache: "no-store" })
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => setConfig({ slack_configured: false }));
  }, []);

  async function saveWebhook() {
    if (!webhookInput.trim().startsWith("https://hooks.slack.com/")) {
      setSaveStatus("error");
      setSaveMsg("URL inválida. Deve começar com https://hooks.slack.com/");
      return;
    }
    setSaveStatus("loading");
    const res  = await fetch("/api/admin/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "slack_webhook_url", value: webhookInput.trim() }),
    });
    const data = await res.json();
    if (!res.ok) {
      setSaveStatus("error");
      setSaveMsg(data.error === "table_missing"
        ? "Tabela app_settings não encontrada. Crie-a no Supabase usando o SQL abaixo."
        : data.error ?? "Erro ao salvar.");
    } else {
      setSaveStatus("ok");
      setSaveMsg("Webhook salvo! Teste o envio abaixo.");
      setConfig({ slack_configured: true, slack_webhook_masked: webhookInput.trim().substring(0, 40) + "…" });
      setWebhookInput("");
    }
  }

  async function sendSlack(type: "morning" | "evening") {
    const setStatus = type === "morning" ? setMorningStatus : setEveningStatus;
    const setMsg    = type === "morning" ? setMorningMsg    : setEveningMsg;
    setStatus("loading");
    try {
      const res  = await fetch(`/api/slack/report?type=${type}`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        setStatus("error"); setMsg(data.error ?? "Erro desconhecido.");
      } else {
        setStatus("ok"); setMsg(`Mensagem enviada! (${data.sent} deals analisados)`);
      }
    } catch {
      setStatus("error"); setMsg("Falha na requisição.");
    }
  }

  function copySQL() {
    navigator.clipboard.writeText(SETUP_SQL).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2000);
    });
  }

  const isConfigured = config?.slack_configured;

  return (
    <div className="space-y-6">

      {/* Header + status */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xl">💬</span>
            <h3 className="text-white font-bold text-base">Conectar com Slack</h3>
          </div>
          <p className="text-gray-500 text-sm">
            Receba relatórios diários do pipeline direto no Slack — sem precisar abrir a plataforma.
          </p>
        </div>
        <span className={`shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full border ${
          isConfigured
            ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
            : "bg-gray-700/40 text-gray-500 border-gray-700"
        }`}>
          {isConfigured ? "🟢 Conectado" : "⚪ Não configurado"}
        </span>
      </div>

      {/* If connected — show masked URL */}
      {isConfigured && config?.slack_webhook_masked && (
        <div className="bg-emerald-500/10 border border-emerald-500/25 rounded-xl p-4">
          <p className="text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-1">Webhook ativo</p>
          <p className="text-emerald-300 font-mono text-xs">{config.slack_webhook_masked}</p>
          <button
            onClick={() => { setConfig((c) => c ? { ...c, slack_configured: false } : c); setWebhookInput(""); }}
            className="mt-3 text-xs text-gray-500 hover:text-gray-300 underline transition-colors"
          >
            Substituir webhook
          </button>
        </div>
      )}

      {/* Setup steps */}
      {!isConfigured && (
        <div className="space-y-4">
          {/* Step 1 */}
          <div className="bg-gray-800/40 border border-gray-700 rounded-xl p-5">
            <p className="text-white text-sm font-semibold mb-2">
              <span className="text-purple-400 mr-2">①</span> Crie um Incoming Webhook no Slack
            </p>
            <p className="text-gray-400 text-xs mb-3">
              Acesse o painel de apps do Slack, crie um novo app com &quot;Incoming Webhooks&quot; ativo e gere uma URL para o canal desejado.
            </p>
            <a
              href="https://api.slack.com/apps"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-medium transition-colors"
            >
              → Acessar api.slack.com/apps
            </a>
          </div>

          {/* Step 2 — table missing warning */}
          {config?.table_missing && (
            <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl p-5">
              <p className="text-amber-400 text-sm font-semibold mb-2">⚠️ Configuração única — execute este SQL no Supabase</p>
              <p className="text-gray-400 text-xs mb-3">Vá em Supabase → SQL Editor e execute:</p>
              <pre className="bg-gray-950 rounded-lg p-3 text-xs text-gray-300 overflow-x-auto">{SETUP_SQL}</pre>
              <button
                onClick={copySQL}
                className="mt-3 text-xs px-3 py-1.5 rounded-lg border border-gray-600 text-gray-400 hover:text-white hover:border-gray-500 transition-colors"
              >
                {copied ? "✅ Copiado!" : "📋 Copiar SQL"}
              </button>
            </div>
          )}

          {/* Step 2 — URL input */}
          <div className="bg-gray-800/40 border border-gray-700 rounded-xl p-5 space-y-3">
            <p className="text-white text-sm font-semibold">
              <span className="text-purple-400 mr-2">②</span> Cole a URL do webhook
            </p>
            <div className="flex gap-2">
              <input
                type="url"
                value={webhookInput}
                onChange={(e) => setWebhookInput(e.target.value)}
                placeholder="https://hooks.slack.com/services/T.../B.../..."
                className="flex-1 bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:border-purple-500 focus:outline-none font-mono placeholder-gray-600"
              />
              <button
                onClick={saveWebhook}
                disabled={saveStatus === "loading" || !webhookInput.trim()}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm font-semibold transition-colors disabled:opacity-40 whitespace-nowrap"
              >
                {saveStatus === "loading" ? "Salvando..." : "Salvar"}
              </button>
            </div>
            {saveStatus === "ok"    && <p className="text-emerald-400 text-xs">✅ {saveMsg}</p>}
            {saveStatus === "error" && <p className="text-red-400 text-xs">❌ {saveMsg}</p>}
          </div>
        </div>
      )}

      {/* Send buttons — always visible once configured */}
      {isConfigured && (
        <div>
          <p className="text-white text-sm font-semibold mb-3">
            <span className="text-purple-400 mr-2">③</span> Enviar relatórios agora
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
              <div>
                <p className="text-white text-sm font-semibold">☀️ Relatório Matinal</p>
                <p className="text-gray-500 text-xs mt-1">Top 10 deals por score + stats · seg–sex 8h</p>
              </div>
              <button
                onClick={() => sendSlack("morning")}
                disabled={morningStatus === "loading"}
                className="w-full py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
              >
                {morningStatus === "loading"
                  ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Enviando...</>
                  : "📤 Enviar Agora"}
              </button>
              {morningStatus === "ok"    && <p className="text-emerald-400 text-xs">✅ {morningMsg}</p>}
              {morningStatus === "error" && <p className="text-red-400 text-xs">❌ {morningMsg}</p>}
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
              <div>
                <p className="text-white text-sm font-semibold">🌙 Resumo Noturno</p>
                <p className="text-gray-500 text-xs mt-1">Visão geral, win rate, top 5 zumbis · seg–sex 18h</p>
              </div>
              <button
                onClick={() => sendSlack("evening")}
                disabled={eveningStatus === "loading"}
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
              >
                {eveningStatus === "loading"
                  ? <><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Enviando...</>
                  : "📤 Enviar Agora"}
              </button>
              {eveningStatus === "ok"    && <p className="text-emerald-400 text-xs">✅ {eveningMsg}</p>}
              {eveningStatus === "error" && <p className="text-red-400 text-xs">❌ {eveningMsg}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Schedule info */}
      <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-5">
        <p className="text-purple-400 text-sm font-semibold mb-2">🗓️ Agendamento automático</p>
        <div className="space-y-1.5 text-xs text-gray-400">
          <p>• <strong className="text-gray-300">08:00 seg–sex</strong> — Relatório Matinal (top 10 prioridades do dia)</p>
          <p>• <strong className="text-gray-300">18:00 seg–sex</strong> — Resumo Noturno (visão geral do pipeline)</p>
        </div>
      </div>
    </div>
  );
}

// Products list — module-level constant so useCallback doesn't need it as a dep
const PRODUCTS = ["GTK 500", "GTX Plus Pro", "GTX Pro", "MG Advanced", "GTX Plus Basic", "GTX Basic", "MG Special"];

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [meta, setMeta]   = useState<Meta>({ agents: [], products: [], stages: [] });
  const [tab, setTab]     = useState<Tab>("upload");

  const loadStats = useCallback(async () => {
    const [statsRes, metaRes, agentsRes] = await Promise.all([
      fetch("/api/admin/pipeline", { cache: "no-store" }),
      fetch("/api/meta",           { cache: "no-store" }),
      fetch("/api/admin/agents",   { cache: "no-store" }),
    ]);
    const s = await statsRes.json();
    const m = await metaRes.json();
    const ag = await agentsRes.json();
    setStats(s);
    // Use agents from sales_teams.csv directly (not just those with active deals)
    const allAgents = ag.agents?.map((a: { sales_agent: string }) => a.sales_agent) ?? m.agents ?? [];
    setMeta({ agents: allAgents, products: PRODUCTS, stages: m.stages ?? [] });
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "upload",  label: "Carregar Pipeline", icon: "📤" },
    { id: "add",     label: "Adicionar Lead",    icon: "➕" },
    { id: "manage",  label: "Gerenciar Leads",   icon: "🗂️" },
    { id: "agents",  label: "Vendedores",        icon: "👥" },
    { id: "slack",   label: "Slack",              icon: "📡" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Navbar />

      <main className="max-w-screen-lg mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold text-white">Painel de Administração</h2>
          <p className="text-gray-500 text-sm mt-1">
            Gerencie os dados do pipeline — carregue novos leads, adicione individualmente ou remova registros.
          </p>
        </div>

        {/* Stats bar */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Total de deals", value: stats.total, color: "text-white" },
              { label: "Ativos",         value: stats.active, color: "text-blue-400" },
              { label: "Ganhos (Won)",   value: stats.won,    color: "text-emerald-400" },
              { label: "Perdidos",       value: stats.lost,   color: "text-red-400" },
            ].map((s) => (
              <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-gray-500 text-xs uppercase tracking-wider mb-1">{s.label}</p>
                <p className={`text-3xl font-black tabular-nums ${s.color}`}>{s.value.toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          {/* Tab headers */}
          <div className="flex border-b border-gray-800">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex-1 px-4 py-4 text-sm font-medium transition-colors ${
                  tab === t.id
                    ? "bg-gray-800 text-white border-b-2 border-blue-500"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-6">
            {tab === "upload" && <UploadTab onDone={loadStats} />}
            {tab === "add"    && <AddLeadTab meta={meta} onDone={loadStats} />}
            {tab === "manage" && <ManageTab onDone={loadStats} />}
            {tab === "agents" && <AgentsTab onDone={loadStats} />}
            {tab === "slack"  && <SlackTab />}
          </div>
        </div>

      </main>
    </div>
  );
}
