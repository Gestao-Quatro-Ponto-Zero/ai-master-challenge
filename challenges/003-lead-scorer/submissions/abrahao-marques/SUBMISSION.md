# Submissão — Abrahão Marques — Challenge 003

## Sobre mim

- **Nome:** Abrahão Marques
- **LinkedIn:** linkedin.com/in/abrahaomarques
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construí um dashboard de priorização de pipeline de vendas em HTML/JS vanilla, sem backend, que roda diretamente no browser. A ferramenta resolve um problema real: vendedores que priorizam deals "no feeling" e deixam oportunidades boas esfriar enquanto gastam tempo em deals que não vão fechar. Cruzei 4 tabelas do CRM (8.800 deals), calculei um score de 0–100 por deal baseado em 3 critérios objetivos, e apresentei o pipeline com impacto financeiro em destaque — porque o que importa para um vendedor não é o score, é o dinheiro em jogo. A principal recomendação é usar o painel de Manager toda segunda-feira como pauta do 1:1, focando os esforços nos 138 deals de score alto que representam $897K em pipeline de alta probabilidade.

---

## Solução

**Live:** https://lead-scorer-abrahao.netlify.app
**GitHub:** https://github.com/markespro/lead-scorer-abrahao

### Abordagem

Antes de escrever qualquer código, usei o Claude para analisar os dados disponíveis e entender o que realmente importava para o scoring. O processo foi:

1. **Escolha do desafio com contexto** — passei meu histórico de trabalhos para o Claude identificar qual challenge eu tinha mais facilidade de entregar bem. O 003 foi escolhido porque já trabalho com CRM, pipeline e qualificação de leads no dia a dia.

2. **Análise exploratória antes de codar** — li os 4 CSVs, identifiquei o bug de `GTXPro` vs `GTX Pro` que quebrava o join de produtos, mapeei campos disponíveis e quantifiquei dados faltantes (68% dos deals sem account vinculada).

3. **Definição da lógica de scoring em conversa** — cada decisão foi discutida com base nos dados reais antes de implementar: qual threshold usar para estagnação (mediana = 165 dias), por que excluir revenue da conta, qual peso dar a cada critério.

4. **Build iterativo** — comecei com tabela simples e fui adicionando camadas: gráficos, abas por perfil, impacto financeiro, KPIs interativos, histórico Won/Lost, tema visual, mobile.

5. **Auditoria final** — cruzei CSV original vs dados embutidos no HTML linha a linha antes do deploy.

### Resultados / Findings

**Dashboard com 3 abas:**

**Pipeline** — 2.089 deals abertos ordenados por $ valor, com score sutil, filtros completos (Regional, Manager, Vendedor, Stage, Status Won/Lost/Todos), badges ⚠ Esfriando e ⏸ Estagnado, exportação CSV.

**Vendedor** — painel pessoal com KPIs clicáveis que filtram gráficos e tabela em tempo real. Top 5 deals por valor, distribuição de score, $ por produto e stage, performance histórica com win rate.

**Manager** — visão da equipe com ranking por $, saúde do pipeline, $ em risco por vendedor, win rate individual, tabela detalhada com filtros.

**Números encontrados:**

| Métrica | Valor |
|---|---|
| Pipeline aberto total | $4.97M |
| Deals de score alto (≥70) | 138 deals — $897K |
| Deals estagnados em Engaging | 779 deals — $2.06M parado |
| Deals esfriando (>250 dias) | 450 deals — $1.14M em risco |
| Receita histórica Won | $10.005.534 |
| Win rate geral | 63.2% |
| Maior pipeline individual | Darcel Schlecht — $656K |
| Menor pipeline individual | $80K |
| Diferença win rate melhor vs pior | 15.4pp (70.4% vs 55.0%) |

### Recomendações

**1. Rebalancear a distribuição de leads por vendedor**
O pipeline está concentrado: Darcel tem $656K enquanto o menor vendedor tem $80K — diferença de 8x. Redistribuir novos leads com base na capacidade real de cada agente usando o dashboard como referência.

**2. Priorização estratégica por score + valor**
Focar os 138 deals de score alto (≥70) = $897K de alta probabilidade. Definir SLA: score ≥70 → contato em 24h | score 40–69 → 72h | score <40 + esfriando → descartar ou transferir.

**3. Ritual semanal de pipeline review**
Usar o filtro por Manager toda segunda-feira como pauta do 1:1 — o gráfico "$ em risco por vendedor" identifica em 30 segundos quem precisa de atenção.

**4. Campanha de reativação dos estagnados**
779 deals estagnados = $2.06M parado no mesmo stage há mais de 165 dias. Script específico para deals parados pode converter parte desse valor antes de dar baixa.

**5. Coaching direcionado por win rate**
15.4pp de diferença entre melhor e pior vendedor com o mesmo volume de pipeline. Replicar práticas dos top performers é a alavanca mais rápida sem aumentar headcount.

**6. Integração com CRM em tempo real**
Próximo passo técnico para eliminar exportação manual de CSVs e ter o score refletindo o pipeline do dia.

### Limitações

| Limitação | Impacto | O que precisaria para escalar |
|---|---|---|
| Dados embutidos no HTML | Arquivo pesado (~2.5MB); não é tempo real | Backend com API + banco de dados |
| Scoring por regras fixas | Não aprende com novos dados | Modelo de ML com retreinamento periódico |
| Win rate histórico fora do score | Vendedor com 70% WR tem mesmo peso que 55% | WR do vendedor como multiplicador no score |
| Sem autenticação | Qualquer pessoa com o link vê todos os dados | Login por vendedor com dados filtrados por permissão |
| 68% dos deals sem account vinculada | Revenue da conta excluído do scoring | Enriquecimento de dados no CRM |
| Data de referência fixa (Dez/2017) | Dias no pipeline calculado a partir de data histórica | Integração com CRM em tempo real |

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude Sonnet (claude.ai) | Análise exploratória dos dados, definição da lógica de scoring, geração de todo o código HTML/JS/CSS, debugging, design e responsividade mobile |
| Netlify | Deploy gratuito da aplicação estática |

### Workflow

1. **Seleção do desafio** — passei meu histórico de trabalhos com CRM/automação para o Claude identificar qual challenge eu tinha mais vantagem competitiva. Escolhemos o 003.
2. **Leitura dos dados** — Claude leu os 4 CSVs, mapeou campos, identificou o bug de normalização do produto e quantificou dados faltantes antes de qualquer código.
3. **Definição do scoring em conversa** — cada critério foi discutido e justificado com base nos dados reais. Excluímos revenue, calibramos threshold de estagnação na mediana, definimos pesos.
4. **Build iterativo em 32 iterações** — tabela básica → filtros → gráficos → abas Vendedor/Manager → impacto financeiro → KPIs interativos → histórico Won/Lost → tema Prumo → mobile.
5. **QA e auditoria** — cruzamento CSV vs HTML confirmou 100% de integridade dos dados.
6. **Deploy** — tentamos Replit (saldo gratuito esgotou), migramos para Netlify.

### Onde a IA errou e como corrigi

- **Bug GTXPro vs GTX Pro** — a IA não detectou o problema de normalização na primeira passagem. Só foi encontrado na auditoria de integridade — 333 deals estavam sem `sales_price` e recebendo `score_valor = 0` incorretamente.
- **Sort invertido** — o dashboard inicial mostrava deals com score baixo primeiro. Bug na lógica de comparação do sort corrigido manualmente.
- **Botão "ver explicação" não funcionava** — a substituição do template JS foi aplicada no CSS mas não no render das linhas. Corrigido após inspeção do HTML gerado.
- **Filtro "Todos" incompleto** — ao selecionar "Todos" no status, Won/Lost não apareciam. A função `getSourceData()` retornava só `RAW_DATA`. Corrigido para combinar os dois datasets.
- **Tentativa com Replit** — plataforma citada no desafio, mas o plano gratuito esgotou rapidamente. Migração para Netlify resolveu.

### O que eu adicionei que a IA sozinha não faria

- **A lógica de scoring — essa foi minha decisão mais importante.** A IA apresentou opções, mas fui eu quem definiu os 3 critérios, os pesos, o threshold de estagnação (165 dias = mediana do dataset), a penalidade de -8pts e a exclusão do revenue da conta. Cada escolha foi discutida com base nos dados reais antes de implementar — a IA executou, mas o raciocínio de negócio foi meu. Um scoring diferente geraria prioridades completamente diferentes para os vendedores.
- **Foco em receita ($) como métrica principal** — a IA gerou score como destaque. Decidi inverter: $ em destaque, score sutil. Vendedor pensa em dinheiro, não em pontuação.
- **KPIs clicáveis com drill-down** — surgiu da observação de como vendedores realmente usam dashboards. Clicar num número e ver os deals por trás é o comportamento natural.
- **Decisão de incluir Won/Lost** — a IA estava focada só no pipeline aberto. Percebi que o histórico de fechamentos era essencial para o Manager entender performance real da equipe.
- **Referências visuais externas** — trouxe dois dashboards de referência (financeiro + sales report) para guiar o redesign. A IA executou, mas a curadoria foi minha.
- **Paleta Prumo Performance** — identidade visual da minha agência aplicada ao projeto. Personalização que a IA não faria sozinha.

---

## Evidências

- [x] **Process Log completo (Notion)** — [https://silky-tapir-21c.notion.site/process-log-abrahao](https://silky-tapir-21c.notion.site/process-log-abrahao)
- [x] **Git history** — [https://github.com/markespro/lead-scorer-abrahao/commits/main](https://github.com/markespro/lead-scorer-abrahao/commits/main)
- [x] **Aplicação ao vivo** — [https://lead-scorer-abrahao.netlify.app](https://lead-scorer-abrahao.netlify.app)

---

_Submissão enviada em: março de 2026_
