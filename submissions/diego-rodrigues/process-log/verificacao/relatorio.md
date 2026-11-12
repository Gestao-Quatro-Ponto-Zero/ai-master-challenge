# Relatório da verificação independente

**Modelo:** claude-opus-5-5 (Claude Code, como subagente revisor; mesma família dos modelos que implementaram, o que o protocolo de `LEIA.md` desaconselha, ver a nota no fim)
**Data:** 2026-11-11
**Clone:** não houve clone separado. O revisor leu só os quatro CSVs, `solution/config.json`, `README.md`, `docs/resumo-executivo.md`, `docs/logica.md` e `docs/numeros-saida.txt`; escreveu o próprio código (`verificar.py`, sem importar `solution/motor` nem `solution/avaliacao`) e só depois abriu o código de produção. A seção 7b do script foi escrita depois dessa leitura, para reimplementar a regra documentada do relógio, mas sem importar nada do motor.

Rodar de novo: `python3 process-log/verificacao/verificar.py > process-log/verificacao/saida.txt` (pandas e numpy, sem scipy; semente própria 12345; cerca de 30 s).

## Números recalculados

| Número citado | Recalculado | Bate? | Comentário |
|---|---|---|---|
| 8.800 linhas | 8.800 | sim | exato |
| "GTXPro" x "GTX Pro", 1.480 linhas | 1.480 | sim | exato; é a única divergência de produto; após normalizar espaço e caixa, 0 linhas ficam sem preço |
| 1.425 de 2.089 abertos sem conta | 1.425 de 2.089 | sim | exato; 0 de 6.711 fechados sem conta, também exato |
| 500 em Prospecting sem data | 500 de 500 | sim | exato; nenhum Engaging sem data, nenhum aberto com close_date |
| maior close_date 2017-12-31 | 2017-12-31 | sim | exato |
| primeiro fechamento 2017-03-01 | 2017-03-01 | sim | exato |
| vendedores 35 / 30 / 27 | 35 / 30 / 27 | sim | exato |
| pipeline aberto US$ 4.966.215 | US$ 4.966.215 (2.089 negócios) | sim | exato, preço de tabela |
| vencidos US$ 3.656.299 (73,6%) | US$ 3.656.299 (73,6%), 1.474 negócios | sim | exato. 1.301 vencem pela idade (> 138 dias) e 173 só pelo prazo do trimestre |
| vivos US$ 235.930, 115 negócios | US$ 235.930, 115 | sim | exato |
| 17 dos 35 vendedores com negócio vivo | 17 | sim | exato; 11 deles têm mais de 5 vivos, como o auto-relato diz |
| Prospecting sem data US$ 1.073.986 | US$ 1.073.986 | sim | exato; 4.966.215 = 3.656.299 + 235.930 + 1.073.986 |
| ciclo máximo 138 dias | 138 | sim | exato; já é 138 em todos os seis cortes |
| regra do trimestre: 1 fechamento fora do prazo em 6.711 | 1 de 6.711 (Q7C5MJ4W, engajado 30/06, perdido 01/11) | sim | exato |
| 734 vencidos distintos nos 6 cortes, nenhum ganho | 734; 0 ganhos | sim, mas ver ressalva | 733 dos 734 seguem em Engaging no fim do export e 1 foi perdido. Ver "O achado central" |
| vivos por corte (1.364, 1.893, 1.845, 1.852, 1.916, 1.591) | idênticos | sim | exato nos seis cortes, com a minha regra de recorte |
| fila "fechar" por corte (385, 1.893, 1.845, 962, 1.916, 1.432) | idênticos | sim | só na seção 7b (regra reimplementada) |
| valor ganho relógio US$ 1.097.324 | US$ 1.097.324 | sim | exato, na reimplementação da regra documentada (7b); corte a corte também idêntico |
| valor ganho preço e prazo US$ 842.462 | US$ 842.462 | sim | exato, com o desempate que o código usa (mais dias restantes primeiro, ver achado) |
| razão 1,30, IC 95% 1,13 a 1,52 | 1,303, IC [1,141; 1,514] | sim | ponto exato; IC difere na 2ª casa só pela semente do bootstrap |
| taxa de acerto 22,7% x 15,4% | 22,7% x 15,4% | sim | média das taxas por corte, como no código |
| relógio perde em 23/10/2017 (133.640 x 150.104) | 133.640 x 150.104 | sim | exato |
| US$ 1.416 por vendedor a cada 4 semanas (US$ 254.862) | 254.862 / 180 = 1.415,9 | sim | aritmética confere; 30 vendedores é o divisor, embora só 27 tenham negócio aberto |
| 57 / 28 / 14 horas | 56,6 / 28,3 / 14,2 | sim | arredondamento |
| fração do teto 41% x 32% | 0,412 x 0,316 | sim | aritmética sobre os totais do documento (oráculo não recalculado) |
| relógio ÷ aleatório 1,54 | 0,227 / 0,147 = 1,544 | só aritmética | o 14,7% do aleatório não foi recalculado |
| nenhum atributo com p < 0,05 | nenhum com p < 0,05 em dois desenhos | sim | ver seção de atributos |
| 3.001 negócios com conta no teste de atributos | 3.001 | sim | exato |
| base 17,3% sobre 3.839 negócios distintos | 17,3% sobre 3.839 | sim | exato (1º corte em que o negócio está vivo, decidiu em [c, c+28)) |
| 996 por braço (em `docs/experimento.md`) | 993 | quase | fórmula de duas proporções sem correção; diferença de 3 é de variante de fórmula |

### O achado central (734 vencidos, nenhum ganho)

Tentei refutar de três formas: com a regra completa (idade > ciclo máximo ou passou do fim do trimestre seguinte), só com o ciclo máximo (733 distintos) e com a convenção de fronteira trocada (`<=` em vez de `<`, 717 distintos). Em nenhuma variante aparece um negócio vencido com `deal_stage == "Won"` e `close_date` posterior ao corte. O número se sustenta.

A ressalva é sobre o que ele prova. Dos 734, 733 nunca fecharam: continuam em Engaging no fim do export, sem close_date. O único que fechou foi perdido, e é exatamente o fechamento fora do prazo usado para aprender a regra. Então "nenhum foi ganho" não é uma validação independente da regra do trimestre; é o mesmo fato do dado visto pelos dois lados. Nesse export, negócio que passa do fim do trimestre seguinte simplesmente para de se mover. A frase "não tem nenhuma chance histórica de fechar" está correta como descrição do export, mas o leitor pode entender que esses negócios foram observados morrendo (perdidos). Não foram: ficaram parados, e não se sabe por quê. A submissão reconhece em `docs/limitacoes.md` que a regra pode ser artefato do gerador sintético, o que é a leitura certa.

### A regra de "vencido" é aprendida ou escrita à mão?

As duas metades são diferentes.

- **Ciclo máximo (138 dias):** aprendido, é o máximo dos ciclos conhecidos na data. Não parece artefato de poucos pontos: a cauda é densa até o fim (entre 2 e 11 fechamentos por dia de ciclo de 128 a 137, e 2 em 138), um padrão de limite rígido de gerador, não de outlier isolado.
- **Fim do trimestre seguinte:** a forma da regra é escrita à mão (`motor/janela.py:16`, `QuarterBegin(2)`); o dado só decide se ela liga ou desliga (`tolerancia_prazo_trimestre`, `min_fechamentos_para_prazo`). A evidência é muito forte dentro do export (6.710 de 6.711 fecham até o prazo; 1% dos ganhos fecha com folga de até 1 dia, ou seja, a regra corta exatamente onde a massa acaba). Mas é uma hipótese de calendário testada contra o dado, não uma regra descoberta pelo dado. Dizer "aprendida do histórico, não escrita à mão" para essa metade é exagero leve; "escolhida à mão e confirmada pelo histórico" seria exato.

Achado lateral que reforça a natureza sintética: em cada início de trimestre, nenhum negócio de 16 a 30 dias decide nas 4 semanas seguintes; o primeiro fechamento desse grupo é sempre o dia 1 do mês seguinte (01/05, 01/08, 01/11). O "relógio" explora regularidades de calendário do gerador. Dentro do export elas são reais; fora dele, não há evidência.

## Vazamento temporal

O que chequei, com o meu recorte (`recorte(c)` no script) em 15/05, 28/08 e 23/10/2017: nenhum fechado visível com close_date ≥ c; nenhum aberto com estágio Won/Lost; nenhum aberto com close_date preenchido; nenhum visível engajado em c ou depois. O ciclo máximo aprendido em cada data só usa fechamentos anteriores a c. Depois li `motor/carregar.py:103-122` (`recortar`) e `motor/aprender.py`: a tabela das datas análogas só usa desfechos antes de A+28 e antes do início do trimestre de `hoje`, ambos anteriores a `hoje`. **Sem vazamento de desfecho.**

Dois vazamentos menores, que a submissão não menciona:

1. **O campo `account` não é apagado no recorte.** O próprio documento mostra que a conta só é preenchida depois do desfecho (0 de 6.711 fechados sem conta). Em cada corte, um negócio que só vai fechar depois já aparece com a conta do export final. O motor não usa a conta para ordenar, então o backtest de valor não é afetado. Mas a correção do teste de atributos (`avaliacao/permutacao.py:25`, `s.conta.notna()`) filtra justamente por esse campo vindo do futuro: a amostra de 3.001 é selecionada por "vai ter desfecho em algum momento, ou é um dos 664 abertos com conta". Como o filtro é igual para todos os grupos, o efeito provável é só na taxa-base, não no p-valor; mesmo assim é condicionar numa variável posterior ao corte, o mesmo tipo de erro que a correção quis tirar.
2. **`motor/carregar.py:113`** decide se descarta os Prospecting comparando `hoje` com `p["close_date"].max()` do export inteiro, ou seja, usa a maior data do futuro para saber se `hoje` está no passado. Só afeta quais negócios sem data entram no recorte (fora das filas), não o resultado.

## Viés de sobrevivência

Construí as duas tabelas (seção 6 da saída). Ingênua: só fechados, cada um contado em cada idade que atingiu; decidiu se fechou em até 28 dias daquela idade. Correta: todos os abertos em cortes semanais de 01/03 a 03/12/2017, incluindo os que nunca fecharam.

| Faixa | Ingênua | Correta (cortes semanais) |
|---|---|---|
| 91-105 | 89,7% | 34,6% |
| 106-120 | 98,9% | 21,0% |
| 121+ | 100% | 1,1% |

A afirmação central se confirma: a tabela ingênua dá praticamente 100% nas faixas altas, e só a tabela com os abertos no denominador derruba o número. **Uma correção de redação:** "essencialmente zero em 106-120" só vale nas datas análogas que o motor usa (inícios de trimestre: 01/04, 01/07, 01/10), onde a tabela publicada tem p = 0 em 106-120 e 121-138. Somando todas as semanas do ano, 106-120 decide 21% das vezes. A diferença é a posição no trimestre, e é por isso que o motor aprende em datas análogas e não em todas as semanas. A afirmação não está errada no contexto do motor, mas não é uma propriedade da idade sozinha.

Observação inversa: a tabela das datas análogas (`motor/aprender.py:47`) põe no denominador todos os abertos com idade ≤ 138, inclusive os que já passaram do prazo do trimestre e nunca vão fechar. Isso puxa as faixas altas para baixo pelo motivo oposto ao da sobrevivência. Na data de referência é inofensivo, porque nenhum vivo em 01/01/2018 tem mais de 92 dias.

## Backtest: o ganho do relógio se sustenta?

Duas tentativas, as duas no script:

- **Versão simplificada própria, antes de ler o motor (seção 7):** ordenar só pela chance de decidir da faixa (tabela semanal, sem valor), desempate pelo prazo. Ela **perde** para preço e prazo: razão 0,66, IC [0,50; 0,85]. Ou seja, o ganho não vem de "olhar o relógio em vez do valor".
- **Reimplementação da regra documentada (seção 7b):** chave = preço de tabela × chance de ganhar em 28 dias, aprendida nas datas análogas (c − 3, 6, 9 meses), fila "fechar" com p_decide ≥ 5%. Reproduz os seis cortes ao dólar e a razão 1,303.

Conclusão: o número 1,30 é real e reproduzível, mas o que vence é **valor esperado com sazonalidade do trimestre**, não tempo no lugar de valor. O README e o resumo dizem "priorizar pelo relógio do trimestre em vez de por valor"; a fórmula do relógio multiplica o valor. A frase devia ser "por valor esperado no trimestre, em vez de por valor de tabela".

Checagem de espantalho no baseline: `avaliacao/backtest.py:60` desempata "preço e prazo" por **mais** dias restantes primeiro (`dias_restantes` descendente). Com só 7 preços distintos, o desempate pesa muito. Testei o desempate oposto (menos dias restantes primeiro): o baseline fica pior (US$ 815.589) e a razão sobe para 1,345 [1,196; 1,536]. O baseline publicado é o mais forte dos dois, então não é espantalho. A palavra "prazo" no nome é ambígua: deveria dizer em que direção.

Também: "valor ganho" no backtest é preço de tabela dos ganhos, não `close_value`. É uma escolha defensável (a ferramenta só conhece preço de tabela), mas não está declarada no resumo.

## Atributos x ganhar

Dois desenhos, os dois sem sinal:

- Meu desenho (só fechados, ganho x perda, qui-quadrado e permutação estratificada por mês do trimestre): menor p = 0,226 (vendedor). Taxas de ganho por grupo variam pouco (gerente 62–64%, região 63–64%).
- Desenho do documento (1 registro por negócio vivo com conta, ganhou em 28 dias, variância entre grupos, 500 permutações estratificadas): conta 0,485, vendedor 0,150, gerente 0,455, região 0,289, setor 0,521, porte 0,581, produto 0,417. Batem com os do documento na faixa de ruído de Monte Carlo, exceto porte (0,983 no documento): eu fiz quartis sobre os negócios, o código faz quartis sobre as contas (`avaliacao/permutacao.py:18`). Conclusão igual.

Concordo: não há sinal de atributo, nos dois sentidos de "ganhar".

## Limiares fora de config.json

Nenhum limiar escondido muda a fila ou o estado de um negócio em produção, com uma exceção estrutural:

| Arquivo:linha | Valor | Natureza |
|---|---|---|
| `solution/motor/janela.py:16` | `QuarterBegin(2)`: prazo = fim do trimestre **seguinte** | regra de negócio escrita à mão; o dado só liga/desliga |
| `solution/motor/aprender.py:21` | `DateOffset(months=3)`: datas análogas a cada 3 meses | assume trimestre de calendário; não é aprendido nem configurável |
| `solution/motor/aprender.py:54` | `inicio_trimestre + 3 meses`: "até o fim do trimestre" | mesmo pressuposto de trimestre |
| `solution/motor/aprender.py:29` | faixas começam em 1 dia | negócio engajado no próprio dia (idade 0) fica sem faixa; irrelevante porque o recorte exige `engage_date < hoje` |
| `solution/avaliacao/backtest.py:21` | cortes `2017-07-03` a `2017-12-03`, `4W-MON` | o passo de 4 semanas repete o `horizonte_dias` à mão; se o horizonte mudar no config, as janelas passam a se sobrepor |
| `solution/avaliacao/backtest.py:16-17` | `RODADAS_ALEATORIO = 200`, `NUMERO_CONTROLE = 7` | parâmetro de avaliação; a semente duplica `config.json:semente` (7), que nenhum código Python lê |
| `solution/avaliacao/backtest.py:118` | `n = 5000` reamostras | parâmetro de avaliação |
| `solution/avaliacao/numeros.py:12-13` | `REPETICOES_PERMUTACAO = 1000`, `LIMITE_SINAL = 0.05` | parâmetro de avaliação |
| `solution/avaliacao/permutacao.py:18` | `qcut(..., 4)` para porte | parâmetro de avaliação |
| `solution/motor/carregar.py:10-11` | typos de setor e país | limpeza de dado, não regra |
| `solution/motor/explicar.py:36` | texto "Nas três viradas de trimestre anteriores" | fixo; certo em 01/01/2018, errado nos cortes de julho e agosto, que têm uma ou duas datas análogas |

Também, `janela.py:38` usa `<=` na tolerância, e `docs/logica.md` diz "menos de 0,1%". Sem efeito prático (a fração é 0,015%).

## Regra de negócio no front

Não encontrei decisão de estado, fila, chance ou elegibilidade em `solution/app/app.js`. Fila, posição, em_foco, p_decide, sinal dos atributos e "vivos" chegam prontos do JSON. Pontos de fronteira, todos menores:

- `app.js:310-311` soma no navegador o "valor vivo" por vendedor filtrando `d.estado === 'vivo'`. É agregação, não decisão, mas duplica um total que o back-end já poderia entregar.
- `app.js:338` calcula a taxa de discordância a partir das ações registradas. É métrica de operação calculada no front.
- `app.js:131` assume 13 semanas por trimestre; `app.js:414` escreve "5 deals por vendedor" em vez de ler `cfg.foco_por_vendedor`; `app.js:410` rotula "Preço até 138 dias" fixo; `app.js:432` escreve "mil vezes" e "0,05" fixos. Texto que pode desatualizar se o config ou o ciclo mudar.

## Números sem fonte confirmada por este revisor

- "detectá-lo exigiria **109 vendedores por braço**, e a operação tem 30" (`docs/resumo-executivo.md`, última seção). Não recalculei; exige a variância do valor ganho por vendedor e premissas de poder que não estão no resumo.
- "Taxa de acerto: aleatório **14,7%**" e "**1,54**" (só em `docs/logica.md` e `numeros-saida.txt`; o README não cita). Conferi só a divisão.
- "Valor ganho: oráculo **US$ 2.666.327**" e, por consequência, "**41%** do teto" e "**32%**": conferi só a divisão, não o oráculo.
- "**59 testes**" (README, Resultados): não executei a suíte.
- "Relógio sobre preço, até 138 dias: **1,26** (IC 1,13 a 1,44)" (`docs/logica.md`): não reimplementei essa política.
- "0,012 virou 0,141 ao filtrar deals sem conta" (README): reproduzi o 0,141 (0,150 com outra semente), não o 0,012.

Inconsistências de texto, não de número: `docs/logica.md:7` diz "cinco datas" e lista seis cortes na mesma página; o código gera seis. O enunciado desta verificação dizia "de 03/07/2017 a 03/12/2017"; 03/12 é o limite do `date_range`, o último corte real é 20/11/2017.

## Veredito

A submissão é confiável para o que afirma em número: todos os números de qualidade do dado, do pipeline e do backtest batem exatamente, a partir dos CSVs crus e com código independente, e não há vazamento de desfecho no recorte. As ressalvas são de interpretação, não de conta: (1) "nenhum vencido foi ganho" é verdadeiro mas quase circular, porque 733 dos 734 simplesmente nunca fecharam e a regra do trimestre foi escolhida à mão e confirmada pelo mesmo fato; (2) o ganho de 1,30× vem de valor esperado com sazonalidade de trimestre, não de "relógio em vez de valor", e uma ordenação só por tempo perde para preço; (3) "chance zero nas faixas altas" vale nas datas análogas, não para a idade em si; (4) o campo de conta vindo do futuro ainda filtra o teste de atributos. Tudo isso está num dataset sintético cujas regularidades de calendário são, muito provavelmente, do gerador, como a própria submissão reconhece.

## Comparação com o auto-relatado

Lido depois dos cálculos: `process-log/diario.md` e `process-log/onde-a-ia-errou.md`.

**Eles também encontraram:**
- O viés de sobrevivência da fórmula ingênua (100% aos 120 dias) e a correção com abertos no denominador. Confirmei.
- O vazamento do campo conta no teste de atributos (vendedor p = 0,012 → 0,141). Confirmei o 0,141 e os 3.001.
- Que o relógio perde no corte de 23/10 e que o argumento é o IC, não a consistência. Confirmei os valores.
- Que 11 dos 17 vendedores com vivo têm mais de cinco. Confirmei.
- A base do experimento (17,3% sobre 3.839, não 22%). Confirmei.
- Que 138 dias e a regra do trimestre podem ser artefato do gerador (`docs/limitacoes.md`).

**Não mencionam:**
- Que 733 dos 734 "vencidos sem ganho" nunca fecharam, o que torna o achado mais descritivo do que confirmatório.
- Que a forma da regra do trimestre é escrita à mão e só o liga/desliga é aprendido.
- Que o recorte não apaga `account`, e que a correção do teste de atributos filtra por esse campo vindo do futuro.
- `carregar.py:113` usando a maior data do export inteiro no recorte.
- Que uma ordenação só por tempo perde para preço (0,66×): o ganho depende de multiplicar valor por chance, e a frase "em vez de por valor" induz ao contrário.
- A direção do desempate do baseline "preço e prazo" (testei: o baseline publicado é o mais forte, então não muda a conclusão, mas não está documentado).
- Que "zero nas faixas 106-138" é propriedade das datas de início de trimestre, não da idade.
- O texto fixo "três viradas de trimestre" em `explicar.py:36`, a semente do `config.json` não lida, e o passo de 4 semanas dos cortes duplicando o horizonte.

**Nota sobre o protocolo:** `LEIA.md` pede um modelo de outra família. Este revisor é da mesma família (Claude) dos que implementaram. A independência aqui é de código e de ordem de leitura, não de família de modelo. A etapa com outra família continua pendente se o Diego quiser cumprir o protocolo à risca.
