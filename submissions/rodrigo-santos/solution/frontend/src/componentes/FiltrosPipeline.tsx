/** Barra de filtros: vendedor, manager, escritório, produto, prioridade e busca. */

import type { Filtros, OpcoesFiltro } from "../tipos";
import { FILTROS_VAZIOS } from "../tipos";

interface Props {
  filtros: Filtros;
  opcoes: OpcoesFiltro | null;
  aoMudar: (filtros: Filtros) => void;
}

/** Configuração de cada caixa de seleção: campo do filtro, rótulo e de onde vêm as opções. */
const CAMPOS_SELECAO: { campo: keyof Filtros; rotulo: string; opcoes: keyof OpcoesFiltro }[] = [
  { campo: "vendedor", rotulo: "Vendedor", opcoes: "vendedores" },
  { campo: "manager", rotulo: "Gerente", opcoes: "managers" },
  { campo: "escritorio", rotulo: "Escritório", opcoes: "escritorios" },
  { campo: "produto", rotulo: "Produto", opcoes: "produtos" },
  { campo: "prioridade", rotulo: "Prioridade", opcoes: "prioridades" },
];

export default function FiltrosPipeline({ filtros, opcoes, aoMudar }: Props) {
  const alterar = (campo: keyof Filtros, valor: string) => aoMudar({ ...filtros, [campo]: valor });
  const temFiltroAtivo = Object.values(filtros).some(Boolean);

  return (
    <section className="filtros">
      {CAMPOS_SELECAO.map(({ campo, rotulo, opcoes: chaveOpcoes }) => (
        <label key={campo}>
          <span>{rotulo}</span>
          <select value={filtros[campo]} onChange={(e) => alterar(campo, e.target.value)}>
            <option value="">Todos</option>
            {opcoes?.[chaveOpcoes].map((opcao) => (
              <option key={opcao} value={opcao}>
                {opcao}
              </option>
            ))}
          </select>
        </label>
      ))}

      <label className="campo-busca">
        <span>Buscar</span>
        <input
          type="search"
          placeholder="Nome da conta ou código"
          value={filtros.busca}
          onChange={(e) => alterar("busca", e.target.value)}
        />
      </label>

      {temFiltroAtivo && (
        <button className="botao-limpar" onClick={() => aoMudar(FILTROS_VAZIOS)}>
          Limpar filtros
        </button>
      )}
    </section>
  );
}
