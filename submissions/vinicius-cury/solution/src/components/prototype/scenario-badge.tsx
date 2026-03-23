"use client";

import { cn } from "@/lib/utils";
import { SCENARIO_LABELS } from "@/lib/routing/taxonomy";

interface ScenarioBadgeProps {
  scenario: string;
  className?: string;
}

const SCENARIO_COLORS: Record<string, string> = {
  acelerar: "bg-red-100 text-red-800 border-red-200",
  desacelerar: "bg-blue-100 text-blue-800 border-blue-200",
  redirecionar: "bg-yellow-100 text-yellow-800 border-yellow-200",
  quarentena: "bg-gray-100 text-gray-800 border-gray-200",
  manter: "bg-green-100 text-green-800 border-green-200",
  liberar: "bg-emerald-100 text-emerald-800 border-emerald-200",
};

export function ScenarioBadge({ scenario, className }: ScenarioBadgeProps) {
  const info = SCENARIO_LABELS[scenario];
  const colorClass = SCENARIO_COLORS[scenario] || SCENARIO_COLORS.manter;
  const label = info?.label || scenario;

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold animate-in fade-in zoom-in-95 duration-300",
        colorClass,
        className
      )}
    >
      {label}
    </span>
  );
}
