import { Target, TrendingUp, Zap, Clock, ArrowDown } from "lucide-react";
import type { Deal } from "@/types/deal";

interface Props {
  deals: Deal[];
}

export function KPICards({ deals }: Props) {
  const total = deals.length;
  const avg = total > 0 ? deals.reduce((s, d) => s + d.priority_score, 0) / total : 0;
  const focus = deals.filter((d) => d.priority_label === "Foco Agora").length;
  const nurture = deals.filter((d) => d.priority_label === "Nutrir").length;
  const low = deals.filter((d) => d.priority_label === "Baixa Prioridade").length;

  const cards = [
    {
      label: "Pipeline Ativo",
      value: total.toLocaleString("pt-BR"),
      sub: "oportunidades",
      icon: Target,
      accent: "bg-primary/10 text-primary",
    },
    {
      label: "Score Médio",
      value: avg.toFixed(1),
      sub: "pontos",
      icon: TrendingUp,
      accent: "bg-primary/10 text-primary",
    },
    {
      label: "Foco Agora",
      value: focus.toLocaleString("pt-BR"),
      sub: `${total > 0 ? ((focus / total) * 100).toFixed(0) : 0}% do pipeline`,
      icon: Zap,
      accent: "bg-priority-focus-bg text-priority-focus",
    },
    {
      label: "Nutrir",
      value: nurture.toLocaleString("pt-BR"),
      sub: `${total > 0 ? ((nurture / total) * 100).toFixed(0) : 0}% do pipeline`,
      icon: Clock,
      accent: "bg-priority-nurture-bg text-priority-nurture",
    },
    {
      label: "Baixa Prioridade",
      value: low.toLocaleString("pt-BR"),
      sub: `${total > 0 ? ((low / total) * 100).toFixed(0) : 0}% do pipeline`,
      icon: ArrowDown,
      accent: "bg-priority-low-bg text-priority-low",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {cards.map((c) => (
        <div
          key={c.label}
          className="bg-card rounded-xl border p-5 flex flex-col gap-3 shadow-sm hover:shadow-md transition-all duration-200 group"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest">
              {c.label}
            </span>
            <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${c.accent} transition-transform group-hover:scale-110`}>
              <c.icon className="h-4 w-4" />
            </div>
          </div>
          <div>
            <span className="text-3xl font-extrabold text-foreground tracking-tight">{c.value}</span>
            <p className="text-xs text-muted-foreground mt-0.5">{c.sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
