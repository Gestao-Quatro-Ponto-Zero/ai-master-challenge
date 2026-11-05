# Process log

Registro do que aconteceu, na ordem em que aconteceu. Ferramenta usada: Claude Code (modelos Claude Opus 5.5 e, na reta final, Claude Fable 5), no VS Code.

## Divisão do trabalho

| Quem | O quê |
|---|---|
| Vinicius | Decisões de produto e de escopo listadas abaixo, além da revisão final |
| Claude Code | Leitura do desafio, análise dos dados, código, testes e primeira versão dos textos |

## Decisões tomadas por Vinicius

Em cada caso, o Claude apresentou as opções e uma recomendação, e Vinicius decidiu.

| Decisão | Escolha | Alternativas descartadas |
|---|---|---|
| Desafio | 003 Lead Scorer | 001, 002 e 004 |
| Deals acima de 138 dias | Fila separada, com decisão do vendedor | Lista única com score baixo; destaque para resgate |
| Efeito de trimestre | Testar no replay antes de incluir | Só alerta; ignorar |
| Formato | Web app sem deploy, para abrir localmente | Vercel; Streamlit |
| Extras, depois de perguntar se dava para ir além do enunciado | Máquina do tempo, plano de piloto e calculadora de tempo | Mensagem pronta para deal parado |

## Como o trabalho evoluiu

1. **Leitura das regras.** O alvo definido foi superar o baseline de IA, com software funcionando e validação medida.
2. **Auditoria dos dados** (`exploration/audit.py`). Apareceram o limite de 138 dias, as contas em branco em 68% dos deals abertos, o erro `GTXPro` e o corte no início do histórico.
3. **Teste de sinais** (`exploration/signals.py`). Com validação temporal, as características fixas chegaram a AUC de cerca de 0,55. Foi aqui que o plano mudou: um score baseado em vendedor, produto e porte seria precisão falsa.
4. **Primeiro replay** (`exploration/first_replay.py`). Reconstrução de segundas-feiras passadas, usando só o que se sabia em cada data.
5. **Teste de variantes** (`exploration/variant_test.py`). Trimestre entrou; vendedor e produto ficaram de fora.
6. **Cobertura por vendedor** (`exploration/rep_coverage.py`). A região Central inteira não tinha deal vivo, o que mudou o desenho da tela.
7. **Interface e teste no navegador** (`solution/tests/ui_check.py`).
8. **Revisão visual e correção do início de trimestre** (`exploration/quarter_start_check.py`).
9. **Extras.** Vinicius perguntou se o enunciado estava atendido e se dava para ir além. O Claude apontou as fraquezas da entrega e propôs quatro ideias, e ele escolheu três.
10. **Redesign.** Ao usar a página, Vinicius achou que ela estava simples demais e pediu algo mais visual, fácil de entender, de agir e de revisar. O Claude transformou a lista em uma mesa de trabalho: plano da semana em 3 passos, cartões com linha da vida do deal, botões Feito e Adiar, triagem da fila Decidir com atalhos de teclado, aba Revisar e visões por região. O score não mudou.
11. **Auditoria final** (`exploration/final_audit.py`). Vinicius pediu para analisar se tudo funcionava e se a solução daria resultado. O Claude testou um clone limpo e tentou derrubar o ganho principal. O "+42%" era verdadeiro, mas parcial, e a mensagem principal mudou.
12. **Prompt consolidado** ([`prompt-consolidado.md`](prompt-consolidado.md)). A pedido de Vinicius, escrito depois do trabalho para resumir o raciocínio. Não é o prompt usado no processo real.

Os scripts de `exploration/` são a evidência de cada etapa. `variant_test.py` roda na versão do commit `7e39015`, antes da troca de mês por semana.

13. **Datas.** Vinicius apontou que a ferramenta estava presa a uma data fixa. O Claude acrescentou o filtro de data do pipeline, com datas passadas só para consulta, e a ordenação por data de entrada.

14. **Detalhes do deal.** Vinicius perguntou se dava para incluir mais detalhes que ajudassem o vendedor a ver valor no deal. O Claude acrescentou o fechamento típico, o perfil da conta, o relacionamento e o histórico do vendedor, como contexto, sem mudar o score.

15. **Sequência de prompts** ([`sequencia-de-prompts.md`](sequencia-de-prompts.md)). Vinicius preferiu não publicar a conversa original, por ter sido informal, e pediu uma versão com engenharia de prompt aprimorada. O Claude a escreveu depois do trabalho, identificada como tal, ao lado do que aconteceu em cada etapa.

16. **Critérios do avaliador, conversa devolvida e ferramentas publicadas.** O Claude leu os PRs e comentários públicos do repositório: o avaliador pede evidência de julgamento humano (30% da nota), process log auditável dentro do repositório e entrega fácil de testar. Vinicius então se inscreveu na vaga, mandou devolver a conversa completa, publicar as ferramentas e medir o tempo de triagem do Challenge 002 em um ensaio próprio. Ele pediu também que suas falas fossem refinadas; o refinamento ficou apenas na [`sequencia-de-prompts.md`](sequencia-de-prompts.md), identificada como escrita depois, e o transcript permaneceu sem retoques.

## Onde a IA errou e como foi corrigido

Todos os itens abaixo foram detectados pelo próprio Claude Code, nos testes automáticos e na revisão das telas que ele fez, e não por Vinicius.

| Erro | Como apareceu | Correção |
|---|---|---|
| Afirmei que a chance subia de forma contínua com a idade | O teste de variantes mostrou dois picos. O número anterior olhava só deals já encerrados | Mensagem corrigida; o score usa a chance real por faixa de idade |
| A equipe era montada a partir dos deals, e 5 vendedores sumiam | Teste no navegador: o filtro não encontrava `Carl Lin` | Leitura direta de `sales_teams.csv` |
| Um score mais alto aparecia abaixo de um mais baixo | Teste no navegador de ordem dos scores | Regra única de ranking, usada na ferramenta e no replay, com teste próprio |
| Em 1º de janeiro, um deal de 67 dias aparecia com cerca de 14% de chance | Revisão da tela: contradizia o achado de que, no início do trimestre, só deals novos fecham. Medido: 0–2,6% | Troca de mês por semana do trimestre |
| A mensagem "peça a decisão" contradizia uma chance baixa | Mesma revisão | Nova mensagem quando a chance é baixa, com teste |
| Propus um piloto de 30 dias | Simulação de divisões falsas: um mês só detectaria ganhos acima de 61% em receita | Piloto de um trimestre, com deals ganhos como métrica principal |
| Empates de preço seguiam a ordem do arquivo, que é por data | Revisão do código ao construir a Máquina do tempo | Desempate por ID e medição com empates sorteados: a vantagem ficou em 41–42% |
| A Máquina do tempo mostrava números de janeiro de 2018 sobre uma lista de agosto de 2017 | Revisão da tela | Resumo oculto nessa aba |
| O "+42%" era o resultado principal, contra uma referência fraca | Auditoria final: contra quem já ignora os parados, o ganho é de +21%, e de +8% em out–nov | Rival mais forte incluído no replay, na ferramenta e na mensagem principal |

Um vazamento foi evitado antes de existir: "Conta em branco" entregaria, antes da revelação, que o deal nunca fechou. Por isso, a conta fica oculta até o clique, e um teste confere isso no navegador.

## Exceção a um critério definido antes

A troca de mês por semana só ficaria "se o replay não piorasse". O resultado foi +3,7% em jul–set, **−2,0% em out–nov** e +1,7% no total, ou seja, o critério não foi cumprido por inteiro. A troca foi mantida porque o ranking praticamente empata e a chance mostrada no início do trimestre fica muito mais próxima do real.

## Armadilha do repositório

O `.gitignore` do desafio ignora `submissions/`, e o PR não pode alterar nada fora da pasta do candidato. A solução foi usar `git add -f` para os arquivos da submissão.

## Iterações do score

| Versão | Receita no top 10, média por segunda | Ganho sobre ordenar por valor |
|---|---:|---:|
| Maior valor (referência) | US$ 225,2 mil | — |
| Valor × idade | US$ 288,5 mil | +28% |
| Valor × idade × mês do trimestre | US$ 313,4 mil | +39% |
| Valor × idade × semana do trimestre (final) | US$ 318,7 mil | +42% |
| Versão final, com desempate por ID | US$ 319,1 mil (referência: US$ 225,0 mil) | +42% |
| Rival mais forte: maior valor, sem os parados | US$ 264,4 mil | Score à frente em +21% |

## O que eu adicionei

*Texto organizado pelo Claude Code a partir das respostas de Vinicius, e revisado por ele.*

Não conheço o negócio de vendas. Resolvi este problema junto com a IA, e minha contribuição foi de direção e de cobrança, não de conhecimento comercial:

- **Decidi o rumo:** escolhi o desafio, a fila separada para os deals parados, testar o efeito de trimestre antes de usá-lo, o formato sem deploy e quais extras entrariam.
- **Usei a ferramenta e disse o que estava ruim:** achei a página simples demais, e isso levou ao redesign. Notei que ela estava presa a uma data fixa, e isso levou ao filtro de data. Perguntei se dava para mostrar mais detalhes para o vendedor ver valor no deal, e isso levou aos detalhes do deal.
- **Cobrei resultado:** perguntei se estávamos atendendo ao enunciado e se dava para ir além. Depois, perguntei se tudo funcionava e se teríamos resultado. Essa última pergunta levou à auditoria que trocou o "+42%" pela comparação mais honesta, de +21%.

**Minha aposta:** se a ferramenta resolver a dor do vendedor, eles vão usar. A decisão sobre um deal parado precisa ser breve, para ele decidir e fazer acontecer. Isso é uma opinião, não um dado, e o piloto serve para testá-la.

**O que eu não fiz:** não encontrei os erros técnicos, que foram detectados pelo Claude Code, e não validei as regras comerciais com alguém da área. Também não tenho os minutos reais gastos em um deal parado, por isso a calculadora usa premissas ajustáveis.
