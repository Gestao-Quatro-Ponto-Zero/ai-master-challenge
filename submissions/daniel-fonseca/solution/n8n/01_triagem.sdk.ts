import { workflow, node, trigger, sticky, newCredential, ifElse, switchCase, expr } from '@n8n/workflow-sdk';

const sbCred = { supabaseApi: newCredential('G4 - Supabase') };
const aiCred = { openAiApi: newCredential('G4 - OpenAI') };

const receberTicket = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Receber ticket do console',
    parameters: {
      httpMethod: 'POST',
      path: 'g4-support/triage',
      authentication: 'headerAuth',
      responseMode: 'responseNode',
      options: {}
    },
    credentials: { httpHeaderAuth: newCredential('G4 - Segredo do webhookk') }
  },
  output: [{ body: { ticket_text: 'cannot login to confluence password reset needed', source: 'holdout', ds2_id: 31 } }]
});

const prepararTicket = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Preparar ticket',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'ticket_text', name: 'ticket_text', value: expr('{{ String($json.body?.ticket_text ?? $json.ticket_text ?? "").trim() }}'), type: 'string' },
          { id: 'source', name: 'source', value: expr('{{ $json.body?.source ?? $json.source ?? "console" }}'), type: 'string' },
          { id: 'ds2_id', name: 'ds2_id', value: expr('{{ $json.body?.ds2_id ?? $json.ds2_id ?? null }}'), type: 'number' },
          { id: 'requested_by', name: 'requested_by', value: expr('{{ $json.body?.requested_by ?? "console" }}'), type: 'string' }
        ]
      },
      options: { ignoreConversionErrors: true }
    }
  },
  output: [{ ticket_text: 'cannot login to confluence password reset needed', source: 'holdout', ds2_id: 31, requested_by: 'console' }]
});

const entradaValida = ifElse({
  version: 2.3,
  config: {
    name: 'Entrada válida?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.ticket_text }}'), operator: { type: 'string', operation: 'notEmpty', singleValue: true } },
          { leftValue: expr('{{ $json.ticket_text.length }}'), operator: { type: 'number', operation: 'lte' }, rightValue: 4000 },
          { leftValue: expr('{{ ["console", "holdout"].includes($json.source) }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } }
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
    parameters: {
      respondWith: 'json',
      responseBody: '{ "error": "ticket_text obrigatório (até 4.000 caracteres) e source deve ser console ou holdout" }',
      options: { responseCode: 400 }
    }
  },
  output: [{}]
});

const gerarEmbedding = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Gerar embedding (OpenAI)',
    parameters: {
      method: 'POST',
      url: 'https://api.openai.com/v1/embeddings',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'openAiApi',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ model: "text-embedding-3-small", input: $json.ticket_text, dimensions: 512 }) }}'),
      options: { timeout: 20000 }
    },
    credentials: aiCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000,
    onError: 'continueErrorOutput'
  },
  output: [{ data: [{ embedding: [0.01, -0.02, 0.03] }], usage: { total_tokens: 12 } }]
});

const classificarRag = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Classificar por casos parecidos (RAG)',
    parameters: {
      method: 'POST',
      url: 'https://awiphrbtvgapuuebiouw.supabase.co/rest/v1/rpc/classify_ticket',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'supabaseApi',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ query: $json.data[0].embedding }) }}'),
      options: { timeout: 20000 }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000,
    onError: 'continueErrorOutput'
  },
  output: [{ category: 'Access', confidence: 0.96, sensitive_share: 0.01, votes: { Access: 0.96, Hardware: 0.04 }, similar_cases: [{ id: 120, category: 'Access', similarity: 0.82, snippet: 'password reset confluence' }] }]
});

const buscarSolucoes = node({
  type: 'n8n-nodes-base.httpRequest',
  version: 4.5,
  config: {
    name: 'Buscar soluções validadas',
    parameters: {
      method: 'POST',
      url: 'https://awiphrbtvgapuuebiouw.supabase.co/rest/v1/rpc/match_resolutions_json',
      authentication: 'predefinedCredentialType',
      nodeCredentialType: 'supabaseApi',
      sendBody: true,
      contentType: 'json',
      specifyBody: 'json',
      jsonBody: expr('{{ JSON.stringify({ query: $("Gerar embedding (OpenAI)").item.json.data[0].embedding, p_category: $json.category, k: 3 }) }}'),
      options: { timeout: 20000 }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000,
    onError: 'continueErrorOutput'
  },
  output: [{ resolutions: [{ id: 4, resolution_text: 'Thanks for reaching out. You can reset your password...', similarity: 0.71, source: 'playbook' }] }]
});

const reunirDados = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Reunir resultado e limiares',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'ticket_text', name: 'ticket_text', value: expr('{{ $("Preparar ticket").item.json.ticket_text }}'), type: 'string' },
          { id: 'source', name: 'source', value: expr('{{ $("Preparar ticket").item.json.source }}'), type: 'string' },
          { id: 'ds2_id', name: 'ds2_id', value: expr('{{ $("Preparar ticket").item.json.ds2_id }}'), type: 'number' },
          { id: 'embedding', name: 'embedding', value: expr('{{ JSON.stringify($("Gerar embedding (OpenAI)").item.json.data[0].embedding) }}'), type: 'string' },
          { id: 'category', name: 'category', value: expr('{{ $("Classificar por casos parecidos (RAG)").item.json.category }}'), type: 'string' },
          { id: 'confidence', name: 'confidence', value: expr('{{ Number($("Classificar por casos parecidos (RAG)").item.json.confidence) }}'), type: 'number' },
          { id: 'sensitive_share', name: 'sensitive_share', value: expr('{{ Number($("Classificar por casos parecidos (RAG)").item.json.sensitive_share) }}'), type: 'number' },
          { id: 'votes', name: 'votes', value: expr('{{ $("Classificar por casos parecidos (RAG)").item.json.votes }}'), type: 'object' },
          { id: 'similar_cases', name: 'similar_cases', value: expr('{{ $("Classificar por casos parecidos (RAG)").item.json.similar_cases }}'), type: 'array' },
          { id: 'resolutions', name: 'resolutions', value: expr('{{ $json.resolutions }}'), type: 'array' },
          { id: 'limiar_auto', name: 'limiar_auto', value: 0.9, type: 'number' },
          { id: 'limiar_humano', name: 'limiar_humano', value: 0.5, type: 'number' },
          { id: 'limiar_sensivel', name: 'limiar_sensivel', value: 0.3, type: 'number' },
          { id: 'categorias_sensiveis', name: 'categorias_sensiveis', value: expr('{{ ["HR Support", "Administrative rights"] }}'), type: 'array' },
          { id: 'termos_bloqueio', name: 'termos_bloqueio', value: expr('{{ ["salary", "payroll", "bonus", "termination", "dismissal", "resignation", "lawsuit", "legal", "harassment", "sick leave", "maternity"] }}'), type: 'array' }
        ]
      },
      options: { ignoreConversionErrors: true }
    }
  },
  output: [{ ticket_text: 'cannot login to confluence password reset needed', source: 'holdout', ds2_id: 31, embedding: '[0.01,-0.02,0.03]', category: 'Access', confidence: 0.96, sensitive_share: 0.01, votes: { Access: 0.96 }, similar_cases: [], resolutions: [{ id: 4, resolution_text: 'Thanks for reaching out...', similarity: 0.71, source: 'playbook' }], limiar_auto: 0.9, limiar_humano: 0.5, limiar_sensivel: 0.3, categorias_sensiveis: ['HR Support', 'Administrative rights'], termos_bloqueio: ['salary'] }]
});

const marcarBloqueio = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Marcar termos de bloqueio',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'blocked', name: 'blocked', value: expr('{{ $json.termos_bloqueio.some(t => (" " + $json.ticket_text.toLowerCase().replace(/[^a-z0-9]+/g, " ") + " ").includes(" " + t + " ")) }}'), type: 'boolean' }
        ]
      },
      options: {}
    }
  },
  output: [{ ticket_text: 'cannot login to confluence password reset needed', source: 'holdout', ds2_id: 31, embedding: '[0.01]', category: 'Access', confidence: 0.96, sensitive_share: 0.01, votes: { Access: 0.96 }, similar_cases: [], resolutions: [{ id: 4 }], limiar_auto: 0.9, limiar_humano: 0.5, limiar_sensivel: 0.3, categorias_sensiveis: ['HR Support', 'Administrative rights'], termos_bloqueio: ['salary'], blocked: false }]
});

const aplicarPolitica = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Aplicar política de 3 níveis',
    parameters: {
      mode: 'manual',
      includeOtherFields: true,
      assignments: {
        assignments: [
          { id: 'level', name: 'level', value: expr('{{ ($json.categorias_sensiveis.includes($json.category) || $json.sensitive_share >= $json.limiar_sensivel || $json.blocked || $json.confidence < $json.limiar_humano) ? 3 : (($json.confidence >= $json.limiar_auto && $json.resolutions.length > 0) ? 1 : 2) }}'), type: 'number' },
          { id: 'level_reason', name: 'level_reason', value: expr('{{ $json.categorias_sensiveis.includes($json.category) ? "Categoria sensível: " + $json.category : $json.sensitive_share >= $json.limiar_sensivel ? "Votos em categorias sensíveis: " + Math.round($json.sensitive_share * 100) + "%" : $json.blocked ? "Termo da lista de bloqueio no texto" : $json.confidence < $json.limiar_humano ? "Confiança baixa (" + $json.confidence.toFixed(2) + ")" : ($json.confidence >= $json.limiar_auto && $json.resolutions.length > 0) ? "Confiança alta (" + $json.confidence.toFixed(2) + ") e solução validada da categoria" : $json.confidence >= $json.limiar_auto ? "Confiança alta (" + $json.confidence.toFixed(2) + "), mas sem solução validada da categoria" : "Confiança intermediária (" + $json.confidence.toFixed(2) + ")" }}'), type: 'string' }
        ]
      },
      options: {}
    }
  },
  output: [{ ticket_text: 'cannot login to confluence password reset needed', source: 'holdout', ds2_id: 31, embedding: '[0.01]', category: 'Access', confidence: 0.96, sensitive_share: 0.01, votes: { Access: 0.96 }, similar_cases: [], resolutions: [{ id: 4, resolution_text: 'Thanks...', similarity: 0.71 }], blocked: false, level: 1, level_reason: 'Confiança alta (0.96) e solução validada da categoria' }]
});

const montarRegistro = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Montar registro da triagem',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'source', name: 'source', value: expr('{{ $json.source }}'), type: 'string' },
          { id: 'ds2_id', name: 'ds2_id', value: expr('{{ $json.ds2_id }}'), type: 'number' },
          { id: 'ticket_text', name: 'ticket_text', value: expr('{{ $json.ticket_text }}'), type: 'string' },
          { id: 'embedding', name: 'embedding', value: expr('{{ $json.embedding }}'), type: 'string' },
          { id: 'category', name: 'category', value: expr('{{ $json.category }}'), type: 'string' },
          { id: 'confidence', name: 'confidence', value: expr('{{ $json.confidence }}'), type: 'number' },
          { id: 'sensitive_share', name: 'sensitive_share', value: expr('{{ $json.sensitive_share }}'), type: 'number' },
          { id: 'votes', name: 'votes', value: expr('{{ $json.votes }}'), type: 'object' },
          { id: 'similar_cases', name: 'similar_cases', value: expr('{{ $json.similar_cases }}'), type: 'array' },
          { id: 'blocked', name: 'blocked', value: expr('{{ $json.blocked }}'), type: 'boolean' },
          { id: 'level', name: 'level', value: expr('{{ $json.level }}'), type: 'number' },
          { id: 'level_reason', name: 'level_reason', value: expr('{{ $json.level_reason }}'), type: 'string' },
          { id: 'status', name: 'status', value: 'received', type: 'string' }
        ]
      },
      options: { ignoreConversionErrors: true }
    }
  },
  output: [{ source: 'holdout', ds2_id: 31, ticket_text: 'cannot login', embedding: '[0.01]', category: 'Access', confidence: 0.96, sensitive_share: 0.01, votes: { Access: 0.96 }, similar_cases: [], blocked: false, level: 1, level_reason: 'Confiança alta', status: 'received' }]
});

const registrarTriagem = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Registrar triagem',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'triage_runs',
      dataToSend: 'autoMapInputData'
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, status: 'received', level: 1 }]
});

const rotearNivel = switchCase({
  version: 3.4,
  config: {
    name: 'Rotear por nível',
    parameters: {
      rules: {
        values: [
          { outputKey: 'Automático', conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' }, conditions: [{ leftValue: expr('{{ $("Aplicar política de 3 níveis").item.json.level }}'), operator: { type: 'number', operation: 'equals' }, rightValue: 1 }], combinator: 'and' } },
          { outputKey: 'Revisão humana', conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' }, conditions: [{ leftValue: expr('{{ $("Aplicar política de 3 níveis").item.json.level }}'), operator: { type: 'number', operation: 'equals' }, rightValue: 2 }], combinator: 'and' } },
          { outputKey: 'Só humano', conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' }, conditions: [{ leftValue: expr('{{ $("Aplicar política de 3 níveis").item.json.level }}'), operator: { type: 'number', operation: 'equals' }, rightValue: 3 }], combinator: 'and' } }
        ]
      },
      options: { fallbackOutput: 'extra', renameFallbackOutput: 'Fallback → só humano' }
    }
  }
});

const adaptarSolucao = node({
  type: '@n8n/n8n-nodes-langchain.openAi',
  version: 2.3,
  config: {
    name: 'Adaptar solução validada ao ticket (OpenAI)',
    parameters: {
      resource: 'text',
      operation: 'response',
      modelId: { __rl: true, mode: 'id', value: 'gpt-5.4-mini' },
      responses: {
        values: [
          { type: 'text', role: 'user', content: expr('Ticket:\n{{ $("Aplicar política de 3 níveis").item.json.ticket_text }}\n\nCategory: {{ $("Aplicar política de 3 níveis").item.json.category }}\n\nValidated solution:\n{{ $("Aplicar política de 3 níveis").item.json.resolutions[0].resolution_text }}') }
        ]
      },
      simplify: true,
      options: {
        instructions: 'You are an IT service desk agent. Adapt the VALIDATED SOLUTION to the customer ticket.\nRules:\n1. Use only the steps, conditions and information that are in the validated solution. Never add new steps, deadlines, promises, exceptions, links or contacts.\n2. You may reorder, shorten and personalize the wording so it addresses this ticket.\n3. Write the reply in the same language as the ticket.\n4. If the validated solution does not address what the ticket asks for, set fits to false, leave response_text empty and explain why in reason (in Brazilian Portuguese).\nReturn only the JSON object.',
        maxTokens: 900,
        reasoning: { reasoningOptions: { effort: 'low', summary: 'none' } },
        store: false,
        textFormat: { textOptions: { type: 'json_schema', name: 'adapted_reply', strict: true, schema: '{"type":"object","properties":{"response_text":{"type":"string"},"fits":{"type":"boolean"},"reason":{"type":"string"}},"required":["response_text","fits","reason"],"additionalProperties":false}' } }
      }
    },
    credentials: aiCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000,
    onError: 'continueErrorOutput'
  },
  output: [{ output: [{ type: 'message', content: [{ type: 'output_text', text: '{"response_text":"Hi! You can reset your password...","fits":true,"reason":""}' }] }] }]
});

const lerAdaptacao = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Ler resposta adaptada',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'llm', name: 'llm', value: expr('{{ (() => { const j = $json; const c = Array.isArray(j.output) ? j.output.flatMap(o => o.content ?? []).find(x => x.type === "output_text") : null; const t = c ? c.text : (j.output_text ?? j.text ?? j.output); if (t && typeof t === "object") return t; try { return JSON.parse(t); } catch (e) { return { response_text: "", fits: false, reason: "Resposta do LLM fora do formato" }; } })() }}'), type: 'object' }
        ]
      },
      options: {}
    }
  },
  output: [{ llm: { response_text: 'Hi! You can reset your password...', fits: true, reason: '' } }]
});

const solucaoServe = ifElse({
  version: 2.3,
  config: {
    name: 'Solução serve ao ticket?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [
          { leftValue: expr('{{ $json.llm.fits === true && String($json.llm.response_text ?? "").trim().length > 0 }}'), operator: { type: 'boolean', operation: 'true', singleValue: true } }
        ],
        combinator: 'and'
      },
      options: {}
    }
  }
});

const marcarRespondido = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Marcar como respondido',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Registrar triagem").item.json.id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'auto_answered' },
          { fieldId: 'response_text', fieldValue: expr('{{ $json.llm.response_text }}') },
          { fieldId: 'resolution_id', fieldValue: expr('{{ $("Aplicar política de 3 níveis").item.json.resolutions[0].id }}') },
          { fieldId: 'updated_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, status: 'auto_answered', level: 1, level_reason: 'Confiança alta', response_text: 'Hi!...', resolution_id: 4 }]
});

const redigirRascunho = node({
  type: '@n8n/n8n-nodes-langchain.openAi',
  version: 2.3,
  config: {
    name: 'Redigir rascunho (OpenAI)',
    parameters: {
      resource: 'text',
      operation: 'response',
      modelId: { __rl: true, mode: 'id', value: 'gpt-5.4-mini' },
      responses: {
        values: [
          { type: 'text', role: 'user', content: expr('Ticket:\n{{ $("Aplicar política de 3 níveis").item.json.ticket_text }}\n\nPredicted category: {{ $("Aplicar política de 3 níveis").item.json.category }} (confidence {{ $("Aplicar política de 3 níveis").item.json.confidence.toFixed(2) }})\n\nValidated solutions for this category:\n{{ $("Aplicar política de 3 níveis").item.json.resolutions.length ? $("Aplicar política de 3 níveis").item.json.resolutions.map((r, i) => (i + 1) + ". " + r.resolution_text).join("\\n") : "(none yet)" }}\n\nMost similar past tickets (context only, they have no resolution):\n{{ $("Aplicar política de 3 níveis").item.json.similar_cases.map(c => "- [" + c.category + ", sim " + c.similarity + "] " + c.snippet).join("\\n") }}') }
        ]
      },
      simplify: true,
      options: {
        instructions: 'You are an IT service desk agent drafting a reply that a HUMAN agent will review before sending.\nRules:\n1. Base the draft on the validated solutions when they apply. Similar past tickets only show what kind of request this is; they contain no answers.\n2. Never invent policies, deadlines, promises or exceptions. When information is missing, ask the customer for it.\n3. Write the draft in the same language as the ticket.\n4. In checks, list 2 to 4 items, in Brazilian Portuguese, that the reviewer must verify before sending.\nReturn only the JSON object.',
        maxTokens: 1200,
        reasoning: { reasoningOptions: { effort: 'low', summary: 'none' } },
        store: false,
        textFormat: { textOptions: { type: 'json_schema', name: 'draft_reply', strict: true, schema: '{"type":"object","properties":{"draft":{"type":"string"},"checks":{"type":"array","items":{"type":"string"}}},"required":["draft","checks"],"additionalProperties":false}' } }
      }
    },
    credentials: aiCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000,
    onError: 'continueErrorOutput'
  },
  output: [{ output: [{ type: 'message', content: [{ type: 'output_text', text: '{"draft":"Hello, ...","checks":["Confirmar o nome do sistema"]}' }] }] }]
});

const lerRascunho = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Ler rascunho',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'llm', name: 'llm', value: expr('{{ (() => { const j = $json; const c = Array.isArray(j.output) ? j.output.flatMap(o => o.content ?? []).find(x => x.type === "output_text") : null; const t = c ? c.text : (j.output_text ?? j.text ?? j.output); if (t && typeof t === "object") return t; try { return JSON.parse(t); } catch (e) { return { draft: String(t ?? ""), checks: ["Resposta do LLM fora do formato: revisar com atenção"] }; } })() }}'), type: 'object' }
        ]
      },
      options: {}
    }
  },
  output: [{ llm: { draft: 'Hello, ...', checks: ['Confirmar o nome do sistema'] } }]
});

const montarItemFila = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Montar item da fila',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'triage_run_id', name: 'triage_run_id', value: expr('{{ $("Registrar triagem").item.json.id }}'), type: 'number' },
          { id: 'draft_text', name: 'draft_text', value: expr('{{ $json.llm.draft }}'), type: 'string' },
          { id: 'checks', name: 'checks', value: expr('{{ $json.llm.checks ?? [] }}'), type: 'array' }
        ]
      },
      options: {}
    }
  },
  output: [{ triage_run_id: 1, draft_text: 'Hello, ...', checks: ['Confirmar o nome do sistema'] }]
});

const enviarFila = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Enviar para fila de revisão',
    parameters: {
      resource: 'row',
      operation: 'create',
      tableId: 'hitl_queue',
      dataToSend: 'autoMapInputData'
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, triage_run_id: 1, draft_text: 'Hello, ...', checks: ['Confirmar o nome do sistema'], status: 'pending' }]
});

const marcarRevisao = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Marcar como em revisão',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Registrar triagem").item.json.id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'pending_review' },
          { fieldId: 'level', fieldValue: expr('{{ 2 }}') },
          { fieldId: 'level_reason', fieldValue: expr('{{ $("Aplicar política de 3 níveis").item.json.level === 1 ? $("Aplicar política de 3 níveis").item.json.level_reason + " → solução validada não se aplica ao ticket" : $("Aplicar política de 3 níveis").item.json.level_reason }}') },
          { fieldId: 'updated_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, status: 'pending_review', level: 2, level_reason: 'Confiança intermediária (0.75)' }]
});

const resumirHumano = node({
  type: '@n8n/n8n-nodes-langchain.openAi',
  version: 2.3,
  config: {
    name: 'Resumir para o humano (OpenAI)',
    parameters: {
      resource: 'text',
      operation: 'response',
      modelId: { __rl: true, mode: 'id', value: 'gpt-5.4-mini' },
      responses: {
        values: [
          { type: 'text', role: 'user', content: expr('Ticket:\n{{ $("Aplicar política de 3 níveis").item.json.ticket_text }}\n\nPredicted category: {{ $("Aplicar política de 3 níveis").item.json.category }}\nWhy it must be handled only by a human: {{ $("Aplicar política de 3 níveis").item.json.level_reason }}') }
        ]
      },
      simplify: true,
      options: {
        instructions: 'You triage support tickets that must be handled ONLY by a human. Do NOT write any reply to the customer.\nWrite in Brazilian Portuguese:\n- summary: 2 to 3 sentences on what the person needs;\n- risk_signals: sensitive aspects (HR, legal, personal data, access privileges, urgency); empty list if none;\n- suggested_owner: the team that should handle it.\nReturn only the JSON object.',
        maxTokens: 700,
        reasoning: { reasoningOptions: { effort: 'low', summary: 'none' } },
        store: false,
        textFormat: { textOptions: { type: 'json_schema', name: 'human_summary', strict: true, schema: '{"type":"object","properties":{"summary":{"type":"string"},"risk_signals":{"type":"array","items":{"type":"string"}},"suggested_owner":{"type":"string"}},"required":["summary","risk_signals","suggested_owner"],"additionalProperties":false}' } }
      }
    },
    credentials: aiCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000,
    onError: 'continueErrorOutput'
  },
  output: [{ output: [{ type: 'message', content: [{ type: 'output_text', text: '{"summary":"Colaborador pede...","risk_signals":["RH"],"suggested_owner":"RH"}' }] }] }]
});

const montarAlerta = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Montar mensagem de alerta',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'llm', name: 'llm', value: expr('{{ (() => { const j = $json; const c = Array.isArray(j.output) ? j.output.flatMap(o => o.content ?? []).find(x => x.type === "output_text") : null; const t = c ? c.text : (j.output_text ?? j.text ?? j.output); if (t && typeof t === "object") return t; try { return JSON.parse(t); } catch (e) { return { summary: String(t ?? ""), risk_signals: [], suggested_owner: "Suporte" }; } })() }}'), type: 'object' },
          { id: 'title', name: 'title', value: expr('{{ "Ticket só para humano · " + $("Aplicar política de 3 níveis").item.json.category + " · triagem #" + $("Registrar triagem").item.json.id }}'), type: 'string' }
        ]
      },
      options: {}
    }
  },
  output: [{ llm: { summary: 'Colaborador pede...', risk_signals: ['RH'], suggested_owner: 'RH' }, title: 'Ticket só para humano · HR Support · triagem #1' }]
});

const montarCorpo = node({
  type: 'n8n-nodes-base.set',
  version: 3.5,
  config: {
    name: 'Formatar texto do alerta',
    parameters: {
      mode: 'manual',
      includeOtherFields: false,
      assignments: {
        assignments: [
          { id: 'triage_run_id', name: 'triage_run_id', value: expr('{{ $("Registrar triagem").item.json.id }}'), type: 'number' },
          { id: 'kind', name: 'kind', value: 'level3_alert', type: 'string' },
          { id: 'channel_intended', name: 'channel_intended', value: 'slack', type: 'string' },
          { id: 'title', name: 'title', value: expr('{{ $json.title }}'), type: 'string' },
          { id: 'body', name: 'body', value: expr(':rotating_light: *{{ $json.title }}*\n*Motivo:* {{ $("Aplicar política de 3 níveis").item.json.level_reason }}\n*Categoria prevista:* {{ $("Aplicar política de 3 níveis").item.json.category }} (confiança {{ $("Aplicar política de 3 níveis").item.json.confidence.toFixed(2) }})\n*Resumo:* {{ $json.llm.summary }}\n*Sinais de risco:* {{ ($json.llm.risk_signals ?? []).join(", ") || "nenhum" }}\n*Time sugerido:* {{ $json.llm.suggested_owner }}\nA IA não respondeu ao cliente. Abra o console para assumir o ticket.'), type: 'string' },
          { id: 'payload', name: 'payload', value: expr('{{ $json.llm }}'), type: 'object' }
        ]
      },
      options: {}
    }
  },
  output: [{ triage_run_id: 1, kind: 'level3_alert', channel_intended: 'slack', title: 'Ticket só para humano', body: 'texto do alerta', payload: { summary: 'Colaborador pede...' } }]
});

const gravarCaixa = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Gravar na caixa do painel',
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
  output: [{ id: 1, title: 'Ticket só para humano', body: 'texto do alerta' }]
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
      text: expr('{{ $("Gravar na caixa do painel").item.json.body }}'),
      otherOptions: { includeLinkToWorkflow: false }
    },
    credentials: { slackApi: newCredential('G4 – Slack') },
    onError: 'continueRegularOutput'
  },
  output: [{ ok: true }]
});

const marcarAguardando = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Marcar como aguardando humano',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Registrar triagem").item.json.id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'awaiting_human' },
          { fieldId: 'level', fieldValue: expr('{{ 3 }}') },
          { fieldId: 'updated_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    retryOnFail: true,
    maxTries: 3,
    waitBetweenTries: 1000
  },
  output: [{ id: 1, status: 'awaiting_human', level: 3 }]
});

const responderConsole = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Responder ao console',
    parameters: {
      respondWith: 'json',
      responseBody: expr('{{ JSON.stringify({ triage_run_id: $("Registrar triagem").item.json.id, status: $json.status, level: $json.level ?? $("Aplicar política de 3 níveis").item.json.level, level_reason: $json.level_reason ?? $("Aplicar política de 3 níveis").item.json.level_reason, category: $("Aplicar política de 3 níveis").item.json.category, confidence: $("Aplicar política de 3 níveis").item.json.confidence, sensitive_share: $("Aplicar política de 3 níveis").item.json.sensitive_share, votes: $("Aplicar política de 3 níveis").item.json.votes, similar_cases: $("Aplicar política de 3 níveis").item.json.similar_cases, resolutions: $("Aplicar política de 3 níveis").item.json.resolutions, response_text: $json.response_text ?? null, resolution_id: $json.resolution_id ?? null, hitl: $("Enviar para fila de revisão").isExecuted ? { hitl_id: $("Enviar para fila de revisão").item.json.id, draft_text: $("Enviar para fila de revisão").item.json.draft_text, checks: $("Enviar para fila de revisão").item.json.checks } : null, notification: $("Gravar na caixa do painel").isExecuted ? { notification_id: $("Gravar na caixa do painel").item.json.id, title: $("Gravar na caixa do painel").item.json.title, body: $("Gravar na caixa do painel").item.json.body } : null }) }}'),
      options: { responseCode: 200 }
    }
  },
  output: [{}]
});

const marcarErro = node({
  type: 'n8n-nodes-base.supabase',
  version: 1,
  config: {
    name: 'Marcar triagem com erro',
    parameters: {
      resource: 'row',
      operation: 'update',
      tableId: 'triage_runs',
      filterType: 'manual',
      matchType: 'allFilters',
      filters: { conditions: [{ keyName: 'id', condition: 'eq', keyValue: expr('{{ $("Registrar triagem").item.json.id }}') }] },
      dataToSend: 'defineBelow',
      fieldsUi: {
        fieldValues: [
          { fieldId: 'status', fieldValue: 'error' },
          { fieldId: 'updated_at', fieldValue: expr('{{ $now.toISO() }}') }
        ]
      }
    },
    credentials: sbCred,
    alwaysOutputData: true
  },
  output: [{ id: 1, status: 'error' }]
});

const responderFalha = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Responder falha (503)',
    parameters: {
      respondWith: 'json',
      responseBody: '{ "error": "Falha temporária na triagem (OpenAI ou banco). O console deve usar o modo de resultados pré-computados." }',
      options: { responseCode: 503 }
    }
  },
  output: [{}]
});

const notaPolitica = sticky('## Política de 3 níveis (ADR-0010 + ADR-0012)\n**Nível 3 (só humano):** categoria sensível (HR Support, Administrative rights), ≥ 30% dos votos em categoria sensível, termo da lista de bloqueio ou confiança < 0,5.\n**Nível 1 (automático):** confiança ≥ 0,9 **e** existe solução validada da categoria.\n**Nível 2 (revisão humana):** o resto.\nNo holdout de 9.567 tickets: 31% / 28% / 41%; o nível 1 acerta 98,8%.\nOs limiares ficam no nó *Reunir resultado e limiares*: edite lá.', [reunirDados, marcarBloqueio, aplicarPolitica], { color: 4 });

const notaRag = sticky('## Classificação (RAG no Supabase)\nO voto dos 50 tickets mais parecidos (peso similaridade^16) roda na função SQL `classify_ticket`. O n8n só chama a função pela API REST do Supabase (HTTP Request + credencial Supabase), porque o nó Supabase não chama funções.\nO embedding usa o HTTP Request com a credencial nativa da OpenAI, porque o nó *Embeddings OpenAI* é sub-nó e não tem saída no fluxo principal.', [gerarEmbedding, classificarRag, buscarSolucoes], { color: 5 });

const notaNivel1 = sticky('## Nível 1: resposta automática\nO LLM só adapta a solução validada (sem passos, prazos ou promessas novas). Se ela não servir ao ticket, o ticket desce para a revisão humana.', [adaptarSolucao, lerAdaptacao, solucaoServe, marcarRespondido], { color: 6 });

const notaNivel3 = sticky('## Nível 3: só humano\nA IA não responde ao cliente: resume, aponta riscos e avisa. A caixa do painel é a fonte de verdade. O nó Slack fica **desativado** até existir um workspace; para ligar, selecione a credencial e o canal (ADR-0007).', [resumirHumano, montarAlerta, montarCorpo, gravarCaixa, avisarSlack, marcarAguardando], { color: 3 });

export default workflow('g4-triagem-v2', 'G4 · Triagem de ticket (RAG + 3 níveis)')
  .add(receberTicket)
  .to(prepararTicket)
  .to(entradaValida
    .onTrue(gerarEmbedding)
    .onFalse(responderErro400))
  .add(gerarEmbedding)
  .to(classificarRag)
  .to(buscarSolucoes)
  .to(reunirDados)
  .to(marcarBloqueio)
  .to(aplicarPolitica)
  .to(montarRegistro)
  .to(registrarTriagem)
  .to(rotearNivel
    .onCase(0, adaptarSolucao)
    .onCase(1, redigirRascunho)
    .onCase(2, resumirHumano)
    .onCase(3, resumirHumano))
  .add(adaptarSolucao)
  .to(lerAdaptacao)
  .to(solucaoServe
    .onTrue(marcarRespondido.to(responderConsole))
    .onFalse(redigirRascunho))
  .add(redigirRascunho)
  .to(lerRascunho)
  .to(montarItemFila)
  .to(enviarFila)
  .to(marcarRevisao)
  .to(responderConsole)
  .add(resumirHumano)
  .to(montarAlerta)
  .to(montarCorpo)
  .to(gravarCaixa)
  .to(avisarSlack)
  .to(marcarAguardando)
  .to(responderConsole)
  .add(gerarEmbedding.onError(responderFalha))
  .add(classificarRag.onError(responderFalha))
  .add(buscarSolucoes.onError(responderFalha))
  .add(adaptarSolucao.onError(marcarErro))
  .add(redigirRascunho.onError(marcarErro))
  .add(resumirHumano.onError(marcarErro))
  .add(marcarErro)
  .to(responderFalha)
  .add(notaPolitica)
  .add(notaRag)
  .add(notaNivel1)
  .add(notaNivel3);
