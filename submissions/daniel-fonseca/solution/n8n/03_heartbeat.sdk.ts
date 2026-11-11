import { workflow, node, trigger, sticky, newCredential, expr } from '@n8n/workflow-sdk';

// Keep-alive do Supabase só no n8n (ADR-0006, revisão de 10/11 pelo Daniel): sem cron da Vercel.
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

const registrar = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Registrar heartbeat no banco',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'heartbeat',
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'source', fieldValue: 'n8n' },
          { fieldId: 'ok', fieldValue: expr('{{ true }}') },
          { fieldId: 'detail', fieldValue: 'keep-alive' }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 5000
  },
  output: [{ id: 5, source: 'n8n', ok: true, ran_at: '2026-11-11T00:22:22Z' }]
});

const nota = sticky('## Heartbeat (ADR-0006)\nO Supabase free pausa por inatividade. Todo dia às 06:00 de São Paulo, este fluxo grava uma linha em `heartbeat` (`source = n8n`) com a credencial G4 - Supabase.\nO keep-alive roda só no n8n, por decisão do Daniel (10/11). Se a gravação falhar nas 3 tentativas, a execução fica com erro no n8n.', [registrar], { color: 4 });

export default workflow('g4-heartbeat-v3', 'G4 · Heartbeat diário (Supabase ativo)')
  .add(todoDia)
  .to(registrar)
  .add(nota);
