import type { FiltrosEquipe as Dados } from "@/server/parametros";
import { Seletor } from "./Filtros";

/** Seletores de região, manager e vendedor; só aparecem os que o papel usa. */
export function FiltrosEquipe({ filtros }: { filtros: Dados }) {
  const { opcoes } = filtros;
  if (!opcoes.vendedores.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      {opcoes.regioes.length ? <Seletor nome="regiao" rotulo="Região" valor={filtros.regiao ?? ""} opcoes={opcoes.regioes} todos="Todas" /> : null}
      {opcoes.managers.length ? <Seletor nome="manager" rotulo="Manager" valor={filtros.manager ?? ""} opcoes={opcoes.managers} todos="Todos" /> : null}
      <Seletor nome="vendedor" rotulo="Vendedor" valor={filtros.vendedor ?? ""} opcoes={opcoes.vendedores} todos="Todos" />
    </div>
  );
}
