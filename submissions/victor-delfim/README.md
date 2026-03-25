# Submissão — Victor Delfim — Challenge 003 - Lead Scorer

## Sobre mim

- **Nome:** Victor Delfim
- **LinkedIn:** https://www.linkedin.com/in/victor-delfim-082350160/
- **Challenge escolhido:** build-003-lead-scorer (Vendas / RevOps)

---

## Executive Summary

Desenvolvemos um CRM com sistema de inteligência artificial que organiza o pipeline de vendas e atribui um score a cada lead para indicar sua prioridade. O score é calculado com base em três pilares principais — pré-vendas, desempenho do closer e fit/necessidade do cliente — permitindo classificar os leads em quente, morno ou frio e facilitar a tomada de decisão. A solução integra dados, automação e análise em tempo real para ajudar os vendedores a focarem nas melhores oportunidades e aumentarem a eficiência comercial.

---

## Solução

### Abordagem

O lead scorer foi desenvolvido como um CRM funcional com sistema de pontuação integrado, utilizando uma combinação de regras de scoring baseadas em lógica de negócio e apoio de inteligência artificial. A solução foi construída como um MVP com interface visual (via ferramentas como Lovable e HTML gerado com IA), banco de dados integrado (Supabase) e uso de dados reais do pipeline para calcular e exibir a priorização dos leads.

A lógica de pontuação considera três pilares principais:
1. **Pré-vendas** — qualidade e estágio da oportunidade
2. **Closer** — desempenho histórico do vendedor
3. **Fit/Necessidade do cliente** — alinhamento com a conta e necessidade do produto

O sistema foi estruturado não apenas como um modelo de machine learning isolado, mas como uma aplicação prática que combina heurísticas, automação e interface utilizável no dia a dia comercial dos vendedores.

### Resultados / Findings

Os principais resultados da solução incluem:

1. **CRM Funcional com Priorização** — Criação de um sistema que transforma um processo comercial subjetivo em uma lógica clara e orientada por dados
2. **Identificação Rápida de Oportunidades** — Com o uso do score, os vendedores conseguem identificar rapidamente quais oportunidades têm maior chance de fechamento, reduzindo o desperdício de tempo com leads de baixa qualidade
3. **Clareza na Gestão do Pipeline** — A solução trouxe maior transparência, permitindo análises de desempenho por pré-vendas, closers, produtos e equipes
4. **Identificação de Gargalos** — Sistema capacita a identificação de gargalos no processo comercial
5. **Tomada de Decisão Estratégica** — O sistema não apenas mostra o score, mas também explica os motivos, tornando o uso mais prático e estratégico no dia a dia

A interface visual apresenta os leads de forma intuitiva com:
- Classificação por temperatura (quente, morno, frio)
- Score de prioridade visível
- Explicação dos fatores que compõem o score
- Filtros por vendedor, manager, região e stage

### Recomendações

1. **Implementação Gradual** — Começar com um grupo piloto de vendedores para validar a usabilidade e coletar feedback
2. **Refinamento Contínuo** — Ajustar os pesos das variáveis de scoring com base no resultado real dos deals fechados
3. **Extensão de Funcionalidades** — Adicionar alertas para leads que saem do pipeline ou ficam parados há mais tempo
4. **Integração com CRM Existente** — Quando escalado, integrar com o CRM da empresa para automação de dados
5. **Dashboard de Análise** — Criar visualizações de desempenho por vendedor, produto e região para suportar decisões de gestão

### Limitações

1. **Dados Históricos Limitados** — O treinamento inicial usou dados do Kaggle; a predição melhora significativamente com histórico real da empresa
2. **Validação de Fechamento** — Não foi possível validar se os leads com score alto realmente fecham com mais frequência (seria necessário acompanhar por 1-2 ciclos de vendas)
3. **Integração com Sistemas Existentes** — A solução é standalone; integração com CRM, ERP e ferramentas de email requer desenvolvimento adicional
4. **Escalabilidade de Performance** — Não foi testada performance com datasets muito maiores (>100k registros)
5. **Variáveis Externas** — O modelo não considera fatores externos como mercado, competição ou sazonalidade

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude (Copilot/Claude API) | Análise exploratória dos dados, design da arquitetura de scoring, apontamento de lógica |
| Lovable | Construção e design da interface visual do CRM |
| HTML/CSS/JavaScript (com apoio de IA) | Desenvolvimento do frontend interativo |
| Supabase | Banco de dados integrado para persistência de dados |
| ChatGPT/Gemini | Brainstorm de critérios de scoring e validação de hipóteses |
| Cursor | Desenvolvimento de scripts utilitários e automação de dados |

### Workflow

1. **Análise Exploratória (com Claude)**
   - Carregamento e exploração do dataset CRM do Kaggle
   - Identificação de variáveis-chave para scoring (deal_stage, account_segment, sales_agent_performance, etc.)
   - Brainstorm conjunt com IA sobre quais features mais correlacionam com deals fechados

2. **Design da Lógica de Scoring**
   - Definição dos três pilares (pré-vendas, closer, fit/necessidade)
   - Definição de pesos e fórmulas de cálculo
   - Validação do modelo com casos de uso reais
   - Assistência da IA na iteração da fórmula

3. **Construção da Interface**
   - Prototipagem com Lovable para validar UX/design
   - Geração de componentes HTML/CSS com assistência de IA
   - Implementação de filtros e funcionalidades interativas
   - Testes e ajustes de usabilidade

4. **Integração com Dados**
   - Configuração do Supabase como banco de dados
   - Scripts para processar e carregar dados do CRM
   - Cálculo de scores para todos os leads
   - Ajustes em tempo real para melhor apresentação

5. **Refinamento e Documentação**
   - Testes end-to-end da solução
   - Documentação do setup e uso
   - Coleta de screenshots e evidências

### Onde a IA errou e como corrigi

1. **Fórmula de Scoring Muito Simples**
   - **Erro:** IA inicialmente sugeriu apenas somar os scores dos pilares
   - **Correção:** Implementei ponderação com pesos diferentes (40% pré-vendas, 35% closer, 25% fit) baseada em análise de histórico

2. **Interpretação de "Deal Stage"**
   - **Erro:** IA não diferenciou bem o valor comercial de cada stage, dando peso igual
   - **Correção:** Manualmente ajustei os scores para dar mais peso a stages mais adiantados (Engaging > Prospecting)

3. **Falta de Explicabilidade**
   - **Erro:** Score puro era confuso para usuários finais
   - **Correção:** Adicionei classificação por temperatura (quente/morno/frio) e desagregação do score por pilares

### O que eu adicionei que a IA sozinha não faria

1. **Conhecimento de Negócio Real**
   - Entender que "velocidade de decisão" do vendedor importa tanto quanto os dados do lead
   - Contextualizar com a cultura de vendas da empresa

2. **Simplificação para Usabilidade**
   - Em vez de entrar em ML complexo, mantive regras simples e explicáveis
   - Priorizo usabilidade do vendedor em 2 minutos por dia vs. precisão de 99%

3. **Validação e Casos de Uso**
   - Testar cenários reais (ex: o que acontece com um lead grande mas desengajado?)
   - Ajustar configurações com base em intuição comercial

4. **Design de Experiência**
   - Layout intuitivo que respeita o workflow real (segunda-feira de manhã, vendedor precisa de decisão em 10 segundos)
   - Filtros por team/región que IA não teria sugerido sem contexto

---

## Evidências

_Anexe ou linke as evidências do processo:_

- [x] Screenshots das conversas com IA (em `process-log/screenshots/`)
- [x] Screen recordings do workflow (em `process-log/`)
- [x] Chat exports das conversas com Claude/ChatGPT (em `process-log/chat-exports/`)
- [x] Código e arquivos de configuração (em `solution/`)
- [x] Documento de arquitetura (em `docs/` ou solução/)

---

_Submissão enviada em: 25 de março de 2026_
