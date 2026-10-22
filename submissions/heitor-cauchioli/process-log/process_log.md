---
title: "Process Log — Diagnóstico de Churn RavenStack"
date: "22/10/2026 · Heitor Cauchioli"
---

## Resumo

Usei uma única ferramenta de IA: o Claude (modelo Opus 5.5), no app claude.ai, com execução de código em Python e publicação de artefatos. Foi uma única conversa, com três pedidos meus. A IA executou quase toda a análise de forma autônoma. Meu papel foi escrever o briefing e definir os critérios de qualidade. Este log descreve o que a IA fez a partir dele.

| Item | Detalhe |
| --- | --- |
| Ferramenta | Claude Opus 5.5 (claude.ai), com Python/pandas, scipy e scikit-learn num ambiente de código |
| Por que ela | Precisava cruzar 5 tabelas (33 mil linhas) com código reproduzível, não só conversar sobre os dados |
| Meus pedidos | 1) o briefing completo do desafio; 2) este process log; 3) o pacote de submissão |
| Execução da IA | Cerca de 25 scripts de análise, 3 erros de código corrigidos, 4 problemas de dados detectados |
| Entregas | Relatório em PDF e Markdown, lista de 500 contas priorizadas, script diário para o CS, scripts que reproduzem cada número, painel interativo |

Registro aqui, de forma transparente, quem fez o quê, porque é isso que o desafio pede para avaliar.

## Como decompus o problema antes de promptar

Em vez de pedir "analise o churn", montei um prompt com o desafio inteiro, estruturado para a IA não parar na resposta óbvia:

1. **Papel e contexto:** "novo AI Master da RavenStack", um SaaS B2B com cerca de 500 contas e assinaturas mensais e anuais.
2. **A contradição do CEO como problema central:** o churn subiu, o CS diz que a satisfação está ok e o Produto diz que o uso cresceu. Isso orientou a análise a testar cada uma dessas afirmações.
3. **Três perguntas fechadas:**
    - Qual é a causa raiz?
    - Quais segmentos estão em risco, com contas específicas?
    - Quais ações tomar, priorizadas e com impacto?
4. **Critérios de qualidade explícitos:**
    - Cruzar as 5 tabelas.
    - Números verificáveis.
    - Recomendações acionáveis.
    - Separar correlação de causa.
    - Linguagem que um CEO não técnico consiga usar.
5. **Dicas de direção:**
    - Cruzar o uso com os eventos de churn.
    - Comparar os tickets de quem saiu com os de quem ficou.
    - Checar se o uso cresceu em todos os segmentos.
    - Ponderar o churn por MRR.
    - Desconfiar de correlações.
6. **Os 5 CSVs anexados** na mesma mensagem.

O briefing já trazia a ideia de que a resposta provavelmente estava numa contradição entre fontes. Os critérios de avaliação viraram a checklist que a IA usou.

## Passo a passo da execução

A partir do briefing, o Claude trabalhou em etapas, com uma lista de tarefas visível ao lado da conversa:

1. **Estrutura e qualidade dos dados.** Leu as 5 tabelas, conferiu chaves e datas e comparou as três formas de medir churn: flag na conta, eventos de churn e assinaturas canceladas. Elas não batem (110, 352 e 312 contas), e todas as 500 contas ainda têm assinatura ativa.
2. **Churn em taxa, não em contagem.** Recalculou o churn como taxa sobre a base ativa de cada trimestre. A maior parte do aumento era volume, mas o 4º tri/24 tinha uma piora real, sobretudo em MRR.
3. **Testes de hipóteses por conta.** Comparou quem saiu e quem ficou em 23 variáveis, como uso, erros, tickets, CSAT, plano, cobrança, indústria e canal, com testes de significância. Quase nada separava os dois grupos.
4. **A virada: idade da assinatura.** Como os atributos da conta não explicavam o churn, olhou o ciclo de vida. Assinaturas com até 60 dias passaram de cerca de 1% para 3,1% de churn mensal no 2º semestre. As maduras ficaram estáveis.
5. **Expansão contra primeiro contrato.** Separou a primeira assinatura de cada conta das expansões. Só as expansões pioraram: de 1,5% para 5,9% de cancelamento em 60 dias (p < 0,001).
6. **Uso por assento.** Testou a afirmação do Produto. O uso total cresceu, mas o uso por assento caiu 57%, em todos os planos e indústrias.
7. **Os pontos cegos do CS.**
    - O CSAT não registra nenhuma nota abaixo de 3.
    - 68% dos cancelamentos não tiveram ticket nos 90 dias anteriores.
    - O motivo de saída contradiz o comentário do cliente em 66% dos casos.
8. **Modelo preditivo.** Treinou regressão logística e gradient boosting com corte temporal: treino até 30/06/24 e teste no 4º tri. O AUC foi de 0,52 e 0,54, praticamente sorteio, e isso foi assumido como achado.
9. **A alternativa que funcionou.** Construiu uma regra de risco pela idade de cada assinatura e testou como se estivesse em 30/09/24. As contas P1 perderam 7,8% do MRR no trimestre seguinte, contra 1,9% das P3.
10. **Entrega.** Gerou o script diário para o CS, a lista de contas, o painel interativo e o relatório.

## Onde a IA errou e como foi corrigido

Todos os erros abaixo foram detectados e corrigidos pela própria IA durante a execução, sem intervenção minha.

| Erro | Como apareceu | Correção |
| --- | --- | --- |
| Conclusão precipitada sobre o uso | O primeiro cálculo mostrou o uso por conta despencando desde 2023 | Checou as datas e viu que 53% do uso e 54% dos tickets eram anteriores ao cadastro da conta. Refez tudo só com registros válidos, e a tendência mudou de forma |
| Taxa de churn inflada | A primeira taxa trimestral misturava assinaturas que nasceram e morreram no mesmo trimestre (11,7% no Q4) | Restringiu o denominador à base existente no início do trimestre (4,2%) |
| Sinal que se invertia | A variável "peso de assinaturas novas" parecia útil no treino, mas teve AUC de 0,43 no teste | Descartou o modelo por conta e passou a modelar por assinatura e idade |
| Regra que subestimava perdas | O backtest previu $226K de perda, contra $552K reais | Mantido como limitação declarada; o script recalibra as taxas a cada execução |
| Erros de código | Caminho de arquivo errado, conflito de colunas num join e um `np.select` com listas de tamanhos diferentes | Corrigidos na hora e scripts reexecutados |

Houve também um risco de interpretação. O pico de cancelamentos em 29–31/12/24 pode ser efeito do fim da extração dos dados. A conclusão foi testada sem dezembro (julho a novembro) e se manteve.

## O que o briefing trouxe que a IA sozinha não teria

A IA não tinha o contexto do negócio nem os critérios de quem vai avaliar a análise. Isso veio do meu prompt:

- **A contradição do CEO** (churn sobe, satisfação ok, uso cresce) virou a hipótese de trabalho: testar cada afirmação dos times, em vez de só descrever o churn.
- **"Nem todo churn tem o mesmo peso"** levou a medir tudo em MRR. Foi em MRR que o salto do Enterprise apareceu.
- **"O uso cresceu para todos os segmentos?"** levou ao achado do uso por assento.
- **"Distinga correlação de causalidade"** levou à separação entre o que está provado e o que é hipótese, e à proposta de teste controlado.
- **"O CEO precisa conseguir ler e agir"** definiu o formato: resumo de uma página e ações com dono, prazo e métrica.

## Iterações

Foram 3 pedidos meus na conversa:

1. O briefing completo, com os dados.
2. Este process log.
3. O pacote de submissão: relatório em PDF e Markdown, README de setup e código.

Dentro do primeiro pedido, a IA fez cerca de 25 rodadas de análise em código. Dessas, 3 corrigiram erros de programação e 2 corrigiram conclusões da análise.

## Como reproduzir

Todos os scripts esperam os 5 CSVs da RavenStack na mesma pasta e rodam com Python 3, pandas, numpy, scipy e scikit-learn.

| Arquivo | O que faz | Comando |
| --- | --- | --- |
| `analise_diagnostico.py` | Recalcula todos os números do relatório e grava `out.json` | `python3 analise_diagnostico.py` |
| `modelo_ml_teste.py` | Treina os modelos de ML com corte temporal e imprime o AUC (0,52 e 0,54) | `python3 modelo_ml_teste.py` |
| `watchlist.py` | Gera `watchlist_contas.csv`, com prioridade P1/P2/P3 e ação sugerida por conta | `python3 watchlist.py . 2024-12-31` |
| `watchlist_contas.csv` | Lista de 500 contas em 31/12/24, pronta para o CS | — |

O relatório principal é o `relatorio_diagnostico_churn.pdf`, também disponível em Markdown. As instruções de setup estão no `README.md`. Há ainda uma versão em painel interativo, publicada no claude.ai.
