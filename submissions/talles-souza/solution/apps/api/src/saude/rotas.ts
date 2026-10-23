/** Rota de saúde: o processo está de pé e com qual dado (total, referência e checksum conferido). */
import { Hono } from 'hono';
import { ROTA_SAUDE, type RespostaSaude } from '@lead-scorer/dominio/aplicacao';

/** O que a saúde informa; montado pelo servidor na partida. */
export interface InfoSaude {
  versao: string;
  /** ISO 8601. */
  iniciadoEm: string;
  dados: { total: number; referencia: string; checksum: string };
}

/** `GET /health`, fora do rate limit (é do monitoramento). */
export function rotasSaude(info: InfoSaude): Hono {
  const app = new Hono();
  app.get(ROTA_SAUDE, (c) => {
    const corpo: RespostaSaude = {
      status: 'ok',
      versao: info.versao,
      dados: info.dados,
      iniciadoEm: info.iniciadoEm,
    };
    return c.json(corpo);
  });
  return app;
}
