/**
 * O que toda tela precisa: o cliente (API com queda para o modo local), o repositório das
 * respostas, o relógio e a base carregada uma vez (política, método, organização, resumo).
 */
import type { Organizacao, Perfil } from '@lead-scorer/dominio/organizacao';
import type { RespostaResumo } from '@lead-scorer/dominio/pipeline';
import {
  textosDaTela,
  type PoliticaPriorizacao,
  type TextosPreenchidos,
} from '@lead-scorer/dominio/priorizacao';
import {
  mesclarRegistros,
  type MetodoQualificacao,
  type RepositorioRespostas,
} from '@lead-scorer/dominio/qualificacao';
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ClienteResiliente, Modo, RegistrosRemotos } from '../infra';

export interface Base {
  politica: PoliticaPriorizacao;
  metodo: MetodoQualificacao;
  organizacao: Organizacao;
  resumo: RespostaResumo;
  /** Os textos da tela, da política, já preenchidos com os limites e a janela. */
  textos: TextosPreenchidos;
}

export interface Dependencias {
  cliente: ClienteResiliente;
  repositorio: RepositorioRespostas;
  /** As respostas e decisões no servidor (o banco compartilhado, quando a API tem um). */
  registros: RegistrosRemotos;
  /** ISO 8601 de agora (as respostas guardam quando foram dadas). */
  agoraIso: () => string;
  /** Perfil guardado e o jeito de guardar outro. */
  perfil: { ler(): Perfil | null; salvar(p: Perfil): void };
  /** A comissão (%) que o vendedor digitou, guardada neste navegador; null = vazio. */
  comissao: { ler(): number | null; salvar(p: number | null): void };
}

export type EstadoBase =
  { tipo: 'carregando' } | { tipo: 'erro'; mensagem: string } | { tipo: 'pronta'; base: Base };

interface ValorContexto {
  deps: Dependencias;
  base: EstadoBase;
  modo: Modo;
  /**
   * true quando as respostas e decisões estão no banco compartilhado (valem para todos os
   * aparelhos); false quando são só as deste navegador.
   */
  respostasCompartilhadas: boolean;
  /** Sobe a cada vez que registros do servidor entram neste navegador (as telas recarregam). */
  versaoRegistros: number;
}

const Contexto = createContext<ValorContexto | null>(null);

/** Carrega a base e acompanha o modo do cliente. */
export function ProvedorApp({ deps, children }: { deps: Dependencias; children: ReactNode }) {
  const [base, setBase] = useState<EstadoBase>({ tipo: 'carregando' });
  const [modo, setModo] = useState<Modo>(deps.cliente.modo());
  const [respostasCompartilhadas, setCompartilhadas] = useState(false);
  const [versaoRegistros, setVersaoRegistros] = useState(0);

  useEffect(() => {
    const cancelar = deps.cliente.assinar(setModo);
    // a troca que aconteceu entre o render e a assinatura não se perde
    setModo(deps.cliente.modo());
    return cancelar;
  }, [deps.cliente]);

  useEffect(() => {
    let vivo = true;
    const { cliente } = deps;
    Promise.all([cliente.politica(), cliente.metodo(), cliente.organizacao(), cliente.resumo()])
      .then(([politica, metodo, organizacao, resumo]) => {
        if (!vivo) return;
        const textos = textosDaTela(politica, resumo.janela);
        setBase({ tipo: 'pronta', base: { politica, metodo, organizacao, resumo, textos } });
      })
      .catch((e: unknown) => {
        if (vivo) setBase({ tipo: 'erro', mensagem: e instanceof Error ? e.message : String(e) });
      });
    return () => {
      vivo = false;
    };
  }, [deps]);

  // Com a API de pé, baixa as respostas guardadas no servidor e junta com as deste navegador
  // (por pergunta, vale a mais recente). Só no banco compartilhado elas valem para a equipe.
  useEffect(() => {
    if (modo !== 'api') {
      setCompartilhadas(false);
      return;
    }
    let vivo = true;
    void deps.registros.baixar().then((r) => {
      if (!vivo || !r) return;
      for (const doServidor of r.registros) {
        const local = deps.repositorio.ler(doServidor.dealId);
        deps.repositorio.salvar(local ? mesclarRegistros(local, doServidor) : doServidor);
      }
      setCompartilhadas(r.armazenamento === 'banco');
      if (r.registros.length > 0) setVersaoRegistros((v) => v + 1);
    });
    return () => {
      vivo = false;
    };
  }, [modo, deps]);

  // No modo local, pergunta à API a cada 15 s se ela voltou.
  useEffect(() => {
    if (modo !== 'local') return;
    const id = setInterval(() => void deps.cliente.sondar(), 15_000);
    return () => clearInterval(id);
  }, [modo, deps.cliente]);

  const valor = useMemo(
    () => ({ deps, base, modo, respostasCompartilhadas, versaoRegistros }),
    [deps, base, modo, respostasCompartilhadas, versaoRegistros],
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

/** O contexto da aplicação (fora do provedor é erro de programação). */
export function useApp(): ValorContexto {
  const v = useContext(Contexto);
  if (!v) throw new Error('useApp fora do ProvedorApp');
  return v;
}
