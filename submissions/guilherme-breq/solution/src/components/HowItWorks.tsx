import { formatPct } from "@/lib/format";
import { HORIZON_DAYS, MOMENTUM_WEIGHT, VALUE_WEIGHT, WINDOW_ALERT_DAYS } from "@/lib/scoring";

/** Curva p(decisão em 30 dias | idade), calculada do histórico. É o que alimenta o "momento". */
function DecideCurve({ curve, maxCycle }: { curve: number[]; maxCycle: number }) {
  const W = 560, H = 180, P = { l: 36, r: 12, t: 12, b: 28 };
  const x = (age: number) => P.l + (age / maxCycle) * (W - P.l - P.r);
  const y = (p: number) => P.t + (1 - p) * (H - P.t - P.b);
  const line = curve.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p).toFixed(1)}`).join(" ");
  const area = `${line} L${x(curve.length - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const ticks = [0, 30, 60, 90, 120, maxCycle];
  return (
    <figure>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Chance de o deal se decidir nos próximos 30 dias, por idade do deal">
        {[0, 0.5, 1].map((p) => (
          <g key={p}>
            <line x1={P.l} x2={W - P.r} y1={y(p)} y2={y(p)} stroke="rgb(255 255 255 / 0.07)" />
            <text x={P.l - 8} y={y(p) + 4} textAnchor="end" className="fill-fg-subtle font-mono text-[10px]">{formatPct(p)}</text>
          </g>
        ))}
        {ticks.map((t) => (
          <text key={t} x={x(t)} y={H - 8} textAnchor="middle" className="fill-fg-subtle font-mono text-[10px]">{t}d</text>
        ))}
        <path d={area} fill="rgb(200 242 80 / 0.10)" />
        <path d={line} fill="none" stroke="var(--color-signal)" strokeWidth="2" />
      </svg>
      <figcaption className="mt-1 text-xs text-fg-subtle">
        Idade do deal (dias desde o engajamento) × chance de ele se decidir, ganho ou perdido, nos próximos {HORIZON_DAYS} dias. Calculado com os deals já fechados.
      </figcaption>
    </figure>
  );
}

export function HowItWorks({ curve, maxCycle, globalWinRate }: { curve: number[]; maxCycle: number; globalWinRate: number }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <Card tag={`até ${VALUE_WEIGHT} pts`} title="Valor" color="bg-cool">
          O preço do produto, em escala logarítmica, porque vai de US$ 55 a US$ 26 mil. É o fator que mais separa um deal do outro: no backtest, ordenar por valor colocou metade da receita ganha nos 20% do topo.
        </Card>
        <Card tag={`até ${MOMENTUM_WEIGHT} pts`} title="Momento" color="bg-signal">
          A chance de o deal se decidir no próximo mês, pela idade dele. Deals jovens ou no &quot;vale&quot; de 15 a 45 dias raramente se resolvem logo; a partir de 90 dias, 86% ou mais se resolvem. Testado em datas passadas: AUC de 0,66 a 0,87.
        </Card>
        <Card tag="fora do ranking" title="Zumbi" color="bg-risk">
          Nenhum deal do histórico fechou depois de {maxCycle} dias. Deal mais velho que isso vai para Higiene: confirmar se está vivo ou marcar como perdido. Em 589 zumbis de datas passadas, nenhum fechou depois.
        </Card>
      </div>

      <div className="rounded-xl border border-line bg-ink-900 p-5">
        <DecideCurve curve={curve} maxCycle={maxCycle} />
      </div>

      <div className="rounded-xl border border-line bg-ink-900 p-5">
        <h3 className="font-medium text-fg">O que testamos e ficou de fora</h3>
        <p className="mt-1 text-sm text-fg-muted">
          Cada hipótese foi testada em 5 datas passadas, usando só o que se sabia naquele dia. AUC 0,50 é cara ou coroa.
        </p>
        <table className="mt-4 w-full text-sm">
          <tbody className="divide-y divide-line">
            {[
              ["Chance por vendedor", "AUC 0,51", "Varia de 55% a 70%, mas não se repete de um semestre para o outro."],
              ["Chance por produto ou setor", "AUC 0,50–0,51", "Todos ficam entre 60% e 65%. Não diferencia."],
              ["Tamanho da conta (receita, funcionários)", "sem efeito", "De 61% a 66% entre quartis, sem padrão."],
              ["Idade como chance de ganhar", "AUC 0,52", "A idade prevê quando o deal se decide, não se ele é ganho."],
              ["Fim de trimestre (81% contra 52%)", "descartado", "O efeito vale para o mês inteiro, não para os últimos dias. Parece artefato dos dados, não comportamento de venda."],
            ].map(([h, m, w]) => (
              <tr key={h}>
                <td className="py-2.5 pr-4 text-fg">{h}</td>
                <td className="tabular whitespace-nowrap py-2.5 pr-4 font-mono text-xs text-fg-muted">{m}</td>
                <td className="py-2.5 text-fg-muted">{w}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-4 text-sm text-fg-muted">
          Conclusão: neste CRM, todo deal vivo tem ~{formatPct(globalWinRate)} de chance. O que muda é <span className="text-fg">quanto vale</span>,{" "}
          <span className="text-fg">quando se decide</span> e <span className="text-fg">se ainda está vivo</span>. O alerta de janela aparece quando faltam {WINDOW_ALERT_DAYS} dias ou menos para o limite do ciclo.
        </p>
      </div>
    </div>
  );
}

function Card({ tag, title, color, children }: { tag: string; title: string; color: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-ink-900 p-5">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 font-medium text-fg">
          <i className={`size-2 rounded-full ${color}`} aria-hidden />
          {title}
        </span>
        <span className="font-mono text-[11px] text-fg-subtle">{tag}</span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-fg-muted">{children}</p>
    </div>
  );
}
