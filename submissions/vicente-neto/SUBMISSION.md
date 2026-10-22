# Submissão — Vicente Neto — Challenge 001

## Sobre mim

- **Nome:** Vicente Neto
- **LinkedIn:** https://www.linkdin.com/in/vsneto
- **Challenge escolhido:** 001 — Diagnóstico de Churn (RavenStack, Dados / Analytics)

---

## Executive Summary

Cruzei as 5 tabelas do RavenStack numa tabela mestre por conta, testei as afirmações do CEO, do CS e do Produto e construí um modelo preditivo e uma ferramenta de CS. O churn subiu de verdade: a taxa trimestral de primeiro churn foi de **18,5% para 32,2%** entre o 4T23 e o 4T24, em todos os segmentos, com **US$ 2,91 mi de MRR perdido**. Mas nenhum comportamento medido (satisfação, tickets, uso, erros, downgrades) separa quem sai de quem fica. O único fator que prevê churn é a **idade da conta**: contas novas saem mais (AUC 0,645 num período que o modelo não viu). O problema mais urgente é a medição: três fontes dão 22%, 62% e 70% de churn, e 52,9% do uso registrado é anterior ao cadastro da conta. A principal recomendação é fechar uma definição única de churn e corrigir os dados antes de cobrar metas. Enquanto isso, o risco deve ser estimado pela idade da conta, e não cortar o investimento em ads, que é o canal que mais retém.

---

## Solução

A entrega tem quatro partes, todas reprodutíveis a partir dos 5 CSVs:

| Entregável | O que é | Arquivo |
|---|---|---|
| **Painel de diagnóstico fase a fase** | Dashboard interativo com 11 fases (0 a 10). Cada número leva à fonte de dados que o gerou | Link Painel : https://claude.ai/artifact/HNmaQcLqcSEXyxg6wfyKgA ) *| 
| **Relatório para o CEO** | Diagnóstico com resumo executivo, causa raiz, hipóteses, modelo e ações com base nos dados | `diagnostico_churn_ravenstack.md` |
| **Painel executivo** | Uma página: o que se pode e o que não se pode afirmar | `dashboard_ceo_churn.html` |
| **Tabela mestre para Supabase/Lovable** | 500 contas × 106 colunas, gerada por SQL | `build_accounts_master.sql`, `accounts_master.csv` |
| **Modelo preditivo** | Churn em 90 dias com fotos mensais e validação temporal | `churn_model.py`, `model_*.csv` |
| **Ferramenta de CS** | Fila de contas por MRR esperado em risco, com gatilhos, evidências e tickets por conta | `cs_risk_tool.py`, `cs_*.csv` |
| **Evidências** | 32 números do relatório com fonte, tabelas cruzadas e teste estatístico | `evidence.py`, `evidence.csv` |

### Estrutura do repositório

```
churn-diagnostic/
├── README.md                          # visão geral e como rodar
├── SUBMISSION.md                      # este documento
├── requirements.txt                   # pandas, numpy, scipy, scikit-learn
├── run_all.sh                         # roda todo o pipeline em Python
├── data/                              # os 5 CSVs do Kaggle (RavenStack, River @ Rivalytics)
├── sql/
│   └── build_accounts_master.sql      # tabelas brutas + tabela mestre (PostgreSQL/Supabase)
├── src/
│   ├── paths.py                       # caminhos de data/ e outputs/
│   ├── analysis_base.py               # carga e análises base
│   ├── evidence.py                    # evidence.csv e at_risk_accounts.csv
│   ├── build_monthly_trend.py         # série mensal
│   ├── feature_channel_analysis.py    # tendência por feature e churn por canal
│   ├── churn_model.py                 # modelo preditivo e previsões
│   └── cs_risk_tool.py                # ferramenta de CS
├── outputs/                           # tudo o que os scripts geram (+ accounts_master.csv do SQL)
└── docs/
    ├── diagnostico_churn_ravenstack.md
    ├── dashboard_ceo_churn.html
    └── data_dictionary_and_quality.md
```

**Para reproduzir:**
1. `sql/build_accounts_master.sql` no PostgreSQL/Supabase gera `outputs/accounts_master.csv`. Uma cópia já vem no repositório.
2. `pip install -r requirements.txt` e depois `bash run_all.sh`. O pipeline foi rodado do zero nesta estrutura, e as saídas são idênticas às do relatório.

---

## Abordagem

Segui um roteiro em fases, do entendimento dos dados à ferramenta para o CS:

| Fase | O que fiz | Por quê |
|---|---|---|
| 0 · Setup | Estrutura do projeto e roteiro | Ter um plano antes de tocar nos dados |
| 1 · Dados | Validação de tamanho, granularidade, chaves e conteúdo das 5 tabelas | Não construir em cima de dado quebrado |
| 2 · Tabela mestre | Agregação por conta antes do join; corte temporal no primeiro churn (variáveis `_pre`); SQL validado em PostgreSQL 16 | Evitar duplicar linhas e usar o futuro para explicar o passado |
| 3 · Contradições | Teste separado de cada fala: CEO (churn), CS (satisfação), Produto (uso) | O enunciado diz que "algo não bate" |
| 4 · Causalidade | Testes estatísticos, estratificação, permutação, correção para múltiplos testes | Separar correlação, artefato e causa |
| 5 · Valor | Churn em MRR, não só em contas; contas em risco | Perder US$ 5 mil/mês ≠ perder US$ 50/mês |
| 6 · Diferenciais | Canal de aquisição, dia 30, trial e modelo preditivo | Responder às perguntas que mudam a decisão |
| 7 · Relatório | Relatório e painel executivo para o CEO | Leitura não técnica |
| 8 · Process log | Registro das correções | Transparência sobre o uso de IA |
| 9 · Causa e decisão | Escada de evidência e conclusões para o CEO | Critério do desafio: correlação × causalidade |
| 10 · Ferramenta de CS | Fila priorizada com gatilhos e ações por conta | Transformar o diagnóstico em ação |

**O que priorizei:**
- **Primeiro, a qualidade da medição.** Percebi cedo que as fontes de churn não batiam, e isso mudou toda a narrativa.
- **Depois, testar cada hipótese contra explicações alternativas** antes de chamá-la de achado.
- **Por último, só ações com base nos dados.** Removi propostas que não tinham número que as sustentasse.

---

## Resultados / Findings

### 1. As três falas do CEO

| Afirmação | O que os dados mostram | Veredito |
|---|---|---|
| "O churn subiu" | Eventos de churn foram de 6 para 251 por trimestre. A taxa de primeiro churn, sobre contas já ativas no início do trimestre, foi de 18,5% para 32,2% (4T23 → 4T24). Todos os 17 segmentos estão entre 25% e 39% | **Verdadeiro e generalizado** |
| "A satisfação está ok" (CS) | CSAT 3,98 nas churnadas e 3,98 nas retidas (p = 0,83). 41,2% dos tickets não têm nota e só existem notas 3, 4 e 5 | **O número é verdadeiro, mas a métrica não distingue quem sai** |
| "O uso cresceu" (Produto) | O total registrado subiu 2,6%, mas 52,9% dele é anterior ao cadastro da conta. Com o uso válido, o uso por conta ativa subiu 2,3% em 2024, sem diferença significativa entre segmentos (Kruskal p de 0,13 a 0,91) | **Não se sustenta: o total está contaminado** |

### 2. O churn medido é inconsistente (achado mais forte)
- **Três critérios de churn, três números:** flag em accounts **110 contas (22%)**, ≥1 assinatura encerrada **312 (62%)**, ≥1 evento de churn **352 (70%)**. Só 75 contas aparecem no flag e nos eventos, sem relação estatística entre os dois (p = 0,65).
- **Nenhuma conta perdeu todas as assinaturas.** As 352 contas com churn ainda têm **US$ 7,14 mi de MRR ativo**.
- **Há atividade depois do churn:** 28% do uso e 27,7% dos tickets das contas churnadas.

### 3. Hipóteses testadas

| Hipótese | Resultado | Veredito |
|---|---|---|
| Mais tickets ou escalações antes de sair | 0,53 vs 0,52 tickets em 90 dias (p = 0,76) | Descartada |
| Queda de uso antecede o churn | 50,0% vs 56,8% de churn (p = 0,56) | Descartada |
| Erros ou features beta explicam | 4,29 vs 4,44 erros por 100 usos (p = 0,80) | Descartada |
| Quem usa menos sai mais | p = 0,02 no total, mas some ao comparar contas com o mesmo tempo de vida | Descartada (artefato) |
| Alguma feature piorou | Duração por uso: nenhuma feature resiste à correção para 40 testes. Taxa de erro: **feature_9 dobrou** (3,6 → 7,1 por 100 usos válidos, q = 0,03), mas o erro nela não difere entre quem saiu e quem ficou | Achado de produto, sem ligação com churn |
| Plano, indústria, porte ou país concentra o churn | Todos p > 0,14 | Descartada |
| Downgrade antecede o churn | 73,4% vs 68,7% (p = 0,32) | Descartada |
| Motivo declarado reflete o comportamento | Motivo × comentário do cliente p = 0,99 | Descartada |
| Aquisição paga traz clientes piores | **Ao contrário:** ads tem 41% sem churn em 365 dias, contra 26% nos demais (log-rank p = 0,005; permutação p = 0,006; estável por plano, indústria, porte e país) | **Ads retém mais** |
| Comportamentos preveem quem sai | AUC 0,47–0,48 | Descartada |
| A idade da conta prevê quem sai | AUC 0,645 (IC 95% 0,59–0,70) num período que o modelo não viu | **Confirmada** |

### 4. Impacto financeiro
- **MRR perdido no momento do primeiro churn:** **US$ 2,91 mi**, dos quais **US$ 1,37 mi só no 4T24**. No 4T24 foram 112 contas, contra 80 no 3T24, mas a perda em MRR cresceu 58%.
- **Proporção:** o churn atinge as contas grandes na mesma proporção que as pequenas (70,3% do MRR vs 70,4% das contas).
- **Reembolsos:** somam US$ 8.652, cerca de 0,3% do MRR perdido.

### 5. Modelo preditivo (churn em 90 dias)
- **Desenho:** 2.705 fotos mensais de 388 contas, cada uma só com o que se sabia naquela data. Treino de abr/2023 a mar/2024 e teste de abr a out/2024.
- **Desempenho:** o melhor modelo usa **só a idade da conta**. Teve AUC de 0,645, e nos 20% de contas de maior risco o churn foi de 45,7%, contra 29,4% na média (lift de 1,55).
- **Comparação:** gradient boosting com 34 variáveis teve AUC 0,583, e sem a idade ficou em 0,552.
- **Previsão para 1º/01/2025:** 148 contas ativas, cerca de 42 churns esperados em 90 dias e US$ 850 mil de MRR em risco.

### 6. Ferramenta de CS
- **Fila:** as 148 contas ordenadas pelo MRR esperado em risco. 119 delas têm pelo menos um gatilho ligado a tickets, satisfação, assinaturas ou uso.
- **Ficha por conta:** cada gatilho traz a evidência (tickets citados por número e data) e a ação ligada.
- **Honestidade das regras:** só a regra "conta nova" previu churn. As outras são motivo de contato e informam isso.

### Links
- **Painel de diagnóstico fase a fase:** https://claude.ai/artifact/HNmaQcLqcSEXyxg6wfyKgA *(compartilhar antes de enviar)*
- **Screenshots:** [adicionar capturas do painel: topo, Fase 3, Fase 6 e Fase 10]

---

## Recomendações

Só entram aqui ações que decorrem diretamente de um achado. Donos, prazos e metas não estão nos dados e ficam para a empresa definir.

| Prioridade | Ação | Base nos dados |
|---|---|---|
| 1 | **Definir uma regra única de churn e recalcular o histórico** | 110, 312 e 352 contas churnadas conforme a fonte; nenhuma conta perdeu todas as assinaturas |
| 2 | **Corrigir os registros de uso antes de medir crescimento** | 52,9% do uso registrado é anterior ao cadastro |
| 3 | **Corrigir o ciclo das assinaturas** | 4.514 de 5.000 assinaturas abertas; contas com churn seguem com US$ 7,14 mi de MRR ativo |
| 4 | **Corrigir a coleta da nota de satisfação** | 41,2% dos tickets sem nota; só notas 3 a 5 |
| 5 | **Corrigir o registro do motivo de churn** | Motivo e comentário do cliente não batem (p = 0,99) |
| 6 | **Estimar o risco pela idade da conta**, não por comportamentos ou sinais de alerta | Só a idade prevê (AUC 0,645); comportamentos ficam no acaso (AUC 0,47) |
| 7 | **Investigar organic e partner, e não cortar ads** | Sem churn em 365 dias: ads 41%, organic 25%, partner 26% |
| 8 | **Investigar o aumento de erros na feature_9** (questão de produto, não de churn) | Erros por 100 usos válidos: 3,6 em 2023 → 7,1 em 2024 (q = 0,03) |

---

## Limitações

- **Dataset sintético.** O README descreve os dados como gerados por sorteios. A ausência de padrões comportamentais pode ser artefato do gerador. Em dados reais, eu concluiria que a instrumentação atual não enxerga a causa, e não que a causa não existe.
- **Definição de churn em aberto.** Todas as análises usam o evento da tabela `churn_events`. Com outra definição, os números mudam.
- **MRR inflado.** As contas têm em média 10 assinaturas sobrepostas, então o MRR por conta é peso relativo, não receita real.
- **Causalidade não testada.** Nenhum achado chega a causa: isso exige experimento com grupo de controle. Ads reter mais pode refletir o perfil de quem chega por anúncio.
- **Sem custo por canal.** Não dá para avaliar o retorno do investimento em ads.
- **Probabilidades do modelo.** Na mesma idade, o churn do teste foi o dobro do treino. As previsões foram recalibradas para a taxa recente e assumem que ela se mantém.
- **Sem registro de ações do CS.** O efeito das ações da ferramenta não pode ser medido.
- **Colunas de uso da tabela mestre.** Ainda somam o uso anterior ao cadastro. As análises recalculam só o uso válido, e o dicionário de dados registra o alerta.
- **Testes múltiplos.** Os p-valores não têm correção global, exceto na análise por feature (Benjamini-Hochberg) e no contraste de canais (Bonferroni).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude (Anthropic), com execução de código | Roteiro do desafio, análise exploratória, testes estatísticos, SQL da tabela mestre, modelo preditivo, ferramenta de CS, relatório, painéis e este documento |
| PostgreSQL 16 (rodado pela IA no ambiente de execução) | Validar que o SQL da tabela mestre roda e bate coluna a coluna com a versão em pandas |
| Python (pandas, scipy, scikit-learn) | Análises, testes, modelo e ferramenta de CS |
| [Supabase / Lovable] | [Preencher se você subiu a tabela mestre e construiu algo lá] |

### Workflow

1. **Planejamento.** Pedi à IA um passo a passo para o desafio. Ela propôs o roteiro de 8 fases que segui.
2. **Fases 1 e 2.** A IA leu os 5 CSVs, validou chaves e conteúdo e encontrou os problemas de qualidade. Depois montou a tabela mestre e o SQL para Supabase. Eu defini o destino (Lovable/Supabase).
3. **Explicação do problema.** Pedi o cruzamento explícito das 5 tabelas e um número verificável em cada insight. A IA gerou o `evidence.csv`, com fonte e teste para cada número.
4. **Painel para o CEO.** Pedi um painel que separasse o que se pode e o que não se pode afirmar.
5. **Perguntas de negócio.** Testei com a IA as hipóteses que eu levantei:
   - churn por "saturação natural";
   - degradação de features;
   - canal de aquisição;
   - tickets de quem saiu;
   - uso por segmento;
   - impacto em MRR;
   - assinaturas sobrepostas e efetivação no dia 30.
6. **Validação e SQL.** Pedi para validar a fala do CEO e gerar o SQL da base. A IA rodou o SQL num PostgreSQL local e comparou com o pandas.
7. **Painel fase a fase.** Pedi um painel com todas as fases, depois a Fase 9 (causalidade e leitura do CEO).
8. **Revisão crítica.** Mandei remover as sugestões sem base nos dados, no painel, no relatório e no painel executivo.
9. **Modelo preditivo e ferramenta de CS.** Pedi o modelo e uma ferramenta de automação para o CS ligada aos tickets.

### Onde a IA errou e como corrigi

| # | Erro | Antes → depois | Como foi detectado |
|---|---|---|---|
| 1 | Taxa trimestral de churn com base misturada: contas novas entravam no numerador, mas não na base | 43,1% → **32,2%** no 4T24 | A IA validou a mesma conta em SQL e o número não bateu |
| 2 | "Uso cresceu 2,6%" usava todo o uso registrado, inclusive o anterior ao cadastro | +2,6% total → **+2,3% por conta ativa (uso válido)** | Ao responder minha pergunta sobre uso por segmento, a IA cruzou data de uso e data de cadastro |
| 3 | Sinal de uso e AUC acima do acaso vinham do tempo de vida da conta | AUC 0,58–0,60 → **0,47** | Comparação dentro de faixas de tempo de vida |
| 4 | Quatro features com duração "degradada" eram falso positivo de múltiplos testes; a análise também usava o uso inválido | Duração: 4 → **0** após Benjamini-Hochberg. Refeita com uso válido ao organizar o repositório, ela revelou que o **erro da feature_9 dobrou** | Correção para 40 testes e revisão de reprodutibilidade |
| 5 | Lista de risco usava a queda de uso sem filtrar o uso inválido | 19 contas / US$ 540 mil → **17 / US$ 394 mil** | Pedi para atualizar todos os documentos com o uso válido |
| 6 | Relatório dizia que "nenhum canal se destaca", mas a análise de sobrevivência mostrou que ads retém mais | Corrigido em relatório e painéis | Revisão dos documentos após a análise de canal |
| 7 | Bugs de SQL: tipo da nota de satisfação, data com hora, coluna vazia no dia 30 | Corrigidos | Rodando o SQL no PostgreSQL e comparando com o pandas |
| 8 | Modelo numa foto única tratava a idade da conta como vazamento | Refeito com fotos mensais e validação temporal: AUC 0,645 | Revisão do desenho do modelo quando pedi o modelo preditivo |
| 9 | Regra de renovação automática da ferramenta de CS disparava em 112 de 148 contas | Critério relativo (percentil 75): **37 contas** | A IA viu que o gatilho não diferenciava ninguém |
| 10 | O painel trazia metas, donos, prazos e um piloto sem base nos dados | **Removidos**; cada ação ficou ligada ao número que a sustenta | **Eu** apontei e pedi a remoção |

### O que eu adicionei que a IA sozinha não faria

- **As perguntas de negócio.** Levantei as hipóteses que guiaram as Fases 3 a 6: saturação natural da base, degradação de features, canal de aquisição sem foco, tickets de quem saiu, uso por segmento, peso financeiro do churn, trial e efetivação no dia 30. A análise de canal mostrou o contrário do que eu supunha (ads retém mais), e mantive o achado.
- **O critério de só recomendar o que tem base nos dados.** A IA tinha incluído metas, prazos, donos e um piloto. Eu pedi para remover tudo que não tivesse um número que sustentasse, e isso deixou o relatório mais defensável diante do CEO.
- **Consistência entre documentos.** Pedi para levar cada correção a todos os entregáveis (relatório, painel executivo, evidências, série mensal e dicionário), e não só ao último arquivo.
- **O destino prático.** Defini que a base tinha que subir no Lovable/Supabase em CSV com o SQL que a gera, e que o diagnóstico tinha que virar uma ferramenta que o CS usaria no dia seguinte.
- **A leitura do CEO.** Pedi a fase que responde se a análise separa correlação de causalidade e se um CEO não técnico consegue agir com ela.

### Evidências

- [ ] Screenshots das conversas com IA — [adicionar]
- [ ] Screen recording do workflow — [adicionar, se houver]
- [ ] Chat exports — [exportar a conversa com o Claude e anexar]
- [ ] Git history — [link do repositório]
- [x] Outro: painel de diagnóstico fase a fase com o process log na Fase 8 e o registro das correções — https://claude.ai/artifact/HNmaQcLqcSEXyxg6wfyKgA
- [x] Outro: `evidence.csv`, com os 32 números do relatório, a fonte, as tabelas cruzadas e o teste de cada um

---

**Submissão enviada em:** [data]
