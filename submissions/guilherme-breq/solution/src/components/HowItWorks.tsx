import { formatPct } from "@/lib/format";
import { decisionWindow as phases, HORIZON_DAYS, MOMENTUM_WEIGHT, VALUE_WEIGHT, WINDOW_ALERT_DAYS } from "@/lib/scoring";

/** Curva p(decisão em 30 dias | idade), estimada com o histórico. É o que alimenta o "momento". */
function CurveSvg({ curve, maxCycle, compact }: { curve: number[]; maxCycle: number; compact: boolean }) {
  // Versão compacta para o mobile: viewBox estreito (texto não encolhe), rótulos curtos e menos ticks.
  const W = compact ? 340 : 960;
  const H = compact ? 250 : 300;
  const P = { l: compact ? 34 : 36, r: compact ? 10 : 16, t: 30, b: 28 };
  const fs = compact ? "text-[15px]" : "text-[14px]";
  const x = (age: number) => P.l + (age / maxCycle) * (W - P.l - P.r);
  const top = Math.max(0.5, Math.ceil(Math.max(...curve) * 10) / 10);
  const y = (p: number) => P.t + (1 - p / top) * (H - P.t - P.b);
  const line = curve.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p).toFixed(1)}`).join(" ");
  const area = `${line} L${x(curve.length - 1)},${y(0)} L${x(0)},${y(0)} Z`;
  const { start, end } = phases(curve);
  const bands = [
    { from: 0, to: start, label: compact ? "cedo" : "ainda cedo", color: "rgb(141 186 214 / 0.07)", text: "fill-sky" },
    { from: start, to: end, label: compact ? "decisão" : "fase de decisão", color: "rgb(217 185 138 / 0.08)", text: "fill-gold-hi" },
    { from: end, to: maxCycle, label: "esfriando", color: "rgb(224 144 126 / 0.08)", text: "fill-risk" },
  ];
  const ticks = compact ? [0, 60, 120] : [0, 30, 60, 90, 120];
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className={`w-full ${compact ? "md:hidden" : "hidden md:block"}`}
      role="img"
      aria-label={`Chance de o deal se decidir nos próximos ${HORIZON_DAYS} dias, por idade. Fase de decisão entre ${start} e ${end} dias; limite em ${maxCycle} dias.`}
    >
      {bands.map((b) => (
        <g key={b.label}>
          <rect x={x(b.from)} y={P.t} width={x(b.to) - x(b.from)} height={H - P.t - P.b} fill={b.color} />
          <text x={(x(b.from) + x(b.to)) / 2} y={P.t - 10} textAnchor="middle" className={`${b.text} ${fs}`}>
            {b.label}
          </text>
        </g>
      ))}
      {[0, top / 2, top].map((p) => (
        <g key={p}>
          <line x1={P.l} x2={W - P.r} y1={y(p)} y2={y(p)} stroke="rgb(245 244 243 / 0.1)" />
          <text x={P.l - 6} y={y(p) + 4} textAnchor="end" className={`fill-fg-3 ${fs}`}>{formatPct(p)}</text>
        </g>
      ))}
      {ticks.map((t) => (
        <text key={t} x={x(t)} y={H - 8} textAnchor="middle" className={`fill-fg-3 ${fs}`}>{t}d</text>
      ))}
      <path d={area} fill="rgb(217 185 138 / 0.10)" />
      <path d={line} fill="none" stroke="var(--color-gold-hi)" strokeWidth="2" />
      {/* Limite no topo, à esquerda da linha: ali a curva já está baixa, sem colisão com os ticks do eixo. */}
      <line x1={x(maxCycle)} x2={x(maxCycle)} y1={P.t} y2={H - P.b} stroke="var(--color-risk)" strokeDasharray="3 3" />
      <text x={x(maxCycle) - 5} y={P.t + 16} textAnchor="end" className={`fill-risk ${fs}`}>limite {maxCycle}d</text>
    </svg>
  );
}

function DecideCurve({ curve, maxCycle }: { curve: number[]; maxCycle: number }) {
  return (
    <figure>
      <CurveSvg curve={curve} maxCycle={maxCycle} compact={false} />
      <CurveSvg curve={curve} maxCycle={maxCycle} compact />
      <figcaption className="mt-2 text-[13px] leading-relaxed text-fg-2">
        Idade do deal (dias desde o engajamento) × chance de ele se decidir, ganho ou perdido, nos próximos {HORIZON_DAYS} dias. Calculado com todo o histórico,
        incluindo os deals que seguem abertos. Depois da fase de decisão, a chance despenca: o deal esfria e tende a virar zumbi.
      </figcaption>
    </figure>
  );
}

export function HowItWorks({ curve, maxCycle, globalWinRate }: { curve: number[]; maxCycle: number; globalWinRate: number }) {
  const { peak, peakAge, start, end } = phases(curve);
  return (
    <div className="space-y-6">
      <div className="grid gap-3 md:grid-cols-3">
        <Card tag={`até ${VALUE_WEIGHT} pts`} title="Valor" color="bg-sky">
          O preço do produto, que vai de US$ 55 a US$ 26 mil. Para o GTK 500 não engolir tudo, cada vez que o preço dobra o deal ganha o mesmo tanto de pontos. É o fator que mais separa um deal do outro.
        </Card>
        <Card tag={`até ${MOMENTUM_WEIGHT} pts`} title="Momento" color="bg-gold">
          A chance de o deal se decidir no próximo mês, pela idade dele. O pico é aos {peakAge} dias ({formatPct(peak)} se decidem no mês seguinte) e vale {MOMENTUM_WEIGHT} pts. Entre {start} e {end} dias o deal está na fase de decisão. Depois disso, ele esfria.
        </Card>
        <Card tag="fora do ranking" title="Zumbi" color="bg-risk">
          Nenhum deal do histórico fechou depois de {maxCycle} dias. Deal mais velho que isso vai para a pilha Encerrar: confirmar se está vivo ou marcar como perdido. Dos 411 deals que estavam nessa situação em datas passadas, nenhum fechou depois.
        </Card>
      </div>

      <div className="rounded-xl border border-line bg-navy p-5">
        <DecideCurve curve={curve} maxCycle={maxCycle} />
      </div>

      <div className="rounded-xl border border-line bg-navy p-5">
        <h3 className="font-medium text-fg">Como cada ideia foi testada</h3>
        <p className="mt-1 text-sm leading-relaxed text-fg-2">
          Voltamos a datas passadas e pontuamos os deals só com o que se sabia naquele dia. Depois conferimos o que aconteceu. A nota vai de 0,5 (cara ou coroa: o
          critério não ajuda) a 1 (acerta sempre).
        </p>
        <table className="mt-4 w-full text-sm">
          <tbody className="divide-y divide-line">
            {[
              ["Momento (idade → decisão em 30 dias)", "0,65", "entra", "Separa quem vai se decidir logo. A previsão média (25%) bateu com o que aconteceu (26%)."],
              ["Chance de ganhar por vendedor", "0,51", "fora", "Varia de 55% a 70%, mas não se repete de um semestre para o outro."],
              ["Chance por produto ou setor", "0,50", "fora", "Todos ficam entre 60% e 65%."],
              ["Tamanho da conta", "—", "fora", "De 61% a 66% entre faixas de receita e funcionários, sem padrão."],
              ["Fim de trimestre (81% × 52%)", "—", "fora", "O efeito vale para o mês inteiro, não só para os últimos dias. Parece artefato dos dados, não comportamento de venda."],
            ].map(([h, m, v, w]) => (
              <tr key={h} className="align-top">
                <td className="py-2.5 pr-4 text-fg">{h}</td>
                <td className="tabular whitespace-nowrap py-2.5 pr-3 text-[13px] text-fg-2">{m}</td>
                <td className={`whitespace-nowrap py-2.5 pr-4 text-[13px] ${v === "entra" ? "text-gold-hi" : "text-fg-3"}`}>{v}</td>
                <td className="py-2.5 text-fg-2">{w}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-4 text-sm leading-relaxed text-fg-2">
          Conclusão: neste CRM, todo deal vivo tem ~{formatPct(globalWinRate)} de chance de ser ganho. O que muda é <span className="text-fg">quanto vale</span>,{" "}
          <span className="text-fg">quando se decide</span> e <span className="text-fg">se ainda está vivo</span>. O alerta de janela aparece quando faltam {WINDOW_ALERT_DAYS} dias
          ou menos para o limite. No empate de score, vem primeiro o deal mais perto do limite.
        </p>
      </div>
    </div>
  );
}

function Card({ tag, title, color, children }: { tag: string; title: string; color: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-navy p-5">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 font-medium text-fg">
          <i className={`size-2 rounded-full ${color}`} aria-hidden />
          {title}
        </span>
        <span className="text-[13px] text-fg-3">{tag}</span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-fg-2">{children}</p>
    </div>
  );
}
