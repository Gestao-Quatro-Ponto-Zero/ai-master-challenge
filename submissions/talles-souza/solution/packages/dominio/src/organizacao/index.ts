/**
 * Contexto `organizacao`: vendedores, managers e regiões; filtros; o seletor de perfil.
 * O perfil NÃO é autenticação: é só "de quem é esta fila".
 */
import type { Deal, MembroDoTime } from '../pipeline';
import type { Bloco } from '../qualificacao';

export * from './http';

/** Um vendedor do time, com o manager, a região e quantos deals abertos ele tem (0 se nenhum). */
export interface Vendedor {
  nome: string;
  manager: string;
  regiao: string;
  /** Deals abertos (Prospecting + Engaging) do vendedor. */
  abertos: number;
  /**
   * Quantos abertos o vendedor tem em cada grupo da segunda-feira, para o seletor. Quem preenche
   * é a composição (`criarServicos`), uma vez na carga: o grupo vem da política de priorização.
   */
  grupos?: Record<Bloco, number>;
}

/** Um manager, a região dele e o time de vendedores. */
export interface Manager {
  nome: string;
  regiao: string;
  vendedores: string[];
}

/** O time de vendas como aparece nos deals. */
export interface Organizacao {
  vendedores: Vendedor[];
  managers: Manager[];
  regioes: string[];
}

/** "Sou o vendedor X", "sou o manager Y" ou a visão de todos. */
export type Perfil =
  { tipo: 'vendedor'; nome: string } | { tipo: 'manager'; nome: string } | { tipo: 'todos' };

/** Recorte dos deals por vendedor, manager e região. */
export interface Filtro {
  vendedor?: string | undefined;
  manager?: string | undefined;
  regiao?: string | undefined;
}

// locale fixo: a API e o modo local da web ordenam igual, em qualquer máquina
const porTexto = (a: string, b: string): number => a.localeCompare(b, 'pt-BR');

/**
 * Monta vendedores, managers e regiões a partir do time inteiro (todos aparecem, inclusive quem
 * não tem negócio: abertos 0), com os abertos contados nos deals, em ordem de nome.
 */
export function montarOrganizacao(
  time: readonly MembroDoTime[],
  deals: readonly Deal[],
): Organizacao {
  const vendedores = new Map<string, Vendedor>();
  const managers = new Map<string, { nome: string; regiao: string; vendedores: Set<string> }>();
  const regioes = new Set<string>();
  for (const t of time) {
    vendedores.set(t.nome, { nome: t.nome, manager: t.manager, regiao: t.regiao, abertos: 0 });
    const m = managers.get(t.manager) ?? {
      nome: t.manager,
      regiao: t.regiao,
      vendedores: new Set<string>(),
    };
    m.vendedores.add(t.nome);
    managers.set(t.manager, m);
    regioes.add(t.regiao);
  }
  for (const d of deals) {
    const v = vendedores.get(d.vendedor);
    if (v && d.aberto) v.abertos += 1;
  }
  return {
    vendedores: [...vendedores.values()].sort((a, b) => porTexto(a.nome, b.nome)),
    managers: [...managers.values()]
      .map((m) => ({
        nome: m.nome,
        regiao: m.regiao,
        vendedores: [...m.vendedores].sort(porTexto),
      }))
      .sort((a, b) => porTexto(a.nome, b.nome)),
    regioes: [...regioes].sort(porTexto),
  };
}

/** Filtro equivalente a um perfil. */
export function filtroDoPerfil(perfil: Perfil): Filtro {
  if (perfil.tipo === 'vendedor') return { vendedor: perfil.nome };
  if (perfil.tipo === 'manager') return { manager: perfil.nome };
  return {};
}

/** Os vendedores do time que o filtro alcança (campos ausentes não filtram), com ou sem negócio. */
export function filtrarTime(time: readonly MembroDoTime[], filtro: Filtro): MembroDoTime[] {
  return time.filter(
    (v) =>
      (filtro.vendedor === undefined || v.nome === filtro.vendedor) &&
      (filtro.manager === undefined || v.manager === filtro.manager) &&
      (filtro.regiao === undefined || v.regiao === filtro.regiao),
  );
}

/** Aplica o filtro (campos ausentes não filtram). */
export function aplicarFiltro(deals: readonly Deal[], filtro: Filtro): Deal[] {
  return deals.filter(
    (d) =>
      (filtro.vendedor === undefined || d.vendedor === filtro.vendedor) &&
      (filtro.manager === undefined || d.manager === filtro.manager) &&
      (filtro.regiao === undefined || d.regiao === filtro.regiao),
  );
}
