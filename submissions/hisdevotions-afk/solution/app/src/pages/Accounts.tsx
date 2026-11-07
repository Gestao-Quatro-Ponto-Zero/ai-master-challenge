import { DealRow, Empty } from "../components";
import { dealInScope, isOpen, useApp } from "../data";
import { int, money, shortDate, sum } from "../format";
import { link } from "../router";
import type { Deal, OpenDeal } from "../types";

export function Accounts() {
  const { model, filters, decisions } = useApp();
  const rows = model.accounts
    .map((a) => {
      const deals = model.deals.filter((d) => d.account === a.account);
      const open = deals.filter(isOpen).filter((d) => dealInScope(d, filters) && !decisions[d.id]);
      return {
        a,
        open,
        won: deals.filter((d) => d.stage === "Won").length,
        lost: deals.filter((d) => d.stage === "Lost").length,
      };
    })
    .filter((r) => r.open.length > 0 || !(filters.region || filters.manager || filters.agent))
    .sort((x, y) => sum(y.open, (d) => d.ev) - sum(x.open, (d) => d.ev));

  return (
    <div>
      <header className="page-head">
        <h1>Contas</h1>
        <p className="lede">Ordenadas pelo esperado (sem prazo) dos deals abertos no seu recorte.</p>
      </header>
      <div className="table-wrap">
        <table className="deals">
          <thead>
            <tr>
              <th scope="col">Conta</th>
              <th scope="col">Setor</th>
              <th scope="col" className="num">Abertos</th>
              <th scope="col" className="num">Esperado (sem prazo)</th>
              <th scope="col" className="num">Ganhos</th>
              <th scope="col" className="num">Perdidos</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ a, open, won, lost }) => (
              <tr key={a.account}>
                <th scope="row"><a href={link("contas", a.account)}>{a.account}</a></th>
                <td>{a.sector}</td>
                <td className="num">{int(open.length)}</td>
                <td className="num">{money(sum(open, (d) => d.ev))}</td>
                <td className="num">{int(won)}</td>
                <td className="num">{int(lost)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function AccountPage({ name }: { name: string }) {
  const { model, decisions } = useApp();
  const account = model.accountByName.get(name);
  if (!account) return <Empty>Não encontrei a conta {name}. <a href={link("contas")}>Ver todas as contas</a></Empty>;
  const deals = model.deals.filter((d) => d.account === name);
  // Lista mistura filas diferentes: ev_soon/ev são 0 para decidir/prospectar (sem
  // score), então já caem para o fim sem precisar de um switch por bucket.
  const open = deals.filter(isOpen).filter((d) => !decisions[d.id])
    .sort((a, b) => b.ev_soon - a.ev_soon || b.ev - a.ev || b.price - a.price) as OpenDeal[];
  const closed = deals.filter((d) => !isOpen(d)).sort((a, b) => (b.close ?? "").localeCompare(a.close ?? "")) as Deal[];
  const won = closed.filter((d) => d.stage === "Won");
  const parent = account.subsidiary_of && model.accountByName.get(account.subsidiary_of);
  const siblings = model.accounts.filter((a) => a.subsidiary_of === name);

  return (
    <div>
      <a className="back" href={link("contas")}>Contas</a>
      <header className="page-head">
        <h1>{name}</h1>
        <p className="lede">
          {account.sector}, {account.office_location}. Fundada em {account.year_established}, {int(Number(account.employees))}{" "}
          funcionários, receita anual de {money(Number(account.revenue) * 1_000_000)}.
          {parent && <> Faz parte do grupo <a href={link("contas", parent.account)}>{parent.account}</a>.</>}
          {siblings.length > 0 && <> Controla {siblings.map((s) => s.account).join(", ")}.</>}
        </p>
      </header>

      <dl className="facts">
        <div><dt>Deals ganhos</dt><dd>{int(won.length)}</dd></div>
        <div><dt>Deals perdidos</dt><dd>{int(closed.length - won.length)}</dd></div>
        <div><dt>Receita já fechada</dt><dd>{money(sum(won, (d) => d.close_value ?? 0))}</dd></div>
        <div><dt>Em aberto, esperado (sem prazo)</dt><dd>{money(sum(open, (d) => d.ev))}</dd></div>
      </dl>

      <section>
        <h2>Deals abertos, de todos os vendedores</h2>
        {open.length ? (
          <ol className="deal-list">{open.map((d) => <DealRow key={d.id} deal={d} />)}</ol>
        ) : (
          <Empty>Nenhum deal aberto com esta conta.</Empty>
        )}
      </section>

      <section>
        <h2>Últimos fechamentos</h2>
        <div className="table-wrap">
          <table className="deals">
            <thead>
              <tr>
                <th scope="col">Fechado em</th>
                <th scope="col">Produto</th>
                <th scope="col">Vendedor</th>
                <th scope="col">Resultado</th>
                <th scope="col" className="num">Valor</th>
              </tr>
            </thead>
            <tbody>
              {closed.slice(0, 12).map((d) => (
                <tr key={d.id}>
                  <td>{shortDate(d.close)}</td>
                  <td>{d.product}</td>
                  <td>{d.agent}</td>
                  <td className={d.stage === "Won" ? "won" : "lost"}>{d.stage === "Won" ? "Ganho" : "Perdido"}</td>
                  <td className="num">{d.stage === "Won" ? money(d.close_value ?? 0) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
