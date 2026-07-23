# Roteiro da Demonstração Guiada — 3:10

A aplicação contém uma Demonstração guiada em oito etapas na rota `/demo`. Este roteiro usa os mesmos rótulos em português do Brasil exibidos na interface e foi desenhado para uma avaliação de 2 a 4 minutos.

| Tempo | Rota | Ação | Fala do apresentador | Métrica/evidência | Transição |
|---|---|---|---|---|---|
| 0:00–0:20 | `/` | Abrir Visão geral | “A inteligência de retenção começa transformando eventos históricos fragmentados em evidência governada, sem saltar para uma previsão.” | 500 contas; 35.586 eventos processados | “Primeiro, veremos o que passou pelos controles de qualidade.” |
| 0:20–0:45 | `/quality` | Abrir Qualidade dos dados | “Somente 13.927 eventos são utilizáveis. Os 21.659 registros excluídos permanecem como pendência de qualidade e nunca se tornam sinal comportamental.” | Populações principal/estrita; alertas; quarentena separada | “Com o limite da evidência claro, podemos examinar jornadas reais.” |
| 0:45–1:15 | `/journeys` | Selecionar Perfil B e depois Perfil C | “O Perfil B mostra churn recorrente observado; o Perfil C mostra reativação com retorno de uso. São exemplos históricos anônimos, não contas ranqueadas.” | 4.221 jornadas governadas; três perfis anônimos | “A evidência repetida das jornadas pode ser explorada em um grafo delimitado.” |
| 1:15–1:45 | `/graph` | Alterar o modo para Explorador de padrões; selecionar um nó | “Somente evidência promovível, robusta ou sensível está presente. A visão é reduzida, filtrada e explicitamente descritiva.” | 435 padrões promovíveis; 43 transições; máximo de 35 nós/80 arestas | “A mesma evidência governada pode sustentar filas de revisão humana.” |
| 1:45–2:20 | `/watchlist` | Filtrar uma fila; clicar em Ver evidência | “Sete filas organizam a investigação. A prioridade é uma matriz transparente de componentes discretos, nunca probabilidade individual. Todo item exige decisão humana.” | Sete filas; população anônima de 500 contas; somente MRR associado | “Ações potenciais são hipóteses; o próximo passo é desenhar um teste.” |
| 2:20–2:50 | `/experiments` | Abrir o primeiro detalhe experimental | “Oito desenhos especificam elegibilidade, amostra, métricas, plano estatístico, salvaguardas e interrupção. Todos permanecem não testados; nada foi executado.” | Oito desenhos; status causal não testado | “Encerramos tornando os controles tão visíveis quanto a oportunidade.” |
| 2:50–3:10 | `/governance` | Revisar os controles | “A demonstração não expõe PII ou chaves de conta, não usa dados futuros, pontuação preditiva, intervenção automática, experimento executado ou alegação causal.” | 15 JSONs determinísticos; data-limite fixa em 31/12/2024 19:00 | “O resultado está pronto para documentação e submissão, não para operação ao vivo.” |

## Perfis da demonstração

- Perfil A — sem churn observado.
- Perfil B — churn recorrente.
- Perfil C — reativação e retorno de uso.

Os rótulos representam três contas analíticas anônimas selecionadas deterministicamente. As chaves internas nunca devem ser reveladas ou narradas.

## Salvaguardas do apresentador

Use “observado”, “associado”, “histórico”, “descritivo” e “exige revisão humana”. Não use “vai cancelar”, “causou”, “receita em risco”, “receita salva”, “melhor ação” ou “experimento bem-sucedido”. Se perguntarem sobre produção, informe que autenticação, dados ao vivo, observabilidade, intervenções e execução experimental permanecem fora do escopo.
