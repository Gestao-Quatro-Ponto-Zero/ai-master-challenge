"use client";

import { scoreColor, scoreLabel } from "@/lib/scoring";

interface ScoreBadgeProps {
  score: number;
  onClick?: () => void;
  size?: "sm" | "md";
}

const colorClasses = {
  green: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40 hover:bg-emerald-500/30",
  yellow: "bg-amber-500/20 text-amber-400 border-amber-500/40 hover:bg-amber-500/30",
  red: "bg-red-500/20 text-red-400 border-red-500/40 hover:bg-red-500/30",
};

export function ScoreBadge({ score, onClick, size = "md" }: ScoreBadgeProps) {
  const color = scoreColor(score);
  const label = scoreLabel(score);
  const sizeClasses = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1";

  return (
    <button
      onClick={onClick}
      title={`${label} — clique para ver breakdown`}
      className={`
        inline-flex items-center gap-1.5 rounded-full border font-semibold
        transition-colors cursor-pointer
        ${sizeClasses}
        ${colorClasses[color]}
      `}
    >
      <span className="tabular-nums text-base font-bold">{score}</span>
      <span className="hidden sm:inline opacity-70">/100</span>
    </button>
  );
}
