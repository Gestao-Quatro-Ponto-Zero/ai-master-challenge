import { inScope, useApp, useScopedOpen } from "../data";
import { int, money, moneyShort, pct, sum } from "../format";
import type { Agent } from "../types";

export function Team() {
  const { model, filters } = useApp();
  const open = useScopedOpen();
  // Receita ganha é fato, não estimativa: ordenar por ela não tem o problema
  // de ranquear por taxa de ganho, que aqui é ruído (p = 0,30).
  const agents = model.agents.filter((a) => inScope(a, a.name, filters)).sort((a, b) => b.revenue_won - a.revenue_won);
  const withDeals = agents.filter((a) => a.has_deals);
  const idle = agents.filter((a) => !a.has_deals);
  const total = sum(withDeals, (a) => a.revenue_won);
  const count = (name: string, pred: (d: (typeof open)[number]) => boolean) =>
    open.filter((d) => d.agent === name && pred(d)).length;

  return (
    <div>
      <header className="page-head">
        <h1>Time</h1>
        <p className="lede">
          O time ganhou <strong>{moneyShort(total)}</strong> no histórico. Receita e volume variam muito entre as pessoas e
          aparecem aqui como são, ordenados por receita ganha. A taxa de ganho é outra história: nenhuma diferença entre
          vendedores passa do que o acaso produz, então ela não serve para comparar ninguém.
        </p>
      </header>
      <div className="table-wrap">
        <table className="deals team">
          <thead>
            <tr>
              <th scope="col">Vendedor</th>
              <th scope="col" className="num">Receita ganha</th>
              <th scope="col" className="num">Ticket médio</th>
              <th scope="col">Taxa de ganho e faixa plausível</th>
              <th scope="col" className="num">Na janela</th>
              <th scope="col" className="num">Deals parados</th>
              <th scope="col" className="num">Sem conta</th>
              <th scope="col" className="num">Abertos</th>
            </tr>
          </thead>
          <tbody>
            {withDeals.map((a) => (
              <tr key={a.name}>
                <th scope="row">
                  {a.name}
                  <span className="muted block">{a.manager}, {a.region}</span>
                </th>
                <td className="num">{money(a.revenue_won)}<span className="muted block">{pct(total > 0 ? a.revenue_won / total : 0)} do time</span></td>
                <td className="num">{a.avg_ticket == null ? "—" : money(a.avg_ticket)}</td>
                <td><RateBar agent={a} base={model.meta.base_rate} /></td>
                <td className="num">{int(count(a.name, (d) => d.bucket === "fechar"))}</td>
                <td className="num">{int(count(a.name, (d) => d.bucket === "decidir"))}</td>
                <td className="num">{int(count(a.name, (d) => !d.account))}</td>
                <td className="num">{int(count(a.name, () => true))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {idle.length > 0 && (
        <p className="queue-note">
          <strong>{idle.map((a) => a.name).join(", ")}</strong>{" "}
          {idle.length === 1 ? "está no time mas não tem" : "estão no time mas não têm"} nenhum deal no CRM, nem aberto nem
          fechado. Pode ser gente nova, desligada ou que registra fora do sistema: vale perguntar ao manager.
        </p>
      )}
      <p className="queue-note">
        A faixa plausível mostra onde a taxa de ganho de cada pessoa provavelmente está. Com poucos deals fechados a faixa fica
        larga, e por isso ninguém aqui aparece marcado como acima ou abaixo do time.
      </p>
    </div>
  );
}

function RateBar({ agent, base }: { agent: Agent; base: number }) {
  if (agent.win_rate == null) return <span className="muted">Sem deals fechados</span>;
  const x = (p: number) => `${((p - 0.3) / 0.6) * 100}%`; // eixo de 30% a 90%
  const label = `${pct(agent.win_rate)} de ${agent.closed} deals fechados, faixa plausível de ${pct(agent.ci_low)} a ${pct(agent.ci_high)}`;
  return (
    <div className="ratebar" title={label} aria-label={label}>
      <span className="ratebar-track">
        <span className="ratebar-range" style={{ left: x(agent.ci_low), right: `calc(100% - ${x(agent.ci_high)})` }} />
        <span className="ratebar-base" style={{ left: x(base) }} title={`Média do time: ${pct(base)}`} />
        <span className="ratebar-dot" style={{ left: x(agent.win_rate) }} />
      </span>
      <span className="ratebar-label">{pct(agent.win_rate)} de {agent.closed}</span>
    </div>
  );
}
