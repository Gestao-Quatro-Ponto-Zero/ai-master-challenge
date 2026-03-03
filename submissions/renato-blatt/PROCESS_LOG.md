# Process Log — Lead Scorer

## Ferramentas usadas
- **SAGE (Claude Sonnet)**: parceiro estratégico para decomposição do problema, definição da lógica de scoring e construção do código
- **OpenAI gpt-4o-mini**: agente embutido na aplicação para briefings e chat

## Como o problema foi decomposto

Antes de escrever qualquer linha de código, a pergunta central foi: o que um vendedor realmente precisa ver numa segunda-feira de manhã?

Não é um número. É uma resposta para "onde eu coloco minha energia hoje e por quê."

Isso definiu a arquitetura: briefing personalizado + pipeline priorizado + agente para aprofundar qualquer deal.

## Decisões de scoring que a IA sozinha não tomaria

A lógica de scoring padrão que qualquer modelo de IA produz ordena deals por valor. Essa solução inverte a prioridade:

**Peso maior para winrate do vendedor (35%) e match produto-setor (30%)** — baseado em julgamento comercial real: vendedor errado mata o deal independente do valor, e produto certo para o setor é o sinal mais forte de fechamento.

Essa decisão veio de experiência em vendas, não de um modelo.

## Onde a IA errou e como foi corrigido

**Problema 1 — Datas absurdas**: o primeiro código calculou days_in_stage usando datetime.now() como referência, resultando em 3.000+ dias para todos os deals. O dataset é de 2017/2018. Correção: usar a data máxima do próprio dataset como referência.

**Problema 2 — Close value zerado**: deals abertos não têm close_value preenchido. A IA não percebeu isso. Correção: usar sales_price do produto como valor estimado quando close_value é zero.

**Problema 3 — Chaves de merge erradas**: o código gerado assumiu colunas account_id, product_id, sales_agent_id. O dataset real usa account, product, sales_agent. Correção via inspeção das colunas reais.

## Iterações

1. Definição do problema e arquitetura — antes do código
2. Decisão de scoring com base em julgamento comercial
3. Build do código em 3 partes estruturadas
4. Correção das datas (3 iterações)
5. Correção dos valores zerados
6. Correção das chaves de merge
7. Validação visual do briefing e do chat com dados reais

## O que foi adicionado além do que a IA produziria sozinha

- Lógica de scoring baseada em julgamento comercial real (não só valor)
- Briefing em linguagem natural personalizado por vendedor — não um número sem contexto
- Agente de chat que responde perguntas sobre deals específicos com dados reais
- Explicação em português do motivo de cada score
- Visão do manager com receita esperada ponderada por probabilidade
