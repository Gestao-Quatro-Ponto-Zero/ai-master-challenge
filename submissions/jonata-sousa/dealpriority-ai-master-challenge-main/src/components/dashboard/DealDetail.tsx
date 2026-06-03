import { X, TrendingUp, AlertTriangle, Lightbulb, Building2, User, MapPin, Package, Layers, Hash } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PriorityBadge } from "./PriorityBadge";
import type { Deal } from "@/types/deal";

interface Props {
  deal: Deal;
  onClose: () => void;
}

export function DealDetail({ deal: d, onClose }: Props) {
  const scoreColor =
    d.priority_score >= 40 ? "text-primary" : d.priority_score >= 25 ? "text-warning" : "text-muted-foreground";
  const scoreBg =
    d.priority_score >= 40 ? "from-primary/5 to-primary/10" : d.priority_score >= 25 ? "from-warning/5 to-warning/10" : "from-muted/30 to-muted/50";

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-md bg-card border-l shadow-2xl z-50 animate-slide-in-right flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b bg-muted/30">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">Oportunidade</p>
          <h2 className="text-base font-bold text-foreground mt-0.5">{d.account || d.opportunity_id}</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full hover:bg-muted">
          <X className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Score Hero */}
        <div className={`mx-6 mt-6 rounded-xl bg-gradient-to-br ${scoreBg} p-6 text-center space-y-3 border`}>
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest">
            Priority Score
          </span>
          <div className={`text-5xl font-extrabold tracking-tight ${scoreColor}`}>
            {d.priority_score.toFixed(1)}
          </div>
          <div className="w-full h-2 rounded-full bg-background overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                d.priority_score >= 40 ? "bg-primary" : d.priority_score >= 25 ? "bg-warning" : "bg-muted-foreground"
              }`}
              style={{ width: `${Math.min(d.priority_score, 100)}%` }}
            />
          </div>
          <PriorityBadge label={d.priority_label} size="md" />
        </div>

        {/* Info */}
        <div className="px-6 pt-6 pb-4">
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest mb-3">Informações do Deal</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <InfoItem icon={Hash} label="ID" value={d.opportunity_id} />
            <InfoItem icon={Building2} label="Conta" value={d.account || "—"} />
            <InfoItem icon={User} label="Vendedor" value={d.sales_agent} />
            <InfoItem icon={User} label="Gestor" value={d.manager} />
            <InfoItem icon={MapPin} label="Região" value={d.regional_office} />
            <InfoItem icon={Package} label="Produto" value={d.product} />
            <InfoItem icon={Layers} label="Estágio" value={d.deal_stage} />
            {/* engage_date and close_value removed — not in DB */}
          </div>
        </div>

        {/* Sections */}
        <div className="px-6 space-y-4 pb-8">
          {/* Positive */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <div className="h-6 w-6 rounded-md bg-success-muted flex items-center justify-center">
                <TrendingUp className="h-3.5 w-3.5 text-success" />
              </div>
              <span className="text-[11px] font-semibold text-success uppercase tracking-widest">Pontos Fortes</span>
            </div>
            <div className="space-y-2">
              {[d.positive_factor_1, d.positive_factor_2].filter(Boolean).map((r, i) => (
                <div key={i} className="flex items-start gap-3 rounded-lg bg-success-muted/60 border border-success/10 p-3">
                  <div className="h-1.5 w-1.5 rounded-full bg-success mt-1.5 shrink-0" />
                  <span className="text-sm text-foreground leading-relaxed">{r}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Risks */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <div className="h-6 w-6 rounded-md bg-destructive/10 flex items-center justify-center">
                <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
              </div>
              <span className="text-[11px] font-semibold text-destructive uppercase tracking-widest">Riscos Identificados</span>
            </div>
            <div className="space-y-2">
              {[d.risk_factor_1, d.risk_factor_2].filter(Boolean).map((r, i) => (
                <div key={i} className="flex items-start gap-3 rounded-lg bg-destructive/5 border border-destructive/10 p-3">
                  <div className="h-1.5 w-1.5 rounded-full bg-destructive mt-1.5 shrink-0" />
                  <span className="text-sm text-foreground leading-relaxed">{r}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Action */}
          <section>
            <div className="flex items-center gap-2 mb-2">
              <div className="h-6 w-6 rounded-md bg-accent flex items-center justify-center">
                <Lightbulb className="h-3.5 w-3.5 text-primary" />
              </div>
              <span className="text-[11px] font-semibold text-primary uppercase tracking-widest">Ação Recomendada</span>
            </div>
            <div className="rounded-lg border-2 border-primary/15 bg-accent p-4">
              <p className="text-sm font-medium text-foreground leading-relaxed">{d.recommended_action}</p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ icon: Icon, label, value }: { icon: typeof Hash; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <Icon className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
      <div className="min-w-0">
        <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
        <p className="text-sm font-medium text-foreground truncate">{value}</p>
      </div>
    </div>
  );
}
