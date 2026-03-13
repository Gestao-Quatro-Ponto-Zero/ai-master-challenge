"use client";

import { type ScoreComponent } from "@/lib/scoring";

interface ScoreBreakdownProps {
  score: number;
  components: ScoreComponent[];
  dealName: string;
  onClose: () => void;
}

const componentColors = ["blue", "purple", "cyan", "orange"] as const;

const colorMap = {
  blue:   "bg-blue-500/10   text-blue-400   border-blue-500/25",
  purple: "bg-purple-500/10 text-purple-400 border-purple-500/25",
  cyan:   "bg-cyan-500/10   text-cyan-400   border-cyan-500/25",
  orange: "bg-orange-500/10 text-orange-400 border-orange-500/25",
};
const barColorMap = {
  blue:   "bg-blue-500",
  purple: "bg-purple-500",
  cyan:   "bg-cyan-500",
  orange: "bg-orange-500",
};
const labelBg = {
  blue:   "bg-blue-500/15 text-blue-300",
  purple: "bg-purple-500/15 text-purple-300",
  cyan:   "bg-cyan-500/15 text-cyan-300",
  orange: "bg-orange-500/15 text-orange-300",
};

// Static guide per component — explains the scoring criteria to a junior rep
const componentGuide: Record<string, { icon: string; guide: string }> = {
  "Stage + Momentum": {
    icon: "⚡",
    guide:
      "Quanto mais recente o engajamento, mais quente o lead. " +
      "≤30 dias em Engaging = máximo (30pts). 31–60 dias = esfriando (22pts). " +
      "61–90 dias = ciclo longo (12pts). +90 dias = deal zumbi (4pts). " +
      "Ciclo médio de fechamento é 52 dias — acima de 78 dias a chance de fechar cai muito. " +
      "Prospecting com conta = 10pts. Sem conta = 2pts.",
  },
  "Produto / Ticket": {
    icon: "💰",
    guide:
      "Produtos mais caros têm maior impacto na receita da empresa. " +
      "GTK 500 ($26.768) = 25pts (produto top). GTX Plus Pro ($5.482) = 22pts. " +
      "GTX Pro = 20pts. MG Advanced = 16pts. GTX Plus Basic = 12pts. " +
      "GTX Basic = 8pts. MG Special ($55) = 3pts.",
  },
  "Qualidade da Conta": {
    icon: "🏢",
    guide:
      "Empresas maiores têm mais orçamento e menor risco. " +
      "Enterprise (receita +$2B) = 25pts. Large ($500M–2B) = 18pts. " +
      "Mid-market ($100–500M) = 11pts. SMB (abaixo de $100M) = 6pts. " +
      "Sem conta identificada = 0pts (penalidade total). Subsidiária de grupo maior = +3pts bônus.",
  },
  "Win Rate do Vendedor": {
    icon: "🎯",
    guide:
      "Calculado a partir do histórico real de cada vendedor no pipeline. " +
      "Win Rate = vitórias (Won) ÷ total de deals encerrados (Won + Perdidos). " +
      "Acima de 70% = 20pts (excelente). 50–70% = 15pts. " +
      "30–50% = 10pts. Abaixo de 30% = 5pts.",
  },
};

function ScoreRing({ score }: { score: number }) {
  const color =
    score >= 70 ? "#34d399" : score >= 40 ? "#fbbf24" : "#f87171";
  const r = 28;
  const circ = 2 * Math.PI * r;
  const dash = circ * (score / 100);

  return (
    <div className="relative flex items-center justify-center w-20 h-20 shrink-0">
      <svg className="absolute inset-0 -rotate-90" width="80" height="80">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#1f2937" strokeWidth="6" />
        <circle
          cx="40" cy="40" r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="text-center z-10">
        <div className="text-2xl font-black text-white tabular-nums leading-none">{score}</div>
        <div className="text-[10px] text-gray-500 leading-none mt-0.5">/ 100</div>
      </div>
    </div>
  );
}

export function ScoreBreakdown({
  score,
  components,
  dealName,
  onClose,
}: ScoreBreakdownProps) {
  const priorityLabel =
    score >= 70 ? "Alta prioridade"
    : score >= 40 ? "Média prioridade"
    : "Baixa prioridade";
  const priorityColor =
    score >= 70 ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
    : score >= 40 ? "text-amber-400 bg-amber-500/10 border-amber-500/30"
    : "text-red-400 bg-red-500/10 border-red-500/30";

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      <div
        className="relative bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl max-h-[92vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header — sticky */}
        <div className="flex items-start justify-between p-6 border-b border-gray-800 sticky top-0 bg-gray-900 z-10 rounded-t-2xl">
          <div className="flex items-center gap-4">
            <ScoreRing score={score} />
            <div className="min-w-0">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-0.5">Score do Lead</p>
              <h3 className="text-white font-semibold text-base leading-snug truncate max-w-[220px]">
                {dealName}
              </h3>
              <span className={`inline-flex mt-1.5 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${priorityColor}`}>
                {priorityLabel}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 transition-colors p-1 shrink-0 mt-1"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Intro callout */}
        <div className="px-6 pt-5 pb-1">
          <p className="text-gray-400 text-xs leading-relaxed bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
            O score soma até <span className="text-white font-medium">100 pontos</span> divididos em 4 componentes.
            Quanto maior, <span className="text-white font-medium">mais vale priorizar este lead agora</span>.
            Expanda o &quot;Como é calculado&quot; em cada bloco para entender os critérios.
          </p>
        </div>

        {/* Score components */}
        <div className="p-6 pt-4 space-y-4">
          {components.map((comp, i) => {
            const color = componentColors[i % componentColors.length];
            const pct = (comp.pts / comp.maxPts) * 100;
            const guide = componentGuide[comp.label];

            return (
              <div key={comp.label} className={`rounded-xl border p-4 ${colorMap[color]}`}>
                {/* Component header row */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-base leading-none">{guide?.icon ?? "•"}</span>
                    <span className="font-semibold text-sm">{comp.label}</span>
                  </div>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold tabular-nums ${labelBg[color]}`}>
                    {comp.pts} / {comp.maxPts} pts
                  </span>
                </div>

                {/* Progress bar */}
                <div className="h-2 rounded-full bg-white/10 mb-3">
                  <div
                    className={`h-full rounded-full transition-all ${barColorMap[color]}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>

                {/* Detail — what this specific deal scored */}
                <p className="text-sm font-medium opacity-90 mb-2 leading-snug">
                  {comp.detail}
                </p>

                {/* Expandable criteria guide */}
                {guide && (
                  <details className="group">
                    <summary className="text-xs opacity-40 group-open:opacity-60 cursor-pointer hover:opacity-70 transition-opacity select-none list-none flex items-center gap-1">
                      <span className="group-open:rotate-90 inline-block transition-transform text-[10px]">▶</span>
                      Como é calculado
                    </summary>
                    <p className="text-xs opacity-55 mt-2 leading-relaxed pl-3 border-l-2 border-white/10">
                      {guide.guide}
                    </p>
                  </details>
                )}
              </div>
            );
          })}
        </div>

        {/* Action recommendation */}
        <div className="mx-6 mb-5 p-4 rounded-xl bg-gray-800/60 border border-gray-700/50">
          <p className="text-xs font-semibold text-white mb-1">💡 O que fazer com este lead?</p>
          <p className="text-xs text-gray-400 leading-relaxed">
            {score >= 70
              ? "Score alto — priorize contato hoje. Verifique próximos passos e avance para proposta ou fechamento."
              : score >= 40
              ? "Score médio — mantenha contato ativo. Identifique o maior bloqueador (tempo em stage, conta, produto) e resolva antes de entrar na zona de risco."
              : "Score baixo — revise a qualificação antes de investir mais tempo. Analise: o produto é adequado? A conta foi identificada? O deal está parado há quanto tempo?"}
          </p>
        </div>

        <div className="pb-4 text-center">
          <p className="text-xs text-gray-600">Clique fora ou no ✕ para fechar</p>
        </div>
      </div>
    </div>
  );
}
