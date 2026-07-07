"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRightLeft, Search } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/hooks/useAuth";
import { agentsForUser, scopedManagers } from "@/lib/scope";
import { avatarBg, cn, formatMoney, formatPercent, initials } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";

const TIER_COLORS = {
  hot: "bg-emerald-500",
  warm: "bg-amber-500",
  cold: "bg-slate-400",
  at_risk: "bg-red-500",
} as const;

export default function TeamPage() {
  const { user, hydrated } = useAuth();
  const router = useRouter();
  const [managerFilter, setManagerFilter] = useState<string>("__all");
  const [regionFilter, setRegionFilter] = useState<string>("__all");

  useEffect(() => {
    if (hydrated && user && user.role === "seller")
      router.replace("/pipeline");
  }, [hydrated, user, router]);

  const scopedAgents = useMemo(
    () => (user ? agentsForUser(user) : []),
    [user],
  );
  const scopedMgrs = useMemo(
    () => (user ? scopedManagers(user) : []),
    [user],
  );

  const filtered = useMemo(() => {
    let list = [...scopedAgents];
    if (managerFilter !== "__all")
      list = list.filter((a) => a.manager === managerFilter);
    if (regionFilter !== "__all")
      list = list.filter((a) => a.region === regionFilter);
    return list.sort((a, b) => b.overallWr - a.overallWr);
  }, [scopedAgents, managerFilter, regionFilter]);

  const regions = useMemo(
    () => Array.from(new Set(scopedAgents.map((a) => a.region))).sort(),
    [scopedAgents],
  );

  if (!user || user.role === "seller") return null;
  const canFilterManager = user.role === "gestor";

  const totalRealloc = filtered.reduce((s, a) => s + a.reallocatedOut, 0);
  const totalDeals = filtered.reduce((s, a) => s + a.openDeals, 0);

  return (
    <div className="p-6 lg:p-8 space-y-5">
      <PageHeader
        title="Mapa do time"
        subtitle="Vendedores ordenados pela taxa de conversão, com setores de especialização e distribuição do pipeline."
        action={
          <div className="flex items-center gap-2">
            {canFilterManager && (
              <Select
                value={managerFilter}
                onValueChange={(v) => setManagerFilter(v ?? "__all")}
              >
                <SelectTrigger className="w-[180px] bg-white">
                  <span className="truncate">
                    {managerFilter === "__all"
                      ? "Todos os gerentes"
                      : managerFilter}
                  </span>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all">Todos os gerentes</SelectItem>
                  {scopedMgrs.map((m) => (
                    <SelectItem key={m.manager} value={m.manager}>
                      {m.manager}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Select
              value={regionFilter}
              onValueChange={(v) => setRegionFilter(v ?? "__all")}
            >
              <SelectTrigger className="w-[160px] bg-white">
                <span className="truncate">
                  {regionFilter === "__all"
                    ? "Todas as regiões"
                    : regionFilter}
                </span>
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all">Todas as regiões</SelectItem>
                {regions.map((r) => (
                  <SelectItem key={r} value={r}>
                    {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
        <span>
          <b className="text-slate-900">{filtered.length}</b> vendedores
        </span>
        <span className="text-slate-300">·</span>
        <span>
          <b className="text-slate-900 tabular-nums">{totalDeals}</b>{" "}
          negociações abertas
        </span>
        <span className="text-slate-300">·</span>
        <span className="flex items-center gap-1 text-blue-700">
          <ArrowRightLeft className="h-3 w-3" />
          <b className="text-blue-700 tabular-nums">{totalRealloc}</b>{" "}
          remanejamentos sugeridos
        </span>
      </div>

      {filtered.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-10 text-center text-sm text-slate-400">
          <Search className="h-5 w-5 mx-auto mb-2 text-slate-300" />
          Nenhum vendedor bate com os filtros.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((a) => {
            const totalOpen = a.openDeals || 1;
            return (
              <div
                key={a.name}
                className="rounded-xl border border-slate-200 bg-white p-4 space-y-3"
              >
                <div className="flex items-start gap-3">
                  <div
                    className={cn(
                      "h-11 w-11 shrink-0 rounded-lg grid place-items-center text-white text-sm font-semibold",
                      avatarBg(a.name),
                    )}
                  >
                    {initials(a.name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-slate-900 truncate">
                      {a.name}
                    </div>
                    <div className="text-[11px] text-slate-500 truncate">
                      {a.manager} · {a.region}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-slate-900 tabular-nums leading-none">
                      {formatPercent(a.overallWr)}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      {a.totalClosed} negociações
                    </div>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>Pipeline aberto</span>
                    <span className="tabular-nums text-slate-700 font-medium">
                      {a.openDeals} · {formatMoney(a.pipelineValue)}
                    </span>
                  </div>
                  <div className="flex h-2 rounded-full overflow-hidden bg-slate-100">
                    {(["hot", "warm", "cold", "at_risk"] as const).map((t) => {
                      const count =
                        t === "hot"
                          ? a.hotDeals
                          : t === "warm"
                            ? a.warmDeals
                            : t === "cold"
                              ? a.coldDeals
                              : a.atRiskDeals;
                      const pct = (count / totalOpen) * 100;
                      if (pct === 0) return null;
                      return (
                        <div
                          key={t}
                          className={cn("h-full", TIER_COLORS[t])}
                          style={{ width: `${pct}%` }}
                          title={`${t}: ${count}`}
                        />
                      );
                    })}
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-slate-500">
                    <span>🔥 {a.hotDeals}</span>
                    <span>⚡ {a.warmDeals}</span>
                    <span>❄️ {a.coldDeals}</span>
                    <span>⚠️ {a.atRiskDeals}</span>
                  </div>
                </div>

                {a.sectors.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[11px] uppercase tracking-wide text-slate-500 font-medium">
                      Setores de especialização
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {a.sectors.slice(0, 5).map((s) => (
                        <Badge
                          key={s.sector}
                          variant="outline"
                          className={cn(
                            "font-medium text-[11px]",
                            s.wr >= 0.75
                              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                              : s.wr >= 0.55
                                ? "border-blue-200 bg-blue-50 text-blue-700"
                                : "border-slate-200 bg-slate-50 text-slate-600",
                          )}
                        >
                          {s.sector}{" "}
                          <span className="opacity-70 ml-1">
                            {formatPercent(s.wr)}
                          </span>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {a.reallocatedOut > 0 && (
                  <div className="flex items-center gap-1.5 text-[11px] text-amber-700 bg-amber-50 border border-amber-100 rounded-md px-2 py-1.5">
                    <ArrowRightLeft className="h-3 w-3" />
                    <b className="tabular-nums">{a.reallocatedOut}</b> para
                    redirecionar
                    {a.reallocatedIn > 0 && (
                      <span className="ml-auto text-blue-700">
                        + <b className="tabular-nums">{a.reallocatedIn}</b> para receber
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
