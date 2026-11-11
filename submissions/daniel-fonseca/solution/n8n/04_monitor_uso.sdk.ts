import { workflow, node, trigger, sticky, newCredential, ifElse, expr } from '@n8n/workflow-sdk';

const sbCred = { supabaseApi: newCredential('G4 - Supabase') };

const aCada15 = trigger({
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.4,
  config: {
    name: 'A cada 15 minutos',
    parameters: { rule: { interval: [{ field: 'minutes', minutesInterval: 15 }] } }
  },
  output: [{ timestamp: '2026-11-10T08:15:00-03:00' }]
});

const calcularSinais = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Calcular sinais de uso',
    parameters: {
      method: 'POST',
      url: 'https://awiphrbtvgapuuebiouw.supabase.co/rest/v1/rpc/usage_monitor_check',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'supabaseApi',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: '{}',
      options: { timeout: 20000 }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 5000
  },
  output: [{
    checked_at: '2026-11-10T11:15:00Z',
    alert_count: 1,
    signals: [{ signal: 'ip_triage', value: 14, threshold: 10, breached: true }],
    alerts: [{ signal: 'ip_triage', title: 'Uso do app: triagens de um único IP na última hora = 14 (limite 10)', body: 'Triagens de um único IP na última hora: 14, acima do limite de 10.', payload: { signal: 'ip_triage', value: 14 } }]
  }]
});

const haAlerta = ifElse({
  version: 2.3,
  config: {
    name: 'Há alerta novo?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.alert_count }}'), operator: { type: 'number', operation: 'gt' }, rightValue: 0 }
        ],
        combinator: 'and'
      },
      options: {}
    }
  }
});

const semAlertas = node({
  type: 'n8n-nodes-base.noOp',
  version: 1,
  config: { name: 'Uso dentro dos limites' },
  output: [{}]
});

const separarAlertas = node({
  type: 'n8n-nodes-base.splitOut',
  version: 1,
  config: {
    name: 'Separar alertas',
    parameters: { fieldToSplitOut: 'alerts', include: 'noOtherFields', options: {} }
  },
  output: [{ signal: 'ip_triage', title: 'Uso do app: ...', body: '...', payload: { signal: 'ip_triage' } }]
});

const formatarAlerta = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Formatar alerta para o Slack',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'kind', name: 'kind', value: 'usage_alert', type: 'string' },
          { id: 'channel_intended', name: 'channel_intended', value: 'slack', type: 'string' },
          { id: 'title', name: 'title', value: expr('{{ $json.title }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr(':warning: *{{ $json.title }}*\n{{ $json.body }}\n*Verificado em:* {{ DateTime.fromISO($json.payload.checked_at).setZone("America/Sao_Paulo").toFormat("dd/MM HH:mm") }} (São Paulo)'), type: 'string' },
          { id: 'payload', name: 'payload', value: expr('{{ $json.payload }}'), type: 'object' }
        ]
      },
      options: {}
    }
  },
  output: [{ kind: 'usage_alert', channel_intended: 'slack', title: 'Uso do app: ...', body: '...', payload: { signal: 'ip_triage' } }]
});

const gravarCaixa = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Gravar alerta na caixa do painel',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'notifications',
      dataToSend: 'autoMapInputData'
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, title: 'Uso do app: ...', body: '...' }]
});

const avisarSlack = node({
  type: 'n8n-nodes-base.slack',
  version: 2.7,
  config: {
    name: 'Avisar no Slack',
    disabled: true,
    parameters: {
      resource: 'message',
      operation: 'post',
      select: 'channel',
      channelId: { __rl: true, mode: 'name', value: '#suporte-alertas' },
      messageType: 'text',
      text: expr('{{ $("Gravar alerta na caixa do painel").item.json.body }}'),
      otherOptions: { includeLinkToWorkflow: false }
    },
    credentials: { slackApi: newCredential('G4 – Slack') },
    onError: 'continueRegularOutput'
  },
  output: [{ ok: true }]
});

const nota = sticky('## Monitor de uso (PRD §8.1)\nA cada 15 min, a função `usage_monitor_check` calcula 8 sinais (IP com muitas triagens, 429, volume, custo do dia, erros, prompt injection, ações em massa na fila, tamanho do banco) e devolve só os alertas novos.\nO alerta vai para a caixa do painel como Slack simulado. **O monitor só observa e alerta: nenhuma ação contra abuso sem instrução do Daniel.**', [calcularSinais, haAlerta, gravarCaixa], { color: 5 });

export default workflow('g4-monitor-uso', 'G4 · Monitor de uso (alertas)')
  .add(aCada15)
  .to(calcularSinais)
  .to(haAlerta
    .onTrue(separarAlertas)
    .onFalse(semAlertas))
  .add(separarAlertas)
  .to(formatarAlerta)
  .to(gravarCaixa)
  .to(avisarSlack)
  .add(nota);
