"use client";

import { CircleCheck, CircleX, Eye, EyeOff, KeyRound, LoaderCircle, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import {
  clearSettings,
  DEFAULT_SETTINGS,
  EFFORTS,
  KEY_HEADER,
  loadSettings,
  MODELS,
  saveSettings,
  type AgentSettings,
} from "@/lib/agent/config";

type Status = { kind: "idle" } | { kind: "busy" } | { kind: "ok"; text: string } | { kind: "error"; text: string };

/** Configuração da API do Claude: cada usuário usa a própria chave, guardada só no navegador. */
export function SettingsForm() {
  const [settings, setSettings] = useState<AgentSettings>(DEFAULT_SETTINGS);
  const [showKey, setShowKey] = useState(false);
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  useEffect(() => {
    // Lê o que já está salvo neste navegador depois da hidratação.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSettings(loadSettings());
  }, []);

  const update = (patch: Partial<AgentSettings>) => {
    setSettings((s) => ({ ...s, ...patch }));
    setStatus({ kind: "idle" });
  };

  function save(event: React.FormEvent) {
    event.preventDefault();
    const ok = saveSettings({ ...settings, apiKey: settings.apiKey.trim() });
    setStatus(ok ? { kind: "ok", text: "Configurações salvas neste navegador." } : { kind: "error", text: "O navegador bloqueou o armazenamento local." });
  }

  async function test() {
    if (!settings.apiKey.trim()) {
      setStatus({ kind: "error", text: "Informe a chave antes de testar." });
      return;
    }
    setStatus({ kind: "busy" });
    try {
      const response = await fetch("/api/agente/teste", {
        method: "POST",
        headers: { "content-type": "application/json", [KEY_HEADER]: settings.apiKey.trim() },
        body: JSON.stringify({ modelo: settings.model }),
      });
      const data = (await response.json()) as { ok?: boolean; modelo?: string; erro?: string };
      setStatus(data.ok ? { kind: "ok", text: `Conexão ok: ${data.modelo} disponível para esta chave.` } : { kind: "error", text: data.erro ?? "Falha no teste." });
    } catch {
      setStatus({ kind: "error", text: "Não foi possível testar a conexão." });
    }
  }

  function remove() {
    clearSettings();
    setSettings(DEFAULT_SETTINGS);
    setStatus({ kind: "ok", text: "Chave e configurações removidas deste navegador." });
  }

  return (
    <form onSubmit={save} className="space-y-6">
      <section className="card space-y-4 p-6">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-full bg-hover text-secondary">
            <KeyRound className="size-5" aria-hidden />
          </span>
          <div>
            <h2 className="text-[18px] font-semibold">Chave da API da Anthropic</h2>
            <p className="text-[13px] text-secondary">Cada usuário usa a própria chave. A Régua não tem chave própria.</p>
          </div>
        </div>
        <label className="block">
          <span className="field">Chave</span>
          <span className="relative mt-1.5 block">
            <input
              type={showKey ? "text" : "password"}
              value={settings.apiKey}
              onChange={(e) => update({ apiKey: e.target.value })}
              placeholder="sk-ant-…"
              autoComplete="off"
              spellCheck={false}
              className="h-11 w-full rounded-full border border-line bg-surface pr-12 pl-4 font-mono text-[14px] placeholder:text-secondary focus:border-moment focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setShowKey((v) => !v)}
              aria-label={showKey ? "Ocultar chave" : "Mostrar chave"}
              className="absolute top-1/2 right-1 grid size-9 -translate-y-1/2 place-items-center rounded-full text-secondary hover:bg-hover"
            >
              {showKey ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
            </button>
          </span>
        </label>
        <p className="text-[13px] text-secondary">
          A chave fica salva só neste navegador. Ela vai ao servidor da Régua apenas junto de cada pergunta ao agente, que a repassa à
          Anthropic na mesma hora e não a guarda. Crie e gerencie chaves em{" "}
          <a href="https://platform.claude.com/settings/keys" target="_blank" rel="noreferrer" className="underline underline-offset-4">
            platform.claude.com
          </a>
          ; o consumo é cobrado na conta dona da chave.
        </p>
      </section>

      <section className="card space-y-4 p-6">
        <h2 className="text-[18px] font-semibold">Modelo</h2>
        <div role="radiogroup" aria-label="Modelo" className="grid gap-3 md:grid-cols-3">
          {MODELS.map((m) => (
            <label
              key={m.id}
              className={`cursor-pointer rounded-xl border p-4 transition-colors ${settings.model === m.id ? "border-moment bg-moment-soft" : "border-line hover:bg-hover"}`}
            >
              <input type="radio" name="modelo" value={m.id} checked={settings.model === m.id} onChange={() => update({ model: m.id })} className="sr-only" />
              <span className="block text-[15px] font-semibold">{m.label}</span>
              <span className="block text-[13px] text-secondary">{m.hint}</span>
            </label>
          ))}
        </div>

        <h2 className="pt-2 text-[18px] font-semibold">Esforço de raciocínio</h2>
        <div role="radiogroup" aria-label="Esforço" className="inline-flex flex-wrap gap-1 rounded-full border border-line p-1">
          {EFFORTS.map((e) => (
            <label
              key={e.id}
              title={e.hint}
              className={`cursor-pointer rounded-full px-4 py-2 text-[14px] ${settings.effort === e.id ? "bg-primary font-semibold text-surface" : "text-secondary hover:bg-hover"}`}
            >
              <input type="radio" name="esforco" value={e.id} checked={settings.effort === e.id} onChange={() => update({ effort: e.id })} className="sr-only" />
              {e.label}
            </label>
          ))}
        </div>

      </section>

      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" className="h-11 cursor-pointer rounded-full bg-primary px-6 text-[15px] font-semibold text-surface hover:opacity-90">
          Salvar
        </button>
        <button
          type="button"
          onClick={test}
          disabled={status.kind === "busy"}
          className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-full border border-line bg-surface px-5 text-[15px] font-semibold hover:bg-hover disabled:opacity-60"
        >
          {status.kind === "busy" && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
          Testar conexão
        </button>
        <button type="button" onClick={remove} className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-full px-4 text-[14px] text-secondary hover:bg-hover hover:text-stalled">
          <Trash2 className="size-4" aria-hidden /> Remover chave
        </button>
      </div>

      <p role="status" aria-live="polite" className="min-h-6 text-[14px]">
        {status.kind === "ok" && (
          <span className="inline-flex items-center gap-2 text-moment">
            <CircleCheck className="size-4" aria-hidden /> {status.text}
          </span>
        )}
        {status.kind === "error" && (
          <span className="inline-flex items-center gap-2 text-stalled">
            <CircleX className="size-4" aria-hidden /> {status.text}
          </span>
        )}
      </p>
    </form>
  );
}
