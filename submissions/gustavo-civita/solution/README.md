# Case G4 · AI Master: prioridade de vendas

Ferramenta para o vendedor abrir, ver a carteira e saber em qual negociação
gastar o tempo. Roda no navegador, a partir dos quatro CSVs do CRM.

## Como rodar

**Demo no ar:** <https://case-g4-gustavo-c.vercel.app/>. Link direto para uma
vendedora: <https://case-g4-gustavo-c.vercel.app/?vendedor=Kary%20Hendrixson>.

**Sem instalar nada:** abra `solution/app/index.html` com dois cliques. A
ferramenta roda inteira no navegador, sem servidor, sem banco e sem etapa de
build: `index.html`, `style.css`, `app.js`, `workflow.js` e os dados em
`data.js`. A única biblioteca é a fonte de ícones Phosphor (MIT), copiada para
`app/vendor/phosphor/`. A fonte do texto (Inter) vem do Google Fonts quando há
internet; sem internet a tela usa a fonte do sistema e funciona igual. Testado
no Chrome.

Os dados são os quatro CSVs do dataset indicado no enunciado (CRM Sales
Predictive Analytics, Kaggle, licença CC0), com o mesmo conteúdo, em `data/`.
A pasta traz também o `metadata.csv` do dataset (dicionário de colunas), que o
código não lê.

Se preferir servir por HTTP (Python 3.10 ou mais novo):

```bash
cd submissions/gustavo-civita/solution
python -m http.server 8765 --directory app
```

e abra <http://localhost:8765>. Escolha "Vendedor" e um nome, ou "Gerente" e um
time. O Python só é necessário para regerar os dados e rodar os testes.

Para regerar os dados a partir dos CSVs, rodar o teste histórico e os testes
automatizados:

```bash
pip install -r requirements.txt   # pandas e scipy
python build.py                   # recria app/data.js
python backtest.py                # imprime a validação
python -m unittest discover tests # 19 testes da priorização (leva cerca de 40 s)
node tests/test_workflow.js       # 16 testes do fluxo de contato
```

Link direto para um vendedor: `http://localhost:8765/?vendedor=Kary%20Hendrixson`.

A tela se adapta de celular a monitor largo e tem modo escuro (botão no canto
da barra lateral; segue a preferência do sistema na primeira vez). Para abrir já
num tema: `?tema=escuro` ou `?tema=claro`.

**Como a demo foi publicada:** a pasta `app/` é um site estático, sem etapa de
build. A demo é uma cópia dela, sem alteração, num repositório próprio
(<https://github.com/tivita912/case-g4>), publicado na Vercel sem configuração.
Em qualquer hospedagem de arquivos estáticos (Vercel, Netlify, GitHub Pages)
basta apontar a raiz do projeto para `submissions/gustavo-civita/solution/app`.
A demo é pública e sem senha; o que cada visitante registra fica só no
navegador dele.

## O que a ferramenta faz

| Tela | Para quem | O que mostra |
|---|---|---|
| Entrada | Todos | Três perfis (vendedor, gerente, operações de receita) em duas etapas; dá para trocar de perfil a qualquer momento |
| Hoje | Vendedor | A fila do dia em duas partes, com um botão por linha. Em cima, a meta do dia: retornos combinados e negociações com chance, na ordem preço × chance; o contador "X de Y prioridades feitas hoje" conta só essas. Embaixo, "se sobrar tempo": primeiro contato e reativação, com as que têm empresa cadastrada primeiro |
| Aguardando | Vendedor | O que depende do cliente ou de uma data, e quando volta para a fila |
| Carteira | Todos | Todas as negociações abertas, com busca, filtros e ordenação |
| Painel | Gerente e operações de receita | Quatro indicadores (com chance, valor esperado das com chance = preço × chance, sem chance, receita do trimestre) e três seções: "Pipeline hoje" (abertas por time ou vendedor, chance por faixa, prioritárias sem contato), "Atividade do time" (contatos registrados, só os deste navegador) e "Como veio 2017" (receita ganha ou negociações iniciadas por mês) |
| Vendedores | Gerente e operações de receita | Uma linha por vendedor e, ao clicar, o detalhe dele: carteira, prioritárias sem contato, receita por mês e últimos contatos |
| Como funciona | Todos | A conta, o teste e os limites |

Clicar numa linha abre a ficha em duas colunas: à esquerda o que fazer, por que
o score é aquele e o registro do que aconteceu (com confirmação e anotação); à
direita, quem é a empresa.

Em Hoje e na Carteira dá para trocar a **lista** por um **kanban**: as mesmas
negociações, na mesma ordem de prioridade, separadas em colunas por situação. A
escolha fica guardada no navegador. Os gráficos são HTML e CSS, sem biblioteca
(`app/charts.js`), e cada um troca para a tabela dos mesmos números. No tablet
e no celular a navegação vira uma barra fixa embaixo.

A Carteira, Aguardando e Vendedores exportam em **CSV** (o que está filtrado, na mesma ordem) e em
**PDF** (pelo "salvar como PDF" do navegador, com um estilo de impressão próprio
e todas as linhas, sem biblioteca).

## Lógica

Cada negociação aberta vai para uma de quatro listas:

| Lista | Regra | O que o vendedor faz |
|---|---|---|
| Em negociação | Ainda tem chance de fechar pelo histórico | Liga, na ordem de preço × chance |
| Não iniciada | Está em Prospecting (sem data de início) | Primeiro contato, na ordem do preço |
| Reativação | Sem chance, mas iniciada há até 150 dias (180 para produtos a partir de $3.000) | Uma mensagem com condição especial |
| Encerrar | Sem chance e mais antiga que isso | Encerra no CRM |

**A chance** vem do histórico, olhando o mesmo ponto dos trimestres anteriores:
das negociações que estavam abertas com a mesma idade há 3, 6 e 9 meses, quantas
foram ganhas depois. Idade sozinha não basta, porque nesta base uma negociação
é ganha no trimestre em que começou ou no seguinte, e nenhuma depois (entre as
perdidas há uma exceção em 2.473).

**O score** (0 a 100) é a posição de preço × chance entre as negociações com
chance de fechar na empresa. A tela mostra a chance em faixas (alta, média,
baixa), e não em percentual, porque o número exato erra (ver Limitações).

**O que cada fator faz.** O preço pesa mais na posição: entre as 128 negociações
com chance, o score tem correlação de postos (Spearman) de 0,81 com o preço e
de 0,40 com a chance. A chance faz duas coisas, as duas medidas no teste:

- **O corte.** Hoje nenhuma negociação com mais de 96 dias tem chance, contra
  os 138 dias do ciclo mais longo. Isso tira 170 negociações a mais da lista de
  ligação.
- **A ordem de quem fica.** Pegando as mesmas negociações que a ferramenta
  mantém na lista e ordenando só pelo preço, a receita das 10 primeiras cai:
  preço × chance rende +14% no 3º trimestre e +20% no 4º, e ganha em 24 de 24
  semanas. Não é só ordenar por valor.

**Os parâmetros, todos em `scoring.py`:**

| Parâmetro | Valor | Para quê |
|---|---|---|
| Data de referência ("hoje") | A última data de fechamento da base, 31/12/2017 | Idade de cada negociação |
| Preço | O de tabela do produto, não o valor fechado | Uma negociação aberta ainda não tem valor fechado |
| Trimestres de comparação | 3, 6 e 9 meses de calendário antes; só os que caem depois de 01/03/2017, quando a base começa a registrar fechamentos | De onde vem a chance |
| "Mesma idade" | Idade ± 7 dias, juntando as amostras dos trimestres (não é média das taxas) | Amostra suficiente por idade |
| Amostra mínima | 15 negociações; abaixo disso a chance é zero | Não confiar em poucos casos |
| Idade máxima considerada | 200 dias | Acima disso a chance é zero |
| "Tem chance" | Chance de 1% ou mais | Separa "ligar" do resto |
| Faixas | Alta: 40% ou mais. Média: de 20% a 40%. Baixa: abaixo de 20% | O que a tela mostra |
| "Pode fechar este mês" | 10% ou mais de chance de ser ganha em 30 dias, pela mesma conta | Rótulo na linha |
| Reativação | Sem chance e iniciada há até 150 dias (180 para produtos de $3.000 ou mais) | Decisão de negócio minha |
| Score | Posição do valor esperado (preço × chance) entre as com chance, de 0 a 100; empates recebem o mesmo score | Coluna da tabela |

**O que ficou de fora, e por quê.** O enunciado cita deal stage, tempo no
pipeline, tamanho da conta, produto e vendedor como fatores óbvios. Stage e
tempo entram (são a chance) e produto entra pelo preço. Os outros foram
testados e não entram:

- **Vendedor, setor, conta, manager e região:** entre as negociações fechadas,
  a taxa de ganho não difere de forma significativa (p de 0,26 a 0,97).
- **Produto, além do preço:** a taxa de ganho vai de 60% a 65% entre produtos
  (p = 0,37).
- **Tamanho da conta:** por funcionários, p = 0,36. Por faturamento, p = 0,03,
  mas sem direção: as quatro faixas, da menor para a maior, ganham 63%, 62%,
  66% e 61%. Não serve para ordenar, e 68% das negociações abertas nem têm a
  conta preenchida.
- **Combinações:** mais de 100 (vendedor com produto, histórico da conta, carga
  do vendedor, desconto, dia da semana) foram testadas com validação no tempo,
  em `../docs/analises/sinais/`, e nenhuma melhorou a ordem de forma que se
  sustente. Uma delas, "a conta já comprou este produto", melhora alguns pontos
  no papel, mas muito provavelmente é vazamento: nenhuma negociação fechada está sem conta, contra
  68% das abertas, ou seja, a conta costuma ser preenchida no fechamento.

Rode `python backtest.py` para ver a tabela com os p-valores.

Código: `scoring.py` (regras e chance), `backtest.py` (validação), `build.py`
(gera os dados da tela), `app/workflow.js` (o que acontece depois de cada
contato), `app/app.js` (telas), `app/charts.js` (gráficos do painel).

## O que o teste prova

Voltando no tempo em 24 semanas seguidas (01/07 a 09/12/2017) e usando só o que
se sabia em cada dia:

| Verificação | Resultado |
|---|---|
| Receita das 10 primeiras negociações de cada vendedor, contra a regra simples "produto mais caro primeiro, ignorando o que tem mais de 90 dias" (empates de preço desempatados por sorteio) | +9% no 3º trimestre (ganhou em 14 de 14 semanas) e +3% no 4º (5 de 10) |
| A mesma regra simples, desempatando pela negociação mais nova | +7% no 3º trimestre (12 de 14) e −3% no 4º (2 de 10) |
| A regra simples com outros cortes de idade (45, 60, 75, 100, 120 e 138 dias) | A ferramenta fica à frente em todos, de +3% (75 dias, 4º trimestre) a +35% (45 dias, 4º trimestre) |
| As mesmas negociações que a ferramenta mantém na lista, ordenadas só pelo preço | Preço × chance rende +14% no 3º trimestre e +20% no 4º; ganha em 24 de 24 semanas |
| Negociações tiradas da lista de ligação que foram ganhas depois | 0 de 801 |
| Ganho por faixa de chance (observações negociação × semana) | Alta 42,5%, média 21,4%, baixa 2,4% |
| Marcadas como "pode fechar este mês", ganhas em 30 dias | 20,3%, contra 4,2% das não marcadas que ainda tinham chance. Hoje só 2 das 128 têm a marca |

## O que o teste não prova

O teste mostra que a ferramenta **aponta** melhor para onde a receita vai cair.
Ele não mostra que **usá-la** faz cair mais receita: para isso o vendedor
precisa mudar o que faz, e o contato a mais precisa mudar o desfecho. Um
histórico parado, sem registro de atividade, não permite medir nenhum dos dois.
O plano para medir isso está em `../docs/plano-de-piloto-e-adocao.md`.

## Limitações

- **A lista de hoje não pode ser validada.** No fim dos trimestres anteriores,
  cerca de 60% das negociações do trimestre seguiam abertas; em 31/12/2017 são
  10%. A chance das 128 negociações em andamento pode estar superestimada.
- **Uma boa regra simples chega perto na ordem.** Contra "o mais caro primeiro,
  até 90 dias e, no empate, a mais nova", a ferramenta rende +7% no 3º trimestre
  e −3% no 4º. A vantagem de ordem existe contra "só preço" e contra o acaso em
  todas as semanas; contra uma regra simples bem feita, só no 3º trimestre.
- **As semanas do teste se sobrepõem.** São 24 fotos semanais das mesmas
  negociações; "14 de 14 semanas" não são 14 provas independentes. Contando só o
  que foi ganho nos 7 dias seguintes a cada foto, a diferença para a regra
  simples é +10% no 3º trimestre e −5% no 4º.
- **O desempate importa.** Vários produtos têm o mesmo preço. O teste desempata
  as regras de comparação por sorteio; desempatar pela negociação mais velha,
  como uma versão anterior fazia sem declarar, inflava a vantagem da ferramenta
  para +13% e +10%.
- **"Valor esperado" não é previsão de receita do trimestre.** Soma só as 128
  negociações com chance, e a mesma conta superestimou o ganho nas datas
  passadas em que foi testada (a chance prevista foi em média 43% e 35% foram
  ganhas).
- **71% das negociações com chance não têm a empresa no CRM** (91 de 128). A
  ficha avisa e dá o código, mas localizar o cliente fica com o vendedor.
- **O percentual de chance erra.** Em 30/09, para negociações de 60 a 75 dias, a
  previsão era 37% e 7% foram ganhas. Por isso a tela usa faixas.
- **A chance separa "fecha" de "fica aberta", não ganho de perda.** Entre as que
  fecham, ela quase não distingue quem ganha de quem perde (AUC 0,52, em
  `../docs/analises/conferencia/verifica_veredito.py`).
- **Uma regra simples faz a maior parte da triagem.** "Encerrar o que passou de
  138 dias" cobre 1.291 das 1.461 negociações que a ferramenta tira da lista.
- **Não há prova de que os vendedores gastavam tempo nas negociações mortas.**
  Das 801 tiradas da lista no teste, 799 nunca foram fechadas por ninguém.
- **"Sem contato" é o que a ferramenta registrou.** O CRM não guarda ligações,
  e-mails nem reuniões, nem telefone ou e-mail do cliente. Não há custo de
  produto, e 68% das negociações abertas não têm a empresa preenchida.
- **Não iniciadas não têm chance nem score.** A base não mostra quantas viram
  negociação.
- **A ferramenta prioriza de verdade para 17 dos 35 vendedores.** Dez, todos do
  escritório Central, têm negociações abertas mas nenhuma com chance; oito não
  têm nada aberto. Para esses dez a tela diz isso ("Nenhuma prioridade hoje") e
  mostra só o bloco de primeiro contato e reativação, com as que têm empresa
  cadastrada primeiro (primeiro contato antes de reativação, e o mais caro antes
  dentro de cada um). É um roteiro de prospecção, não uma priorização.
- **"Empresa cadastrada primeiro" é bom senso, não dado.** No bloco "se sobrar
  tempo" a ordem não foi testada: a base não permite medir se primeiro contato
  ou reativação viram negócio.
- **Reativação e prazos de retorno são apostas.** Nenhuma negociação parada foi
  ganha no histórico, e os prazos (religar em 2 dias, segunda mensagem em 3,
  trocar ligação por mensagem depois de 3 tentativas) são decisões de negócio,
  sem dado por trás.
- **O padrão de trimestre vem de 14 meses de uma base de exemplo.** Numa empresa
  real precisa ser medido de novo.

## O que precisaria para escalar

- Ler e gravar direto no CRM, em vez de CSV e do armazenamento do navegador.
- Login do CRM: hoje a entrada separa vendedor e gerente, mas não tem senha, e
  todos os dados estão no arquivo.
- Registro central de contatos, com quem fez, a posição na fila e a chance no
  momento. Sem isso o gerente não vê o que o time registrou.
- Recalcular a chance todo dia. Hoje a idade é contada até 31/12/2017.
- Com clientes reais e anotações no CRM, um modelo de linguagem poderia resumir
  o histórico e personalizar a mensagem. Não foi incluído porque as empresas da
  base são fictícias e ele inventaria o que elas fazem.
