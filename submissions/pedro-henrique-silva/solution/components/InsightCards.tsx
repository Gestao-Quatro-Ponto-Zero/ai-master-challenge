type InsightCardsProps = {
  recoverableHours: number;
  recoverableBrl: number;
  deflectionRate: number;
  confidenceAvg: number;
};

export function InsightCards({
  recoverableHours,
  recoverableBrl,
  deflectionRate,
  confidenceAvg,
}: InsightCardsProps) {
  const cards = [
    {
      title: "Horas recuperáveis",
      value: `${recoverableHours.toLocaleString("pt-BR")}h`,
      hint: "Estimativa mensal",
    },
    {
      title: "Impacto financeiro",
      value: `R$ ${recoverableBrl.toLocaleString("pt-BR")}`,
      hint: "Potencial de redução",
    },
    {
      title: "Taxa de deflexão",
      value: `${Math.round(deflectionRate * 100)}%`,
      hint: "Resoluções sem abrir ticket",
    },
    {
      title: "Confiança média RAG",
      value: `${Math.round(confidenceAvg * 100)}%`,
      hint: "Qualidade percebida da sugestão",
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <article key={card.title} className="card p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">{card.title}</p>
          <p className="mt-2 text-2xl font-semibold text-[hsl(var(--primary))]">{card.value}</p>
          <p className="mt-1 text-xs text-slate-600">{card.hint}</p>
        </article>
      ))}
    </div>
  );
}
