# Diagnóstico de Churn — RavenStack

*Dataset: RavenStack (sintético, River @ Rivalytics). Janela: jan/2023 a dez/2024. Cada número abaixo tem um código (E01…E32) na planilha `evidence.csv`, com a fonte, as tabelas cruzadas e o teste estatístico usado. Toda análise de uso considera só o **uso válido**: registros a partir da data de cadastro da conta.*

---

## 1. Resumo executivo

1. **O churn subiu de verdade e subiu em todo lugar.** Entre as contas já ativas no início de cada trimestre, a taxa de primeiro churn foi de **18,5% (4T23) para 32,2% (4T24)**. No 4T24, todos os 17 segmentos (canal, plano, indústria, porte) estão entre 25% e 39% (E01–E03). O MRR perdido no momento do churn soma **US$ 2,91 mi**, dos quais US$ 1,37 mi só no 4T24.
2. **Nenhum comportamento medido explica quem sai.** Churnadas e retidas são praticamente iguais em satisfação (3,98 vs 3,98), tickets, escalações, uso, erros e downgrades. Um modelo preditivo baseado nesses comportamentos fica **no nível do acaso (AUC 0,47–0,48)** (E31). **O único fator que prevê churn é a idade da conta:** num modelo validado em período que ele não viu, só a idade atinge AUC 0,645, e as contas no quinto de maior risco churnaram 45,7% em 90 dias, contra 29,4% na média (seção 5). A outra diferença robusta vai na direção oposta à esperada: **clientes do canal pago (ads) ficam mais tempo**.
3. **CS e Produto estão "ambos certos" porque medem coisas que não separam quem fica de quem sai.** A satisfação está estável em ~4,0, mas 41% dos tickets não têm nota e a escala só tem 3, 4 e 5 (E08, E09). O "uso cresceu" vem de um total contaminado: **52,9% do uso registrado é anterior ao cadastro da conta**. Com o uso válido, o uso por conta ativa subiu só **2,3%** em 2024, sem diferença significativa entre segmentos (E13–E18).
4. **O problema mais urgente é que ninguém consegue dizer o que é "churn" nos dados.** Três fontes dão 22%, 62% e 70% das contas; nenhuma conta perdeu todas as assinaturas; e 28% do uso acontece depois da data de churn (E04–E07).
5. **O que os dados indicam fazer:** fechar uma definição única de churn (as fontes discordam em 110, 312 e 352 contas) e corrigir os registros de uso, assinaturas, satisfação e motivo antes de qualquer meta. Para estimar risco, os dados sustentam usar a **idade da conta**, e **não** comportamentos ou sinais de alerta (AUC 0,47; queda de uso não antecede churn). Também não sustentam cortar ads.

---

## 2. Como as 5 tabelas foram cruzadas

Cada tabela foi agregada **por conta antes** de juntar, para não multiplicar linhas. Resultado: `accounts_master.csv` com 500 linhas e 106 colunas, gerado por `build_accounts_master.sql` e conferido contra os brutos (5.000 assinaturas, 25.000 usos, 2.000 tickets, 600 eventos, MRR e reembolsos batem).

```
accounts (500) ──account_id──► subscriptions (5.000) ──subscription_id──► feature_usage (25.000)
     │
     ├──account_id──► support_tickets (2.000)
     └──account_id──► churn_events (600; 352 contas)
```

| Pergunta | Tabelas cruzadas |
|---|---|
| Quem churnou e quanto MRR carregava? | accounts + churn_events + subscriptions (E04–E06, E29) |
| O uso cresceu, e caiu antes do churn? | feature_usage → subscriptions → accounts + churn_events (E13–E21) |
| Suporte pior antes de sair? | support_tickets + churn_events + accounts (E08–E12) |
| O motivo declarado bate com o comportamento? | churn_events + support_tickets + feature_usage + subscriptions (E26–E27) |
| Downgrade antecede churn? | churn_events + subscriptions (E28) |
| Atividade depois do churn? | feature_usage + subscriptions + churn_events; support_tickets + churn_events (E07) |

---

## 3. Por que CS e Produto estão "ambos certos"

| Afirmação | O que os dados mostram | Veredito |
|---|---|---|
| **CS:** "satisfação está ok" | CSAT 3,98 nas churnadas e 3,98 nas retidas (E08). **41,2% dos tickets sem nota**; só existem notas 3, 4 e 5, nunca 1 ou 2 (E09). | Verdadeiro, mas a métrica **não discrimina** e está truncada. Não prova que o cliente está satisfeito. |
| **Produto:** "uso cresceu" | O total registrado subiu 2,6% em 8 trimestres, mas **52,9% dele é anterior ao cadastro da conta** (94,6% no 1T23, 6,0% no 4T24) (E13). Com o uso válido, o uso por conta ativa foi de 54,3 para 55,5 por trimestre em 2024, **+2,3%** (E14). Por segmento: Cybersecurity **+16,5%**, Enterprise +7,4%, DevTools **−18,8%**, Basic −4,9%, mas as diferenças entre segmentos não são significativas (Kruskal p de 0,13 a 0,91) (E15–E18). | O total registrado não mede crescimento. O uso por conta está **estável**. |
| **CEO:** "o churn subiu" | 6 → 251 eventos por trimestre (E01); taxa de 18,5% → 32,2% (E02). | Verdadeiro e generalizado. |

Um dado que parece uma pista e **não é**: o uso por 30 dias desde o cadastro é menor nas churnadas (mediana 18,2 vs 20,4, p = 0,02). Comparando contas com o mesmo tempo de vida, a diferença some (p de 0,19 a 0,74 nos quatro quartis) (E20). A diferença vem de as churnadas serem contas mais jovens.

---

## 4. Causa raiz: o que os dados sustentam e o que não sustentam

### 4.1 O churn medido é inconsistente (achado mais forte)

- Contas "churnadas" por três critérios: flag em accounts **110 (22%)**, ≥1 assinatura encerrada **312 (62%)**, ≥1 churn_event **352 (70%)**. Só 75 contas estão no flag e nos eventos, sem relação estatística entre eles (p = 0,65) (E04, E05).
- **Zero contas** perderam todas as assinaturas. As 352 contas com churn_event ainda têm assinaturas pagantes ativas, somando **US$ 7,14 mi de US$ 10,16 mi de MRR (70,3%)** (E04, E06).
- **28,0% do uso (4.962 de 17.690 linhas) e 27,7% dos tickets (386 de 1.395) acontecem depois da data de churn** dessas contas (E07).
- Das 53 vezes em que o evento diz "teve downgrade antes", só 8 são confirmadas pelas assinaturas (E28).

**Leitura:** o "churn" atual parece ser cancelamento ou contração de partes da conta, não perda do cliente. **Não podemos afirmar isso**, porque as datas dos eventos quase nunca coincidem com o fim de assinaturas (1% dos casos). O CEO precisa de uma definição oficial antes de qualquer meta.

### 4.2 Os dados de uso também precisam de auditoria

Mais da metade do uso registrado tem data anterior ao cadastro da conta (E13), e as assinaturas se sobrepõem em vez de se renovar (em média 10 por conta, quase todas abertas). Por isso o uso total não serve para medir crescimento, e o MRR por conta deve ser lido como peso relativo.

### 4.3 Parte da alta de encerramentos é crescimento da base

As assinaturas iniciadas por trimestre foram de 31 (1T23) para 2.069 (4T24). O percentual encerrado por trimestre de início ficou entre 8% e 11% desde 4T23 (E25). Ou seja, mais encerramentos em número absoluto não significa, por si só, pior retenção. **Ressalva:** coortes novas tiveram menos tempo para encerrar, o que pode esconder uma piora.

### 4.4 Hipóteses testadas

| Hipótese | Resultado | Código | Veredito |
|---|---|---|---|
| Churnadas tinham mais tickets/escalações antes de sair | 0,53 vs 0,52 tickets nos 90 dias anteriores (p = 0,76); escalação 5,1% vs 4,0%; resolução 35,7h vs 36,1h | E10, E11 | Descartada |
| Queda de uso antecede churn | Queda de uso válido >40%: churn 50,0% (n = 36) vs 56,8% (n = 229), p = 0,56 | E21 | Descartada |
| Erros ou features beta explicam | Erros por 100 usos nos 90 dias antes: mediana 4,29 vs 4,44 (p = 0,80); beta 10,7% vs 10,3% | E19, E21 | Descartada |
| Alguma feature piorou com o tempo | Duração por uso: nenhuma feature resiste à correção para 40 testes. Taxa de erro: **feature_9 dobrou (3,6 → 7,1 por 100 usos válidos, q = 0,03)** e feature_32 melhorou (7,4 → 4,3). Em nenhuma das duas o erro difere entre quem saiu e quem ficou | `feature_trends.csv` | Achado de produto, sem ligação com churn |
| Contas que usam menos saem mais | Diferença de uso por 30 dias some ao comparar contas com o mesmo tempo de vida | E20 | Descartada (efeito do tempo de vida) |
| Um plano, indústria, porte ou país concentra o churn | Todos p > 0,14 na taxa de churn | E22, E23 | Descartada |
| Aquisição paga traz clientes piores | **Ao contrário:** ads tem 60% de churn contra 71–75% nos demais canais, e 41% de sobrevivência em 365 dias contra 26%. Log-rank p = 0,005 (permutação p = 0,006), estável ao controlar plano, indústria, porte e país | `channel_churn_analysis.csv` | **Confirmado: ads retém mais** |
| Cobrança mensal ou auto-renovação segura mais | Nível assinatura: p = 0,49 e 0,98 | E24 | Descartada |
| O motivo declarado reflete o comportamento | "support" tem 2,78 tickets pré-churn vs 2,80 nos demais; Kruskal p ≥ 0,10 em todas as variáveis; motivo × texto de feedback p = 0,99 | E26, E27 | Descartada |
| Downgrade antecede churn | Contas com downgrade: 73,4% vs 68,7% (p = 0,32) | E28 | Descartada |
| Perder conta grande pesa mais | 70,3% do MRR vs 70,4% das contas; top 50 por MRR: 68% vs 70,7% no resto | E29 | Descartada |
| Cliente "silencioso" churna | Só 8 contas sem ticket (5 churnaram) | E12 | Não testável |
| Comportamentos preveem quem sai | AUC 0,467 (logística) e 0,479 (gradient boosting), com uso válido e sem variáveis ligadas ao tempo de vida | E31 | Descartada |
| A idade da conta prevê quem sai | Modelo de fotos mensais, testado em abr–out/2024: AUC 0,645 (IC 95% 0,59–0,70); nenhuma outra variável acrescenta | `model_results.csv` | **Confirmado** |

### 4.5 Correlação vs causalidade e limites

| Achado | O que NÃO podemos afirmar | O que falta nos dados |
|---|---|---|
| Alta generalizada de churn | Que seja piora real de retenção: pode ser efeito da definição (4.1) ou do crescimento da base (4.3) | Uma definição única de churn |
| Nenhum comportamento separa quem sai | Que não exista causa: só que as variáveis **deste dataset** não a capturam | Variáveis que o dataset não registra; as que existem não separam os grupos |
| Ads retém mais | Que ads *cause* retenção: pode refletir o perfil de quem chega por anúncio. Sem custo por canal, não dá para avaliar o retorno do investimento | Custo de aquisição por canal |
| Uso por segmento (Cybersecurity ↑, DevTools ↓) | Que seja tendência real ou que afete retenção (p de 0,13 a 0,91; churn por indústria p = 0,79) | Uso corrigido (52,9% do registrado é anterior ao cadastro) |
| Motivos de churn | Que sejam confiáveis (p = 0,99 contra o feedback) | Um registro de motivo coerente com o comentário |

**Limitação central:** o README descreve o dataset como sintético, gerado por sorteios. A ausência de padrões comportamentais é compatível com variáveis geradas de forma independente. Em dados reais eu **não** concluiria que não há causa; concluiria que a instrumentação atual não a enxerga.

---

## 5. Contas, segmentos e impacto financeiro

**Impacto financeiro.** O MRR vivo nas contas no momento do primeiro churn soma **US$ 2,91 mi**, e cresce mais rápido que o número de contas: no 4T24 foram 112 contas e **US$ 1,37 mi**, contra 80 contas e US$ 0,87 mi no 3T24. Esse é o piso. Se o MRR que as contas churnadas ainda mostram como ativo (US$ 7,14 mi) também for perdido, o impacto é cerca de 2,5 vezes maior; isso depende da definição de churn. Reembolsos somam só US$ 8.652.

**Segmentos.** Como nenhum comportamento separa quem sai, **não há segmento estatisticamente "mais em risco"**. O recorte honesto é: as **148 contas ainda sem churn_event (MRR US$ 3,02 mi)** e, dentro delas, as que acumulam sinais de alerta explícitos e auditáveis (E32):

| Sinal | Regra |
|---|---|
| Queda de uso | uso válido dos últimos 90 dias < 60% dos 90 dias anteriores |
| Escalação | ≥1 ticket escalado |
| Downgrade | ≥1 assinatura com downgrade |
| Sem nota de CSAT | tem tickets, mas nenhum avaliado |

| Grupo | Contas | MRR |
|---|---|---|
| ≥1 sinal | 79 | US$ 1,54 mi |
| **≥2 sinais (prioridade)** | **17** | **US$ 394 mil** |
| Queda de uso válido >40% (isolado) | 18 | US$ 317 mil |

Maiores contas com 2+ sinais: A-e60f9d (FinTech, US$ 50,1 mil, 2 downgrades), A-1f7acb (FinTech, US$ 46,9 mil, uso −68%, 3 downgrades), A-50f3f7 (HealthTech, US$ 44,1 mil, 1 escalação, 2 downgrades), A-d5a319 (FinTech, US$ 37,8 mil, 1 escalação, 2 downgrades), A-92a3af (Cybersecurity, US$ 34,5 mil, 1 escalação, 2 downgrades). Lista completa, com os sinais, em `at_risk_accounts.csv`.

**Importante:** esses sinais **não** previram churn nos dados (E21, E28). A lista mostra onde os sinais se concentram, não quem vai sair.

### 5.1 Modelo preditivo de churn em 90 dias

**Pergunta:** uma conta ativa hoje terá o primeiro churn nos próximos 90 dias?

**Como foi feito:**
- **Fotos mensais:** uma por mês de cada conta ativa, de abril/2023 a outubro/2024. São 2.705 fotos de 388 contas.
- **Sem informação do futuro:** em cada foto, 34 variáveis (perfil, assinaturas, MRR, uso válido, erros, tickets, satisfação) calculadas só com o que se sabia naquela data.
- **Validação temporal:** treino de abr/2023 a mar/2024 e teste de abr a out/2024. O intervalo de confiança vem de bootstrap por conta.

**Resultado no período de teste** (taxa média de churn em 90 dias: 29,4%):

| Modelo | AUC (IC 95%) | Churn nos 20% de maior risco | Lift |
|---|---|---|---|
| **Só idade da conta (modelo final)** | **0,645 (0,59–0,70)** | **45,7%** | **1,55** |
| Gradient boosting, todas as variáveis | 0,583 (0,53–0,63) | 36,7% | 1,25 |
| Gradient boosting sem a idade | 0,552 (0,50–0,60) | 33,2% | 1,13 |
| Regressão logística, todas as variáveis | 0,538 (0,48–0,59) | 30,1% | 1,02 |

- **O modelo ordena o risco.** O decil de menor risco teve 13% de churn em 90 dias e o de maior risco, 51% (`model_test_deciles.csv`).
- **Contas novas saem mais.** No teste, o churn em 90 dias foi de 50% nas contas com até 30 dias e de 18% nas com mais de um ano (`model_risk_by_age.csv`).
- **Nenhuma variável acrescenta à idade.** A melhor muda o AUC em 0,001, e indústria, auto-renovação e número de assinaturas pioram até 0,078 (`model_feature_gain.csv`).

**Previsão para 1º/01/2025** (`model_scores_2025-01-01.csv`):
- **Contas pontuadas:** as 148 ainda sem churn, com probabilidade recalibrada para a taxa dos seis meses mais recentes.
- **Esperado em 90 dias:** cerca de 42 churns e US$ 850 mil de MRR em risco.
- **Faixa de maior risco:** 16 contas.

**Limites:**
- **Probabilidades:** na mesma idade, o churn do teste foi o dobro do treino, por isso a recalibração. Ela assume que a taxa recente se mantém.
- **Causa:** a idade indica quem tem mais risco, não por quê. Ela pode estar no lugar de algo que o dataset não mede, como o onboarding.
- **Rótulo:** o churn usado é o evento da tabela `churn_events`, cuja definição ainda está em aberto.


---

## 6. O que os dados indicam fazer

Só entram aqui ações que decorrem diretamente de um achado, cada uma com o número que a sustenta. Donos, prazos e metas não estão nos dados e ficam para a empresa definir.

| # | Ação | Base nos dados | Código |
|---|---|---|---|
| 1 | **Definir uma regra única de churn** e recalcular o histórico | Fontes discordam: 110, 312 e 352 contas churnadas; nenhuma conta perdeu todas as assinaturas | E04–E06 |
| 2 | **Corrigir os registros de uso** antes de medir crescimento | 52,9% do uso registrado é anterior ao cadastro; 28% do uso das churnadas é posterior ao churn | E07, E13 |
| 3 | **Corrigir o ciclo das assinaturas** antes de medir receita por conta | 4.514 de 5.000 assinaturas abertas; 352 contas com churn seguem com US$ 7,14 mi de MRR ativo | E06 |
| 4 | **Corrigir a coleta da nota de satisfação** | 41,2% dos tickets sem nota; só notas 3, 4 e 5 | E09 |
| 5 | **Corrigir o registro do motivo de churn** | Código do motivo e comentário do cliente não batem (p = 0,99) | E27 |
| 6 | **Investigar organic e partner, não ads**, para entender o churn por canal | Sem churn em 365 dias: ads 41%, organic 25%, partner 26% (log-rank p = 0,005) | `channel_churn_analysis.csv` |
| 7 | **Estimar o risco pela idade da conta, não por comportamentos ou sinais de alerta** | Só a idade prevê (AUC 0,645 no período seguinte); comportamentos AUC 0,47–0,48; churn com queda de uso 50,0% contra 56,8% sem queda (p = 0,56) | E21, E31, `model_results.csv` |

**Cenário de exposição (cálculo, não previsão):** se a taxa do 4T24 (32,2% por trimestre) se mantiver, cerca de 48 das 148 contas retidas e US$ 0,97 mi de MRR entram em churn por trimestre.

---

## 7. Reprodutibilidade

- `build_accounts_master.sql` (PostgreSQL/Supabase) → `accounts_master.csv`
- `build_monthly_trend.py` → `monthly_trend.csv`
- `analysis_base.py` + `evidence.py` → `evidence.csv` (32 números com fonte e teste) e `at_risk_accounts.csv`
- `churn_model.py` → `model_results.csv`, `model_test_deciles.csv`, `model_risk_by_age.csv`, `model_feature_gain.csv` e `model_scores_2025-01-01.csv`
- Testes: qui-quadrado (categóricas), Mann-Whitney e Kruskal-Wallis (numéricas), log-rank com teste de permutação (sobrevivência por canal), validação cruzada 5-fold (modelo transversal) e validação temporal com bootstrap por conta (modelo de fotos mensais). Os p-valores não têm correção para múltiplos testes, exceto na análise por feature (Benjamini-Hochberg). Com ~30 testes, esperaríamos 1 ou 2 "significativos" por acaso. Apareceram dois: o de uso por 30 dias, que some ao controlar o tempo de vida, e o de canal (ads), que se mantém após a correção de Bonferroni para 5 canais (p = 0,024).
