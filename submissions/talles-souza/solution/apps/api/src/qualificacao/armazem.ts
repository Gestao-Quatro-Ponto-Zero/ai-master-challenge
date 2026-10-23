/**
 * Onde a API guarda as respostas e as decisões do vendedor: uma porta com duas implementações,
 * o banco compartilhado (tabelas `lead_scorer.respostas` e `lead_scorer.decisoes`) e a memória
 * deste processo, mais o armazém resiliente, que usa o banco e cai para a memória quando ele
 * falha. Só se acrescentam linhas; nada é alterado nem apagado (o estado atual sai de
 * `montarRegistros`, no domínio).
 */
import type {
  Armazenamento,
  LinhaDecisao,
  LinhaResposta,
  TipoAcao,
} from '@lead-scorer/dominio/qualificacao';
import { semQuebra, type Consultor, type DisjuntorBanco } from '../infra/banco';

/** As linhas gravadas até agora. */
export interface LinhasGravadas {
  respostas: LinhaResposta[];
  decisoes: LinhaDecisao[];
}

/** A porta do armazenamento das respostas e decisões. */
export interface ArmazemRegistros {
  /** `banco` = compartilhado entre aparelhos; `memoria` = só neste processo, some ao reiniciar. */
  tipo(): Armazenamento;
  listar(): Promise<LinhasGravadas>;
  gravarResposta(linha: LinhaResposta): Promise<void>;
  /** Grava todas as linhas ou nenhuma (o lote é um INSERT só). */
  gravarDecisoes(linhas: readonly LinhaDecisao[]): Promise<void>;
}

/** Armazém na memória do processo: o modo local da API, sem banco. */
export function criarArmazemEmMemoria(): ArmazemRegistros {
  const respostas: LinhaResposta[] = [];
  const decisoes: LinhaDecisao[] = [];
  return {
    tipo: () => 'memoria',
    listar: async () => ({ respostas: [...respostas], decisoes: [...decisoes] }),
    gravarResposta: async (linha) => {
      respostas.push({ ...linha });
    },
    gravarDecisoes: async (linhas) => {
      decisoes.push(...linhas.map((l) => ({ ...l })));
    },
  };
}

const TIPOS_ACAO: readonly TipoAcao[] = [
  'avancar_hoje',
  'manter_ritmo',
  'qualificar',
  'encaminhar_para_nutricao',
];

/**
 * A tabela `decisoes` guarda a ação num texto só: `aceitar:<ação>` ou `contestar:<ação>` (ex.:
 * `aceitar:encaminhar_para_nutricao`). Assim o aceite e a contestação cabem no schema que já
 * existe, sem coluna nova.
 */
export function acaoParaTexto(acao: TipoAcao, aceita: boolean): string {
  return (aceita ? 'aceitar:' : 'contestar:') + acao;
}

/** O inverso de `acaoParaTexto`; texto fora do formato vira null (a linha é ignorada). */
export function textoParaAcao(texto: string): { acao: TipoAcao; aceita: boolean } | null {
  const casou = /^(aceitar|contestar):(\w+)$/.exec(texto);
  const acao = casou?.[2] as TipoAcao | undefined;
  if (!casou || !acao || !TIPOS_ACAO.includes(acao)) return null;
  return { acao, aceita: casou[1] === 'aceitar' };
}

const iso = (d: Date | string): string => (d instanceof Date ? d : new Date(d)).toISOString();

interface LinhaRespostaBanco {
  opportunity_id: string;
  sales_agent: string;
  pergunta: string;
  resposta: boolean;
  respondido_em: Date;
}

interface LinhaDecisaoBanco {
  opportunity_id: string;
  sales_agent: string;
  acao: string;
  motivo: string | null;
  decidido_em: Date;
}

/** Armazém no banco compartilhado: só SELECT e INSERT, sempre em `lead_scorer.*`. */
export function criarArmazemNoBanco(banco: Consultor): ArmazemRegistros {
  return {
    tipo: () => 'banco',
    async listar() {
      const [respostas, decisoes] = await Promise.all([
        banco.consultar<LinhaRespostaBanco>(
          'select opportunity_id, sales_agent, pergunta, resposta, respondido_em ' +
            'from lead_scorer.respostas order by id',
        ),
        banco.consultar<LinhaDecisaoBanco>(
          'select opportunity_id, sales_agent, acao, motivo, decidido_em ' +
            'from lead_scorer.decisoes order by id',
        ),
      ]);
      return {
        respostas: respostas.map((l) => ({
          dealId: l.opportunity_id,
          vendedor: l.sales_agent,
          perguntaId: l.pergunta,
          valor: l.resposta ? ('sim' as const) : ('nao' as const),
          em: iso(l.respondido_em),
        })),
        decisoes: decisoes.flatMap((l) => {
          const a = textoParaAcao(l.acao);
          if (!a) return [];
          return [
            {
              dealId: l.opportunity_id,
              vendedor: l.sales_agent,
              ...a,
              motivo: l.motivo,
              em: iso(l.decidido_em),
            },
          ];
        }),
      };
    },
    async gravarResposta(l) {
      await banco.consultar(
        'insert into lead_scorer.respostas ' +
          '(opportunity_id, sales_agent, pergunta, resposta, respondido_em) ' +
          'values ($1, $2, $3, $4, $5)',
        [l.dealId, l.vendedor, l.perguntaId, l.valor === 'sim', l.em],
      );
    },
    async gravarDecisoes(linhas) {
      if (linhas.length === 0) return;
      // um INSERT só: o lote entra inteiro ou não entra
      await banco.consultar(
        'insert into lead_scorer.decisoes ' +
          '(opportunity_id, sales_agent, acao, motivo, decidido_em) ' +
          'select * from unnest($1::text[], $2::text[], $3::text[], $4::text[], $5::timestamptz[])',
        [
          linhas.map((l) => l.dealId),
          linhas.map((l) => l.vendedor),
          linhas.map((l) => acaoParaTexto(l.acao, l.aceita)),
          linhas.map((l) => l.motivo),
          linhas.map((l) => l.em),
        ],
      );
    },
  };
}

/**
 * Armazém resiliente: tenta o banco (pelo disjuntor); se falhar ou o circuito estiver aberto,
 * grava e lê na memória deste processo e passa a dizer `memoria` até o banco responder de novo.
 * Ao ler do banco, junta as linhas que ficaram na memória durante a queda.
 */
export function criarArmazemResiliente(
  banco: ArmazemRegistros,
  disjuntor: DisjuntorBanco,
  log: (linha: string) => void,
  memoria: ArmazemRegistros = criarArmazemEmMemoria(),
): ArmazemRegistros {
  let caiu = false;
  async function tentar<T>(
    oQue: string,
    noBanco: () => Promise<T>,
    naMemoria: () => Promise<T>,
  ): Promise<T> {
    try {
      const valor = await disjuntor.executar(noBanco);
      caiu = false;
      return valor;
    } catch (e) {
      if (!caiu) {
        log('banco: ' + oQue + ' falhou; usando a memória: ' + semQuebra((e as Error).message));
      }
      caiu = true;
      return naMemoria();
    }
  }
  return {
    tipo: () => (caiu || disjuntor.aberto() ? 'memoria' : 'banco'),
    listar: () =>
      tentar(
        'ler',
        async () => {
          const [b, m] = await Promise.all([banco.listar(), memoria.listar()]);
          return {
            respostas: [...b.respostas, ...m.respostas],
            decisoes: [...b.decisoes, ...m.decisoes],
          };
        },
        () => memoria.listar(),
      ),
    gravarResposta: (l) =>
      tentar(
        'gravar resposta',
        () => banco.gravarResposta(l),
        () => memoria.gravarResposta(l),
      ),
    gravarDecisoes: (ls) =>
      tentar(
        'gravar decisões',
        () => banco.gravarDecisoes(ls),
        () => memoria.gravarDecisoes(ls),
      ),
  };
}
