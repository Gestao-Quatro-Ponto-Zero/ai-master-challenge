import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { Deal } from "@/hooks/useDeals";
import { formatNumber, formatPct, formatUSD } from "@/lib/format";
import { CurvaChart } from "./CurvaChart";
import { AlertChips, MomentoChip } from "./Chips";

export function ScoreSheet({ deal, onClose }: { deal: Deal | null; onClose: () => void }) {
  return (
    <Sheet open={!!deal} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        {deal && (
          <>
            <SheetHeader>
              <SheetTitle className="font-display text-3xl font-normal">Por que este score</SheetTitle>
              <SheetDescription>
                {deal.opportunity_id} · {deal.product} · {deal.account ?? "sem conta"}
              </SheetDescription>
            </SheetHeader>

            <div className="mt-6 space-y-6 text-sm">
              <div className="flex flex-wrap items-center gap-3">
                {deal.score != null && <span className="font-numeric text-5xl font-semibold tabular-nums">{deal.score}</span>}
                <div className="space-y-1">
                  <p className="text-muted-foreground">{formatNumber(deal.idade_dias)} dias em aberto</p>
                  <div className="flex flex-wrap gap-1">
                    <MomentoChip momento={deal.momento} />
                    {(deal.sem_conta || deal.possivel_duplicata) && <AlertChips semConta={deal.sem_conta} duplicata={deal.possivel_duplicata} />}
                  </div>
                </div>
              </div>

              {!!deal.motivos?.length && (
                <ul className="space-y-2">
                  {deal.motivos.map((m, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                      <span>{m}</span>
                    </li>
                  ))}
                </ul>
              )}

              {deal.fila !== "requalificar" && deal.p_ganho != null && (
                <div className="rounded-lg bg-muted p-3">
                  Chance de <strong>{formatPct(deal.p_ganho)}</strong> × preço de lista <strong>{formatUSD(deal.sales_price)}</strong> = valor esperado <strong>{formatUSD(deal.valor_esperado)}</strong>
                </div>
              )}

              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">Chance de ganho pela idade do deal</p>
                <CurvaChart height={200} idadeDeal={deal.idade_dias} pGanhoDeal={deal.p_ganho} compact />
              </div>

              <div className="rounded-lg border border-border p-3">
                <p className="font-medium">Contexto (não entra no score)</p>
                <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1">
                  <dt className="text-muted-foreground">Setor</dt><dd>{deal.sector ?? "—"}</dd>
                  <dt className="text-muted-foreground">Receita</dt><dd>{deal.revenue != null ? `US$ ${formatNumber(deal.revenue)} mi` : "—"}</dd>
                  <dt className="text-muted-foreground">Funcionários</dt><dd>{formatNumber(deal.employees)}</dd>
                  <dt className="text-muted-foreground">País</dt><dd>{deal.office_location ?? "—"}</dd>
                  <dt className="text-muted-foreground">Escritório</dt><dd>{deal.regional_office ?? "—"}</dd>
                  <dt className="text-muted-foreground">Vendedor</dt><dd>{deal.sales_agent ?? "—"}</dd>
                </dl>
                <p className="mt-3 text-xs text-muted-foreground">
                  Nos testes com o histórico, vendedor, produto e setor não previram o resultado; por isso aparecem só como contexto.
                </p>
              </div>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
