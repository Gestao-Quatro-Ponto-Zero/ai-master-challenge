import { useMemo, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Deal } from "@/hooks/useDeals";
import { formatDate, formatNumber, formatPct, formatPrazo, formatUSD } from "@/lib/format";
import { sortFocar, sortProspectar, sortRequalificar } from "@/lib/metrics";
import { AlertChips, ContaCell, MomentoChip, ScoreCell } from "./Chips";
import { DealTable, type Column } from "./DealTable";
import { ScoreSheet } from "./ScoreSheet";
import { useParametros } from "@/hooks/useParametros";
import { Inbox } from "lucide-react";

const oportunidade: Column = {
  key: "op",
  header: "Oportunidade",
  cell: (d) => (
    <div>
      <div className="font-mono text-xs text-muted-foreground">{d.opportunity_id}</div>
      <div className="font-medium">{d.product}</div>
    </div>
  ),
};
const conta: Column = { key: "conta", header: "Conta", cell: (d) => <ContaCell account={d.account} /> };
const vendedorCols: Column[] = [
  { key: "vend", header: "Vendedor", cell: (d) => <span className="whitespace-nowrap">{d.sales_agent}</span> },
  { key: "mgr", header: "Manager", cell: (d) => <span className="whitespace-nowrap text-muted-foreground">{d.manager}</span> },
];

export function PipelineTabs({ deals, showVendedor }: { deals: Deal[]; showVendedor: boolean }) {
  const { data: params } = useParametros();
  const ciclo = params?.ciclo_max_dias;
  const [tab, setTab] = useState("focar");
  const [selected, setSelected] = useState<Deal | null>(null);

  const { focar, requalificar, prospectar } = useMemo(() => ({
    focar: deals.filter((d) => d.fila === "focar").sort(sortFocar),
    requalificar: deals.filter((d) => d.fila === "requalificar").sort(sortRequalificar),
    prospectar: deals.filter((d) => d.fila === "prospectar").sort(sortProspectar),
  }), [deals]);

  const extra = showVendedor ? vendedorCols : [];

  const focarCols: Column[] = [
    { key: "score", header: "Score", cell: (d) => <ScoreCell score={d.score} /> },
    oportunidade,
    conta,
    ...extra,
    { key: "idade", header: "Idade", cell: (d) => (
      <div className="space-y-1"><div className="tabular-nums">{formatNumber(d.idade_dias)} dias</div><MomentoChip momento={d.momento} /></div>
    ) },
    { key: "prazo", header: "Prazo limite", cell: (d) => (
      <div className="whitespace-nowrap"><div>{formatDate(d.prazo_limite)}</div>
        <div className={(d.dias_ate_limite ?? 99) <= 7 ? "text-xs text-warning-foreground" : "text-xs text-muted-foreground"}>{formatPrazo(d.dias_ate_limite)}</div></div>
    ) },
    { key: "chance", header: "Chance", align: "right", cell: (d) => formatPct(d.p_ganho) },
    { key: "ve", header: "Valor esperado", align: "right", cell: (d) => formatUSD(d.valor_esperado) },
    { key: "alertas", header: "Alertas", cell: (d) => <AlertChips semConta={d.sem_conta} duplicata={d.possivel_duplicata} /> },
  ];

  const requalCols: Column[] = [
    { ...oportunidade, cell: (d) => <span className="font-mono text-xs">{d.opportunity_id}</span> },
    { key: "prod", header: "Produto", cell: (d) => d.product },
    conta,
    ...extra,
    { key: "parado", header: "Dias parado", align: "right", cell: (d) => formatNumber(d.idade_dias) },
    { key: "alem", header: "Dias além do limite", align: "right", cell: (d) => (
      <span className="text-warning-foreground">{ciclo == null ? "—" : `+${formatNumber((d.idade_dias ?? 0) - ciclo)}`}</span>
    ) },
    { key: "lista", header: "Valor de lista", align: "right", cell: (d) => formatUSD(d.sales_price) },
  ];

  const prospCols: Column[] = [
    { ...oportunidade, cell: (d) => <span className="font-mono text-xs">{d.opportunity_id}</span> },
    { key: "prod", header: "Produto", cell: (d) => d.product },
    conta,
    ...extra,
    { key: "lista", header: "Valor de lista", align: "right", cell: (d) => formatUSD(d.sales_price) },
    { key: "ve", header: "Valor esperado", align: "right", cell: (d) => formatUSD(d.valor_esperado) },
  ];

  return (
    <div className="px-4 pb-10 md:px-8">
      <Tabs value={tab} onValueChange={setTab}>
        <div className="w-full overflow-x-auto">
          <TabsList>
            <TabsTrigger value="focar">Focar agora ({formatNumber(focar.length)})</TabsTrigger>
            <TabsTrigger value="requalificar">Requalificar ou encerrar ({formatNumber(requalificar.length)})</TabsTrigger>
            <TabsTrigger value="prospectar">Prospectar ({formatNumber(prospectar.length)})</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="focar" className="rounded-lg border border-border bg-card">
          <DealTable deals={focar} columns={focarCols} onSelect={setSelected}
            empty={
              <div className="flex flex-col items-center gap-3 px-4 py-12 text-center text-sm text-muted-foreground">
                <Inbox className="h-6 w-6" />
                <p>Nenhum deal vivo para focar neste recorte. Comece pela fila Requalificar ou encerrar e por Prospectar.</p>
                <div className="flex flex-wrap justify-center gap-2">
                  <button onClick={() => setTab("requalificar")} className="rounded-md bg-primary px-3 py-1.5 text-primary-foreground hover:opacity-90">Ir para Requalificar ou encerrar</button>
                  <button onClick={() => setTab("prospectar")} className="rounded-md border border-border px-3 py-1.5 text-foreground hover:bg-muted">Ir para Prospectar</button>
                </div>
              </div>
            } />
        </TabsContent>

        <TabsContent value="requalificar" className="rounded-lg border border-border bg-card">
          <p className="border-b border-border px-4 py-3 text-sm text-muted-foreground">
            Estes deals estão abertos há mais tempo que qualquer venda já fechada. Atualize no CRM: requalifique com nova data ou encerre como perdido.
          </p>
          <DealTable deals={requalificar} columns={requalCols} onSelect={setSelected}
            empty="Nenhum deal parado neste recorte." />
        </TabsContent>

        <TabsContent value="prospectar" className="rounded-lg border border-border bg-card">
          <p className="border-b border-border px-4 py-3 text-sm text-muted-foreground">Ainda não engajados. Comece pelos de maior valor.</p>
          <DealTable deals={prospectar} columns={prospCols} onSelect={setSelected}
            empty="Nenhum deal para prospectar neste recorte." />
        </TabsContent>
      </Tabs>
      <ScoreSheet deal={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
