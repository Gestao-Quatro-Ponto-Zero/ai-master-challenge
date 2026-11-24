import { Area, AreaChart, Bar, BarChart, Cell, Line, LineChart, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Tip } from "./charts";
import { dec, int, mes, pct, usdK } from "./format";
import type { Palette } from "./theme";

type M = { mes: string; taxa_churn_mrr: number | null; taxa_churn_assinaturas: number | null; uso_eventos: number; uso_por_assinatura_ativa: number | null };

type Props = {
  pal: Palette;
  mensal: M[];
  sat: { nota: string; tickets: number }[];
  kpis: { contas: number; mrr_ativo: number; variaveis_testadas: number; variaveis_significativas: number; pct_sem_nota: number };
  def: { so_flag: number; so_evento: number; ambos: number; nenhum: number };
};

function Claim({ quem, frase, veredito, tipo, children, prova }: {
  quem: string; frase: string; veredito: string; tipo: "true" | "false" | "partial"; children: React.ReactNode; prova: string;
}) {
  return (
    <article className="claim">
      <div className="claim-who">{quem} diz</div>
      <p className="claim-said">“{frase}”</p>
      <div className="claim-chart">{children}</div>
      <div className="claim-verdict"><span className={`tag ${tipo}`}>{veredito}</span></div>
      <p className="claim-proof">{prova}</p>
    </article>
  );
}

export function Hero({ pal, mensal, sat, kpis, def }: Props) {
  const serie = mensal.filter((m) => m.mes >= "2024-01");
  const jun = mensal.find((m) => m.mes === "2024-06")!;
  const dez = mensal.find((m) => m.mes === "2024-12")!;
  const jan = mensal.find((m) => m.mes === "2024-01")!;
  const nov = mensal.find((m) => m.mes === "2024-11")!;
  const usoQueda = 1 - (dez.uso_por_assinatura_ativa ?? 0) / (jan.uso_por_assinatura_ativa ?? 1);
  const usoIdx = serie.map((m) => ({
    mes: m.mes,
    total: (m.uso_eventos / serie[0].uso_eventos) * 100,
    porAssinatura: ((m.uso_por_assinatura_ativa ?? 0) / (serie[0].uso_por_assinatura_ativa ?? 1)) * 100,
  }));
  const satResp = sat.filter((s) => s.nota !== "Sem nota");
  const media = satResp.reduce((a, b) => a + Number(b.nota) * b.tickets, 0) / satResp.reduce((a, b) => a + b.tickets, 0);
  const vezes = (dez.taxa_churn_mrr ?? 0) / (jun.taxa_churn_mrr ?? 1);
  const total = def.so_flag + def.ambos + def.so_evento + def.nenhum;

  return (
    <section id="resumo" className="hero2">
      <div className="eyebrow">RavenStack · diagnóstico de churn · jan/23 a dez/24</div>
      <h1>O churn subiu. O resto da história estava mal medido.</h1>

      {/* ---------------------------------------------------- número principal */}
      <div className="headline">
        <div className="headline-num">
          <div className="hn-label">Receita perdida por churn, por mês</div>
          <div className="hn-value">{pct(dez.taxa_churn_mrr)}</div>
          <div className="hn-sub">do MRR em dez/24, <b>{dec(vezes, 0)}×</b> o patamar de jun/24 ({pct(jun.taxa_churn_mrr)})</div>
          <div className="hn-note">Parte de dezembro é efeito do fim dos dados. Sem ele, a alta já aparece em nov/24: {pct(nov.taxa_churn_mrr)}, {dec((nov.taxa_churn_mrr ?? 0) / (jun.taxa_churn_mrr ?? 1), 0)}× junho.</div>
          <ul className="hn-facts">
            <li><b>{int(kpis.contas)}</b> contas · <b>{usdK(kpis.mrr_ativo)}</b> de MRR ativo</li>
            <li><b>{int(kpis.variaveis_significativas)}</b> de {int(kpis.variaveis_testadas)} variáveis explicam quem sai</li>
          </ul>
        </div>
        <div className="headline-chart" aria-label="Taxa mensal de churn de MRR em 2024">
          <ResponsiveContainer width="100%" height={210}>
            <AreaChart data={serie} margin={{ top: 28, right: 44, left: 4, bottom: 0 }}>
              <defs>
                <linearGradient id="g-mrr" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={pal["--s2"]} stopOpacity={0.28} />
                  <stop offset="100%" stopColor={pal["--s2"]} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="mes" tickFormatter={mes} stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false} interval="preserveStartEnd" minTickGap={24} />
              <YAxis hide domain={[0, "dataMax"]} />
              <Tooltip cursor={{ stroke: pal["--axis"] }} content={<Tip fmt={(v) => pct(v)} labelFmt={mes} />} />
              <Area type="monotone" dataKey="taxa_churn_mrr" name="Churn de MRR" stroke={pal["--s2"]} strokeWidth={2.5} fill="url(#g-mrr)" isAnimationActive={false}
                activeDot={{ r: 4, stroke: pal["--surface"], strokeWidth: 2 }} />
              <ReferenceDot x="2024-06" y={jun.taxa_churn_mrr ?? 0} r={4} fill={pal["--s2"]} stroke={pal["--surface"]} strokeWidth={2}
                label={{ value: pct(jun.taxa_churn_mrr), position: "top", fill: pal["--ink-2"], fontSize: 12 }} />
              <ReferenceDot x="2024-12" y={dez.taxa_churn_mrr ?? 0} r={5} fill={pal["--s2"]} stroke={pal["--surface"]} strokeWidth={2}
                label={{ value: pct(dez.taxa_churn_mrr), position: "left", fill: pal["--ink"], fontSize: 13, fontWeight: 600 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ---------------------------------------------------- o que cada área disse */}
      <h2 className="claims-title">O que cada área disse, e o que os dados mostram</h2>
      <div className="claims">
        <Claim quem="O CEO" frase="O churn subiu." veredito="Verdade" tipo="true"
          prova={`Não é só volume: a taxa sobre a base ativa saiu de ~1% para ${pct(dez.taxa_churn_assinaturas)} das assinaturas por mês.`}>
          <ResponsiveContainer width="100%" height={92}>
            <LineChart data={serie} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <YAxis hide domain={[0, "dataMax"]} />
              <XAxis dataKey="mes" hide />
              <Tooltip cursor={{ stroke: pal["--axis"] }} content={<Tip fmt={(v) => pct(v)} labelFmt={mes} />} />
              <Line type="monotone" dataKey="taxa_churn_assinaturas" name="Assinaturas encerradas" stroke={pal["--s1"]} strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="mini-cap">taxa mensal de churn, jan → dez/24</div>
        </Claim>

        <Claim quem="Produto" frase="O uso da plataforma cresceu." veredito="Só no total" tipo="false"
          prova={`O volume ficou parado enquanto a base se multiplicou: cada assinatura usa ${pct(usoQueda, 0)} menos que em jan/24.`}>
          <ResponsiveContainer width="100%" height={92}>
            <LineChart data={usoIdx} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
              <YAxis hide domain={[0, 120]} />
              <XAxis dataKey="mes" hide />
              <Tooltip cursor={{ stroke: pal["--axis"] }} content={<Tip fmt={(v) => `${dec(v, 0)} (jan/24 = 100)`} labelFmt={mes} />} />
              <Line type="monotone" dataKey="total" name="Uso total" stroke={pal["--neutral"]} strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="porAssinatura" name="Uso por assinatura" stroke={pal["--s1"]} strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="mini-cap">
            <span><i style={{ background: pal["--neutral"] }} />total</span>
            <span><i style={{ background: pal["--s1"] }} />por assinatura</span>
            <span>(jan/24 = 100)</span>
          </div>
        </Claim>

        <Claim quem="CS" frase="A satisfação está ok." veredito="Mal medida" tipo="partial"
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
        </Claim>
      </div>

      {/* ---------------------------------------------------- o que ninguém disse */}
      <div className="nobody">
        <div className="nobody-text">
          <div className="claim-who">O que ninguém disse</div>
          <p className="nobody-said">A empresa não sabe quem saiu, nem por quê.</p>
          <p className="claim-proof">
            Dois registros de churn por conta discordam em {int(def.so_flag + def.so_evento)} das {int(total)} contas, e o motivo de saída
            registrado não tem relação com o comentário do cliente. Antes de atacar a causa, é preciso medir direito.
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
