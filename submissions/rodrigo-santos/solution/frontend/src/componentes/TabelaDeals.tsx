/** Visualização em lista: tabela ordenável, boa para comparar muitos deals. */

import { useEffect, useMemo, useState } from "react";

import type { DealResumo } from "../tipos";
import { formatarDias, formatarMoeda, NOMES_ETAPA, tituloDeal } from "../utils/formatadores";
import SeloPrioridade from "./SeloPrioridade";

type ColunaOrdenavel = "score" | "valor" | "valor_esperado" | "dias_aberto";

const COLUNAS: { chave: ColunaOrdenavel; rotulo: string }[] = [
  { chave: "score", rotulo: "Pontuação" },
  { chave: "valor", rotulo: "Valor" },
  { chave: "valor_esperado", rotulo: "Valor esperado" },
  { chave: "dias_aberto", rotulo: "Tempo aberto" },
];

const LINHAS_POR_PAGINA = 50;

interface Props {
  deals: DealResumo[];
  aoSelecionar: (id: string) => void;
}

export default function TabelaDeals({ deals, aoSelecionar }: Props) {
  const [ordenarPor, setOrdenarPor] = useState<ColunaOrdenavel>("score");
  const [visiveis, setVisiveis] = useState(LINHAS_POR_PAGINA);

  useEffect(() => setVisiveis(LINHAS_POR_PAGINA), [deals, ordenarPor]);

  // Ordem decrescente; deals sem valor (ex.: sem data) vão para o fim.
  const ordenados = useMemo(
    () => [...deals].sort((a, b) => (b[ordenarPor] ?? -1) - (a[ordenarPor] ?? -1)),
    [deals, ordenarPor],
  );

  return (
    <div className="tabela-container">
      <table className="tabela">
        <thead>
          <tr>
            <th>Prioridade</th>
            <th>Conta</th>
            <th>Produto</th>
            <th>Vendedor</th>
            <th>Etapa</th>
            <th>Principal motivo</th>
            {COLUNAS.map(({ chave, rotulo }) => (
              <th key={chave}>
                <button
                  className={`cabecalho-ordenavel ${ordenarPor === chave ? "ativo" : ""}`}
                  onClick={() => setOrdenarPor(chave)}
                  title="Ordenar do maior para o menor"
                >
                  {rotulo} {ordenarPor === chave && "▼"}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ordenados.slice(0, visiveis).map((deal) => (
            <tr key={deal.id} onClick={() => aoSelecionar(deal.id)}>
              <td><SeloPrioridade prioridade={deal.prioridade} /></td>
              <td>{tituloDeal(deal)}</td>
              <td>{deal.produto}</td>
              <td>{deal.vendedor}</td>
              <td>{NOMES_ETAPA[deal.etapa]}</td>
              <td className={deal.prioridade === "Alta" ? "motivo-positivo" : "motivo-negativo"}>
                {deal.motivo_principal}
              </td>
              <td className="numero">{deal.score}</td>
              <td className="numero">{formatarMoeda(deal.valor)}</td>
              <td className="numero">{formatarMoeda(deal.valor_esperado)}</td>
              <td className={`numero ${deal.parado ? "alerta-parado" : ""}`}>
                {deal.parado && "⚠ "}
                {formatarDias(deal.dias_aberto)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {visiveis < ordenados.length && (
        <button className="botao-mais" onClick={() => setVisiveis(visiveis + LINHAS_POR_PAGINA)}>
          Mostrar mais ({ordenados.length - visiveis} restantes)
        </button>
      )}
    </div>
  );
}
