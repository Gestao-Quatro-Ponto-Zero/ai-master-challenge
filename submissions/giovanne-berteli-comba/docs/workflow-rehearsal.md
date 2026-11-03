# Ensaio de uso — resultado H01

**O assistido teve maior concordância, mas levou mais tempo.** O resultado
registrado não demonstra redução de tempo ou custo.

| Medida | Manual | Assistido |
| --- | ---: | ---: |
| Tickets | 8 | 8 |
| Tempo decorrido do lote | 41,58 s | 52,72 s |
| Tempo médio por ticket | 5,20 s | 6,59 s |
| Concordância com os rótulos fornecidos | 1/8 (12,5%) | 7/8 (87,5%) |
| Correções da sugestão | Não se aplica | 0 |
| Falhas de sugestão | Não se aplica | 0 |

A diferença manual − assistido foi **−11,14 s por lote**: o assistido levou
26,79% mais tempo que o manual. A ordem atribuída foi assistido → manual. Não há
conversão desses tempos em horas mensais ou economia financeira.

## Origem e conferência

O banco local contém um ensaio completo com tipo **Operador (declarado)**. A IA
encontrou esse registro ao preparar a submissão, extraiu um snapshot consistente
em modo somente leitura e reconciliou plano, fontes, decisões e artefatos. Não
executou as decisões desse participante nem criou outro ensaio para melhorar o
resultado. A identidade/atenção do participante não foi observada independentemente.

O protocolo foi registrado antes das etapas. São 16 textos de TRAIN, grupos
distintos, uma tarefa por classe em cada etapa, pareamento por comprimento e
ordem por hash. Os hashes de fontes e protocolo foram conferidos; os casos foram
reproduzidos sem novas predições. O cronômetro inclui espera, revisão, correção e
pausas até o arquivo pronto; exclui preparação do estudo, download e helpdesk.

- [Resultado e plano](review-evidence/h01-result.json)
- Decisões: [manual](review-evidence/h01-manual-decisions.csv) e [assistido](review-evidence/h01-assisted-decisions.csv)
- Trilhas: [manual](review-evidence/h01-manual-audit.json) e [assistido](review-evidence/h01-assisted-audit.json)
- [Inventário de todas as tentativas e checagens da extração](review-evidence/h01-checks.json)

Os exports omitem nome do operador e textos originais. O banco continua local,
ignorado pelo Git. O revisor pode examinar esses arquivos sem executar novamente
o ensaio; pode também repeti-lo em **Instrutor → Experimento**.

## Interpretação e decisão

A concordância manual muito baixa impede tratar seu tempo menor como execução
equivalente em qualidade. O assistido apresentou maior concordância nesta amostra,
mas isso não prova que reduziu trabalho: houve mais tempo e nenhuma correção da
sugestão. O registro não explica sozinho a diferença entre as etapas.

Este é um ensaio pequeno, balanceado, com textos processados já usados no treino,
rótulos fornecidos sem adjudicação e possíveis efeitos de experiência, ordem e
aprendizado. Não constitui novo benchmark independente nem validação em produção.

**Decisão recomendada:** manter a assistência com confirmação, investigar os
atritos e a compreensão das categorias, e planejar um piloto com operadores e
dados representativos. Medir tempo e qualidade juntos antes de expandir ou
prometer economia. O [aprendizado](operational-learning.md) permanece: a métrica
do modelo, sozinha, não demonstra valor operacional.
