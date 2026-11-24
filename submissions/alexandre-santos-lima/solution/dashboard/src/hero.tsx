import { Bar, BarChart, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { SafraBars, Tip, type Safra } from "./charts";
import { dec, int, mes, pct, usdK } from "./format";
import type { Palette } from "./theme";

type M = {
  mes: string; taxa_churn_mrr: number | null; taxa_churn_assinaturas: number | null; uso_eventos: number;
  uso_por_assinatura_ativa: number | null; eventos_churn: number; assinaturas_ativas: number;
};

type Props = {
  pal: Palette;
  mensal: M[];
  sat: { nota: string; tickets: number }[];
  kpis: { contas: number; mrr_ativo: number; variaveis_testadas: number; variaveis_significativas: number; pct_sem_nota: number };
  def: { so_flag: number; so_evento: number; ambos: number; nenhum: number };
  safras: Safra[];
  mediaSafra: number;
};

function Result({ tema, titulo, children, prova }: { tema: string; titulo: string; children: React.ReactNode; prova: string }) {
  return (
    <article className="claim">
      <div className="claim-who">{tema}</div>
      <p className="claim-said">{titulo}</p>
      <div className="claim-chart">{children}</div>
      <p className="claim-proof">{prova}</p>
    </article>
  );
}

function Cap({ itens, pal }: { itens: [string, keyof Palette][]; pal: Palette }) {
  return (
    <div className="mini-cap">
      {itens.map(([l, c]) => <span key={l}><i style={{ background: pal[c] }} />{l}</span>)}
      <span>(jan/24 = 100)</span>
    </div>
  );
}

export function Hero({ pal, mensal, sat, kpis, def, safras, mediaSafra }: Props) {
  const serie = mensal.filter((m) => m.mes >= "2024-01");
  const desde = mensal.filter((m) => m.mes >= "2023-07");
  const dez = mensal.find((m) => m.mes === "2024-12")!;
  const dez23 = mensal.find((m) => m.mes === "2023-12")!;
  const jan = serie[0];
  const usoQueda = 1 - (dez.uso_por_assinatura_ativa ?? 0) / (jan.uso_por_assinatura_ativa ?? 1);
  const idx = serie.map((m) => ({
    mes: m.mes,
    cancelamentos: (m.eventos_churn / jan.eventos_churn) * 100,
    base: (m.assinaturas_ativas / jan.assinaturas_ativas) * 100,
    usoTotal: (m.uso_eventos / jan.uso_eventos) * 100,
    usoPorAssinatura: ((m.uso_por_assinatura_ativa ?? 0) / (jan.uso_por_assinatura_ativa ?? 1)) * 100,
  }));
  const satResp = sat.filter((s) => s.nota !== "Sem nota");
  const media = satResp.reduce((a, b) => a + Number(b.nota) * b.tickets, 0) / satResp.reduce((a, b) => a + b.tickets, 0);
  const xEv = dez.eventos_churn / dez23.eventos_churn;
  const xBase = dez.assinaturas_ativas / dez23.assinaturas_ativas;
  const total = def.so_flag + def.ambos + def.so_evento + def.nenhum;
  const idxTip = <Tip fmt={(v) => `${dec(v, 0)} (jan/24 = 100)`} labelFmt={mes} />;

  return (
    <section id="resumo" className="hero2">
      <div className="eyebrow">RavenStack · diagnóstico de churn · jan/23 a dez/24</div>
      <h1>Não há sinal de que o churn piorou. A empresa cresceu, e mede mal.</h1>

      {/* ---------------------------------------------------- número principal */}
      <div className="headline">
        <div className="headline-num">
          <div className="hn-label">Cada safra de assinaturas perde</div>
          <div className="hn-value">{pct(mediaSafra)}</div>
          <div className="hn-sub">dos clientes, <b>sem piora: 12% nas safras de 2023, 9% nas de 2024</b>. O que cresceu foi a base.</div>
          <ul className="hn-facts">
            <li>Cancelamentos por mês: <b>{int(dez23.eventos_churn)} → {int(dez.eventos_churn)}</b> ({dec(xEv, 0)}×)</li>
            <li>Assinaturas ativas: <b>{int(dez23.assinaturas_ativas)} → {int(dez.assinaturas_ativas)}</b> ({dec(xBase, 0)}×)</li>
            <li><b>{int(kpis.variaveis_significativas)}</b> de {int(kpis.variaveis_testadas)} variáveis explicam quem sai · <b>{usdK(kpis.mrr_ativo)}</b> de MRR</li>
          </ul>
        </div>
        <div className="headline-pair">
          <div>
            <div className="hp-title">Cancelamentos por mês</div>
            <div className="hp-sub">sobem junto com a base de clientes</div>
            <ResponsiveContainer width="100%" height={170}>
              <BarChart data={desde} margin={{ top: 10, right: 4, left: 4, bottom: 0 }} barCategoryGap={2}>
                <XAxis dataKey="mes" tickFormatter={mes} stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 10 }} tickLine={false} interval="preserveStartEnd" minTickGap={30} />
                <YAxis hide />
                <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={<Tip fmt={(v) => int(v)} labelFmt={mes} />} />
                <Bar dataKey="eventos_churn" name="Cancelamentos" fill={pal["--s2"]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div>
            <div className="hp-title">% de cada safra que cancelou</div>
            <div className="hp-sub">por trimestre de entrada: estável</div>
            <SafraBars data={safras} media={mediaSafra} pal={pal} height={170} compact />
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------- resultados */}
      <h2 className="claims-title">Principais resultados</h2>
      <div className="claims">
        <Result tema="Churn" titulo="Os cancelamentos crescem no mesmo ritmo da base"
          prova="De dez/23 a dez/24, cancelamentos e assinaturas ativas cresceram 7×. A proporção de clientes que sai não aumentou.">
          <ResponsiveContainer width="100%" height={92}>
            <LineChart data={idx} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <YAxis hide domain={[0, "dataMax"]} />
              <XAxis dataKey="mes" hide />
              <Tooltip cursor={{ stroke: pal["--axis"] }} content={idxTip} />
              <Line type="monotone" dataKey="base" name="Assinaturas ativas" stroke={pal["--neutral"]} strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="cancelamentos" name="Cancelamentos" stroke={pal["--s2"]} strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <Cap pal={pal} itens={[["base ativa", "--neutral"], ["cancelamentos", "--s2"]]} />
        </Result>

        <Result tema="Uso" titulo={`O uso total está parado; por assinatura, caiu ${pct(usoQueda, 0)}`}
          prova={`O volume de uso ficou em ~10 mil eventos por mês enquanto a base de assinaturas cresceu.`}>
          <ResponsiveContainer width="100%" height={92}>
            <LineChart data={idx} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <YAxis hide domain={[0, 120]} />
              <XAxis dataKey="mes" hide />
              <Tooltip cursor={{ stroke: pal["--axis"] }} content={idxTip} />
              <Line type="monotone" dataKey="usoTotal" name="Uso total" stroke={pal["--neutral"]} strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="usoPorAssinatura" name="Uso por assinatura" stroke={pal["--s1"]} strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <Cap pal={pal} itens={[["uso total", "--neutral"], ["por assinatura", "--s1"]]} />
        </Result>

        <Result tema="Satisfação" titulo="A nota média não enxerga o cliente insatisfeito"
          prova={`A média ${dec(media, 1)} vem de quem respondeu. ${pct(kpis.pct_sem_nota, 0)} dos tickets não têm nota e não existe nenhuma nota 1 ou 2.`}>
          <ResponsiveContainer width="100%" height={92}>
            <BarChart data={sat} margin={{ top: 8, right: 8, left: 8, bottom: 0 }} barCategoryGap="18%">
              <YAxis hide />
              <XAxis dataKey="nota" tickLine={false} axisLine={{ stroke: pal["--axis"] }} tick={{ fill: pal["--muted"], fontSize: 10 }}
                tickFormatter={(v) => (v === "Sem nota" ? "s/ nota" : v)} interval={0} />
              <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={<Tip fmt={(v) => `${int(v)} tickets`} labelFmt={(l) => (l === "Sem nota" ? l : `Nota ${l}`)} />} />
              <Bar dataKey="tickets" name="Tickets" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                {sat.map((s) => <Cell key={s.nota} fill={s.nota === "Sem nota" ? pal["--s2"] : pal["--s1"]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mini-cap">tickets por nota (1 a 5)</div>
        </Result>
      </div>

      {/* ---------------------------------------------------- qualidade dos dados */}
      <div className="nobody">
        <div className="nobody-text">
          <div className="claim-who">Qualidade dos dados</div>
          <p className="nobody-said">Não há registro confiável de quem cancelou, quando e por quê.</p>
          <p className="claim-proof">
            Dois registros de churn por conta discordam em {int(def.so_flag + def.so_evento)} das {int(total)} contas, e o motivo de saída
            registrado não tem relação com o comentário do cliente. Nem a data de cancelamento é confiável: contratos anuais “terminam” em
            poucos dias. Antes de atacar a causa, é preciso medir direito.
          </p>
        </div>
        <div className="nobody-bar">
          <div className="venn" role="img" aria-label={`Só flag ${def.so_flag}, ambos ${def.ambos}, só evento ${def.so_evento}, nenhum ${def.nenhum}`}>
            <div style={{ flex: def.so_flag, background: pal["--s2"] }}>{def.so_flag}</div>
            <div style={{ flex: def.ambos, background: pal["--s1"] }}>{def.ambos}</div>
            <div style={{ flex: def.so_evento, background: pal["--s3"] }}>{def.so_evento}</div>
            <div style={{ flex: def.nenhum, background: pal["--neutral"], color: pal["--ink"] }}>{def.nenhum}</div>
          </div>
          <div className="mini-cap">
            <span><i style={{ background: pal["--s2"] }} />só flag</span>
            <span><i style={{ background: pal["--s1"] }} />os dois concordam</span>
            <span><i style={{ background: pal["--s3"] }} />só evento</span>
            <span><i style={{ background: pal["--neutral"] }} />nenhum</span>
          </div>
        </div>
        <a className="nobody-link" href="#definicoes">Ver detalhes ↓</a>
      </div>
    </section>
  );
}
