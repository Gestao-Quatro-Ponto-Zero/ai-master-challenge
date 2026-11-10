// Parâmetros do CRM. Espelham config_parametros do banco; quando a fonte for o banco, vêm de lá.

export const CONFIG = {
  /** Relógio do CRM no modo demonstração (P6): "hoje" = último dia com registro no dataset. */
  dataReferencia: "2017-12-31",
  fusoHorario: "America/Sao_Paulo",
  faixasNota: { alta: 70, media: 40 },
  icone: { diasMinQuente: 15, diasMaxQuente: 106, diasMaxRisco: 138, precoMinQuente: 3000 },
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
  prioridadesVisiveis: 5,
  metaPrioridadesDia: 10,
  diasPuladoAlerta: 3,
  fitMinimoFurarFila: 75,
  janelaPainelDias: 30,
  papeisReabrir: ["manager", "admin"] as const,
  papeisImportacao: ["manager", "admin"] as const,
  papeisCriarTag: ["manager", "admin"] as const,
  /** Limite de escritas por endereço de rede (não há login; o limite por usuário seria contornável). */
  limiteEscritasPorIp: { quantidade: 60, janelaSegundos: 60 },
  porPagina: 50,
  cartoesPorColuna: 50,
} as const;
