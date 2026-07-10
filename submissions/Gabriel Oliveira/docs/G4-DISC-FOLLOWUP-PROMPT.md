# G4 — Super Prompts para DISC + Follow-up + Ganchos de Venda

Pacote de prompts para implementar, no Lead Scorer, as funcionalidades:
1. Perfil DISC por lead
2. 3 opções de copy de follow-up em 3 tons diferentes
3. Botão de copiar e colar por copy
4. Sugestões de ganchos para avançar para venda

Use estes prompts em sequência (P01 a P07). Eles já seguem o contexto do
Challenge 003 e respeitam o Design System G4.

---

## P01 — Spec da feature completa (DISC + Copy + Ganchos)

```text
[AGENT: ARCHITECT] [SKILL: SPEC-DRIVEN]

Contexto:
- Produto: Lead Scorer (Challenge 003)
- Stack: Python + Streamlit + pandas + plotly
- Público: vendedores e managers (não técnicos)
- Objetivo: priorizar deals e acelerar follow-up

Crie a SPEC técnica da feature "Perfil DISC + Assistente de Follow-up".

Escopo obrigatório:
1) Perfil DISC por lead (D, I, S, C)
2) 3 copies de follow-up por lead em tons diferentes:
   - consultivo
   - direto
   - provocativo elegante
3) Botão "Copiar" em cada copy (com fallback se clipboard não disponível)
4) Bloco "Ganchos de Venda" com 3 a 5 sugestões acionáveis por lead
5) Tudo em PT-BR, sem jargão desnecessário

Requisitos da SPEC:
- Objetivo de negócio (1 frase)
- Entradas/saídas por função
- Contrato de dados (campos obrigatórios do perfil do lead)
- Regras de fallback para dados faltantes
- Critérios de aceitação mensuráveis
- Edge cases (campos vazios, texto longo, perfil indefinido)
- Plano de testes (unit + integração + smoke UI)

Não escreva código ainda. Entregue só a SPEC em markdown.
```

---

## P02 — Estrutura do perfil do lead e inferência DISC

```text
[AGENT: ARCHITECT] [SKILL: EXPLAINABILITY-FIRST]

Desenhe a estrutura de dados do perfil do lead e a regra de inferência DISC.

Entrada disponível por lead (base):
{COLE AQUI AS COLUNAS REAIS DO DATASET}

Regras:
- Não inventar coluna além das fornecidas
- Se faltar dado para inferência DISC, retornar "DISC indefinido" + motivo
- Perfil DISC deve ser explicável em linguagem de vendedor
- Retornar também "confianca_disc" de 0 a 100 e "racional_disc" em 2-3 linhas

Quero a saída neste formato:
1) Schema do objeto LeadProfile (json exemplo)
2) Tabela de regras de inferência por perfil D/I/S/C
3) Função conceitual infer_disc_profile(...) com inputs/outputs
4) Fallbacks para missing data
5) Checklist de validação para garantir consistência

Sem código executável. Foque em lógica clara e auditável.
```

---

## P03 — Engine de copy com 3 tons por lead

```text
[AGENT: BUILDER]

Implemente um módulo de geração de follow-up baseado em LeadProfile + DISC.
Arquivo: submissions/gabriel/solution/followup_engine.py

Objetivo:
- Gerar 3 mensagens de follow-up por lead, cada uma com tom diferente:
  1) consultivo
  2) direto
  3) provocativo elegante

Contrato de saída por lead:
{
  "lead_id": "...",
  "disc_profile": "D|I|S|C|indefinido",
  "copies": [
    {"tone": "consultivo", "text": "...", "subject": "..."},
    {"tone": "direto", "text": "...", "subject": "..."},
    {"tone": "provocativo elegante", "text": "...", "subject": "..."}
  ],
  "sales_hooks": ["...", "...", "..."],
  "next_best_action": "..."
}

Regras de qualidade das copies:
- PT-BR natural, curto, acionável
- 60 a 120 palavras por copy
- Sem promessas absolutas
- Sempre incluir CTA explícito
- Referenciar sinais do lead (quando houver)
- Se dado crítico faltar, usar template fallback elegante

Regras de ganchos de venda:
- 3 a 5 ganchos específicos do perfil DISC
- Cada gancho deve ter:
  - "gancho"
  - "por_que_funciona"
  - "pergunta_de_abertura"

Técnico:
- Type hints + docstrings
- Sem hardcode de path absoluto
- Sem usar serviços externos
- Cobrir edge cases de campos nulos

Entregue código pronto para import no app.
```

---

## P04 — UI Streamlit: card de perfil, 3 copies e botões copiar

```text
[AGENT: BUILDER] [SKILL: DESIGN-SYSTEM-G4]

Implemente a seção "Assistente de Follow-up" no app Streamlit.
Arquivo: submissions/gabriel/solution/app.py

UI obrigatória por lead selecionado:
1) Card "Perfil do Lead" com:
   - DISC
   - confiança DISC
   - racional resumido
2) Card "3 opções de Follow-up" com 3 blocos (consultivo, direto, provocativo elegante)
3) Cada bloco com:
   - assunto
   - texto
   - botão "Copiar"
   - feedback visual "Copiado" após clique
4) Card "Ganchos para avançar a venda" com lista priorizada
5) Bloco "Próxima melhor ação" em destaque

Clipboard:
- Tentar copy real via JS (navigator.clipboard)
- Se clipboard não permitido, fallback:
  - selecionar texto automaticamente (ou instrução clara)
  - botão alternativo "Selecionar texto"

UX:
- Não poluir tela
- Bom uso para vendedor em 30 segundos
- Texto sempre em PT-BR

Design system G4:
- Seguir integralmente tokens e restrições do super prompt de design
- Definir hover, focus-visible e disabled para botões
- Sem valores visuais fora da escala/tokens

Entregue patch completo do app, sem placeholders.
```

---

## P05 — Ganchos de venda por DISC (biblioteca reutilizável)

```text
[AGENT: BUILDER] [SKILL: SPEC-DRIVEN]

Crie uma biblioteca de "ganchos de venda" reutilizável.
Arquivo: submissions/gabriel/solution/sales_hooks.py

Função principal:
get_sales_hooks(lead_profile: dict) -> list[dict]

Saída de cada item:
{
  "priority": 1,
  "hook": "...",
  "why_it_works": "...",
  "opening_question": "...",
  "risk_if_badly_used": "..."
}

Regras:
- 3 a 5 hooks por lead
- Ordenar por prioridade
- Ajustar conteúdo por DISC
- Se DISC indefinido, usar estratégia neutra baseada em contexto do deal
- Linguagem comercial prática (não acadêmica)

Inclua também:
- get_next_best_action(lead_profile, hooks) -> str
- Docstrings explicando lógica
- Type hints
```

---

## P06 — Testes (unit + integração)

```text
[AGENT: TDD-GUIDE]

Escreva testes para DISC + follow-up engine + sales hooks.

Arquivos sugeridos:
- submissions/gabriel/tests/test_disc_profile.py
- submissions/gabriel/tests/test_followup_engine.py
- submissions/gabriel/tests/test_sales_hooks.py

Cobertura mínima dos cenários:
1) Perfil D, I, S, C retornam copies adequadas
2) DISC indefinido cai em fallback elegante
3) Sempre retorna 3 copies com tons únicos
4) Sempre retorna CTA nas 3 copies
5) Sempre retorna 3-5 hooks válidos
6) next_best_action nunca vazio
7) Campos nulos não quebram o pipeline

Formato AAA (Arrange, Act, Assert). Sem mocks desnecessários.
```

---

## P07 — Review rigoroso de qualidade comercial e técnica

```text
[AGENT: REVIEWER] [SKILL: SEC-SCAN]

Revise os arquivos alterados da feature DISC + Follow-up.

Procure explicitamente:
- Invenção de colunas inexistentes
- Hardcode de paths
- Falta de fallback para nulos
- Copy genérica sem personalização por perfil
- Ausência de CTA
- Ganchos de venda vagos ou não acionáveis
- Falta de botão copiar funcional (ou fallback)
- Falha de acessibilidade de foco/contraste

Resposta obrigatória:
- Linha/arquivo
- Problema
- Impacto no vendedor
- Correção sugerida

Não usar "looks good".
```

---

## Prompt único (versão turbo)

Use quando quiser fazer tudo em um único ciclo.

```text
[AGENT: BUILDER] [SKILL: DESIGN-SYSTEM-G4] [SKILL: EXPLAINABILITY-FIRST]

Implemente no Lead Scorer a feature completa "Perfil DISC + Assistente de Follow-up".

Entregáveis obrigatórios:
1) Inferência DISC explicável por lead (com confiança + racional)
2) 3 copies por lead com tons: consultivo, direto, provocativo elegante
3) Botão copiar por copy com feedback visual e fallback sem clipboard
4) 3-5 ganchos de venda acionáveis por lead + próxima melhor ação
5) UI em Streamlit aderente ao Design System G4
6) Tratamento de edge cases (nulos, overflow, perfil indefinido)
7) Testes unitários e integração para contratos principais

Restrições:
- Não inventar colunas
- PT-BR comercial
- Sem path absoluto
- Sem dependência externa online
- Sem valores visuais fora dos tokens G4

Campos do lead disponíveis:
{COLE AQUI AS COLUNAS REAIS}

Saída esperada:
- Patch completo nos arquivos de solution e tests
- Breve changelog técnico
- Checklist final validando critérios de aceite
```

---

## Estrutura mínima recomendada de LeadProfile

Use este bloco para orientar o agente quando necessário.

```json
{
  "lead_id": "opportunity_id",
  "lead_name": "account",
  "segment": "account_size",
  "deal_stage": "stage",
  "days_in_stage": 0,
  "close_value": 0,
  "owner": "sales_agent",
  "manager": "manager",
  "region": "regional_office",
  "disc_profile": "D",
  "disc_confidence": 82,
  "disc_rationale": "Lead orientado a resultado e velocidade.",
  "pain_points": ["..."],
  "objections": ["..."],
  "buying_signals": ["..."],
  "next_best_action": "..."
}
```

Se algum campo não existir no dataset real, substitua por `null` e documente fallback.
