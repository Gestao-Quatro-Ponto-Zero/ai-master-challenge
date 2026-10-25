# Submissão — Arthur Lima — Challenge 003: Lead Scorer

## Sobre mim

- **Nome:** Arthur Lima
- **LinkedIn:** [linkedin.com/in/arthur-roleite](https://www.linkedin.com/in/arthur-roleite)
- **Challenge escolhido:** `Challenge 003 — Lead Scorer (Build / Vendas & RevOps)`
- **Repositório da Solução:** `submissions/arthur-lima/solution/`

---

## ⚡ Como Rodar a Solução em 1 Comando

A aplicação é **autônoma** e já contém todos os 4 CSVs oficiais em `solution/data/`.

### No Windows:
Basta dar dois cliques ou executar no terminal dentro da pasta `solution`:
```cmd
cd submissions/arthur-lima/solution
run.bat
```
*(O script verifica o ambiente Python 3.10+, cria e ativa o venv, instala os requisitos exatos de `requirements.txt`, executa os 17 testes do pytest e abre o painel executivo em http://localhost:8501).*

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
*Acesse no navegador:* **`http://localhost:8501`**

---

## Executive Summary

Auditamos as 8.800 oportunidades históricas do CRM e diagnosticamos o gargalo operacional da equipe comercial: a priorização manual por valor nominal ou por idade isolada falha em discriminar vitória (AUC ~0,49 a 0,50), enquanto mais de 87% das oportunidades abertas encontram-se estagnadas há meses consumindo tempo dos 35 vendedores. Desenvolvemos o **RevOps Copilot**, uma ferramenta operacional pragmática estruturada em duas esteiras independentes (1.589 deals em `Engaging` para Closers e 500 leads em `Prospecting` para SDRs), orientada por **Velocidade de Receita ($EV/Dia$)**, **Penalização Contínua de Estagnação** e **Explicabilidade Comercial com SLA**. Em validação de coorte prospectiva point-in-time em 30/06/2017 (970 negócios com desfecho resolvido e 716 censurados), a ferramenta comprova que o ganho real de RevOps não advém de predições místicas de caixa-preta, mas da eliminação sistemática de negócios zumbis e da disciplina na execução comercial na segunda-feira às 8h00.

---

## Solução

### Abordagem

Abordamos o desafio sob a ótica de quem precisa resolver a dor real de gestão comercial do G4:

1. **Auditoria Forense dos Dados & Sanitização de Schemas:**
   - **Correção de Chave Estrangeira:** O produto `GTXPro` em `sales_pipeline.csv` não possuía espaço, rompendo o join relacional com `GTX Pro` em `products.csv`. Normalizamos o catálogo para restaurar a integridade de preços.
   - **Correção Cadastral:** Corrigimos o erro de digitação de setor (`technolgy` -> `technology`) em `accounts.csv`.
   - **Identificação de Contas Órfãs:** Identificamos que **68,5% das oportunidades abertas em `Engaging` (1.088 de 1.589)** e **67,4% em `Prospecting` (337 de 500)** não possuem conta corporativa vinculada no CRM. Em vez de descartá-las ou imputar dados fictícios, criamos um indicador explícito de gap cadastral e atribuímos um desconto operacional preventivo, orientando o vendedor a enriquecer a conta antes de aprofundar a negociação.
2. **Estimativa de Valor sem Vazamento de Dados (Anti-Leakage):**
   - Deals abertos não possuem `close_value`. Estimamos o valor esperado de fechamento através da **mediana histórica de vitórias por (produto, escritório regional)** calculada estritamente com dados passados, com fallback limpo para o catálogo geral em caso de histórico vazio.
3. **Curva Contínua de Maturação & Gestão de Estagnação:**
   - A análise empírica dos negócios revelou uma dinâmica não-linear: negócios com até 14 dias apresentam taxas de vitória menores (~53-57%) devido à desqualificação precoce de leads sem perfil; entre 14 e 60 dias ocorre o ápice de maturação e negociação ativa (~68%); e além do ciclo mediano (~57 dias) o risco de estagnação cresce progressivamente.
   - Substituímos regras arbitrárias de corte rígido por uma função contínua e suave, instituindo o alerta operacional de **`Zombie Suspect`** para oportunidades que ultrapassam o percentil 95 da coorte (~118 dias).
4. **Métrica de Velocidade de Receita ($EV/Dia$):**
   - Para equilibrar a dispersão de 486x entre os produtos (\$55 a \$26.768), dividimos o Valor Esperado Monetário ($EV = P \times \text{Valor}$) pela estimativa contínua de dias restantes no ciclo, evitando que um único contrato gigante monopolize a atenção da equipe em detrimento de contratos rápidos e lucrativos.
5. **Divisão Operacional em Duas Esteiras:**
   - **Aba 1 (Closers / `Engaging`):** 1.589 oportunidades abertas com ranking de prioridade (0-100), 3 motivos comerciais, próximo passo tático com SLA, scripts de abordagem e botão para registrar discordâncias e contexto de campo.
   - **Aba 2 (SDRs / `Prospecting`):** 500 leads sem `engage_date`, ranqueados por Fit ICP de conta/produto para triagem de 1º contato.

---

### Resultados / Findings

#### 1. Avaliação de Coorte Prospectiva Point-in-Time (Sem Vazamento Futuro)

Para medir o comportamento real do motor sem qualquer vazamento de datas de fechamento (`close_date`), construímos uma validação prospectiva na data de corte **30/06/2017**:
- **Treino Passado:** Todos os 2.679 negócios já fechados em ou antes de 30/06/2017 (onde o motor aprendeu as taxas e medianas).
- **População de Teste em 30/06:** Exatamente as **1.686 oportunidades abertas naquele dia**, utilizando sua idade observável no corte: `(30/06/2017 - engage_date).days`.
- **Desfecho:** 970 negócios tiveram desfecho fechado resolvido até o encerramento do dataset (609 Won e 361 Lost), enquanto 716 negócios permaneceram abertos (censurados à direita).

Avaliando o modelo e os 3 baselines com **alinhamento estrito linha a linha sobre a mesma população de 970 negócios**:

| Estratégia / Modelo | AUC-ROC | Brier Score | Lift @ Top 10% | Lift @ Top 20% | Precisão @ Top 20% | Receita Observada no Top 20% |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **🎯 RevOps Survival Engine (Nosso)** | **0,5021** | **0,2398** | **0,94x** | **0,96x** | **60,3%** | **US$ 625.063,00** |
| Baseline 1: Valor Nominal (`sales_price`) | 0,4916 | N/A | 1,10x | 1,01x | 63,4% | US$ 810.210,00 |
| Baseline 2: Aging (-cycle_days no corte) | 0,5011 | N/A | 0,92x | 0,90x | 56,7% | US$ 598.440,00 |
| Baseline 3: Média Histórica do Vendedor | 0,5070 | 0,2355 | 1,10x | 1.05x | 66,0% | US$ 720.150,00 |

*Diagnóstico Honesto de RevOps:*
- **Limitação Intrínseca do CRM:** Os dados estáticos do CRM (sem logs diários de WhatsApp, e-mail ou reuniões) possuem poder preditivo de discriminação modesto (AUC ~0,50 a 0,51 em dados prospectivos não contaminados). Qualquer alegação de AUC > 0,80 nesse dataset decorre de vazamento de target ou sobreajuste in-sample.
- **Papel Real da Ferramenta:** O valor da solução não reside em "adivinhar o futuro", mas em **organizar o funil de vendas**: ao categorizar 87,4% dos negócios ativos como candidatos a higienização de pipeline e destacar os deals com maior yield diário, o software evita a inércia comercial e orienta a rotina semanal de gestão.

#### 2. Matriz de Ação Tática

A carteira de 1.589 negócios ativos foi segmentada em 3 ações operacionais:
- 🚀 **Acelerar Fechamento (47 deals):** Negócios em janela de maturação com alto rendimento esperado por dia.
- 🛠️ **Intervenção de Resgate (153 deals):** Negócios acima da mediana do ciclo que demandam toque de patrocinador executivo (*Executive Sponsor Touch*).
- 🧹 **Higienizar / Auditar Zombie (1.389 deals):** Negócios que ultrapassaram a janela P95 de ciclo (~118 dias), candidatos a envio de e-mail de encerramento amigável (*break-up pitch*) para liberar a atenção da equipe.

---

### Recomendações

1. **Instituir a Cerimônia de Higienização de Pipeline na Segunda-feira:**
   A gestão de vendas deve utilizar o filtro de *Zombie Suspects* no início de cada semana para despachar e-mails de encerramento ou arquivar formalmente negócios estagnados há mais de 4 meses, impedindo a poluição visual do CRM.
2. **Impor Validação Obrigatória de Contas no CRM:**
   Como 68,5% das oportunidades abertas não possuem cliente cadastrado, RevOps deve bloquear o avanço de deals sem CNPJ/razão social preenchidos.
3. **Acompanhar a Velocidade de Receita ($EV/Dia$):**
   Substituir a cobrança puramente baseada no valor bruto do pipeline pela métrica de velocidade esperada diária, incentivando fechamentos ágeis.
4. **Auditar Semanalmente as Discordâncias de Campo:**
   Analisar os registros salvos em `artifacts/feedback_overrides.json` para mapear motivos reais de perda relatados pelos vendedores (ex.: agressividade de concorrente ou congelamento de budget).

---

### Limitações

1. **Ausência de Telemetria de Atividades no CRM:**
   O dataset registra apenas datas macro (`engage_date`, `close_date`). Sem histórico de ligações, e-mails ou mensagens trocadas, o modelo não consegue capturar o engajamento recente do cliente.
2. **Censura à Direita no Término do Dataset:**
   O registro histórico encerra em 31/12/2017 com 1.589 negócios ainda abertos. Em produção com CRM contínuo, a taxa de sobrevivência deve ser reestimada periodicamente com desfechos atualizados.
3. **Métrica Observacional de Receita:**
   A receita somada no Top 20% reflete o volume dos negócios históricos selecionados; ganhos incrementais causais exigem a realização de testes A/B controlados em campo.

---

## Process Log — Como Usei IA

> O log detalhado de todo o ciclo de desenvolvimento, iterações e auditorias encontra-se no arquivo dedicado:  
> 🔗 **[`PROCESS_LOG.md`](./PROCESS_LOG.md)** e **[`process-log/adversarial-red-team-audit.md`](./process-log/adversarial-red-team-audit.md)**.

### Resumo das Ferramentas & Harness:
- **Antigravity / Claude Code:** Construção modular em Python, TDD com 17 testes automatizados no pytest, normalização de dados e interface Streamlit.
- **DeepSeek API (Persona Red Team CRO / Principal AI Architect):** Primeira sabatina adversarial sobre premissas estatísticas, desmascarando a falácia do corte rígido de 138 dias e a distorção de preços.
- **Codex / Auditoria Independente Pré-Submissão:** Segunda sabatina crítica que identificou o vazamento sutil de `close_date` no backtest anterior, desalinhamento de arrays nos baselines e necessidade de continuidade matemática estrita.

### Principais Correções Humanas sobre Sugestões da IA:
- Rejeitamos modelos demográficos com `sector` e `regional_office` (AUC ~0,50 — ruído puro).
- Eliminamos o corte arbitrário de 138 dias, substituindo por curva contínua e flag operacional de zombie.
- Corrigimos o vazamento temporal de `cycle_days` no backtest, ancorando a idade estritamente na data de corte prospectiva.
- Consertamos o alinhamento posicional dos baselines, garantindo comparações reproduzíveis sobre os mesmos IDs.
- Corrigimos a falha silenciosa de chave estrangeira em `GTXPro`.

---

## Evidências

- [x] **Suíte de Testes Automatizados:** 17 testes unitários e de anti-leakage em `tests/test_engine.py` (executados com `python -m pytest tests/test_engine.py -v` — 100% passando).
- [x] **Relatório de Backtest Alinhado:** Gerado automaticamente em `solution/artifacts/backtest_report.md`.
- [x] **Auditoria Adversarial do Red Team:** Documentada em `process-log/adversarial-red-team-audit.md`.
- [x] **Aplicação Executiva Interativa:** Disponível em `solution/app.py` com suporte a Windows (`run.bat`) e macOS/Linux (`run.sh`).
- [x] **Dados Pré-Carregados:** Todos os 4 CSVs oficiais incluídos em `solution/data/` para execução sem necessidade de downloads externos.

---

*Submissão enviada em: 25 de Outubro de 2026 por Arthur Lima.*
