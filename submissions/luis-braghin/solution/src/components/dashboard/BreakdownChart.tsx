import type { DealBreakdown } from "@/types/deals";
import { HelpCircle } from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";

interface BreakdownChartProps {
  breakdown: DealBreakdown;
}

const labelMap: Record<string, string> = {
  velocity: "Velocidade",
  agentProductAffinity: "Afinidade Vendedor-Produto",
  productSectorFit: "Fit Produto-Setor",
  dealValue: "Valor do Deal",
  accountQuality: "Qualidade da Conta",
  opportunityWindow: "Janela de Oportunidade",
};

const descriptionMap: Record<string, string> = {
  agentProductAffinity: "Win rate histórico deste vendedor com este produto específico. Quanto maior, mais chance de fechar.",
  dealValue: "Valor monetário do deal em escala logarítmica. Deals de maior valor recebem score mais alto.",
  velocity: "Tempo no pipeline. Janela ideal: 14–30 dias (73% win rate histórico). Penalidade progressiva após 138 dias.",
  accountQuality: "Porte da empresa (receita, funcionários) e histórico de deals com esta conta.",
  productSectorFit: "Win rate histórico da combinação deste produto com o setor da conta.",
  opportunityWindow: "Estima se engajar agora resultaria em fechamento num mês de alta conversão (fim de trimestre).",
};

function getBarColor(value: number): string {
  if (value >= 75) return "bg-success";
  if (value >= 50) return "bg-warning";
  return "bg-destructive";
}

export function BreakdownChart({ breakdown }: BreakdownChartProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-3">
        {Object.entries(breakdown).map(([key, value]) => {
          if (value == null) return null;
          const label = labelMap[key] ?? key;
          const description = descriptionMap[key];
          return (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground flex items-center gap-1">
                  {label}
                  {description && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-3 w-3 text-muted-foreground/50 hover:text-muted-foreground cursor-help shrink-0" />
                      </TooltipTrigger>
                      <TooltipContent side="top" className="max-w-[240px] text-xs">
                        {description}
                      </TooltipContent>
                    </Tooltip>
                  )}
                </span>
                <span className="font-medium">{value}</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div
                  className={`h-2 rounded-full transition-all ${getBarColor(value)}`}
                  style={{ width: `${value}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </TooltipProvider>
  );
}