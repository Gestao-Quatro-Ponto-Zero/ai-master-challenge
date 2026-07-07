import { Sparkles } from "lucide-react";
import type { Role } from "@/lib/types";

function timeGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Bom dia";
  if (h < 18) return "Boa tarde";
  return "Boa noite";
}

export function GreetingHeader({
  name,
  hotCount,
  reallocatedCount,
  role,
}: {
  name: string;
  hotCount: number;
  reallocatedCount: number;
  role: Role;
}) {
  const first = name.split(/\s+/)[0];
  const line =
    role === "gestor"
      ? `${hotCount} negociações quentes na operação e ${reallocatedCount} sugestões de remanejamento.`
      : role === "manager"
        ? `${hotCount} negociações quentes no time e ${reallocatedCount} sugestões de remanejamento.`
        : hotCount > 0
          ? `Você tem ${hotCount} negociaç${hotCount > 1 ? "ões quentes" : "ão quente"} para fechar hoje.`
          : `Sem negociações quentes hoje — foco em nutrir as mornas e reengajar as frias.`;

  return (
    <div className="rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50 via-blue-50/60 to-white p-5 flex items-start gap-4">
      <div className="h-11 w-11 shrink-0 rounded-lg bg-blue-500 text-white grid place-items-center shadow-sm shadow-blue-500/30">
        <Sparkles className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-lg font-semibold text-slate-900">
          {timeGreeting()}, {first}!
        </div>
        <p className="text-sm text-slate-600 mt-0.5">{line}</p>
      </div>
    </div>
  );
}
