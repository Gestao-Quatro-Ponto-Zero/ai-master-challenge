import type { Filtro, Organizacao } from '@lead-scorer/dominio/organizacao';

export type ValorFiltros = Filtro;

/** Filtros por vendedor, manager e região; vazio = todos. */
export function Filtros({
  organizacao,
  valor,
  aoMudar,
}: {
  organizacao: Organizacao;
  valor: ValorFiltros;
  aoMudar: (f: ValorFiltros) => void;
}) {
  const vendedores = organizacao.vendedores.filter(
    (v) =>
      (!valor.manager || v.manager === valor.manager) &&
      (!valor.regiao || v.regiao === valor.regiao),
  );
  const managers = organizacao.managers.filter((m) => !valor.regiao || m.regiao === valor.regiao);
  const mudar = (campo: keyof ValorFiltros, v: string) => {
    const novo: ValorFiltros = { ...valor, [campo]: v === '' ? undefined : v };
    // trocar região ou manager limpa o vendedor que não pertence mais ao recorte
    if (campo !== 'vendedor') novo.vendedor = undefined;
    if (campo === 'regiao') novo.manager = undefined;
    aoMudar(novo);
  };
  return (
    <div className="filtros">
      <div className="campo">
        <label htmlFor="filtro-regiao">Região</label>
        <select
          id="filtro-regiao"
          data-testid="filtro-regiao"
          value={valor.regiao ?? ''}
          onChange={(e) => mudar('regiao', e.target.value)}
        >
          <option value="">Todas</option>
          {organizacao.regioes.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>
      <div className="campo">
        <label htmlFor="filtro-manager">Manager</label>
        <select
          id="filtro-manager"
          data-testid="filtro-manager"
          value={valor.manager ?? ''}
          onChange={(e) => mudar('manager', e.target.value)}
        >
          <option value="">Todos</option>
          {managers.map((m) => (
            <option key={m.nome} value={m.nome}>
              {m.nome}
            </option>
          ))}
        </select>
      </div>
      <div className="campo">
        <label htmlFor="filtro-vendedor">Vendedor</label>
        <select
          id="filtro-vendedor"
          data-testid="filtro-vendedor"
          value={valor.vendedor ?? ''}
          onChange={(e) => mudar('vendedor', e.target.value)}
        >
          <option value="">Todos</option>
          {vendedores.map((v) => (
            <option key={v.nome} value={v.nome}>
              {v.nome}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
