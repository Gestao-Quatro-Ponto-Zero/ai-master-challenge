import { useMemo } from "react";
import { CartesianGrid, Line, LineChart, ReferenceDot, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useCurva, type PontoCurva } from "@/hooks/useCurva";
import { useParametros } from "@/hooks/useParametros";
import { ErrorState, LoadingState } from "./States";

type Ponto = { idade: number; solida: number | null; tracejada: number | null };

/**
 * Linha sólida onde há amostra suficiente (n_sobreviventes >= amostraMinima, p_ganho não nulo);
 * daí até o ciclo máximo, segmento horizontal no último valor confiável (o que o score usa).
 */
export function buildCurvaPontos(curva: PontoCurva[], amostraMinima: number, cicloMax: number): Ponto[] {
  const confiaveis = curva.filter((c) => c.p_ganho != null && c.n_sobreviventes >= amostraMinima && c.idade <= cicloMax);
  if (!confiaveis.length) return [];
  const ultimo = confiaveis[confiaveis.length - 1]!;
  const ultimoVal = Math.round((ultimo.p_ganho as number) * 1000) / 10;
  const pontos: Ponto[] = confiaveis.map((c) => ({
    idade: c.idade,
    solida: Math.round((c.p_ganho as number) * 1000) / 10,
    tracejada: c.idade === ultimo.idade ? ultimoVal : null,
  }));
  if (ultimo.idade < cicloMax) pontos.push({ idade: cicloMax, solida: null, tracejada: ultimoVal });
  return pontos;
}

export function CurvaChart({ height = 320, idadeDeal, pGanhoDeal, compact }: {
  height?: number; idadeDeal?: number | null; pGanhoDeal?: number | null; compact?: boolean;
}) {
  const curva = useCurva();
  const params = useParametros();

  const pontos = useMemo(
    () => (curva.data && params.data ? buildCurvaPontos(curva.data, params.data.amostra_minima, params.data.ciclo_max_dias) : []),
    [curva.data, params.data],
  );

  if (curva.isLoading || params.isLoading) return <LoadingState rows={compact ? 2 : 4} />;
  const error = curva.error ?? params.error;
  if (error) return <ErrorState error={error} onRetry={() => { curva.refetch(); params.refetch(); }} />;
  if (!pontos.length || !params.data) return null;

  const { ciclo_max_dias: ciclo, fase_risco_dias: risco, reta_final_dias: reta } = params.data;
  const ticks = compact ? [0, risco, reta, ciclo] : [0, risco, 30, 60, 90, reta, ciclo];
  const marcador = idadeDeal != null && pGanhoDeal != null
    ? { x: Math.min(idadeDeal, ciclo), y: Math.round(pGanhoDeal * 1000) / 10 }
    : null;

  return (
    <div className="w-full">
      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={pontos} margin={{ top: 16, right: compact ? 12 : 24, bottom: compact ? 4 : 16, left: 0 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="idade" type="number" domain={[0, ciclo + 10]} ticks={ticks}
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)"
              {...(compact ? {} : { label: { value: "Idade do deal (dias)", position: "insideBottom", offset: -8, fontSize: 12, fill: "var(--muted-foreground)" } })} />
            <YAxis unit="%" width={44} domain={[50, 90]} ticks={[50, 60, 70, 80, 90]} allowDataOverflow
              tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} stroke="var(--border)" />
            <Tooltip
              formatter={(v, name) => [`${v}%`, name === "tracejada" ? "Chance (último valor confiável)" : "Chance de ganho"]}
              labelFormatter={(l) => `${l} dias`}
              contentStyle={{ background: "var(--popover)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
            />
            <ReferenceLine x={ciclo} stroke="var(--warning)" strokeDasharray="4 4"
              label={{ value: "limite histórico", position: "insideTopRight", fontSize: 11, fill: "var(--warning-foreground)" }} />
            <Line type="monotone" dataKey="solida" stroke="var(--primary)" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
            <Line type="linear" dataKey="tracejada" stroke="var(--primary)" strokeWidth={2} strokeDasharray="5 4" dot={false} connectNulls isAnimationActive={false} />
            {marcador && (
              <ReferenceDot x={marcador.x} y={marcador.y} r={5} fill="var(--primary)" stroke="var(--background)" strokeWidth={2} ifOverflow="extendDomain" />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">Linha tracejada: poucos deals nessa idade; o score usa o último valor confiável.</p>
    </div>
  );
}
