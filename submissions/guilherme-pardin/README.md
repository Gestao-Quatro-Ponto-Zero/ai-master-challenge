# Submissão — Guilherme Pardin — Challenge 003

## Sobre mim

- **Nome:** Guilherme Pardin
- **LinkedIn:** https://www.linkedin.com/in/guipardindev/
- **Challenge escolhido:** Build-003 — Lead Scorer

## Executive Summary

Construí um CRM funcional de priorização de pipeline que resolve o problema central: vendedores gastam tempo em negociações que não vão fechar e deixam oportunidades boas esfriar. O sistema calcula um score de 0-100 para cada um dos 2.089 deals abertos usando 6 dimensões baseadas em dados históricos de 6.711 deals fechados, classifica automaticamente em 4 níveis de prioridade, e redistribui negociações para o vendedor com melhor taxa de conversão histórica no setor. A principal recomendação é organizar o time por especialização setorial — a variação de conversão vendedor+setor chega a 54 pontos percentuais, tornando essa a maior alavanca de desempenho disponível.

## Solução

### Abordagem

Comecei entendendo onde eu poderia contribuir melhor. Tenho experiência prática com soluções para a área comercial — opero dois CRMs em produção (Nutriceler e Grupo Tala) para clientes B2B no agronegócio. Escolhi o Challenge 003 porque é o que mais se conecta com o que eu já faço no dia a dia: construir ferramentas que ajudam vendedores a priorizar e fechar.

Antes de escrever qualquer código, fiz três coisas: diagnostiquei por que minha primeira submissão não passou (Streamlit com tabela de scores — mostrava dados em vez de ajudar a decidir), trouxe referência dos meus CRMs em produção como base de UX, e explorei os dados profundamente antes de definir o modelo de scoring.

A descoberta-chave veio da análise cruzada dos 4 CSVs: a combinação vendedor+setor tem variação de até 54 pontos percentuais em taxa de conversão. Um vendedor que converte 90% em entretenimento converte 35% em tecnologia. São praticamente dois vendedores diferentes. Isso definiu a tese central: organizar o time por especialização setorial é a maior alavanca de desempenho disponível.

### Resultados / Findings

**Demo ao vivo:** [TODO: URL da Vercel]

**Pipeline Kanban com etapas reais** — Prospecção (500), Em Negociação (1.589), Vendas Fechadas (4.238), Perdidas (2.473). Deals ordenados por pontuação dentro de cada coluna, com badge de prioridade e produto de interesse.

**Priorização** — Seções agrupadas por tipo de ação: "Fechar agora" (negociações quentes, cadência diária), "Remanejamentos sugeridos" (643 negociações com vendedor desalinhado ao setor), "Nutrir com cadência" (mornas, follow-up a cada 2-3 dias), "Reengajar ou descartar" (frias/em risco).

**Classificação automática por vendedor ótimo** — O sistema não sugere realocação, ele já classifica. Para cada negociação, calcula a taxa de conversão de todos os vendedores ativos no setor e identifica quem tem melhor fit.

**Dashboard gerencial em 3 camadas** — Foco agora (quem precisa de atenção), recomendações (3 ações claras), dados de suporte (colapsáveis). Cada nível da hierarquia vê as pessoas do nível abaixo que precisam de atenção.

**Hierarquia de 3 níveis** — Gestor (Head de RevOps) vê todos os gerentes e toda a operação, Gerente vê só os vendedores do seu time, Vendedor vê só seus próprios dados. Isolamento completo por perfil.

**Mapa de especialização do time** — Cada vendedor com seus setores de força, taxa de conversão por setor, e quantas negociações precisam ser redirecionadas.

**Modelo de scoring (6 dimensões, 0-100 pts):**

| Dimensão | Peso | Lógica |
|----------|------|--------|
| Estágio da negociação | 0-25 | Em negociação = 25, Prospecção = 10 |
| Afinidade vendedor+contexto | 0-25 | Conversão vendedor×setor → vendedor×produto → vendedor |
| Valor da negociação | 0-20 | Proporcional ao teto do produto |
| Conversão do produto | 0-15 | Taxa histórica por linha de produto |
| Qualidade da empresa | 0-10 | Revenue + employees + conta conhecida |
| Sazonalidade | 0-5 | Taxa de conversão por mês |

### Recomendações

1. **Organizar o time por especialização setorial.** O fit vendedor+setor é o preditor mais forte de conversão (54pp de variação). Vendedores que performam bem em software devem focar exclusivamente em software.
2. **Redistribuir as 643 negociações desalinhadas.** 31% do pipeline converte melhor com outro vendedor. Nos casos mais críticos, o ganho potencial é de +45 pontos percentuais.
3. **Implementar cadência diferenciada.** Quentes: contato diário, abordagem agressiva. Mornos: follow-up a cada 2-3 dias. Frios: email semanal ou descartar.
4. **Usar análise de perdas como input para CS/pós-venda.** Padrões de perda por setor e produto geram demandas diretas.
5. **Evoluir para análise de conversas com IA.** Com WhatsApp API, capturar produto de interesse e objeções automaticamente.

### Limitações

- **Login simulado.** A autenticação é seleção de perfil para demonstração. Em produção, seria Supabase Auth com RLS por hierarquia — como já opero nos CRMs Nutriceler e Grupo Tala.
- **Scoring é algorítmico, não IA.** Modelo baseado em regras e taxas de conversão históricas. Chamá-lo de "IA" seria desonesto. Em produção, com mais dados, poderia evoluir para modelo preditivo.
- Dataset de 2016-2017: sazonalidade baseada em padrões desse período
- 68% dos deals abertos não têm conta identificada no CSV
- Sem dados de atividade recente (emails, ligações)
- Classificação por vendedor ótimo assume capacidade disponível — em produção precisaria de balanceamento

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (Opus 4.6, claude.ai) | Análise dos 4 datasets cruzados, cálculo de win rates, definição do modelo de scoring, arquitetura do CRM, redação da documentação |
| Claude Code (Opus 4.7) | Construção do app Next.js completo a partir do prompt estruturado (CLAUDE.md) |

### Workflow

1. **Análise dos 4 challenges** — Avaliei qual encaixava melhor no meu perfil de product builder. Escolhi o 003 por experiência direta com CRM em produção.
2. **Diagnóstico da submissão anterior** — Claude analisou meu código anterior e diagnosticou problemas: Streamlit parecia protótipo, features exigiam API key do avaliador, interface mostrava dados em vez de ajudar a decidir.
3. **Exploração dos dados** — Claude analisou os 4 CSVs cruzados. Descoberta-chave: variação de 54pp no win rate vendedor×setor.
4. **Referência de produto real** — Compartilhei screenshots e código dos CRMs Nutriceler e Grupo Tala para usar padrões de UX validados.
5. **Design do scoring** — Iteramos os pesos das 6 dimensões. Fit do vendedor subiu de 10 para 25 pts, sazonalidade caiu de 20 para 5 pts.
6. **Prompt estruturado** — Compilei tudo num CLAUDE.md de ~300 linhas como input para o Claude Code.
7. **Construção** — Claude Code construiu o app Next.js. Iterei com prompts de ajuste: hierarquia de perfis, tradução para português, simplificação do dashboard, foco em pessoas.

### Onde a IA errou e como corrigi

- **Distribuição do scoring concentrada.** 77% dos deals ficaram como "morno". Recalibrei usando percentis em vez de thresholds fixos, gerando distribuição 15/37/33/15%.
- **Sazonalidade com peso inflado.** IA manteve 20 pts do modelo anterior sem questionar. Reduzi para 5 pts após analisar que o spread era só 25pp vs 54pp do fit vendedor+setor.
- **Dashboard com informação demais.** Claude Code construiu painel com todos os dados visíveis. Reorganizei em 3 camadas (foco → recomendações → dados colapsáveis).

### O que eu adicionei que a IA sozinha não faria

- Escolha do challenge baseada em experiência profissional real com CRMs em produção
- Hierarquia de 3 níveis (Gestor → Gerente → Vendedor) com isolamento de dados
- Organização da informação em 3 camadas (foco agora → recomendações → dados de suporte)
- Remanejamento automático em vez de sugestão — na prática, sugestão não gera ação
- Cadência diferenciada como processo de vendas, não como métrica decorativa
- Decisão de não chamar o scoring de "IA" — honestidade sobre o que é e o que não é
- Foco em pessoas (quem precisa de atenção) em vez de métricas abstratas
- Narrativa de especialização setorial como tese central do produto

### Evidências

- [x] Chat export da conversa com Claude (planejamento, análise, scoring)
- [x] CLAUDE.md usado como input para o Claude Code
- [x] Screenshots do app funcionando


---

*Submissão enviada em: julho 2026*
