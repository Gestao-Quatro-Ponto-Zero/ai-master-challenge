import { useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import raw from "./sugestoes.json";
import { dec, int, pct } from "./format";
import { Tecnico } from "./charts";
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
      <p className="lede">Só o que os dados permitem afirmar: quantos clientes costumam cancelar e quantos cancelamentos esperar por mês para um certo
        número de clientes. Não dá para prever datas, porque isso exigiria adivinhar quanto a empresa vai crescer, e as datas de cancelamento anotadas não são confiáveis.</p>
      <div className="grid2">
        <div className="card">
          <h3>De cada 100 assinaturas novas, cerca de {dec(sf.taxa * 100, 0)} serão canceladas</h3>
          <p className="note" style={{ fontSize: 14 }}>Contando a margem de erro, entre {dec(sf.ic[0] * 100, 0)} e {dec(sf.ic[1] * 100, 0)} de cada 100. Isso equivale a cerca de
            {" "}{pct(sf.pct_mrr_perdido, 0)} da receita mensal contratada.</p>
          <Tecnico>
            <div className="stats">
              <span><b>{pct(sf.taxa)}</b> das {int(sf.total)} assinaturas pagas</span>
              <span><b>{pct(sf.ic[0])} a {pct(sf.ic[1])}</b> IC 95% (Wilson)</span>
              <span><b>{pct(sf.pct_mrr_perdido)}</b> do MRR contratado</span>
            </div>
          </Tecnico>
          <div className="big-range" aria-label={`Entre ${dec(sf.ic[0] * 100, 0)} e ${dec(sf.ic[1] * 100, 0)} de cada 100`}>
            {Array.from({ length: 100 }, (_, i) => (
              <i key={i} style={{ background: i < Math.round(sf.ic[0] * 100) ? pal["--s2"] : i < Math.round(sf.ic[1] * 100) ? pal["--s2"] : pal["--grid"], opacity: i >= Math.round(sf.ic[0] * 100) && i < Math.round(sf.ic[1] * 100) ? 0.45 : 1 }} />
            ))}
          </div>
          <p className="foot">Cada quadrado é uma assinatura. Laranja forte: o mínimo esperado ({dec(sf.ic[0] * 100, 0)}). Laranja claro: até onde a faixa vai ({dec(sf.ic[1] * 100, 0)}).
            Vale para o horizonte observado (até 2 anos de vida da assinatura).</p>
        </div>
        <div className="card">
          <h3>Com {int(p.base)} clientes ativos, o normal é ter cerca de {dec(p.esperado, 0)} cancelamentos por mês</h3>
          <p className="note" style={{ fontSize: 14 }}>Qualquer número entre <b>{dec(p.lo, 0)} e {dec(p.hi, 0)}</b> é normal, sem que nada tenha mudado.
            {p.extrapolado ? ` Atenção: a empresa nunca teve mais de ${int(raw.base_obs[1])} clientes, então aqui a previsão é menos segura.` : ""} Arraste para simular outro número de clientes.</p>
          <label className="slider">
            <span>Clientes ativos</span>
            <input type="range" min={500} max={C[C.length - 1].base} step={50} value={base} onChange={(e) => setBase(Number(e.target.value))} aria-label="Clientes ativos" />
            <output>{int(p.base)}</output>
          </label>
          <ResponsiveContainer width="100%" height={210}>
            <ComposedChart data={C} margin={{ top: 10, right: 12, left: 0, bottom: 14 }}>
              <CartesianGrid vertical={false} stroke={pal["--grid"]} />
              <XAxis type="number" dataKey="base" domain={[0, 7500]} ticks={[0, 1500, 3000, 4500, 6000, 7500]} allowDataOverflow stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false}
                tickFormatter={(v) => int(v)} label={{ value: "clientes ativos (assinaturas)", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false} axisLine={false} width={40} />
              <ReferenceArea x1={obsMax} x2={C[C.length - 1].base} fill={pal["--grid"]} fillOpacity={0.6}
                label={{ value: "nunca observado", position: "insideTop", fill: pal["--muted"], fontSize: 11 }} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const c = payload[0].payload as (typeof C)[number];
                return (
                  <div className="tt">
                    <b>{int(c.base)} clientes ativos</b>
                    <div className="row"><span>Esperado por mês</span><span>{dec(c.esperado, 0)}</span></div>
                    <div className="row"><span>Faixa normal</span><span>{dec(c.lo, 0)} a {dec(c.hi, 0)}</span></div>
                  </div>
                );
              }} />
              <Area dataKey="faixa" stroke="none" fill={pal["--s1"]} fillOpacity={0.18} isAnimationActive={false} activeDot={false} />
              <Line dataKey="esperado" stroke={pal["--s1"]} strokeWidth={2} dot={false} isAnimationActive={false} />
              <ReferenceDot x={p.base} y={p.esperado} r={5} fill={pal["--s2"]} stroke={pal["--surface"]} strokeWidth={2} />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="foot">Área cinza: números de clientes que a empresa nunca teve; ali a previsão é menos segura.</p>
          <Tecnico><p>Modelo quase-Poisson da seção “Base, mês e uso” (96% da variação explicada), faixa de predição de 95%.</p></Tecnico>
        </div>
      </div>
    </section>
  );
}
