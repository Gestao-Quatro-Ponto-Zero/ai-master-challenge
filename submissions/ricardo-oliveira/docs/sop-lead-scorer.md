SOP do case G4 Educação AI Master, Challenge 003 (Lead Scorer). Passo a passo de como a gente sai de 8.800 oportunidades num CRM e chega numa ferramenta que o vendedor abre na segunda de manhã e sabe onde focar. Esta é a cópia do SOP que vale pra submissão, atualizada em 23/10 com as decisões da terceira rodada de revisão; o resumo executável está em `logica.md`, e as fórmulas que executam cada regra, em `../solution/sheet/formulas.md`.

## O problema que estamos resolvendo

A Head de RevOps falou duas dores, e a ferramenta tem que atacar as duas:

1. **Tempo gasto em deal que não vai fechar.** O vendedor precisa saber o que largar.
2. **Deal bom esfriando.** O vendedor precisa saber o que não pode esperar.

E uma restrição: tem que funcionar e ser usado. Nada de modelo no Jupyter que ninguém abre.

> **A lógica do SOP**
> Prioridade vem em três camadas, nessa ordem. **1. ICP:** essa conta parece com quem compra, compra mais e fica? **2. MEDDPICC:** a gente tem o que precisa saber pra mover esse deal, ou é só um nome no pipeline? **3. Momento:** o deal está andando ou esfriando? Só depois das três a gente fala em prioridade. (O MEDDPICC acabou ficando de lado por falta de dado: veja a Etapa 5.) Ordenar por valor não é priorizar.

## O que os dados têm (e o que não têm)

Olhamos o arquivo antes de escrever este SOP (23/10). O que muda o plano:

- **Pipeline:** 8.800 oportunidades. 4.238 ganhas, 2.473 perdidas, 1.589 em Engaging, 500 em Prospecting. Ou seja, **2.089 abertas** pra priorizar e **6.711 fechadas** pra aprender.
- **68% dos deals abertos não têm conta** (1.425 de 2.089: 1.088 em Engaging, 337 em Prospecting). Sem conta, não dá pra comparar com o ICP. Isso já é um achado de qualificação, não só um buraco no dado.
- **Prospecting não tem data nenhuma.** Não dá pra medir idade desses 500.
- **Período:** engajamentos de 20/10/2016 a 27/12/2017, fechamentos até 31/12/2017. "Hoje", na ferramenta, vai ser 31/12/2017.
- **Contas:** 85, todas com pelo menos 23 deals ganhos. Todo mundo compra. Então o ICP não sai de "quem compra vs quem não compra", sai de **quem compra melhor**: ganha mais, paga mais, volta mais, sobe de produto.
- **Região é do vendedor, não do cliente.** Central, East e West são escritórios do time comercial. As mesmas contas são trabalhadas por várias regiões (71 contas pelas três, 14 por duas). 71 das 85 contas têm sede nos EUA.
- **Time:** 35 vendedores, 6 managers, 3 regiões. 5 vendedores não têm nenhum deal.
- **Não existe campo de renovação, contrato ou churn.** Retenção só por aproximação: recompra ao longo do tempo e expansão pra produto mais caro, dentro de 14 meses.
- **Moeda:** o dataset não traz moeda, só o número. Formatamos os valores em dólar porque os clientes são internacionais (71 das 85 contas têm sede nos EUA e as outras 14 estão em 14 países diferentes).
- **Sujeira conhecida:** `GTXPro` no pipeline vs `GTX Pro` no catálogo, setor `technolgy`, país `Philipines`.
- **Sobre o dataset (revisão 23/10):** é público (Kaggle, CC0) e tem cara de dado gerado: o deal ganho mais longo e o perdido mais longo param exatamente nos mesmos 138 dias, e a taxa de ganho fica entre 61% e 65% em todo corte. Os cortes (57 e 138) são percentis deste arquivo, ficam em células editáveis, e num CRM real seriam recalculados todo mês.

## Passo a passo

### Etapa 1. Auditar e limpar os dados
- Corrigir os nomes que não batem (produto, setor, país) e registrar cada correção no process log.
- Juntar as quatro tabelas numa visão por oportunidade: deal, vendedor, manager, região, produto, preço de tabela, conta e dados da conta.
- Marcar o que falta em cada deal (conta, datas) como campo próprio. Dado ausente vira sinal, não linha descartada.
- Fixar a data de referência (31/12/2017) e calcular dias em aberto de cada deal em Engaging.

### Etapa 2. Construir o ICP a partir de quem compra melhor
Como toda conta já comprou, "bom cliente" é medido por cinco coisas, todas tiradas dos deals fechados:
- **Taxa de ganho** (ganhos sobre fechados)
- **Ticket** (valor fechado, e valor fechado contra o preço de tabela, pra ver desconto)
- **Recompra** (quantos deals ganhos e por quantos meses a conta continua comprando), nosso substituto de renovação
- **Expansão** (a conta subiu de série de produto, por exemplo de GTX Basic pra GTX Pro?)
- **Ciclo** (dias de engage até ganho)

Cortes pra testar: setor, porte por receita, porte por funcionários, idade da empresa, se é subsidiária, sede (EUA vs fora) e produto. Cada corte só entra no ICP se mostrar diferença real com amostra suficiente. O critério (por exemplo, quantos pontos de diferença na taxa de ganho e com quantos deals no mínimo) a gente define olhando os números, e fica registrado.

Saída: ICP em tiers (A, B, C) com o motivo de cada um em português claro.

### Etapa 3. Decidir se o ICP muda por região
Como região é o escritório do vendedor, a pergunta certa é: **cada time regional ganha melhor com tipos diferentes de conta?**
- Rodar a Etapa 2 dentro de cada região (Central, East, West).
- Se o ICP de uma região for diferente de verdade (mesmo critério da Etapa 2), trabalhamos região por região e cada vendedor vê o ICP da sua região.
- Se não for, fica um ICP só, e a gente diz isso no process log com os números. Também é resposta.

> **ICP aprovado pelo Rica (23/10)**
> **Um ICP só**, igual pras três regiões: nenhuma combinação setor x região ou receita x região fugiu do acaso. O ICP mede **valor da conta**, não chance de fechar: a taxa de ganho fica entre 61% e 65% em todo corte.
> - **ICP 1:** receita de 3 bilhões de dólares ou mais, ou setor software (receita observada por conta de 169 mil e 154 mil)
> - **ICP 2:** receita entre 1 e 3 bilhões (122 mil)
> - **ICP 3:** receita abaixo de 1 bilhão (84 mil a 100 mil)
>
> **Diferença real:** na taxa de ganho, pelo menos 2 erros-padrão; no valor, pelo menos 20% a mais de receita por conta, com 5 contas ou mais no segmento. Subsidiária, sede e ano de fundação não passaram. Números na aba ICP da planilha.

### Etapa 4. Medir o encaixe de cada deal aberto no ICP
- Cada deal aberto com conta recebe o tier do ICP (da sua região, se a Etapa 3 separar).
- Deal **sem conta** não recebe tier. Recebe a ação "identificar a conta" como primeiro passo. São 1.425 deals, então o tratamento deles é parte central da ferramenta, não nota de rodapé.

### Etapa 5. Aplicar o MEDDPICC

> **Decisão do Rica (23/10): MEDDPICC de lado**
> No começo eu queria usar o MEDDPICC, porque é a metodologia que ajuda a avaliar um deal parado no pipeline e entender se ele é real ou só torcida. Mas o CRM não tem dado pra isso: seis das oito letras estão vazias. Deixei o MEDDPICC de lado, e o que falta vira recomendação de campos pra RevOps.

Pra cada letra, o que o CRM tem hoje:

- **Metrics** (o ganho que o cliente espera): não tem. Aproximação: valor do deal e preço do produto.
- **Economic buyer** (quem assina o orçamento): não tem.
- **Decision criteria** (como vão escolher): não tem.
- **Decision process** (quem decide e em que ordem): não tem.
- **Paper process** (compras, jurídico, contrato): não tem.
- **Identify pain** (dor e caso de uso): parcial. O produto indica o caso de uso; a dor não está registrada.
- **Champion** (quem vende por nós lá dentro): não tem.
- **Competition** (contra quem estamos): não tem.

E as perguntas que eu sempre faço:
- **Dono do deal?** Tem: o vendedor, com manager e região.
- **Dono do orçamento?** Não tem.
- **Caso de uso claro?** Parcial: o produto.
- **Evento de urgência?** Não tem. Aproximação: o tempo do deal parado contra o ciclo normal de quem ganha (Etapa 6).
- **Capacidade financeira de comprar?** Tem: receita e funcionários da conta, comparados ao preço do produto. Só pra deals com conta.

> **O CRM não captura qualificação**
> Das oito letras do MEDDPICC, o dataset tem uma aproximação pra duas (Metrics e Identify pain) e nenhum dado das outras seis. Por isso o MEDDPICC fica de fora da prioridade. Vira recomendação pra RevOps: quais campos criar no CRM pra que, com o tempo, dê pra separar deal real de torcida.

> **Decisão do Rica (23/10): primeiro os deals com conta**
> Os 1.425 deals sem conta ficam estacionados. Primeiro a gente fecha os 664 deals abertos com conta: trabalha esses deals por vendedor, organiza por manager (se o time tem um padrão, o manager foca o trabalho dele nesse ponto) e finaliza prioridade e rótulos. Depois volta pros sem conta, com um proxy ou outro jeito de dividir entre os vendedores.

### Etapa 6. Medir o momento do deal
- **57 dias** é o ciclo normal de quem ganha (mediana de engage até o fechamento).
- **138 dias** é o deal ganho mais longo de toda a história. Nenhum deal fechou depois disso.
- Cada deal em Engaging cai numa faixa: **vivo** (até 138 dias, com **recente** até 57) ou **passou do ciclo** (mais de 138 dias: nenhum deal fechou depois disso, então o dono requalifica em 30 dias ou fecha como perdido).
- Dentro da janela, idade não é sinal de esfriamento (revisão 23/10): deal perdido morre cedo (mediana 14 dias). Deal aberto há mais de 30 dias ganha 68%, há mais de 90, 71%, contra 63% no geral. Todo deal vivo é pra trabalhar; o tempo desperdiçado está nos que passaram de 138.
- Prospecting não tem data, então o momento dele é "sem atividade registrada".

### Etapa 7. Montar a prioridade e a próxima ação
A prioridade junta três sinais: o deal está vivo (Etapa 6), o produto está na hora de ser recomprado naquela conta, e o valor da conta (ICP). A ordem travada está no fim deste SOP ("Ordem de prioridade travada"). Deal sem conta recebe a ação "identificar a conta" antes de entrar na lista.

> **Regra acordada com o Rica (23/10)**
> Topo da lista: produto **fora da janela estimada de recompra ou entrando nela em até 30 dias** naquela conta **e** com deal aberto pra esse mesmo produto. É motivo pra ligar e oportunidade no CRM ao mesmo tempo. Em 31/12/2017 são 280 pares conta e produto, com 518 dos 664 deals abertos que têm conta. Deal sem conta não entra aqui: primeiro identifica a conta (Etapa 4).

O texto do porquê é curto e no idioma do vendedor ("conta parecida com as que mais compram, GTX Pro fora da janela de recompra há 12 dias, deal aberto há 40 dias"). Sem data de último contato no CRM, a lista diz "aberto há X dias", nunca "parado"..

### Etapa 8. Validar antes de mostrar (na fase do app)
- Nenhum critério entra na prioridade sem provar nos 6.711 fechados que muda alguma coisa.
- Backtest: montar a lista do dia com os dados até uma data e testar se a ordem coloca os deals que foram ganhos acima dos que foram perdidos depois dela.
- Se um critério que a gente achava importante não provar nada, ele sai, e isso vai pro process log.

> **Backtest feito na planilha (aba Backtest, 23/10; refeito no mesmo dia com top N exato e acaso pareado)**
> Snapshot editável; em 30/09/2017: 1.401 deals em Engaging com conta abertos. Dos 169 passados de 138 dias, nenhum fechou depois (nem ganho nem perdido). Entre os vivos, estar na hora de recomprar não muda a taxa de ganho (60% nos passos 1 e 2). Top 18 por vendedor, exato (537 deals em toda ordem, empates desfeitos pela linha): ordem do SOP original (ICP depois valor) 235 ganhos e US$ 648 mil; valor depois ICP 239 e US$ 815 mil; só preço de tabela 221 e US$ 905 mil; mais novo primeiro 293 e US$ 688 mil; acaso pareado por vendedor (mesmo N de cada um, com a taxa e a receita média dele) 215 e US$ 650 mil; ordem em uso (urgência, valor, ICP, atropelados no fim) 270 e US$ 624 mil. Só deals em Engaging (Prospecting não tem data). Leitura exploratória, escrita na própria aba: um snapshot, dado gerado, cortes de 57 e 138 dias calculados no arquivo inteiro, nenhuma prova de causa. Como nada fecha depois de 138 dias neste arquivo, "mais novo primeiro" é favorecido aqui mais do que seria num CRM real. **Decidido (Rica, 23/10, 'go'):** valor depois ICP. Chave na aba Hoje, B13.

### Etapa 9. O app (próximo passo)
O SOP cria o padrão. O app mantém o padrão rodando todo dia, sozinho.
- **Visão do vendedor:** a lista do dia na ordem de prioridade, cada deal com o porquê e a próxima ação.
- **Visão do manager:** o time, as carteiras e as checagens em vermelho (time, motivo, faixa de 10%).
- **Atualização diária automática:** quando um produto entra na janela de recompra numa conta, o deal sobe na lista no dia seguinte; quando um deal passa de 138 dias, sai dos vivos.
- Filtros por vendedor, manager e região. Link no ar, sem instalar nada.

### Etapa 10. Registrar o processo em cada etapa
Cada etapa fecha com um commit e um trecho no process log (`process-log/00-narrativa.md` no repositório): o que pedi pra IA, onde ela errou, o que corrigi e o que eu trouxe que ela sozinha não traria.

> **Carteiras por vendedor (Rica, 23/10)**
> Cada conta tem um dono e cada vendedor vende o catálogo inteiro na sua carteira. A carteira de cada um tem o tamanho do que ele ganhou nos últimos 14 meses (sem GTK 500), então ninguém deve perder comissão: todo mundo fica entre -4% e +7% do que ganhou. Isso preserva o potencial histórico, não garante a comissão futura; o efeito real é checado no piloto, junto com a carga de trabalho (deals abertos e mix de produto por vendedor). Todo deal aberto com conta passa pro dono da conta agora, menos os 82 deals vivos, que o vendedor atual termina. Três especialistas em GTK 500 (Elease Gluck, Rosalina Dieter, Markita Hansen), com carteira própria de volume menor: quem negocia GTK 500 traz um deles, e o deal de GTK vai pro especialista, que pode agir em qualquer conta junto com o dono (Rica, 23/10: é o estado final, como está na planilha). O time do Dustin Brinkmann nunca vendeu GTXPro: primeiro descobrir se é acesso ao produto ou treinamento; se for treinamento, um trimestre vendendo junto com o time da Cara Losch. Piloto: time da Celia Rouche. Abas Books, Rep Books e GTK 500 KPIs na planilha.

> **Redistribuição dos deals abertos (Rica, 23/10)**
> Regra por idade, porque nenhum deal ganho na história levou mais de 138 dias.
> - **Deals vivos** (até 138 dias): 82 deals ficam com o vendedor atual até ganhar ou perder. Depois disso, ele não abre mais nada naquela conta se não for o dono.
> - **Todo o resto muda hoje pro dono da conta:** 394 deals passados do ciclo mais longo (o dono requalifica em 30 dias ou fecha como perdido) e 155 em Prospecting. 33 já estão com o dono.
> - **Deal sem conta:** quando a conta for identificada, vale a mesma regra de idade: os 209 vivos ficam com quem está neles até ganhar ou perder, os demais vão pro dono (Rica, 23/10, revisto no mesmo dia). Identificar a conta é tarefa de todo dia, depois dos deals vivos: fila própria, com prazo e escalada pro manager.
> - **Prospecting com conta:** o novo dono engaja no primeiro dia e registra a data; até lá, ordena pelo valor do produto.
> - **Daqui pra frente:** só entra deal no CRM com conta, e só na conta que o vendedor é dono. Conta nova (new logo) fica pra outra regra.
> Aba Open Deals na planilha, com quem trabalha cada deal agora e o dono da conta.

> **Ordem de prioridade travada (Rica, 23/10; revista no mesmo dia)**
> Só deals limpos entram nos passos 1 a 4. Deal limpo = aberto, com conta, e nenhum outro vendedor fechou o mesmo produto nessa conta depois de ele abrir.
> 1. Deal vivo (até 138 dias) em produto fora da janela estimada de recompra ou entrando nela em até 30 dias (17 em 31/12/2017).
> 2. Os outros deals vivos (3).
> 3. Deals mais antigos em produto entrando na janela de recompra ou pouco fora dela (até 30 dias); os muito fora da janela entram no fim como recuperação (137). Esse passo cobre a requalificação de 30 dias.
> 4. O resto, produto ainda dentro da janela (43).
> 5. **Confirmar** (464): outro vendedor fechou o mesmo produto na conta depois de o deal abrir. Pode ser o mesmo pedido, já atendido, ou demanda separada (outro departamento, outra quantidade, compra recorrente); os dados não dizem qual, e no backtest esses deals fecharam ganhos em 58% contra 62% dos limpos. Ação: confirmar com a conta. Mesmo pedido: juntar ao deal do colega ou fechar como perdido. Demanda separada: marcar no app e o deal volta pros passos 1 a 4. Nunca encerrar sem perguntar (Rica, 23/10, depois da terceira revisão; a regra anterior era "Encerrar" e foi revista).
> Dentro de cada passo: urgência da recompra (dias até a janela; no passo 3 os muito vencidos por último), depois valor do deal, depois tier de ICP (Rica, 23/10). 'ICP depois valor' era a regra original e fica como opção em Hoje!B13. Deal marcado feito hoje vai pro fim da lista do dia e volta amanhã. Primeira passada começa na segunda e todo deal dos passos 1 a 3 é tocado até sexta (cerca de 18 por vendedor). A lista é atualizada todo dia.
>
> **Recompra sem deal (Rica, 23/10):** pares conta e produto da carteira na hora de recomprar e sem nenhum deal aberto no CRM (103 de 383 em 31/12/2017) entram no Meu dia depois dos vivos, com a ação "abrir o deal e ligar" e um Feito. Onde o par já tem um deal a confirmar, a ação é confirmar esse deal, não abrir outro. Quando o atraso da recompra passa do dobro do ritmo, o card avisa que a conta pode ter parado de comprar e manda confirmar antes de contar com ela.

> **Managers reorganizam a carteira do time (Rica, 23/10)**
> A divisão de contas por vendedor é uma sugestão pra RevOps. A fatia de cada time fica fixa; dentro dela, o manager pode trocar o dono das contas, com quatro travas:
> - só entre vendedores do próprio time (mover conta pra outro time passa por RevOps);
> - a carteira de cada vendedor fica a no máximo 10% do que ele ganhou antes;
> - toda troca tem um motivo escrito;
> - uma semana pra entregar; depois a carteira congela no trimestre, com revisão a cada trimestre.
> Na planilha: dono sugerido, checagem de time e de motivo na aba Books; checagem dos 10% na aba Rep Books. Uma troca de dono já leva os deals abertos daquela conta junto (aba Open Deals).

## Regras em ordem de precedência (pra fase do app)

Salvo em 23/10 a pedido do Rica, pra usar na hora de construir o app. O código executa nesta ordem, e a primeira regra que bate decide:

1. **Deal sem conta** vai pra fila "identificar a conta" (aba própria, prazo, escalada pro manager). Fica com quem está nele. Quando a conta for identificada, volta pra esta lista e segue da regra 2.
2. **Deal de GTK 500** vai pra um dos três especialistas, que age em qualquer conta junto com o dono.
3. **Deal vivo** (até 138 dias desde o engajamento) fica com o vendedor atual até ganhar ou perder.
4. **Todo o resto** vai pro dono da conta (modo carteiras). No modo "como está hoje", fica com o vendedor atual. A ordem de prioridade é a mesma nos dois modos.
5. **Troca feita pelo manager** dentro do próprio time e da faixa de 10% substitui o dono sugerido, e leva os deals abertos da conta junto.
6. **Deal em que outro vendedor fechou o mesmo produto na conta depois de ele abrir** sai dos passos 1 a 4 e vai pro bloco Confirmar, com quem o trabalha hoje. Confirmada demanda separada, volta pros passos.

## Decisões em aberto
- Regra pra distribuir conta nova (proposta: por espaço na carteira e performance) e programa de ramp de 3 meses pros 5 vendedores sem nenhum deal (um em cada time, menos o do Dustin). Propostos, falta aprovar.
