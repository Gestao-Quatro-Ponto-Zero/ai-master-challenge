# Submissão — Arthur Lima — Challenge 003: Lead Scorer

## Sobre mim

- **Nome:** Arthur Lima
- **LinkedIn:** [linkedin.com/in/arthur-roleite](https://www.linkedin.com/in/arthur-roleite)
- **Challenge escolhido:** `Challenge 003 — Lead Scorer (Build / Vendas & RevOps)`
- **Repositório da Solução:** `submissions/arthur-lima/solution/`

---

## ⚡ Como Rodar a Solução em 1 Comando

A aplicação é autônoma e já inclui os 4 CSVs oficiais do desafio em `solution/data/`.

### No Windows:
```cmd
cd submissions/arthur-lima/solution
run.bat
```
*(Cria/ativa `venv`, instala `requirements.txt`, executa os 13 testes automatizados de mutação/invariância/UI com `pytest` e inicia o painel em `http://localhost:8501`).*

### No macOS / Linux:
```bash
cd submissions/arthur-lima/solution
chmod +x run.sh
./run.sh
```

### Execução Manual:
```bash
cd submissions/arthur-lima/solution
pip install -r requirements.txt
python -m pytest tests/test_engine.py -v
streamlit run app.py
```

---

## Executive Summary

Definimos uma pergunta operacional explícita para o time comercial: **diante de todas as oportunidades abertas em `Engaging` hoje na fila do vendedor, quais priorizar para maximizar a receita fechada (`Won`) nos próximos 90 dias?** A auditoria das 8.800 linhas do CRM revelou três fatos estruturais: (1) os escritórios `East` e `West` não utilizam o estágio `Prospecting` (`0` deals contra `500` em `Central`) e acumulam negócios abandonados diretamente em `Engaging` (`1.372` dos `1.589` abertos já ultrapassam 120 dias); (2) `100%` dos negócios fechados (`4.238 Won` e `2.473 Lost`) possuem `account` preenchido contra `31,5%` em `Engaging`, indicando que a conta é vinculada até o fechamento e não deve ser usada como preditor histórico sob pena de *snapshot leakage*; e (3) após uma primeira versão super-parametrizada não superar o baseline na subpopulação resolvida (`Won` vs `Lost`), **simplificamos o motor** para `EV_90d = P_90d(idade, vendedor) × Ticket_Mediano`, separando estimativa estatística de regras operacionais de higiene cadastral. Na avaliação *out-of-time* sobre a **fila aberta completa** em três cortes independentes (`31/07`, `31/08` e `30/09/2017`, horizonte de +90 dias sem censura), o Top 20% ordenado por `EV_90d` captura **60,1% a 63,7% da receita realizada no trimestre** (contra `47,6%–49,9%` do preço nominal e `10,7%–46,2%` da idade pura), enquanto no recorte condicional apenas entre deals já resolvidos (`Won` vs `Lost`) todos os atributos estáticos permanecem em **AUC ~0,49–0,51** — delimitando com transparência onde os dados geram valor e onde atingem seu teto informativo.

---

## Solução

### 1. Auditoria Empírica do CRM & Saneamento de Dados (`src/data_loader.py`)

- **Correção de Chave Estrangeira (`GTXPro` → `GTX Pro`):** `1.480` linhas em `sales_pipeline.csv` grafavam `GTXPro` sem espaço, quebrando o join com `products.csv`. Corrigimos também `technolgy` → `technology` em `accounts.csv`.
- **Artefato de Fechamento em `account` (`0` ausentes em fechados vs. `1.425` em abertos):** Como `Won` e `Lost` têm `0%` de ausência de `account`, a falta de conta em `1.088` deals `Engaging` e `337` `Prospecting` reflete estágio cadastral pré-fechamento. Por isso, **excluímos `account` do cálculo de `P_90d`** (evitando *snapshot leakage* e penalidades arbitrárias) e a tratamos como tarefa explícita de higiene cadastral (`crm_hygiene_status`).
- **Assimetria Regional de Funil e Vendedores:** `100%` dos `500` leads em `Prospecting` pertencem ao escritório `Central`. Além disso, dos `35` nomes em `sales_teams.csv`, `30` possuem histórico em `sales_pipeline.csv` e `5` não possuem registros. O acúmulo desigual de deals mortos em `Engaging` distorce o win rate fechado ingênuo `Won / (Won + Lost)` de vendedores que não dão baixa como `Lost`.
- **Estimativa Point-in-Time de Ticket (`expected_won_value`):** Mediana histórica de `close_value` dos negócios `Won` por `(produto, escritório)` fechados estritamente até `as_of_date` (fallback para preço de catálogo quando não há histórico).

### 2. Separação Estrita entre Estimativa Estatística e Regras Operacionais (`src/survival_and_scoring.py`)

| Camada | Natureza | Como Funciona |
| :--- | :--- | :--- |
| **`p_win_90d` e `ev_90d`** | **Estimativa Estatística** (validada *out-of-time*) | Aprende a taxa empírica de conversão em +90 dias por faixa de idade em snapshots semanais históricos cujas janelas de 90 dias já se encerraram até `as_of_date` (interpolação linear contínua, suavização Empirical Bayes `m=20`), multiplicada por ajuste moderado do vendedor (`m=50`) e pelo `expected_won_value`. |
| **`crm_hygiene_status`** | **Regra de Governança Cadastral** | Sinaliza `⚠️ Sem Conta (Enriquecer CRM)` para preenchimento obrigatório antes da proposta final, **sem alterar `p_win_90d`**. |
| **`action_tier` (`Engaging`)** | **Regra Operacional de Triagem** | Classifica a fila pela idade frente aos marcos históricos de `Won` do produto: `🚀 Priorizar (<= Mediana ~57d)`, `🛠️ Revisar Gargalo (Mediana–P95)` e `🧹 Higienizar (>P95 ~116d)`. |
| **Overrides de Campo (`app.py`)** | **Intervenção Humana Funcional** | Permite ao vendedor promover (`⬆️`), pausar (`⏸️`) ou arquivar (`🗑️`) negócios na fila operacional em tempo real (`artifacts/feedback_overrides.json`), mantendo `p_win_90d` e `ev_90d` originais visíveis e inalterados. |
| **Triagem `Prospecting` (`500` leads)** | **Regra Determinística** (não-probabilística) | Como não há `engage_date` nem log de descarte pré-contato no CRM, ordena de forma transparente por prontidão cadastral (`has_account`) e `expected_won_value`, sem inventar probabilidades não-verificáveis. |

---

## Resultados / Findings (`src/backtest.py`)

Publicamos **dois regimes complementares de avaliação** (com desempate neutro por `opportunity_id` e zero vazamento futuro, verificados por teste de mutação):

### Regime 1 — Avaliação Operacional Primária: Fila Aberta Completa no Corte (Horizonte +90 Dias, Sem Censura)

Avalia **todas** as oportunidades abertas em `Engaging` disponíveis ao vendedor em três datas de corte mensais (`31/07/2017`, `31/08/2017` e `30/09/2017` — todas com janela futura completa de 90 dias até `31/12/2017`):

| Corte Out-of-Time | Estratégia | AUC (`P_90d`) | Brier | Lift @ Top 20% | Receita no Top 20% (Fila Global) | Receita no Top 20% (Intra-Vendedor) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **`2017-07-31`**<br>(`N = 2.257` abertos) | **🎯 EV_90d (Idade + Vendedor × Ticket)** | **0,7209** | **0,2046** | **1,31x** | **US\$ 1.033.856 (60,1%)** | **US\$ 1.030.733 (59,9%)** |
| | 🔬 Ablação: EV_90d (Apenas Idade × Ticket) | 0,7503 | 0,2043 | 1,31x | US\$ 1.033.818 (60,1%) | US\$ 1.030.733 (59,9%) |
| | Baseline 1: Preço Nominal (`sales_price`) | 0,5086 | N/A | 1,05x | US\$ 857.458 (49,9%) | US\$ 828.223 (48,2%) |
| | Baseline 2: Frescor (`-idade` no corte) | 0,5581 | N/A | 0,49x | US\$ 183.140 (10,7%) | US\$ 314.570 (18,3%) |
| | Baseline 3: Win Rate Fechado do Vendedor | 0,4945 | 0,3170 | 1,01x | US\$ 272.678 (15,9%) | N/A (constante por rep) |
| **`2017-08-31`**<br>(`N = 2.265` abertos) | **🎯 EV_90d (Idade + Vendedor × Ticket)** | **0,6556** | **0,1860** | **1,36x** | **US\$ 790.036 (60,9%)** | **US\$ 785.445 (60,5%)** |
| | 🔬 Ablação: EV_90d (Apenas Idade × Ticket) | 0,6593 | 0,1862 | 1,36x | US\$ 789.714 (60,8%) | US\$ 785.445 (60,5%) |
| | Baseline 1: Preço Nominal (`sales_price`) | 0,5105 | N/A | 1,07x | US\$ 635.562 (49,0%) | US\$ 580.894 (44,7%) |
| | Baseline 2: Frescor (`-idade` no corte) | 0,5974 | N/A | 1,41x | US\$ 339.496 (26,1%) | US\$ 333.123 (25,7%) |
| | Baseline 3: Win Rate Fechado do Vendedor | 0,5234 | 0,3258 | 1,12x | US\$ 299.234 (23,1%) | N/A (constante por rep) |
| **`2017-09-30`**<br>(`N = 2.409` abertos) | **🎯 EV_90d (Idade + Vendedor × Ticket)** | **0,6253** | **0,1756** | **1,37x** | **US\$ 776.685 (63,7%)** | **US\$ 701.740 (57,5%)** |
| | 🔬 Ablação: EV_90d (Apenas Idade × Ticket) | 0,6133 | 0,1754 | 1,36x | US\$ 773.270 (63,4%) | US\$ 701.740 (57,5%) |
| | Baseline 1: Preço Nominal (`sales_price`) | 0,4880 | N/A | 0,98x | US\$ 580.662 (47,6%) | US\$ 546.305 (44,8%) |
| | Baseline 2: Frescor (`-idade` no corte) | 0,8265 | N/A | 2,14x | US\$ 564.032 (46,2%) | US\$ 551.774 (45,2%) |
| | Baseline 3: Win Rate Fechado do Vendedor | 0,4925 | 0,3509 | 0,90x | US\$ 227.784 (18,7%) | N/A (constante por rep) |

**O que a ablação comprova:** praticamente todo o ganho de captura de receita (`+10` a `+16` pontos percentuais sobre o Preço Nominal, tanto na fila global quanto dentro da carteira de cada vendedor) vem da **combinação simples entre a curva empírica de conversão por idade e o ticket mediano do produto**; o fator do vendedor atua apenas como critério fino de desempate entre carteiras (`+0,0%` a `+0,3%`).

### Regime 2 — Diagnóstico Condicional: Subpopulação Resolvida (`Won` vs `Lost`, `N = 970` em `30/06/2017`)

Quando removemos *a posteriori* os `716` negócios que permaneceram abertos sem fechar e avaliamos apenas os `970` negócios que efetivamente chegaram a `Won` (`609`) ou `Lost` (`361`):

| Estratégia (Subconjunto `Won` vs `Lost`) | AUC-ROC | Brier | Lift @ Top 20% | Precisão @ Top 20% |
| :--- | :---: | :---: | :---: | :---: |
| Motor `EV_90d` | 0,4879 | N/A | 1,03x | 64,4% |
| Baseline 1: Preço Nominal (`sales_price`) | 0,4916 | N/A | 1,02x | 63,9% |
| Baseline 2: Frescor (`-idade` no corte) | 0,5011 | N/A | 0,90x | 56,7% |
| Baseline 3: Win Rate Fechado do Vendedor | 0,5067 | 0,2352 | 1,04x | 65,5% |

**Interpretação objetiva:** uma vez eliminados os negócios estagnados usando informação futura de quem fechou, os campos estáticos disponíveis neste CRM não distinguem vitória de derrota entre negociações ativas (`AUC ~0,49–0,51`). Logo, o motor **não** substitui o contexto qualitativo do vendedor em negociações vivas — ele evita que a atenção comercial seja drenada pelo passivo acumulado em `Engaging` e pondera os negócios ativos pelo retorno esperado.

---

## Recomendações

1. **Padronizar o estágio `Prospecting` e a baixa de `Lost` em `East` e `West`:** eliminar a assimetria operacional em relação ao escritório `Central`, exigindo revisão quinzenal de negócios acima do P95 de ciclo (`~116` dias).
2. **Tornar `account` obrigatório na passagem para proposta comercial:** sanear os `1.088` registros sem conta em `Engaging` como rotina de qualidade cadastral, sem misturar falta de preenchimento com probabilidade estatística.
3. **Instrumentar telemetria de interações no CRM:** registrar data do último contato bidirecional, reuniões realizadas e envio de proposta para superar o teto de `AUC ~0,51` observado na subpopulação condicional `Won` vs `Lost`.
4. **Validar impacto causal em campo antes de automatizar bloqueios:** os ganhos de captura de receita no Top 20% são observacionais sobre coortes históricas; ganhos incrementais reais de receita exigem teste controlado por carteira/equipe.

---

## Limitações

1. **Sem telemetria de esforço ou atividades comerciais:** `EV_90d` mede receita esperada no horizonte de 90 dias corridos, não retorno por hora de trabalho do vendedor.
2. **Sem histórico de transição pré-contato em `Prospecting`:** os `500` registros em `Prospecting` não permitem estimar probabilidade empírica de qualificação; a Aba 2 opera estritamente como fila determinística de triagem.
3. **Recalibração automática ainda não acoplada aos overrides:** os overrides do vendedor reordenam imediatamente a fila operacional e ficam auditados em JSON, mas não reestimam os pesos estatísticos de `P_90d` automaticamente sem desfechos fechados verificados.

---

## Process Log — Como Usei IA

> O registro completo das iterações, falhas intermediárias, auditorias independentes e atribuição de autoria está em:  
> 🔗 **[`PROCESS_LOG.md`](./PROCESS_LOG.md)** e **[`process-log/adversarial-red-team-audit.md`](./process-log/adversarial-red-team-audit.md)**.

---

## Evidências

- [x] **Suíte de Testes de Mutação, Invariância, Paridade e UI (`13` testes):** `python -m pytest tests/test_engine.py -v` (testa corrupção deliberada de dados futuros, separação entre `account` e `P_90d`, permutação de linhas, paridade lote vs. simulador, reordenação funcional por override e renderização completa das 4 abas via `Streamlit AppTest`).
- [x] **Relatório Reprodutível dos Dois Regimes + Ablação:** [`solution/artifacts/backtest_report.md`](./solution/artifacts/backtest_report.md).
- [x] **Aplicação Interativa Executável em 1 Comando:** [`solution/app.py`](./solution/app.py), `run.bat` e `run.sh`.
