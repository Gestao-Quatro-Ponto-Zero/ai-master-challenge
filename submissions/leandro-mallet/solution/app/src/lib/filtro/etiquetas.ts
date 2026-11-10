// Etiquetas: o filtro estruturado que o campo livre gera e que o servidor aplica.
// As chaves seguem os parâmetros de core_buscar_deals no banco.
import type { AcaoSugerida, Estagio, Icone, Porte } from "../tipos";

export interface Etiquetas {
  estagios?: Estagio[];
  nota_min?: number;
  nota_max?: number;
  sem_nota?: boolean;
  icones?: Icone[];
  abertura_de?: string;
  abertura_ate?: string;
  sem_abertura?: boolean;
  dias_aberto_min?: number;
  contato_ha_dias_min?: number;
  contato_ha_dias_max?: number;
  sem_contato?: boolean;
  sem_contato_principal?: boolean;
  setores?: string[];
  portes?: Porte[];
  sem_empresa?: boolean;
  empresas?: string[];
  produtos?: string[];
  series?: string[];
  vendedores?: string[];
  managers?: string[];
  regioes?: string[];
  acoes_sugeridas?: AcaoSugerida[];
  valor_min?: number;
  fechamento_de?: string;
  fechamento_ate?: string;
  tags?: string[];
  sem_tag?: boolean;
  com_comentario?: boolean;
  contem?: string;
  // Aba Contas
  padroes?: ("na_janela" | "fora_da_janela" | "sem_padrao")[];
  compras_min?: number;
  com_aberto?: boolean;
  sem_aberto?: boolean;
  receita_min?: number;
  subsidiaria?: boolean;
  independente?: boolean;
  bonus_min?: number;
  sedes?: string[];
}

export type ChaveEtiqueta = keyof Etiquetas;

/** Uma etiqueta visível ("chip"): o pedaço de filtro e o texto que a tela mostra. */
export interface Etiqueta {
  chave: ChaveEtiqueta;
  valor: Etiquetas[ChaveEtiqueta];
  rotulo: string;
}

/** Etiquetas no link da página (?f=): lista compacta [chave, valor, rótulo]. */
export function codificar(lista: Etiqueta[]): string {
  return JSON.stringify(lista.map((e) => [e.chave, e.valor, e.rotulo]));
}

/** Junta as etiquetas num filtro; listas da mesma chave se somam. */
export function juntar(lista: Etiqueta[]): Etiquetas {
  const e: Record<string, unknown> = {};
  for (const { chave, valor } of lista) {
    const atual = e[chave];
    if (Array.isArray(atual) && Array.isArray(valor)) e[chave] = [...new Set([...atual, ...valor])];
    else e[chave] = valor;
  }
  return e as Etiquetas;
}
