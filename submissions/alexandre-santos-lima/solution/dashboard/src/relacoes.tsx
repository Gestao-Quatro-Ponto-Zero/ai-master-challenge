import {
  Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart,
  Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import raw from "./mes_uso.json";
import { dec, int, mes, pct, pval } from "./format";
import type { Palette } from "./theme";

type Mes = (typeof raw.mensal)[number];
const S = raw.stats;
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

const ax = (pal: Palette) => ({ stroke: pal["--axis"], tick: { fill: pal["--muted"], fontSize: 11 }, tickLine: false });

function Box({ children }: { children: React.ReactNode }) {
  return <div className="tt">{children}</div>;
}
function Row({ k, v }: { k: string; v: string }) {
  return <div className="row"><span>{k}</span><span>{v}</span></div>;
}
function Stats({ itens }: { itens: [string, string][] }) {
  return (
    <div className="stats">
      {itens.map(([k, v]) => <span key={k}><b>{v}</b> {k}</span>)}
    </div>
  );
}
function Leg({ itens, pal }: { itens: ([string, keyof Palette] | [string, keyof Palette, "dot" | "line" | "band"])[]; pal: Palette }) {
  return (
    <div className="legend">
      {itens.map(([l, c, f]) => (
        <span key={l}>
          <i style={{
            background: pal[c], opacity: f === "band" ? 0.25 : 1,
            height: f === "line" ? 2 : 10, borderRadius: f === "dot" ? 999 : 3, verticalAlign: f === "line" ? 3 : -1,
          }} />{l}
        </span>
      ))}
    </div>
  );
}

export function Relacoes({ pal }: { pal: Palette }) {
  const M = raw.mensal as Mes[];
  const desde = M.filter((m) => m.mes >= "2023-07");
  const pontos = M.filter((m) => m.base > 0);
  const est = pontos.filter((m) => m.estavel);
  const fora = pontos.filter((m) => !m.estavel);
  const saz = raw.sazonal.map((s) => ({ ...s, nome: MESES[s.mes - 1] }));
  const resid = est.filter((m) => m.cancel_resid != null);
  const ad = raw.antes_depois;
  const maxAd = Math.max(...ad.map((p) => Math.max(p.antes, p.depois)));
  const topo = Math.ceil(maxAd / 40) * 40;
  const marcas = Array.from({ length: topo / 40 + 1 }, (_, i) => i * 40);
  const feb = M.find((m) => m.mes === "2024-02")!;

  const tipMes = ({ active, payload }: { active?: boolean; payload?: { payload: Mes }[] }) => {
    if (!active || !payload?.length) return null;
    const m = payload[0].payload;
    return (
      <Box>
        <b>{mes(m.mes)}</b>
        <Row k="Cancelamentos" v={int(m.cancelamentos)} />
        <Row k="Esperado pela base" v={dec(m.esp, 1)} />
        <Row k="Faixa de 95%" v={`${dec(m.faixa[0], 0)} a ${dec(m.faixa[1], 0)}`} />
        <Row k="Assinaturas ativas" v={int(m.base)} />
      </Box>
    );
  };

  return (
    <section className="block" id="relacoes">
      <div className="eyebrow">O que determina os cancelamentos</div>
      <h2>Os cancelamentos seguem o tamanho da base, e não o mês nem o uso</h2>
      <p className="lede">Cada gráfico testa uma explicação. Os números ao lado de cada título são o resultado do teste estatístico.
        Os meses de jan–jun/23, com no máximo 5 cancelamentos, e dez/24, que tem o efeito do fim dos dados, entram nos gráficos mas ficam fora dos testes.</p>

      {/* ------------------------------------------------ BASE */}
      <h3 className="sub">1. Tamanho da base</h3>
      <div className="grid2">
        <div className="card">
          <h3>A base explica {pct(S.r2, 0)} da variação dos cancelamentos</h3>
          <Stats itens={[["da variação explicada", pct(S.r2, 0)], [`elasticidade (IC ${dec(S.elasticidade_ic[0], 2)} a ${dec(S.elasticidade_ic[1], 2)})`, dec(S.elasticidade, 2)]]} />
          <p className="note">Cada ponto é um mês. A curva é o modelo “cancelamentos proporcionais à base”. Elasticidade 1 = proporcional.</p>
          <Leg pal={pal} itens={[["mês usado no teste", "--s1", "dot"], ["mês fora do teste", "--neutral", "dot"], ["modelo", "--s2", "line"]]} />
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="base" domain={[0, "dataMax"]} {...ax(pal)} tickFormatter={(v) => int(v)}
                label={{ value: "assinaturas ativas no mês", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="cancelamentos" {...ax(pal)} axisLine={false} width={40} />
              <Tooltip content={tipMes as never} cursor={{ stroke: pal["--axis"] }} />
              <Line data={raw.curva} dataKey="esp" stroke={pal["--s2"]} strokeWidth={2} dot={false} isAnimationActive={false} activeDot={false} />
              <Scatter data={fora} dataKey="cancelamentos" fill={pal["--neutral"]} isAnimationActive={false} />
              <Scatter data={est} dataKey="cancelamentos" fill={pal["--s1"]} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>{S.dentro_faixa} de {S.n_estavel} meses caem dentro do esperado pela base</h3>
          <Stats itens={[["tendência além da base", `p = ${pval(S.p_tendencia)}`], ["meses dentro da faixa", `${S.dentro_faixa}/${S.n_estavel}`]]} />
          <p className="note">Faixa: onde os cancelamentos cairiam 95% das vezes se dependessem só do tamanho da base.</p>
          <Leg pal={pal} itens={[["faixa esperada (95%)", "--s1", "band"], ["esperado", "--s1", "line"], ["observado", "--s2", "dot"]]} />
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart data={desde} margin={{ top: 10, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke={pal["--grid"]} />
              <XAxis dataKey="mes" tickFormatter={mes} {...ax(pal)} interval="preserveStartEnd" minTickGap={18} />
              <YAxis {...ax(pal)} axisLine={false} width={40} />
              <Tooltip content={tipMes as never} cursor={{ stroke: pal["--axis"] }} />
              <Area dataKey="faixa" stroke="none" fill={pal["--s1"]} fillOpacity={0.18} isAnimationActive={false} activeDot={false} />
              <Line dataKey="esp" stroke={pal["--s1"]} strokeWidth={1.5} dot={false} isAnimationActive={false} activeDot={false} />
              <Line dataKey="cancelamentos" stroke="none" isAnimationActive={false}
                dot={{ r: 4, fill: pal["--s2"], stroke: pal["--surface"], strokeWidth: 2 }} activeDot={{ r: 5, fill: pal["--s2"] }} />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="foot">Fora da faixa: só fev/24 ({int(feb.cancelamentos)} contra {dec(feb.esp, 0)} esperados). Dez/24 fica acima, pelo efeito do fim dos dados.</p>
        </div>
      </div>

      {/* ------------------------------------------------ MÊS */}
      <h3 className="sub">2. Mês do ano</h3>
      <div className="card">
        <h3>Nenhum mês se repete acima ou abaixo do esperado nos dois anos</h3>
        <Stats itens={[["efeito do mês do ano", `p = ${pval(S.p_sazonal)}`], [`concordância 2023 × 2024 (${S.n_saz} meses comparáveis)`, `ρ = ${dec(S.rho_saz, 2)}`]]} />
        <p className="note">Cancelados ÷ esperado pela base em cada mês. Acima de 1, o mês cancelou mais que o tamanho da base explica.
          A linha em 1,0 marca o esperado. Se houvesse sazonalidade, as duas barras de cada mês ficariam do mesmo lado da linha.</p>
        <Leg pal={pal} itens={[["2023", "--s3"], ["2024", "--s1"]]} />
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={saz} margin={{ top: 10, right: 8, left: 0, bottom: 0 }} barCategoryGap="22%" barGap={2}>
            <CartesianGrid vertical={false} stroke={pal["--grid"]} />
            <XAxis dataKey="nome" {...ax(pal)} interval={0} />
            <YAxis {...ax(pal)} axisLine={false} width={40} domain={[0, 2]} ticks={[0, 0.5, 1, 1.5, 2]} allowDataOverflow tickFormatter={(v) => dec(v, 1)} />
            <ReferenceLine y={1} stroke={pal["--ink-2"]} />
            <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const s = payload[0].payload as (typeof saz)[number];
              return (
                <Box>
                  <b>{s.nome}</b>
                  <Row k="2023" v={`${dec(s.r2023, 2)}× (esperado ${dec(s.esp2023, 1)})`} />
                  <Row k="2024" v={`${dec(s.r2024, 2)}× (esperado ${dec(s.esp2024, 1)})`} />
                </Box>
              );
            }} />
            <Bar dataKey="r2023" name="2023" radius={[3, 3, 0, 0]} isAnimationActive={false}>
              {saz.map((s) => <Cell key={s.mes} fill={pal["--s3"]} fillOpacity={s.esp2023 < 5 ? 0.3 : 1} />)}
            </Bar>
            <Bar dataKey="r2024" name="2024" fill={pal["--s1"]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
        <div className="warn">Barras claras: meses de 2023 com menos de 5 cancelamentos esperados, nos quais a razão oscila só por acaso (jan/23 passa de 8× e foi cortado).
          Com apenas 2 anos de dados, cada mês aparece duas vezes: o teste mostra ausência de sinal sazonal, mas não prova que ele não existe.</div>
      </div>

      {/* ------------------------------------------------ USO */}
      <h3 className="sub">3. Uso do produto</h3>
      <div className="grid2">
        <div className="card">
          <h3>Aparente: menos uso, mais cancelamentos (ρ = {dec(S.rho_cru, 2)})</h3>
          <Stats itens={[["correlação crua", `ρ = ${dec(S.rho_cru, 2)}`]]} />
          <p className="note">Cada ponto é um mês. A correlação quase perfeita vem só do crescimento da base: o uso total fica parado,
            então o uso por assinatura cai, e os cancelamentos sobem junto com a base.</p>
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="uso_por_assinatura" {...ax(pal)} tickFormatter={(v) => dec(v, 0)}
                label={{ value: "uso por assinatura ativa", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="cancelamentos" {...ax(pal)} axisLine={false} width={40} />
              <ZAxis range={[60, 60]} />
              <Tooltip content={tipMes as never} />
              <Scatter data={est} fill={pal["--neutral"]} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Real: descontada a base, não há relação significativa</h3>
          <Stats itens={[["descontando a base", `ρ = ${dec(S.rho_controlado, 2)}, p = ${pval(S.p_controlado)}`], ["variação mês a mês", `ρ = ${dec(S.rho_delta, 2)}, p = ${pval(S.p_delta)}`]]} />
          <p className="note">Os mesmos meses, agora com o efeito da base removido dos dois eixos. Se menos uso causasse churn, os pontos
            formariam uma linha descendo da esquerda para a direita. A leve subida que aparece não é significativa e vai na direção oposta.</p>
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="uso_resid" {...ax(pal)} tickFormatter={(v) => dec(v, 2)} domain={[-0.15, 0.15]}
                label={{ value: "uso acima (+) ou abaixo (−) do esperado", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="cancel_resid" {...ax(pal)} axisLine={false} width={44} tickFormatter={(v) => dec(v, 1)} />
              <ReferenceLine x={0} stroke={pal["--axis"]} />
              <ReferenceLine y={0} stroke={pal["--axis"]} />
              <ZAxis range={[60, 60]} />
              <Tooltip content={tipMes as never} />
              <Scatter data={resid} fill={pal["--s1"]} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="foot">Eixo vertical: cancelamentos acima (+) ou abaixo (−) do esperado pela base, em escala log.</p>
        </div>
      </div>

      <div className="grid2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>O cliente usa igual antes e depois do churn</h3>
          <Stats itens={[["média 90 dias antes", dec(S.antes_media, 1)], ["média 90 dias depois", dec(S.depois_media, 1)], ["seguem usando depois", pct(S.pct_usa_depois, 0)], ["diferença", `p = ${pval(S.p_antes_depois)}`]]} />
          <p className="note">Cada ponto é um evento de churn ({int(S.n_antes_depois)} eventos até out/24). Uso da conta nos 90 dias antes e nos 90 dias depois.
            Se o churn fosse saída real, quase todos os pontos ficariam colados no eixo de baixo (uso zero depois).</p>
          <ResponsiveContainer width="100%" height={260}>
            <ScatterChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="antes" domain={[0, topo]} ticks={marcas} {...ax(pal)}
                label={{ value: "uso nos 90 dias antes", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="depois" domain={[0, topo]} ticks={marcas} {...ax(pal)} axisLine={false} width={40}
                label={{ value: "depois", angle: -90, position: "insideLeft", fill: pal["--muted"], fontSize: 11 }} />
              <ZAxis range={[24, 24]} />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: topo, y: topo }]} stroke={pal["--s2"]} strokeWidth={1.5}
                label={{ value: "igual antes e depois", position: "insideTopLeft", fill: pal["--ink-2"], fontSize: 11 }} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as { antes: number; depois: number };
                return <Box><b>Evento de churn</b><Row k="90 dias antes" v={int(p.antes)} /><Row k="90 dias depois" v={int(p.depois)} /></Box>;
              }} />
              <Scatter data={ad} fill={pal["--s1"]} fillOpacity={0.45} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Quem saiu e quem ficou usam o produto do mesmo jeito</h3>
          <Stats itens={[["AUC (0,5 = não separa)", dec(S.auc_conta, 2)], ["diferença entre distribuições", `p = ${pval(S.p_ks)}`]]} />
          <p className="note">% das contas em cada faixa de eventos de uso, separando contas com flag de churn das demais. As distribuições se sobrepõem.</p>
          <Leg pal={pal} itens={[["contas com churn", "--s2"], ["contas sem churn", "--s1"]]} />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={raw.hist_conta} margin={{ top: 10, right: 8, left: 0, bottom: 14 }} barCategoryGap="16%" barGap={2}>
              <CartesianGrid vertical={false} stroke={pal["--grid"]} />
              <XAxis dataKey="faixa" {...ax(pal)} interval="preserveStartEnd" tick={{ fill: pal["--muted"], fontSize: 10 }}
                label={{ value: "eventos de uso da conta (histórico)", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis {...ax(pal)} axisLine={false} width={40} domain={[0, 0.3]} ticks={[0, 0.1, 0.2, 0.3]} tickFormatter={(v) => pct(v, 0)} />
              <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                return <Box><b>{label} eventos</b>{payload.map((p) => <Row key={String(p.name)} k={String(p.name)} v={pct(Number(p.value))} />)}</Box>;
              }} />
              <Bar dataKey="churn" name="Com churn" fill={pal["--s2"]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="retida" name="Sem churn" fill={pal["--s1"]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="verdict"><span className="tag partial">Conclusão</span>
        <span>Os cancelamentos são proporcionais ao tamanho da base ({pct(S.r2, 0)} explicado), sem efeito de mês e sem relação com o uso.
          O cliente que “cancela” continua usando o produto do mesmo jeito, o que indica que o registro de churn não marca a saída real do cliente.</span>
      </div>
    </section>
  );
}
