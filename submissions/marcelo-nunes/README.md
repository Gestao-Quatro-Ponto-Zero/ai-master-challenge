# Submissão — Marcelo Adriano Nunes Filho — Challenge 001 (Diagnóstico de Churn)

## Sobre mim

- **Nome:** Marcelo Adriano Nunes Filho
- **LinkedIn:** [linkedin.com/in/marceloanunesfilho](https://www.linkedin.com/in/marceloanunesfilho/)
- **Challenge escolhido:** 001 — Diagnóstico de Churn (Data/Analytics)

---

## Executive Summary

Analisei os 5 datasets da RavenStack cruzando 33.100 registros e descobri que o churn de **22% (110 contas inativas)** é só a ponta do iceberg: **352 contas (70%)** já cancelaram pelo menos uma vez, num problema **estrutural** de Porta Giratória — 277 contas cancelam, voltam, e cancelam de novo. As métricas que o time de CS usa (satisfação, uso, health score) **não detectam** quem vai sair. DevTools é o único segmento estatisticamente significativo (p=0.004), e 25 contas Enterprise perdidas representam 73% do MRR perdido ($122k/mês). Construí um dashboard interativo com 10 seções, um modelo de risk scoring cruzando todas as 5 tabelas, e 5 estratégias com ROI estimado que podem recuperar ~$1M/ano (51% da perda).

---

## Solução

### Abordagem

1. **Reconhecimento dos dados**: Explorei os 5 CSVs com Python/Pandas para entender schema, volumes e relações. A IA apresentou 110 contas com churn_flag=True como "22% de churn". Olhando os números, percebi que 600 eventos de churn para 110 contas não fazia sentido — havia dados duplicados que precisavam ser investigados.

2. **Questionamento crítico**: Pedi para a IA investigar: "muitos dados duplicados", "61 reativações repetem?". Isso revelou que 352 contas únicas tiveram eventos de churn — 277 cancelaram e voltaram (Porta Giratória). As 110 inativas (22%) são reais, mas o problema é maior: 70% da base já churnaram pelo menos 1x.

3. **Validação estatística**: A IA inicialmente listava "Alemanha 32% churn" como segmento em risco. Apontei que Alemanha tem base pequena de clientes — isso levou à aplicação de teste chi-quadrado + IC 95% para cada segmentação. Dos ~20 segmentos, apenas DevTools é significativo.

4. **Dashboard interativo**: Construí em Lovable (React/TypeScript/Recharts) um dashboard de 10 seções navegável com tema claro/escuro, acessível para CEO não-técnico.

5. **Automação CS**: A Risk Watchlist — modelo de scoring ponderado que cruza as 5 tabelas para identificar as 20 contas ativas em maior risco de churn. Ferramenta acionável para o time de CS.

### Resultados / Findings

**Dashboard interativo**: [g4-ai-challenge-churn.lovable.app](https://g4-ai-challenge-churn.lovable.app) (React + Recharts, light/dark theme)

**5 descobertas principais:**

| # | Descoberta | Evidência | Impacto |
|---|-----------|-----------|---------|
| 1 | **Porta Giratória**: 55% das contas já cancelaram pelo menos 1x | 600 eventos / 352 contas únicas. 175 com 2+ churns. 82% mudam o motivo entre churns | O churn não é um evento isolado — é um padrão recorrente. Motivos declarados são ruído |
| 2 | **Satisfação QUEBRADA**: Score não detecta insatisfação | Zero scores 1-2 em 2.000 tickets. Média idêntica: churned 3.95 vs retained 3.94. 41% sem resposta | CS está cego. Instrumento precisa ser reconstruído |
| 3 | **DevTools = único segmento significativo** | p=0.004, taxa 24.8% (vs 15% documentado). DevTools+Enterprise = 31.4% (pior intersecção) | Todos os outros segmentos (país, plano, canal) NÃO são significativos. Foco deve ser DevTools |
| 4 | **Enterprise = 73% do MRR perdido** | 25 contas = $122k/mês. Top 10 sozinhas = $97k/mês = 58% de toda perda | Perder 1 Enterprise = perder 5 Basic. Requer atenção desproporcional |
| 5 | **Uso da plataforma NÃO cresceu** | ~10.500 interações/mês flat por 24 meses. ~420 contas ativas flat | Contradiz narrativa do time de Produto. ~20 signups/mês anulados pelo churn |

**Automação construída — Risk Watchlist:**
- Score ponderado cruzando as 5 tabelas (churn history 25pts/evento, DevTools +20pts, Enterprise +15pts, billing mensal +10pts, MRR alto +10pts, escalações +5pts/cada, conta silenciosa +5pts)
- Top 20 contas ativas em risco com MRR combinado, playbook de ação por timeline (amanhã, esta semana, este mês)
- Impacto estimado: salvar 5 de 25 Enterprise = $683k/ano com ROI 7x

### Recomendações

| Prioridade | Estratégia | Custo/mês | Recuperação/ano | ROI |
|------------|-----------|-----------|-----------------|-----|
| IMEDIATO | Enterprise Save Program (1 CSM dedicado) | $8.000 | $683.000 | 7x |
| CURTO PRAZO | Desconto Anual 15% (lock-in mensais >$2k) | $5.600 | $68.000 | 2x |
| CURTO PRAZO | DevTools PMF Audit (único p<0.01) | $0 | $274.000 | Alto |
| MÉDIO PRAZO | Programa 90-Day Success (Porta Giratória) | $0 | $971.000 | Alto |
| MÉDIO PRAZO | Qualificar Canal Events (p=0.059) | $0 | Qualitativo | - |

**Impacto combinado conservador: ~$85k/mês = ~$1M/ano recuperável (51% da perda)**

### Limitações

1. **Dataset sintético**: Padrões podem não refletir SaaS real (distribuições uniformes de reason codes podem ser artefato de geração)
2. **Health Score paradoxal**: Health score calculado (uso + features + recência + erros + tickets) NÃO prediz churn neste dataset — contas perdidas têm score MAIOR que retidas. Pode ser artefato ou insight real
3. **Causalidade vs correlação**: DevTools ter maior churn não significa que ser DevTools CAUSA churn. Pode ser confounding (ex: DevTools tende a ser mais Enterprise)
4. **Amostra insuficiente por país**: Alemanha (n=25), França (n=22), Canadá (n=23) — impossível tirar conclusões válidas
5. **Risk Watchlist não validada**: O modelo de scoring é baseado nos fatores identificados, mas não foi validado contra dados futuros (out-of-sample)
6. **Sem análise de texto**: O campo `feedback_text` dos churn events não foi analisado (NLP poderia extrair temas adicionais)

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Opus 4.6) | Análise exploratória dos 5 CSVs, geração de scripts Python, construção do dashboard HTML v1-v3, cruzamento de dados, testes estatísticos, construção do dashboard Lovable |
| VS Code | IDE principal, revisão de código, outputs e screenshots |
| Python + Pandas | Processamento e análise dos 33.100 registros, chi-quadrado, intervalos de confiança |
| Lovable | Hospedagem e deploy do dashboard React final |
| Recharts | Biblioteca de gráficos no dashboard interativo |
| Git/GitHub | Versionamento, evolução do código, submissão via PR |

### Workflow

1. **Reconhecimento**: Pedi ao Claude para baixar dados do Kaggle, clonar o repo, explorar headers e contagens. Já nessa fase notei que 600 eventos para 110 contas flagged não fazia sentido.
2. **Dashboard v1**: Pedi dashboard HTML local para visualizar dados. A IA gerou com 9 abas, mas tratava churn como binário (errado). Eu olhei os dados e vi duplicações.
3. **Questionamento crítico**: Questionei: "muitos dados duplicados", "61 reativações repetem?". Isso levou à descoberta dos 4 segmentos reais (Nunca Churnou, Porta Giratória, Perdido Permanente, Flag sem Evento).
4. **Dashboard v2**: Pedi para provar a pergunta do CEO: "o uso cresceu?". A IA investigou e confirmou que uso é flat 24 meses. Pedi também para corrigir a aba de satisfação — revelou que só mede 3-5.
5. **Matrizes de análise**: Sugeri: "existem matrizes tipo RFM para SaaS?". A IA pesquisou, construiu Customer Health Score, Engagement Matrix, Value vs Risk. Resultado paradoxal: health score NÃO prediz churn.
6. **Rigor estatístico + ROI**: Apontei: "Alemanha tem base pequena de clientes". A IA adicionou chi-quadrado para tudo. Sugeri desconto anual como mecanismo de lock-in. A IA construiu 5 estratégias com ROI.
7. **Lovable**: Pedi para gerar o prompt completo e criei o projeto no Lovable. Depois fiz push via Git com melhorias (Porta Giratória, Risk Watchlist, tema claro/escuro).
8. **Risk Watchlist**: Modelo de scoring cruzando as 5 tabelas. A IA analisou os 5 CSVs com Python para gerar scores reais das 390 contas ativas.
9. **Polish final**: Pedi correções de português, tema light/dark, e reclamei que "a explicação ficou muito longa" — levou ao TL;DR no topo.

### Onde a IA errou e como corrigi

| # | O que a IA fez | Problema | Correção |
|---|---------------|----------|----------|
| 1 | Dashboard v1 tratou churn_flag como binário | Ignorava 277 contas que churnaram e voltaram (55% da base) | Questionei: "muitos dados duplicados" e "61 reativações repetem?" — redesign completo |
| 2 | Merge de DataFrames sem tratar colunas homônimas | KeyError em plan_tier e churn_flag duplicados | A IA corrigiu tecnicamente, mas eu identifiquei o sintoma |
| 3 | Satisfação apresentada como métrica válida | Não percebeu que só existem scores 3-5 (instrumento quebrado) | Questionei: "não mostra muita coisa sobre satisfação" — a IA investigou e confirmou |
| 4 | Listou "Alemanha 32% churn" como segmento em risco | n=25, IC [11.5%-43.4%] — amostra insuficiente | Apontei: "Alemanha tem base pequena" — a IA adicionou testes estatísticos para tudo |
| 5 | Health Score paradoxal aceito sem questionamento | Score de contas perdidas MAIOR que retidas (64.7 vs 61.9) | Resultado paradoxal que virou insight: métricas tradicionais não funcionam neste cenário |
| 6 | Compactou contexto e perdeu meu prompt anterior | Tive que repetir as mesmas perguntas porque a IA perdeu o histórico | Repeti o prompt e apontei: "você compactou e perdeu minha pergunta anterior" |

### O que eu adicionei que a IA sozinha não faria

1. **Questionamento dos dados**: A IA aceitou churn_flag=True como "110 contas churned" e seguiu em frente. Eu olhei os números e percebi que não batiam — forcei a investigação que revelou a Porta Giratória.

2. **Ceticismo sobre métricas**: A IA mostrou satisfação como métrica válida. Eu comentei que "não mostra muita coisa" e pedi para investigar melhor — revelou que o instrumento só mede 3-5.

3. **Rigor estatístico**: A IA listava segmentos "em risco" sem validar. Eu apontei que Alemanha tem poucos clientes para ter certeza — isso levou à aplicação de testes estatísticos que derrubaram várias conclusões iniciais.

4. **Estratégia de desconto anual**: Sugeri a ideia de oferecer desconto para quem migrar de mensal para anual como mecanismo de lock-in. A IA desenvolveu a simulação a partir da minha sugestão.

5. **Decisão de usar Lovable**: Escolhi migrar de HTML estático para dashboard React interativo com deploy público. Pedi para a IA gerar o prompt e criei o projeto no Lovable.

6. **Pedido de síntese**: Reclamei que "a explicação ficou muito longa" e pedi um resumo inicial — levou ao TL;DR de 30 segundos no topo do dashboard.

---

## Evidências

- [x] Screenshots das conversas com IA (45 screenshots em `process-log/screenshots/`)
- [ ] Screen recording do workflow
- [ ] Chat exports
- [x] Git history (5 commits mostrando evolução: dashboard base → seções → risk watchlist → polish)
- [x] Dashboard interativo publicado: [g4-ai-challenge-churn.lovable.app](https://g4-ai-challenge-churn.lovable.app)
- [x] Scripts Python de análise (solution/)
- [x] Process Log detalhado com prompts reais e correções

---

## Diferenciais entregues (além do diagnóstico básico)

1. **Dashboard interativo** com 10 seções navegáveis, tema claro/escuro, responsivo
2. **Risk Watchlist** — modelo de scoring cruzando 5 tabelas, ferramenta acionável para CS
3. **Porta Giratória** — análise que mudou toda a narrativa (55% da base recicla)
4. **Rigor estatístico**: chi-quadrado + IC 95% em cada segmentação (descarta conclusões inválidas)
5. **ROI quantificado**: 5 estratégias com custo, recuperação e ROI estimados

---

## Como acessar

O dashboard é um protótipo público, sem senha, acessível direto pelo navegador:

**[g4-ai-challenge-churn.lovable.app](https://g4-ai-challenge-churn.lovable.app)**

Código-fonte: [github.com/marcelinhonunes/ravenstack-churn-insights](https://github.com/marcelinhonunes/ravenstack-churn-insights)

---

_Submissão enviada em: 2026-03-03_

_Dados: RavenStack Synthetic Dataset by River @ Rivalytics (MIT license)_
