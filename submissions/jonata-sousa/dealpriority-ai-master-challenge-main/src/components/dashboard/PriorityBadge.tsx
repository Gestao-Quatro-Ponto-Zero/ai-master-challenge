import { cn } from "@/lib/utils";
import { Zap, Clock, ArrowDown } from "lucide-react";

interface Props {
  label: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}

const config: Record<string, { bg: string; text: string; border: string; icon: typeof Zap }> = {
  "Foco Agora": {
    bg: "bg-priority-focus-bg",
    text: "text-priority-focus",
    border: "border-priority-focus-border",
    icon: Zap,
  },
  Nutrir: {
    bg: "bg-priority-nurture-bg",
    text: "text-priority-nurture",
    border: "border-priority-nurture-border",
    icon: Clock,
  },
  "Baixa Prioridade": {
    bg: "bg-priority-low-bg",
    text: "text-priority-low",
    border: "border-priority-low-border",
    icon: ArrowDown,
  },
};

export function PriorityBadge({ label, className, size = "sm" }: Props) {
  const c = config[label] || { bg: "bg-muted", text: "text-muted-foreground", border: "border-border", icon: ArrowDown };
  const Icon = c.icon;

  const sizeClasses = {
    sm: "px-2.5 py-1 text-xs gap-1",
    md: "px-3 py-1.5 text-sm gap-1.5",
    lg: "px-4 py-2 text-sm gap-2",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border font-semibold whitespace-nowrap",
        c.bg, c.text, c.border,
        sizeClasses[size],
        className
      )}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} />
      {label}
    </span>
  );
}
