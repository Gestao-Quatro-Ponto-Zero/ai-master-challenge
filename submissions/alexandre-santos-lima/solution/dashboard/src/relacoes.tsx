import {
  Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart,
  Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import raw from "./mes_uso.json";
import { dec, int, mes, pct, pval } from "./format";
import { Tecnico } from "./charts";
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
function Stats({ itens, extra }: { itens: [string, string][]; extra?: React.ReactNode }) {
  return (
    <Tecnico>
      <div className="stats">{itens.map(([k, v]) => <span key={k}><b>{v}</b> {k}</span>)}</div>
      {extra}
    </Tecnico>
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
      <h2>Os cancelamentos acompanham o número de clientes, e não a época do ano nem o uso do produto</h2>
      <p className="lede">Cada gráfico testa uma explicação possível para o número de cancelamentos. O começo de 2023, quando havia pouquíssimos
        clientes, e dezembro de 2024, que tem um erro de registro no fim dos dados, aparecem nos gráficos em cinza e ficam fora das contas.</p>

      {/* ------------------------------------------------ BASE */}
      <h3 className="sub">1. Número de clientes</h3>
      <div className="grid2">
        <div className="card">
          <h3>O número de clientes explica {pct(S.r2, 0)} das variações nos cancelamentos</h3>
          <p className="note">Cada ponto é um mês. Quanto mais clientes ativos, mais cancelamentos, quase na mesma proporção. A linha mostra o que se esperaria só pelo número de clientes.</p>
          <Stats itens={[["da variação explicada (pseudo-R²)", pct(S.r2, 0)], [`elasticidade, IC 95% ${dec(S.elasticidade_ic[0], 2)} a ${dec(S.elasticidade_ic[1], 2)}`, dec(S.elasticidade, 2)]]}
            extra={<p>Regressão quase-Poisson com log do nº de assinaturas ativas, meses de jul/23 a nov/24. Elasticidade 1 = cancelamentos proporcionais ao nº de clientes.</p>} />
          <Leg pal={pal} itens={[["mês usado na conta", "--s1", "dot"], ["mês fora da conta", "--neutral", "dot"], ["esperado pelo nº de clientes", "--s2", "line"]]} />
          <ResponsiveContainer width="100%" height={260}>
            <ComposedChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="base" domain={[0, "dataMax"]} {...ax(pal)} tickFormatter={(v) => int(v)}
                label={{ value: "clientes ativos no mês (assinaturas)", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="cancelamentos" {...ax(pal)} axisLine={false} width={40} />
              <Tooltip content={tipMes as never} cursor={{ stroke: pal["--axis"] }} />
              <Line data={raw.curva} dataKey="esp" stroke={pal["--s2"]} strokeWidth={2} dot={false} isAnimationActive={false} activeDot={false} />
              <Scatter data={fora} dataKey="cancelamentos" fill={pal["--neutral"]} isAnimationActive={false} />
              <Scatter data={est} dataKey="cancelamentos" fill={pal["--s1"]} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>{S.dentro_faixa} de {S.n_estavel} meses ficaram dentro do esperado</h3>
          <p className="note">A faixa azul mostra quantos cancelamentos seriam normais em cada mês só pelo número de clientes. Os pontos laranja são os cancelamentos reais.</p>
          <Stats itens={[["tendência além do nº de clientes", `p = ${pval(S.p_tendencia)}`], ["meses dentro da faixa de 95%", `${S.dentro_faixa}/${S.n_estavel}`]]} />
          <Leg pal={pal} itens={[["faixa normal", "--s1", "band"], ["esperado", "--s1", "line"], ["cancelamentos reais", "--s2", "dot"]]} />
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
          <p className="foot">Fora da faixa: só fev/24 ({int(feb.cancelamentos)} contra {dec(feb.esp, 0)} esperados). Dez/24 fica acima por causa do erro de registro no fim dos dados.</p>
        </div>
      </div>

      {/* ------------------------------------------------ MÊS */}
      <h3 className="sub">2. Época do ano</h3>
      <div className="card">
        <h3>Não há uma época do ano comprovadamente pior</h3>
        <p className="note">Cada barra compara os cancelamentos do mês com o esperado pelo número de clientes. Acima da linha, o mês cancelou mais que o normal.
          Se houvesse uma época ruim, as barras de 2023 e de 2024 daquele mês ficariam as duas bem acima da linha. Só dezembro fica acima
          nos dois anos, e dezembro de 2024 tem o erro de registro do fim dos dados; os outros meses ficam perto da linha ou de lados opostos.</p>
        <Stats itens={[["efeito do mês do ano", `p = ${pval(S.p_sazonal)}`], [`concordância 2023 × 2024 (${S.n_saz} meses comparáveis)`, `ρ = ${dec(S.rho_saz, 2)}`]]}
          extra={<p>Barras = cancelados ÷ esperado pelo modelo. Linha em 1,0 = igual ao esperado.</p>} />
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
        <div className="warn">Barras claras: meses de 2023 com muito poucos clientes, em que qualquer variação parece grande (janeiro de 2023 passa do limite do gráfico).
          Com só dois anos de dados, não dá para descartar de vez uma época ruim. O que dá para dizer é que nenhuma apareceu.</div>
      </div>

      {/* ------------------------------------------------ USO */}
      <h3 className="sub">3. Uso do produto</h3>
      <div className="grid2">
        <div className="card">
          <h3>Parece que quem usa menos cancela mais…</h3>
          <p className="note">Cada ponto é um mês. Parece uma relação forte, mas é ilusão: os clientes aumentaram e o uso total ficou igual. Então o uso por
            cliente caiu e os cancelamentos subiram ao mesmo tempo, sem que um cause o outro.</p>
          <Stats itens={[["correlação sem descontar o crescimento", `ρ = ${dec(S.rho_cru, 2)}`]]} />
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="uso_por_assinatura" {...ax(pal)} tickFormatter={(v) => dec(v, 0)}
                label={{ value: "uso do produto por cliente", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="cancelamentos" {...ax(pal)} axisLine={false} width={40} />
              <ZAxis range={[60, 60]} />
              <Tooltip content={tipMes as never} />
              <Scatter data={est} fill={pal["--neutral"]} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>…mas, tirando o efeito do crescimento, não há relação</h3>
          <p className="note">Os mesmos meses, sem o efeito do crescimento. Se usar menos levasse a cancelar, os pontos formariam uma linha descendo da
            esquerda para a direita. Não formam: estão espalhados, com uma leve subida que pode ser acaso.</p>
          <Stats itens={[["descontando o nº de clientes", `ρ = ${dec(S.rho_controlado, 2)}, p = ${pval(S.p_controlado)}`], ["variação de um mês para o outro", `ρ = ${dec(S.rho_delta, 2)}, p = ${pval(S.p_delta)}`]]}
            extra={<p>Resíduos dos dois eixos contra o log do nº de assinaturas ativas; eixo vertical em escala log.</p>} />
          <ResponsiveContainer width="100%" height={240}>
            <ScatterChart margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="uso_resid" {...ax(pal)} tickFormatter={(v) => dec(v, 2)} domain={[-0.15, 0.15]}
                label={{ value: "uso acima (+) ou abaixo (−) do normal", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis type="number" dataKey="cancel_resid" {...ax(pal)} axisLine={false} width={44} tickFormatter={(v) => dec(v, 1)} />
              <ReferenceLine x={0} stroke={pal["--axis"]} />
              <ReferenceLine y={0} stroke={pal["--axis"]} />
              <ZAxis range={[60, 60]} />
              <Tooltip content={tipMes as never} />
              <Scatter data={resid} fill={pal["--s1"]} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
          <p className="foot">Eixo vertical: cancelamentos acima (+) ou abaixo (−) do normal para o número de clientes.</p>
        </div>
      </div>

      <div className="grid2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>O cliente continua usando o produto depois de “cancelar”</h3>
          <p className="note" style={{ fontSize: 14 }}><b>{dec(S.pct_usa_depois * 100, 0)} de cada 100</b> clientes seguem usando depois do cancelamento registrado, e usam
            o mesmo tanto: em média {dec(S.antes_media, 0)} usos nos 90 dias antes e {dec(S.depois_media, 0)} nos 90 dias depois.</p>
          <Stats itens={[["média 90 dias antes", dec(S.antes_media, 1)], ["média 90 dias depois", dec(S.depois_media, 1)], ["diferença (Wilcoxon pareado)", `p = ${pval(S.p_antes_depois)}`]]} />
          <p className="note">Cada ponto é um cancelamento registrado ({int(S.n_antes_depois)}, até out/24). Se o cliente tivesse saído de verdade, os pontos
            ficariam todos no chão do gráfico (uso zero depois). Ficam espalhados em volta da linha de “igual antes e depois”.</p>
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
                return <Box><b>Cancelamento registrado</b><Row k="90 dias antes" v={int(p.antes)} /><Row k="90 dias depois" v={int(p.depois)} /></Box>;
              }} />
              <Scatter data={ad} fill={pal["--s1"]} fillOpacity={0.45} isAnimationActive={false} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Quem cancelou e quem ficou usam o produto do mesmo jeito</h3>
          <p className="note">Porcentagem de clientes em cada faixa de uso. As barras laranja (cancelaram) e azuis (ficaram) quase se sobrepõem.</p>
          <Stats itens={[["AUC (0,5 = não separa)", dec(S.auc_conta, 2)], ["diferença entre distribuições (KS)", `p = ${pval(S.p_ks)}`]]} />
          <Leg pal={pal} itens={[["cancelaram", "--s2"], ["ficaram", "--s1"]]} />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={raw.hist_conta} margin={{ top: 10, right: 8, left: 0, bottom: 14 }} barCategoryGap="16%" barGap={2}>
              <CartesianGrid vertical={false} stroke={pal["--grid"]} />
              <XAxis dataKey="faixa" {...ax(pal)} interval="preserveStartEnd" tick={{ fill: pal["--muted"], fontSize: 10 }}
                label={{ value: "quanto o cliente usou o produto (total)", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis {...ax(pal)} axisLine={false} width={40} domain={[0, 0.3]} ticks={[0, 0.1, 0.2, 0.3]} tickFormatter={(v) => pct(v, 0)} />
              <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                return <Box><b>{label} eventos</b>{payload.map((p) => <Row key={String(p.name)} k={String(p.name)} v={pct(Number(p.value))} />)}</Box>;
              }} />
              <Bar dataKey="churn" name="Cancelaram" fill={pal["--s2"]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
              <Bar dataKey="retida" name="Ficaram" fill={pal["--s1"]} radius={[3, 3, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="verdict"><span className="tag partial">Conclusão</span>
        <span>O número de cancelamentos sobe porque a empresa tem mais clientes, e não por causa da época do ano ou do uso do produto. E o cliente
          que “cancela” continua usando o produto do mesmo jeito: o registro de cancelamento não marca a saída real do cliente.</span>
      </div>
    </section>
  );
}
