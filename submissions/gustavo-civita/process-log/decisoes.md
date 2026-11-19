# Registro de decisões

Cada decisão da ferramenta, na ordem em que foi tomada. O resumo logo abaixo
está na minha voz. As decisões numeradas foram redigidas pelo Claude Code
durante a sessão, por isso falam de mim em terceira pessoa; as minhas falas
estão transcritas como escrevi, erros de digitação incluídos, e podem ser
conferidas na conversa exportada em `chat-exports/`.

Para quem tem pouco tempo: as decisões de **lógica** são 1 a 8, 10, 14, 16, 18,
20, 21, 24, 25, 31, 37, 39, 40, 41 e 42. As demais são de interface e de
entrega.

---

## Resumo: onde eu contrariei ou redirecionei a IA

Para quem tem cinco minutos. O detalhe de cada ponto está na decisão indicada.

1. **Parei a IA quando ela começou a decidir a lógica sozinha** ("isso não tira a
   minha parte lógica?"). Passamos a uma decisão de negócio por vez.
2. **Negociação parada não se descarta, se reativa** com condição especial, os
   mais caros primeiro e só as recentes, para não irritar o cliente (decisões 1,
   2, 3 e 5).
3. **Revi a minha própria intuição diante do dado:** eu ligaria para o cliente
   antigo de ticket maior; ao ver que só 9% dos deals de quatro meses fecham,
   mudei (decisão 4).
4. **Exigi registrar tudo que o vendedor faz** (decisão 6), o que virou o único
   jeito de medir "oportunidade esfriando".
5. **Rejeitei seis versões inteiras da tela, e pedi ajustes em mais três,** até chegar numa que o vendedor entende
   (decisões 9, 13, 15, 17, 19, 22, 23 e 28).
6. **Mandei auditar o que estava pronto** (decisão 14). A auditoria achou que a
   chance mostrada estava errada, e o cálculo foi refeito.
7. **Perguntei se a solução resolve ou só mascara** (decisão 24) e mandei
   subagentes independentes atacarem a tese. O resultado mudou o que a entrega
   promete.
8. **Aceitei um "não" da IA** quando propus usar um modelo de linguagem para
   enriquecer os leads: as empresas da base são fictícias (decisão 11).
9. **Três ligações sem resposta não encerram a negociação:** antes vem uma
   mensagem para confirmar o interesse (decisão 27).
10. **Reabri uma decisão minha.** Eu tinha mantido a fila do dia numa lista só
    (decisão 29); quando dois revisores mostraram que isso não priorizava para
    metade do time, pedi a recomendação da IA e separei a fila em meta do dia
    e "se sobrar tempo" (decisão 42).

---

## Decisão 1 — O que fazer com negociação parada há muito tempo

**Pergunta (Claude):** um vendedor tem um cliente que pediu proposta há 14 meses
e nunca mais respondeu. Continuar ligando, tirar da lista ou outra coisa?

**Proposta inicial da IA:** uma aba "Reativar ou encerrar", ordenada por valor,
deixando o vendedor e o manager decidirem caso a caso.

**Resposta do Gustavo:**

> "Se ele pediu uma proposta a 14 meses e nunca mais respondeu, eu mandaria uma
> mensagem com uma condicao especial para ele, ja que ele entrou em contato um
> tempo atras e ele pode ter esquecido"

**O que os dados mostram:** nenhum deal do histórico fechou depois de 138 dias
do início. Dos 1.589 deals em Engaging, 1.291 já passaram desse prazo (mediana
de 201 dias, o mais antigo com 423). São em média 48 por vendedor.

**Decisão:** esses deals saem da lista de foco do dia a dia (não vale gastar
ligação neles), mas não são descartados. Viram uma lista de **reativação**: uma
mensagem com condição especial, que custa pouco tempo do vendedor.

**O que mudou em relação à proposta da IA:** a IA tratava a lista como triagem
("reativar ou encerrar"). O Gustavo definiu uma ação concreta e barata para
todos: mensagem com condição especial.

---

## Decisão 2 — Quem recebe a mensagem de reativação

**Pergunta (Claude):** a condição especial vai para todos os 1.291 parados ou só
para parte deles? Qual o critério?

**Resposta do Gustavo:**

> "na real, depende... qual o umero de casos assim, pq se nao dps o vendedor
> perde MUITO tempo, para um produto barato. entao neste caso vamos ver o
> produto que tem a margem maior, pra que a gente consiga adiciobnar uma especie
> de condicao especial nela. e tambem eu verificaria qual o engahjamento que a
> empresa teve, se so foi uma pessoa que querioa uma proposta e pronto, talvez
> nao vale muito a pena. mas se foi alguem que o vendedor fez reuniao, conversou
> bastante ai sim pode valer"

**Critérios definidos pelo Gustavo:** (1) volume, para não tomar tempo demais do
vendedor; (2) margem do produto, para caber uma condição especial; (3) nível de
engajamento anterior com o cliente.

**O que os dados permitem (verificado pela IA a pedido):**

| Critério | Existe nos dados? | O que há no lugar |
|---|---|---|
| Volume | Sim | Parados por produto: GTK 500 = 14, GTX Plus Pro = 139, GTX Pro = 197, MG Advanced = 213, GTX Plus Basic = 203, GTX Basic = 279, MG Special = 246 |
| Margem | Não. Não há custo de produto | Só preço de tabela ($55 a $26.768). O histórico mostra quanto já se cedeu: metade dos ganhos fechou abaixo da tabela, 25% deles pelo menos 7% abaixo, e o maior desconto foi de 34% |
| Engajamento | Não. Não há registro de reuniões, ligações ou e-mails | Só dá para saber se o mesmo vendedor já vendeu para a mesma conta. E 68% dos parados não têm conta preenchida; dos 412 que têm, 137 são de um vendedor que já vendeu para aquela conta |

**Complemento do Gustavo (mensagem seguinte):**

> "e tambem acredito que podemos enviar essa condicao especial somente para os
> ultimos 5/6 meses"

**O que os dados mostram sobre esse corte:** dos 1.291 parados, 561 começaram há
até 180 dias (6 meses) e 139 há até 150 dias (5 meses). Os outros 730 são mais
antigos que 6 meses. Com o corte de 6 meses, sobram em média 21 por vendedor;
somando um piso de preço de $3.000, sobram 227 no total (8 por vendedor), que
concentram $1,09 milhão dos $1,25 milhão em preço de tabela desse grupo.

---

## Decisão 3 — Ordem e limite da reativação

**Contexto:** a IA informou que os dados não têm margem nem engajamento e
ofereceu substitutos (preço de tabela; histórico do vendedor com a conta).

**Resposta do Gustavo:**

> "Entao como nao existe dado de margem e engajamento. Vamos proprizar os
> produtos mais caros primeiro, com uma condicao especial algum bonus dentro.
> Por ela ja ter recebido a proposta. e depois que enviar mensagem para todos
> estes de produtos mais caros, comeca fazenejdo pelo restante, nos ultimos 5
> meses. Talvez enviar pra tanta gente depois dos 5 meses, eles nem respondam
> mais e ate podem ficar puto com a empresa enchendo o saco"

**Decisão:**

1. A lista de reativação é ordenada do produto mais caro para o mais barato.
2. A abordagem é uma condição especial com um bônus, já que o cliente recebeu
   proposta antes.
3. Só entram negociações iniciadas nos últimos 5 meses (150 dias). As mais
   antigas não recebem mensagem: a chance de resposta é baixa e insistir pode
   irritar o cliente.
4. O substituto de engajamento oferecido pela IA (histórico do vendedor com a
   conta) não foi adotado.

**Consequência nos dados:** um deal vira "parado" depois de 138 dias e o limite
de contato é 150 dias, então a lista de reativação tem 139 deals (cerca de 5 por
vendedor, $335 mil em preço de tabela). Os outros 1.152 parados ficam fora de
qualquer ação e são candidatos a serem encerrados no CRM.

---

## Decisão 4 — Quem o vendedor atende primeiro na lista principal (em aberto)

**Pergunta (Claude):** dois clientes ativos e tempo para ligar para um só.
Cliente A: produto de $5.000, negociando há 4 meses. Cliente B: produto de
$1.000, começou semana passada. Para qual ligar primeiro?

**Resposta do Gustavo:**

> "Cliente A, se ele esta negociando a 4 meses é porque ainda existe um
> interesse dentro dele, e tambem por conta do ticket. Se l gar agora e resolver
> isso, para de ficar arrastando o case do cliente pra frente e no final ele
> acaba enrolando e nao fechadno"

**O que os dados mostram (verificado pela IA):**

- Contra o primeiro argumento ("ainda existe interesse"): no histórico, de 1.480
  deals que continuavam abertos no dia 120, só 134 foram ganhos (9%). 45 foram
  perdidos e 1.301 nunca fecharam. No dia 7, a chance de ganho é 49%.
- Valor esperado quase empata: A = $5.000 x 9% = $453; B = $1.000 x 49% = $493.
  O rascunho da IA, que ordenava só por valor esperado, colocaria B na frente.
- A favor do segundo argumento ("resolver agora em vez de arrastar"): esperar
  uma semana custa $276 de valor esperado no cliente A (a chance cai de 9% para
  3,5%) e $16 no cliente B (de 49% para 48%). O cliente A está a 18 dias do
  prazo em que nenhum deal jamais fechou; o B pode esperar.
- 188 dos 298 deals vivos têm mais de 90 dias, ou seja, a maior parte da lista
  principal está perto de expirar.

**Resposta do Gustavo depois de ver os números:**

> "Faz essa -> Quem vale mais hoje vem primeiro (o meu rascunho). pq realmente,
> se 9% somente fecham, vale mais a pena ligar para o de 1K a uma semana"

**Decisão:** a lista principal é ordenada por valor esperado hoje (preço de
tabela x chance de ganhar dada a idade). O Gustavo reviu a própria intuição
inicial (ligar para o cliente antigo de ticket maior) ao ver que só 9% dos deals
com 4 meses são ganhos.

---

## Decisão 5 — Ampliar a reativação

**Contexto:** o Gustavo achou a lista de reativação fraca (139 deals, $335 mil)
e pediu uma recomendação. A IA propôs juntar os dois critérios dele (ticket e
não irritar o cliente): produtos a partir de $3.000 até 6 meses, os demais até
5 meses. Resultado: 304 deals, 11 por vendedor, $1,13 milhão em preço de tabela.

**Resposta do Gustavo:**

> "$1,13 milhão -> otimo, acho que vale sim"

**Decisão:** adotada a regra por preço (6 meses para caros, 5 para o resto).

**Pergunta do Gustavo sobre a evidência:**

> "Nenhuma negociação do histórico fechou depois de 138 dias. -> de quanto tempo
> é esse hisotiroc? talvez se for varios anos assim, talvez a gente tem que
> seguir nessa linha pra nao criar a roda do 0"

**O que a IA verificou:**

- O histórico não tem vários anos: são 14 meses de negociações iniciadas
  (20/10/2016 a 27/12/2017) e 10 meses de fechamentos (01/03/2017 a 31/12/2017),
  com 6.711 deals fechados.
- Dentro desse período o teto é consistente: o ciclo mais longo fica entre 132 e
  138 dias em 8 dos 11 meses de início que tiveram tempo de chegar lá.
- Achado novo: não existe nenhum fechamento antes de 01/03/2017. Os deals
  iniciados em 2016 só aparecem com ciclo de 63 dias ou mais, ou seja, os
  fechamentos rápidos de 2016 não estão na base. A curva de chance por idade
  passa a usar só deals iniciados a partir de 01/03/2017 para não herdar esse
  viés.

---

## Decisão 6 — Registrar o que o vendedor faz (métricas)

**Fala do Gustavo (não foi pergunta da IA, foi exigência dele):**

> "é importante metrificar tudo na ferramenta pra gente coletar o maximo de
> dados possiveis, pra saber insighjts, oq foi enviado, quando foi enviado, qual
> tipo de empresa da pessoa (nao sei se o cleinte sao empresas variaveis ou um
> mercado/nicho padrao)"

**O que a IA verificou sobre o tipo de empresa:** não é um nicho. São 85 contas
em 10 setores (varejo 17, tecnologia 12, saúde 12, marketing 8, finanças 8,
software 7, entretenimento 6, telecom 6, serviços 5, emprego 4), de 9 a 34 mil
funcionários, em 15 países. Porém 68% dos deals abertos não têm a conta
preenchida, então para a maioria a ferramenta não sabe o tipo de empresa.

**Decisão:** a ferramenta registra cada ação do vendedor em um deal (o que foi
feito, quando, resultado), junto com produto, idade e setor da conta quando
existir, e permite exportar esse registro. Isso responde à ressalva da IA de que
não há prova de que reativação funciona: a própria ferramenta passa a gerar
essa prova.

**O que a IA não tinha proposto:** o rascunho só ordenava e explicava deals. O
registro de ações e a medição de resultado vieram do Gustavo.

---

## Decisão 7 — As 500 negociações que ainda não começaram (Prospecting)

**Pergunta (Claude):** lista separada ou misturadas na lista principal?

**Resposta do Gustavo:**

> "colcoar tambem pra enviar mensagem ne, oq vc acha"

**Opinião da IA (pedida por ele):** sim, mas com mensagem diferente e sem
condição especial, porque esse cliente ainda não recebeu proposta e metade das
negociações iniciadas é ganha a preço normal; e em lista separada, para não
misturar a medição de primeiro contato com a de reativação.

**Confirmação do Gustavo:**

> "Mensagem diferente, sem condição especia -> exatamente, pq nao temos os dados.
> Lista separada tambem -> okk"

**Decisão:** aba própria "A abordar", ordenada pelo valor esperado, com ação de
primeiro contato a preço normal. Onde o cliente não está preenchido (67% dessas
500), o próximo passo mostrado é informar o cliente no CRM.

---

## Nota técnica — correção da curva depois da Decisão 5

A curva de chance por idade foi recalculada para lidar com o buraco de dados de
2016 (nenhum fechamento antes de 01/03/2017) e com deals ainda abertos. Os
números citados na Decisão 4 mudaram pouco: a chance no dia 120 foi de 9,1% para
9,4% e a do dia 7 de 49% para 53%. A conclusão não mudou.

---

## Decisão 8 — Sem login; cada vendedor abre direto na sua lista

**Pergunta do Gustavo:** "cada vendedor tem que ter o seu proprio login?"

**Resposta da IA:** no desafio não (exige servidor e aumenta o risco de não
rodar na máquina do avaliador); em produção sim, usando o login do CRM. Meio
termo: a ferramenta lembra quem é o vendedor e abre na lista dele.

**Encaminhamento:** adotado o meio-termo dentro do redesenho da Decisão 9. Login
real fica registrado nas limitações.

---

## Decisão 9 — Redesenho da experiência (rejeição da primeira tela)

**Contexto:** a IA entregou a primeira versão da tela: seis abas, quatro cartões
de resumo com valores da empresa inteira, e em cada negociação um círculo de
score, três linhas de explicação com a conta e três botões.

**Avaliação do Gustavo depois de usar:**

> "A platafoirma esta muito estrnaha, vamos priorizar que ela seja intuitiva e
> objetva para o vendedor utilziar. como ele vai abrir todo dia a plataforma, a
> experiencia dele UX tem que estar impecavel, do jeito que esta agora esta
> muito estranho. existe muita margem para melhorar este sisteminha"

**Diagnóstico da IA sobre o que estava errado:**

- Abria na empresa inteira, e não no dia de um vendedor.
- Misturava o que é do vendedor (o que fazer) com o que é do manager (resumos,
  resultados, metodologia) na mesma barra de abas.
- Cada cartão tinha texto demais para quem só precisa saber para quem ligar.
- Marcar uma ação não mudava nada de forma visível.

**Decisão:** refazer a tela em torno do dia do vendedor: ele escolhe quem é uma
vez, e a primeira tela vira uma lista curta de tarefas (ligar, primeiro contato,
reativar), com uma linha de motivo por item, um botão principal, e o detalhe da
conta escondido atrás de "Por quê?". Resumos do time, resultados e metodologia
saem do caminho do vendedor e vão para telas próprias.

---

## Nota técnica — erros da IA encontrados no teste da segunda tela

- A taxa de resposta em Gestão mostrou 200%: cada clique em um resultado era
  contado como uma resposta nova. Corrigido para contar um contato por
  negociação, com o último resultado marcado.
- A barra de navegação mostrava uma barra de rolagem em telas estreitas e os
  setores apareciam em inglês, como vêm do CRM. Ambos corrigidos.
- O teste da tela revelou um padrão que a análise inicial não tinha mostrado:
  vários vendedores (o escritório Central quase inteiro) não têm nenhuma
  negociação viva. A tela de Gestão passou a destacar essas linhas.

---

## Decisão 10 — O fluxo de cada negociação depois do clique

**Crítica do Gustavo à segunda tela:**

> "ainda esta pouco claro oque tem que ser feito e as possibilidades, como por
> exemplo: clicamos aqui em 'liguei' depois ele vai pra onde? outro ponto: esta
> muito estranho a questao de selecionar o 'avancou' 'sem resposta' e etc.
> Porque as vezes a pessoa no responde agora, e nao tem como selecionar sem
> reposta. Temos que pensar em um fluxo melhor para cada negociacao, pensando
> novamente que o vendedor vai abrir o sistema todo dia"

**O que estava errado na versão da IA:** depois do clique a negociação ficava
marcada como feita e nada mais acontecia. A pergunta "como foi?" aparecia na
hora, quando o vendedor ainda não sabia a resposta.

**Proposta da IA:** perguntar só o que o vendedor já sabe no momento e trazer a
negociação de volta sozinha no dia certo. Ligação: "atendeu?" e, se sim, "o que
ficou combinado?" (retornar em tal dia, fechou, sem interesse). Mensagem: vai
para "Aguardando" e volta se não houver resposta.

**Resposta do Gustavo sobre a parte do "atendeu":** "acho isso interessante"

**Decisão:** fluxo adotado. Toda ação mostra um aviso dizendo para onde a
negociação foi e quando volta.

**Pendente de confirmação dele:** as três regras de prazo (religar em 2 dias,
segunda mensagem em 3 dias, desistir após 3 tentativas) são palpites da IA. O
Gustavo não confirmou os números; a base não tem dado para calibrá-los.

---

## Decisão 11 — LLM local e enriquecimento de lead

**Ideia do Gustavo:**

> "voce acredita que seria viave, por ex adicionar um LLM local para ajudar
> neste sistema? como por exm LLama. E dai podemos sugerir tambem mensagens,
> oque falar, gerar um resumo, fazer um enriquecimento do lead. preparar
> basicmente o vendedor para fazer aquela ligacao, ele pode abrir um modal
> daquele lead, ver todas as infos, site, oq a empresa faz [...] oque voce
> acha? entra na proposta do desafio ou acredita que tangencia muito"

**Avaliação da IA:** preparar o vendedor cabe no desafio; o LLM e o
enriquecimento externo não cabem nesta entrega, porque (1) as empresas da base
são fictícias, então um LLM inventaria o que elas fazem; (2) 68% das negociações
abertas não têm cliente; (3) um modelo local exige instalação pesada e põe em
risco o critério "roda seguindo as instruções".

**Decisão do Gustavo:** "Crie este modal entao."

**O que foi feito:** ficha de cada negociação com dados reais cruzados das
quatro tabelas (cadastro da empresa, histórico de compras, histórico com o
próprio vendedor, outras negociações abertas), roteiro de ligação e mensagem
sugerida por modelo fixo. O LLM fica documentado como próximo passo para uma
empresa com clientes reais e anotações no CRM.

**Pergunta dele que gerou um dado para a documentação:** "oq elas tem de fato
rpeenciddo?" As 1.425 negociações abertas sem cliente têm só código, vendedor,
produto, etapa e, nas 1.088 já iniciadas, a data de início.

---

## Decisão 12 — Governança e organização do vendedor

**Fala do Gustavo:**

> "este sistema quem utiliza? porque nao podemos deixar que um vendedor consiga
> entrar e saber os deals de outro vendedor (governanca)"

> "esta confuso ainda as abas, confuso os modais, e outra, temos que pensar em
> organizacao do vendedor tamnbem"

**O que mudou na terceira tela:** a navegação do vendedor virou Hoje (o que
fazer), Aguardando (o que depende do cliente ou de uma data) e Carteira (tudo,
com busca e situação). Time e Como funciona ficaram separados. O detalhe de uma
negociação passou a existir em um lugar só, a ficha.

**Governança, em aberto:** a IA explicou que nesta arquitetura (arquivo aberto
no navegador) todos os dados estão no arquivo, e que uma tela de senha por cima
não protegeria nada. Controle de acesso real (vendedor vê o seu, manager vê o
time) exige um servidor. A ficha já não mostra detalhes de negociações de outros
vendedores, só a contagem. O Gustavo ainda não decidiu entre construir o
servidor ou documentar como limitação.

---

## Decisão 13 — Quarta tela: fila compacta, painel de ação, entrada por perfil

**Pedidos do Gustavo depois de usar a terceira tela:**

> "A parte de oq ficou combinado, tem que ter opcao de adicionar um campo para o
> proprio vendedor poder digitar. e outra coisa, ainda esta bem confuso para o
> vendedor oq ele tem que fazer, clicar e etc. e pense que vao ter varias
> negociações no sistema/pipeline, se tiver desta forma, vai ficar inviavel
> arrastar sempre pra baixo a pagina, pesne disso. E tambem crie uma especie de
> 'login' onde selciona se voce é o gerente ou vendedor e entra no cadstro
> especifoco. obviamente por ser um MVP sem banco/senhas/usuarios, esta liberado"

> "tambem crie botoes de confirmação 'voce deseja confirmar esta acao x' para
> evitar que o vendedor de misclick"

**O que estava errado na versão da IA:** cada negociação era um cartão alto, com
botão dentro, então uma carteira grande virava uma página enorme; e havia dois
lugares para agir (o cartão e a ficha), o que confundia.

**O que foi feito:**

- **Lista compacta + painel fixo.** À esquerda, uma linha por negociação, com
  rolagem só dentro da lista. À direita, a ficha da negociação selecionada. A
  página em si não rola. Em tela estreita, mostra a lista ou a ficha.
- **Um lugar só para agir.** A ficha abre com a caixa "Agora", que diz em
  passos o que fazer e traz os botões do que pode ter acontecido.
- **Próxima automática.** Depois de registrar, a ferramenta abre a próxima
  negociação da fila.
- **Anotação.** Campo de texto livre em toda ação; aparece no histórico da
  negociação, é lembrada no retorno e sai na exportação.
- **Confirmação.** Nenhuma ação é salva no primeiro clique: a caixa mostra o que
  vai acontecer com a negociação e pede "Confirmar" ou "Cancelar".
- **Entrada por perfil.** Vendedor escolhe o nome e vê só as próprias
  negociações (Hoje, Aguardando, Carteira). Gerente escolhe o time e vê Time e
  Carteira do time. Há também "Toda a empresa" para RevOps.

**Governança, decidida pelo Gustavo:** separar o que cada perfil vê, sem senha
nem banco, por ser um MVP. Fica registrado nas limitações que isso organiza o
acesso mas não o protege, e que em produção o acesso viria do login do CRM.

---

## Decisão 14 — Auditoria contra a task e correção do cálculo

**Pedido do Gustavo, no meio do trabalho de layout:**

> "como estamos modificando a questao de visual, experiencia do vendedor e etc.
> nao podemos deixar de lado o objetivo principal. vamos repassar oque a task
> exigia e se o nosso sistema de fato resolve o problema de forma comprovada e
> testada"

**O que a auditoria encontrou (erro da IA):** o teste que existia media só a
receita capturada. Ao testar também se a "chance de ganhar" mostrada na tela
batia com a realidade, ela errava muito. Voltando a 30/06/2017, a ferramenta
dava 33% de chance para negociações de 90 a 138 dias; nenhuma das 201 foi ganha.
Para as de 60 a 90 dias dava 60%; foram ganhas 22%.

**A causa:** a IA tinha assumido que a chance dependia só da idade. Cruzando mês
de início com mês de fechamento, apareceu um padrão que a idade esconde: nesta
base uma negociação fecha no trimestre em que começou ou no seguinte, nunca
depois. A regra "nada fecha depois de 138 dias" era verdadeira, mas frouxa.

**A correção:** a chance passou a ser estimada olhando o mesmo ponto dos
trimestres anteriores (negociações abertas com a mesma idade há 3, 6 e 9 meses,
e quantas foram ganhas depois).

**O que o teste mostra agora, em cinco datas (em vez de três):**

| Data | Esta ferramenta | Só pelo preço | Ao acaso | Parados que fecharam |
|---|---|---|---|---|
| 30/06/2017 | $763.973 | $664.397 | $280.122 | 0 de 252 |
| 31/07/2017 | $793.675 | $691.776 | $249.852 | 0 de 334 |
| 15/08/2017 | $745.513 | $602.035 | $225.063 | 0 de 379 |
| 15/09/2017 | $601.615 | $447.494 | $192.713 | 0 de 459 |
| 30/09/2017 | $641.049 | $447.959 | $174.287 | 0 de 543 |

Receita = o que geraram depois as 10 primeiras negociações de cada vendedor.

**O que ainda não é perfeito, e fica declarado na ferramenta:** a chance
continua otimista. Onde a ferramenta previu em média 48%, foram ganhas 42%; onde
previu 34%, foram 21%. A ordem está certa, o número não é promessa.

**Consequência para as listas:** as negociações com chance real caíram de 298
para 128, todas dos escritórios East e West. A reativação subiu de 304 para 474,
pela mesma regra de prazo que o Gustavo definiu nas decisões 3 e 5.

**Testes automatizados criados:** 10 testes em `solution/tests/`, incluindo um
que garante que o cálculo de uma data não usa nada que aconteceu depois dela.

**O que continua faltando da task:** o README (como rodar, lógica, limitações) e
o export desta conversa.

---

## Decisão 15 — Quinto layout

**Avaliação do Gustavo sobre o quarto layout:**

> "Não gostei deste novo layout, as fontes nao estao legais (utilzie a inter),
> nao gostei do 'Boa Noite...', isso significa AI slop. e vamos remodelar todo o
> layout. tambem a 'pagina' de uma negocialção em especifico, nao precisa ser
> assim uma separada, porque são muitos deals, acredito que um pop-up bonito ja
> vale a pena"

**O que mudou:** fonte Inter; saudação removida (a página se chama "Hoje" e
mostra quatro números); barra lateral fixa com as páginas e as contagens;
negociações em tabela compacta com idade, chance, valor e score em colunas;
detalhe e ações em um pop-up; Carteira paginada de 20 em 20.

---

## Decisão 16 — Deixar explícito onde gastar tempo e o que está sem atenção

**Contexto:** a IA fez um raio-x da solução contra a task e disse que a dor "boas
oportunidades esfriando" estava resolvida só em parte.

**Exigência do Gustavo:**

> "tem que ficar extremamente claro no sistema qual oportundiade boa esta sem
> atencao e onde ele tem que fgastar tempo, tem que ser feito isso"

**O que a IA mediu antes de desenhar:**

- Testou a ideia de "esfriar" como queda de chance em duas semanas. Hoje
  (31/12/2017, fim de trimestre) a queda é praticamente zero, porque no primeiro
  mês de um trimestre as negociações antigas não fecham. A ideia foi descartada.
- O que os dados mostram no lugar: só 2 das 128 negociações vivas podem fechar
  nos próximos 30 dias; as outras fecham mais adiante ou não fecham.
- 89% do valor esperado da empresa ($529 mil de $593 mil) está nas 500
  negociações que ainda não foram iniciadas, todas no escritório Central. Uma
  negociação iniciada agora tem 24% de chance de fechar em 30 dias.
- Validação em cinco datas: negociações marcadas como "pode fechar este mês"
  foram ganhas em 30 dias entre 18% e 20% das vezes; as não marcadas, entre 0% e
  2,4%.

**O que entrou na ferramenta:**

- **Mapa no topo de Hoje**, com três blocos: "Gaste seu tempo aqui" (quantas e
  quanto valem), "Boas e sem atenção" (score 70 ou mais sem nenhum contato
  registrado) e "Não gaste ligação aqui" (sem chance pelo histórico, com o
  resultado do teste).
- **Coluna "Último contato"** em toda tabela: "Nunca", "Hoje", "Há N dias".
- **Seção "Ligar primeiro: podem fechar este mês"** acima das demais ligações.
- **No pop-up**, a frase dizendo se a negociação pode fechar este mês ou não.
- **Para o gerente**: o mesmo mapa por time, colunas "Valor esperado" e "Boas
  sem contato" por vendedor, e filtro por região.
- **Score por lista**: antes a melhor negociação de um vendedor podia aparecer
  com 63, porque disputava com as 500 não iniciadas. Agora o score compara
  negociações da mesma lista.

**Limite declarado:** o CRM não registra contatos, então "sem atenção" é medido
pelos registros da própria ferramenta. No primeiro dia, toda boa oportunidade
aparece como "Nunca" contatada. O valor esperado das não iniciadas supõe que
elas sejam de fato iniciadas.

---

## Decisão 17 — Sexto layout: o mais fácil possível para o vendedor

**Avaliação do Gustavo sobre o quinto layout:**

> "Ainda sobre a parte de estilo do sistema nao ficou agradavel, o objetivo não é
> dificultar mas sim deixar o mais facil possivel para o vendedor. a parte do
> conteudo nao esta centralizado na pagina, ele esta tangenciando para a
> esquerda e tambem os KPIS estao feios nao estao claros, e tambem eu entrando
> aqui como vendedor nao sei oque eu tenho que fazer, nao sei oque clicar. sem
> contar quando eu abro o modal de uma negocialecao, tem um monte de informacoes
> despejadas que o vendedor nao vai ler"

**Diagnóstico da IA:** a tela estava feita para quem analisa dados (tabela de
sete colunas, três blocos com parágrafos, pop-up com tudo aberto), não para quem
só precisa saber o próximo passo.

**O que mudou:**

- Conteúdo centralizado, com barra de navegação no topo em vez de lateral.
- Uma frase de instrução no alto: "Comece pelo número 1. Clique no botão, faça o
  contato e marque o que aconteceu."
- Fila numerada. Cada linha tem o nome, uma frase simples com o motivo, o score
  e um botão com o verbo do que fazer ("Ligar", "Enviar mensagem"). A primeira
  linha vem destacada.
- Três números grandes com legenda curta: para fazer hoje, boas oportunidades
  sem contato, não valem ligação.
- Pop-up com uma frase de motivo e só a ação. A anotação aparece na
  confirmação. Roteiro, explicação completa, empresa e histórico ficam atrás de
  "Ver detalhes da negociação".

---

## Decisão 18 — Verificação por três frentes independentes

**Instrução do Gustavo:**

> "avalie se a nossa solucao é de fato eficiente, verifque se nao existem outras
> coisas que podemos fazer, pesqusie tambem se existia outras empresas com o
> mesmo problema e como foi resolvido, se teve resultado mensuravel e etc. O
> objetivo aqui é resolver o problema da melhor forma possivel, as decisoes
> cruciais e estrategicas voce tem que me consultar antes. lance subagentes para
> fazer estas subtasks"

**Como foi feito:** três subagentes em paralelo, cada um sem acesso às conclusões
dos outros: (1) pesquisa de como empresas reais resolveram o mesmo problema e
com que resultado medido; (2) auditoria da solução contra o enunciado, com
instrução de conferir os números no código e nos dados em vez de confiar no que
este registro afirma; (3) busca de sinais ainda não usados nos dados, com
validação fora da amostra obrigatória.

**Regra a partir daqui:** decisões estratégicas são levadas ao Gustavo antes de
qualquer implementação.

---

## Decisão 19 — Formato da tela: tabela tipo CRM

**Avaliação do Gustavo sobre o sexto layout (fila com um botão por linha):**

> "nao esta agradavel, ele esta constuirdo de uma forma que nao se sustenta com
> VARIAS negociações, tem que ser um formato que sustente, e tambem nao esta com
> os dados prioncipais para o vendedor ber e entender, saber o ome da empresa,
> oq ela faz, o valor do deal, informacoes e etc. sempre se baseando no problema
> que estamos resolvendo"

**Como foi decidido:** em vez de construir uma sétima tentativa às cegas, a IA
apresentou três formatos com esboço (tabela tipo CRM, quadro kanban por etapa,
uma negociação por vez). **O Gustavo escolheu a tabela tipo CRM.**

**O que foi construído:** colunas fixas (posição, empresa com setor e número de
funcionários, produto com a situação, valor, chance, score, botão de ação),
busca, filtros por ação e produto, ordenação por coluna e paginação. No pop-up,
o nome da empresa, o que ela faz, o tamanho, o país e quantas vezes já comprou
vêm no topo.

**Ajustes pedidos por ele depois de usar:**

> "preciasmos melhorar quando a gente clica no enviar mensagem, parece que ali
> ja vai ser enviado uma mensagem ao lead, e temos que melhroar o pop-up que
> aparece, e tambem aumentar o tamanho horizontal dele. oyutra coisa, quando foi
> a proxima vez do lead X, deixar ele maior em tamanho vertical na tabela, pra
> ter um nimo de destque. e faca que a rolagem seja na tabela e nao na pagina em
> si, assim a gente ja se prepara para uma longa tabela de leads"

- O botão "Enviar mensagem" virou "Ver mensagem", e o pop-up diz que a
  ferramenta não envia nada: o vendedor copia, ajusta e envia pelo próprio canal.
- Pop-up mais largo (de 600 para 820 px).
- A próxima negociação da fila aparece mais alta e com o selo "Próxima".
- A página fica parada e quem rola é a tabela, com o cabeçalho fixo.

---

## Decisão 20 — Resultado das três frentes de verificação (aguardando o Gustavo)

**Pesquisa de mercado.** Um único caso com medição controlada publicada
(LinkedIn Account Prioritizer, +8,08% em renovações, teste A/B, KDD 2023). Os
demais casos com nome de empresa são material de fornecedor, sem grupo de
controle. O que se aplica aqui: explicar cada score em uma frase, lista diária
curta, regras auditáveis, validar antes de prometer.

**Auditoria independente.** Dor 1 resolvida e bem comprovada. Dor 2 e "saber
onde focar" fracas. Apontou que a validação provava menos do que a IA afirmava.

**Busca de sinais.** Cerca de 160 hipóteses testadas com validação no tempo;
nenhuma melhora a ordenação. "Cliente preenchido" parecia um sinal forte, mas é
artefato: nas negociações abertas, o cliente foi preenchido ao acaso.

**O que a IA conferiu por conta própria (e onde discordou da auditoria):**

| Ponto da auditoria | Conferência da IA |
|---|---|
| A comparação com "só preço" era fácil demais | Confirmado. Contra "preço entre negociações de até 90 dias", a vantagem cai de 15-43% para cerca de 10% |
| A ferramenta perde em 8 de 10 semanas do 4º trimestre | **Não confirmado.** Refeita a conta: ganha em 7 de 10 no 4º trimestre e em 25 de 28 no total |
| A chance erra muito em negociações de 45 a 75 dias | Confirmado. Em 30/09, previa 37% para 60-75 dias; foram ganhas 7% |
| As negociações vivas de hoje não têm como ser validadas | Confirmado. No fim dos trimestres anteriores, 56-61% dos deals do trimestre seguiam abertos; em 31/12 são 10% |
| As não iniciadas recebem 49% sem base | Confirmado. A conversão de prospecção em negociação não existe nos dados |

**Erro da IA registrado:** as cinco datas do primeiro teste eram todas do período
mais favorável, e a comparação escolhida favorecia a ferramenta.

**Correções propostas, ainda sem resposta do Gustavo:** (1) trocar o percentual
de chance por faixas; (2) tirar chance e score das não iniciadas; (3) refazer o
teste com a comparação justa e publicar a vantagem real.

---

## Decisão 21 — Correções de honestidade aprovadas e aplicadas

**Resposta do Gustavo às três correções propostas na Decisão 20:**

> "concordo, vamos efetuar estas modificacoes e depois testar tudo novamente."

**O que foi feito:**

1. **Chance em faixas.** A tela mostra Alta, Média ou Baixa em vez de
   percentual. No teste, as faixas ordenam bem: alta 42,5% de ganho, média
   21,4%, baixa 2,4%.
2. **Não iniciadas sem chance e sem score.** As 500 negociações em prospecção
   ficam na ferramenta, ordenadas pelo valor, com "chance desconhecida". A frase
   dos 89% do valor esperado foi removida.
3. **Teste refeito com a comparação justa.** 24 semanas seguidas (01/07 a
   09/12/2017), contra a regra "produto mais caro primeiro, ignorando
   negociações com mais de 90 dias":

| Período | Esta ferramenta | Regra simples | Diferença | Semanas em que ganhou |
|---|---|---|---|---|
| 3º trimestre | $9.965.786 | $8.814.823 | +13% | 14 de 14 |
| 4º trimestre | $6.406.468 | $5.850.012 | +10% | 7 de 10 |

   A ferramenta perdeu da regra simples em 04/11, 18/11 e 25/11. Das 12.886
   negociações tiradas da lista de ligação ao longo das semanas, nenhuma foi
   ganha depois e 2 foram encerradas como perdidas.

**Testes automatizados:** 16, todos passando.

**Pedido adicional do Gustavo, que muda o enquadramento do trabalho:**

> "nao quero focar na tarefa como exclusivamente um case da G4, e sim como se
> fosse um cliente que estamos resolvendo um problema"

---

## Decisão 22 — Oitavo layout

**Avaliação do Gustavo:**

> "ainda ficou confuso os kips e etc, vamos remodar a parte do pront, para que
> nao pareca que estamos despejando varias textos e informacoes para o vendedor,
> tambem nao acredito que o KPI Chance la na tabela seja tao interessante a
> nivel de estar fixo na tabela. [...] é interessante termos uam sidebar com as
> paginas"

**O que mudou:** barra lateral com as páginas; os três blocos de números da tela
"Hoje" saíram e deram lugar a abas com contagem (Tudo, Retornos, Ligar,
Mensagem), que também filtram a tabela; a coluna Chance saiu da tabela e ficou
só no pop-up; a instrução do topo virou uma frase curta; a informação sobre
negociações sem chance virou uma linha no rodapé.

---

## Decisão 23 — Página inicial do vendedor e dado de contato

**Perguntas e pedidos do Gustavo:**

> "E telefone/email dados de conteto ndo cliente nao existem? e ttambem quando eu
> comentei para a gente nao deixar o SCORE ali na tabela, talvez seja
> interessante adicionar outro dado que seja importante para o vendedor. e
> tambem melhorar essa pagina inicial do vendedor, ele saber oq esta acontecendo
> e etc. pq hoje em dia ele abre e só tem uma tabela la"

**Resposta sobre contato:** a base não tem telefone, e-mail nem nome de contato
em nenhuma das quatro planilhas. A ficha da negociação passou a dizer isso.

**O que entrou:**

- Coluna "Último contato" na tabela (Nunca, Hoje, Há N dias), no lugar que a
  coluna Chance ocupava. É o dado que mostra o que está sem atenção.
- Resumo do dia acima da tabela, em quatro quadros: quantos contatos já foram
  feitos, retornos para hoje, o que está aguardando o cliente, e a composição da
  carteira em uma barra (com chance, não iniciadas, para reativar, sem chance).

**Em aberto:** o Gustavo citou tirar o score da tabela. A IA manteve a coluna e
recomenda mantê-la, porque o score é o centro do que foi pedido ("lead scorer")
e é o que explica a ordem da lista. Aguardando a decisão dele.

**Erros da IA apontados por uma verificação independente e corrigidos:**

- O contador "Hoje" do menu mostrava 10 enquanto a fila tinha 30.
- O número "sem chance de fechar" do gerente aumentava quando alguém fechava
  uma negociação.
- Fechar ou perder na primeira ligação não contava como contato.
- O filtro de região escolhido em "Time" continuava valendo na "Carteira" sem
  aparecer na tela.
- A página "Como funciona" falava em 12.886 negociações tiradas da lista; são
  801 negociações diferentes, contadas uma vez por semana de teste.

**Novo pedido registrado para depois:** plano de adoção pelos vendedores e forma
de medir o resultado da ferramenta.

---

## Decisão 24 — A tese posta à prova: resolve ou mascara?

**Pergunta do Gustavo:**

> "os problemas apresentados foram: A e B. Estamos resolvendo eles de qual
> maneira? é metrificavel? existe outra forma melhor que nao estou vendo pra
> resolver estes 2 problemas? é possivel gerar resultado esta solucao ou só
> estamos mascarando o problema? Verifique isso com subagentes para validarem a
> tese e nos dar um veredito sobre tudo isso"

**Como foi feito:** quatro subagentes independentes, sem acesso às conclusões uns
dos outros: (1) verificação com olhar de cliente; (2) advogado do diabo, com a
missão de montar o caso mais forte de que a ferramenta só mascara; (3)
alternativas melhores, conferidas nos dados; (4) plano de medição e piloto.
Depois a IA refez por conta própria as contas centrais.

**Números conferidos pela IA (script `verifica_veredito.py`):**

| Afirmação dos subagentes | Conferência |
|---|---|
| A chance não separa ganho de perda (AUC 0,524); separa "fecha" de "fica aberta" (0,844) | Confirmado |
| Das 801 negociações tiradas da lista no teste, 799 nunca foram fechadas por ninguém | Confirmado (0 ganhas, 2 perdidas) |
| Uma regra simples, "mais de 138 dias", já cobre a maior parte da triagem | Confirmado: 1.291 das 1.461 que a ferramenta tira |
| 37% da receita ganha fechou em até 14 dias do início | Confirmado (37,4%) |
| "Boa oportunidade" na prática quer dizer produto caro | Confirmado: score x preço 0,81; score x chance 0,40 |
| A entrada de negociações cai de ~780 por mês para 283 e 121 | Confirmado |

**Veredito consolidado:**

- **Não mascara**, porque declara os limites, mas hoje prova priorização e não
  resultado. O teste mostra que a ferramenta prevê onde a receita vai cair, não
  que usá-la faz cair mais.
- **Problema A:** a triagem não errou no histórico, mas não há evidência de que
  os vendedores gastavam tempo nas negociações mortas (elas estavam abandonadas),
  e uma regra de CRM de uma linha resolve 88% do mesmo.
- **Problema B:** não é mensurável com os dados do CRM. A ferramenta tem o
  mecanismo (registro de contato, retornos), que só gera evidência com uso.
- **Medição:** comportamento e qualidade do pipeline são mensuráveis. Receita
  não: com 35 vendedores, um piloto só detecta efeitos de 30% para cima.
- **Alternativa de maior impacto que a ferramenta:** limpeza única por regra,
  antes de qualquer coisa.

**Decisões levadas ao Gustavo:** como posicionar a entrega diante disso; tratar
a reativação como experimento com grupo de controle; o plano de adoção e de
medição que ele pediu.

---

## Decisão 25 — Reposicionamento da entrega e avaliação final

**Sobre o reposicionamento proposto na Decisão 24, o Gustavo perguntou:**

> "mas ai nao sairia do escopo do desafio?"

**Resposta da IA:** não, desde que fique no texto. A ferramenta não muda; o
diagnóstico entra em "Resultados", a regra de limpeza em "Lógica", o que não foi
provado em "Limitações" e o piloto em "O que precisaria para escalar". O que
sairia do escopo seria construir mais coisa ou escrever um relatório longo.

> "ok entao, pra isso precisamos adicionar novas pagians aqui no sistema e etc?"

**Decisão:** nenhuma página nova. Foram escritos o README da solução, o README
da submissão e uma página de plano de piloto e adoção.

**Pedido seguinte do Gustavo:**

> "lance subagentes como adv do diabo e como validadores do proprio G4, e
> analise com olhar critico toda a solucao, e de notas, se passou, se nao
> passou. oque falta pra solucao ficar melhor, oque foi demais e etc"

**Notas recebidas:**

| Avaliador | Nota como está | Nota com ajustes | Veredito |
|---|---|---|---|
| Avaliador do G4 | cerca de 6,5 | 7,5 | Aprovado com ajustes |
| Advogado do diabo | 6,5 | 8,5 | Risco de desclassificação sem o export |

**Erros da IA apontados e conferidos (script `verifica_final.py`), já corrigidos:**

- A fila da tela punha "pode fechar este mês" no topo, uma ordem diferente da
  que o teste validou. Medida, essa ordem perdia da regra simples (-1,6% e
  -1,7%). A fila voltou à ordem testada; o aviso ficou como rótulo.
- O roteiro e a mensagem sugeriam desconto com base na variação do valor
  fechado. Ela é simétrica (25% fecharam 7% ou mais abaixo da tabela, 23% 7% ou
  mais acima): é ruído, não política de desconto. Referência removida.
- O plano dizia que a taxa de ganho cairia para 55%; com as 1.291 negociações
  que ele manda encerrar, cai para 53%.
- O rótulo do score dizia "das negociações em andamento"; ele compara só as 128
  com chance.
- O README passou a dizer que o score tem correlação de 0,81 com o preço e que
  a vantagem cai para +4% e +5% com as 20 primeiras em vez das 10.

**Pendências que dependem do Gustavo:** export da conversa, LinkedIn, prazos de
retorno, coluna Score e o que cortar por excesso.

---

## Decisão 26 — Evidências, tecnologia, entrada, modo escuro e QA

**Pedidos do Gustavo:**

> "a submissao tem que ter evidencias visuais do processo com IA - screenshots
> das iteracoes, basicamente ter prints da interface rodando. Exemplos de output
> da nossa solucao, pra quem for avalisar conseguir verificar se o modelo se
> comporta como necessario"

> "verifique se estamos utilizando FasAAPI e Nextjs"

> "Vamos pesnar em um sistema que nao tenha dependencia do backend, que seja um
> frontend-only que consiga ser auditavel, leve"

> "em breve vamos publicar uma demo no Vercel. ja vamos preparar o sistema para
> ser responsivo com as telas mais variadas e tambem adicionar um sistema de
> DARK-MODE. melhroar a questao do login de gerente/vendedor. E em seguida
> tambem lembre-se que temos que efetuar rodadas de QA"

**Sobre a tecnologia:** a ferramenta não usa FastAPI nem Next.js. É HTML, CSS e
JavaScript sem nenhuma dependência instalada. A IA confirmou abrindo o
`index.html` direto do disco, sem servidor, e a tela carregou inteira. O Gustavo
decidiu manter assim: sem backend, leve e auditável.

**O que foi feito:**

- Prints das oito versões da tela e da versão final em `screenshots/`, e
  exemplos de saída em `docs/exemplos/`.
- Modo escuro, com todas as cores em variáveis e botão de troca.
- Layout responsivo em quatro faixas: monitor, notebook, tablet e celular.
- Nova tela de entrada: perfil, busca pelo nome, resumo da carteira de cada
  pessoa e atalho para o último acesso.
- 9 testes automatizados do fluxo de contato (antes não havia teste de JS).

**QA, duas rodadas.** Cada rodada percorreu 13 telas em 4 tamanhos (1440, 1024,
768 e 360 px) e 2 temas, 104 verificações, checando rolagem horizontal, elemento
fora da tela, controle pequeno demais, contraste de texto e erro de console.

| Rodada | Resultado |
|---|---|
| 1 | Sem estouro de largura e sem erro. Achou texto cinza-claro com contraste 3,1 no tema claro (o mínimo é 4,5) em seis tipos de elemento |
| 2 | Depois da correção, restou um contador das abas com 4,3; corrigido |

Erro da IA achado na conferência visual: os prints de celular tirados com o
navegador sem janela saíram cortados, porque ele não aceita largura menor que
500 px. Foram refeitos pelo painel, em 390 px.

**Ainda sem decisão do Gustavo:** como definir os pesos do score com mais
fatores; os KPIs do vendedor e do gerente dependem disso.

---

## Decisão 27 — Fechamento das pendências

A IA tinha deixado cinco decisões em aberto (decisões 10, 12, 20, 23 e 25). O
Gustavo respondeu a todas de uma vez:

**Prazos de retorno** (religar em 2 dias, segunda mensagem em 3, três
tentativas):

> "Vamos seguir"

**Três ligações sem resposta.** A IA mandava para "Encerrar" e depois sugeriu
"revisar com o gerente". O Gustavo definiu outra coisa:

> "vamos passar para outra etapa de mensagens, dai se nao responder encerra,
> precisa verificar com clietne"

Implementado: depois da terceira ligação sem resposta, o próximo passo vira uma
mensagem para confirmar o interesse. Só o silêncio nos dois canais encerra. Se o
cliente responder, a negociação volta para ligação, do zero.

**Coluna Score na tabela:**

> "vamos manter entao, mas tem que ser auditavel e o vendedor entender de foram
> clara e objetiva o porque daquele score"

Implementado: o pop-up abre com "Por que o score é N", mostrando os dois fatores
(valor do produto e chance de fechar), a posição entre as negociações com
chance e um link para a conta e o teste.

**Enxugar a entrega:**

> "voce achja nesseario isso?"

Resposta da IA: em parte. Vale um resumo curto no topo deste registro, para quem
tem cinco minutos; não vale apagar análises, que são a prova do que foi afirmado.
Foi feito só o resumo.

**Declarar o tempo gasto:**

> "nao estamos mais de 6 horas trabalhando nisso"

**Erro da IA:** ela tinha afirmado que o trabalho levou "bem mais que 6 horas",
repetindo a suposição de dois subagentes avaliadores, que julgaram pelo volume.
Conferindo os horários dos arquivos, a sessão começou às 20h48 e esta decisão
foi tomada perto de meia-noite: cerca de três horas e meia. O Gustavo estava
certo. O tempo passou a constar no README.

**Governança (decisão 12):** resolvida na decisão 13, com a entrada por perfil
sem senha, declarada nas limitações.

**Ainda em aberto:** como definir os pesos se o score ganhar mais fatores, e os
indicadores do vendedor e do gerente, que dependem disso.

---

## Decisão 28 — Nono layout: sistema com nome, três perfis, ícones e exportação

**Pedido do Gustavo:**

> "Tela de login tem que ser mais simpes e objetiva, escolkher entre os roles
> existentes (mais de 2 acredito), selecionar cada etapa, sempre com um frontend
> moderno e agradavel visualmente. Vamos alterar o nome de empresa em vez de
> FOCO para Case G4 - AI Master e criar como se fosse um sistema mesmo, quero
> que a gente possa altrar sempre a questao da governanca, ou seja eu sair e
> migrar para outro perfil, instale tambem a biblioteca de icons phospor [...]
> o objeito nao é deixar só visualmente bonito, mas ter algo que não seja
> cansativo para o gerente e o vendedor [...] tambem adicione o efeito de
> SKELETON se formos mudar de pagina, e somente nas informacoes que sao
> dinamicas como numeros. tambem botoes de exportar via planilha em CSV tambem
> em PDF"

**O que foi feito:**

- Nome do sistema: Case G4 · AI Master.
- Entrada em duas etapas: primeiro o perfil (vendedor, gerente ou operações de
  receita, que era um item escondido na lista de gerentes), depois o nome, com
  busca. O botão "Trocar perfil" fica sempre na barra lateral.
- Ícones Phosphor (MIT). A IA copiou a fonte para dentro do projeto em vez de
  usar CDN, para manter a decisão do Gustavo de rodar sem dependência externa.
- Efeito de carregamento ao trocar de página, só nos números (contadores,
  valores, score, último contato). Quando o navegador pede menos animação, o
  bloco aparece parado.
- Exportação em CSV (o que está filtrado, na ordem da tela) e em PDF. O PDF usa
  a impressão do navegador com um estilo próprio e todas as linhas, sem
  biblioteca.

**QA, terceira rodada:** 14 telas em 4 tamanhos e 2 temas, 112 verificações.
Sem estouro de largura e sem erro de console. Achou o número da etapa inativa
com contraste 4,4 no tema claro e 3,9 no escuro; corrigido.

---

## Decisão 29 — Fila inteira, sem efeito de carregamento, telas mais limpas

**Tamanho da fila.** A IA recomendou limitar a fila de Hoje às 10 primeiras,
que é o que o teste validou. O Gustavo decidiu o contrário:

> "Acreidot que nao precisa. vamos manter a fila toda"

**Efeito de carregamento.** Tinha sido pedido por ele na decisão 28; depois de
ver, ele mandou tirar:

> "Nao gostei do efeito skeleton, retire ele"

**Página Hoje e demais perfis:**

> "Pagina de HOJE do vendedor esta extremaemnte confusa, muita poluicao visual
> dele. melhora isso"

> "Faca essa modificacao de visual e layout para os outros perfis tambe, estao
> todos ruine e estranhos para se testar."

**O que saiu da página Hoje:** os quatro quadros do topo (viraram uma faixa
única com o progresso do dia), o filtro de produto e os botões de exportar
(ficaram na Carteira), a coluna "Último contato" (mostrava "Nunca" em toda
linha) e as cores do score.

**O que mudou para gerente e operações de receita:** os três blocos de números
viraram a mesma faixa única; a tabela de vendedores perdeu duas colunas e o
destaque amarelo de linha inteira, trocado por um aviso discreto abaixo do nome;
os painéis de resultado só aparecem quando há contato registrado.

**Preocupação registrada pelo Gustavo:**

> "Meu receio é deixar a desejar na parte principal, que é a logica por tras.
> garantir que funcione e resolve o pro problema"

A IA lançou mais uma verificação independente, só da lógica, pedindo que
recalcule à mão cinco negociações e confira código, tela e README entre si.

---

## Decisão 30 — Logo do G4 e favicon

**Pedido do Gustavo**, enviando a imagem da logo:

> "Aqui esta a logo da G4, precisamos adicionar ela no sistema e tambem no
> favicon do site"

**O que foi feito:** a logo entrou na barra lateral e na tela de entrada. O
favicon usa só o símbolo, recortado da própria imagem. Para o tema escuro a IA
gerou uma versão em que o "G4" azul-marinho fica claro, porque no fundo escuro
ele sumia; o dourado não mudou.

**Ressalva levantada pela IA:** a logo é marca do G4. Dentro da submissão ao
desafio do próprio G4 o uso é natural; numa demonstração pública, pode parecer
um produto oficial. Por isso a tela de entrada passou a dizer "Projeto de
candidato para o AI Master Challenge. Não é um produto oficial do G4; os dados
são fictícios".

---

## Decisão 31 — Resultado da última verificação da lógica

A verificação independente pedida na Decisão 29 recalculou as 2.089
negociações abertas e não achou nenhuma diferença contra o que a tela mostra,
nem vazamento de informação do futuro no teste histórico. Veredito: "a lógica
está correta e entregável". Sobraram arestas pequenas (eventos registrados
depois de uma negociação concluída, armazenamento corrompido no navegador,
arredondamento que invertia pares vizinhos), todas corrigidas e cobertas por
teste. Total: 16 testes da priorização e 13 do fluxo.

---

## Decisão 32 — Painel de gestão com indicadores e gráficos

**Pedido do Gustavo:**

> "Os gestores precisam ter uma visao com mais detalhes e governanca de cada
> vendedor, acredito que a visao de agora esta muito simples. tambem a oprações
> de receita nao tem graficos, KPIS importantes e etc."

**O que foi feito:** a tela "Time" virou duas. **Painel**: quatro indicadores
e quatro gráficos (receita ganha por mês, negociações iniciadas por mês,
pipeline aberto por time ou por vendedor, chance por faixa). **Vendedores**:
uma linha por pessoa e uma página de detalhe com carteira, prioritárias sem
contato, receita por mês e últimos contatos registrados.

**Limite que a IA manteve:** a taxa de ganho não diferencia vendedores nesta
base (Decisão sobre os sinais), então o detalhe serve para acompanhar carteira
e atividade, não para ranquear pessoas. A tela diz isso.

**Escolha técnica:** gráficos em HTML e CSS, sem biblioteca, para o projeto
continuar sem dependências e abrindo com dois cliques.

---

## Decisão 33 — Barra de navegação embaixo no tablet e no celular

**Pedido do Gustavo, depois de testar no celular:**

> "Testei no mobile e o sistema nao esta legal, acredito que no tablet e mobile
> ter uma barra embaixo com os botoes para trocar de paginas é extremamente
> interessate."

**O que foi feito:** até 900 px de largura, as páginas ficam numa barra fixa
embaixo, com ícone, nome e contador. Conferido em 390 px e 768 px, nos três
perfis e nos dois temas, sem rolagem horizontal.

---

## Decisão 34 — Ficha da negociação em duas colunas, sem o painel de demonstração

**Pedidos do Gustavo:**

> "ja deixando as informacoes da empresa no lado direito e as demais coisas no
> lado esquerdo, aumentar o tamnho vertical do popup"

> "A etapa: Demonstração: ver os retornos acontecendo ... na pagina de como
> funciona, não precisa ter"

**O que foi feito:** a ficha ficou mais larga e mais alta; ação, explicação do
score, roteiro e histórico à esquerda, dados da empresa à direita (no celular,
uma coluna só). O botão "avançar um dia" saiu da tela; a ferramenta usa sempre
a data real do navegador.

---

## Decisão 35 — Kanban como segunda visualização e "Ver dados" refeito

**Pedidos do Gustavo:**

> "deixe para os usuarios mudar a forma que a tabela aparece para eles, por ex:
> mudar a visualização, agora esta em lista, mas ele pode mudar para kanban"

> "A parte de 'ver dados' no login do manager, podemos mudar esta parte não
> ficou legal, e esta complicando e bugando o layout"

**O que foi feito:**

- Em Hoje e na Carteira há um seletor Lista / Kanban. O kanban separa as
  mesmas negociações em colunas por situação (retornos de hoje, para ligar,
  primeiro contato, reativação, aguardando, encerrar, concluídas) e, dentro de
  cada coluna, mantém a ordem de prioridade que o teste histórico validou. A
  preferência fica guardada no navegador.
- Cada coluna mostra até 25 cartões e avisa quantos ficaram de fora, porque um
  gerente tem até 2.089 negociações e um kanban com tudo travaria a tela.
- O "Ver dados" que abria embaixo de cada gráfico e empurrava o cartão vizinho
  virou um botão "Tabela" no canto do cartão: troca o gráfico pela tabela dos
  mesmos números, na mesma altura, sem mexer no resto da página.

**Ressalva da IA:** o kanban é só visualização. Não dá para arrastar um cartão
de coluna, porque a situação de uma negociação é derivada dos contatos
registrados, não escolhida à mão; arrastar criaria um estado que os registros
não sustentam.

---

## Decisão 36 — Painel de gestão reorganizado

**Crítica do Gustavo à primeira versão do painel:**

> "Não me agrada o layout do gerente, tem muita informação desperada e graficos
> despejados, precisamos melhroar essa visualização"

**O que mudou:** os quatro gráficos do mesmo tamanho, lado a lado, deram lugar
a duas seções com título e uma ordem de leitura:

- **Pipeline hoje**: o gráfico principal (negociações abertas por time ou por
  vendedor) com a divisão por faixa de chance ao lado, e logo abaixo uma faixa
  "Prioritárias sem contato" com os cinco vendedores que mais têm negociação
  boa parada. Clicar no nome abre o detalhe do vendedor.
- **Como veio 2017**: um gráfico só, com um seletor entre receita ganha e
  negociações iniciadas, em vez de dois gráficos disputando espaço.

Os quatro indicadores do topo ficaram como estavam.

---

## Decisão 37 — O que o gerente precisa ver: previsão e atividade

**Pedido do Gustavo:**

> "Analise e repasse todas as informações principais que um gerente precisa ter
> e acessar, e verifique se estamos apresentando isso no sistema"

A IA listou o que um gerente comercial precisa e conferiu tela por tela. Oito
itens já estavam cobertos (pipeline com chance real, tempo gasto em negociação
morta, oportunidade boa parada, carga por vendedor, navegação do time até a
negociação, resultado do ano, governança por time, exportação). Dois faltavam,
e o Gustavo mandou incluir os dois:

- **Previsão de receita.** O painel mostrava $307 mil "com chance", a preço de
  tabela, o que infla a expectativa. Agora mostra o valor esperado (preço ×
  chance): cerca de $64 mil na empresa, com quantas podem fechar no mês.
- **Atividade do time.** Contatos nos últimos 7 dias, prioritárias já
  contatadas, taxa de resposta positiva e quantos vendedores estão usando.

**Limite declarado na própria tela:** sem servidor, os registros ficam no
navegador de cada pessoa; o gerente só vê os contatos feitos no mesmo
navegador. Num cliente real, é a primeira coisa a resolver.

**O que ficou de fora de propósito:** meta por vendedor (a base não tem) e
ranking por taxa de ganho (ela não diferencia ninguém nesta base).

---

## Decisão 38 — Varredura de celular e tablet

**Crítica do Gustavo:**

> "outra cosia que precisamos melhorar é a questao do mobile/tablet, tem
> elementos que fazem a pagina quebrar"

**Como a IA procurou:** um script percorreu todas as telas dos três perfis em
390 px e 768 px, listando o que passava da largura da tela e os botões com
menos de 32 px de altura; depois, prints de todas as telas lado a lado em
molduras com a largura real do celular, para ver o que o script não vê.

**O que estava quebrado e foi corrigido:**

- o Painel rolava de lado no celular (o seletor de medida do gráfico forçava a
  largura do cartão);
- o topo ocupava duas linhas; agora é uma, com os dois botões só com ícone;
- as abas de Hoje cortavam "Mensagem"; agora as quatro cabem;
- busca e seletor Lista/Kanban ficaram na mesma linha; filtros da Carteira,
  dois a dois;
- a tabela de Vendedores era cortada; no celular ficam as duas colunas que
  pedem ação e o resto está no detalhe do vendedor;
- o botão "Tabela" dos gráficos caía para uma linha própria;
- rótulos dos gráficos cortados ("Com chance de fe...") agora quebram linha, e
  o eixo dos meses perde o "/17" quando não cabe;
- links e botões pequenos passaram a ter pelo menos 40 px de altura.

---

## Decisão 39 — "Vamos concentrar o foco em entregar algo que FUNCIONE"

**Pedido do Gustavo**, depois das rodadas de interface:

> "Agora que acertarmos as primeiras versoes da parte de front-end [...] vamos
> concentrar o foco em entregar algo que FUNCIONE"

Em vez de mais uma revisão de leitura, a IA fez dois ensaios de uso.

**1. Ensaio do avaliador.** A submissão foi copiada para uma pasta vazia, fora
do projeto, e um script rodou ali tudo o que o README promete: `build.py`,
`backtest.py`, os 16 + 13 testes, os 29 scripts de análise de `docs/analises`
e a abertura do `index.html` com dois cliques (`file://`, sem servidor) nos
três perfis.

- Na primeira rodada, 6 das 38 etapas falharam, todas em scripts de apoio:
  20 arquivos tinham caminhos da minha máquina (`D:\Case G4\...`), três
  dependiam de um arquivo que outro script gera, e três tinham ficado para
  trás quando o código mudou. Nenhuma falha era da ferramenta.
- Corrigido: caminhos relativos à submissão, dependência resolvida, scripts
  ajustados sem mudar o que medem. Segunda rodada: **38 de 38**.
- O `data.js` regerado a partir dos CSVs saiu idêntico, byte a byte, ao
  entregue.

**2. Fluxo completo na tela**, clicando como vendedora e avançando os dias:

- 3 ligações sem resposta (volta em 2 dias a cada vez) → vira mensagem de
  confirmação → sem resposta em 3 dias → vai para Encerrar;
- 3 mensagens de reativação sem resposta → Encerrar;
- retorno combinado com data e anotação → some de Hoje, aparece em Aguardando,
  volta no dia como primeira da fila, com a anotação;
- fechou → sai da lista; desfazer → volta;
- CSV da carteira (103 linhas) e do time; painel do gerente refletindo os
  contatos registrados.

**Um erro achado e corrigido:** na última tentativa de mensagem, a tela dizia
"sem resposta, volta para Hoje", mas a regra manda para Encerrar. A regra
estava certa; o texto, não.

**O que continua sem prova**, e não tem como ter nesta base: que os vendedores
vão usar e que a receita sobe. Isso é o piloto (`docs/plano-de-piloto-e-adocao.md`).

---

## Decisão 40 — Três revisões antes de enviar: feedback alheio, avaliador e aderência

**Pedido do Gustavo:**

> "Antes disso, verificamos os feedbacks que foram passados para outras pessoas
> e se nao estamos cometendo os mesmos erros bobos? [...] como modificamos
> muitas coisas no front-end, precisamos voltar o foco na solucao, ela de fato
> resolve o problema? estamos fazendo tudo que a task pediu? da forma que pediu?"

Três subagentes independentes, sem acesso às conclusões uns dos outros:

1. **Feedback dado a outros candidatos.** Leu as avaliações de 98 Pull Requests
   do repositório do desafio (51 do Challenge 003) e conferiu a submissão contra
   cada erro que custou ponto a alguém.
2. **Avaliador.** Rodou tudo seguindo só o README e deu nota: 7,4 como estava
   ("aprovado com ajustes"), 8,2 com as pendências resolvidas.
3. **Aderência ao enunciado.** Listou 32 requisitos com a frase original e
   conferiu um a um, refazendo as contas nos CSVs.

**O que as três acharam, e a IA conferiu antes de mexer:**

| Achado | Conferência | O que mudou |
|---|---|---|
| O README se sabotava: "o preço domina, a chance só acrescenta o corte" | Refeita a conta: ordenando só por preço as mesmas negociações, a receita cai 19% e 41%; a ferramenta ganha em 24 de 24 semanas | Comparação incluída em `backtest.py`; frase corrigida no README e na tela |
| O resultado dependia do corte de 90 dias da regra simples? | Testado com 45, 60, 75, 100, 120 e 138 dias: ganha em todos, de +6% a +50% | Tabela de sensibilidade em `backtest.py` e no README |
| "Tamanho da conta", citado no enunciado, não tinha linha própria | Funcionários p = 0,36; faturamento p = 0,03 mas sem direção (63%, 62%, 66%, 61%) | Entrou no teste e na tabela "o que não entra na conta" |
| A ficha mandava "Ligar" para negociação sem empresa, sem aviso | 91 das 128 com chance não têm empresa | Aviso na ficha com o código para localizar no CRM; declarado nas limitações |
| Oito vendedores sem negociação aberta não conseguiam entrar | Reproduzido | Entram e veem um aviso de lista vazia |
| Filtro por manager era só troca de perfil | Conferido | Filtro "Time" na Carteira de operações de receita |
| "Nunca depois" do trimestre seguinte | Vale para as 4.238 ganhas; entre as 2.473 perdidas há uma exceção | Texto corrigido |
| "Cerca de 160 combinações testadas" | Os arquivos guardam 103 | Texto corrigido para "mais de 100" |
| "24 decisões", "sete versões", "sem CDN", tela "Time" | Conferidos | Corrigidos |
| README em primeira pessoa para análises que a IA executou | Conferido no próprio log | Abordagem reescrita separando "IA" de "eu"; parágrafo "Quem fez o quê" |
| O botão de baixar os registros de contato tinha sumido da tela | Conferido | Voltou, no Painel: é o dado do piloto |

**O que as revisões pediram e depende do Gustavo** (não foi aplicado):

- Incluir a conversa exportada e prints da conversa: foi o que mais reprovou
  ou travou outros candidatos. A IA preparou `chat-exports/exportar.py`; na
  primeira tentativa o aplicativo não a deixou ler a sessão. Depois, a pedido
  do Gustavo ("voce nao consegue exportar esta conversa aqui?"), a exportação
  foi feita pelo próprio aplicativo e convertida pelo script. Os prints da
  conversa continuam com ele.
- Separar a reativação e o primeiro contato da fila de ligações. Dois revisores
  apontaram que, para metade do time, a fila do dia é só mensagem ordenada por
  preço. Isso reabre a Decisão 29 (manter a fila inteira), então é dele.

---

## Decisão 41 — QA por recálculo: o teste histórico exagerava

**Pedido do Gustavo:**

> "Agora vamos lancar agentes para realizar funcoes de QA, garantindo que tudo
> esta funcional, e garantindo que todas as partes logicas do sistema esta
> fazendo. Garanta que a forma que vamos entregar esta de acordo com oq foi
> pedido."

Três agentes: um testando a interface, um recalculando a lógica do zero a
partir dos CSVs (sem usar o código da solução) e um conferindo o formato da
entrega com um ensaio de commit num clone separado.

**O que o recálculo confirmou:** as 2.089 negociações abertas batem em todos os
campos (idade, chance, lista, faixa, score); não há vazamento de informação do
futuro; todos os números que o `backtest.py` imprimia foram reproduzidos.

**O que o recálculo derrubou.** Vários produtos têm o mesmo preço, então uma
regra "o mais caro primeiro" tem muitos empates. O teste desempatava essas
regras pela ordem do arquivo, que põe a negociação mais velha primeiro: o pior
caso possível para a regra simples. Ninguém tinha escolhido isso de propósito,
e nenhuma das revisões anteriores viu. A IA refez a conta e confirmou:

| Comparação | Como estava (desempate pela mais velha) | Desempate por sorteio | Desempate pela mais nova |
|---|---|---|---|
| Contra "preço, até 90 dias" | +13% e +10% | +9% e +3% | +7% e −3% |
| Contra "preço, entre as que a ferramenta mantém" | +19% e +41% | +14% e +20% | +10% e +4% |

**O que mudou:**

- `backtest.py` desempata as regras de comparação por sorteio (semente fixa),
  mostra também a regra "preço, depois a mais nova" e uma medida sem repetir
  negociação. Há um teste automatizado que falha se o texto sobre o 4º
  trimestre deixar de ser verdade.
- README, página "Como funciona" e exemplos passaram a dizer o que se
  sustenta (o corte: 0 de 801; a ordem das faixas; a vantagem sobre "só preço")
  e onde a ferramenta empata (contra uma boa regra simples, no 4º trimestre).
  Os números "+19% e +41%", escritos na Decisão 40, ficaram errados por um dia.
- O indicador "Previsão de receita" do painel virou "Valor esperado das com
  chance", com o aviso de que não é a previsão do trimestre: a mesma conta
  previu 43% de ganho onde 35% aconteceram.
- Os parâmetros da lógica (janela de ±7 dias, amostra mínima de 15, cortes das
  faixas) estavam só no código; agora estão numa tabela no README.
- Fluxo: dois avisos errados corrigidos (retorno marcado para hoje; última
  mensagem), prazos contados em dias de calendário, e registros corrompidos
  não somem mais com a negociação. Três testes novos.

**Leitura do Gustavo que isso confirma:** desde a Decisão 24 ("resolve ou
mascara?") a entrega diz que uma regra simples faz boa parte do trabalho. O
recálculo mostrou que isso vale também para a ordem, não só para o corte.

**O QA da interface** rodou 834 verificações automáticas num Chrome controlado
por script (cliques, duplo clique e teclas de verdade), nos três perfis, em
390, 768 e 1440 px. Nenhuma tela quebrada; 27 defeitos, 13 deles do tipo que
atrapalha o uso. Corrigidos e conferidos um a um:

- **Governança:** um vendedor sem negociações conseguia baixar, pelo CSV, a
  tabela que o perfil anterior tinha deixado na tela; e o CSV de registros de
  contato trazia os registros de todos os times. Agora cada exportação só leva
  o que o perfil enxerga.
- **Registro sem querer:** apertar Esc numa confirmação e clicar em outro lugar
  reabria a ficha já em "Confirmar"; e um duplo clique em "Sem interesse"
  confirmava sozinho, porque o botão Confirmar aparecia no mesmo lugar. Esc
  agora esquece a ação, e um segundo clique em menos de 0,4 s não confirma.
- **PDF em retrato** saía desalinhado (a folha é mais estreita que a tela);
  agora sai em colunas.
- **Avisos escondidos atrás da ficha** ("escolha a data", "mensagem copiada")
  passaram a aparecer por cima dela. Data com ano inválido ou além de 12 meses
  é recusada com aviso.
- "Abrir carteira" de um vendedor sem negociações deixava a Carteira presa em
  vazio; a busca ficava inutilizável em 768 px; o score sumia da lista no
  celular; o nome do vendedor aparecia cortado na Carteira do gerente; busca
  sem acento não achava "Saúde". Todos corrigidos.
- Cada registro passou a guardar quem o fez (vendedor ou gerente), e as
  células dos CSVs que começam como fórmula são neutralizadas.

Ficaram como estão, por serem cosméticos e declarados aqui: o contador "X de Y
feitos hoje" não sobe em todos os tipos de registro; depois de registros, o
Painel conta 3 negociações concluídas a menos que a Carteira; e a tabela de um
gráfico volta para gráfico ao trocar a medida.

---

## Decisão 42 — A fila de Hoje em duas partes (reabre a Decisão 29)

**O problema.** Na Decisão 29 o Gustavo manteve a fila do dia inteira numa
lista só. Depois, dois revisores independentes (Decisão 40) apontaram a mesma
coisa como o maior risco da lógica: para metade do time a tela de Hoje não
priorizava. Um vendedor do Central abria com "0 de 169 feitos hoje"; na fila de
uma vendedora do West, 17 dos 30 itens eram reativações com chance "Nenhuma",
na mesma lista e no mesmo contador das 13 ligações que valem dinheiro. A IA não
mexeu, porque a decisão era dele, e perguntou.

**Pergunta do Gustavo:**

> "Separo a fila de Hoje em ligações primeiro e mensagens num bloco à parte?
> oque voce recoemdna?"

**Recomendação da IA:** separar, sem tirar nada da tela e sem mexer na conta da
priorização. Custo declarado: reabrir uma decisão dele e mexer em tela depois
do QA. Alternativa oferecida: manter a fila única e declarar a limitação.

**Decisão do Gustavo:**

> "Sim, separar"

**O que mudou na tela de Hoje:**

- **Em cima, a meta do dia:** retornos combinados (data marcada, cliente
  respondeu, nova tentativa de ligação) e negociações com chance, na ordem
  preço × chance. É a ordem que o teste histórico mediu.
- **Embaixo, "Se sobrar tempo":** primeiro contato e reativação. O histórico
  não consegue ordenar essas, então vêm antes as que têm empresa cadastrada
  (sem empresa, o vendedor ainda precisa descobrir no CRM quem é o cliente);
  dentro disso, primeiro contato antes de reativação e o mais caro antes. A
  segunda mensagem de uma reativação que ficou sem resposta volta para este
  bloco, não para a meta.
- **O contador** virou "X de Y prioridades feitas hoje" e conta só a parte de
  cima; ao lado aparece "Mais N se sobrar tempo". O número do menu passou a ser
  o das prioridades que faltam.
- **Quem não tem nenhuma prioridade** (os dez vendedores do Central) vê
  "Nenhuma prioridade hoje" e o bloco de baixo com o título "Para abrir
  conversa". A tela diz que, sem negociação com chance, a ferramenta não tem
  como dizer qual vale mais.
- Abas, busca e ordenação por coluna continuam, e não misturam as duas partes.
  No kanban nada mudou: as colunas já separavam por situação.

**O que não mudou:** `scoring.py`, as quatro listas, a regra de reativação e os
números do teste histórico. Nenhuma negociação saiu da tela. A ordem "empresa
cadastrada primeiro" é bom senso, não dado, e está nas limitações do README.

**Conferido no navegador,** com cliques de verdade:

- West (13 ligações e 17 mensagens): "0 de 13", divisor depois da linha 13.
  Registrar "não atendeu" numa ligação leva a "1 de 13"; registrar uma mensagem
  enviada no bloco de baixo não mexe no contador e reduz "Mais 17" para 16.
- Dois dias depois, a ligação não atendida volta como primeira da meta; três
  dias depois, a reativação sem resposta volta no topo do bloco de baixo.
- Central (169 mensagens): "Nenhuma prioridade hoje", título "Para abrir
  conversa", e as 50 linhas da primeira página têm empresa cadastrada.
- Ordenar por valor ordena cada parte separadamente; as abas Ligar e Mensagem
  filtram certo; Carteira, Aguardando e as telas de gestão não mudaram; 375 px
  sem rolagem lateral.

Com isso, o defeito cosmético do contador registrado na Decisão 41 deixa de
valer como estava escrito: agora o contador sobe quando um registro de hoje
tira uma prioridade da fila, e não sobe, de propósito, para o que é do bloco
"se sobrar tempo".

**Ensaio do zero depois da mudança:** a primeira rodada deu 36 de 38. Os dois
que falharam eram scripts de apoio (`docs/analises/verificacao2/sim.js` e
`sim2.js`) que simulam a tela e chamavam a função antiga da fila. Ajustados à
fila em duas partes, a segunda rodada deu 38 de 38: os 19 testes da
priorização, os 16 do fluxo, o `data.js` regerado idêntico ao entregue e as
quatro telas abrindo por `file://` sem erro. Os prints da tela de Hoje, de
celular, de tablet e de "Como funciona" foram refeitos, e os exemplos em
`docs/exemplos/` passaram a mostrar as duas partes.

---

## Decisão 43 — Envio e demo pública

**Commits.** Nada foi commitado enquanto a solução mudava: os commits
dependiam da aprovação do Gustavo. Com o "Sim, pode" dele, a IA fez os commits por
componente (dados e priorização, teste histórico, gerador dos dados, fluxo de
contato, interface, documentação, process log), todos com o horário real de
18/11. O histórico de commits mostra a organização da entrega; a evolução de
verdade está neste registro e na conversa exportada.

**Prints da conversa.** A IA vinha tratando prints da conversa como
obrigatórios. O Gustavo perguntou:

> "e realmente precisa das prints das conversas? nao basta somente tudo que
> conversamos aqui?"

A IA releu o guia do G4: ele aceita seis formatos de process log e diz
"escolha um ou combine". A conversa exportada, este registro e o histórico de
commits já cobrem três. A IA corrigiu a própria orientação: prints são reforço,
não requisito. A submissão foi enviada sem eles.

**Demo.** Pedido do Gustavo:

> "Acho legal colocar uma demo no vercel, suba para este repositorio"

A pasta `solution/app` foi copiada, sem alteração, para um repositório próprio
(o do desafio não pode ter arquivos fora da pasta da submissão), e o Gustavo
publicou na Vercel sem configuração: <https://case-g4-gustavo-c.vercel.app/>.
A IA abriu a demo publicada e conferiu a tela de Hoje de uma vendedora e o
Painel de operações de receita, sem erro no console. A demo é pública e sem
senha; a tela de entrada já dizia que é projeto de candidato, não produto
oficial do G4 (ressalva da Decisão 30), e os dados são fictícios.

---

## Decisão 44 — Prints da conversa, depois de ler como os aprovados foram avaliados

**Pedido do Gustavo,** já com o PR aberto:

> "veja os prs do challenge 3 e o pq foram aprovados e ve se o meu segue bnessa
> linha"

**O que a IA leu:** as revisões formais dos 48 PRs do Challenge 003 que o G4
já tinha avaliado (33 aprovados, 15 com pedido de mudanças), pela API pública
do GitHub.

**O que os aprovados têm em comum e a submissão também tem:** hipóteses
derrubadas pelos dados, recusa de modelo sofisticado quando o sinal é fraco,
"hoje" fixado no fim da base, controle de vazamento, teste histórico com corte
no tempo, testes automatizados, auditoria por outro agente, erros da IA com a
causa, separação entre decisão humana e IA, e demo no ar. O achado dos 138
dias não é exclusivo: outros dois candidatos aprovados chegaram nele.

**Onde a IA tinha errado.** Na Decisão 43 ela disse que prints da conversa
eram reforço, porque o guia aceita "um ou mais" formatos. As revisões mostram
outra coisa: em três PRs deste challenge o avaliador exigiu prints das sessões
com a IA antes de aprovar, e num deles o motivo foi exatamente ter só capturas
da aplicação final. Outros passaram só com a conversa exportada, então não era
certo que travaria, mas a orientação estava frouxa. A IA disse isso ao
Gustavo e indicou os momentos que valiam print.

**O que o Gustavo fez:** tirou 19 prints da própria conversa, nos momentos em
que decidiu, discordou ou mandou conferir: quando parou a IA, a regra de
reativação, a intuição dele posta à prova pelos dados, a exigência de
governança, o layout rejeitado (com a auditoria que achou o erro no cálculo da
chance), a pergunta "resolve ou mascara?" e a separação da fila de Hoje.

**O que a IA fez:** abriu os 19 arquivos um a um antes de incluir (só trechos
da conversa, sem dado pessoal), pôs em ordem cronológica em
`screenshots/conversa/` e listou cada um, com data, hora e o que mostra, no
README dos prints.

---

## Decisão 45 — Conferir a entrega contra os motivos de reprovação dos outros

**Pedido do Gustavo:**

> "Agora veja TODOS do case 3 que foram reprovados, e ve se o motivo eu estou
> cometendo"

**O que a IA fez:** leu na íntegra as revisões com pedido de mudanças dos PRs
do Challenge 003 (os 15 que seguem reprovados e os que foram reprovados antes
de aprovar), agrupou os motivos em 17 e conferiu cada um na submissão com um
script que só lê o repositório (`higiene`, chaves, commits, números dos
READMEs contra o `data.js` e as constantes do `scoring.py`).

**Resultado:** 11 motivos não se aplicam; 4 se aplicam em parte e estão
declarados (commits concentrados no mesmo dia, análise executada pela IA, dez
vendedores sem priorização, prazos de retorno sem dado por trás); 2 se
aplicavam e foram corrigidos:

| Motivo visto nos reprovados | O que havia aqui | Correção |
|---|---|---|
| Defeito documentado na própria submissão e não corrigido | A Decisão 41 declarava dois: o Painel e a Carteira contavam as concluídas de forma diferente, e a tabela de um gráfico voltava para gráfico ao trocar a medida | A Carteira passou a contar só as abertas no menu e a dizer "N abertas e M concluídas nesta ferramenta"; cada gráfico lembra que foi deixado em tabela, mesmo trocando a medida, o filtro ou a página |
| Documentação diferente do que está implementado | O plano de adoção citava o indicador "Previsão de receita", renomeado na Decisão 41 para "Valor esperado das com chance" | Nome corrigido no plano |

O terceiro defeito declarado na Decisão 41 (o contador do dia) já tinha sido
resolvido na Decisão 42. Com isso não resta defeito conhecido sem correção.

**Conferido no navegador:** com a tabela aberta em "Como veio 2017", trocar a
medida, trocar a região e sair e voltar ao Painel mantêm a tabela; voltar ao
gráfico também se mantém. Depois de três negociações marcadas como "Sem
interesse" por uma vendedora, o menu dela mostra 100 na Carteira (eram 103) e
a página diz "100 abertas e 3 concluídas"; no perfil de operações de receita,
o Painel e a Carteira mostram o mesmo número, 2.086.

**O que a IA disse que não dá para corrigir:** os sete primeiros commits têm o
mesmo minuto. Mudar as datas seria falsificar o histórico; a evolução real
está neste registro e na conversa exportada, com horário em cada mensagem.

**Ensaio do zero depois das correções:** a primeira rodada deu 36 de 38; os
dois scripts de apoio que simulam a tela (`verificacao2/sim.js` e `sim2.js`)
não conheciam a função nova dos gráficos. Ajustados, a segunda rodada deu 38
de 38, com os 19 testes da priorização e os 16 do fluxo passando.
