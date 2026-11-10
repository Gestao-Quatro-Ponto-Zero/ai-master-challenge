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
- Tempo real: a primeira medição do orquestrador do laptop foi às 13:53 -03 (do `date`). Hora em que o Daniel começou: PENDENTE (pergunta feita a ele às 15:08).

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

### O que ficou pendente nesta etapa

- O fork: é público e precisa do ok do Daniel. O clone é só leitura do upstream; nada foi enviado.
- A hora em que o Daniel começou a preparação e a data do download dos dados.

## O que o candidato decidiu

(a preencher com a resposta do Daniel, nas palavras dele)
