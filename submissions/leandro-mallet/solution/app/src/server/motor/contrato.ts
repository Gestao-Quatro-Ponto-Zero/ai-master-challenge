// Contrato entre a rotina diária (rotas e banco, sessão #4) e o motor do score (src/lib/score/, sessão #3).
//
// A rotina abre UMA transação no banco com o papel de carga (g4_rotina → set local role system_carga), inicia o
// contexto "sistema" com ctx.correlationId e chama, nesta ordem:
//   1. motor.semanal(ctx), só quando a data de negócio é domingo: FIT da janela de 3 meses, redistribuição pela
//      core_repassar_deal(origem 'redistribuicao') e padrões de conta;
//   2. motor.diario(ctx), todo dia: HEAT e nota novos → execução nova (score_execucoes/score_deals/... e
//      score_ativar_execucao), repasse por mudança de faixa sem contato pela core_repassar_deal(origem
//      'repasse_janela'), lead novo sem dono roteado ao vendedor de maior conversão (a penalidade é do banco).
// Regras para o motor:
//   - grave SÓ por ctx.sql, na transação da rotina (nada de outra conexão); qualquer erro lançado desfaz tudo;
//   - use ctx.correlationId nas funções do banco que pedem correlation_id (é o da transação);
//   - nada de DELETE; nada de senha ou chave no código;
//   - devolva um resumo pequeno em números (vai para o registro do dia em system_eventos).

/** Consulta parametrizada na transação da rotina ($1, $2, …). Devolve as linhas. */
export type Sql = <T = Record<string, unknown>>(texto: string, parametros?: unknown[]) => Promise<T[]>;

export interface ContextoRotina {
  sql: Sql;
  /** Data de negócio do dia (AAAA-MM-DD), pelo relógio do banco (system_data_negocio). */
  dataNegocio: string;
  /** Dia real (AAAA-MM-DD) no fuso do CRM. */
  diaReal: string;
  /** A data de negócio é domingo? */
  domingo: boolean;
  /** correlation_id da transação da rotina (já registrado como "sistema"). */
  correlationId: string;
}

/** Resumo de um job: só números e textos curtos (ex.: { deals: 2089, repasses: 12 }). */
export type ResumoJob = Record<string, number | string | boolean | null>;

export interface MotorScore {
  semanal(ctx: ContextoRotina): Promise<ResumoJob>;
  diario(ctx: ContextoRotina): Promise<ResumoJob>;
}
