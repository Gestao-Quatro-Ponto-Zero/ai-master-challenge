import { workflow, node, trigger, sticky, newCredential, placeholder, expr } from '@n8n/workflow-sdk';

const sbCred = { supabaseApi: newCredential('G4 - Supabase') };

const todoDia = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.4,
  config: {
    name: 'Todo dia às 06:00 (São Paulo)',
    parameters: { rule: { interval: [{ field: 'days', daysInterval: 1, triggerAtHour: 6, triggerAtMinute: 0 }] } }
  },
  output: [{ timestamp: '2026-11-10T06:00:00-03:00' }]
});

const chamarVercel = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Chamar /api/heartbeat da Vercel',
    parameters: {
      method: 'GET',
      url: placeholder('URL da rota no app da Vercel, ex.: https://<projeto>.vercel.app/api/heartbeat?source=n8n'),
      authentication: 'genericCredentialType',
      genericAuthType: 'httpTemplatedCustomAuth',
      options: { timeout: 20000 }
    },
    credentials: { httpTemplatedCustomAuth: newCredential('G4 – Cron da Vercel') },
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 5000,
    onError: 'continueErrorOutput'
  },
  output: [{ ok: true, source: 'n8n', ran_at: '2026-11-10T09:00:00Z' }]
});

const heartbeatOk = node({
  type: 'n8n-nodes-base.noOp',
  version: 1,
  config: { name: 'Heartbeat ok' },
  output: [{ ok: true }]
});

const registrarDireto = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Registrar heartbeat direto no banco',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'heartbeat',
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'source', fieldValue: 'n8n-fallback' },
          { fieldId: 'ok', fieldValue: expr('{{ false }}') },
          { fieldId: 'detail', fieldValue: expr('{{ "Vercel não respondeu: " + String($json.error?.message ?? $json.message ?? "erro desconhecido").slice(0, 300) }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 5000
  },
  output: [{ id: 1, ran_at: '2026-11-10T09:00:05Z' }]
});

const gravarAlerta = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Gravar alerta na caixa do painel',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'notifications',
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'kind', fieldValue: 'heartbeat_failure' },
          { fieldId: 'channel_intended', fieldValue: 'slack' },
          { fieldId: 'title', fieldValue: 'Heartbeat da Vercel falhou' },
          { fieldId: 'body', fieldValue: expr('{{ "O n8n não conseguiu chamar /api/heartbeat às " + $now.setZone("America/Sao_Paulo").toFormat("dd/MM HH:mm") + ". O banco foi mantido ativo por escrita direta; verifique o deploy da Vercel." }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 5000
  },
  output: [{ id: 2 }]
});

const nota = sticky('## Heartbeat (ADR-0006)\nO Supabase free pausa por inatividade. O cron da Vercel chama `/api/heartbeat` uma vez por dia; este fluxo é a **redundância**, às 06:00 de São Paulo.\nSe a Vercel falhar, o n8n escreve direto no banco (mantém o projeto ativo) e deixa um alerta na caixa do painel.', [chamarVercel, registrarDireto, gravarAlerta], { color: 4 });

export default workflow('g4-heartbeat-v2', 'G4 · Heartbeat diário (Supabase ativo)')
  .add(todoDia)
  .to(chamarVercel)
  .to(heartbeatOk)
  .add(chamarVercel.onError(registrarDireto))
  .add(registrarDireto)
  .to(gravarAlerta)
  .add(nota);
