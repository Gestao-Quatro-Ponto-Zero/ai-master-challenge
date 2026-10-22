# Process log — como a solução foi construída

Toda a solução foi construída numa única sessão com o **Claude Code** (extensão do VS Code, modelo Claude Opus), em
cerca de 4 horas (22/10, das 12h13 às 16h). Eu conduzi: defini o problema, tomei as decisões e revisei cada entrega
antes de seguir. O Claude executou: análise, código, testes e git.

## Evidências nesta pasta

| Arquivo | O que é |
|---|---|
| [`chat-exports/conversa-claude-code.md`](chat-exports/conversa-claude-code.md) | **A conversa completa**: minhas mensagens na íntegra, as respostas do Claude, as perguntas que ele me fez com as minhas escolhas, e cada ação executada (comandos, arquivos) |
| [`chat-exports/conversa-claude-code-detalhada.md`](chat-exports/conversa-claude-code-detalhada.md) | A mesma conversa com **os comandos completos e as saídas das ferramentas**: cada teste rodando, cada erro aparecendo e sendo corrigido |
| [`plano-inicial.md`](plano-inicial.md) | O plano que o Claude propôs e eu aprovei antes de qualquer código |
| [`analises/01_explorar_backtest.py`](analises/01_explorar_backtest.py) | Primeira análise de validação, que mostrou que a lógica da v1 não se sustentava |
| [`analises/02_explorar_atributos.py`](analises/02_explorar_atributos.py) | Teste de 14 atributos como previsores de vitória (todos ≈ sorteio) |
| [`analises/03_teste_navegador.js`](analises/03_teste_navegador.js) | Teste automatizado no navegador (abre a tela, clica, filtra, checa erros no console) |
| [`screenshots/`](screenshots/) | Evolução da interface: v1 → v1.1 → v2 |
| Git history da branch | Commits de cada etapa, com mensagens descrevendo o que mudou e por quê |

## Linha do tempo

| Hora | Iteração | O que eu pedi / decidi | O que mudou |
|---|---|---|---|
| 12h13 | **1. Planejamento e v1** | Passei o problema como recebi do meu gestor. Escolhi **FastAPI + React** (manutenção e expansão) e **tudo em português** (time que vai manter). Aprovei o plano. | Perfil dos dados (inconsistências `GTXPro`/`technolgy`, 1.425 negócios sem conta), backend + API + tela, 16 testes. |
| 13h17 | **2. Explicabilidade** | "O vendedor precisa entender o motivo de um score ser baixo e outro alto." | Pontos por parte que somam a nota, motivo principal em cada cartão, tela "Como funciona a pontuação". 21 testes. |
| 14h19 | **3. Git e submissão** | Fork, estrutura `submissions/rodrigo-santos/`, README no template. | O Claude leu as regras do desafio antes de montar a pasta e encontrou o `.gitignore` do repositório ignorando `submissions/`. |
| 14h39 | **4. "Precisa rodar sem erro para quem receber"** | Exigi que o avaliador conseguisse rodar de primeira. | Clone limpo testado em Python 3.10, 3.12, 3.13 e 3.14: **não instalava no 3.14** (versão fixa do pandas). Corrigido, a tela passou a ser servida pela API (basta Python) e o README foi reescrito por sistema operacional. Teste no navegador encontrou um erro 404 no console. 22 testes. |
| 15h32 | **5. Validação (backtest)** | O Claude apontou que a pontuação nunca tinha sido validada e propôs um backtest. Aceitei, e depois decidi **refazer a lógica** quando a validação a contrariou. | Ver a seção abaixo. 30 testes. |
| 15h58 | **6. Process log e PR** | Este registro. | — |

## A iteração que mais importou: validar antes de entregar

A v1 parecia certa. A nota combinava a chance histórica por vendedor, produto, setor e conta (35 pts), o valor (35 pts)
e um fator de tempo que penalizava negócios a partir de 88 dias (30 pts). Estava explicada e testada, mas ninguém tinha
verificado se ela **acertava**.

O backtest voltou a 4 datas do passado. Em cada uma, usou só os negócios já fechados, pontuou os que estavam abertos e
comparou com o que aconteceu depois. Resultado:

| Descoberta | Evidência | Consequência |
|---|---|---|
| A chance por vendedor, produto, setor e conta não prevê nada | AUC 0,45–0,51 em 14 atributos (0,5 = sorteio); só 2 de 30 vendedores fora da margem, quando ~1,4 seria esperado por acaso | A chance saiu da nota, e a tela explica ao vendedor o porquê |
| A penalidade por tempo estava invertida dentro do ciclo | Negócio ainda aberto aos 0 dias ganha 63%; aos 120 dias, 76% (as perdas acontecem cedo) | Substituída por "reta final", que é urgência e não penalidade |
| O sinal real é o limite de 138 dias | Nenhum negócio, ganho ou perdido, durou mais que isso; dos 1.246 que passaram do limite nos cortes, **0 fecharam depois** | "Parado" virou critério central: prioridade baixa, ação "atualize ou encerre" e fora do valor esperado |

O Claude apresentou a descoberta e me deu duas opções: redesenhar com base na evidência, ou manter a v1 e só registrar a
limitação. **Decidi redesenhar.** A validação ficou dentro do produto: um módulo testado, a rota `/api/validacao`, o
relatório em [`../docs/validacao.md`](../docs/validacao.md) e um teste que avisa se, com dados novos, algum atributo
passar a prever o resultado.

## Onde a IA errou e como foi corrigido

| Erro | Como apareceu | Correção |
|---|---|---|
| Lógica da v1 plausível, mas sem poder preditivo | Backtest (proposto pelo Claude, aprovado por mim) | Pontuação refeita (iteração 5) |
| Valor esperado inflado (US$ 3,1 mi, 67% em negócios parados) | Backtest | US$ 1,1 mi, sem os parados |
| Nota sem explicação clara | Minha revisão da v1 | Pontos que somam a nota + motivo no cartão |
| Soma dos pontos diferente da nota em 1 | Teste automatizado | Nota = soma dos pontos já arredondados |
| Não instalava no Python 3.14 | Teste com clone limpo | Faixas de versão no `requirements.txt` |
| README com comandos que falham no PowerShell 5.1 | Revisão das instruções | Comandos por sistema operacional, sem ativar o venv |
| Centenas de cartões com o título "Conta não informada" | Captura de tela | Título mostra o código do negócio |
| Texto que presumia o gênero do vendedor | Revisão dos textos | Frase neutra |
| Erro 404 de favicon no console | Teste no navegador | Ícone embutido no HTML |
| Teste do navegador com condição de corrida | O próprio teste falhou | Espera a recarga antes de ordenar |
| Ambiente: porta ocupada, proxy em IPv6, conta git errada no push | Execução | Porta alternativa, `127.0.0.1`, remote com o usuário certo |

## O que eu adicionei que a IA sozinha não faria

- **O enquadramento:** uma ferramenta para vendedor que não é técnico, não um modelo de ciência de dados.
- **As decisões que dependem de contexto:** a stack e o idioma, pensando em quem vai manter o código.
- **Os critérios de qualidade que guiaram cada iteração:**
  - "o vendedor precisa entender a nota";
  - "precisa rodar sem erro para quem receber";
  - "se der para validar, valide antes de entregar".
- **A decisão de jogar fora uma lógica que funcionava**, porque a evidência mostrou que ela não estava certa.
