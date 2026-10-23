/**
 * Onde as respostas e decisões do vendedor ficam: o `localStorage` deste navegador, com prefixo
 * versionado. Toda leitura passa pelo schema do domínio (JSON quebrado ou formato errado é
 * ignorado) e todo acesso fica em try/catch; sem `localStorage`, guarda em memória.
 */
import type { Perfil } from '@lead-scorer/dominio/organizacao';
import {
  criarRepositorioEmMemoria,
  validarRespostas,
  type RepositorioRespostas,
  type RespostasDoDeal,
} from '@lead-scorer/dominio/qualificacao';

export const PREFIXO_RESPOSTAS = 'lead-scorer:respostas:v1:';
export const CHAVE_PERFIL = 'lead-scorer:perfil:v1';
export const CHAVE_COMISSAO = 'lead-scorer:comissao:v1';

/** O `localStorage`, se existir e aceitar escrita; senão null. */
export function storageDisponivel(): Storage | null {
  try {
    const s = globalThis.localStorage;
    if (!s) return null;
    const teste = 'lead-scorer:teste';
    s.setItem(teste, '1');
    s.removeItem(teste);
    return s;
  } catch {
    return null;
  }
}

function lerValidado(storage: Storage, chave: string): RespostasDoDeal | null {
  try {
    const texto = storage.getItem(chave);
    if (texto === null) return null;
    const r = validarRespostas(JSON.parse(texto));
    return r.ok ? r.valor : null;
  } catch {
    return null;
  }
}

/** Repositório no `localStorage`; recebe o storage para os testes. Null → em memória. */
export function criarRepositorioNavegador(
  storage: Storage | null = storageDisponivel(),
): RepositorioRespostas {
  if (!storage) return criarRepositorioEmMemoria();
  return {
    ler: (dealId) => lerValidado(storage, PREFIXO_RESPOSTAS + dealId),
    salvar(respostas) {
      try {
        storage.setItem(PREFIXO_RESPOSTAS + respostas.dealId, JSON.stringify(respostas));
      } catch {
        // storage cheio ou bloqueado: a resposta vale só nesta sessão da tela
      }
    },
    listar() {
      const out: RespostasDoDeal[] = [];
      try {
        for (let i = 0; i < storage.length; i++) {
          const chave = storage.key(i);
          if (chave === null || !chave.startsWith(PREFIXO_RESPOSTAS)) continue;
          const r = lerValidado(storage, chave);
          if (r) out.push(r);
        }
      } catch {
        // storage ilegível: lista o que já leu
      }
      return out;
    },
    limpar(dealId) {
      try {
        storage.removeItem(PREFIXO_RESPOSTAS + dealId);
      } catch {
        // nada a fazer
      }
    },
  };
}

/** Lê o perfil escolhido ("sou o vendedor X"); qualquer coisa estranha vira null. */
export function lerPerfil(storage: Storage | null = storageDisponivel()): Perfil | null {
  try {
    const texto = storage?.getItem(CHAVE_PERFIL);
    if (!texto) return null;
    const p = JSON.parse(texto) as { tipo?: unknown; nome?: unknown };
    if (p.tipo === 'todos') return { tipo: 'todos' };
    if (
      (p.tipo === 'vendedor' || p.tipo === 'manager') &&
      typeof p.nome === 'string' &&
      p.nome.length > 0
    ) {
      return { tipo: p.tipo, nome: p.nome };
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * A comissão que o vendedor digitou (% de 0 a 100, exclusivo no zero), ou null. O dataset não
 * tem comissão: o campo começa vazio e nada é sugerido. Valor estranho no storage vira null.
 */
export function lerComissao(storage: Storage | null = storageDisponivel()): number | null {
  try {
    const texto = storage?.getItem(CHAVE_COMISSAO);
    if (!texto) return null;
    const n = Number(texto);
    return comissaoValida(n) ? n : null;
  } catch {
    return null;
  }
}

/** Guarda a comissão (null apaga). Sem storage, vale só nesta sessão da tela. */
export function salvarComissao(
  percentual: number | null,
  storage: Storage | null = storageDisponivel(),
): void {
  try {
    if (percentual === null || !comissaoValida(percentual)) storage?.removeItem(CHAVE_COMISSAO);
    else storage?.setItem(CHAVE_COMISSAO, String(percentual));
  } catch {
    // sem storage: a comissão vale só nesta sessão da tela
  }
}

/** Comissão aceita: número maior que 0 e até 100. */
export function comissaoValida(n: number): boolean {
  return Number.isFinite(n) && n > 0 && n <= 100;
}

/** Guarda o perfil escolhido (o perfil não é login: só diz de quem é a fila). */
export function salvarPerfil(perfil: Perfil, storage: Storage | null = storageDisponivel()): void {
  try {
    storage?.setItem(CHAVE_PERFIL, JSON.stringify(perfil));
  } catch {
    // sem storage: o perfil vale só nesta sessão da tela
  }
}
