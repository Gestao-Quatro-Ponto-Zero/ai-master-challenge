# Diário de bordo: como o case foi resolvido

**Candidato:** Liberato Gonçalves Gouveia
**Case:** 003 Lead Scorer (Vendas / RevOps)
**Ferramenta de IA:** Claude (app Claude, modo agente com acesso a terminal, Python e internet)
**Divisão do trabalho:** Liberato toma as decisões de negócio e aprova cada etapa. O Claude faz a execução técnica (baixar dados, rodar análises, escrever código) e explica cada passo.

> Este diário é atualizado a cada etapa. Cada número citado aqui vem de um script salvo na pasta `analises/`, junto com a saída dele em `analises/resultados/`. Qualquer pessoa pode rodar de novo e conferir.

---

## Etapa 0: Ler as regras antes de começar (03/11)

**O que foi feito:** leitura completa do repositório do desafio: regras gerais, guia de submissão, regras do Pull Request, modelo de README e os 4 cases.

**O que aprendemos e que mudou a estratégia:**
- O G4 já passou cada case pelo Claude, pelo GPT e pelo Gemini. Entregar algo parecido com essas respostas elimina o candidato. Precisamos **superar** o que a IA faz sozinha.
- Sem registro do processo (este diário), a entrega é desclassificada.
- O case 003 pede **software funcionando**, não um documento. Ele tem que usar os dados reais, explicar **por que** cada deal tem nota alta ou baixa e ser fácil para um vendedor que não é técnico.

## Etapa 1: Escolha do case e da forma de trabalhar (03/11, decisão do Liberato)

- **Case escolhido:** 003 Lead Scorer, por ser o mais próximo da experiência do Liberato com CRM e geração de leads (Motor de Leads, OrbittaIA).
- **Forma de trabalho:** o Liberato decide e o Claude executa, com paradas de aprovação.

## Etapa 2: Conseguir os dados reais

**O que foi feito:** o case manda baixar os dados do Kaggle (site de bases de dados). O ambiente do Claude tem a internet restrita e o Kaggle está bloqueado. A saída foi procurar cópias públicas da mesma base no GitHub.

**Como garantimos que os dados são os certos:**
1. A base é pública e conhecida. Ela foi criada pela Maven Analytics e mostra uma empresa **fictícia** que vende hardware.
2. Baixamos **duas cópias independentes**, de pessoas diferentes, e comparamos as duas registro por registro: **o conteúdo é idêntico**.
3. As contagens batem exatamente com o que o README do case descreve: 8.800 oportunidades, 85 contas, 35 vendedores e 7 produtos.
4. A única diferença entre as cópias: uma delas corrigiu o nome do produto "GTXPro" para "GTX Pro". Usamos a versão **sem correção**, que é mais fiel à original, e fazemos a correção dentro do nosso código (ver Etapa 3).

**Pendência:** se o Liberato quiser confirmar 100%, pode baixar o arquivo original do Kaggle num computador e comparar. É opcional.

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

## Etapa 4: O que separa um deal ganho de um perdido?

**O que foi feito:** para os 6.711 deals já fechados, calculamos a **taxa de ganho** (quantos % foram ganhos) separando por produto, setor, região, gerente, vendedor e tamanho da empresa (`analises/eda2.py`).

**Resultado:** a taxa média é **63%**, e quase tudo fica perto disso:
- Por produto: entre 60% e 65%
- Por setor: entre 61% e 65%
- Por região: entre 63% e 64%
- Por gerente: entre 62% e 64%
- Por vendedor: entre 55% e 70%. Parece uma diferença grande, mas a Etapa 5 mostra que não é.

## Etapa 5: Essas diferenças são reais ou é sorte?

**O que foi feito:** um teste estatístico (`analises/eda3.py`).

**Explicação simples:** jogue uma moeda 100 vezes e o resultado não vai ser exatamente 50 caras. Vai dar 45, 53, 56... Isso é variação natural. O teste mede se a diferença entre, por exemplo, os vendedores é **maior** do que a variação que a sorte sozinha produziria. O número que decide se chama **p**. Pela convenção, a diferença só é considerada real se p for menor que 0,05.

| Fator | p | Conclusão |
|---|---|---|
| Vendedor | 0,26 | Cabe no acaso |
| Produto | 0,37 | Cabe no acaso |
| Gerente | 0,79 | Cabe no acaso |
| Empresa (conta) | 0,94 | Cabe no acaso |
| Vendedor × produto | 0,46 | Cabe no acaso |

**Conclusão:** nesta base, **produto, setor, empresa, gerente e vendedor não preveem se um deal vai ser ganho.** Uma ferramenta que dá pontos por "produto que vende mais" ou "setor que fecha mais" está ranqueando ruído. Esse é justamente o tipo de ferramenta que uma IA monta quando recebe o brief sem análise.

### O que tem sinal de verdade: tempo e valor

**Tempo.** Analisamos quanto tempo cada deal levou do início da negociação até fechar:
- Deals que fecham na **primeira semana** ganham só ~53% das vezes. O "não" costuma vir rápido.
- Um deal que **passou de 14 dias** vivo fecha ganho ~67–70% das vezes.
- **Nenhum deal da história levou mais de 138 dias para fechar.** 99% fecharam em até 127 dias.

**Cuidado que tomamos (uma armadilha evitada):** os deals iniciados em 2016 só aparecem fechados a partir de março/2017, porque a base começa a registrar fechamentos nessa data. Isso infla artificialmente o resultado dos deals "antigos". Para não cair nisso, refizemos a conta usando só os deals iniciados entre março e agosto/2017, que tiveram tempo de sobra para fechar.

**O pipeline está cheio de "zumbis":** em 31/12/2017, **1.291 dos 1.589 deals em negociação (81%) estavam abertos há mais de 138 dias**, mais tempo do que qualquer deal já levou para fechar. Na prática, são deals mortos que ninguém encerrou no CRM.

**A armadilha:** a tabela crua mostra que "deals que demoraram mais de 120 dias ganharam 75,6%". Uma leitura apressada conclui que quanto mais velho, melhor, e coloca os 1.291 zumbis **no topo** do ranking. Isso só vale até 138 dias. Depois disso não existe nenhum exemplo real.

**Valor.** O preço varia de US$ 55 (MG Special) a US$ 26.768 (GTK 500), e deals ganhos fecham praticamente pelo preço de tabela (em média 99,6% dele). Os **428 deals abertos de MG Special somam US$ 23.540**, menos de 1% do valor em aberto e menos do que um único GTK 500.

## Etapa 6: Prova final com machine learning

**O que foi feito:** treinamos dois modelos de machine learning (`analises/model_check.py`) com **todos** os dados de cada deal: produto, preço, vendedor, gerente, região, setor, tamanho e país da empresa, histórico de compras da empresa e mês de início.

**Como ler o resultado (AUC):** pegue ao acaso um deal ganho e um perdido e pergunte ao modelo qual dos dois foi ganho. A AUC é a porcentagem de acertos. Chute puro dá 50%. Um modelo útil costuma passar de 70%.

**Resultado:** **AUC de 54%** no melhor modelo e de 52% no outro. Com todos os dados juntos, o modelo é quase um chute. Isso confirma a Etapa 5 por outro caminho.

**O que isso muda na ferramenta:** a nota de cada deal vai se basear no que tem sinal comprovado:
**chance de fechar (pelo tempo de vida do deal) × valor do produto.**
Os outros fatores aparecem na tela como informação, mas **não** mudam a nota. A ferramenta explica ao usuário por quê.

## Etapa 7: Decisões do Liberato (04/11)

Com base nos achados acima, o Liberato decidiu:

1. **Deals zumbis (mais de 138 dias):** saem do ranking de foco e vão para uma lista separada, "Requalificar ou encerrar".
2. **Deals de valor muito baixo (ex.: MG Special):** saem do foco do vendedor e são marcados para cadência automática (mensagens em lote).
3. **Usuário:** o vendedor, com a "minha lista do dia", mais uma visão do gerente usando filtros por vendedor, gerente e região.
4. **Regras de experiência em vendas que entram na ferramenta:**
   - **Requalificar antes de matar:** um deal grande parado ganha uma ligação de requalificação antes de ser encerrado.
   - **Deal sem conta = sem dono:** um deal sem empresa cadastrada vira tarefa de cadastro antes de qualquer contato.
   - **Janela de ouro (14 a 138 dias):** um deal que já passou da primeira semana e ainda está dentro do ciclo normal é onde o vendedor tem mais alavanca, e por isso ganha destaque.

---

## Verificações que evitaram conclusões erradas (até aqui)

| O que poderia dar errado | Como foi pego |
|---|---|
| 1.480 deals sem preço por causa do nome "GTXPro" | Raio-X comparou os nomes do pipeline com os do catálogo (Etapa 3) |
| Superestimar deals antigos por causa do corte de datas da base | Análise refeita só com os deals que tiveram tempo de fechar (Etapa 5) |
| Colocar zumbis no topo ao extrapolar "deal longo fecha mais" | Limite de 138 dias tirado do histórico real (Etapa 5) |
| Dar nota usando fatores que são ruído | Teste estatístico + modelo de machine learning (Etapas 5 e 6) |

## Glossário

- **Pipeline:** a lista de todas as oportunidades de venda e da etapa em que cada uma está.
- **Deal / oportunidade:** uma possível venda de um produto para uma empresa.
- **Etapas do deal:** Prospecting (prospecção, contato inicial) → Engaging (negociação) → Won (ganho) ou Lost (perdido).
- **Taxa de ganho:** de cada 100 deals fechados, quantos foram ganhos.
- **Script Python:** um arquivo com instruções que o computador executa. Fica salvo, então qualquer pessoa pode rodar de novo e chegar aos mesmos números.
- **CSV:** uma planilha em formato de texto simples.
- **p (valor-p):** a chance de uma diferença aparecer só por sorte. Abaixo de 0,05, a diferença é considerada real.
- **AUC:** a nota de um modelo de previsão. 50% é chute e acima de 70% é útil.
- **Ciclo:** os dias entre o início da negociação e o fechamento.
- **Deal zumbi:** um deal aberto há mais tempo do que qualquer deal já levou para fechar.
- **Valor esperado:** a chance de fechar × o valor. Um deal de US$ 5.000 com 60% de chance "vale" US$ 3.000 na fila de prioridade.
- **Fork / branch / Pull Request:** a forma de entregar no GitHub. O fork é a sua cópia do repositório do G4. A branch é uma linha de trabalho dentro dessa cópia. O Pull Request é o pedido para o G4 receber a sua pasta.

## Evidências deste processo

- Este diário
- Os scripts e as saídas em `analises/` (dá para rodar de novo e conferir cada número)
- A conversa com o Claude: prints ou link de compartilhamento, a serem anexados em `process-log/`
