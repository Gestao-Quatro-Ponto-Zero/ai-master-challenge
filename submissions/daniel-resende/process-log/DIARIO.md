# Diário do processo

Escrito na mesma etapa em que cada coisa aconteceu. As horas vêm do comando `date` (fuso -03), nunca de estimativa.

## Quem faz o quê

- **Daniel (o candidato)** define a visão do produto (`process-log/produto.md`), dirige o trabalho, responde aos relatórios de decisão, usa o app como vendedor antes da entrega e aprova tudo o que é público. Só ele decide.
- **Orquestrador**: duas sessões do Claude Code que nunca constroem. Uma, no servidor do Daniel, leu as regras e desenha o caminho e os prompts; outra, neste laptop, leu as regras de forma independente, confere cada rascunho contra o disco, corrige e grava em `prompts/`. O Daniel leva cada prompt ao construtor à mão.
- **Construtor (esta sessão)**: lê, audita, desenha, constrói, testa e faz os commits. Quando há trabalho em paralelo é o líder: os subagentes escrevem arquivos e nunca rodam git.
- **Verificadores**, no fim: uma sessão limpa de outra família de modelo (Codex CLI) e uma sessão nova desta. Não editam a solução; tentam refutá-la. Quem construiu não aprova.

O piso fixo de todas as sessões está em `process-log/piso.md`; cada prompt em `process-log/prompts/` (sete deles como trechos, marcados na primeira linha).

## Ferramentas e por quê

| Ferramenta | Para quê | Por quê |
|---|---|---|
| Claude Code (extensão do VS Code), modelo Claude Fable 5 | construtor líder: fundação, desenho e validação do score, contratos, relatório | lê e roda no disco, então cada afirmação sai de um comando |
| Subagente do Claude Code (mesmo modelo) | auditoria dos dados (`solution/audit.py`) | roda em paralelo ao desenho, com contexto próprio |
| Subagente de pesquisa do Claude Code (com busca na web) | `docs/pesquisa.md`, fontes nomeadas e datadas | a tela e o score partem de práticas verificadas, não de memória |
| `claude -p` em contexto limpo (`--setting-sources "" --tools ""`) | o baseline "IA sozinha" | medir o que o texto cru do desafio produz, para saber onde esta entrega precisa ser melhor |
| GitHub CLI (`gh`) | checar o upstream; fork e PR só com o ok do Daniel | é o canal de entrega do teste |
| Duas sessões do Claude Code como orquestrador | planejar, redigir e conferir os prompts | separa quem planeja e confere de quem constrói |

## Preparação, antes de qualquer prompt (10/11/2026)

- As regras do teste foram lidas de forma independente por duas sessões e as leituras, comparadas.
- O laptop foi medido (o que roda aqui, com qual Python, como chamar o modelo sem chave de API).
- O produto foi escrito em `PRODUTO.md` antes de qualquer código, e o Daniel aprovou o texto.
- O plano foi revisado várias vezes antes do primeiro prompt.
- Tempo real: a primeira medição do orquestrador do laptop foi às 13:53 -03 (do `date`). Hora em que o Daniel começou, nas palavras dele: "Comecei hoje por volta das 13:30, lendo o desafio e planejando com o orquestrador. O primeiro prompt ao builder foi às 15:06."

## Etapa 1: fundação, auditoria e desenho (prompt `01-fundacao-auditoria-desenho.md`)

Início real: 15:06:55. Caixa de tempo: 60 minutos.

### 1.1 Fundação (15:06 a 15:10)

- `pwd` e `dados/` conferidos. A pasta tem os quatro CSVs pedidos e mais um `metadata.csv` (dicionário de campos do dataset), que não foi copiado.
- Upstream: nenhum PR do usuário `danielgresende`; a pasta `daniel-resende` não aparece nos arquivos de nenhum dos 238 PRs que listam arquivos (só títulos e listas de arquivos foram lidos). Existem `daniel-schkolnick`, `daniel-spinelli` e `daniel-vieira`: sem colisão.
- O fork ainda não existia e criar um fork é público. Perguntei ao Daniel e, sem esperar parado, clonei o upstream só para leitura (`upstream` configurado, `git rev-parse upstream/main` com saída 0), criei a branch `submission/daniel-resende` e a identidade local do git. O remoto `origin` entra quando o Daniel der o ok.
- Hook local de pre-commit instalado (não vai para o repositório). Prova às 15:09: um arquivo descartável com uma chave falsa foi recusado ("key-shaped string in the staged diff", saída 1) e um arquivo fora da pasta da submissão também ("staged path outside submissions/daniel-resende/", saída 1). Os dois foram tirados do stage e apagados.
- Lidos na íntegra: `README.md`, `CONTRIBUTING.md`, `submission-guide.md`, o template, `challenges/README.md`, o README do challenge 003 e o `.gitignore`.
- Esqueleto criado; `piso.md`, `produto.md` e o prompt copiados byte a byte; dados copiados com `SHA256SUMS` e `FONTE.md`.

### 1.2 Três frentes em paralelo (lançadas às 15:10)

Os prompts dados a cada uma foram gravados antes do lançamento e estão em `process-log/prompts/` (`01a`, `01b`, `01b2`, `01c`). Os subagentes escreveram arquivos e não rodaram git.

**Baseline (15:10:49 a 15:20:45, em segundo plano).** O texto cru do README do desafio, e mais nada, para o modelo mais forte disponível aqui, em contexto limpo e sem ferramentas. O que uma IA sozinha entrega e onde esta entrega precisa ser melhor:

1. Não entrega software: sem ferramentas e sem os dados, devolve a descrição de um app. O desafio exige algo que rode.
2. Afirma ter construído app, CLI, backtest, testes e screenshots, e cita números ("AUC 0.63 against 0.49") que não mediu. Aqui cada número sai de um script guardado no repositório.
3. O score que descreve usa vendedor, conta, produto e setor. A auditoria mostra que esses campos ficam dentro do ruído (AUC 0,520) e que a conta está vazia em 68,2% dos negócios abertos: é um score que não funcionaria nos negócios que importam.
4. Não vê o fato central destes dados: 1.291 dos 1.589 Engaging abertos são mais velhos que o ganho mais demorado da história. Nada no texto dele testa a ordenação em negócios que estavam abertos numa data de corte.
5. Onde ser melhor: validar em negócios abertos, por corte no tempo; grupos com o que aconteceu de verdade; uma tela que diz o que não sabe.

O que deu errado: a primeira execução partiu de um diretório vazio cujo caminho continha o nome da pasta do teste, e a resposta citava um caminho parecido com o do projeto. Percebi lendo a resposta. Rodei de novo de um diretório temporário de nome neutro. As duas respostas estão em `baseline/resposta.md`, sem edição além dos caminhos da máquina, trocados por uma marca; nenhuma foi escolhida por ser melhor.

**Auditoria (subagente, 15:10 a 15:15; correção 15:20 a 15:21).** `solution/audit.py`, só biblioteca padrão, saída em `docs/auditoria-saida.txt`. O que deu errado: o subagente concluiu que "o tempo no funil não reduz a chance" (63,2% de ganho no dia 0, 71,1% no dia 90). Percebi porque minha validação mostrava o contrário: a conta dele olhava só negócios que tiveram desfecho e deixava de fora os que nunca fecham, que são justamente a dor do vendedor. Pedi (prompt `01b2`) a segunda tabela, com todos os abertos: 38,6% no dia 0, 5,5% no dia 120, 0% no dia 140. O veredito passou a "parcial", com as duas visões impressas.

**Pesquisa (subagente, 15:10:53 a 15:14:41).** `docs/pesquisa.md`, 15 fontes nomeadas e datadas, com o que não foi possível verificar dito no próprio arquivo. O que mudou no desenho: grupos em vez de porcentagem com cara de previsão; o modelo de linguagem nunca escreve número nem nome; cartões com poucos motivos em vez de tabela.

### 1.3 Desenho e validação (15:11 a 15:28, seis rodadas de `validate.py`)

A divisão é por tempo e pelo que se sabia: para cada data de corte o código monta "o mundo como era conhecido" (apaga todo evento posterior, com `assert`), pontua os negócios abertos naquela data e só depois olha o que aconteceu nos 90 dias seguintes. Empates dividem as vagas do top 5, para que a comparação não dependa de ordem arbitrária.

1. **15:15, primeira rodada.** Regra A por faixas de idade aprendidas de fotos passadas. Perdeu para "ordenar por valor" no corte de 01/07 (52,4 ganhos e 339.063 contra 62,1 e 387.942). Não escondi: fui atrás da causa.
2. **15:16, a causa.** Cruzando mês de engajamento com mês de fechamento, vi que não existe fechamento antes de 01/03/2017: os negócios engajados antes disso fecharam todos de março em diante e inflavam as idades. Vi também que os fechamentos param no fim do trimestre seguinte ao do engajamento.
3. **15:17, segunda rodada.** Troquei as faixas por uma tabela de vida (quem chegou aberto a cada idade e o que lhe aconteceu), sem a coorte anterior a 01/03. A regra A passou a ganhar nos dois cortes.
4. **15:19, terceira rodada.** Acrescentei o prazo do trimestre (aplicado só se o passado conhecido na data o confirma), um terceiro corte no meio de um trimestre e grupos que olham o valor. Achado: a faixa de chance entre 5% e 25% não tinha ganhado nada nos cortes de início de trimestre; "manter aquecido" como faixa de chance não se sustentava e foi redefinido (vivo, mas de valor baixo).
5. **15:21, quarta rodada.** Medi a ideia de "esfriando" (vivo hoje, fraco em 30 dias). Só se sustenta no meio do trimestre. Ficou registrado como apoio parcial no contrato.
6. **15:26, quinta rodada.** Com tempo de sobra na caixa, rodei mais seis cortes para testar a robustez. Apareceu um erro meu: nos cortes de junho, "deixar ir" (chance abaixo de 5%) continha 372 e 306 negócios, dos quais 114 e 44 foram ganhos. A tabela de vida ainda era curta e eu tratava "ninguém foi visto com essa idade" como "não fecha".
7. **15:27, sexta rodada.** "Deixar ir" passou a exigir evidência positiva: o prazo venceu, ou o negócio é mais velho que o ganho mais demorado já visto. Idade sem nenhum caso observado é tratada como negócio médio. Resultado: nenhum ganho em 3.192 negócios postos em "deixar ir" nos nove cortes, e a regra A ganha de "ordenar por valor" em 9 de 9 (B e C: 5 de 9).

Ressalva escrita no relatório: o prazo e os 138 dias são regularidades que eu vi olhando os dados inteiros. Cada corte só usa o que se sabia na data, mas a regra nasceu depois de eu ter visto o padrão.

### 1.4 Contratos e fatos de exemplo (15:22 a 15:28)

`docs/contrato-score.md` (o arquivo que o score emite), `docs/contrato-ia.md` (o arquivo de textos, com marcadores e conferência) e `docs/fatos-exemplo.json`, escrito por `solution/make_example_facts.py` para cinco negócios reais. Nenhum texto de IA foi gerado nesta etapa.

### 1.5 Relatório de decisão (15:25 a 15:30)

`relatorios/01.md`, fora do fork, entregue ao Daniel.

### O que ficou em aberto às 15:30 (resolvido no fechamento, abaixo)

- O fork: é público e precisa do ok do Daniel. O clone é só leitura do upstream; nada foi enviado.
- A hora em que o Daniel começou a preparação e a data do download dos dados.
- A pergunta "regra A: sim, não ou muda" não chegou a ser respondida: o orquestrador leu o relatório 01, refez as contas e respondeu com o prompt `01z`, que pede três medições antes da decisão.

### 1.6 Fechamento e confirmação (prompt `01z-fechamento-e-confirmacao.md`, 15:43 a 15:48)

Início real: 15:43:03. Caixa de tempo: 25 minutos.

- **Respostas do Daniel**, digitadas no chat junto com o prompt. Fork: "sim, pode criar danielgresende/ai-master-challenge público e ligar como origin. Sem push." Início: "Comecei hoje por volta das 13:30, lendo o desafio e planejando com o orquestrador. O primeiro prompt ao builder foi às 15:06." Dados: "Baixei o dataset do Kaggle hoje, 10/11/2026, por volta das 15h05 e extraí as 15:06."
- **Fork (15:43).** `gh repo fork --remote --remote-name origin`, de dentro do clone, saída 0. `git remote -v` mostra `origin` como `danielgresende/ai-master-challenge` (público) e `upstream` como o repositório do G4; os nomes saíram certos, sem precisar renomear. Nada foi enviado: o fork não tem nenhuma branch `submission/*`.
- **Regra congelada.** `validate.py` não foi tocado (`git diff --quiet 53f9ed2`). Tudo o que segue está num script novo, `solution/confirm.py`, que importa a regra; saída em `docs/confirmacao-saida.txt`.
- **M1 (15:44, rodou uma vez).** Nos três cortes fixados pelo orquestrador, a regra A ganhou de "ordenar por valor" nos três: +9,1%, +8,6% e +4,0% de valor ganho no top 5 por vendedor. "Deixar ir": nenhum ganho em 350, 384 e 504. Nada na regra mudou depois de ver o resultado.
- **M2.** O que estava errado no relatório 01, e quem percebeu foi o orquestrador, não eu: a tabela de grupos somava cortes que se sobrepõem, então o mesmo negócio parado entrava várias vezes (4.430 colocações em "deixar ir" eram 717 negócios). Em negócios distintos: nenhum ganho em 717, 1 perdido, 716 abertos no fim dos dados; nenhum voltou a um grupo vivo.
- **M3.** A tabela que a tela vai dizer no lugar da porcentagem: quem chegou aberto a cada idade e o que aconteceu depois, só com negócios que já tiveram tempo de fechar (escolhidos pela data de engajamento). A forma é estável entre as datas; o nível, não (aos 90 dias: 38, 33 e 26 em cada 100); em 01/07 a tabela ainda não existia.
- **M4, que o prompt não pedia.** A nova forma do produto ordena os vivos só por valor, e essa ordem nunca tinha sido medida: a regra A ordena por chance x valor. Medi nos doze cortes. "Vivos por valor" ganha de "ordenar por valor" em 12 de 12 e da regra A em 6 de 12. Pôr o mais urgente primeiro piora (9 de 12, e só 3 contra a A); o desempate que funciona é o inverso. Foi vista nos doze cortes de uma vez, então não vale como confirmação.
- **O que deu errado nesta etapa.** Na primeira saída do `confirm.py` os títulos de duas colunas da M3 saíram colados. Vi lendo a saída. Corrigi só a largura das colunas e conferi com `diff` que as seções M1 e M2 ficaram idênticas à primeira execução.
- Relatório `relatorios/01z.md` entregue ao Daniel às 15:48, com a pergunta: regra A congelada, com a nova forma do produto: sim, não ou muda.

## Etapa 2: construção em paralelo (prompt `02-construcao-em-paralelo.md`)

Início real: 16:06:36. Caixa de tempo: 90 minutos. O `PRODUTO.md` novo, escrito pelo orquestrador a partir da decisão do Daniel, foi copiado para `process-log/produto.md`; a página aprovada antes dos dados ficou em `produto-v1-antes-dos-dados.md`. O screenshot da decisão entrou como `screenshots/01-decisao-do-score.png`.

### 2.1 Contratos e fatia fina (16:08 a 16:12, do construtor)

- `docs/contrato-score.md` e `docs/contrato-ia.md` reescritos para a forma nova: um arquivo por segunda-feira, o corte na véspera (assim a regra congelada dá a leitura do Daniel, com o dia do prazo contando como vivo, sem tocar em `validate.py`), os três blocos, a contagem regressiva, a frase da tabela do tempo, os agregados do gestor.
- A fatia: `solution/build.py`, `solution/run.py` e uma página simples. Commit `f72e17e` às 16:12, com a manchete de um vendedor já na página.
- **O que saiu diferente do plano:** o prompt pedia a fatia só da data padrão e o `build.py` completo como entrega do subconstrutor do núcleo. Como o código de uma data e o das seis é o mesmo, escrevi o `build.py` inteiro na fatia. O subconstrutor do núcleo passou a revisar e endurecer esse arquivo, em vez de escrevê-lo.
- **O que deu errado:** o `build.py` quebrou na primeira execução (`max()` de lista vazia) porque eu supus que algum vendedor teria os três blocos. Nenhum tem: a regional Central tem toda a fila (500) e nenhum vivo; East e West têm os vivos (45 e 70) e nenhuma fila. Virou fato do contrato e do README.

### 2.2 Dois subconstrutores em paralelo (lançados às 16:12; prompts `02a`, `02b`, `02b2`, `02b3`)

**Núcleo (16:12 a 16:18).** `check_contract.py`, `numbers.py` (saída em `docs/numeros-saida.txt`), `drift.py` com `window.json`, e 8 testes em linhas reais. Mudou três coisas no `build.py` sem mudar a forma: os `assert` viraram erros explícitos, a contagem regressiva só usa o prazo quando a regra o aplica, e um valor que eu tinha deixado fixo passou a ser calculado. Apontou duas frases do contrato que não diziam tudo (o campo `account` aparece para exibir embora esteja na lista dos que vazam; de onde se conta `days_after`); corrigi o contrato. Conferi por comando antes do commit: `check_contract.py` com saída 0, 20 testes OK, `numbers.py` idêntico ao arquivo guardado, `drift.py` "janela estável".

**Camada de IA (16:12 a 16:26, três rodadas).** Geração pelo CLI sem interface, de um diretório vazio, sem chave de API; modelo pedido `sonnet` (o envelope registra `claude-sonnet-5-5` e, em alguns lotes, também `claude-haiku-5-5`; não sabemos por que o segundo aparece, e a procedência guarda os dois nomes).
1. Cinco textos primeiro, lidos por mim. Estavam presos aos fatos e ruins para um vendedor: o plural era digitado pelo modelo ("1 negócios vivos" aconteceria), os zeros liam mal ("Sua fila está em 0") e o próximo passo não dizia nada ("Jogada da semana: ..."). Correção (`02b2`): as contagens com substantivo passaram a ser frases montadas pelo código, com singular, plural e zero; a frase da tabela do tempo vem inteira do score; o próximo passo diz o passo e o fato que leva a ele.
2. Na tela apareceram mais três defeitos: frase começando em minúscula depois de ponto, "você tem nenhum negócio vivo" e rótulo repetindo a frase. Correção (`02b3`), com regras novas na conferência e teste para cada uma.
3. Na regeneração, 9 briefings foram recusados pela regra nova de sequência repetida; o subconstrutor estreitou a regra (uma lista de três negócios repete palavras preenchidas de forma legítima) e gerou os 9. Estado final: 148 textos (115 negócios vivos, 27 briefings, 6 gestores), `check.py` com saída 0, 12 testes.
- O subconstrutor não conseguiu apagar `make_example_facts.py` (o comando foi negado a ele). Era um arquivo meu, da forma antiga, e eu mesmo o removi com `git rm`.
- Defeitos de redação que ficaram: o resumo do gestor abre duas frases com "Time"; "Na janela, nenhum dos 717..." soa estranho. Estão ditos no relatório.

### 2.3 A interface (16:12 a 16:37, do construtor, com a skill `visual-tier1`)

Apliquei o método visual do Daniel (skill `visual-tier1`) na interface.

**Desenho da tela.** Âncora: a janela de 138 dias, o fato que sustenta o produto. A tela é uma régua do tempo: cada negócio vivo é uma marca na idade em que está, a zona depois dos 90 dias é a de quem esfria, e depois da borda fica a pilha do que é para limpar. Sob cada idade da régua vai a conta "cerca de X em cada 100". Uma família tipográfica (Bricolage Grotesque, embutida, licença OFL). Cor por função (vivo, esfriando, fila, limpar), sempre com rótulo ou forma além da cor. Claro por padrão, escuro no botão.

**O que deu errado, e como percebi.**
- Matei o processo errado ao encerrar o servidor da fatia e ele ficou vivo na porta 8765; percebi quando o servidor novo falhou com "Address already in use". Identifiquei o processo como meu e o encerrei.
- Sem o arquivo de textos, a página registrava um erro 404. O `run.py` passou a responder "nenhum texto".
- A manchete do gestor saiu com "[object HTMLSpanElement]" na primeira vez que a tela abriu: uma lista aninhada que eu não achatava. Corrigido, e uma conferência automática passou a cobrir esse erro em todas as telas.
- Uma conferência automática de encaixe apontou 148 problemas na primeira rodada: o link de pular navegação fora da tela, uma lista escondida que se sobrepunha a outro texto, rótulos que quebravam de linha em cima de outros e duas anotações da régua colidindo. Corrigi a página em cada caso. Uma nota recolhível (`details`) também se sobrepunha às linhas; troquei por um botão simples.

**O segundo olhar (prompt `02c`, 16:29 a 16:30).** Um subagente que não desenhou a tela recebeu nove capturas, sem a minha justificativa. O que ele apontou e o que mudou:
- o primeiro negócio ficava abaixo da dobra, no desktop e no celular → cabeçalho e régua mais baixos, o briefing recolhido no celular, a conta por idade atrás de um botão no celular;
- cada negócio repetia os mesmos fatos num parágrafo → linha enxuta (produto, conta, valor, contagem regressiva, próximo passo) e o porquê atrás de "Por quê?";
- "cerca de 39 em cada 100" dentro de cada negócio parece chance do negócio → a frase saiu da face do cartão, fica no "Por quê?" com o aviso de que vale para todos os negócios daquela idade; a régua diz que a posição não é ordem nem chance;
- 91 linhas iguais em "para limpar" pareciam despejo de dados → uma linha por produto, que abre os negócios dela; cada negócio ganhou o ID do CRM, sem o qual o vendedor não o acharia;
- blocos vazios pareciam inacabados → o bloco de trabalho do vendedor ocupa a coluna larga e os outros dois dividem o trilho ao lado;
- os termos não eram definidos → cada bloco abre com uma linha dizendo o que é; duas colunas quase sempre zeradas saíram da tabela do gestor.
- Ele preferiu a composição empilhada; a que ficou como padrão (coluna larga e trilho) nasceu dessa crítica. A empilhada continua em `?comp=pilha` para o Daniel comparar.

**Conferências automáticas (16:36).** Encaixe: sem problemas, da largura de 320 a 1920 px, sem rolagem lateral. Acessibilidade (WCAG 2.2 A/AA): 0 violações, nos temas claro e escuro. Números da tela contra os arquivos do contrato: 496 conferências, 0 divergências. Sem erro no console. Não medido: celular real e o escurecimento automático de navegadores de celular.

### 2.4 Integração (16:37 a 16:40)

`run.py` é o comando único; o README ganhou a metade técnica (como rodar, a lógica nas palavras do vendedor, os resultados com os números de `numbers.py`, as limitações). Testado também com o Python 3.14 do sistema.

### 2.5 A interface refeita pelo método visual do Daniel (prompt `02v-visual-pelo-metodo.md`, 16:43 a 17:02)

Às 16:39 avisei o Daniel de que o app estava no ar. A resposta veio como o prompt `02v`: a tela do vendedor carregava texto demais para quem não é técnico e lia como relatório. Refiz a interface pelo método visual do Daniel.

**O que mudou.**
- A primeira vista cabe numa tela, sem rolar a página, em 1366 x 768 e em 1920 x 1080: a manchete, a janela e os primeiros negócios vivos. As listas rolam dentro do próprio painel.
- Uma linha por negócio: produto, conta quando existe, valor de tabela, dias restantes e a marca "esfriando". Tudo o que explica a linha (o próximo passo, a frase da IA, a frase da conta por idade com o aviso de que não é a chance do negócio, o que é o valor, o ID) abre ao passar o mouse, no foco do teclado e no toque, e fecha de novo.
- As notas de método saíram da primeira vista e foram para um painel só, "Como a ferramenta decide", a um clique, e para uma linha no rodapé. Nenhuma frase que o prompt 02 exigia foi apagada.
- O briefing virou um botão que copia; o texto aparece ao passar o mouse ou no foco.
- "Para limpar" mostra a contagem, o valor, uma linha de evidência e a ação; a lista abre a pedido, uma linha por produto.
- A tela do gestor e a segunda-feira do passado seguem a mesma disciplina. A composição empilhada (`?comp=pilha`) saiu.
- A janela ganhou uma imagem feita pelo método visual do Daniel.

**Medição do texto na tela**, na vista do vendedor ao carregar, em 1366 x 768:

| | Antes (commit `1d88afb`) | Depois | Alvo |
|---|---|---|---|
| Palavras visíveis | 374 | 113 | no máximo 124 (um terço) |
| Maior parágrafo visível | 80 palavras | 12 | no máximo 20 |
| A página rola | sim | não | não |
| Primeiro negócio vivo, do topo | 829 px (fora da tela) | 342 px | dentro da tela |
| No celular (412 x 800), primeiro negócio vivo | 1.003 px | cerca de 480 px | até 1.200 px, sem tabela antes |

**O que deu errado, e como percebi.**
- A primeira contagem de palavras incluía linhas já roladas para fora do painel. Percebi comparando a contagem com o que a captura mostrava; corrigi a contagem e medi de novo o "antes".
- A tela nova deu 149 palavras na primeira medição, acima do alvo. Cortei rótulos repetidos, a soma dos vivos e metade da nota do rodapé; tudo o que saiu da vista continua a uma ação de distância.
- O painel "Como a ferramenta decide" abriu sem a tabela e sem a data da conta: uma lista aninhada virou texto. Uma conferência automática apontou a falta.
- A conferência de acessibilidade apontou a régua: um desenho marcado como imagem com controles focáveis dentro. Passou a ser um grupo.
- Nas linhas do passado, em 320 px, o nome da conta invadia o número. Corrigido.

**O segundo olhar (prompt `02d`, 16:59).** O revisor que não desenhou recebeu onze capturas novas. O que mudou por causa dele: a contagem ao lado de "fora" na janela; a marca do negócio na janela acende quando a linha dele é aberta; o título de cada bloco diz o que o bloco é, quando perguntado; um botão "Fechar" na explicação aberta por toque; uma borda suave que avisa que a lista continua; a fila sem a linha repetida "sem data de engajamento". O que ele apontou e eu não mudei, e levo ao Daniel: a frase da conta por idade, mesmo com o aviso, ainda pode ser lida como chance do negócio; e o próximo passo é a mesma regra para quase todos os vivos.

**Conferências depois do refazer:** texto dentro do alvo; 539 conferências dos números da tela, 0 divergências; encaixe sem problemas; acessibilidade sem violações.

### 2.6 A cor e o gráfico da janela (prompt `02w-cor-e-grafico-da-janela.md`, 17:02 a 17:14)

O orquestrador olhou as capturas das 16:59: o texto estava onde devia, mas a cor (branco, cinza, verde escuro e marrom) podia ser de qualquer painel, e a faixa da janela lia como textura, não como gráfico.

**O que mudou.**
- **Paleta própria.** Página fria e clara com painéis brancos; um acento forte para o que está vivo; uma cor quente de atenção; um negativo claro para o que passou da janela; uma quarta matiz para a fila; tintas neutras para o resto. Cada cor vem com a palavra ou a forma dela (círculo, losango, quadrado, traço).
- **A janela virou um gráfico.** Colunas finas nas idades da tabela do tempo (0, 30, 60, 90, 120 e 138 dias): de cada 100 negócios que chegaram abertos àquela idade, quantos foram ganhos depois, como se sabia naquela segunda. Cada coluna leva o número em cima, em tinta; um título curto diz de quem é a conta e a data. No mesmo eixo de idade, uma marca por negócio vivo do vendedor, sem número nenhum. De 90 dias até o fim da janela, o fundo de atenção com a palavra "esfriando"; depois do fim, um bloco na cor negativa com a contagem para limpar. Numa segunda sem tabela, as colunas somem e uma linha diz isso. No celular o gráfico vira linhas, uma por idade.
- **As imagens do gráfico** foram feitas pelo método visual do Daniel.
- **Uma régua de seis números** sob a manchete, cada um com rótulo de duas palavras e a unidade: vivos e o valor deles, esfriando, fila, para limpar e o valor parado.
- **A explicação de um negócio abre ao lado da própria linha** e nunca cobre a manchete.

**A paleta** (as quatro cores que carregam significado) foi conferida nos dois temas, inclusive para quem não distingue vermelho de verde.

Um aviso, no claro: a cor de atenção tem contraste de 2,73:1 contra o painel, abaixo de 3:1, e por isso nunca aparece sozinha (vem com a palavra "esfriando" e com o losango).

**O que deu errado, e como percebi.**
- A minha primeira paleta tinha o laranja de atenção e o vermelho negativo parecidos demais. Troquei as matizes até as quatro cores ficarem bem distintas nos dois temas; no escuro o acento foi ajustado.
- A explicação aberta mostrava a palavra "null" no fim. Vi na captura do tema escuro e corrigi.
- Com o gráfico, só cabiam 4 linhas de negócio em 1366 x 768; o gráfico e as linhas ficaram mais baixos e agora cabem 6.

**Conferências automáticas (17:12).**
- **Gráfico**: a altura de cada coluna bate com o número do arquivo do score: 8 imagens, 48 colunas, 0 divergências.
- **Texto**: 112 palavras visíveis ao carregar (eram 374; alvo 124), maior frase visível com 14 palavras, página sem rolagem em 1366 x 768 e 1920 x 1080; no celular o primeiro negócio vivo está a 855 px (limite 1.200).
- **Números da tela**: 599 conferências contra o arquivo do score, 0 divergências.
- **Encaixe**: sem problemas. **Acessibilidade**: sem violações, nos temas claro e escuro.
- Não medido: celular real; o escurecimento automático de navegadores de celular.

## O que o candidato decidiu

### Etapa 1: a regra e a forma do produto (10/11/2026, resposta recebida no chat e registrada às 15:54, do `date`)

A pergunta do construtor: "regra A congelada como está, com essa forma do produto: sim, não ou muda?" A resposta do Daniel, como ele escreveu:

> Sim, com ajustes
> 1- A forma nova é a que eu quero: vivos, fila para engajar e limpar
> 2- O que sustenta o produto é a separação entre o que está vivo e o que é para limpar: a janela da regra A, 138 dias e o prazo do trimestre. Foi isso que se confirmou nas datas novas e nos 717 negócios distintos, então é isso que vem primeiro na tela e no README
> 3- Entre os vivos, a ordem é por valor, com mais dias restantes como desempate. A contagem regressiva aparece, mas não ordena. O README diz que essa ordem não foi confirmada em datas novas e que, com sete preços de tabela, ordenar por valor é quase ordenar por produto
> 4- Negócio vivo com mais de 90 dias aparece como "esfriando", com a frase da tabela e a data da conta. Informa, não reordena
> 5- A fila é só uma lista por preço de tabela, e a tela diz que nada mais nos dados a ordena
> 6- Em "limpar", mostra a evidência e a ação, sem afirmar o motivo
> 7- A segunda-feira do produto é 01/01/2018, com os dados fechados no domingo 31/12; o dia do prazo ainda conta como vivo
> 8- Nenhuma porcentagem por negócio

O que o construtor apontou ao receber a resposta, para o próximo prompt (não é decisão dele):

- O ajuste 7 muda uma borda da regra congelada: em `validate.py` o dia do prazo já conta como fora da janela (a conta olha os 90 dias seguintes). Na segunda 01/01/2018 as duas leituras dão os mesmos grupos, porque os prazos de 31/12 já venceram; elas só diferem numa "segunda-feira do passado" que caia exatamente num dia de prazo. O núcleo de scoring precisa implementar a borda como o Daniel decidiu e dizer isso.
- Os contratos e os fatos de exemplo desta etapa descrevem a forma antiga (focar agora, manter aquecido, deixar ir). Ficam como registro; o próximo prompt os reescreve a partir do `PRODUTO.md` atualizado pelo orquestrador.
