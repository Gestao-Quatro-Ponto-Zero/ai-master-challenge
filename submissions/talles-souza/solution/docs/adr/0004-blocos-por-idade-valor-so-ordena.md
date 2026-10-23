# ADR 0004: Blocos por idade (política em config), com o valor só ordenando dentro do bloco

**Status:** aceita

## Contexto

O enunciado pede lógica de scoring que "não é só ordenar por valor" e que o vendedor entenda o porquê. A dica sugere estágio, tempo no pipeline, conta, produto e vendedor como candidatos. Antes de escolher, cada candidato foi medido no histórico.

O que os dados mostram:
- **Fora da amostra, os atributos do negócio não preveem ganho.** Treino nos fechados até 30/09/2017, teste nos 1.985 fechados do 4º trimestre: AUC do vendedor 0,522, da conta 0,488, do produto 0,500, do setor 0,486, dos quatro juntos 0,498 ([`process-log/evidencias/validar-sinal.txt`](../../../process-log/evidencias/validar-sinal.txt)).
- **Na tabela de pontos** (taxa do valor ÷ taxa geral de 63,2% em 6.711 fechados), setor, produto, porte, escritório e vendedor ficam entre 0,87 e 1,11; a idade passa de 1,5 (`packages/dominio/src/aplicacao/integracao.test.ts`).
- **A idade separa.** No replay (corte em 30/09/2017, 2.409 negócios abertos), até 40 dias fecharam 50,2%; de 41 a 50, 32,3%; de 51 a 60, 21,9%; de 61 a 90, 6,7%; acima de 90, nenhum (mesmo teste).
- **O valor é o preço de tabela.** Nos ganhos, a mediana do `close_value` é 1,0 × o preço do produto nos 7 produtos ([`process-log/evidencias/explorar-pipeline.txt`](../../../process-log/evidencias/explorar-pipeline.txt)).

## Decisão

- O bloco sai **só da idade**, pelas faixas da política: até 40 dias Siga no ritmo; 41 a 60 Foque agora; acima de 60 Nutrição. Sem data de início: bloco próprio, "Aborde primeiro".
- Cada negócio mostra a chance histórica da faixa dele ("N em 10 fecharam com essa idade"), calculada pelo replay, com uma frase que explica.
- O valor ordena **dentro** do bloco, nunca entre blocos: a receita esperada, que é a chance da faixa × o preço de tabela ([ADR 0011](0011-receita-esperada.md)).
- Vendedor, conta, produto, setor e porte ficam como contexto e filtro, e a tela "Como a nota funciona" diz por quê.

## Consequências

- A nota é honesta sobre o que mede: "diz se negócios com essa idade costumam fechar. Não diz se este cliente é bom." (texto da política).
- Na fila de todos: Foque agora 30, Siga no ritmo 27, Nutrição 1.532, Aborde primeiro 500 (`integracao.test.ts`). O foco é curto e acionável.
- A região Central fica sem negócio em Foque agora (0, contra 14 no West e 16 no East); a tela mostra o grupo vazio com a faixa.
- Se o dado vivo mostrar outra curva, recalibra-se a política (ADR 0003).

## Alternativas consideradas

- **Pontos somados por atributo:** dariam um número com cara de precisão sobre atributos que, neste histórico, não separam ganho de perda.
- **Modelo de aprendizado de máquina:** com AUC perto de 0,50 nos atributos, o modelo aprenderia ruído; e seria mais difícil de explicar ao vendedor.
- **Ordenar por valor:** o enunciado pede mais que isso, e o valor sozinho põe um negócio parado há 300 dias na frente de um que ainda fecha.
- **Janela dos ganhos (p95 de 116 dias, máximo de 138) como limite:** separa o que ainda pode fechar do que nunca fechou, mas não diz onde o esforço muda o resultado; a curva por faixa diz.
