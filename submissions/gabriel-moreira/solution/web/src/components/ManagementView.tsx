import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, ApiError, triggerBlobDownload } from "../api";
import { ESTADO_CHART_COLOR } from "../estadoColors";
import { formatPct, formatUsd } from "../format";
import { ESTADO_LABELS, ESTADOS, type Rollup } from "../types";

const NIVEL_LABELS: Record<string, string> = {
  sales_agent: "Vendedor",
  manager: "Gerente",
  regional_office: "Escritório",
};

const ALTURA_BARRA_PX = 32;
const ALTURA_MINIMA_GRAFICO = 140;

/** Aba Gestão — rollup por vendedor/gerente/escritório e esforço por
 * produto, disponível a qualquer usuário e respeitando os filtros de
 * organização e produto ativos (Requirement "Aba de gestão"). O download
 * do dataset completo não é mais condicionado a papel. */
export function ManagementView({ rollup }: { rollup: Rollup }) {
  const [baixando, setBaixando] = useState(false);
  const [erroDownload, setErroDownload] = useState<string | null>(null);

  async function baixarDatasetCompleto() {
    setBaixando(true);
    setErroDownload(null);
    try {
      const blob = await api.downloadProcessedCsv();
      triggerBlobDownload(blob, "pipeline_processado.csv");
    } catch (err) {
      setErroDownload(err instanceof ApiError ? err.message : "falha no download");
    } finally {
      setBaixando(false);
    }
  }

  const niveis = Array.from(new Set(rollup.linhas.map((l) => l.nivel)));

  const totalOportunidades = rollup.esforco_por_produto.reduce((soma, p) => soma + p.n_oportunidades, 0);
  const esforcoOrdenado = rollup.esforco_por_produto
    .slice()
    .sort((a, b) => b.n_oportunidades - a.n_oportunidades)
    .map((p) => ({
      ...p,
      pct_esforco: totalOportunidades > 0 ? (p.n_oportunidades / totalOportunidades) * 100 : 0,
      pct_receita: p.participacao_receita_historica * 100,
    }));

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center gap-3 bg-white border border-border rounded-sm p-3">
        <button
          type="button"
          onClick={baixarDatasetCompleto}
          disabled={baixando}
          className="text-sm font-semibold bg-navy text-white px-4 py-2 rounded-xs hover:bg-navy/90 disabled:opacity-50"
        >
          {baixando ? "Baixando…" : "Baixar dataset processado completo (CSV)"}
        </button>
        {erroDownload && <span className="text-alert text-sm">{erroDownload}</span>}
      </div>

      {niveis.map((nivel) => {
        const linhasNivel = rollup.linhas
          .filter((l) => l.nivel === nivel)
          .slice()
          .sort((a, b) => b.valor_esperado - a.valor_esperado);
        const alturaGrafico = Math.max(ALTURA_MINIMA_GRAFICO, linhasNivel.length * ALTURA_BARRA_PX);

        return (
          <section key={nivel}>
            <h3 className="text-sm font-bold text-navy mb-2 uppercase tracking-wide">
              Rollup por {NIVEL_LABELS[nivel] ?? nivel}
            </h3>
            <p className="text-xs text-muted mb-2">
              Distribuição de estado das oportunidades abertas de cada {NIVEL_LABELS[nivel]?.toLowerCase() ?? nivel}.
            </p>
            <div className="bg-white border border-border rounded-sm p-3 mb-3">
              <ResponsiveContainer width="100%" height={alturaGrafico}>
                <BarChart data={linhasNivel} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="chave"
                    width={110}
                    tick={{ fontSize: 11 }}
                    interval={0}
                  />
                  <RechartsTooltip formatter={(value: number, name: string) => [value, name]} />
                  <Legend
                    formatter={(estado: string) => ESTADO_LABELS[estado as keyof typeof ESTADO_LABELS] ?? estado}
                    wrapperStyle={{ fontSize: 11 }}
                  />
                  {ESTADOS.map((estado) => (
                    <Bar
                      key={estado}
                      dataKey={`por_estado.${estado}`}
                      name={ESTADO_LABELS[estado]}
                      stackId="estado"
                      fill={ESTADO_CHART_COLOR[estado]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse bg-white border border-border rounded-sm">
                <thead>
                  <tr className="text-left text-xs text-muted uppercase border-b border-border">
                    <th className="py-2 px-3">{NIVEL_LABELS[nivel] ?? nivel}</th>
                    <th className="py-2 px-3">Abertas</th>
                    <th className="py-2 px-3">Valor esperado</th>
                    <th className="py-2 px-3">Foco urgente</th>
                    <th className="py-2 px-3">Acompanhar</th>
                    <th className="py-2 px-3">Engajar</th>
                    <th className="py-2 px-3">Qualificar</th>
                    <th className="py-2 px-3">Desistir</th>
                  </tr>
                </thead>
                <tbody>
                  {linhasNivel.map((linha) => (
                    <tr key={`${linha.nivel}-${linha.chave}`} className="border-b border-border">
                      <td className="py-2 px-3 font-medium">{linha.chave}</td>
                      <td className="py-2 px-3">{linha.n_abertas}</td>
                      <td className="py-2 px-3">{formatUsd(linha.valor_esperado)}</td>
                      <td className="py-2 px-3">{linha.por_estado.foco_urgente}</td>
                      <td className="py-2 px-3">{linha.por_estado.acompanhar}</td>
                      <td className="py-2 px-3">{linha.por_estado.engajar}</td>
                      <td className="py-2 px-3">{linha.por_estado.qualificar}</td>
                      <td className="py-2 px-3 text-alert font-semibold">{linha.por_estado.desistir}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}

      <section>
        <h3 className="text-sm font-bold text-navy mb-2 uppercase tracking-wide">
          Distribuição de esforço por produto
        </h3>
        <p className="text-xs text-muted mb-2">
          Produtos que consomem esforço desproporcional à receita histórica que geram.
        </p>
        <div className="bg-white border border-border rounded-sm p-3 mb-3">
          <ResponsiveContainer width="100%" height={Math.max(ALTURA_MINIMA_GRAFICO, esforcoOrdenado.length * 40)}>
            <BarChart data={esforcoOrdenado} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="product" tick={{ fontSize: 11 }} interval={0} />
              <YAxis
                yAxisId="esforco"
                tick={{ fontSize: 11 }}
                label={{ value: "% do esforço", angle: -90, position: "insideLeft", fontSize: 11 }}
                tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              />
              <RechartsTooltip
                formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name]}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar
                yAxisId="esforco"
                dataKey="pct_esforco"
                name="% das oportunidades abertas"
                fill={ESTADO_CHART_COLOR.acompanhar}
              />
              <Bar
                yAxisId="esforco"
                dataKey="pct_receita"
                name="% da receita histórica"
                fill={ESTADO_CHART_COLOR.foco_urgente}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse bg-white border border-border rounded-sm">
            <thead>
              <tr className="text-left text-xs text-muted uppercase border-b border-border">
                <th className="py-2 px-3">Produto</th>
                <th className="py-2 px-3">Oportunidades abertas</th>
                <th className="py-2 px-3">Participação na receita histórica</th>
              </tr>
            </thead>
            <tbody>
              {esforcoOrdenado.map((p) => (
                <tr key={p.product} className="border-b border-border">
                  <td className="py-2 px-3 font-medium">{p.product}</td>
                  <td className="py-2 px-3">{p.n_oportunidades}</td>
                  <td className="py-2 px-3">{formatPct(p.participacao_receita_historica)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
