# SPEC - Perfil DISC + Assistente de Follow-up

## Objetivo de negocio
Ajudar vendedores e managers a acelerar conversao com abordagens de follow-up personalizadas por perfil comportamental, sem perder explicabilidade.

## Escopo funcional
1. Inferencia de perfil DISC por lead: D, I, S, C ou indefinido.
2. Geracao de 3 copys de follow-up por lead: consultivo, direto e provocativo elegante.
3. Botao Copiar por copy com fallback Selecionar texto quando clipboard nao estiver disponivel.
4. Bloco de ganchos de venda (3 a 5 itens priorizados).
5. Recomendacao de proxima melhor acao.

## Entradas e saidas por funcao

### infer_disc_profile(lead_row, today) -> DiscInference
Entradas:
- lead_row: linha com colunas reais do dataset consolidado
- today: data de referencia

Saida:
- disc_profile: D, I, S, C, indefinido
- disc_confidence: 0-100
- disc_rationale: explicacao de 2-3 linhas
- buying_signals, pain_points, objections

### build_lead_profile(lead_row, today) -> dict
Entradas:
- lead_row: linha selecionada no app
- today: data de referencia

Saida:
- objeto LeadProfile padronizado para engine de follow-up

### get_sales_hooks(lead_profile) -> list[dict]
Saida por item:
- priority
- hook
- why_it_works
- opening_question
- risk_if_badly_used

### get_next_best_action(lead_profile, hooks) -> str
Saida:
- recomendacao acionavel em linguagem comercial

### generate_followup_package(lead_profile) -> dict
Saida:
- lead_id
- disc_profile
- copies: 3 itens com tone, subject e text
- sales_hooks
- next_best_action

## Contrato de dados (campos obrigatorios)
Fonte real consolidada no app:
- opportunity_id
- sales_agent
- product
- account
- deal_stage
- engage_date
- close_value
- industry
- acquisition_channel
- revenue
- employees
- has_trial
- manager
- regional_office

Campos derivados:
- days_in_stage
- disc_profile
- disc_confidence
- disc_rationale

## Regras de fallback para dados faltantes
1. Se deal_stage ausente ou close_value <= 0, DISC vira indefinido com motivo explicito.
2. Se lead_id/lead_name ausentes, follow-up usa template fallback elegante.
3. Se clipboard bloquear copy, fallback seleciona texto e instrui Ctrl+C.
4. Se hooks por DISC nao existirem, usa biblioteca neutra.

## Criterios de aceitacao mensuraveis
1. Sempre retorna 3 copys com tons unicos.
2. Cada copy contem CTA explicito (interrogacao ou convite de acao).
3. Cada copy fica no intervalo pratico de tamanho (aprox. 60-120 palavras; tolerancia ate 130 por validacao defensiva).
4. Sempre retorna 3 a 5 hooks com prioridade crescente.
5. next_best_action nunca vazio.
6. Pipeline nao quebra com nulos em campos comportamentais.
7. UI exibe DISC, confianca, racional, copys, hooks e proxima acao.

## Edge cases
- Campos nulos: stage, value, engage_date, industry, channel.
- Perfil indefinido por baixa evidencia.
- Texto longo em KPI e blocos de copy.
- Duplicidade de widgets Streamlit (corrigido com renderizacao unica).

## Plano de testes

### Unit
- test_disc_profile.py
- test_followup_engine.py
- test_sales_hooks.py

Cobertura minima validada:
- DISC definido e fallback indefinido
- 3 tons unicos
- CTA nas 3 copys
- 3-5 hooks validos
- next_best_action nao vazio

### Integracao
- App renderiza Assistente de Follow-up sem erro de widget duplicado.
- Dados reais do dataset alimentam o perfil e as copys.

### Smoke UI
- Selecao de lead no assistente.
- Cards de perfil, copys e hooks visiveis.
- Botoes Copiar/Selecionar texto renderizados por copy.
