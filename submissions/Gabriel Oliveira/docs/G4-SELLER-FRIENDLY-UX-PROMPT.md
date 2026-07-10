# G4 — Super Prompts Seller-Friendly UX (for dummies)

Pacote de prompts para transformar o Lead Scorer em uma ferramenta de uso
imediato para vendedor, com interface simples, visual forte e filtros úteis.

Objetivo: reduzir fricção de uso para 30 segundos de entendimento prático.

---

## Resultado esperado desta frente

1. Dashboard de acompanhamento diário/semanal fácil de ler
2. Visualização de leads mais clara (prioridade, ação e contexto)
3. Filtros melhores (rápidos, salvos, combináveis, explicáveis)
4. Linguagem anti-jargão (texto comercial direto)
5. Fluxo "o que fazer agora" para vendedor

---

## P01 — Spec UX simplificada para vendedor

```text
[AGENT: ARCHITECT] [SKILL: SPEC-DRIVEN]

Contexto:
- Produto: Lead Scorer (Challenge 003)
- Público principal: vendedor de campo (não técnico, sem paciência para telas complexas)
- Objetivo da tela: responder em 10 segundos "em qual lead eu devo agir agora e como"

Crie uma SPEC de UX "Seller-Friendly" com foco em simplicidade operacional.

Escopo obrigatório:
1) Dashboard de acompanhamento (visão rápida)
2) Lista de leads "for dummies" (foco em decisão, não em dado bruto)
3) Sistema de filtros melhorado (rápido + salvo + reset)
4) Linguagem em PT-BR comercial sem jargão
5) Fluxo guiado: Próxima ação recomendada

Entregue:
- Problema de UX atual e impacto no vendedor
- Arquitetura de informação da tela (ordem dos blocos)
- Critérios de aceitação mensuráveis
- Edge cases (sem dados, muitos leads, filtros sem resultado)
- Plano de validação com usuário (smoke test de 5 minutos)

Sem código neste passo.
```

---

## P02 — Dashboard de acompanhamento (executivo + vendedor)

```text
[AGENT: BUILDER] [SKILL: DESIGN-SYSTEM-G4]

Implemente no app Streamlit um "Painel de Acompanhamento" de leitura imediata.
Arquivo: submissions/gabriel/solution/app.py

Blocos obrigatórios:
1) Faixa "Hoje":
   - leads quentes
   - leads em risco
   - follow-ups pendentes
   - valor potencial do dia
2) Faixa "Semana":
   - taxa de avanço de estágio
   - score médio por carteira
   - top 5 oportunidades
3) Bloco "Atenção agora":
   - lista curta (3-7 itens) com alerta acionável

Regras de UX:
- Cada KPI deve responder "o que isso muda na minha ação"
- Sempre mostrar contexto textual curto abaixo dos números
- Cores com significado simples (bom/atenção/crítico) sem poluição visual
- Se não houver dado, mostrar estado vazio com instrução clara

Regras de visual:
- Seguir tokens do design system G4
- Gráficos simples e legíveis (sem overplot)
- Títulos em linguagem comercial, não analítica

Entregue patch pronto.
```

---

## P03 — Lead list "for dummies" (mais visível)

```text
[AGENT: BUILDER] [SKILL: DESIGN-SYSTEM-G4]

Reestruture a visualização de leads para tomada de decisão rápida.
Arquivo: submissions/gabriel/solution/app.py

Modelo de card por lead (obrigatório):
- Nome da conta + estágio atual
- Score em destaque (0-100) com cor por faixa
- "Motivo do score" em 1 frase
- "Próxima ação" em 1 frase (imperativa)
- "Prazo sugerido" (ex: hoje, 24h, esta semana)
- Botões rápidos:
  - "Ver detalhes"
  - "Gerar follow-up"

Modo de visualização:
- Alternar entre:
  1) cards (default vendedor)
  2) tabela (modo analítico)

Regras:
- Cards devem priorizar leitura vertical e ação
- Não mostrar campos irrelevantes no primeiro nível
- Texto anti-jargão (sem termos técnicos de dados)
- Tratar nomes longos, valores ausentes e overflow

Entregue com comportamento responsivo básico.
```

---

## P04 — Filtros melhores (rápidos e inteligentes)

```text
[AGENT: BUILDER] [SKILL: SPEC-DRIVEN]

Implemente uma camada de filtros melhores para vendedor.
Arquivo: submissions/gabriel/solution/app.py

Filtros obrigatórios:
1) Dono da carteira (vendedor)
2) Manager
3) Região
4) Estágio
5) Faixa de score
6) Situação de follow-up (pendente, enviado, atrasado)

Comportamentos obrigatórios:
- Busca por texto (nome da conta / oportunidade)
- Chips de filtros ativos visíveis
- Botão "Limpar tudo"
- Presets rápidos (ex: "Quentes hoje", "Risco alto", "Sem contato 7 dias")
- Exibir quantidade de resultados em tempo real
- Mensagem clara quando filtro zera resultados

UX:
- Ordem dos filtros por frequência de uso
- Labels claros para leigo
- Não exigir mais de 2 cliques para filtros comuns

Entregue patch pronto + breve explicação de trade-offs.
```

---

## P05 — Copywriting da interface (anti técnico)

```text
[AGENT: BUILDER]

Reescreva os textos da interface para linguagem de vendedor.
Arquivo: submissions/gabriel/solution/app.py (e módulos de texto, se existirem)

Diretrizes:
- Trocar jargão técnico por linguagem comercial simples
- Sempre responder "o que fazer agora"
- Títulos curtos e orientados a ação
- Microcopy útil em botões/empty states/tooltips

Exemplos de transformação:
- "Distribuição de score" -> "Como está sua carteira agora"
- "Pipeline velocity" -> "Velocidade das oportunidades"
- "Outliers" -> "Casos fora do padrão"

Entregue:
- Lista antes/depois dos principais textos
- Patch com os novos textos aplicados
```

---

## P06 — Prompt de revisão de usabilidade para vendedor

```text
[AGENT: REVOPS-EXPERT]

Você é um vendedor abrindo o Lead Scorer na segunda-feira às 9h.
Faça uma revisão brutal de usabilidade desta interface.

Avalie:
1) Em 10 segundos fica claro onde agir?
2) A lista de leads está prática ou ainda técnica?
3) Os filtros ajudam de verdade ou só ocupam espaço?
4) O dashboard orienta decisão ou só informa?
5) O que te faria abandonar essa tela?

Formato da resposta:
- Pontos fortes (máx. 5)
- Fricções críticas (priorizadas)
- Melhorias de alto impacto (top 5)
- Quick wins implementáveis em 1-2 horas

Não seja gentil. Seja útil.
```

---

## P07 — Prompt turbo (implementação única)

```text
[AGENT: BUILDER] [SKILL: DESIGN-SYSTEM-G4]

Transforme o Lead Scorer em versão "seller-friendly for dummies" sem perder a lógica de score.

Entregáveis obrigatórios no app:
1) Dashboard de acompanhamento (Hoje + Semana + Atenção agora)
2) Lead list visual por cards (default) com próxima ação clara
3) Filtros melhorados com presets, chips ativos e limpar tudo
4) Busca textual e contagem de resultados
5) Copy da interface em PT-BR comercial sem jargão
6) Estados vazios úteis e mensagens claras
7) Manter opção de tabela para usuários avançados

Restrições:
- Sem inventar colunas
- Sem paths absolutos
- Sem visual fora dos tokens G4
- UX com foco em vendedor, não analista

Campos disponíveis do dataset:
{COLE AQUI AS COLUNAS REAIS}

Saída esperada:
- Patch completo no app
- Changelog objetivo
- Checklist de aceite preenchido
```

---

## Checklist de aceite (Seller-Friendly)

- Usuário entende em até 10s onde agir
- Topo da tela traz prioridades do dia
- Cada lead mostra "próxima ação" sem abrir detalhe técnico
- Filtros comuns exigem no máximo 2 cliques
- Presets aceleram uso real (hoje/risco/sem contato)
- Mensagens estão em PT-BR comercial simples
- Empty states orientam próximo passo
- Sem quebra visual em tela pequena
