# Avaliação final — 02/11/2026

## Pedido e congelamento

Após o commit `cb01264`, o usuário pediu a próxima etapa. Codex retomou o contexto
pelos donos operacionais, com worktree limpa e recibo de fundação válido. V01
precisava avaliar a seleção I01 sem usar o teste para trocar candidato ou limites.

O [plano do driver](../data/final-evaluation-plan.json) foi escrito antes das
previsões: classificar todos os 7.175 registros reservados, medir runtime em 64 casos
por hash e manter falhas provocadas numa população separada. Preferiu-se cálculo
de features/scores em lote seguido do mesmo serviço/núcleo/SQLite para a população
completa; medir o worker frio em todos os registros custaria muito mais sem ser
necessário para o benchmark de classificação. O lote não foi apresentado como
latência individual ou teste do timeout.

O avaliador e oito testes novos foram preparados com fixtures sintéticas. Os 72
testes passaram antes de congelar hashes do driver/testes, fontes, lock, membership,
modelos, política e referência. O [freeze](../data/final-evaluation-freeze.json)
foi registrado em 2026-11-03T01:00:51.366945+00:00; a tentativa começou depois,
em 2026-11-03T01:00:51.571884+00:00. A fonte completa já fora auditada/agrupada;
o que permanecia reservado era seu uso preditivo/de desempenho para escolhas.

## Resultado observado

[Relatório completo](../docs/final-evaluation.md) e
[JSON agregado](../data/final-evaluation.json): macro F1 de 0,844612 para logística
C=2, frente a 0,646094 do baseline de texto e 0,055387 da majoritária. Foram mantidos
limiar0,80 e cauda0,01. Os seis alvos numéricos prévios passaram; não houve treino,
refit, novo candidato, ajuste de referência ou peso depois de ver o teste.

As filas tiveram 1.951 confirmações padrão,1.977 especialistas e 3.247 triagens.
Cobertura padrão 27,19%;1.884 concordâncias contra o rótulo fornecido e 67 erros,
96,57% de concordância e limite inferior Wilson 95% de 95,66%. 50 desses 67 erros
tinham rótulo de classe especializada (Access 16, Admin 12, HR 15, Purchase 7): a
política depende da previsão e não garante capturar todas as categorias verdadeiras.
A confirmação humana continua obrigatória. Administrative rights teve o menor
F1/recall; os erros agregados foram registrados sem publicar texto ou escolher
exemplos para retunar a solução.

Houve 338 casos distintos com possível anomalia e 345 avaliações sinalizadas (193
score,152 tamanho), sem referência insuficiente neste teste. Não há julgamento
humano, taxa de alarmes falsos ou prova de problema em cada alerta. A média de
custo 0,957449 é um proxy adimensional, sem economia de tempo/dinheiro medida.

## Software, runtime e auditoria

O serviço/repositório salvou 7.175 execuções e 14.350 avaliações no caminho offline,
sem falhas. Os 64 casos predefinidos usaram o subprocesso real e outro SQLite:
64 salvos,128 avaliações, zero falhas ou discrepâncias de decisão contra o lote.
Latência externa incluindo commit: p50 de 587,20 ms, p95 de 600,84 ms, máximo 618,66 ms.
Amostra sequencial pequena, sem garantia de SLA/throughput/contensão. Tempos
individuais desse relógio não foram persistidos; os agregados vêm do driver
congelado. O elapsed_ms do banco tem outro escopo, anterior à persistência.

As nove fixtures separadas de falha passaram, incluindo timeout real com prazo
reduzido e falha de escrita sem registro parcial. Oito tentativas foram salvas;
a nona ficou visivelmente não salva. Não se somaram falhas provocadas à taxa
observada da amostra real. Não houve revisão humana inferida de um teste.

O [auditor dos resultados](../docs/review-evidence/final-evaluation-checks.json)
reagregou 7.175 decisões a partir de scores salvos, conferiu todas as matrizes,
métricas e critérios, sem carregar modelos nem prever novamente. A chamada
repetida ao avaliador retorna o relatório concluído; tentativas parciais ou versões
alteradas são bloqueadas. Bases/score vectors/texto ficam locais e ignorados.

## Estado e próxima ação

O teste agora está consumido. Novo ajuste influenciado por seus resultados não
pode alegar outra avaliação limpa com esses registros. A avaliação retrospectiva
IT não prova validade na abertura, independência por entidade, operação em clientes,
produção, economia medida ou aprovação de negócio. A dependência entre textos
também limita a interpretação binomial independente do critério Wilson.

Donos, plano, status e execução F02/F03 foram atualizados. Recibos foram registrados
após regenerar as saídas analíticas afetadas; a avaliação final foi auditada a
partir dos dados salvos, sem repetição de previsão/treino. E01 consolidará narrativa,
evidência e CodeTour; P01 ainda depende da revisão final. Sem commit/push/deploy.

A [captura 18](chat-exports/18-final-evaluation-chat.md) preserva oito mensagens
novas de quatro turnos, incluindo final da correção de setup e troca de commit.
`hasMore=true` indica histórico anterior fora da página. Mensagens posteriores e
final desta V01 ficam para próxima extração, sem reconstrução de texto ausente.
