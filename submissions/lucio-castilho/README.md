# Submissão — Lúcio Castilho Andrade Pinto — Challenge 003

## Sobre mim

**Nome:** Lúcio Castilho Andrade Pinto  
**LinkedIn:** https://www.linkedin.com/in/luciocapinto/  
**Challenge escolhido:** Challenge 003 — Lead Scorer

## Executive Summary

Construí o **G4 | Lead Scorer**, uma aplicação web em Python que transforma o pipeline aberto em uma fila de decisões explicável para o vendedor. Antes de implementar um score, auditei os datasets, testei hipóteses de conversão e comparei modelos com split temporal; os modelos preditivos apresentaram AUC próxima de 0,50 e lift pequeno/instável, então rejeitei a ideia de apresentar uma falsa probabilidade de fechamento. A solução final combina **Historical Fit** (contexto histórico regularizado) e **Attention Need** (urgência operacional baseada no tempo em Engaging) para gerar um **Priority Score**, uma **Action Category** e uma explicação rastreável. O objetivo é simples: mostrar onde focar, quais deals precisam de uma decisão e por quê.

## Solução

A aplicação está em [`solution/`](solution/) e foi construída com Streamlit.

Principais funcionalidades:

- ranking de oportunidades abertas por ação e prioridade;
- filtros por vendedor, manager, região, estágio, produto e categoria de ação;
- visão `Focus Now`, `Follow Up`, `Re-engage`, `Requalify` e `Qualify or Drop`;
- explicação determinística de cada score;
- indicador de confiança da evidência histórica;
- exportação da visão filtrada para Excel;
- exportação de relatório de ação para PDF;
- funcionamento com os registros reais do dataset, sem criação de oportunidades sintéticas.

### Como rodar

Os dados são baixados separadamente e ficam em `datasets/`, que é ignorada pelo repositório. Consulte [`solution/README.md`](solution/README.md) para o setup completo.

Resumo:

```bash
cd submissions/lucio-castilho/solution
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

### Testes

Os testes verificam, entre outros pontos, que:

- apenas os 2.089 deals abertos são priorizados quando a base oficial está disponível;
- os scores ficam entre 0 e 100;
- alterar `close_value` ou `close_date` dos deals abertos não altera o score;
- oportunidades sem `account` continuam recebendo score;
- a solução não inclui cópias locais dos CSVs dentro da pasta versionada.

## Abordagem

1. **Defini o problema antes da ferramenta:** a decisão central é "em quais deals devo focar agora e por quê?".
2. **Auditei os dados:** validei joins, campos ausentes, datas e uma inconsistência real de produto (`GTXPro` vs `GTX Pro`).
3. **Evitei leakage:** `close_value` e `close_date` nunca entram como features do score.
4. **Testei sinais históricos:** produto, setor, tamanho da conta, região, vendedor e interações.
5. **Comparei modelos com split temporal:** regressão logística, gradient boosting e baselines históricos.
6. **Rejeitei o ML como motor principal:** os resultados fora da amostra ficaram próximos do aleatório.
7. **Redesenhei a solução:** priorização operacional baseada em Historical Fit + Attention Need + Action Category.
8. **Construí o produto:** dashboard focado em decisão, não em exploração de BI.

A metodologia completa está em [`docs/methodology.md`](docs/methodology.md).

## Resultados / Findings

### 1. Os dados estáticos não sustentam uma previsão confiável de Won/Lost

Na validação temporal, os candidatos ficaram próximos de AUC 0,50. O melhor Lift@10% observado foi modesto e não se manteve no Top 20%/30%. A conclusão foi não transformar um sinal fraco em uma falsa "probabilidade de fechamento".

### 2. A maior limitação operacional é a falta de contexto de conta no pipeline aberto

Cerca de 68% das oportunidades abertas não possuem `account`. Por isso, o score possui um caminho Core que funciona sem conta e um enriquecimento opcional quando setor e perfil da empresa existem.

### 3. O tempo em Engaging é útil como sinal de atenção, mas não como penalidade linear

Deals muito antigos não recebem urgência infinita. A aplicação diferencia uma janela de follow-up de uma situação de pipeline potencialmente stale, em que a recomendação passa a ser reengajar, requalificar ou decidir se o deal deve permanecer ativo.

### 4. O score é uma fila de trabalho, não uma previsão

`Priority Score = 35% Historical Fit + 65% Attention Need` para deals Engaging. A categoria de ação é definida por uma matriz de decisão e tem precedência sobre o número na ordenação.

## Recomendações

1. **Usar o Lead Scorer como camada de priorização semanal/diária**, começando pelos blocos `Focus Now` e `Need Decision`.
2. **Melhorar a captura de dados no CRM**, especialmente `created_date`, `last_activity_date`, próxima ação, valor estimado e conta associada.
3. **Revalidar um modelo preditivo somente depois de enriquecer os dados comportamentais**, porque as features estáticas atuais não demonstraram sinal suficiente fora da amostra.
4. **Tratar score alto como necessidade de atenção**, não como garantia de fechamento.

## Limitações

- O dataset não possui `created_date` para Prospecting; portanto não existe aging legítimo para esse estágio.
- Não há valor esperado confiável para oportunidades abertas; `close_value` só existe após o resultado e não é usado no score.
- A maioria do pipeline aberto não possui `account`, limitando o uso de setor e tamanho da empresa.
- O dataset não contém atividade comercial recente, reuniões, emails, próxima ação ou stakeholders.
- O snapshot operacional foi fixado em 31/12/2017, coerente com o período do dataset; a origem dos dados não garante que todas as oportunidades abertas representem um snapshot real e perfeitamente limpo.
- Historical Fit representa contexto histórico, não probabilidade de fechamento.

## Process Log — Como usei IA

O log detalhado está em [`process-log/README.md`](process-log/README.md).

### Ferramentas usadas

| Ferramenta      | Para que usei                                                                                                            |
| --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| ChatGPT         | Decomposição do problema, auditoria metodológica, geração e revisão de código, desenho do scoring, testes e documentação |
| Python / pandas | Validação das hipóteses diretamente nos CSVs e construção dos indicadores                                                |
| Streamlit       | Construção rápida do produto funcional                                                                                   |

### Evidências

- narrativa detalhada do processo em `process-log/README.md`;
- testes automatizados em `solution/tests/`;
- histórico de commits do PR;
- diretórios preparados em `process-log/screenshots/` e `process-log/chat-exports/` para anexar evidências reais.

**Submissão enviada em:** 16/07/2026
