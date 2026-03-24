import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const statusMap: Record<string, { label: string; className: string }> = {
  "Aberto":              { label: "Aberto",        className: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200 border-transparent" },
  "Em Andamento":        { label: "Em Andamento",  className: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200 border-transparent" },
  "Aguardando Cliente":  { label: "Aguardando",    className: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200 border-transparent" },
  "Resolvido":           { label: "Resolvido",     className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200 border-transparent" },
  "Fechado":             { label: "Fechado",       className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-transparent" },
  "Open":                { label: "Aberto",        className: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200 border-transparent" },
  "In Progress":         { label: "Em Andamento",  className: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200 border-transparent" },
  "Resolved":            { label: "Resolvido",     className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200 border-transparent" },
  "Closed":              { label: "Fechado",       className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-transparent" },
};

const priorityMap: Record<string, { label: string; className: string }> = {
  "Baixa":    { label: "Baixa",   className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-transparent" },
  "Média":    { label: "Média",   className: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200 border-transparent" },
  "Alta":     { label: "Alta",    className: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200 border-transparent" },
  "Crítica":  { label: "Crítica", className: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200 border-transparent" },
  "Low":      { label: "Baixa",   className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-transparent" },
  "Medium":   { label: "Média",   className: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200 border-transparent" },
  "High":     { label: "Alta",    className: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200 border-transparent" },
  "Critical": { label: "Crítica", className: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200 border-transparent" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusMap[status] || { label: status, className: "bg-slate-100 text-slate-700 border-transparent" };
  return (
    <Badge className={cn("text-xs font-medium", config.className)}>
      {config.label}
    </Badge>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const config = priorityMap[priority] || { label: priority, className: "bg-slate-100 text-slate-700 border-transparent" };
  return (
    <Badge className={cn("text-xs font-medium", config.className)}>
      {config.label}
    </Badge>
  );
}
