/** Roteador por hash: a raiz (`/` ou `#/`) é a segunda-feira do vendedor. */
import { useEffect, useState } from 'react';

export type Rota =
  | { nome: 'segunda' }
  | { nome: 'deal'; id: string }
  | { nome: 'manager' }
  | { nome: 'novo-lead' }
  | { nome: 'como-funciona' }
  | { nome: 'nao-encontrada'; caminho: string };

/** Lê a rota de um hash (`#/deal/ABC12345`). */
export function lerRota(hash: string): Rota {
  const caminho = hash.replace(/^#/, '').replace(/\/+$/, '') || '/';
  if (caminho === '/' || caminho === '') return { nome: 'segunda' };
  const deal = /^\/deal\/([^/]+)$/.exec(caminho);
  if (deal?.[1]) {
    // um link colado com "%" malformado não pode derrubar o app
    try {
      return { nome: 'deal', id: decodeURIComponent(deal[1]) };
    } catch {
      return { nome: 'nao-encontrada', caminho };
    }
  }
  if (caminho === '/manager') return { nome: 'manager' };
  if (caminho === '/novo-lead') return { nome: 'novo-lead' };
  if (caminho === '/como-funciona') return { nome: 'como-funciona' };
  return { nome: 'nao-encontrada', caminho };
}

/** Hash de cada rota, para os links. */
export const link = {
  segunda: '#/',
  deal: (id: string) => '#/deal/' + encodeURIComponent(id),
  manager: '#/manager',
  novoLead: '#/novo-lead',
  comoFunciona: '#/como-funciona',
} as const;

/** A rota atual; troca na hora, sem transição. */
export function useRota(): Rota {
  const [rota, setRota] = useState<Rota>(() => lerRota(globalThis.location?.hash ?? ''));
  useEffect(() => {
    const ouvir = () => setRota(lerRota(globalThis.location.hash));
    globalThis.addEventListener('hashchange', ouvir);
    return () => globalThis.removeEventListener('hashchange', ouvir);
  }, []);
  return rota;
}
