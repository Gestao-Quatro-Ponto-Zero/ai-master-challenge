# Produto: o copiloto de pipeline do vendedor

Segunda versão, de 10/11/2026. A primeira, que o Daniel aprovou antes de olhar os dados, está em `PRODUTO-v1-antes-dos-dados.md` e prometia "os cinco primeiros" de cada vendedor. A auditoria mostrou que essa promessa não cabe nestes dados, e o Daniel decidiu a forma abaixo. Esta página foi escrita pelo orquestrador a partir da decisão dele; onde houver diferença, vale o que ele escreveu.

## Quem usa
- O vendedor: um dos 35 do time, não técnico. Abre na segunda de manhã, entre uma ligação e outra.
- O gestor: o time dele ou a região, a mesma ferramenta com filtro.
- Quem pediu: a Head de Revenue Operations. Quer algo que o vendedor use, não um modelo que ninguém abre.

## A dor (nas palavras dela)
"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar." São duas dores: tempo perdido no que não fecha, e negócio bom esfriando. Ordenar por valor não resolve nenhuma.

## O que os dados mostraram (fontes: `relatorios/01.md` e `relatorios/01z.md`)
- Só o tempo separa ganho de perda. Produto, setor, porte, vendedor, gestor e região ficam dentro do ruído.
- Existe uma janela: nenhum negócio foi ganho depois de 138 dias aberto, e os fechamentos acontecem até o fim do trimestre seguinte ao do engajamento.
- Na data dos dados, a maior parte da lista aberta já passou dessa janela: 1.474 dos 1.589 negócios em andamento. Vivos são 115; na fila, sem data nenhuma, 500.
- Nenhum negócio que passou da janela foi ganho: zero em 717 negócios distintos, nos doze cortes medidos.

## A decisão do Daniel (10/11/2026, como ele escreveu ao construtor)
1. A forma nova é a que eu quero: vivos, fila para engajar e limpar.
2. O que sustenta o produto é a separação entre o que está vivo e o que é para limpar: a janela da regra A, 138 dias e o prazo do trimestre. Foi isso que se confirmou nas datas novas e nos 717 negócios distintos, então é isso que vem primeiro na tela e no README.
3. Entre os vivos, a ordem é por valor, com mais dias restantes como desempate. A contagem regressiva aparece, mas não ordena. O README diz que essa ordem não foi confirmada em datas novas e que, com sete preços de tabela, ordenar por valor é quase ordenar por produto.
4. Negócio vivo com mais de 90 dias aparece como "esfriando", com a frase da tabela e a data da conta. Informa, não reordena.
5. A fila é só uma lista por preço de tabela, e a tela diz que nada mais nos dados a ordena.
6. Em "limpar", mostra a evidência e a ação, sem afirmar o motivo.
7. A segunda-feira do produto é 01/01/2018, com os dados fechados no domingo 31/12; o dia do prazo ainda conta como vivo.
8. Nenhuma porcentagem por negócio.

## O que o produto faz
1. Abre com uma manchete para o vendedor ("você tem N vivos, M na fila, K para limpar") e três blocos:
   - Vivos: os negócios ainda dentro da janela, por valor, cada um com a contagem regressiva do prazo.
   - Fila para engajar: os negócios que ainda não têm data, como o próximo trabalho do vendedor.
   - Limpar: os que passaram da janela, com a evidência e a ação (encerrar no CRM e parar de gastar a segunda-feira com eles).
2. Explica cada negócio em linguagem de vendedor: há quantos dias está aberto, quantos faltam, o que é o "valor" (o preço de tabela do produto, porque negócio aberto não tem valor de fechamento) e o que aconteceu com negócios que chegaram abertos à mesma idade ("cerca de X em cada 100 foram ganhos depois", com a data da conta).
3. Indica o próximo passo: a ferramenta escolhe o passo por regra, a partir do que os dados mostram daquele negócio, e a IA redige o porquê.
4. Entrega o briefing de segunda: uma página por vendedor, montada dos três blocos, pronta para ler em um minuto.
5. Mostra uma segunda-feira do passado: numa lista curta de datas, o que a ferramenta teria dito ao vendedor com o que se sabia naquele dia, e o que aconteceu depois. É a prova à vista de quem usa.
6. Mostra ao gestor a saúde do pipeline, só em fatos: valor vivo contra valor parado por vendedor, gestor e região, quem não tem nenhum negócio vivo, o tamanho de cada fila, quantos negócios parados cada vendedor ainda carrega.

## Como a IA entra, sem chave de API
- O produto completo é o score mais a tela: manchete, blocos, explicações de regra e filtros funcionam sem nenhum texto de IA. A IA só acrescenta texto.
- Os textos da IA são gerados por um pipeline real sobre os dados reais e ficam guardados no repositório com a procedência (modelo, data, o prompt, os fatos que entraram). O avaliador roda e vê tudo sem chave e sem conta.
- Todo número e todo nome num texto vem dos fatos daquele negócio, preenchido pelo código e não pela IA; um texto com dado que não esteja nos fatos é reprovado. A IA explica e redige; quem decide o bloco, a ordem e o próximo passo é o score, que é auditável.
- Com o Claude Code instalado, um comando regenera os textos. Nenhuma chave de API é usada, e nenhuma credencial vai no repositório.

## Princípios
- Simples na tela, completo por baixo: em dez segundos o vendedor sabe por onde começar.
- Honesto: o que os dados não sustentam não entra no score, e a tela diz o que não sabe.
- Cada recurso de IA responde a uma dor desta página, ou sai.
- Roda com um comando documentado e tem um endereço público.

## Depois da entrega (sustentação)
Um comando recalcula tudo quando os dados mudam; um relatório avisa quando a janela dos dados se afasta da que o score aprendeu; e o ganho real se mede com um grupo de controle (metade do time com a ferramenta, metade sem, por um ciclo de vendas).

## Fora
Editar o CRM, login, integrações reais com e-mail ou Slack (o briefing sai como texto pronto para enviar), previsão de receita. E o que a auditoria derrubou: "os cinco primeiros" como número fixo, porcentagem de chance por negócio, "casos parecidos" por produto, setor ou porte, e "quem insiste no que não fecha" como afirmação sobre o comportamento de alguém.

## Como sabemos que ficou bom
- A separação entre vivo e limpar é a afirmação principal e foi confirmada em três datas que não moldaram a regra e em negócios distintos; o número é publicado como saiu, com o limite dito: as datas se sobrepõem no tempo e não há período que a regra nunca viu.
- A ordem entre os vivos é secundária, e a tela e o README dizem que ela não foi confirmada em datas novas.
- Cada número na tela e no README sai de um comando que está no repositório; cada texto da IA passa na conferência contra os fatos.
- Alguém de fora roda seguindo só o README, e um vendedor entende a tela sem explicação.
