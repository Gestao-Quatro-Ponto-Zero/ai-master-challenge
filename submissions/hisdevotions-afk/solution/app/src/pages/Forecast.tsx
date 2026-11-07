import { BUCKETS, BUCKET_ORDER, Empty, GroupTable, groupDeals, type GroupRow } from "../components";
import { useApp, useScopedOpen } from "../data";
import { int, moneyShort, pct, sum } from "../format";
import { link } from "../router";
import type { Bucket } from "../types";

const GROUPS = { region: "Região", manager: "Manager", agent: "Vendedor" } as const;
type GroupKey = keyof typeof GROUPS;

// O equivalente no Salesforce, onde a categoria é escolhida pelo vendedor.
const SALESFORCE: Record<Bucket, string> = {
  fechar: "Commit",
  avancar: "Best case",
  prospectar: "Pipeline",
  decidir: "Omitted",
};

export function Forecast({ query }: { query: URLSearchParams }) {
  const open = useScopedOpen();
  const { filters, setFilters } = useApp();
  const by = (query.get("por") as GroupKey) in GROUPS ? (query.get("por") as GroupKey) : "region";
  if (open.length === 0) return <Empty>Nenhum deal aberto neste recorte.</Empty>;

  // ev/ev_soon já vêm zerados do motor para zumbi e prospecção (sem histórico
  // comparável / sem taxa de conversão pra Engaging — ver scoring.py): somar
  // sobre TODOS os abertos dá o mesmo "esperado" que Meu Dia mostra, sem
  // precisar filtrar estágio aqui e lá separadamente.
  const declared = sum(open, (d) => d.price);
  const realistic = sum(open, (d) => d.ev);
  const next30 = sum(open, (d) => d.ev_soon);
  const zombie = sum(open.filter((d) => d.bucket === "decidir"), (d) => d.price);
  const prospect = sum(open.filter((d) => d.bucket === "prospectar"), (d) => d.price);

  const rows = groupDeals(open, (d) => d[by]);
  // Grupo com pipeline mas nada vivo em negociação: o problema não é fechar, é o funil travado.
  const stalled = rows.filter((r) => r.live === 0);
  // Mesmo gesto da Overview: o clique aplica o filtro e desce um nível de agrupamento.
  const NEXT: Record<GroupKey, GroupKey> = { region: "manager", manager: "agent", agent: "agent" };
  const select = (r: GroupRow) => {
    const sample = r.ds[0];
    setFilters(
      by === "region" ? { region: r.name, manager: "", agent: "" }
      : by === "manager" ? { region: filters.region || sample.region, manager: r.name, agent: "" }
      : { region: filters.region || sample.region, manager: filters.manager || sample.manager, agent: r.name },
    );
    window.location.hash = `${link("forecast")}?por=${NEXT[by]}`;
  };

  return (
    <div>
      <header className="page-head">
        <h1>Forecast</h1>
        <p className="lede">
          O pipeline declarado soma <strong>{moneyShort(declared)}</strong>. Descontando a chance de cada deal e tirando o que
          está parado além de qualquer ciclo já fechado, o esperado dos deals em negociação é{" "}
          <strong>{moneyShort(realistic)}</strong>. {pct(zombie / declared)} do valor declarado está em deals que o histórico
          nunca viu fechar.
        </p>
      </header>

      <dl className="facts facts-big">
        <div><dt>Pipeline declarado</dt><dd>{moneyShort(declared)}</dd><p>Soma do preço de lista de todos os deals abertos.</p></div>
        <div><dt>Esperado (sem prazo)</dt><dd>{moneyShort(realistic)}</dd><p>Deals em negociação vezes a chance de ganhar pela idade. Parados valem zero; prospecção ({moneyShort(prospect)}) fica de fora por não ter histórico de conversão.</p></div>
        <div><dt>Próximos 30 dias</dt><dd>{moneyShort(next30)}</dd><p>Soma de valor × chance de ganhar em 30 dias (o score). É o mesmo número da Overview.</p></div>
      </dl>

      {stalled.length > 0 && (
        <aside className="hygiene">
          <p>
            <strong>
              {stalled.map((r) => r.name).join(", ")}: nenhum deal na janela de fechamento.
            </strong>{" "}
            Tudo o que está aberto ali ou ainda não engajou ou já passou de qualquer ciclo fechado. O problema não é fechar, é
            destravar o funil: engajar a prospecção e decidir os parados.
          </p>
          <p className="muted">
            Um padrão tão limpo (zero deals em negociação numa região inteira) é improvável numa operação real e pode ser
            efeito de como a base foi gerada ou exportada. Vale confirmar no CRM antes de mudar a cobrança do time.
          </p>
        </aside>
      )}

      <section>
        <h2>De onde vem o valor declarado</h2>
        <div className="stack">
          {BUCKET_ORDER.map((b) => {
            const ds = open.filter((d) => d.bucket === b);
            const v = sum(ds, (d) => d.price);
            const label = `${BUCKETS[b].label}: ${moneyShort(v)} em ${int(ds.length)} deals`;
            return v > 0 ? (
              <a key={b} className={`stack-${b}`} style={{ flexGrow: v }} href={`${link("pipeline")}?fila=${b}`} title={label} aria-label={label} />
            ) : null;
          })}
        </div>
        <ul className="stack-legend">
          {BUCKET_ORDER.map((b) => {
            const ds = open.filter((d) => d.bucket === b);
            return (
              <li key={b} className={`legend-${b}`}>
                <a href={`${link("pipeline")}?fila=${b}`}>{BUCKETS[b].label}</a>: {moneyShort(sum(ds, (d) => d.price))} em {int(ds.length)} deals.
                <span className="muted">
                  {" "}No Salesforce seria “{SALESFORCE[b]}”, escolhido pelo vendedor; aqui vem{" "}
                  {b === "prospectar" ? "do estágio (ainda não engajado)" : "da idade do deal"}.
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <section>
        <div className="section-head">
          <h2>Por {GROUPS[by].toLowerCase()}</h2>
          <nav className="tabs" aria-label="Agrupar por">
            {(Object.keys(GROUPS) as GroupKey[]).map((k) => (
              <a key={k} href={`${link("forecast")}?por=${k}`} aria-current={k === by ? "page" : undefined}>{GROUPS[k]}</a>
            ))}
          </nav>
        </div>
        <GroupTable
          rows={rows} label={GROUPS[by]} showRegion={by === "manager"} onSelect={select}
          selectHint={by === "agent" ? "filtrar o vendedor" : `ver o detalhe por ${GROUPS[NEXT[by]].toLowerCase()}`}
        />
      </section>
    </div>
  );
}
