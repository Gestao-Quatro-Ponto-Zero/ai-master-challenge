// Parâmetros do CRM. Espelham config_parametros do banco; quando a fonte for o banco, vêm de lá.

export const CONFIG = {
  /** Relógio do CRM no modo demonstração (P6): "hoje" = último dia com registro no dataset. */
  dataReferencia: "2017-12-31",
  /** Relógio que anda (decisão 48, migration 0034): no dia real ancoraReal, a data de negócio é ancoraNegocio. */
  relogio: { ancoraReal: "2026-11-10", ancoraNegocio: "2017-12-31" },
  fusoHorario: "America/Sao_Paulo",
  faixasNota: { alta: 70, media: 40 },
  /** precoMinQuente null = super hot sem critério de ticket (O-24). */
  icone: { diasMinQuente: 15, diasMaxQuente: 106, diasMaxRisco: 138, precoMinQuente: null as number | null },
  diasSemContatoRisco: 14,
  acoesContato: ["liguei", "requalifiquei"] as const,
  /** Tipos de atividade do ✓ nas Prioridades do dia (decisão 37); mesma lista de config_tipos_atividade. */
  tiposAtividade: [
    { codigo: "ligacao", rotulo: "Ligação", contaComoContato: true },
    { codigo: "email", rotulo: "E-mail", contaComoContato: true },
    { codigo: "mensagem", rotulo: "Mensagem", contaComoContato: true },
    { codigo: "reuniao", rotulo: "Reunião", contaComoContato: true },
    { codigo: "proposta_enviada", rotulo: "Proposta enviada", contaComoContato: true },
    { codigo: "requalificado", rotulo: "Requalificado", contaComoContato: true },
    { codigo: "sem_resposta", rotulo: "Sem resposta", contaComoContato: true },
  ],
  limiteLote: 500,
  maxTagsPorDeal: 10,
  segundosDesfazer: 10,
  /** Itens das Prioridades do dia, todos à mostra (O-34: 20 por dia, sem fila). */
  metaPrioridadesDia: 20,
  diasPuladoAlerta: 3,
  fitMinimoFurarFila: 75,
  /** Pesos da nota (decisão 33): NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS (0 a 20). */
  pesosNota: { fit: 0.7, heat: 0.3 },
  /** Itens da lista do dia do manager e do admin (config_parametros.prioridades_gestor). Leandro: "só o que pede ação". */
  prioridadesGestor: "atencao" as "icone" | "atencao" | "todos",
  janelaPainelDias: 30,
  papeisReabrir: ["manager", "admin"] as const,
  papeisImportacao: ["manager", "admin"] as const,
  papeisCriarTag: ["manager", "admin"] as const,
  /** Limite de escritas por endereço de rede (não há login; o limite por usuário seria contornável). */
  limiteEscritasPorIp: { quantidade: 60, janelaSegundos: 60 },
  porPagina: 50,
  cartoesPorColuna: 50,
} as const;
