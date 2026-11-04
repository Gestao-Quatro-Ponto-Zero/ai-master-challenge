# Diário de bordo: como o case foi resolvido

**Candidato:** Liberato Gonçalves Gouveia
**Case:** 003 Lead Scorer (Vendas / RevOps)
**Ferramenta de IA:** Claude (app Claude, modo agente com acesso a terminal, Python e internet)
**Divisão do trabalho:** Liberato toma as decisões de negócio e aprova cada etapa. O Claude faz a execução técnica (baixar dados, rodar análises, escrever código) e explica cada passo.

> **O que é este documento:** é a peça principal do *process log*, o registro de como a IA foi usada, que o G4 exige em toda entrega. Ele conta, etapa por etapa, o que foi feito, por quê, o que deu errado e quem decidiu o quê. Junto com ele vão os scripts, os gráficos, os prints da conversa com o Claude e o histórico de versões.
>
> Este diário cobre a análise inicial (Etapas 0 a 7). A partir de 04/11, cada fase do plano tem um registro padronizado em [`registros-por-etapa.md`](registros-por-etapa.md).
>
> Este diário é atualizado a cada etapa. Cada número citado aqui vem de um script salvo na pasta `analises/`, junto com a saída dele em `analises/resultados/`. Qualquer pessoa pode rodar de novo e conferir.

---

## Etapa 0: Ler as regras antes de começar (03/11)

**O que foi feito:** leitura completa do repositório do desafio: regras gerais, guia de submissão, regras do Pull Request, modelo de README e os 4 cases.

**O que aprendemos e que mudou a estratégia:**
- O G4 já passou cada case pelo Claude, pelo GPT e pelo Gemini. Entregar algo parecido com essas respostas elimina o candidato. Precisamos **superar** o que a IA faz sozinha.
- Sem registro do processo (este diário), a entrega é desclassificada.
- O case 003 pede **software funcionando**, não um documento. Ele tem que usar os dados reais, explicar **por que** cada deal tem nota alta ou baixa e ser fácil para um vendedor que não é técnico.

## Etapa 1: Escolha do case e da forma de trabalhar (03/11)

- **Case:** entre as 4 opções, o Claude recomendou o 003 Lead Scorer, porque a entrega é um software funcionando e o tema é próximo da experiência do Liberato com CRM e geração de leads. **O Liberato escolheu o 003.**
- **Forma de trabalho:** o Claude ofereceu duas opções: "o Claude executa e o Liberato decide" ou "o Liberato executa e o Claude guia". **O Liberato escolheu a primeira**, com paradas para aprovação.

## Etapa 2: Conseguir os dados reais

**O que foi feito:** o case manda baixar os dados do Kaggle (site de bases de dados). O ambiente do Claude tem a internet restrita e o Kaggle está bloqueado. A saída foi procurar cópias públicas da mesma base no GitHub.

**Como garantimos que os dados são os certos:**
1. A base é pública e conhecida. Ela foi criada pela Maven Analytics e mostra uma empresa **fictícia** que vende hardware.
2. Baixamos **duas cópias independentes**, de pessoas diferentes, e comparamos as duas registro por registro: **o conteúdo é idêntico**.
3. As contagens batem exatamente com o que o README do case descreve: 8.800 oportunidades, 85 contas, 35 vendedores e 7 produtos.
4. A única diferença entre as cópias: uma delas corrigiu o nome do produto "GTXPro" para "GTX Pro". Usamos a versão **sem correção**, que é mais fiel à original, e fazemos a correção dentro do nosso código (ver Etapa 3).

**Confirmado na Fase 1:** o Liberato baixou o arquivo oficial no Kaggle e enviou na conversa. Os 5 arquivos são **idênticos byte a byte** aos que usamos (`analises/resultados/fase1_item_H_kaggle.txt`). O arquivo oficial também traz o erro "GTXPro".

## Etapa 3: Raio-X dos dados (o que tem, o que falta, o que está errado)

**O que foi feito:** um script, ou seja, uma receita de instruções que o computador executa (`analises/eda1.py`), contou registros, campos vazios, datas e inconsistências.

**O que encontramos:**

| Achado | Por que importa |
|---|---|
| O pipeline tem 4.238 ganhos, 2.473 perdidos, 1.589 em negociação e 500 em prospecção | Só os **2.089 abertos** (negociação + prospecção) recebem nota. Os fechados servem para aprender o que funciona. |
| **1.425 dos 2.089 deals abertos (68%) não têm empresa cadastrada** | O vendedor não sabe para quem ligar. É um problema de cadastro no CRM, não de vendas. |
| O produto aparece como "GTXPro" em 1.480 linhas, mas no catálogo o nome é "GTX Pro" | Sem corrigir, 1.480 deals ficariam **sem preço**, e qualquer nota que use valor sairia errada. |
| Os deals em prospecção não têm data de início | Não dá para medir há quanto tempo estão parados. |
| Os dados vão de out/2016 a 31/dez/2017 | A ferramenta "enxerga" o pipeline como estava em **31/12/2017**, como se hoje fosse esse dia. |
| 5 vendedores não têm nenhum deal | Provavelmente são contratações novas. Não afetam a nota. |
| Erros de digitação ("technolgy", "Philipines") | São detalhes, mas mostram que a base não é limpa. |

## Resumo das Etapas 4, 5 e 6

> Testamos se as características "óbvias" de um deal (produto, setor, vendedor…) ajudam a prever se ele vai ser ganho. **Não ajudam.** O que ajuda é **há quanto tempo o deal está vivo** e **quanto ele vale**. A ferramenta foi desenhada em cima disso.

## Etapa 4: As características "óbvias" fazem diferença?

**A pergunta.** Sabendo o produto, o setor da empresa, a região, o gerente ou o vendedor de um deal, dá para saber se ele tem mais chance de ser ganho? A maioria das ferramentas de score parte desse princípio e dá pontos para "o produto que mais vende", "o setor que mais compra" e assim por diante.

**Como respondemos.** Pegamos os 6.711 deals que já terminaram, ganhos ou perdidos, e fizemos uma conta simples para cada grupo: de cada 100 deals daquele grupo, quantos foram ganhos? Por exemplo, dos 1.436 deals de GTX Basic, 915 foram ganhos, o que dá **64 em cada 100**. Dos 1.084 de MG Advanced, 654 foram ganhos, ou **60 em cada 100**.

**O que encontramos (Gráfico 1).** Todos os grupos ficam colados na média de 63%. O pior produto ganha 60 de cada 100 e o melhor, 65. Com setor, região e gerente acontece a mesma coisa.

![Gráfico 1](graficos/grafico1_fatores.png)

**E os vendedores?** Aqui a diferença parece maior: o pior ganha 55 de cada 100 e o melhor, 70. À primeira vista, alguns vendedores parecem bem melhores que outros. Mas será que são?

**O teste da moeda (Gráfico 2).** Fizemos uma simulação no computador (`analises/simulacao_sorte.py`). Criamos 30 vendedores **imaginários e idênticos**, todos com exatamente 63% de chance de ganhar cada deal e cada um com a mesma quantidade de deals do vendedor real correspondente. Repetimos isso 10.000 vezes. Mesmo sendo idênticos, **só por sorte o "pior" fica em ~56% e o "melhor" em ~70%**. É praticamente a mesma diferença que vemos entre os vendedores reais (55% a 70%).

É como 30 pessoas jogando moeda: alguém vai tirar mais caras que os outros, e isso não quer dizer que ele joga moeda melhor.

![Gráfico 2](graficos/grafico2_sorte.png)

**O que isso muda na ferramenta.** Produto, setor, região, gerente e vendedor **não entram na nota**. Eles aparecem na tela como informação, mas não mexem no ranking. Uma ferramenta que desse pontos por eles estaria ordenando os deals por sorte.

> **Para explicar na entrevista:** "Antes de dar peso a qualquer característica, testei se ela realmente separa deal ganho de perdido. Nenhuma das óbvias separa. A diferença entre os vendedores, por exemplo, é do mesmo tamanho que a sorte produziria com 30 vendedores idênticos."

## Etapa 5: Então o que faz diferença? Tempo e valor

**A pergunta.** Se as características do deal não ajudam a prever, o que ajuda?

**Tempo (corrigido na Fase 1, Gráfico 6).** Para um deal aberto, a pergunta certa é: "dos deals que chegaram vivos até esta idade, quantos acabaram ganhos?". Essa conta usa só o que se sabe hoje, que é a idade do deal. O resultado:
- Deal novo (até 14 dias): **52–53%** acabam ganhos.
- Com 60 dias: **48%**.
- Com 90 dias: **37%**.
- Com 120 dias: **5%**.
- Com 138 dias ou mais: **0%**. Nenhum deal, de nenhuma safra, fechou depois disso.

Ou seja: **quanto mais velho o deal aberto, menor a chance de ser ganho**, e a queda fica forte a partir dos 90 dias.

![Gráfico 6](graficos/grafico6_chance_por_idade.png)

> **Correção registrada.** A primeira versão desta etapa dizia o contrário: que deals com mais de 14 dias fecham mais (65–75%), com base no Gráfico 3 abaixo. Aquela conta tinha dois problemas. (1) Olhava só os deals que já tinham terminado e ignorava os que nunca fecham. (2) Agrupava os deals pela duração total, que um deal aberto ainda não conhece. Isso é "vazamento de futuro". O erro foi da análise feita pela IA e apareceu na revisão crítica pedida pelo Liberato (regra 7: evitar vazamento de informações futuras). O Gráfico 3 fica aqui só como registro histórico.

![Gráfico 3 (versão original, substituída pelo Gráfico 6)](graficos/grafico3_tempo.png)

**O limite de 138 dias é real (verificado na Fase 1).** Os deals iniciados em fevereiro/2017 tiveram 333 dias para fechar e, mesmo assim, nenhum passou de 137. O mesmo acontece em todas as safras, então o limite não é efeito do período coberto pela base.

**Deals fora do padrão histórico, os "zumbis" (Gráfico 4).** Em 31/12/2017, **1.291 dos 1.589 deals em negociação (81%) estavam abertos há mais de 138 dias**, alguns havia 423 dias. Os dados mostram que nenhum deal fechou depois de 138 dias. **Não sabemos o destino real desses deals.** Podem estar mortos e esquecidos no CRM, ou pode ser um efeito de como a base foi gerada. Para a ferramenta, eles estão fora do padrão histórico e precisam ser requalificados antes de receber atenção.

![Gráfico 4](graficos/grafico4_zumbis.png)

**A armadilha.** Quem lesse o Gráfico 3 ao pé da letra colocaria os deals mais velhos no topo do ranking, justamente os que têm menos chance. A primeira análise caiu nessa armadilha, e a Fase 1 corrigiu.

**Valor.** O preço dos produtos vai de US$ 55 (MG Special) a US$ 26.768 (GTK 500), e os deals ganhos fecham praticamente pelo preço de tabela. Entre os deals vivos, a chance varia de ~53% a ~37% conforme a idade, enquanto o valor varia quase 500 vezes. Por isso, **o valor é o que mais diferencia um deal do outro na hora de priorizar**. Um exemplo: os **428 deals abertos de MG Special somam US$ 23.540**, menos de 1% do valor em aberto e menos do que um único GTK 500.

> **Para explicar na entrevista:** "Num deal aberto, eu só posso usar o que sei hoje: a idade dele. Medindo assim, a chance cai com o tempo: 53% para um deal novo, 37% aos 90 dias e quase zero depois de 120. Nenhum deal da história fechou depois de 138 dias, então 81% do pipeline aberto está fora do padrão e não pode ficar no topo da lista. A primeira análise da IA tinha concluído o contrário. A revisão que eu pedi, com a regra de evitar vazamento de futuro, expôs o erro."

## Etapa 6: Contraprova com machine learning

**A pergunta.** E se as características, combinadas de um jeito que não pensamos, conseguissem prever o resultado? Para descartar essa hipótese, usamos machine learning.

**O que é, em uma frase.** Um programa que estuda milhares de exemplos e tenta descobrir um padrão sozinho. Demos a ele **todas** as informações de cada deal: produto, preço, vendedor, gerente, região, setor, tamanho e país da empresa, histórico de compras da empresa e mês de início (`analises/model_check.py`).

**Como testamos de forma justa (prova com gabarito escondido).** Dividimos os deals em 5 partes. O programa estuda 4 delas e tenta adivinhar o resultado da 5ª, que nunca viu. Repetimos 5 vezes, escondendo uma parte diferente a cada vez.

**Como lemos a nota (AUC).** Mostramos ao programa pares de deals que ele nunca viu, sempre um ganho e um perdido, e perguntamos qual dos dois foi ganho. A AUC é a porcentagem de acertos. Quem chuta acerta 50%. Um modelo útil costuma passar de 70%.

**Resultado:** o programa acertou **54%** (Gráfico 5). Mesmo com todas as informações juntas, ele é quase um chute. Isso confirma, por outro caminho, o que as Etapas 4 e 5 mostraram.

![Gráfico 5](graficos/grafico5_auc.png)

**O que isso muda na ferramenta.** A nota de cada deal se baseia só no que tem efeito comprovado:
**chance de fechar (pela idade do deal, curva do Gráfico 6) × valor do produto.**
A tela vai explicar isso ao vendedor em linguagem simples.

> **Para explicar na entrevista:** "Para garantir que não estava deixando passar nada, pedi ao Claude que treinasse um modelo com todas as variáveis e o testasse em deals que ele nunca tinha visto. Ele acertou 54%, quase cara ou coroa. Por isso a nota usa só tempo e valor, e eu consigo explicar cada ponto dela."

## Etapa 7: Decisões do Liberato (04/11)

**Como as decisões foram tomadas:** para cada ponto, o Claude apresentou de 2 a 3 opções e marcou uma como recomendada, e o Liberato escolheu. Nos itens 1 a 3, ele ficou com a opção recomendada. No item 4, selecionou as três regras sugeridas. Ou seja: **as opções foram formuladas pela IA e a escolha foi do Liberato.** Nenhuma das regras abaixo foi criada por ele do zero, e isso fica registrado para não atribuir a ele algo que veio da IA.

1. **Deals zumbis (mais de 138 dias):** saem do ranking de foco e vão para uma lista separada, "Requalificar ou encerrar".
2. **Deals de valor muito baixo (ex.: MG Special):** saem do foco do vendedor e são marcados para cadência automática (mensagens em lote).
3. **Usuário:** o vendedor, com a "minha lista do dia", mais uma visão do gerente usando filtros por vendedor, gerente e região.
4. **Regras de vendas que entram na ferramenta (sugeridas pelo Claude, selecionadas pelo Liberato):**
   - **Requalificar antes de matar:** um deal grande parado ganha uma ligação de requalificação antes de ser encerrado.
   - **Deal sem conta = sem dono:** um deal sem empresa cadastrada vira tarefa de cadastro antes de qualquer contato.
   - **Janela de ouro (14 a 138 dias):** um deal que já passou da primeira semana e ainda está dentro do ciclo normal é onde o vendedor tem mais alavanca, e por isso ganha destaque.

   *Atualização (Fase 1):* testadas nos dados, as regras "sem conta = sem dono" e "janela de ouro" não se sustentam como estão escritas (ver Registro 02 em `registros-por-etapa.md`). A decisão sobre elas está com o Liberato.

**Intervenção do Liberato no mesmo momento:** junto com as respostas, ele escreveu: *"antes de continuar o trabalho, vc precisa me explicar o que está fazendo, nao tenho conhecimento tecnico e preciso que seja mais explicativo nos seus passos, nesse teste eu preciso documentar os log, os processos, e eu nao sei o que voce está fazendo!"*. O Claude parou a construção, e este diário nasceu desse pedido.

---

## Verificações que evitaram conclusões erradas (até aqui)

| O que poderia dar errado | Como foi pego |
|---|---|
| 1.480 deals sem preço por causa do nome "GTXPro" | Raio-X comparou os nomes do pipeline com os do catálogo (Etapa 3) |
| Superestimar deals antigos por causa do corte de datas da base | Análise refeita só com os deals que tiveram tempo de fechar (Etapa 5, Gráfico 3) |
| Colocar zumbis no topo ao extrapolar "deal longo fecha mais" | Limite de 138 dias tirado do histórico real (Etapa 5, Gráfico 4) |
| Concluir que deal aberto mais velho fecha mais (a conta original usava a duração total e ignorava os deals que nunca fecham) | Fase 1, item A: refeita só com a idade atual (Gráfico 6). A conclusão se inverteu |
| Tratar o limite de 138 dias como efeito do período coberto pela base | Fase 1, item B: conferido safra por safra |
| Dar nota usando fatores que são ruído | Simulação do "teste da moeda", teste estatístico e modelo de machine learning (Etapas 4 e 6) |

## Glossário

- **Pipeline:** a lista de todas as oportunidades de venda e da etapa em que cada uma está.
- **Deal / oportunidade:** uma possível venda de um produto para uma empresa.
- **Etapas do deal:** Prospecting (prospecção, contato inicial) → Engaging (negociação) → Won (ganho) ou Lost (perdido).
- **Taxa de ganho:** de cada 100 deals fechados, quantos foram ganhos.
- **Script Python:** um arquivo com instruções que o computador executa. Fica salvo, então qualquer pessoa pode rodar de novo e chegar aos mesmos números.
- **CSV:** uma planilha em formato de texto simples.
- **Vazamento de futuro:** usar na nota uma informação que só existe depois que o deal termina, como a data de fechamento. É como prever um jogo olhando o placar final.
- **Safra:** grupo de deals que começaram no mesmo período.
- **Simulação:** o computador "inventa" milhares de cenários seguindo uma regra (aqui, a de que todos os vendedores são iguais) para ver o que a sorte sozinha produz.
- **Machine learning:** um programa que aprende padrões a partir de exemplos, em vez de seguir regras escritas por uma pessoa.
- **p (valor-p):** a chance de uma diferença aparecer só por sorte. Abaixo de 0,05, a diferença é considerada real.
- **AUC:** a nota de um modelo de previsão. 50% é chute e acima de 70% é útil.
- **Ciclo:** os dias entre o início da negociação e o fechamento.
- **Deal zumbi:** um deal aberto há mais tempo do que qualquer deal já levou para fechar.
- **Valor esperado:** a chance de fechar × o valor. Um deal de US$ 5.000 com 60% de chance "vale" US$ 3.000 na fila de prioridade.
- **Fork / branch / Pull Request:** a forma de entregar no GitHub. O fork é a sua cópia do repositório do G4. A branch é uma linha de trabalho dentro dessa cópia. O Pull Request é o pedido para o G4 receber a sua pasta.

## Evidências deste processo

- Este diário
- Os scripts e as saídas em `analises/` (dá para rodar de novo e conferir cada número)
- Os gráficos em `graficos/`, gerados pelo script `analises/graficos.py` a partir dos dados reais
- As versões anteriores deste diário em `versoes/`, que mostram como o texto foi revisado
- A conversa com o Claude: prints ou link de compartilhamento, a serem anexados em `process-log/`

---

## Apêndice técnico (para avaliadores)

| Teste | Resultado | Leitura |
|---|---|---|
| Qui-quadrado de homogeneidade, taxa de ganho por vendedor | χ²=33,3; gl=29; p=0,26 | Não rejeita "todos iguais" |
| Idem por produto | χ²=6,5; gl=6; p=0,37 | Não rejeita |
| Idem por gerente | χ²=2,4; gl=5; p=0,79 | Não rejeita |
| Idem por conta (85 empresas) | χ²=64,6; gl=84; p=0,94 | Não rejeita |
| Idem vendedor × produto (células com n ≥ 15) | χ²=149,2; gl=148; p=0,46 | Não rejeita |
| Simulação binomial (10.000 rodadas, p=0,632, n real de cada vendedor) | Amplitude real 15,4 p.p.; em 36,9% das rodadas a amplitude simulada foi ≥ a real | A amplitude real é típica do acaso |
| HistGradientBoosting, validação cruzada estratificada com 5 folds | AUC 0,543 | Sem poder preditivo útil |
| Regressão logística, mesmas features | AUC 0,520 | Idem |
| Validação temporal (Fase 1): treino com deals iniciados até 16/08/2017 e teste com os posteriores | AUC 0,476 (GB) e 0,517 (LR) | Confirma a ausência de sinal |
| Chance por idade atual (Fase 1), safra mar–jun/2017, acompanhamento ≥ 184 dias | Ganho: 53% (0 d), 52% (14 d), 48% (60 d), 37% (90 d), 5% (120 d), 0% (138 d) | Base da nota, sem vazamento |
| Ciclo dos deals fechados | máx. 138 dias; p95 = 114,5; p99 = 127 | Base do limite "zumbi" |

Features usadas nos modelos: dummies de vendedor, produto, gerente, região, setor e país; preço; receita, funcionários e ano de fundação da conta; vitórias anteriores da conta (no geral e no mesmo produto) antes da data de início do deal; mês e dia da semana de início; razão preço/receita.

## Revisões deste diário

| Data | O que mudou | Por quê |
|---|---|---|
| 04/11 (madrugada) | Primeira versão (Etapas 0 a 7) | Registro inicial do processo |
| 04/11 (tarde) | Etapas 4, 5 e 6 reescritas com exemplos, 5 gráficos e uma simulação nova ("teste da moeda"). Os detalhes técnicos foram para este apêndice | O Liberato leu a primeira versão e achou essas etapas difíceis de entender. Se quem conduz o processo não entende, o vendedor e o avaliador também não vão entender. A versão anterior está em `versoes/` |
| 04/11 (fim da tarde) | Atribuição corrigida nas Etapas 1 e 7: as opções foram sugeridas pela IA e escolhidas pelo Liberato | Revisão crítica pedida pelo Liberato, cuja regra 5 manda separar o que a IA sugeriu do que ele validou. A versão anterior está em `versoes/` |
| 04/11 (noite) | Etapa 5 corrigida: a chance de um deal aberto cai com a idade (Gráfico 6, novo). O limite de 138 dias foi confirmado, a linguagem sobre os "zumbis" foi ajustada e a pendência do Kaggle foi resolvida | Fase 1 de verificação, autorizada pelo Liberato. A versão anterior está em `versoes/` |
