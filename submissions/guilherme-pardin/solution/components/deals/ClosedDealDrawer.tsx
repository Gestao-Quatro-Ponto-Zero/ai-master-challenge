"use client";

import {
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  User,
  XCircle,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import type { ClosedDeal } from "@/lib/types";
import { avatarBg, cn, formatMoney, initials } from "@/lib/utils";

export function ClosedDealDrawer({
  deal,
  open,
  onOpenChange,
}: {
  deal: ClosedDeal | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  if (!deal) return null;
  const won = deal.stage === "Won";
  const value = won ? deal.closeValue || deal.price : deal.price;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto p-0 shadow-[var(--shadow-drawer)]">
        <div className="p-6 pb-4 border-b border-slate-100 space-y-3">
          <SheetHeader className="p-0">
            <div className="flex items-start gap-3">
              <div
                className={cn(
                  "h-11 w-11 shrink-0 rounded-lg grid place-items-center text-white font-semibold",
                  avatarBg(deal.account),
                )}
              >
                {initials(deal.account)}
              </div>
              <div className="flex-1 min-w-0">
                <SheetTitle className="text-lg leading-tight">
                  {deal.account}
                </SheetTitle>
                <SheetDescription className="mt-0.5">
                  {deal.product} · {deal.sector}
                </SheetDescription>
              </div>
            </div>
          </SheetHeader>

          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={cn(
                "gap-1 font-medium border",
                won
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-red-50 text-red-700 border-red-200",
              )}
            >
              {won ? (
                <CheckCircle2 className="h-3 w-3" />
              ) : (
                <XCircle className="h-3 w-3" />
              )}
              {won ? "Venda fechada" : "Perdida"}
            </Badge>
            <span className="text-2xl font-bold tabular-nums text-slate-900 ml-auto">
              {formatMoney(value)}
            </span>
          </div>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <InfoTile
              icon={<DollarSign className="h-3.5 w-3.5" />}
              label={won ? "Valor fechado" : "Valor potencial perdido"}
              value={formatMoney(value)}
            />
            {won && deal.closeValue !== deal.price && (
              <InfoTile
                icon={<DollarSign className="h-3.5 w-3.5" />}
                label="Preço de tabela"
                value={formatMoney(deal.price)}
              />
            )}
            <InfoTile
              icon={<User className="h-3.5 w-3.5" />}
              label="Vendedor"
              value={deal.agent}
            />
            <InfoTile
              icon={<Building2 className="h-3.5 w-3.5" />}
              label="Gerente"
              value={deal.manager}
            />
            {deal.engageDate && (
              <InfoTile
                icon={<Calendar className="h-3.5 w-3.5" />}
                label="Engajado em"
                value={deal.engageDate}
              />
            )}
            {deal.closeDate && (
              <InfoTile
                icon={<Calendar className="h-3.5 w-3.5" />}
                label="Fechado em"
                value={deal.closeDate}
              />
            )}
            {deal.daysToClose !== null && (
              <InfoTile
                icon={<Clock className="h-3.5 w-3.5" />}
                label="Ciclo da negociação"
                value={`${deal.daysToClose} dias`}
              />
            )}
            <InfoTile
              icon={<Building2 className="h-3.5 w-3.5" />}
              label="Região"
              value={deal.region}
            />
          </div>

          {won && deal.closeValue < deal.price && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              Fechou por{" "}
              <b>
                {(((deal.price - deal.closeValue) / deal.price) * 100).toFixed(0)}%
              </b>{" "}
              abaixo do preço de tabela.
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function InfoTile({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-slate-500">
        {icon}
        {label}
      </div>
      <div className="text-sm font-medium text-slate-900 mt-0.5 truncate">
        {value}
      </div>
    </div>
  );
}
