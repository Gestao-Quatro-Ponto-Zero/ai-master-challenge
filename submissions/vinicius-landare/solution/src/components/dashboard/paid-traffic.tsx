"use client";

interface PaidTrafficProps {
  summary: {
    kpis: {
      total_sponsored_posts: number;
      avg_engagement_sponsored: number;
      avg_engagement_organic: number;
      lift_geral_pp: number;
      avg_cpe_score: number;
      significance: { is_significant: boolean; p_value: number };
    };
    pct_roi_positive: number;
  };
  campaignRoi: {
    data: Array<{
      sponsor_category: string;
      posts: number;
      avg_engagement: number;
      lift_vs_organic: number;
      roi_positive: boolean;
    }>;
  };
  budgetAllocation: {
    invest: Array<{ sponsor_category: string; platform: string; lift: number; posts: number }>;
    cut: Array<{ sponsor_category: string; platform: string; lift: number; posts: number }>;
    estimated_lift_if_reallocated: number;
  };
}

const CAT_LABELS: Record<string, string> = {
  cosmetics: "Cosméticos",
  food: "Alimentação",
  travel: "Turismo",
  electronics: "Eletrônicos",
  gaming: "Games",
  fashion: "Moda",
};

export function PaidTraffic({ summary, campaignRoi, budgetAllocation }: PaidTrafficProps) {
  const kpis = summary?.kpis;
  const roiData = campaignRoi?.data || [];
  const sorted = [...roiData].sort((a, b) => b.lift_vs_organic - a.lift_vs_organic);

  // Valor maximo para escala das barras
  const maxLift = Math.max(...sorted.map((d) => Math.abs(d.lift_vs_organic)), 0.01);

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KPICard label="Campanhas analisadas" value={kpis?.total_sponsored_posts?.toLocaleString("pt-BR") || "—"} />
        <KPICard
          label="Lift geral"
          value={`${kpis?.lift_geral_pp > 0 ? "+" : ""}${kpis?.lift_geral_pp?.toFixed(2) || "0"}%`}
          badge={kpis?.significance?.is_significant ? "significativo" : "não significativo"}
          badgeColor={kpis?.significance?.is_significant ? "emerald" : "amber"}
        />
        <KPICard label="CPE médio" value={kpis?.avg_cpe_score?.toFixed(1) || "—"} />
        <KPICard label="ROI positivo" value={`${summary?.pct_roi_positive?.toFixed(0) || "0"}%`} />
      </div>

      {/* Lift por Categoria — tabela visual */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-base font-semibold text-[#0F1B2D] mb-1">Lift de Patrocínio por Categoria</h3>
        <p className="text-xs text-slate-500 mb-4">Diferença de engagement (patrocinado - orgânico) por categoria de sponsor</p>

        <div className="space-y-2">
          {sorted.map((entry, i) => {
            const pct = (entry.lift_vs_organic / maxLift) * 100;
            const isPositive = entry.lift_vs_organic >= 0;
            const label = CAT_LABELS[entry.sponsor_category] || entry.sponsor_category;

            return (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-slate-600 w-24 text-right shrink-0">{label}</span>
                <div className="flex-1 h-7 bg-slate-50 rounded-lg overflow-hidden relative flex items-center">
                  {/* Linha central (zero) */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-200 z-10" />

                  {isPositive ? (
                    <div
                      className="absolute left-1/2 h-5 bg-emerald-400 rounded-r-md"
                      style={{ width: `${Math.abs(pct) / 2}%` }}
                    />
                  ) : (
                    <div
                      className="absolute right-1/2 h-5 bg-red-400 rounded-l-md"
                      style={{ width: `${Math.abs(pct) / 2}%` }}
                    />
                  )}
                </div>
                <span className={`text-xs font-semibold w-16 text-right shrink-0 ${isPositive ? "text-emerald-600" : "text-red-600"}`}>
                  {isPositive ? "+" : ""}{entry.lift_vs_organic.toFixed(3)}%
                </span>
                <span className="text-[10px] text-slate-400 w-16 shrink-0">{entry.posts} posts</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top e Bottom Campanhas */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-emerald-800 mb-3">Melhores Campanhas (investir)</h3>
          <div className="space-y-2">
            {(budgetAllocation?.invest || []).map((c, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-emerald-50 rounded-lg text-xs">
                <span className="font-medium text-emerald-900">{CAT_LABELS[c.sponsor_category] || c.sponsor_category} / {c.platform}</span>
                <span className="text-emerald-600 font-semibold">+{c.lift.toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h3 className="text-sm font-semibold text-red-800 mb-3">Piores Campanhas (cortar)</h3>
          <div className="space-y-2">
            {(budgetAllocation?.cut || []).map((c, i) => (
              <div key={i} className="flex items-center justify-between p-2.5 bg-red-50 rounded-lg text-xs">
                <span className="font-medium text-red-900">{CAT_LABELS[c.sponsor_category] || c.sponsor_category} / {c.platform}</span>
                <span className="text-red-600 font-semibold">{c.lift.toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recomendação de Budget */}
      {budgetAllocation?.estimated_lift_if_reallocated > 0 && (
        <div className="bg-[#0F1B2D]/5 rounded-2xl border border-[#0F1B2D]/10 p-6">
          <h3 className="text-sm font-semibold text-[#0F1B2D] mb-2">Recomendação de Realocação</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Realocando budget das piores campanhas para as melhores, o lift estimado total seria de{" "}
            <span className="font-bold text-[#E8734A]">+{budgetAllocation.estimated_lift_if_reallocated.toFixed(2)}%</span>.
          </p>
        </div>
      )}
    </div>
  );
}

function KPICard({ label, value, badge, badgeColor }: {
  label: string; value: string; badge?: string; badgeColor?: "emerald" | "amber";
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
      <p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p>
      <p className="text-xl font-bold text-[#0F1B2D] mt-1">{value}</p>
      {badge && (
        <span className={`text-[9px] px-1.5 py-0.5 rounded-full mt-1 inline-block font-medium ${
          badgeColor === "emerald" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
        }`}>
          {badge}
        </span>
      )}
    </div>
  );
}
