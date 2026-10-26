# Process log: narrativa

Diário de como eu e a IA chegamos na solução. Atualizado a cada etapa. O método (etapas 0 a 7) foi commitado etapa por etapa; o build (dados, Apps Script, app, docs, process log) foi commitado em cinco blocos no fim do dia 23/10, e a terceira rodada de revisão (etapa 16) num bloco próprio logo depois, no mesmo dia.

**Ferramenta principal:** Claude Code (Opus), rodando dentro do meu sistema operacional pessoal (um vault Obsidian com meu contexto, regras e histórico de trabalho).

---

## Etapa 0: entender o problema antes de abrir qualquer ferramenta (23/10)

- Escolhi o 003, Lead Scorer, porque é o que eu faço há anos: liderar time comercial e decidir onde o vendedor gasta a semana.
- Pedi pro Claude ler o README do challenge, o CONTRIBUTING, o guia de submissão e o template direto do repositório, em vez de colar o brief num chat.
- O que tirei da leitura: o pedido real da Head de RevOps não é "prever quem fecha". É "o vendedor abre na segunda e sabe onde focar". Probabilidade de ganho é só um pedaço disso.
- Ângulo definido: **prioridade não é probabilidade**. Prioridade = chance de ganhar x valor em jogo x urgência (o deal está esfriando em relação ao ciclo normal de quem ganha?). Cada deal sai com o motivo em português claro e uma próxima ação.
- Regra que eu impus: nenhuma variável entra no score sem provar, nos deals já fechados, que mexe na taxa de ganho. E o score passa por um backtest num período posterior antes de ir pra tela.

## Etapa 1: setup

- Fork, clone e branch `submission/ricardo-oliveira` feitos pelo Claude Code com a credencial git que já estava configurada na minha máquina.
- Pegadinha: o `.gitignore` do próprio repo ignora `submissions/`, e a regra do PR proíbe mexer em qualquer arquivo fora da minha pasta. Editar o `.gitignore` quebraria a regra. Solução: `git add -f` só na minha pasta.

## Etapa 2: método e primeira pergunta pros dados (23/10)

- Antes de qualquer código, defini o método e pedi pro Claude organizar num SOP: primeiro o ICP (quem compra, recompra e fica, por região se mudar), depois o MEDDPICC deal a deal, e só então a prioridade.
- O Claude leu os CSVs e trouxe o que muda o plano: 68% dos deals abertos (1.425 de 2.089) não têm conta, região é o escritório do vendedor e não do cliente, e o CRM não tem nenhum campo de MEDDPICC além de aproximações.
- Minha primeira pergunta no pipeline: quantas contas únicas, quantas ganhamos, quantas perdemos. Resposta: 85 contas, e as 85 têm deal ganho e deal perdido. Nenhuma conta só ganha ou só perde. Taxa de ganho por conta vai de 53% a 75% (mediana 63%, geral 63,2%).
- Leitura: contar contas não separa nada. O ICP vai ter que sair da taxa de ganho, do ticket e da recompra por conta, não de "comprou ou não comprou".
- Minha hipótese seguinte: o jogo é upsell e cross-sell na mesma conta. Pedi pro Claude testar antes de assumir. Resultado: não é bem isso. Toda conta já comprou 6 ou 7 dos 7 produtos, e 88% dos ganhos (3.716 de 4.238) são recompra de um produto que a conta já tinha. É um motion de recompra em alto volume (mediana de 83 deals por conta em 14 meses), não de expansão. Ressalva: os fechamentos só começam em mar/2017, então a primeira compra de cada conta pode ser anterior à janela.
- Achado de RevOps que eu não esperava: mediana de 14 vendedores diferentes trabalhando a mesma conta. Não existe dono de conta.
- Subi o pipeline numa Google Sheet pra olhar com meus próprios olhos e criei a coluna `sales_cycle_days` (close_date menos engage_date). Pedi pro Claude abrir uma aba por estágio (Won 4.238, Lost 2.473, Engaging 1.589, Prospecting 500) com FILTER sobre a aba original, pra ver o funil etapa por etapa sem duplicar dado. Ele conferiu as contagens contra o CSV e apontou que minha coluna de ciclo quebra nos deals abertos (sem close_date a conta fica negativa e aparece como data de 1782).
- Mantive `sales_cycle_days` só pra Won e Lost (em branco nos abertos).
- Foquei nos ganhos e pedi duas tabelas na planilha, uma por conta e uma por vendedor, todas em fórmula sobre a aba Won (dá pra clicar e ver de onde vem cada número). O Claude rodou a mesma análise em código antes e conferiu a planilha contra ela. O que saiu:
  - De 8 a 29 vendedores ganharam deal na mesma conta (mediana 10). Dentro da conta, o mesmo produto é vendido por mais de um vendedor em 502 de 522 combinações conta e produto. Não há dono de conta nem especialização por produto.
  - LTV por conta de 51,6 mil a 341 mil (mediana 111,5 mil). Três contas puxam o topo (Kan-code, Konex, Condax), o resto é uma curva suave. As 21 maiores somam 37% do LTV: não é 80/20. Tiers por quartil (A a partir de 140 mil, B 111,5 mil, C 85 mil, D abaixo), com os cortes em células que eu posso mudar.
  - O vendedor que mais fecha deals na conta é o mesmo que mais fatura nela em 47 de 85 contas. No geral, volume e valor são habilidades diferentes, como eu suspeitava: Anna Snelling é 4ª em deals e 18ª em receita (ticket médio 1.322), Versie Hillebrand é 5ª e 27ª; Elease Gluck é 26ª em deals e 16ª em receita (ticket 3.615).
  - Ciclo médio por produto quase não muda: de 48 a 55 dias, só o GTK 500 vai a 64 (15 deals). Na matriz vendedor x produto, várias células têm 1 a 3 deals, então a média ali é ruído até ter amostra mínima.
- O dataset não traz moeda, só o número. Formatei os valores em dólar porque os clientes são internacionais (71 das 85 contas têm sede nos EUA e as outras 14 estão em 14 países diferentes). Depois pedi os 3 produtos mais vendidos por conta, pra ver se conta Tier A compra um tipo de produto diferente. Resultado: o mix é quase o mesmo em todos os tiers. Tier A compra menos MG Special (16% dos deals contra 24% no Tier D) e concentra 9 dos 15 ganhos de GTK 500.
- Levantei duas hipóteses de operação comercial: (1) os 3 vendedores que vendem GTK 500 virarem especialistas só nesse produto; (2) os outros virarem AEs com conta própria, pra acabar com até 29 vendedores na mesma conta. Antes de afirmar, pedi a mesma leitura pros perdidos. O que os dados disseram:
  - GTK 500 é o produto mais caro (26.768 dólares), não de entrada. São 40 deals no pipeline inteiro, 12 contas compraram, e os 3 vendedores já cuidam de 37 dos 40. A especialização já existe na prática. Com 15 ganhos em 14 meses (400 mil dólares), um vendedor só de GTK 500 faturaria abaixo da média do time.
  - Ter mais vendedores na conta não derruba a taxa de ganho: correlação de -0,01 entre número de vendedores e win rate da conta. Vendedor com 10+ deals fechados na mesma conta ganha 62,5%; com 1 a 4, 66,3%. O argumento pro modelo de AE por conta existe (coordenação, plano de conta, expansão pra série mais cara), mas não é conversão.
  - Darcel Schlecht é o 1º em deals e em receita, mas tem win rate de 63,1%, igual à média. A vantagem dele é volume, não conversão. Win rate por vendedor vai de 55,0% a 70,4%; por produto, de 60% a 65%. Perdas acontecem mais rápido que ganhos (41,5 dias contra 51,8).
- Pedi o ciclo médio por produto dentro de cada conta e um alerta de qual produto está chegando na "renovação". Não existe campo de contrato, então definimos a renovação como recompra: última compra ganha + intervalo médio entre compras daquele produto naquela conta. Resultado em 31/12/2017 (última data do dataset): 180 pares conta e produto atrasados, 203 vencendo em até 30 dias, 126 ainda não, 13 com uma compra só. Intervalo típico de recompra: 34 dias (mediana por par), mas irregular (coeficiente de variação 0,81), então a data prevista é uma estimativa, não um compromisso. 366 dos 522 pares já têm deal aberto com conta.
- Achado lateral: os ganhos sobem no último mês de cada trimestre (mar 531, jun 531, set 503, dez 511, contra 280 a 450 nos outros meses). Fechamento de trimestre é o evento de urgência mais claro que o dataset tem.
- Minha proposta de operação: os 3 vendedores que já venderam GTK 500 cuidam das 12 contas que compraram GTK 500, e o resto do time passa a ter carteira fixa de contas. O argumento não é que isso melhora conversão (os dados não mostram isso), é que também não piora, e organiza cadência e responsabilidade. Pedi pro Claude testar a parte do GTK antes de fechar. O que voltou:
  - Os 3 (Elease, Markita, Rosalina) são todos do mesmo manager, Celia Rouche, região West. Vender GTK 500 é prática de um time, não de 3 pessoas soltas.
  - As 12 contas são 18% do LTV e geraram 1.086 deals no período. Os 3 vendedores, somados, tocaram 643 deals no total. Não dá conta só com 3. Dá com o time inteiro da Celia (6 vendedores, uns 180 deals cada).
  - Nessas 12 contas, os 3 ganham 64,9% e os outros 64,1%. Mesma conversão, o que reforça o argumento de organização, não de performance.
- LTV tier x produto: o mix é quase igual em todos os tiers. O que separa tier é frequência e porte: correlação de 0,86 entre LTV e número de deals, 0,76 com a receita da empresa, 0,68 com funcionários, e só 0,35 com ticket médio. A única relação de produto é fraca e negativa: quanto mais o mix da conta é MG Special, menor o LTV (-0,38). Isso vai direto pro ICP: porte da empresa é o melhor sinal de conta boa.
- Hipótese minha: os deals sem conta são conta nova (new logo), então cada vendedor vive dois mundos, recompra em conta antiga e abertura de conta nova, e a prioridade é recompra primeiro porque quem já confia na gente fecha mais fácil. Pedi pra testar. Os dados não sustentam nenhuma das duas partes:
  - Todo deal fechado (6.711) é de uma das 85 contas que já compram. Em 14 meses nenhuma conta nova fechou. Os 1.425 sem conta estão todos abertos e têm o mesmo mix de produto dos abertos com conta. A leitura mais segura é furo de cadastro (a conta é preenchida no fechamento), não new logo.
  - Relação anterior não aumenta conversão: deal de produto que a conta já comprava ganha 61,5%, produto novo pra conta 67,9%. Parte disso é efeito da janela (972 deals fechados começaram antes de mar/2017, quando a gente ainda não enxerga compras anteriores), então o certo é dizer que os dados não mostram vantagem, nem pra um lado nem pro outro.
  - Ajustei a regra: deal sem conta não é "conta nova", é "identificar a conta". Depois de identificada, vai pro dono da conta. Se não for nenhuma das 85, aí sim vira new logo.
- Regra acordada: topo da lista é produto atrasado ou vencendo em até 30 dias com deal aberto pro mesmo produto na mesma conta. 280 pares, 518 dos 664 deals abertos com conta. Virou a coluna Priority ("Focus now") na planilha e entrou no SOP.
- Revisando o dataset, perguntei: como alguém sabe o produto e não sabe a conta? Pedi pra ver onde a falta de conta se concentra. Resultado: em lugar nenhum. Cerca de 68% dos deals abertos estão sem conta em todo recorte: Engaging 68%, Prospecting 67%, as três regiões entre 67% e 69%, os seis managers entre 66% e 70%, todos os produtos entre 65% e 70% (só o GTK 500, com 15 deals, fica em 53%), e todo mês de engajamento. Por vendedor vai de 61% a 90%, e os mais altos têm poucos deals.
- Leitura: taxa igual em todo lugar não é desleixo de um vendedor ou de um time, é processo. Ou o CRM não exige conta na oportunidade aberta e ela só é preenchida no fechamento, ou a exportação perde o campo. Não dá pra saber qual pelos dados, e isso vira recomendação pra RevOps: conta obrigatória na criação da oportunidade, relatório semanal de deals sem conta por vendedor, e a ação "identificar a conta" na ferramenta até isso estar resolvido.

## Etapa 3: ICP (23/10)

- Trouxe accounts.csv e sales_teams.csv pra planilha (corrigindo `technolgy` e `Philipines`) e montei a aba ICP em fórmula: por receita, funcionários, setor, ano de fundação, subsidiária e sede, com taxa de ganho, deals ganhos por conta, LTV por conta, ticket e participação no total. Os cortes de faixa ficam em células que eu posso mudar. Conferido contra o código.
- Taxa de ganho não muda com nenhum atributo da conta: fica entre 61% e 65% em todo corte, e nenhuma diferença passa de 2 erros-padrão. O ICP não prevê se o deal fecha.
- O que muda é o valor: conta com receita de 3 bilhões ou mais vale 169 mil de LTV, contra 84 mil abaixo de 500 milhões. O dobro, e quase todo pela frequência (65,8 ganhos por conta contra 39,6), com ticket um pouco maior. Funcionários conta a mesma história (correlação 0,95 com receita, então basta um). Software se destaca (154 mil, 64 ganhos por conta). Subsidiária e sede fora dos EUA não mudam nada.
- Região: testei 29 combinações setor x região e 12 receita x região. Nenhuma foge do acaso; as três regiões ganham entre 62,6% e 63,9%. Um ICP só, não um por região. Isso responde a Etapa 3 do SOP.
- Exceção que eu marquei: Condax tem 9 funcionários, 4,5 milhões de receita, fundada em 2017, e é Tier A com 105 ganhos. Ou é dado errado, ou é uma conta que foge da regra; fica sinalizada.
- Consequência pro score: encaixe no ICP entra como valor em jogo e prioridade da conta, não como chance de ganhar.
- Aprovei o ICP: um só, ICP 1 = receita de 3 bilhões ou mais ou setor software, ICP 2 = 1 a 3 bilhões, ICP 3 = abaixo de 1 bilhão. Regra de diferença real: 2 erros-padrão na taxa de ganho, 20% a mais de LTV com 5+ contas. Entrou no SOP e na planilha (cortes em células editáveis).
- Perguntei se algum manager ou vendedor performa melhor em algum ICP. Aba ICP x Team. Na taxa de ganho, não: 0 de 18 combinações manager x ICP e 1 de 90 vendedor x ICP passam de 2 erros-padrão, menos do que o acaso produziria (uns 4). O ranking de um vendedor no ICP 1 quase não prevê o ranking dele no ICP 3 (correlação 0,39).
- O que apareceu no lugar: o time do Dustin Brinkmann (Central, 5 vendedores) nunca teve um deal de GTXPro, em nenhum estágio, e 37% do pipeline dele é MG Special. Ele fatura 923 dólares por deal fechado em qualquer ICP, contra 1.400 a 1.840 dos outros. GTXPro é cerca de 35% da receita da empresa. Não é ICP, é acesso a produto ou treinamento no time. Vira recomendação.

## Etapa 4: replanejamento (23/10)

- No começo eu queria usar o MEDDPICC, porque é a metodologia que ajuda a avaliar um deal parado no pipeline e entender se ele é real ou só torcida. Mas o CRM não tem dado pra isso: seis das oito letras estão vazias. Deixei o MEDDPICC de lado, e o que falta vira recomendação de campos pra RevOps.
- Estacionei os 1.425 deals sem conta. Primeiro resolvo os 664 com conta, por vendedor e por manager; depois volto pros sem conta.

## Etapa 5: carteira por vendedor (23/10)

- Decisão minha: cada conta tem um dono, e cada vendedor vende o catálogo inteiro na sua carteira. O cliente não estranha a troca, porque de 8 a 29 vendedores já trabalhavam cada conta.
- Primeira tentativa do Claude: carteiras de valor igual. Quebrava a comissão (Darcel Schlecht caía 71%, Violet Mclelland subia 162%). Refiz o critério: a carteira de cada um tem o tamanho do que ele ganhou nos últimos 14 meses, sem GTK 500. Todo mundo ficou entre -4% e +7%. Em 73 das 85 contas o dono já tinha ganhado deal ali.
- Testei localização e setor como critério de distribuição. Nenhum dos dois prevê quem ganha: 8 combinações vendedor x setor fora do acaso, contra 8,9 esperadas só por acaso.
- GTK 500 (o produto mais caro, 26.768 dólares) fica com os 3 especialistas, em cima de uma carteira menor, porque só GTK daria a eles bem menos que a média. KPIs com linha de base e regra de decisão depois de 2 a 3 trimestres na aba GTK 500 KPIs.
- Cheguei a pensar em especializar o GTXPro também. Os dados derrubaram: 24 vendedores vendem GTXPro com a mesma taxa de ganho, e o time com mais volume (Melvin Marxen) tem a menor taxa. Fica só o treinamento do time do Dustin, vendendo junto com o time da Cara Losch por um trimestre.
- 5 vendedores nunca tiveram deal, um em cada time menos o do Dustin. Proposta de ramp de 3 meses: acompanhar, vender junto, carteira pequena de ICP 3.
- Os managers recebem a divisão como sugestão e podem reorganizar dentro do próprio time, com travas: carteira a no máximo 10% do que o vendedor ganhava, motivo escrito, uma semana, depois congela no trimestre. A planilha marca em vermelho o que sai da regra.

## Etapa 6: redistribuir os deals abertos agora (23/10)

- Não quis esperar os deals fecharem pra começar. Pedi pra reorganizar tudo já, sem machucar ninguém.
- O dado que destravou: nenhum deal ganho na história levou mais de 138 dias. 412 dos 501 deals em Engaging com conta já passaram disso.
- Regra final: os 82 deals vivos (até 138 dias) ficam com quem já está neles até ganhar ou perder. Os outros 549 vão hoje pro dono da conta; os passados do ciclo têm 30 dias pra voltar à vida ou ser fechados como perdidos. Daqui pra frente, só entra deal no CRM com conta, e só na conta que o vendedor é dono.
- Testei se mexer nos deals vivos premiaria performance. Não: quem perderia e quem ganharia deals têm a mesma taxa de ganho (63,7% e 63,5%). Deixar os vivos parados é o que protege a comissão.

## Etapa 7: prioridade do dia (23/10)

- Ordem travada: (1) deal vivo em produto vencido ou vencendo em 30 dias, 75 deals; (2) os outros vivos, 14; (3) deals mais antigos em produto pouco vencido ou vencendo, 448, com os muito vencidos no fim como recuperação; (4) o resto, 127. Dentro de cada passo, tier de ICP e depois valor.
- Primeira passada de segunda a sexta (cerca de 18 deals por vendedor). A lista é refeita todo dia.

## Etapa 8: revisão independente antes de construir (23/10)

- Antes de abrir o app, pedi duas revisões do que tinha até aqui, de dois modelos diferentes (Claude Fable e GPT), com a instrução explícita de discordar. Nota: 7 e 8 de 10. As duas convergiram nos mesmos pontos: o teto de 138 dias é igual pros ganhos e pros perdidos, então é propriedade do arquivo e não lei de vendas; a lista tem que funcionar mesmo se a RevOps não aprovar a redistribuição de carteiras; os 1.425 deals sem conta não podem ficar estacionados; o backtest vem antes da interface; e o app não é "a parte fácil".
- O que eu aceitei: nota sobre o dataset; reescrever a dor número um (deal que morre, morre em duas semanas; o desperdício está nos deals passados de 138 dias, não nos vivos mais velhos); trocar "vencido" por "fora da janela estimada de recompra" e "parado" por "aberto há X dias", porque o CRM não tem data de último contato; "ninguém perde comissão" vira meta com checagem de carga no piloto; os 209 deals vivos sem conta seguem a mesma regra dos 82 (ficam com quem está neles); identificar a conta é tarefa de todo dia, mas depois dos deals vivos.
- O que eu não aceitei: tirar o login por e-mail do app (quero mostrar que construo, não só que escrevo) e abandonar a proposta de carteiras. A redistribuição fica como aposta explícita, com a ferramenta rodando nos dois modos (como está hoje e com carteiras) pra RevOps comparar.
- Onde a IA errou: o SOP trazia 448 e 127 nos passos 3 e 4; a planilha, montada em fórmula, deu 443 e 132 (75 + 443 = 518, que é o número de deals em pares na hora de recomprar que o documento já citava). Corrigi o SOP pela planilha.

## Etapa 9: o motor na planilha (23/10)

- Decisão minha: a planilha é o motor. Ela encapsula a lógica; o app, depois, só lê dela. Cinco abas novas, tudo em fórmula: Hoje (o relógio: uma célula com os dias passados desde 31/12/2017, modo de dono, ordem dentro do passo, todos os cortes editáveis), Lista do Dia (664 deals com conta, passo, ordem por vendedor, o porquê e a próxima ação em português), Fila Sem Conta (1.425 deals, prazo de 10 dias úteis, status preenchido pelo vendedor, escalada pro manager), Visão Manager (carga por vendedor nos dois modos, passos, fila, alertas; e por manager) e Backtest (data de snapshot editável).
- O relógio é simulado, porque o "hoje" dos dados é 31/12/2017. Testei com 20 dias: os deals vivos caíram de 89 pra 59, o passo 3 cresceu com produtos entrando na janela, e a fila inteira passou pra "escalar pro manager" porque o prazo venceu. É isso que o job diário vai fazer, um dia por vez.
- Backtest em 30/09/2017, 1.401 deals em Engaging com conta abertos naquele dia. Dos 169 passados de 138 dias, nenhum fechou depois, nem ganho nem perdido. Entre os vivos, estar na hora de recomprar não mudou a taxa de ganho (60% nos dois passos): a janela diz o que oferecer, não quem fecha. Nos 18 primeiros de cada vendedor, a ordem do SOP ganhou 235 deals e US$ 648 mil contra 215 e US$ 481 mil do acaso. Só preço de tabela, o baseline, dá US$ 905 mil com menos ganhos (221). Inverter a ordem dentro do passo pra valor antes de ICP dá 239 deals e US$ 815 mil. "Mais novo primeiro" ganha mais deals (298) e menos dinheiro, em parte porque neste arquivo um deal velho no snapshot não tem vida pela frente.
- O que o backtest me ensinou e eu não esperava: como a taxa de ganho é igual em toda conta, o tier de ICP diz em qual conta investir relacionamento, não qual deal ligar primeiro. A ordem dentro do passo está numa chave na aba Hoje; a decisão de inverter ou não é minha e fica registrada aqui quando eu tomar.

## Etapa 10: o app (23/10, noite)

- Decisões que travei antes de começar: Apps Script como API (mora na planilha, roda o job diário, nada de credencial no repositório); os KPIs e as "contas que você é dono" seguem o modo de dono da aba Hoje; "feito" manda o deal pro fim da lista de hoje e ele volta amanhã pelas regras; e inverti a ordem dentro do passo pra valor antes de ICP, por causa do backtest.
- A planilha ganhou duas abas: `KPIs Vendedor` (os oito números do topo do app, por vendedor, com e-mail e papel) e `Atividades` (uma linha por ação do app). A `Lista do Dia` passou a ler `Atividades`: deal marcado ganho ou perdido sai da lista, deal feito hoje afunda, e "último contato" passa a existir a partir de agora. Testei com duas linhas de atividade: a lista caiu de 664 pra 663 e o deal tocado apareceu como feito hoje.
- Onde a IA errou aqui: três tentativas até achar que intervalos abertos (`$J$2:$J`) sobre resultados de `MAP` devolviam vazio na lista, enquanto o lookup escalar funcionava. Intervalo fechado (`$J$2:$J$2000`) resolveu. E as médias de produtos por conta vieram zeradas porque `COUNTIF` com critério em vetor não vetoriza dentro de `SUMPRODUCT`; a saída foi uma área auxiliar com os números por conta e `SUMIF` por cima.
- O Apps Script expõe a planilha como JSON (`config`, `users`, `rep`, `manager`, `snapshot`) e recebe `activity`, `advance`, `reset` e `notify`. O job diário anda o relógio e manda a mensagem de cada vendedor por e-mail (Slack com um webhook). Código em `solution/apps-script`.
- O app: Next.js 16 no Vercel, com os tokens do site da G4 (navy, dourado, Manrope, Libre Baskerville itálico no destaque). Login por e-mail com senha única da demo, `Meu dia` (KPIs + lista com porquê, próxima ação e botões Feito / Ganho / Perdido), `Fila sem conta`, `Meu time` (manager) e `Simulação` (avançar um dia, mandar as mensagens, zerar). Sem a planilha conectada ele roda de um snapshot exportado dela, pra ninguém ficar travado na avaliação; o que o vendedor marca fica no navegador e a lista reordena do mesmo jeito.
- Parede que eu mesmo tive que destravar: o login do Google na linha de comando (pra publicar o Apps Script) tinha expirado, e o Slack precisa de um webhook meu. O app foi no ar primeiro em modo snapshot; a conexão com a planilha entra assim que o script é publicado.
- No ar em https://g4-lead-scorer-seven.vercel.app (modo snapshot até o Apps Script ser publicado). Screenshots do fluxo real (login, meu dia, feito reordenando, fila, manager, simulação) em `process-log/screenshots`.

## Etapa 11: planilha conectada (23/10, fim da noite)

- O login do Google na linha de comando pediu três voltas: a primeira veio sem os escopos de Apps Script (o seletor nem oferecia), a segunda com os escopos certos mas com um token antigo em cache, e aí faltava ativar a Apps Script API no projeto do Google Cloud e nas configurações da minha conta. Cada parede foi uma mensagem de erro lida, não adivinhada.
- Com isso, o script foi criado vinculado à planilha, o código subiu e virou app da web pela própria API. O app da web respondia "Acesso negado" até eu autorizar o script uma vez no editor (rodei `installTrigger`, que também agendou o job das 9h).
- Onde a IA errou aqui: `appendRow` escrevia a atividade na linha 2.001, porque as fórmulas auxiliares de `Atividades` ocupam a coluna até o fim; e um `append` de teste anterior tinha inserido duas linhas e empurrado as fórmulas antigas pra linha 4, o que dava `#REF!` nas novas. Corrigido: o script escreve na primeira linha vazia da coluna A, e as fórmulas duplicadas saíram. Versão 2 do script, mesma URL.
- Prova de ponta a ponta: entrei no app em produção como Kary Hendrixson, marquei o deal da Rangreen (GTX Plus Pro, US$ 5.482) como ganho. A linha apareceu em `Atividades` com o dia da planilha, o deal saiu da lista (37 virou 36) e o passo 1 reordenou. Screenshot `app-07`.
- Mais uma da planilha: `SUMIFS` com critério em vetor dentro de `ARRAYFORMULA` não vetoriza (o `COUNTIFS` vetoriza). O "Vendido" dos KPIs não somava o ganho registrado no app até trocar por `MAP` com `LAMBDA`, uma linha por vendedor.
- Uma coisa que a prova mostrou e eu ajustei: a lista só reordenava depois de recarregar a página, porque a planilha leva um ou dois segundos pra recalcular. O app agora recarrega sozinho dois segundos e meio depois de cada ação.

## Etapa 12: tirei o login (23/10, última decisão do dia)

- Na revisão eu tinha insistido no login por e-mail pra mostrar que construo. Olhando o resultado, voltei atrás: os e-mails dos vendedores não existem no dataset, então o login seria de mentira, e é exatamente o tipo de coisa que o time da G4 iria apontar. Tirei. A primeira tela agora pergunta quem está olhando (vendedor ou manager, agrupados por time) e mostra a lista daquela pessoa. O filtro por vendedor, manager e região, que é o que o brief pede, continua.
- Detalhe pego na hora de testar a tela nova: a API devolvia os seis managers duas vezes (a leitura da aba `KPIs Vendedor` já incluía as linhas deles e o código somava de novo). Versão 3 do script. E a lista de vendedores passou a ficar um minuto em cache no app, porque cada página fazia duas idas à planilha.
- O que entra com a aprovação da RevOps, e está no README: login da empresa (SSO) e permissão por papel, cada vendedor vê só a sua lista, cada manager só o time. O app já separa os dados por pessoa; falta só a porta.

## Etapa 13: o porquê de verdade (23/10, noite)

- Olhando um card real (Treequote, GTX Plus Pro, "entra na janela em 23 dias", "deal aberto há 92 dias") eu não consegui responder qual dos dois mandava. Pedi os dados do deal: aberto em 30/09; desde então a conta comprou GTX Plus Pro cinco vezes, de três vendedores diferentes, a última ontem. O deal não está esfriando: foi atropelado. No pipeline inteiro, 470 dos 501 deals abertos em Engaging com conta têm esse padrão (71 dos 89 vivos). Esse é o sinal de "deal que não vai fechar" que o brief pede e que a idade sozinha não mostrava.
- Mudanças que pedi e entraram: cada card mostra por que a conta é ICP 1, 2 ou 3 (a receita ou o setor contra a regra), o ritmo de recompra daquele produto naquela conta (intervalo médio, quantas compras, última compra), a idade contra o ciclo normal e o limite, e o aviso "a conta comprou X vezes depois deste deal abrir, a última com fulano", com a ação virando "confirmar se ainda é real". Os deals sem conta entram na lista do vendedor, cinco por dia depois dos vivos, com um campo pra registrar a conta; identificada, ela entra na planilha e o deal segue as regras.
- Testei de ponta a ponta: registrei a conta de um deal sem conta da Vicki (DY8DMZZ9, Treequote) no app em produção. A fila marcou Identificada, a planilha reconheceu a conta e o deal entrou na lista dela no passo 1. Detalhe que apareceu no teste: registrar a conta contava como "contato de hoje" e mandava o deal pro fim da lista; identificar a conta não é falar com o cliente, então essa ação ficou de fora do último contato.
- O que ainda não mudei, de propósito: a ordem. Hoje o passo 1 trata "fora da janela" e "entrando em 23 dias" igual, e um deal atropelado continua no lugar que o valor dá a ele. Duas opções em aberto: ordenar dentro do passo pela urgência da recompra (dias até a janela) antes do valor, e mandar o deal atropelado pro fim do passo com a ação de confirmar. Decido depois de ver a lista com os avisos por um dia.
- Depois de ler o card eu quis a história inteira, não três frases: o porquê agora diz quantas vezes a conta comprou aquele produto no período, de quem (nomes), o ritmo e quantos vendedores diferentes venderam o mesmo produto pra mesma conta, e fecha com uma leitura em uma frase ("o pedido deste deal provavelmente já foi atendido por um colega; o registro ficou pra trás"). A ação começa pela confirmação com o cliente, citando quem fechou e há quantos dias.
- E o logo: o emblema da G4 de verdade (SVG do site) no lugar do círculo com "G4".

## Etapa 14: o deal atropelado não é prioridade (23/10, noite)

- Fechei a decisão que tinha deixado aberta: um deal cujo produto a conta já comprou de outro vendedor depois de ele abrir não vai pra frente da fila. O cliente já comprou. Esse deal tem prioridade de perdido, não de venda. Ele sai dos passos 1 a 4 e vai pro fim da lista, num bloco Encerrar, com a ação de fechar como perdido ou juntar ao deal do colega.
- A consequência apareceu nos números antes de eu mexer: dos 664 deals abertos com conta, 470 são atropelados. Sobram 16 no passo 1, 2 no passo 2, 133 no passo 3 e 43 no passo 4. O pipeline real tem 194 deals; o resto é limpeza. A lista tem que mostrar isso, não esconder.
- E a parte que vira o relógio que eu descrevi desde o começo: das 383 combinações conta e produto na hora de recomprar, 263 não têm nenhum deal limpo aberto. A oportunidade existe e não tem dono no CRM. Virou uma aba e um bloco no Meu dia, "Recompra sem deal: abrir e ligar", só no modo Carteiras, porque precisa de dono.
- Também decidi a ordem dentro do passo: urgência da recompra primeiro, depois valor, depois ICP. "Fora da janela" e "entrando em 23 dias" não pesam mais igual.
- O que o backtest disse, e eu registrei mesmo não sendo a favor: neste arquivo os atropelados ainda fecharam quase como os limpos (58% contra 63% no snapshot de 30/09), porque o dado gerado não sabe que o pedido já foi atendido. A nova ordem ganha mais deals nos 18 primeiros (264 contra 239) e menos receita (US$ 624 mil contra 815 mil). A regra é de operação comercial, não do backtest, e está escrita assim no SOP e no documento.
- Fechei também o bônus do brief: uma visão RevOps com todos os times e filtro por manager e região. Com login da empresa, só RevOps e diretoria veriam essa página.

## Etapa 15: os cards em português de vendedor (23/10, noite)

- Li os cards do app como se fosse um vendedor e metade das legendas era pra mim, não pra ele ("quem segura cada deal hoje", "gasto por conta"). Reescrevi todos em palavras simples: "deals com conta que o seu time está segurando agora, antes de redistribuir"; "quanto cada conta sua comprou em 14 meses". E pedi o que faltava pra um manager de verdade: a taxa de fechamento do time, a de cada vendedor e quantos pontos cada um está acima ou abaixo do time, na tabela do manager, na visão RevOps e no topo do Meu dia de cada vendedor (com a posição dele no time).


## Etapa 16: terceira revisão, com o app no ar (23/10, noite)

- Pedi de novo duas revisões independentes (Claude Fable e GPT), agora do produto pronto: repositório, planilha, app no ar, backtest. Nota 8,5 e um "ainda não é 10". Os dois convergiram num ponto que eu tinha decidido errado poucas horas antes.
- **O que eu aceitei e mudei.** "A conta comprou o mesmo produto de outro vendedor depois de o deal abrir" não prova que é o mesmo pedido: pode ser outro departamento, outra quantidade, compra recorrente. E o backtest não sustentava a inferência: esses deals fecharam ganhos em 58% contra 62% dos limpos. Eu tinha mandado 470 de 664 deals pra um bloco "Encerrar". Virou "Confirmar": a ação é perguntar pra conta se é o mesmo pedido ou demanda separada. Mesmo pedido: juntar ou fechar como perdido. Demanda separada: um botão no app, e o deal volta pros passos. Os dados dizem onde confirmar; a conta diz o que é.
- **Onde a IA errou aqui.** A contagem de "outro vendedor" incluía as vendas do próprio vendedor do deal (470 virou 464, e 71 dos 89 vivos virou 69). O ranking do backtest tinha empates, então o "top 18 por vendedor" colocava 545 deals numa ordem e 537 noutra; desempate pela linha, agora 537 em todas. O benchmark de acaso aplicava a média geral a todo mundo; virou acaso pareado por vendedor (mesmo N de cada um, com a taxa e a receita média dele), e a comparação ficou mais dura: o acaso pareado dá US$ 650 mil, não 481 mil, e a ordem em uso ganha mais deals que ele (270 contra 215) mas menos receita (624 mil). Escrevi isso na aba e no README como leitura exploratória, com os cortes de 57 e 138 dias vindo do arquivo inteiro.
- **Buracos de implementação que o revisor achou e eu fechei.** Feito só reordenava no modo snapshot; a chave de ordenação da planilha agora afunda o deal feito, então o modo conectado faz igual. O bloco Recompra sem deal não tinha Feito, e mandava abrir deal onde já existia um deal a confirmar pro mesmo par (a Vicki via "encerrar o deal da Green-Plus" e "abrir um deal na Green-Plus" pro mesmo produto); agora só entra par sem nenhum deal aberto, e onde há um a confirmar a ação é confirmar esse. Os controles da demo (avançar o dia, zerar, mandar mensagens) mudavam a planilha de todo mundo com um clique; agora pedem a senha de administração, que está no README, e o job diário das 9h fica desligado durante a avaliação pra que o "hoje" bata com o que está escrito.
- **Reprodutibilidade.** Toda fórmula e toda configuração da planilha foram exportadas pro repositório (`solution/sheet`), aba por aba, célula a célula. Quem não tiver acesso à planilha consegue reconstruir o motor a partir dos CSVs.
- **O que eu corrigi na minha própria narrativa.** Ela dizia "um commit por etapa", e o build foi commitado em cinco blocos no fim do dia. Corrigi o texto, não o histórico.
- Script v9, planilha e app atualizados, docs e SOP sincronizados.

---

## Onde a IA errou e como corrigi

- A fórmula de top 3 produtos voltava a linha de cabeçalho da QUERY no lugar do produto nº 1. O Claude achou o erro só quando montou a versão dos perdidos e corrigiu nas duas abas.
- O Claude descreveu o ICP pelo valor da conta. Corrigi: ICP é quem é o cliente (desafios, comportamento, perfil). O valor é a evidência de qual perfil compra melhor, não a definição.
- O Claude disse que os especialistas de GTK ganham 60%. Era a taxa de todos os deals de GTK; a dos especialistas é 65,2%. Pegou na hora de montar a aba de KPIs.
- Na conversa, misturei GTK 500 (o mais caro, 3 vendedores) com GTXPro (o que mais fatura, 24 vendedores). O Claude separou os dois com a tabela de preços antes de eu decidir em cima do produto errado.
- A contagem de "a conta comprou depois de abrir" incluía o próprio vendedor do deal; o ranking do backtest tinha empates; o acaso não era pareado por vendedor. Os três saíram da terceira revisão (etapa 16).

## O que eu adicionei que a IA sozinha não faria

- A leitura de operação comercial: carteira fixa por vendedor justificada por organização e cadência, assumindo abertamente que os dados não mostram ganho de conversão.
- "Ninguém pode perder comissão" como regra de desenho. Foi isso que mudou o critério das carteiras e a regra dos deals vivos.
- Reorganizar agora em vez de esperar o pipeline zerar, e travar o CRM pra só aceitar deal em conta própria.
- Dar aos managers a palavra final dentro do time, com travas, em vez de impor a divisão.
- Voltar atrás numa regra minha quando a revisão e o backtest apontaram o mesmo furo: Encerrar virou Confirmar, porque dado nenhum sabe se duas compras são o mesmo pedido. A conta sabe.
