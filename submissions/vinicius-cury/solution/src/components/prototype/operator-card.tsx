"use client";

import { cn } from "@/lib/utils";
import { User } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────

interface Operator {
  id: string;
  name: string;
  status: string;
  level?: string;
  active_tickets: number;
  max_capacity: number;
  specialties: string[] | null;
  total_resolved: number;
}

interface OperatorCardProps {
  operator: Operator;
  isSelected: boolean;
  onClick: () => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────

const LEVEL_CONFIG: Record<
  string,
  { label: string; badgeClass: string }
> = {
  junior: { label: "Junior", badgeClass: "bg-blue-100 text-blue-700" },
  senior: { label: "Senior", badgeClass: "bg-purple-100 text-purple-700" },
  lead: { label: "Lead", badgeClass: "bg-amber-100 text-amber-700" },
};

const STATUS_CONFIG: Record<
  string,
  { label: string; dotClass: string; bgClass: string }
> = {
  available: {
    label: "Disponivel",
    dotClass: "bg-green-500",
    bgClass: "bg-green-100 text-green-800",
  },
  busy: {
    label: "Ocupado",
    dotClass: "bg-yellow-500",
    bgClass: "bg-yellow-100 text-yellow-800",
  },
  offline: {
    label: "Offline",
    dotClass: "bg-gray-400",
    bgClass: "bg-gray-100 text-gray-600",
  },
};

// ─── Workload Bar Colors ────────────────────────────────────────────

function getWorkloadColor(pct: number): { bar: string; text: string } {
  if (pct >= 80) return { bar: "bg-red-500", text: "text-red-700" };
  if (pct >= 60) return { bar: "bg-yellow-500", text: "text-yellow-700" };
  return { bar: "bg-green-500", text: "text-green-700" };
}

// ─── Main Component ─────────────────────────────────────────────────

export function OperatorCard({
  operator,
  isSelected,
  onClick,
}: OperatorCardProps) {
  const statusConfig = STATUS_CONFIG[operator.status] || STATUS_CONFIG.offline;
  const capacityPct =
    operator.max_capacity > 0
      ? (operator.active_tickets / operator.max_capacity) * 100
      : 0;
  const workloadColor = getWorkloadColor(capacityPct);

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full rounded-lg border p-2.5 text-left transition-all hover:bg-muted/50",
        isSelected && "border-primary bg-primary/5 ring-1 ring-primary/20"
      )}
    >
      <div className="flex items-center gap-2">
        {/* Avatar placeholder */}
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
          <User className="h-4 w-4 text-muted-foreground" />
        </div>

        <div className="min-w-0 flex-1">
          {/* Name + level + status */}
          <div className="flex items-center gap-1.5">
            <span className="truncate text-sm font-medium">
              {operator.name}
            </span>
            {operator.level && LEVEL_CONFIG[operator.level] && (
              <span
                className={cn(
                  "rounded px-1 py-0.5 text-[9px] font-semibold",
                  LEVEL_CONFIG[operator.level].badgeClass
                )}
              >
                {LEVEL_CONFIG[operator.level].label}
              </span>
            )}
            <div
              className={cn("h-2 w-2 rounded-full", statusConfig.dotClass)}
              title={statusConfig.label}
            />
          </div>

          {/* Queue capacity bar */}
          <div className="mt-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-muted-foreground shrink-0">Fila</span>
              <div className="h-2.5 flex-1 rounded-full bg-muted overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-300",
                    workloadColor.bar
                  )}
                  style={{ width: `${Math.min(capacityPct, 100)}%` }}
                />
              </div>
              <span className={cn("text-[11px] font-semibold tabular-nums", workloadColor.text)}>
                {operator.active_tickets}/{operator.max_capacity}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Specialties */}
      {operator.specialties && operator.specialties.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {operator.specialties.map((spec) => (
            <span
              key={spec}
              className="rounded bg-muted px-1.5 py-0.5 text-[9px] text-muted-foreground"
            >
              {spec}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
