# Modelo de Machine Learning — Priorizador de Leads

## Objetivo

Adicionar uma camada real de machine learning ao Priorizador de Leads para estimar a probabilidade de fechamento de cada oportunidade aberta.

A versão anterior tinha um score inteligente e explicável, mas não treinava um modelo supervisionado. Esta versão passa a usar histórico de oportunidades fechadas para aprender padrões de conversão.

## Tipo de problema

Classificação binária supervisionada.

| Etapa final | Label |
|---|---:|
| Ganha | 1 |
| Perdida | 0 |

## Algoritmo usado no projeto C#

O projeto usa ML.NET com o treinador `FastTree` para classificação binária.

Arquivo principal:

```text
src/PriorizadorLeads.WinForms/Services/MachineLearningLeadScorer.cs
```

## Pipeline do modelo

1. Carrega os CSVs em português.
2. Cruza funil, contas, produtos e equipe comercial.
3. Mantém apenas oportunidades fechadas para treinamento.
4. Transforma variáveis categóricas com One-Hot Encoding.
5. Concatena variáveis categóricas e numéricas em `Features`.
6. Treina classificador binário.
7. Avalia em conjunto de teste.
8. Aplica o modelo nas oportunidades abertas.
9. Combina probabilidade ML com score explicável.

## Features usadas

- vendedor;
- gerente;
- escritório regional;
- conta;
- setor;
- produto;
- série do produto;
- faixa de receita;
- faixa de funcionários;
- receita anual;
- número de funcionários;
- preço sugerido;
- idade/ciclo da oportunidade.

## Prevenção de vazamento de informação

A etapa do negócio foi excluída do modelo.

Nas oportunidades fechadas, `Ganha` e `Perdida` são justamente a resposta que o modelo precisa prever. Se esse campo fosse usado como entrada, o modelo pareceria excelente, mas estaria apenas lendo a resposta.

## Score híbrido

O resultado final apresentado ao usuário é:

```text
score_hibrido = 0,55 * score_regras + 0,45 * probabilidade_ml * 100
```

Essa composição foi escolhida porque:

- mantém explicabilidade para o vendedor;
- evita uma decisão totalmente opaca;
- adiciona aprendizado supervisionado baseado em histórico;
- reduz o risco de superconfiar em um dataset pequeno e limitado.

## Validação exploratória

Como o ambiente de geração não possui SDK do .NET instalado, foi gerada também uma validação exploratória em Python com estratégia equivalente de classificação supervisionada para conferir a viabilidade do modelo.

Resultado registrado em:

```text
outputs/modelo_ml_validacao.txt
```

Resumo da validação exploratória:

| Métrica | Valor |
|---|---:|
| Linhas fechadas | 6.711 |
| Treino | 5.368 |
| Teste | 1.343 |
| Acurácia | 0,635 |
| AUC ROC | 0,570 |
| AUC Precision-Recall | 0,682 |
| F1-Score | 0,767 |
| Log Loss | 0,654 |

## Interpretação das métricas

O modelo adiciona sinal preditivo, mas ainda não é um modelo forte. Isso é esperado porque o dataset não contém variáveis críticas de RevOps, como origem do lead, número de interações, e-mails, reuniões, proposta enviada, desconto, concorrente, motivo de perda e próximos passos registrados.

Mesmo assim, a camada ML é útil porque identifica padrões combinados de vendedor, produto, conta, setor, porte e ciclo que não aparecem isoladamente no score por regras.

## Recomendação para evolução

Para produção, a empresa deveria:

1. Integrar o CRM real por API.
2. Capturar atividades comerciais e eventos do funil.
3. Registrar motivos de perda e objeções.
4. Versionar modelos treinados.
5. Monitorar métricas por safra.
6. Rodar teste A/B com vendedores.
7. Recalibrar o modelo mensalmente ou por mudança significativa do funil.
