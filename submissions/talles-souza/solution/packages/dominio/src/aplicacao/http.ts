/** Contrato HTTP da saúde da API. */
export const ROTA_SAUDE = '/health';

export interface RespostaSaude {
  status: 'ok';
  versao: string;
  dados: { total: number; referencia: string; checksum: string };
  /** ISO 8601. */
  iniciadoEm: string;
}
