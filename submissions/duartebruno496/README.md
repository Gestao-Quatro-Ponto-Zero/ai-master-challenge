# Submissão — Bruno Duarte — Challenge 003 (Lead Scorer)

## Sobre mim
- **Nome:** Bruno Ferreira Duarte
- **LinkedIn:** https://www.linkedin.com/in/bruno-duarte-338830191/
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

## Executive Summary
O **RavenStack CRM** é uma solução funcional desenvolvida para transformar a priorização de vendas de um modelo baseado em "feeling" para uma cultura de dados assistida por IA. O Hub centraliza ~8.800 oportunidades e utiliza um motor de scoring heurístico para explicar ao vendedor, de forma narrativa, qual a melhor próxima ação. A principal entrega é a redução do ruído operacional, permitindo que o time foque nos leads com maior probabilidade de conversão (Status: Quente).

## Solução
A aplicação foi construída em Streamlit e dividida em três pilares estratégicos:
1. **Central de Ações:** Dashboard tático para o vendedor com filtros em cascata (Waterfall) e Score Narrativo.
2. **Insights Executivos:** Visão macro de faturamento focada na hierarquia Produto > Setor e Top 3 campeões de receita.
3. **Auditoria de Dados:** O "Solo Sagrado" da aplicação, que identifica falhas de integridade e traduz o impacto técnico em prejuízo financeiro real para a empresa.

## Abordagem
- **Limpeza e Governança:** Tratamento de nulos (convertidos para 'N/A') e normalização de nomes (ex: Tecnologia e Marketing).
- **Motor de Scoring:** Lógica ponderada que considera a fase do deal, o porte do cliente (SMB/Mid/Enterprise) e o "aging" (tempo parado), aplicando um fator de decaimento de 30% em leads sem interação há mais de 45 dias.
- **Eficiência de Interface:** Implementação de paginação para suportar o volume de dados sem perda de performance na UX.

## Resultados / Findings
- Identificamos que leads com score > 80 (🔥 Quente) representam o faturamento imediato, enquanto leads com score < 45 demandam revisão estratégica ou descarte.
- A auditoria revelou que a falta de informação de faturamento impede a segmentação correta do porte da conta em registros críticos.

## Limitações
- O sistema é baseado em base histórica estática (CSV); uma versão produtiva exigiria integração via API com CRMs (Salesforce/HubSpot).
- O scoring atual é baseado em regras de negócio (Heurísticas); o próximo estágio seria um modelo preditivo de propensão de fechamento (Propensity Score).

## Process Log — Como usei IA
Trabalhei com o Gemini 3 Flash como um arquiteto parceiro para acelerar o desenvolvimento.

### Ferramentas usadas
- **Gemini 3 Flash:** Engenharia de prompt para lógica de filtros cruzados e debug de tipagem.
- **Streamlit/Plotly:** Visualização e interface.

### Workflow
1. **Decomposição:** Separei o problema em motor de cálculo vs. interface visual.
2. **Vibe Coding:** Usei IA para gerar protótipos rápidos de gráficos e refiná-los iterativamente.
3. **Debug Orientado:** Resolvi erros complexos de comparação de tipos (float vs str) através de diagnósticos compartilhados com a IA.

### O que eu adicionei que a IA sozinha não faria
- **Inteligência Narrativa:** A IA forneceria apenas números. Eu exigi que ela gerasse a "Inteligência da Nota" em linguagem humana para gerar confiança no vendedor.
- **Laudo de Impacto:** O dashboard de auditoria foi um insight humano de que dados sujos custam dinheiro, indo além do pedido original de "apenas um gráfico".