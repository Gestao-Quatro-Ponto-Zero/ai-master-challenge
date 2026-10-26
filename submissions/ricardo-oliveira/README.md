# Submissão — Ricardo Oliveira — Challenge 003

## Sobre mim

- **Nome:** Ricardo Trevizan Rodrigues de Oliveira
- **LinkedIn:** https://www.linkedin.com/in/ricatroliveira/
- **Challenge escolhido:** 003, Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma lista do dia por vendedor que sai de 8.800 oportunidades e diz, deal a deal, o que fazer primeiro e por quê. A lógica mora numa planilha (toda em fórmula, com um relógio que anda um dia por vez) e um app web lê essa planilha, mostra os KPIs e a lista, e grava de volta o que o vendedor fez (feito, ganho, perdido, demanda separada confirmada). O que os dados mostraram: nenhum atributo da conta muda a chance de fechar (61% a 65% em todo corte), deal perdido morre em duas semanas, nenhum deal fecha depois de 138 dias, 68% dos deals abertos estão sem conta no CRM, e em 464 dos 501 deals abertos com conta outro vendedor fechou o mesmo produto na mesma conta depois de o deal abrir. A prioridade usa idade do deal, hora de recompra de cada produto em cada conta, valor e ICP, nessa ordem; os deals atropelados vão pra um bloco de confirmação, não de encerramento, porque os dados não dizem se é o mesmo pedido ou demanda separada. A recomendação principal pra RevOps vai além da lista: cada conta com um dono, carteiras do tamanho do que cada vendedor já ganhou (ninguém perde comissão) e conta obrigatória no CRM.

---

## Solução

### Abordagem

1. **Entender antes de automatizar.** Li o README, o CONTRIBUTING e o guia direto do repositório. O pedido real da Head de RevOps não é "prever quem fecha", é "o vendedor abre na segunda e sabe onde focar".
2. **Método antes de código.** ICP (quem compra melhor), depois MEDDPICC (o que sabemos de cada deal), depois momento (vivo ou morto), e só então prioridade. O resumo executável está em [`docs/logica.md`](./docs/logica.md); o SOP com cada decisão, em [`docs/sop-lead-scorer.md`](./docs/sop-lead-scorer.md).
3. **Dados primeiro, hipótese depois.** Cada regra só entrou depois de provar nos 6.711 deals fechados que muda alguma coisa. O MEDDPICC saiu porque o CRM não tem dado pra seis das oito letras. O ICP ficou como valor em jogo, não como chance de ganhar, porque a taxa de ganho é igual em todo corte.
4. **A planilha é o motor.** Tudo em fórmula, em abas que qualquer pessoa abre e audita: `Hoje` (relógio e regras), `Lista do Dia`, `Fila Sem Conta`, `Recompra sem deal`, `Visão Manager`, `KPIs Vendedor`, `Backtest`, `Atividades`. Toda fórmula e toda configuração estão exportadas no repositório, em [`solution/sheet`](./solution/sheet), pra quem não tiver acesso à planilha.
5. **O app é a janela.** Next.js lendo a planilha por uma API em Apps Script. Escolha do vendedor (sem login na demo), lista do dia com porquê e próxima ação, os deals sem conta do dia com o campo pra identificar a conta, botões Feito / Ganho / Perdido que gravam na planilha, o bloco Recompra sem deal (com Feito), o bloco Confirmar, visão do manager, visão RevOps com filtro por manager e região, simulação de "amanhã" protegida por senha.
6. **Validar antes de mostrar.** Backtest com snapshot editável: volta no tempo, monta a lista com o que se sabia naquele dia e confere o que aconteceu. Leitura exploratória, declarada como tal na própria aba.

### Resultados / Findings

- **App:** https://g4-lead-scorer-seven.vercel.app (sem login: escolha o vendedor ou o manager na primeira tela). Código em [`solution/app`](./solution/app). Setup em [`docs/setup.md`](./docs/setup.md).
- **Planilha (motor):** aba por aba em [`docs/logica.md`](./docs/logica.md). Link de leitura: https://docs.google.com/spreadsheets/d/1IjZSZTpzergXYVKPxf-IUJwsss5xD9P_Nch5KX3IMDc/edit. Fórmulas e configuração exportadas em [`solution/sheet`](./solution/sheet).
- **Lista do dia (31/12/2017, o "hoje" dos dados):** 664 deals com conta. Só deals limpos entram nos passos: passo 1 (vivo e na hora de recomprar) 17, passo 2 (outros vivos) 3, passo 3 (antigos, conta na hora de recomprar) 137, passo 4 (resto) 43. Os 464 deals em que outro vendedor fechou o mesmo produto na conta depois de o deal abrir vão pro bloco Confirmar, no fim. Dentro de cada passo: urgência da recompra, depois valor, depois ICP. E um bloco que não depende de deal: Recompra sem deal, 103 pares conta e produto na hora de recomprar sem nenhum deal aberto no CRM, pra abrir e ligar (de 383 pares na hora de recomprar; os outros 280 já têm deal aberto, limpo ou a confirmar).
- **Fila sem conta:** 1.425 deals (68% dos abertos), taxa igual em todo time, região e produto. É processo do CRM, não desleixo de alguém. Viram fila com prazo e escalada, e cinco por dia entram na lista do vendedor depois dos vivos, com um campo pra registrar a conta; identificada, o deal entra na lista pelas regras no dia seguinte.
- **O sinal mais forte do dataset, e o que ele não prova:** em 464 dos 501 deals abertos em Engaging com conta (69 dos 89 vivos), outro vendedor fechou o mesmo produto na mesma conta depois de o deal abrir. Com 8 a 29 vendedores vendendo na mesma conta, é o caso pra conta ter dono. Mas uma compra posterior não prova que é o mesmo pedido: pode ser outro departamento, outra quantidade, compra recorrente. E o backtest confirma a dúvida: no snapshot de 30/09/2017, esses deals fecharam ganhos em 58% dos casos, contra 62% dos limpos. O sinal não separa quem fecha. **Decisão:** esses deals saem dos passos 1 a 4 e vão pro bloco Confirmar, com a ação "confirmar com a conta se é o mesmo pedido ou demanda separada". Mesmo pedido: juntar ou fechar como perdido. Demanda separada: um clique no app e o deal volta pros passos. Encerrar sem perguntar seria tratar uma hipótese como fato.
- **Backtest (30/09/2017, 1.401 deals em Engaging com conta abertos naquele dia):** dos 169 já passados de 138 dias, nenhum fechou depois, nem ganho nem perdido. Entre os vivos, estar na hora de recomprar não muda a taxa de ganho (60% nos passos 1 e 2). Nos 18 primeiros de cada vendedor (537 deals, top N exato, empates desfeitos), a ordem do SOP com valor antes de ICP ganhou 239 deals e US$ 815 mil; o acaso pareado por vendedor (mesmo N de cada um, com a taxa e a receita média dele) daria 215 deals e US$ 650 mil. Só preço de tabela (o baseline "ordenar por valor") dá mais dinheiro (US$ 905 mil) com menos ganhos (221). "Mais novo primeiro" ganha mais deals (293) com US$ 688 mil, favorecido porque neste arquivo um deal velho no snapshot não tem vida pela frente. A ordem em uso (urgência antes do valor, atropelados no fim) ganha mais deals (270) e menos receita (US$ 624 mil, abaixo do acaso pareado): a regra é de operação comercial, e o arquivo não a premia. Tudo isso é exploratório: um snapshot, dado gerado, cortes de 57 e 138 dias calculados no arquivo inteiro (inclusive no futuro do snapshot), e nenhuma prova de que seguir a ordem causa mais vendas.
- **O que eu mudei por causa do backtest:** a ordem dentro do passo era ICP antes de valor. O backtest mostrou 26% mais receita com a mesma taxa de ganho invertendo. Inverti. E a regra "Encerrar" virou "Confirmar" depois que uma revisão independente apontou que a compra posterior não prova o mesmo pedido e o backtest não sustentava a inferência.
- **Screenshots:** [`process-log/screenshots`](./process-log/screenshots).

### Recomendações

1. **Rodar a lista do dia como está, já na segunda**, no modo "como está hoje" (cada vendedor vê o que já tem). Não depende de nenhuma mudança de organização.
2. **Conta obrigatória na criação do deal** e relatório semanal de deals sem conta por vendedor até o furo sumir. Enquanto isso, a fila sem conta no app.
3. **Cada conta com um dono.** Hoje de 8 a 29 vendedores ganham deal na mesma conta, e em 464 dos 501 deals abertos com conta um colega fechou o mesmo produto depois. Proposta de carteiras do tamanho do que cada vendedor ganhou nos últimos 14 meses (-4% a +7%), deals vivos ficam com quem está neles, o resto vai pro dono. Os managers recebem a divisão como sugestão e reorganizam dentro do time numa faixa de 10%. Piloto: time da Celia Rouche. O app roda nos dois modos pra RevOps comparar.
4. **GTK 500 com três especialistas** (já é assim na prática: 37 dos 40 deals), como suporte ao dono da conta, com KPIs e decisão em 2 a 3 trimestres.
5. **Descobrir por que o time do Dustin Brinkmann nunca vendeu GTXPro** (35% da receita): acesso ao produto ou treinamento.
6. **Campos de MEDDPICC e de desafio do cliente no CRM**, e um campo "pedido" ou "demanda" que diga se duas compras do mesmo produto na mesma conta são a mesma coisa. Sem isso, o bloco Confirmar depende de uma ligação.
7. **Login e permissão por papel** quando a ferramenta for aprovada: SSO da empresa, cada vendedor vê só a sua lista, cada manager só o time. A demo escolhe o vendedor na primeira tela porque os e-mails do dataset não existem.

### Limitações

- **O dataset é gerado.** O deal ganho mais longo e o perdido mais longo param nos mesmos 138 dias, e a taxa de ganho é igual em todo corte. Os cortes (57 e 138 dias) são percentis deste arquivo, em células editáveis. Num CRM real seriam recalculados todo mês, e provavelmente haveria sinal de probabilidade de fechamento que aqui não existe.
- **"Outro vendedor fechou depois" não prova o mesmo pedido.** Por isso é um bloco de confirmação, e por isso os dados não o premiam: no backtest esses deals fecharam ganhos em 58% contra 62% dos limpos. É regra de operação comercial, não achado estatístico.
- **O backtest é exploratório.** Um snapshot só, sem relação de causa, e os cortes de 57 e 138 dias vêm do arquivo inteiro, então o teste conhece um pouco do futuro. Serve pra escolher entre ordens, não pra prometer resultado.
- **Não existe data de último contato.** A lista diz "aberto há X dias", nunca "parado". A partir do app, cada ação vira uma linha em `Atividades`, e aí passa a existir.
- **"Hora de recomprar" é estimativa**, não contrato: última compra mais o intervalo médio daquela conta naquele produto. A lista mostra em quantas compras cada estimativa se baseia, e quando o atraso passa do dobro do ritmo o card avisa que a conta pode ter parado de comprar.
- **"Ninguém perde comissão" é meta, não resultado demonstrado.** A carteira preserva o potencial histórico; o efeito real depende do que cada conta comprar daqui pra frente, e é checado no piloto junto com a carga de trabalho.
- **Prospecting não tem data**, então fica fora do backtest e entra na lista ordenado pelo valor do produto até o vendedor engajar e registrar a data.
- **A redistribuição de carteiras precisa de aprovação da RevOps.** Por isso o app funciona sem ela.
- **O relógio é simulado.** O "hoje" dos dados é 31/12/2017. O job diário das 9h anda um dia por vez em cima de um CRM congelado; durante a avaliação ele fica desligado, pra que os números do app batam com este README. Os controles da demo (avançar o dia, zerar, ligar o job) mudam a planilha pra todo mundo e pedem a senha de administração `g4-revops`.
- **Sem login na demo.** Os e-mails dos vendedores não existem no dataset, então um login seria de mentira. A primeira tela escolhe quem está olhando. Com a aprovação da RevOps, entra o login da empresa (SSO) e a permissão por papel.
- **Mensagens diárias por e-mail** (Apps Script). Slack entra com um webhook, sem mudar o resto.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Quem decidiu o quê

**O que eu levei antes de abrir a IA.** O ângulo (prioridade não é probabilidade) e uma regra: nenhuma variável entra no score sem provar, nos deals fechados, que mexe na taxa de ganho.

**Hipóteses minhas que eu mandei testar, e o que os dados disseram:**
- O jogo é upsell e cross-sell na conta. Não: 88% dos ganhos são recompra de produto que a conta já tinha.
- Deal sem conta é new logo. Não: nenhuma conta nova fechou em 14 meses, é furo de cadastro. A regra virou "identificar a conta".
- Especializar o GTXPro como o GTK 500. Não: 24 vendedores vendem GTXPro com a mesma taxa de ganho. Ficou só o GTK.

**Onde eu corrigi ou travei a IA:** ela descreveu o ICP pelo valor da conta, e eu reposicionei (ICP é quem é o cliente, o valor é a evidência). A minha regra de comissão derrubou a primeira divisão de carteiras dela, que dava o mesmo valor pra todo mundo (Darcel cairia 71%); o critério virou o histórico de cada vendedor.

**Onde eu recusei a IA:** a revisão pediu pra abandonar as carteiras. Mantive como aposta explícita, com o app rodando nos dois modos pra RevOps comparar.

**Onde a IA me corrigiu e eu aceitei:** eu misturei GTK 500 com GTXPro numa decisão; o teto de 138 dias é do arquivo, não lei de vendas; "Encerrar" virou "Confirmar"; e o backtest inverteu a minha ordem de ICP antes de valor. Trechos da conversa em [`process-log/screenshots`](./process-log/screenshots) (arquivos `ia-*`).

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Opus e Fable), dentro do meu sistema operacional pessoal (vault Obsidian com contexto e regras) | Leitura do repositório e dos dados, análise em código, construção da planilha em fórmula, SOP, backtest, app, Apps Script |
| GPT / Codex | Duas revisões independentes, antes do app e depois dele, com instrução explícita de discordar |
| Google Sheets | O motor: toda a lógica em fórmula, auditável célula a célula |
| Google Apps Script | API da planilha, job diário das 9h, mensagens |
| Next.js + Vercel | O app que o vendedor abre |

### Workflow

1. Li o README, o CONTRIBUTING, o guia e o template direto do repositório (não colei o brief num chat). Defini o ângulo: prioridade não é probabilidade.
2. Fork, clone, branch. Pegadinha do `.gitignore` que ignora `submissions/` (resolvida com `git add -f`, sem tocar em arquivo fora da minha pasta).
3. Método antes de código: SOP em português com ICP, MEDDPICC, momento, prioridade. Primeira leitura dos dados pelo Claude: 68% dos abertos sem conta, região é do vendedor, nada de MEDDPICC.
4. Planilha, aba por aba, sempre em fórmula, conferida contra o código: ganhos e perdidos, contas e vendedores, recompra por conta e produto, ICP, ICP por time, carteiras, redistribuição, prioridade.
5. Cada hipótese minha testada antes de virar regra: GTK 500 especialistas (sim, já é assim), AE por conta (organização, não conversão), deals sem conta como new logo (não: furo de cadastro), GTXPro especializado (não).
6. Duas revisões independentes (Claude Fable e GPT) antes de construir. Aceitei a maioria, recusei uma (abandonar as carteiras) e voltei atrás noutra: tinha insistido no login por e-mail e tirei depois, porque os e-mails do dataset não existem.
7. Motor na planilha com relógio simulado, lista do dia, fila sem conta, visão do manager, KPIs, backtest, atividades. Clock testado com 20 dias.
8. Apps Script (API + job diário), app em Next.js, deploy. Screenshots do fluxo real.
9. Terceira rodada de revisão, com o app no ar, pelos dois modelos. Dela saíram: o bloco Encerrar virou Confirmar (a compra posterior não prova o mesmo pedido), a contagem de "outro vendedor" passou a excluir o próprio vendedor do deal, o backtest ganhou top N exato e acaso pareado por vendedor, Feito passou a reordenar também no modo conectado, o bloco Recompra sem deal ganhou Feito e parou de mandar abrir deal onde já existe um a confirmar, os controles da demo ganharam senha, e as fórmulas da planilha foram exportadas pro repositório.

A narrativa completa, etapa por etapa, está em [`process-log/00-narrativa.md`](./process-log/00-narrativa.md). A conversa inteira da tarde de 23/10 (das carteiras ao SOP) está em [`process-log/chat-exports`](./process-log/chat-exports).

### Onde a IA errou e como corrigi

- A fórmula de top 3 produtos devolvia o cabeçalho da QUERY no lugar do produto nº 1. Só apareceu na versão dos perdidos.
- A IA descreveu o ICP pelo valor da conta. ICP é quem é o cliente (desafios, comportamento, perfil); o valor é a evidência de qual perfil compra melhor, não a definição.
- "Os especialistas de GTK ganham 60%" era a taxa de todos os deals de GTK; a dos especialistas é 65,2%.
- Eu mesmo misturei GTK 500 com GTXPro numa decisão; a IA separou os dois com a tabela de preços antes de eu decidir em cima do produto errado.
- O SOP trazia 448 e 127 nos passos 3 e 4; a planilha em fórmula deu 443 e 132. Corrigi o SOP pela planilha.
- Fórmulas com intervalo aberto (`$J$2:$J`) sobre resultados de `MAP` devolviam vazio na `Lista do Dia`; o lookup escalar funcionava. Intervalo fechado resolveu. A IA demorou três tentativas pra isolar.
- A contagem de "a conta comprou depois de abrir" incluía as vendas do próprio vendedor do deal. Um revisor pegou; a fórmula passou a excluir o vendedor do deal (470 virou 464).
- O ranking do backtest tinha empates: o "top 18 por vendedor" colocava 545 deals numa ordem e 537 noutra. Desempate pela linha; agora são 537 em todas.
- O benchmark de "acaso" aplicava a média geral ao total de deals. Virou acaso pareado por vendedor (mesmo N de cada um, com a taxa e a receita média dele): US$ 481 mil virou US$ 650 mil, e a comparação ficou mais dura pra regra nova.
- A narrativa dizia "um commit por etapa", mas o build foi commitado em cinco blocos no fim. Corrigi a narrativa, não o histórico.

### O que eu adicionei que a IA sozinha não faria

- A leitura de operação comercial: carteira fixa por vendedor justificada por organização e cadência, assumindo abertamente que os dados não mostram ganho de conversão.
- "Ninguém pode perder comissão" como regra de desenho. Foi isso que mudou o critério das carteiras e a regra dos deals vivos.
- Reorganizar agora em vez de esperar o pipeline zerar, e travar o CRM pra só aceitar deal em conta própria.
- Dar aos managers a palavra final dentro do time, com travas, em vez de impor a divisão.
- Pedir revisões adversárias antes e depois de construir, e inverter regras minhas quando a evidência mandou: ICP antes de valor virou valor antes de ICP; Encerrar virou Confirmar.
- Manter a lógica numa planilha que RevOps consegue abrir e mudar sem desenvolvedor, e fazer o app ser só a janela.

---

## Evidências

- [x] Screenshots do app em uso: [`process-log/screenshots`](./process-log/screenshots) (arquivos `app-*`)
- [x] Screenshots das interações com a IA e do arco de commits: [`process-log/screenshots`](./process-log/screenshots) (arquivos `ia-*`, trechos literais do chat export e saída do `git log`)
- [ ] Screen recording do workflow
- [x] Chat export: [`process-log/chat-exports`](./process-log/chat-exports)
- [x] Git history (código e process log na branch `submission/ricardo-oliveira`)
- [x] Narrativa escrita: [`process-log/00-narrativa.md`](./process-log/00-narrativa.md)
- [x] Fórmulas e configuração da planilha exportadas: [`solution/sheet`](./solution/sheet)

---

_Submissão enviada em: 23/10/2026_
