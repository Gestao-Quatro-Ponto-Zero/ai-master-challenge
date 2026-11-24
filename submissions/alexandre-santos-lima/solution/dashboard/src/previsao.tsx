import { useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import raw from "./sugestoes.json";
import { dec, int, pct } from "./format";
import type { Palette } from "./theme";

const C = raw.curva.map((c) => ({ ...c, faixa: [c.lo, c.hi] as [number, number] }));
const perto = (b: number) => C.reduce((a, c) => (Math.abs(c.base - b) < Math.abs(a.base - b) ? c : a));

export function Previsao({ pal }: { pal: Palette }) {
  const [base, setBase] = useState(raw.base_atual);
  const p = perto(base);
  const sf = raw.safra;
  const obsMax = raw.base_obs[1];
  return (
    <section className="block" id="previsao">
      <div className="eyebrow">Previsão</div>
      <h2>O que esperar daqui para a frente, se nada mudar</h2>
      <p className="lede">Só o que os dados sustentam: a proporção que cancela em cada safra e quantos registros de churn esperar para um
        tamanho de base. Não há previsão por data, porque ela exigiria prever o crescimento da base, e as datas de encerramento não são confiáveis.</p>
      <div className="grid2">
        <div className="card">
          <h3>De cada 100 assinaturas novas, cerca de {dec(sf.taxa * 100, 0)} serão canceladas</h3>
          <div className="stats">
            <span><b>{pct(sf.taxa)}</b> das {int(sf.total)} assinaturas pagas</span>
            <span><b>{pct(sf.ic[0])} a {pct(sf.ic[1])}</b> faixa de 95%</span>
            <span><b>{pct(sf.pct_mrr_perdido)}</b> do MRR contratado</span>
          </div>
          <div className="big-range" aria-label={`Entre ${dec(sf.ic[0] * 100, 0)} e ${dec(sf.ic[1] * 100, 0)} de cada 100`}>
            {Array.from({ length: 100 }, (_, i) => (
              <i key={i} style={{ background: i < Math.round(sf.ic[0] * 100) ? pal["--s2"] : i < Math.round(sf.ic[1] * 100) ? pal["--s2"] : pal["--grid"], opacity: i >= Math.round(sf.ic[0] * 100) && i < Math.round(sf.ic[1] * 100) ? 0.45 : 1 }} />
            ))}
          </div>
          <p className="foot">Cada quadrado é uma assinatura. Laranja forte: o mínimo esperado ({dec(sf.ic[0] * 100, 0)}). Laranja claro: até onde a faixa vai ({dec(sf.ic[1] * 100, 0)}).
            Vale para o horizonte observado (até 2 anos de vida da assinatura).</p>
        </div>
        <div className="card">
          <h3>Com {int(p.base)} assinaturas ativas, esperam-se {dec(p.esperado, 0)} registros de churn por mês</h3>
          <div className="stats">
            <span><b>{dec(p.lo, 0)} a {dec(p.hi, 0)}</b> faixa de 95%</span>
            <span><b>{p.extrapolado ? "extrapolação" : "dentro do observado"}</b> {p.extrapolado ? `(acima de ${int(obsMax)})` : ""}</span>
          </div>
          <label className="slider">
            <span>Assinaturas ativas</span>
            <input type="range" min={500} max={C[C.length - 1].base} step={50} value={base} onChange={(e) => setBase(Number(e.target.value))} aria-label="Assinaturas ativas" />
            <output>{int(p.base)}</output>
          </label>
          <ResponsiveContainer width="100%" height={210}>
            <ComposedChart data={C} margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid vertical={false} stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="base" domain={[0, 7500]} ticks={[0, 1500, 3000, 4500, 6000, 7500]} allowDataOverflow stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false}
                tickFormatter={(v) => int(v)} label={{ value: "assinaturas ativas", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false} axisLine={false} width={40} />
              <ReferenceArea x1={obsMax} x2={C[C.length - 1].base} fill={pal["--grid"]} fillOpacity={0.6}
                label={{ value: "extrapolação", position: "insideTop", fill: pal["--muted"], fontSize: 11 }} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const c = payload[0].payload as (typeof C)[number];
                return (
                  <div className="tt">
                    <b>{int(c.base)} assinaturas ativas</b>
                    <div className="row"><span>Esperado por mês</span><span>{dec(c.esperado, 0)}</span></div>
                    <div className="row"><span>Faixa de 95%</span><span>{dec(c.lo, 0)} a {dec(c.hi, 0)}</span></div>
                  </div>
                );
              }} />
              <Area dataKey="faixa" stroke="none" fill={pal["--s1"]} fillOpacity={0.18} isAnimationActive={false} activeDot={false} />
              <Line dataKey="esperado" stroke={pal["--s1"]} strokeWidth={2} dot={false} isAnimationActive={false} />
              <ReferenceDot x={p.base} y={p.esperado} r={5} fill={pal["--s2"]} stroke={pal["--surface"]} strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="foot">Modelo da seção “Base, mês e uso” (96% da variação explicada). Área cinza: tamanhos de base nunca observados, previsão menos segura.</p>
        </div>
      </div>
    </section>
  );
}
