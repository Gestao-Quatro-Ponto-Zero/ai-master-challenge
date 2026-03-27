import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, type LucideIcon } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: { value: string; positive: boolean };
  icon: LucideIcon;
  variant?: "default" | "success" | "warning" | "destructive";
}

const variantStyles = {
  default: { card: "", iconBg: "bg-primary/10 text-primary" },
  success: { card: "border-success/30 bg-success/5", iconBg: "bg-success/10 text-success" },
  warning: { card: "border-warning/30 bg-warning/5", iconBg: "bg-warning/10 text-warning" },
  destructive: { card: "border-destructive/30 bg-destructive/5", iconBg: "bg-destructive/10 text-destructive" },
};

export function KPICard({ title, value, subtitle, trend, icon: Icon, variant = "default" }: KPICardProps) {
  const styles = variantStyles[variant];

  return (
    <Card className={cn("p-5 min-w-0", styles.card)}>
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 min-w-0 flex-1">
          <p className="text-xs text-muted-foreground truncate">{title}</p>
          <p className="text-lg font-bold whitespace-nowrap">{value}</p>
          {subtitle && <p className="text-xs text-muted-foreground truncate">{subtitle}</p>}
          {trend && (
            <div className={cn("flex items-center gap-1 text-xs font-medium", trend.positive ? "text-success" : "text-destructive")}>
              {trend.positive ? <TrendingUp className="h-3 w-3 shrink-0" /> : <TrendingDown className="h-3 w-3 shrink-0" />}
              <span className="truncate">{trend.value}</span>
            </div>
          )}
        </div>
        <div className={cn("rounded-lg p-2.5 shrink-0", styles.iconBg)}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </Card>
  );
}
