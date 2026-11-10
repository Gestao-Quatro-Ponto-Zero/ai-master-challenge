import { workflow, node, trigger, sticky, newCredential, ifElse, switchCase, expr } from '@n8n/workflow-sdk';

const sbCred = { supabaseApi: newCredential('G4 - Supabase') };

const receberDecisao = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Receber decisão do revisor',
    parameters: { httpMethod: 'POST', path: 'g4-support/hitl-decision', authentication: 'headerAuth', responseMode: 'responseNode', options: {} },
    credentials: { httpHeaderAuth: newCredential('G4 - Segredo do webhookk') }
  },
  output: [{ body: { hitl_id: 1, decision: 'edit', final_text: 'Hello, ...', final_category: 'Access', reviewer: 'daniel', note: '' } }]
});

const prepararDecisao = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Preparar decisão',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'hitl_id', name: 'hitl_id', value: expr('{{ Number($json.body?.hitl_id ?? $json.hitl_id ?? 0) }}'), type: 'number' },
          { id: 'decision', name: 'decision', value: expr('{{ String($json.body?.decision ?? $json.decision ?? "").toLowerCase().trim() }}'), type: 'string' },
          { id: 'final_text', name: 'final_text', value: expr('{{ String($json.body?.final_text ?? "").trim() }}'), type: 'string' },
          { id: 'final_category', name: 'final_category', value: expr('{{ String($json.body?.final_category ?? "").trim() }}'), type: 'string' },
          { id: 'reviewer', name: 'reviewer', value: expr('{{ String($json.body?.reviewer ?? "revisor").trim() }}'), type: 'string' },
          { id: 'note', name: 'note', value: expr('{{ String($json.body?.note ?? "").trim() }}'), type: 'string' }
        ]
      },
      options: {}
    }
  },
  output: [{ hitl_id: 1, decision: 'edit', final_text: 'Hello, ...', final_category: 'Access', reviewer: 'daniel', note: '' }]
});

const entradaValida = ifElse({
  version: 2.3,
  config: {
    name: 'Entrada válida?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.hitl_id }}'), operator: { type: 'number', operation: 'gt' }, rightValue: 0 },
          { leftValue: expr('{{ ["approve", "edit", "reject"].includes($json.decision) }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } },
          { leftValue: expr('{{ $json.decision !== "edit" || $json.final_text.length > 0 }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } },
          { leftValue: expr('{{ $json.final_category === "" || ["Access", "Administrative rights", "HR Support", "Hardware", "Internal Project", "Miscellaneous", "Purchase", "Storage"].includes($json.final_category) }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } }
        ],
        combinator: 'and'
      },
      options: {}
    }
  }
});

const responderErro400 = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Responder erro 400',
    parameters: { respondWith: 'json', responseBody: '{ "error": "hitl_id e decision (approve | edit | reject) são obrigatórios; edit exige final_text; final_category deve ser uma das 8 categorias" }', options: { responseCode: 400 } }
  },
  output: [{}]
});

const buscarItem = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Buscar item pendente',
    parameters: {
      resource: 'row',
      operation: 'getAll',
      tableId: 'hitl_queue',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $json.hitl_id }}') }, { keyName: 'status', condition: 'eq', keyValue: 'pending' }] },
      returnAll: false,
      limit: 1
    },
    credentials: sbCred,
    alwaysOutputData: true
  },
  output: [{ id: 1, triage_run_id: 10, draft_text: 'Hello, ...', status: 'pending' }]
});

const itemExiste = ifElse({
  version: 2.3,
  config: {
    name: 'Item pendente existe?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [{ leftValue: expr('{{ Number($json.id ?? 0) > 0 }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } }],
        combinator: 'and'
      },
      options: {}
    }
  }
});

const buscarTriagem = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Buscar triagem do item',
    parameters: {
      resource: 'row',
      operation: 'getAll',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $json.triage_run_id }}') }] },
      returnAll: false,
      limit: 1
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 10, ticket_text: 'cannot login', category: 'Access', embedding: '[0.01,0.02]' }]
});

const responder409 = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Responder 409 (já decidido)',
    parameters: { respondWith: 'json', responseBody: '{ "error": "Item não encontrado ou já decidido por outro revisor" }', options: { responseCode: 409 } }
  },
  output: [{}]
});

const qualDecisao = switchCase({
  version: 3.4,
  config: {
    name: 'Qual decisão?',
    parameters: {
      rules: {
        values: [
          { outputKey: 'Aprovar ou editar', conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' }, conditions: [{ leftValue: expr('{{ ["approve", "edit"].includes($("Preparar decisão").item.json.decision) }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } }], combinator: 'and' } },
          { outputKey: 'Rejeitar', conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' }, conditions: [{ leftValue: expr('{{ $("Preparar decisão").item.json.decision }}'), operator: { type: 'string', operation: 'equals' }, rightValue: 'reject' }], combinator: 'and' } }
        ]
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Decisão desconhecida' }
    }
  }
});

const gravarSolucao = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Gravar solução validada',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'validated_resolutions',
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'category', fieldValue: expr('{{ $("Preparar decisão").item.json.final_category || $("Buscar triagem do item").item.json.category }}') },
          { fieldId: 'problem_text', fieldValue: expr('{{ $("Buscar triagem do item").item.json.ticket_text }}') },
          { fieldId: 'resolution_text', fieldValue: expr('{{ $("Preparar decisão").item.json.final_text || $("Buscar item pendente").item.json.draft_text }}') },
          { fieldId: 'embedding', fieldValue: expr('{{ $("Buscar triagem do item").item.json.embedding }}') },
          { fieldId: 'source', fieldValue: 'hitl' },
          { fieldId: 'hitl_id', fieldValue: expr('{{ $("Buscar item pendente").item.json.id }}') },
          { fieldId: 'approved_by', fieldValue: expr('{{ $("Preparar decisão").item.json.reviewer }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 15, category: 'Access' }]
});

const fecharItem = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Fechar item da fila',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'hitl_queue',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Buscar item pendente").item.json.id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: expr('{{ $("Preparar decisão").item.json.decision === "edit" ? "edited" : "approved" }}') },
          { fieldId: 'final_text', fieldValue: expr('{{ $("Preparar decisão").item.json.final_text || $("Buscar item pendente").item.json.draft_text }}') },
          { fieldId: 'final_category', fieldValue: expr('{{ $("Preparar decisão").item.json.final_category || null }}') },
          { fieldId: 'reviewer', fieldValue: expr('{{ $("Preparar decisão").item.json.reviewer }}') },
          { fieldId: 'review_note', fieldValue: expr('{{ $("Preparar decisão").item.json.note || null }}') },
          { fieldId: 'decided_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, status: 'edited', triage_run_id: 10 }]
});

const marcarRespondida = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Marcar triagem como respondida',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Buscar item pendente").item.json.triage_run_id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'answered_after_review' },
          { fieldId: 'response_text', fieldValue: expr('{{ $("Preparar decisão").item.json.final_text || $("Buscar item pendente").item.json.draft_text }}') },
          { fieldId: 'resolution_id', fieldValue: expr('{{ $("Gravar solução validada").item.json.id }}') },
          { fieldId: 'updated_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 10, status: 'answered_after_review', resolution_id: 15 }]
});

const fecharRejeitado = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Fechar item como rejeitado',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'hitl_queue',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Buscar item pendente").item.json.id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'rejected' },
          { fieldId: 'reviewer', fieldValue: expr('{{ $("Preparar decisão").item.json.reviewer }}') },
          { fieldId: 'review_note', fieldValue: expr('{{ $("Preparar decisão").item.json.note || null }}') },
          { fieldId: 'decided_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, status: 'rejected', triage_run_id: 10 }]
});

const marcarRejeitada = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Marcar triagem como rejeitada',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Buscar item pendente").item.json.triage_run_id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'rejected' },
          { fieldId: 'updated_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 10, status: 'rejected', resolution_id: null }]
});

const responderConsole = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Responder ao console',
    parameters: {
      respondWith: 'json',
      responseBody: expr('{{ JSON.stringify({ hitl_id: $("Buscar item pendente").item.json.id, decision: $("Preparar decisão").item.json.decision, triage_run_id: $json.id, triage_status: $json.status, resolution_id: $json.resolution_id ?? null }) }}'),
      options: { responseCode: 200 }
    }
  },
  output: [{}]
});

const nota = sticky('## Aprovação HITL (ADR-0004)\nO console envia a decisão do revisor. **Aprovar/editar** grava o texto final em `validated_resolutions` com o embedding do ticket (reaproveitado da triagem, sem nova chamada à OpenAI).\nA partir daí, um ticket parecido com confiança ≥ 0,9 pode sair no nível 1 com essa solução: o sistema aprende com o humano.\n**Rejeitar** devolve o ticket ao atendimento manual. Um item só pode ser decidido uma vez (409 no segundo clique).', [gravarSolucao, fecharItem, marcarRespondida], { color: 4 });

export default workflow('g4-hitl-v2', 'G4 · Aprovação HITL')
  .add(receberDecisao)
  .to(prepararDecisao)
  .to(entradaValida
    .onTrue(buscarItem)
    .onFalse(responderErro400))
  .add(buscarItem)
  .to(itemExiste
    .onTrue(buscarTriagem)
    .onFalse(responder409))
  .add(buscarTriagem)
  .to(qualDecisao
    .onCase(0, gravarSolucao.to(fecharItem).to(marcarRespondida).to(responderConsole))
    .onCase(1, fecharRejeitado.to(marcarRejeitada).to(responderConsole))
    .onCase(2, responderErro400))
  .add(nota);
