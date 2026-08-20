import { useState } from "react";
import { api, ApiError, triggerBlobDownload } from "../api";
import type { Rollup, Session } from "../types";

function formatUsd(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "USD" });
}

const NIVEL_LABELS: Record<string, string> = {
  sales_agent: "Vendedor",
  supervisor: "Supervisor",
  regional_office: "Escritório",
};

export function ManagementView({ rollup, session }: { rollup: Rollup; session: Session }) {
  const [baixando, setBaixando] = useState(false);
  const [erroDownload, setErroDownload] = useState<string | null>(null);

  async function baixarDatasetCompleto() {
    setBaixando(true);
    setErroDownload(null);
    try {
      const blob = await api.downloadProcessedCsv(session.token);
      triggerBlobDownload(blob, "pipeline_processado.csv");
    } catch (err) {
      setErroDownload(err instanceof ApiError ? err.message : "falha no download");
    } finally {
      setBaixando(false);
    }
  }

  const niveis = Array.from(new Set(rollup.linhas.map((l) => l.nivel)));

  return (
    <div className="flex flex-col gap-8">
      {session.role === "manager" && (
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
      )}

      {niveis.map((nivel) => (
        <section key={nivel}>
          <h3 className="text-sm font-bold text-navy mb-2 uppercase tracking-wide">
            Rollup por {NIVEL_LABELS[nivel] ?? nivel}
          </h3>
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
                {rollup.linhas
                  .filter((l) => l.nivel === nivel)
                  .map((linha) => (
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
      ))}

      <section>
        <h3 className="text-sm font-bold text-navy mb-2 uppercase tracking-wide">
          Distribuição de esforço por produto
        </h3>
        <p className="text-xs text-muted mb-2">
          Produtos que consomem esforço desproporcional à receita histórica que geram.
        </p>
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
              {rollup.esforco_por_produto
                .slice()
                .sort((a, b) => b.n_oportunidades - a.n_oportunidades)
                .map((p) => (
                  <tr key={p.product} className="border-b border-border">
                    <td className="py-2 px-3 font-medium">{p.product}</td>
                    <td className="py-2 px-3">{p.n_oportunidades}</td>
                    <td className="py-2 px-3">
                      {(p.participacao_receita_historica * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
