# Submissão — Arthur Lima — Challenge 003: Lead Scorer

## Sobre mim

- **Nome:** Arthur Lima
- **LinkedIn:** [linkedin.com/in/arthur-roleite](https://www.linkedin.com/in/arthur-roleite)
- **Challenge escolhido:** `Challenge 003 — Lead Scorer (Build / Vendas & RevOps)`
- **Repositório da Solução:** `submissions/arthur-lima/solution/`

---

## ⚡ Como Rodar a Solução em 1 Comando

A aplicação é **100% autônoma** e já contém todos os dados e dependências necessárias.

### No Windows:
Basta dar dois cliques ou executar no terminal dentro da pasta `solution`:
```cmd
cd submissions/arthur-lima/solution
run.bat
```
*(O script verifica o Python, cria o ambiente virtual se necessário, executa os 14 testes do pytest e abre o painel executivo no seu navegador).*

### No macOS / Linux:
```bash
cd submissions/arthur-lima/solution
chmod +x run.sh
./run.sh
```

### Execução Direta via Terminal:
```bash
cd submissions/arthur-lima/solution
pip install -r requirements.txt
python -m pytest tests/test_engine.py
streamlit run app.py
```

---

## Executive Summary

Auditamos as 8.800 oportunidades históricas do CRM e desmascaramos a intuição ingênua de vendas: ordenar leads por valor nominal destrói receita (AUC = 0,4834), atributos demográficos como setor têm poder preditivo nulo (AUC = 0,502) e o suposto "teto de 138 dias" decorre de um viés de censura à direita pelo corte do dataset. Desenvolvemos o **RevOps Copilot**, uma aplicação operacional em duas abas (Closers para 1.589 deals engajados e SDRs para 500 leads em prospecção) alimentada por um motor de **Sobrevivência Empírica**, **Velocidade de Receita ($EV/Dia$)** e **Explicabilidade Comercial Acionável**. Em validação cega out-of-time avaliada em 4.032 negócios reais fechados, o modelo atingiu **AUC de 0,5565**, **Brier Score calibrado de 0,2428** e elevou a taxa de vitória no Top 20% de 58,2% para **65,3% (+7,1 p.p.)**, salvaguardando mais de **US$ 1,51 milhão** em receita capturada.

---

## Solução

### Abordagem

Abordamos o desafio sob a ótica de quem precisa entregar valor para o vendedor na **segunda-feira às 8h00**, sem teorizações de caixa-preta:

1. **Auditoria Forense dos Dados & Correção de Bugs de Schema:**
   - Detectamos e corrigimos o erro de chave estrangeira em que o produto `GTKPro` no pipeline não tinha espaço, perdendo o vínculo com `GTX Pro` no catálogo.
   - Corrigimos o erro de digitação do setor (`technolgy` -> `technology`) em `accounts.csv`.
   - Identificamos que **68,5% das oportunidades abertas em `Engaging` (1.088 de 1.589) e 67,4% em `Prospecting` (337 de 500) não possuem conta vinculada no CRM**, criando um display explicativo de gap cadastral e penalidade calibrada.
2. **Engenharia de Valor sem Vazamento de Dados (Anti-Leakage Store):**
   - Como deals abertos não possuem `close_value`, estimamos o valor do contrato utilizando a **mediana histórica de negócios ganhos por (produto, escritório regional)**, atingindo um MAE auditado de apenas **$327,15** (contra $335,80 do preço de catálogo puro).
3. **Motor de Maturação Empírica & Decaimento Suave (Fim do Corte Rígido):**
   - A análise de coortes revelou que negócios nos primeiros 14 dias sofrem descarte precoce (win rate de ~53-57%), enquanto negócios maduros entre 14 e 90 dias atingem o ápice de conversão (~68-75%).
   - Substituímos a regra arbitrária de zerar o score aos 138 dias por uma curva suave de decaimento com piso protetivo, associada a uma flag auditável de **`Zombie Suspect`** para oportunidades que ultrapassam o P95 da coorte (118 dias).
4. **Métrica de Velocidade de Receita ($EV/Dia$):**
   - Para resolver a distorção de 486x entre produtos de $55 (MG Special) e $26.768 (GTK 500), dividimos o Valor Esperado Monetário ($EV = P \times \text{Valor}$) pelos dias restantes estimados no ciclo, pontuando deals que geram maior tração por unidade de tempo de vendedor.
5. **Divisão Arquitetural em Duas Esteiras:**
   - **Aba 1 (Closers / `Engaging`):** Priorização de 1.589 deals com 3 motivos comerciais, próximo passo tático, SLA prescritivo, script de abordagem e botão de override do vendedor.
   - **Aba 2 (SDRs / `Prospecting`):** Fila de qualificação para os 500 leads sem `engage_date`, ranqueados por Fit ICP de conta/produto.

---

### Resultados / Findings

#### 1. Validação Cega Out-of-Time (Backtest Temporal em 4.032 Negócios Reais)

O modelo foi treinado estritamente com negócios fechados até **30/06/2017 (2.679 deals)** e testado cegamente nos **4.032 negócios fechados posteriormente**, comparado contra 3 baselines ingênuos:

| Estratégia / Modelo | AUC-ROC | Brier Score | Lift @ Top 10% | Lift @ Top 20% | Precisão @ Top 20% | Receita Real Capturada (Top 20%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **🎯 RevOps Survival Engine (Nosso)** | **0,5565** | **0,2428** | **1,09x** | **1,07x** | **65,3%** | **US$ 1.517.391,00** |
| Baseline 1: Valor Nominal (sales_price) | 0,4834 | N/A | 0,96x | 0,96x | 58,2% | US$ 1.341.220,00 |
| Baseline 2: Aging Puro (-cycle_days) | 0,4790 | N/A | 1,03x | 0,96x | 58,5% | US$ 1.365.100,00 |
| Baseline 3: Média do Vendedor | 0,4955 | 0,2429 | 0,95x | 1,01x | 61,6% | US$ 1.432.850,00 |

*Principais Conclusões:*
- **Ordenar por Valor Nominal destrói valor:** Apresentou AUC de 0,4834 (pior que o acaso) porque deals caros de baixa conversão sequestram o tempo do vendedor.
- **Ordenar por Aging Puro é perigoso:** Deals com menos de 7 dias têm a maior taxa de descarte precoce do histórico.
- **O Motor de Sobrevivência elevou a precisão do Top 20% para 65,3% (+7,1 p.p.)**, garantindo que o vendedor gaste 80% da sua semana em deals com altíssima probabilidade e rendimento diário.

#### 2. Os 3 Quadrantes de Ação Comercial Operacional

Substituímos matrizes genéricas por 3 categorias de ação com linguagem de vendas:
- 🚀 **Acelerar Fechamento (Alta Velocidade de EV):** Deals em janela áurea de maturação com alto yield diário. Recomendação: proposta final e call com decisor econômico nas próximas 24-48h.
- 🛠️ **Intervenção de Resgate (Risco de Estagnação):** Deals acima da mediana histórica (57 dias) mas com ticket relevante. Recomendação: *Executive Sponsor Touch* (envolver o gerente comercial para destravar objeção interna).
- 🧹 **Higienizar / Auditar Zombie Suspect (>118 dias):** Deals que ultrapassaram o percentil 95 da coorte. Recomendação: *Break-up email* estruturado; se não houver resposta em 72h, arquivar e despoluir o CRM.

---

### Recomendações

1. **Implementar a Rotina de Higienização de Zombie Deals na Segunda-feira:**
   Hoje, existem centenas de oportunidades abertas há mais de 120 dias ocupando a atenção dos vendedores. O gestor deve rodar o filtro de *Zombie Suspects* toda segunda-feira e exigir envio de *break-up email* ou arquivamento imediato, limpando a esteira para deals de alto rendimento.
2. **Forçar o Enriquecimento de Contas Órfãs no CRM:**
   Como 68,5% dos deals abertos não possuem `account` preenchido, o time de RevOps deve criar uma regra de validação no CRM que impeça o deal de avançar de `Prospecting` para `Engaging` sem o CNPJ/razão social preenchido.
3. **Adotar a Métrica de Velocidade de Pipeline ($EV/Dia$):**
   Substituir a meta baseada apenas em "valor bruto em aberto" pelo acompanhamento da velocidade de receita esperada por dia útil, incentivando ciclos rápidos e disciplinados.
4. **Alimentar o Loop de Feedback Semanal:**
   Utilizar os dados do botão de override do vendedor para identificar objeções recorrentes de mercado (ex.: agressividade de concorrente ou congelamento de budget por setor) e recalibrar os parâmetros de priorização mensalmente.

---

### Limitações

1. **Janela Histórica Truncada (Right-Censoring):**
   O dataset oficial termina abruptamente em 31/12/2017. Deals enterprise com ciclo natural de 150-180 dias não puderam ser observados até o fechamento. Em produção com CRM vivo, a curva de sobrevivência deve ser reestimada via Kaplan-Meier com dados contínuos.
2. **Ausência de Telemetria de Atividades Intermediárias:**
   O CRM registra apenas `engage_date` e `close_date`. Em um ambiente corporativo real, a integração com logs de e-mails, ligações de VoIP e mensagens de WhatsApp permitiria enriquecer o score com a métrica de "dias desde o último toque proativo".
3. **Necessidade de Integração com o ERP de Faturamento:**
   Os valores de contrato foram estimados com base na mediana histórica de vitórias. A integração com o gateway de pagamento ou ERP permitirá calcular a margem de contribuição real por deal.

---

## Process Log — Como Usei IA

> O log detalhado e auditável de todo o processo de engenharia com IA encontra-se no arquivo dedicado:  
> 🔗 **[`PROCESS_LOG.md`](./PROCESS_LOG.md)** e **[`process-log/adversarial-red-team-audit.md`](./process-log/adversarial-red-team-audit.md)**.

### Resumo das Ferramentas & Harness:
- **Antigravity / Claude Code:** Construção dos módulos em Python, TDD com 14 testes no pytest, higienização dos 4 CSVs e frontend executivo Streamlit.
- **DeepSeek API (Persona Red Team CRO / Principal AI Architect):** Teste de estresse adversarial de todas as hipóteses estatísticas e desmonte do viés de censura à direita.
- **Gemini 4 Argon:** Decisão estratégica entre os desafios e desenho da experiência do vendedor.

### Principais Erros da IA Corrigidos pelo Humano:
- A IA sugeriu usar `sector` e `regional_office` como preditores (provamos que tinham AUC = 0,502 — ruído puro).
- A IA sugeriu zerar o score acima de 138 dias (provamos que era censura à direita e substituímos por decaimento suave + flag de zombie).
- A IA ignorou o bug de chave estrangeira em `GTXPro` (corrigido manualmente em `data_loader.py`).
- A IA sugeriu imputar idade nos 500 leads de prospecção (desenhamos duas esteiras operacionais independentes para Closers e SDRs).

---

## Evidências

- [x] **Suíte de Testes Automatizados:** 14 testes unitários e de anti-leakage em `tests/test_engine.py` (executados com `python -m pytest tests/test_engine.py`).
- [x] **Relatório de Backtest Out-of-Time:** Gerado automaticamente em `solution/artifacts/backtest_report.md`.
- [x] **Auditoria Adversarial do Red Team:** Documentada em `process-log/adversarial-red-team-audit.md`.
- [x] **Aplicação Executiva Interativa:** Disponível em `solution/app.py` com suporte a Windows (`run.bat`) e macOS/Linux (`run.sh`).
- [x] **Dados Pré-Carregados:** Todos os 4 CSVs oficiais incluídos em `solution/data/` para execução zero-friction.

---

*Submissão enviada em: 24 de Outubro de 2026 por Arthur Lima.*
