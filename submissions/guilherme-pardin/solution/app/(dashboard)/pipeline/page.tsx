"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, DollarSign, Layers, XCircle } from "lucide-react";
import { FunnelBoard } from "@/components/pipeline/FunnelBoard";
import { PageHeader } from "@/components/shared/PageHeader";
import { SellerFilter } from "@/components/shared/SellerFilter";
import { useAuth } from "@/lib/hooks/useAuth";
import {
  agentsForUser,
  scopedClosedDeals,
  scopedOpenDeals,
} from "@/lib/scope";
import { cn, formatMoney } from "@/lib/utils";

export default function PipelinePage() {
  const { user } = useAuth();
  const [sellerFilter, setSellerFilter] = useState<string>("__all");

  const filtered = useMemo(() => {
    if (!user) return { open: [], closed: [] };
    let open = scopedOpenDeals(user);
    let closed = scopedClosedDeals(user);
    if (user.role !== "seller" && sellerFilter !== "__all") {
      open = open.filter((d) => d.currentAgent === sellerFilter);
      closed = closed.filter((d) => d.agent === sellerFilter);
    }
    return { open, closed };
  }, [user, sellerFilter]);

  if (!user) return null;

  const teamAgents = user.role !== "seller" ? agentsForUser(user) : [];
  const openCount = filtered.open.length;
  const openValue = filtered.open.reduce((s, d) => s + d.price, 0);
  const wonCount = filtered.closed.filter((d) => d.stage === "Won").length;
  const wonValue = filtered.closed
    .filter((d) => d.stage === "Won")
    .reduce((s, d) => s + (d.closeValue || d.price), 0);
  const lostCount = filtered.closed.filter((d) => d.stage === "Lost").length;
  const lostValue = filtered.closed
    .filter((d) => d.stage === "Lost")
    .reduce((s, d) => s + d.price, 0);
  const totalClosed = wonCount + lostCount;
  const wr = totalClosed ? wonCount / totalClosed : 0;

  const title =
    user.role === "gestor"
      ? "Pipeline da operação"
      : user.role === "manager"
        ? "Pipeline do seu time"
        : "Meu pipeline";
  const subtitle =
    user.role === "seller"
      ? "Funil operacional: onde cada negociação está agora. A priorização por pontuação fica em Priorização."
      : "Funil operacional do time — Prospecção, Em negociação, Vendas Fechadas e Perdidas — ordenados por pontuação.";

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        title={title}
        subtitle={subtitle}
        action={
          user.role !== "seller" ? (
            <SellerFilter
              value={sellerFilter}
              onChange={setSellerFilter}
              agentPool={teamAgents}
              placeholder={
                user.role === "manager"
                  ? "Todo o seu time"
                  : "Todos os vendedores"
              }
            />
          ) : null
        }
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <SummaryTile
          icon={<Layers className="h-4 w-4" />}
          label="Negociações abertas"
          value={openCount.toString()}
          hint={formatMoney(openValue)}
        />
        <SummaryTile
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />}
          label="Vendas fechadas"
          value={wonCount.toString()}
          hint={formatMoney(wonValue)}
        />
        <SummaryTile
          icon={<XCircle className="h-4 w-4 text-red-500" />}
          label="Perdidas"
          value={lostCount.toString()}
          hint={`${formatMoney(lostValue)} potencial`}
        />
        <SummaryTile
          icon={<DollarSign className="h-4 w-4 text-blue-500" />}
          label="Taxa de conversão"
          value={`${(wr * 100).toFixed(0)}%`}
          hint={`${totalClosed} negociações fechadas`}
        />
      </div>

      <FunnelBoard
        openDeals={filtered.open}
        closedDeals={filtered.closed}
        showAgent={user.role !== "seller"}
      />
    </div>
  );
}

function SummaryTile({
  icon,
  label,
  value,
  hint,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3.5 flex items-center gap-3 shadow-[var(--shadow-metric)]">
      <div className="h-9 w-9 rounded-md bg-slate-100 grid place-items-center text-slate-700">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] uppercase tracking-wide text-slate-500">
          {label}
        </div>
        <div className={cn("text-lg font-semibold text-slate-900 tabular-nums leading-tight")}>
          {value}
        </div>
        {hint && (
          <div className="text-[11px] text-slate-500 truncate">{hint}</div>
        )}
      </div>
    </div>
  );
}
