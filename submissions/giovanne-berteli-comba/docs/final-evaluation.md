# V01 — Avaliação final da versão congelada

> Registro da etapa indicada no título; suas referências a etapas seguintes são históricas.
> Para a versão atual e a demonstração, siga o [resumo da entrega](start-here.md).

**A versão atingiu os seis critérios numéricos definidos na V00.** Isso sustenta
o benchmark IT assistido desta entrega; toda sugestão ainda exige confirmação
humana. A principal limitação está nos erros da fila padrão: 50 dos 67 casos
divergentes tinham rótulos de classes previstas para especialista.

## O que foi congelado e medido

O [protocolo V00](../data/evaluation-protocol.json) permaneceu intacto. Antes das
previsões foram fixados [plano V01](../data/final-evaluation-plan.json),
[hashes de código/dados/modelos/referência e 64 casos de runtime](../data/final-evaluation-freeze.json).
Os 72 testes de software passaram antes da exposição. Não houve treino, refit,
seleção de candidato, troca de limiar ou recalibração com o teste final.

Foram avaliados os 7.175 registros reservados, nas oito classes, usando o modelo
selecionado em I01 (regressão C=2, limiar 0,80, cauda 0,01) e os dois baselines
previstos. O candidato não selecionado não foi comparado no teste. A membership
fica local; os conjuntos mantêm inteiros os grupos de similaridade definidos na V00.

O teste já foi consumido. Esses resultados não podem guiar outra escolha e depois
ser reapresentados como teste inédito. A interface continua usando exemplos só de
treino e nunca importa os bancos locais desta avaliação.

## Classificação — todos os 7.175 textos

| Modelo congelado | Macro F1 | Acurácia |
| --- | ---: | ---: |
| Classe majoritária | 0,055387 | 28,46% |
| TF-IDF + Naive Bayes | 0,646094 | 72,49% |
| TF-IDF + logística C=2 | **0,844612** | **84,92%** |

O ganho macro F1 sobre o baseline de texto foi0,198518. A métrica dá o mesmo peso
às oito classes; acurácia geral não esconde as categorias menores:

| Classe | Suporte | Precisão | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Access | 1.069 | 0,9034 | 0,8578 | 0,8800 |
| Administrative rights | 264 | 0,8578 | 0,6856 | 0,7621 |
| HR Support | 1.637 | 0,8492 | 0,8705 | 0,8597 |
| Hardware | 2.042 | 0,7932 | 0,8883 | 0,8381 |
| Internal Project | 318 | 0,9173 | 0,7327 | 0,8147 |
| Miscellaneous | 1.059 | 0,8308 | 0,8253 | 0,8280 |
| Purchase | 370 | 0,9745 | 0,8270 | 0,8947 |
| Storage | 416 | 0,9423 | 0,8245 | 0,8795 |

Administrative rights teve o menor F1/recall. Entre os erros mais frequentes,
120 HR Support, 101 Miscellaneous, 80 Access e 71 Administrative rights foram
previstos como Hardware. As matrizes completas usam linhas de rótulo fornecido
e colunas de previsão, na ordem fixa das classes; ver
[relatório agregado](../data/final-evaluation.json) e
[definição primária da matriz](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html).

## Sugestões, erros e carga de revisão

| Destino sugerido | Casos | Interpretação |
| --- | ---: | --- |
| Confirmação padrão | 1.951 (27,19%) | Passaram score, referências e política; ainda exigem confirmação |
| Especialista | 1.977 | Categoria prevista exige especialista, após as regras de triagem |
| Triagem | 3.247 | Score baixo e/ou referência/anomalia demandam revisão |

Na fila padrão, 1.884 previsões concordaram com o rótulo fornecido e 67 divergiram:
**96,57% de concordância**, com limite inferior Wilson 95% de **95,66%**.
Não são 96,57% dos tickets resolvidos; são 1.951 sugestões dentre 7.175 casos.
As três filas exigem participação humana, inclusive os casos sem alerta.

**Risco residual:**50 dos 67 erros padrão eram Access (16), Administrative rights (12),
HR Support (15) ou Purchase (7). Uma regra baseada na categoria prevista não garante
capturar a verdadeira categoria especializada. Esse resultado reforça a confirmação
humana e a necessidade de rótulos/fluxo representativos num piloto. Não foi usado
para mudar o modelo ou limiar nesta entrega.

O proxy médio de revisão/erro foi0,957449, com os pesos congelados. É um custo
adimensional ilustrativo, sem validade como minutos, dinheiro ou economia medida.

## Anomalias e persistência

Foram 338 casos distintos com possível anomalia, aproximadamente4,71% do teste.
Eles geraram345 avaliações sinalizadas: 193 de score (115 altas, 78 baixas) e 152
de tamanho (83 altas, 69 baixas). Sete casos tinham ambas. As duas métricas foram
registradas em todos os casos: 14.350 registros, sem avaliação insuficiente/não
avaliada nesta população. Alertas de referência não são erros confirmados; não
houve adjudicação humana nem medição de taxa de alarmes falsos.

O processamento offline computou vetores em lote e os encaminhou ao mesmo núcleo,
serviço e repositório da aplicação: 7.175 tentativas, 7.175 execuções salvas e nenhuma
falha de execução. Isso verifica decisões/gravação; não mede inicialização do worker
por requisição. Rótulos verdadeiros só participaram do cálculo de avaliação.

## Runtime real e falhas

Uma amostra de 64 casos escolhida por hash **antes das previsões**, sem reposição,
warmup ou retry, passou pelo subprocesso real e por outro SQLite:

| Medida local, incluindo commit | Resultado |
| --- | ---: |
| Tentativas / salvas | 64 / 64 |
| Avaliações persistidas | 128 |
| Falhas observadas / divergências contra o lote | 0 / 0 |
| Latência p50 | 587,20 ms |
| Latência p95 | 600,84 ms |
| Máxima | 618,66 ms |

O relógio externo inclui inicialização, carga do modelo, transformação, previsão
e gravação. Exclui renderização da interface e tempo humano. É uma amostra pequena,
sequencial, deste host; não garante SLA, throughput ou comportamento sob concorrência.
Os tempos individuais desse relógio não foram persistidos, apenas os agregados do
driver congelado. O elapsed_ms salvo no SQLite é anterior à persistência e não
permite refazer esses percentis; essa é uma limitação da trilha de latência.

As nove fixtures automatizadas de falha passaram separadamente: entrada vazia/grande,
contexto não suportado, nenhum termo conhecido, artefatos indisponíveis, timeout
real de processo com orçamento reduzido, exceção, score não finito e escrita falha.
Oito tentativas foram salvas; a falha de escrita ficou visivelmente não salva,
sem registro parcial. Essas falhas provocadas não compõem a taxa observada dos 64
casos reais. Os demais testes verificam limites iguais, referências constantes/
insuficientes, revisões e filtros. Nenhum teste automatizado é revisão humana real.

## Conferir a evidência

[Resultado completo](../data/final-evaluation.json),
[congelamento anterior à exposição](../data/final-evaluation-freeze.json),
[testes](review-evidence/final-evaluation-tests.txt),
[reagregação sem nova previsão](review-evidence/final-evaluation-checks.json) e
[recibo da versão](review-evidence/final-evaluation-current.json).

Na pasta da submissão, com o setup já preparado:

```bash
.venv/bin/python -I scripts/check_final_evaluation.py
python3 -I scripts/check_foundation.py --receipt docs/review-evidence/final-evaluation-current.json
```

A reagregação conferiu os 7.175 resultados a partir de scores salvos, reconciliou
as três matrizes/métricas e os critérios, sem carregar modelos ou prever de novo.
O comando `solution/evaluate_triage.py evaluate` reutiliza o resultado concluído
compatível. Não apague a tentativa ou substitua o freeze para alegar outro teste
limpo. Outra máquina/execução exige registrar a reprodução e sua exposição, sem
trocar silenciosamente esta evidência ou escolher candidatos com seus erros.

Continuam os limites de origem/semântica dos dados processados, disponibilidade
na abertura do ticket, dependência dentro dos grupos e transferência entre domínios.
O limite Wilson é o critério prévio; sua interpretação binomial independente é
limitada por textos/grupos relacionados. Os alvos passaram no benchmark; isso
não comprova operação real, economia ou aprovação de negócio.

**Próxima etapa: E01 — consolidar narrativa, evidências e CodeTour da versão estável.**
