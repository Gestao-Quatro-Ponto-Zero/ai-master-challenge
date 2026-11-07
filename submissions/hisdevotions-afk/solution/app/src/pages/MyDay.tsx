import type { ReactNode } from "react";
import { BUCKETS, DealName, DealRow, DecisionButtons, Empty, GroupTable, groupDeals, Score, TIER_LABEL, type GroupRow } from "../components";
import { nextBestAction, peakAge, PRIORITY, useApp, useScopedOpen, type Filters } from "../data";
import { int, longDate, money, moneyShort, pct, plural, sum } from "../format";
import { link } from "../router";
import type { Bucket, OpenDeal } from "../types";

/** Ícone + número real + barra contra um total real — nada de "12% acima da meta" inventado. */
function StatCard({ icon, label, value, ratio, caption, queue }: { icon: ReactNode; label: string; value: string; ratio: number; caption: string; queue: Bucket }) {
  return (
    <div className={`stat-card on-${queue}`}>
      <div className="stat-card-head">
        <span className="stat-card-label">{label}</span>
        <span className="stat-card-icon">{icon}</span>
      </div>
      <p className="stat-card-value">{value}</p>
      <div className="stat-card-bar"><span style={{ width: `${Math.round(Math.min(ratio, 1) * 100)}%` }} /></div>
      <p className="stat-card-caption">{caption}</p>
    </div>
  );
}

/** Linha de zumbi: todo deal aqui tem score 0 e a régua sempre pregada no fim —
    mostrar as duas repetiria um número e um gráfico que não diferenciam nada.
    O que diferencia é o que o ORDER.decidir já usa pra ordenar: quanto cada deal
    infla o forecast, e há quanto tempo. */
function StalledRow({ deal }: { deal: OpenDeal }) {
  return (
    <li className="deal-row stalled-row">
      <span className="score score-sm on-decidir" title={`${deal.age} dias em negociação`}>{deal.age}</span>
      <div className="deal-row-main">
        <a className="deal-row-title" href={link("deal", deal.id)}><DealName deal={deal} /></a>
        <div className="deal-row-sub">
          <span>{deal.agent}</span>
          <span className={`suggestion suggestion-${deal.suggested_action}`}>
            {deal.suggested_action === "encerrar" ? "Sugestão: encerrar" : "Sugestão: confirmar antes"}
          </span>
        </div>
        <DecisionButtons deal={deal} />
      </div>
      <span className="stalled-value">
        <strong>{money(deal.price)}</strong>
        <span>no forecast declarado</span>
      </span>
    </li>
  );
}

export function MyDay() {
  const { model, filters } = useApp();
  const open = useScopedOpen();
  const queue = (b: Bucket) => open.filter((d) => d.bucket === b).sort(PRIORITY[b]);
  const [fechar, decidir, avancar, prospectar] = (["fechar", "decidir", "avancar", "prospectar"] as Bucket[]).map(queue);
  const noAccount = open.filter((d) => !d.account).length;
  const declared = sum(open, (d) => d.price);
  const expected30 = sum(open, (d) => d.ev_soon);
  const monday = new Date(model.meta.reference_date + "T00:00:00Z");
  monday.setUTCDate(monday.getUTCDate() + 1);

  // Item 1 — a ação do momento: o deal de maior receita esperada em 30 dias na
  // fila Fechar. Não é um score novo — é escolher o topo de um ranking que o
  // motor já ordena, e dar a ele o gesto de "foque AGORA".
  const now = nextBestAction(open);
  // Item 4 — o "pico" da curva, para destacar o(s) deal(s) mais quente(s) da fila
  // de fechamento (mais próxima da idade de máxima chance de ganhar em 30 dias).
  const peak = peakAge(model);
  const peakGap = (d: OpenDeal) => (d.age == null ? Infinity : Math.abs(d.age - peak));
  // Item 2 — agregado da fila Decidir: quantos sugerem encerrar vs. confirmar.
  const encerrar = decidir.filter((d) => d.suggested_action === "encerrar").length;
  const confirmar = decidir.filter((d) => d.suggested_action === "confirmar").length;
  // Item 3 — sinal de funil travado: há prospecção pra engajar, mas nenhum deal
  // novo em negociação pra avançar (o "gargalo do funil" que o Forecast já
  // detecta). Só aparece quando o recorte realmente tem esse desequilíbrio.
  const prospectHeavy = prospectar.length > 0 && avancar.length === 0;
  // Sem vendedor escolhido, quem olha é gestor: ele precisa saber ONDE está o
  // problema (qual time, qual vendedor), não clicar deal a deal. As filas com
  // botões ficam para a visão do vendedor e para o Pipeline.
  const managerView = !filters.agent;
  const stalledValue = sum(decidir, (d) => d.price);
  // Na visão do vendedor o primeiro da fila já está na "Ação do momento": não repete na tabela.
  const closeRows = fechar.filter((d) => managerView || d !== now).slice(0, 6);
  const groups = managerView ? groupDeals(open, (d) => (filters.manager ? d.agent : d.manager)) : [];
  // Funil travado: grupo com pipeline aberto mas nada em negociação viva (nem
  // na janela, nem avançando). É o alarme que o gestor precisa ver primeiro.
  const stuck = groups.filter((g) => g.live === 0);

  const who = filters.agent
    ? `Bom dia, ${filters.agent.split(" ")[0]}.`
    : filters.manager
      ? `Semana do time de ${filters.manager}`
      : filters.region
        ? `Semana da região ${filters.region}`
        : "Semana da empresa inteira";

  if (open.length === 0)
    return (
      <>
        <h1>{who}</h1>
        <Empty>
          Nenhum deal aberto neste recorte. {filters.agent && `${filters.agent} ainda não tem oportunidades registradas no CRM.`}
        </Empty>
      </>
    );

  return (
    <div className="myday">
      <header className="page-head">
        <h1>{who}</h1>
        <p className="lede">
          Semana de {longDate(monday.toISOString().slice(0, 10))}.{" "}
          {fechar.length > 0 ? (
            <>
              A receita esperada para os próximos 30 dias é <strong>{moneyShort(expected30)}</strong>, e{" "}
              {pct(expected30 > 0 ? sum(fechar, (d) => d.ev_soon) / expected30 : 0)} dela vem dos{" "}
              {plural(fechar.length, "deal", "deals")} na janela de fechamento. Comece por eles.{" "}
            </>
          ) : (
            <>Nenhum deal está na janela de fechamento. </>
          )}
        </p>
      </header>

      <div className="stat-row">
        <StatCard
          icon={<svg viewBox="0 0 18 18" aria-hidden="true"><polyline points="2.5,13.5 7,8.5 10.5,11 15.5,4.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /><polyline points="11.5,4.5 15.5,4.5 15.5,8.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>}
          queue="fechar"
          label="Receita esperada (30 dias)"
          value={moneyShort(expected30)}
          ratio={declared > 0 ? expected30 / declared : 0}
          caption={`${pct(declared > 0 ? expected30 / declared : 0)} do pipeline declarado (${moneyShort(declared)})`}
        />
        <StatCard
          icon={<svg viewBox="0 0 18 18" aria-hidden="true"><path d="M2.5 3.5h13L10.2 9.8v5.2l-2.4 1v-6.2Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>}
          queue="fechar"
          label="Na janela de fechamento"
          value={int(fechar.length)}
          ratio={open.length > 0 ? fechar.length / open.length : 0}
          caption={`${plural(fechar.length, "deal", "deals")} de ${int(open.length)} abertos no recorte`}
        />
        <StatCard
          icon={<svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="7" fill="none" stroke="currentColor" strokeWidth="1.6" /><path d="M9 5.2V9l3 2" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>}
          queue="decidir"
          label="Parados para decidir"
          value={int(decidir.length)}
          ratio={declared > 0 ? stalledValue / declared : 0}
          caption={`${pct(declared > 0 ? stalledValue / declared : 0)} do valor aberto (${moneyShort(stalledValue)}) está nesses deals`}
        />
      </div>

      <section className="health-strip" aria-label="Saúde do funil no recorte">
        {stuck.length > 0 && (
          <div className="health-item health-item-alert">
            <span className="health-dot" />
            <p>
              <strong>
                {stuck.map((g) => g.name).join(" e ")}: nenhum deal em negociação.
              </strong>{" "}
              {stuck.length === 1 ? "Esse time não tem" : "Esses times não têm"} nada para fechar nos próximos 30 dias; o
              pipeline ali é só prospecção e parados. O trabalho é engajar e decidir, não fechar.
            </p>
          </div>
        )}
        {prospectHeavy && (
          <div className="health-item health-item-warn">
            <span className="health-dot" />
            <p>
              <strong>{int(prospectar.length)} deals em prospecção e nenhum em negociação nova.</strong>{" "}
              O gargalo aqui é engajar, não fechar.
            </p>
          </div>
        )}
        {noAccount > 0 && (
          <div className="health-item health-item-warn">
            <span className="health-dot" />
            <p>
              <strong>{plural(noAccount, "deal aberto sem conta vinculada", "deals abertos sem conta vinculada")}.</strong>{" "}
              Sem a conta, o deal não entra no histórico do cliente.{" "}
              <a href={`${link("pipeline")}?semconta=1`}>Ver os deals sem conta</a>
            </p>
          </div>
        )}
      </section>

      {managerView && <TeamTable rows={groups} filters={filters} />}

      {!managerView && now && (
        <aside className="razor" aria-label="Ação do momento">
          <div className="razor-head">
            <h2>Ação do momento <span className="razor-why">o deal de maior receita esperada em 30 dias</span></h2>
            <a className="razor-open" href={link("deal", now.id)}>Abrir ficha</a>
          </div>
          <div className="razor-body">
            <div className="razor-score"><Score deal={now} /></div>
            <div className="razor-main">
              <a className="deal-row-title" href={link("deal", now.id)}><DealName deal={now} /></a>
              <p className="razor-action">{now.action}</p>
              <p className="razor-meta">
                {moneyShort(now.ev_soon)} de receita esperada em 30 dias, a maior da fila · {now.score}% de chance de ganhar em 30 dias
                {now.tier && ` (${TIER_LABEL[now.tier].toLowerCase()})`} · {now.age} dias em negociação
              </p>
            </div>
          </div>
        </aside>
      )}

      <section className="queue queue-fechar">
        <QueueHead bucket="fechar" title={managerView ? "Maiores oportunidades da semana" : "Feche esta semana"} count={fechar.length} />
        {fechar.length > 0 && (
          <p className="queue-note">
            Ordenado por receita esperada em 30 dias (valor de lista × chance de ganhar em 30 dias). O score é essa chance; a
            faixa compara com o melhor score possível nesta base ({model.meta.peak_score}%).
          </p>
        )}
        {fechar.length > 0 && (
          <div className="table-wrap close-table">
            <table className="deals">
              <thead>
                <tr>
                  <th scope="col">Deal</th>
                  <th scope="col" className="cell-score" title="Chance de ganhar em 30 dias">Score</th>
                  <th scope="col" className="num">Receita esperada (30d)</th>
                  <th scope="col" className="num">Dias</th>
                  <th scope="col">Próxima ação</th>
                </tr>
              </thead>
              <tbody>
                {closeRows.map((d) => {
                  const closeToPeak = peakGap(d) <= 5;
                  return (
                    <tr key={d.id}>
                      <td>
                        <a className="cell-deal" href={link("deal", d.id)}>
                          <span>
                            {d.account ? (
                              <>
                                {d.account}
                                {" · "}
                                <span className="deal-product">{d.product}</span>
                              </>
                            ) : (
                              <DealName deal={d} />
                            )}
                          </span>
                          <span className="cell-deal-sub">{money(d.price)} · {d.agent}</span>
                        </a>
                      </td>
                      <td className="cell-score"><Score deal={d} showTier /></td>
                      <td className="num">{money(d.ev_soon)}</td>
                      <td className="num">
                        {d.age}d{closeToPeak && <span className="peak-badge">no pico</span>}
                      </td>
                      <td className="cell-action">
                        <a href={link("deal", d.id)} title={d.action}>
                          <span>{d.action}</span>
                          <svg viewBox="0 0 14 14" aria-hidden="true"><path d="M4 10 10 4M10 4H5.5M10 4v4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {fechar.length === 0 && (
          <Empty>
            {avancar.length > 0
              ? "Nenhum deal na janela agora. Use a semana para avançar os mais novos."
              : "Nenhum deal vivo em negociação. A semana é de destravar o funil: engajar a prospecção e decidir os parados."}
          </Empty>
        )}
      </section>

      {!managerView && (<>
      <section className="queue queue-decidir">
        <QueueHead bucket="decidir" title="Decida os parados" count={decidir.length} />
        <p className="queue-note">
          Nenhum deal da base fechou depois de {model.meta.max_cycle} dias. Confirme com o cliente: se ainda existe decisão,
          requalifique; se não, encerre e tire do forecast.
        </p>
        <div className="decide-split" aria-label="Resumo da fila Decidir">
          <span className="decide-split-encerrar">
            <strong>{int(encerrar)}</strong> para encerrar
          </span>
          <span className="decide-split-confirmar">
            <strong>{int(confirmar)}</strong> para confirmar antes
          </span>
          <a className="queue-all" href={`${link("pipeline")}?fila=decidir`}>Ver todos</a>
        </div>
        <ol className="deal-list">
          {decidir.slice(0, 4).map((d) => (
            <StalledRow key={d.id} deal={d} />
          ))}
        </ol>
      </section>

      <div className="queue-pair">
        <section className="queue queue-avancar">
          <QueueHead bucket="avancar" title="Mantenha em movimento" count={avancar.length} />
          <ol className="deal-list">
            {avancar.slice(0, 4).map((d) => (
              <DealRow key={d.id} deal={d} />
            ))}
          </ol>
          {avancar.length === 0 && <Empty>Nenhum deal novo em negociação.</Empty>}
        </section>
        <section className="queue queue-prospectar">
          <QueueHead bucket="prospectar" title="Engaje" count={prospectar.length} />
          <ol className="deal-list">
            {prospectar.slice(0, 4).map((d) => (
              <DealRow key={d.id} deal={d} />
            ))}
          </ol>
          {prospectar.length === 0 && <Empty>Nenhum deal em prospecção.</Empty>}
        </section>
      </div>
      </>)}
    </div>
  );
}

function QueueHead({ bucket, title, count }: { bucket: Bucket; title: string; count: number }) {
  return (
    <header className="queue-head">
      <h2>{title}</h2>
      <span className="queue-hint">{BUCKETS[bucket].hint}</span>
      {count > 0 && (
        <a className="queue-all" href={`${link("pipeline")}?fila=${bucket}`}>
          Ver {count === 1 ? "o deal" : `os ${int(count)}`}
        </a>
      )}
    </header>
  );
}

/** Visão de gestor: a mesma tabela por grupo do Forecast. Um clique aplica o
    filtro e desce um nível (manager → vendedor → a semana do vendedor). */
function TeamTable({ rows, filters }: { rows: GroupRow[]; filters: Filters }) {
  const { setFilters } = useApp();
  const byAgent = !!filters.manager;
  const select = (r: GroupRow) => {
    setFilters(byAgent ? { ...filters, agent: r.name } : { region: filters.region || r.region, manager: r.name, agent: "" });
    window.scrollTo(0, 0); // o título da nova visão ("Semana do time de…", "Bom dia…") precisa ficar à vista
  };
  return (
    <section className="queue team-table">
      <header className="queue-head">
        <h2>{byAgent ? `Time de ${filters.manager}` : "Onde está o pipeline, por manager"}</h2>
      </header>
      <GroupTable
        rows={rows} label={byAgent ? "Vendedor" : "Manager"} showRegion={!byAgent} onSelect={select}
        selectHint={byAgent ? "ver a semana do vendedor" : "ver o time do manager"}
      />
    </section>
  );
}
