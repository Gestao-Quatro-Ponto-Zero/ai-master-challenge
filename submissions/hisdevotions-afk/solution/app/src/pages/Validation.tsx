import { useApp } from "../data";
import { int, longDate, money, moneyShort, pct, sum } from "../format";
import type { BacktestRun } from "../types";

const OURS = "Pipeline em Foco";
const PRICE = "Só valor";
const RANDOM = "Aleatório";
const NEWEST = "Mais novos primeiro";

/** Captura: receita ganha em 30 dias que os 20% melhores da fila teriam pego. */
export function Validation() {
  const { model } = useApp();
  const bt = model.backtest;
  const q = model.quality;
  const ours = bt.summary.find((r) => r.name.startsWith(OURS))!;
  const price = bt.summary.find((r) => r.name === PRICE)!;
  const random = bt.summary.find((r) => r.name.startsWith(RANDOM))!;
  const newest = bt.summary.find((r) => r.name === NEWEST)!;
  const strategy = (run: BacktestRun, name: string) => run.strategies.find((s) => s.name.startsWith(name))!;

  return (
    <div>
      <header className="page-head">
        <h1>Validação</h1>
        <p className="lede">
          A mesma fila, testada em quatro datas de 2017. Em cada corte o motor aprende só com os deals
          fechados até aquele dia e reconstrói o pipeline aberto na data. O desfecho posterior serve
          apenas para medir — nada dele entra no score.
        </p>
      </header>

      <dl className="facts facts-big">
        <div>
          <dt>Captura da fila</dt>
          <dd>{pct(ours.capture)}</dd>
          <p>
            da receita ganha em 30 dias estava nos {int(Math.round(bt.top_fraction * 100))}% melhores deals da
            nossa ordem. O acaso pega {pct(random.capture)}; só ordenar por valor pega {pct(price.capture)}.
          </p>
        </div>
        <div>
          <dt>Pior corte</dt>
          <dd>{pct(ours.min_capture)}</dd>
          <p>
            Mesmo no pior dos quatro cortes a fila pegou quase três vezes o acaso. A captura do “mais novos
            primeiro” varia de {pct(newest.min_capture)} a {pct(newest.max_capture)}.
          </p>
        </div>
        <div>
          <dt>AUC</dt>
          <dd>{ours.auc.toFixed(2)}</dd>
          <p>
            Chance de um ganho em 30 dias aparecer acima de uma perda na nossa ordem. 0,50 é sorteio;
            1,00 seria separação perfeita.
          </p>
        </div>
      </dl>

      <section>
        <div className="section-head">
          <h2>Nossa fila contra alternativas</h2>
        </div>
        <div className="table-wrap">
          <table className="deals">
            <thead>
              <tr>
                <th scope="col">Estratégia</th>
                <th scope="col" className="num">AUC</th>
                <th scope="col" className="num">Receita capturada (30d)</th>
                <th scope="col" className="num">Ganhos</th>
                <th scope="col" className="num">Captura</th>
                <th scope="col" className="num">Pior corte</th>
                <th scope="col" className="num">Parados na seleção</th>
              </tr>
            </thead>
            <tbody>
              {bt.summary.map((r) => (
                <tr key={r.name} className={r.name.startsWith(OURS) ? "row-highlight" : undefined}>
                  <th scope="row">{r.name}</th>
                  <td className="num">{r.auc.toFixed(2)}</td>
                  <td className="num">{money(r.top_revenue)}</td>
                  <td className="num">{int(r.top_wins)}</td>
                  <td className="num">{pct(r.capture)}</td>
                  <td className="num">{pct(r.min_capture)}</td>
                  <td className="num">{pct(r.zombies)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="queue-note">
          Captura é a métrica de negócio: quanta receita ganha em 30 dias caiu nos 20% melhores da ordem.
          AUC mede separação, não dinheiro — “mais novos primeiro” tem AUC alta nos cortes em que só deals
          recém-engajados fecham, mas captura {pct(newest.capture)} no total e {pct(newest.min_capture)} no
          pior corte. A nossa fila é a única que fica acima de 50% em todos os cortes.
        </p>
      </section>

      <section>
        <div className="section-head">
          <h2>Por corte</h2>
        </div>
        <div className="table-wrap">
          <table className="deals">
            <thead>
              <tr>
                <th scope="col">Corte</th>
                <th scope="col" className="num">Deals abertos</th>
                <th scope="col" className="num">Ganhos em 30d</th>
                <th scope="col" className="num">Nossa captura</th>
                <th scope="col" className="num">Só valor</th>
                <th scope="col" className="num">Acaso</th>
                <th scope="col" className="num">Forecast ajustado</th>
                <th scope="col" className="num">Forecast ingênuo</th>
              </tr>
            </thead>
            <tbody>
              {bt.runs.map((run) => {
                const f = run.forecast;
                return (
                  <tr key={run.cutoff}>
                    <th scope="row">{longDate(run.cutoff)}</th>
                    <td className="num">{int(run.candidates)}</td>
                    <td className="num">{int(run.won)}</td>
                    <td className="num">{pct(strategy(run, OURS).top.capture)}</td>
                    <td className="num">{pct(strategy(run, PRICE).top.capture)}</td>
                    <td className="num">{pct(strategy(run, RANDOM).top.capture)}</td>
                    <td className="num">{f.predicted_error == null ? "—" : `${f.predicted_error > 0 ? "+" : ""}${pct(f.predicted_error)}`}</td>
                    <td className="num">{f.naive_error == null ? "—" : `${f.naive_error > 0 ? "+" : ""}${pct(f.naive_error)}`}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="queue-note">
          “Ganhos em 30d” conta os deals abertos no corte que fecharam como ganhos nos 30 dias seguintes.
          O forecast ajustado é a soma de valor × chance que o app mostra; o ingênuo é o pipeline inteiro
          vezes a taxa histórica de ganho.
        </p>
      </section>

      <section>
        <h2>Forecast de 30 dias</h2>
        <dl className="facts">
          <div>
            <dt>Realizado</dt>
            <dd>{moneyShort(bt.forecast.actual)}</dd>
            <p>Soma dos ganhos que saíram dos deals abertos em cada corte, nos 30 dias seguintes.</p>
          </div>
          <div>
            <dt>Ajustado pela idade</dt>
            <dd>{moneyShort(bt.forecast.predicted)}</dd>
            <p>
              {bt.forecast.predicted_error == null ? "—" : `${bt.forecast.predicted_error > 0 ? "+" : ""}${pct(bt.forecast.predicted_error)}`} contra o realizado.
              Nos cortes de agosto e setembro o erro fica entre -20% e +8%.
            </p>
          </div>
          <div>
            <dt>Ingênuo (taxa base)</dt>
            <dd>{moneyShort(bt.forecast.naive)}</dd>
            <p>
              {bt.forecast.naive_error == null ? "—" : `${bt.forecast.naive_error > 0 ? "+" : ""}${pct(bt.forecast.naive_error)}`} contra o realizado.
              O ajuste reduz o erro em cerca de dez vezes.
            </p>
          </div>
        </dl>
      </section>

      <section>
        <h2>Higiene do CRM</h2>
        <p className="lede">
          O backtest mede a fila; esta lista mede o que impede a fila de funcionar. Os números são do
          retrato de {longDate(model.meta.reference_date)}.
        </p>
        <dl className="facts">
          <div>
            <dt>Sem conta vinculada</dt>
            <dd>{int(q.missing_account)}</dd>
            <p>{pct(q.missing_account / q.open_total)} dos {int(q.open_total)} deals abertos, {moneyShort(q.missing_account_value)} em valor declarado. Sem conta não há histórico do cliente.</p>
          </div>
          <div>
            <dt>Conflito conta × produto</dt>
            <dd>{int(q.conflicts)}</dd>
            <p>{moneyShort(q.conflicts_value)} em deals em que outro vendedor fechou o mesmo produto na mesma conta depois do deal abrir. É confirmação, não encerramento.</p>
          </div>
          <div>
            <dt>Pares duplicados</dt>
            <dd>{int(q.duplicate_pairs)}</dd>
            <p>{int(q.duplicate_deals)} deals em {int(q.duplicate_pairs)} pares de conta e produto com mais de um deal aberto. Vale consolidar antes de prever.</p>
          </div>
          <div>
            <dt>Parados além do ciclo</dt>
            <dd>{int(q.stalled)}</dd>
            <p>{moneyShort(q.stalled_value)} ({pct(q.stalled_value / sum(model.open, (d) => d.price))} do pipeline aberto) em deals que nenhum ciclo fechado alcança.</p>
          </div>
        </dl>
      </section>

      <section>
        <h2>O que este teste não prova</h2>
        <ul className="context">
          <li>
            São quatro cortes de uma base sintética de 2017, não um experimento causal. A fila mostra
            associação, não que seguir a ordem <em>causa</em> a venda.
          </li>
          <li>
            Em julho e outubro a base não tem deals antigos fechando dentro de 30 dias — os cohorts pulam
            meses. Por isso o forecast ajustado erra para cima nesses cortes; o ingênuo erra muito mais.
          </li>
          <li>
            O desfecho é o que está no CRM: um deal marcado como ganho não prova que o cliente comprou por
            causa da priorização.
          </li>
          <li>
            A AUC da janela de 30 dias mede separação de ganhos e perdas; a captura mede dinheiro. As duas
            aparecem juntas de propósito, porque uma sozinha conta meia história.
          </li>
        </ul>
      </section>
    </div>
  );
}
