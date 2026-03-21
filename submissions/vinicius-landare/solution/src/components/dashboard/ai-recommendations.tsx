"use client";

import { useState } from "react";

interface Script {
  title: string;
  copy: string;
  visual_spec: string;
  hashtags: string[];
  publish_time: string;
  cta: string;
  thumbnail_description: string;
}

interface StepStatus {
  draft: "idle" | "loading" | "done" | "error";
  critique: "idle" | "loading" | "done" | "error";
  refinement: "idle" | "loading" | "done" | "error";
}

export function AIRecommendations() {
  const [platform, setPlatform] = useState("Instagram");
  const [niche, setNiche] = useState("beauty");
  const [audience, setAudience] = useState("19-25");
  const [scripts, setScripts] = useState<Script[]>([]);
  const [stepStatus, setStepStatus] = useState<StepStatus>({ draft: "idle", critique: "idle", refinement: "idle" });
  const [error, setError] = useState("");
  const [modelsUsed, setModelsUsed] = useState<Record<string, string>>({});

  async function generate() {
    setError("");
    setScripts([]);
    setStepStatus({ draft: "loading", critique: "idle", refinement: "idle" });

    try {
      // Simula progresso visual (a API faz tudo de uma vez)
      setStepStatus({ draft: "loading", critique: "idle", refinement: "idle" });

      const res = await fetch("/api/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: "perfil_demo",
          platform,
          niche,
          audience_age: audience,
          avg_engagement: 19.9,
          top_posts: [
            `Post sobre ${niche} com alta interação (20.3%)`,
            `Carrossel de dicas de ${niche} (20.1%)`,
            `Reels tutorial de ${niche} (20.0%)`,
          ],
          worst_posts: [
            "Foto produto genérica (19.5%)",
            "Repost sem contexto (19.6%)",
            "Texto longo sem visual (19.7%)",
          ],
          peak_hours: ["7h", "11h", "18h", "21h"],
          hashtag_combos: ["#" + niche, "#dicas", "#trending"],
        }),
      });

      const data = await res.json();

      if (data.error) {
        setError(data.error);
        setStepStatus({ draft: "error", critique: "error", refinement: "error" });
        return;
      }

      setModelsUsed(data.models_used || {});
      setStepStatus({ draft: "done", critique: "done", refinement: "done" });
      setScripts(data.scripts?.scripts || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar recomendações");
      setStepStatus({ draft: "error", critique: "error", refinement: "error" });
    }
  }

  return (
    <div className="space-y-4">
      {/* Config */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Gerador de Conteúdo IA</h3>
        <p className="text-xs text-slate-500 mb-4">Pipeline de 3 etapas: Rascunho (Gemini) → Crítica (Claude) → Roteiro Final (Gemini)</p>

        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <label className="text-xs text-slate-500 block mb-1">Plataforma</label>
            <select value={platform} onChange={(e) => setPlatform(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg">
              <option>Instagram</option>
              <option>TikTok</option>
              <option>YouTube</option>
              <option>Bilibili</option>
              <option>RedNote</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Nicho</label>
            <select value={niche} onChange={(e) => setNiche(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg">
              <option value="beauty">Beleza</option>
              <option value="lifestyle">Estilo de Vida</option>
              <option value="tech">Tecnologia</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Público-alvo</label>
            <select value={audience} onChange={(e) => setAudience(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg">
              <option value="13-18">13-18 anos</option>
              <option value="19-25">19-25 anos</option>
              <option value="26-35">26-35 anos</option>
              <option value="36-50">36-50 anos</option>
              <option value="50+">50+ anos</option>
            </select>
          </div>
        </div>

        <button
          onClick={generate}
          disabled={stepStatus.draft === "loading"}
          className="px-6 py-2.5 bg-[#E8734A] text-white text-sm font-medium rounded-lg hover:bg-[#d4653f] transition-colors disabled:opacity-50"
        >
          {stepStatus.draft === "loading" ? "Gerando..." : "Gerar Recomendações"}
        </button>
      </div>

      {/* Steps Progress */}
      {stepStatus.draft !== "idle" && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-[#0F1B2D] mb-3">Progresso</h3>
          <div className="space-y-2">
            <StepIndicator
              step="1"
              label="Rascunho — gerando ideias criativas"
              model={modelsUsed.draft}
              status={stepStatus.draft}
            />
            <StepIndicator
              step="2"
              label="Crítica — avaliando com dados"
              model={modelsUsed.critique}
              status={stepStatus.critique}
            />
            <StepIndicator
              step="3"
              label="Refinamento — criando roteiros finais"
              model={modelsUsed.refinement}
              status={stepStatus.refinement}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-xs text-red-700">{error}</p>
          <p className="text-[10px] text-red-500 mt-1">Verifique se a OPENROUTER_API_KEY está configurada no .env</p>
        </div>
      )}

      {/* Scripts Output */}
      {scripts.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-base font-semibold text-[#0F1B2D]">Roteiros Prontos para Produção</h3>
          {scripts.map((script, i) => (
            <div key={i} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="bg-[#E8734A] text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center">{i + 1}</span>
                <h4 className="font-semibold text-sm text-[#0F1B2D]">{script.title}</h4>
              </div>

              <div className="space-y-3">
                <ScriptSection label="Copy (legenda)" content={script.copy} />
                <ScriptSection label="Especificação Visual" content={script.visual_spec} />
                <ScriptSection label="CTA" content={script.cta} />
                <ScriptSection label="Thumbnail / Capa" content={script.thumbnail_description} />

                <div className="flex flex-wrap gap-2">
                  {script.hashtags.map((tag, j) => (
                    <span key={j} className="px-2 py-0.5 bg-[#0F1B2D]/5 text-[#0F1B2D] rounded-full text-[10px] font-medium">
                      {tag}
                    </span>
                  ))}
                </div>

                <p className="text-[10px] text-slate-400">Horário ideal: {script.publish_time}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StepIndicator({ step, label, model, status }: {
  step: string; label: string; model?: string; status: "idle" | "loading" | "done" | "error";
}) {
  const icons = {
    idle: "○",
    loading: "◎",
    done: "✓",
    error: "✗",
  };
  const colors = {
    idle: "text-slate-300",
    loading: "text-[#E8734A] animate-pulse",
    done: "text-emerald-500",
    error: "text-red-500",
  };

  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className={`text-lg font-bold ${colors[status]}`}>{icons[status]}</span>
      <div className="flex-1">
        <p className="text-xs text-[#0F1B2D]">Step {step}: {label}</p>
        {model && status === "done" && (
          <p className="text-[10px] text-slate-400">Modelo: {model}</p>
        )}
      </div>
    </div>
  );
}

function ScriptSection({ label, content }: { label: string; content: string }) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-xs text-[#0F1B2D] whitespace-pre-wrap leading-relaxed">{content}</p>
    </div>
  );
}
