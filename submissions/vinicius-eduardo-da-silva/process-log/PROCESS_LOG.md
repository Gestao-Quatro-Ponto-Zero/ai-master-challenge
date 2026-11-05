# Process log

Registro do que aconteceu, na ordem em que aconteceu. Ferramenta usada: Claude Code (modelo Claude Opus 5.5), no VS Code.

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

## Como o trabalho evoluiu

1. **Leitura das regras.** O alvo definido foi superar o baseline de IA, com software funcionando e validação medida.
2. **Auditoria dos dados** (`exploration/audit.py`). Apareceram o limite de 138 dias, as contas em branco em 68% dos deals abertos, o erro `GTXPro` e o corte no início do histórico.
3. **Teste de sinais** (`exploration/signals.py`). Com validação temporal, as características fixas chegaram a AUC de cerca de 0,55. Foi aqui que o plano mudou: um score baseado em vendedor, produto e porte seria precisão falsa.
4. **Primeiro replay** (`exploration/first_replay.py`). Reconstrução de segundas-feiras passadas, usando só o que se sabia em cada data.
5. **Teste de variantes** (`exploration/variant_test.py`). Trimestre entrou; vendedor e produto ficaram de fora.
6. **Cobertura por vendedor** (`exploration/rep_coverage.py`). A região Central inteira não tinha deal vivo, o que mudou o desenho da tela.
7. **Interface e teste no navegador** (`exploration/ui_check.py`).
8. **Revisão visual e correção do início de trimestre** (`exploration/quarter_start_check.py`).

Os scripts de `exploration/` são a evidência de cada etapa. `variant_test.py` roda na versão do commit `4a93295`, antes da troca de mês por semana.

## Onde a IA errou e como foi corrigido

Todos os itens abaixo foram percebidos durante o trabalho, com a verificação indicada.

| Erro | Como apareceu | Correção |
|---|---|---|
| Afirmei que a chance subia de forma contínua com a idade | O teste de variantes mostrou dois picos. O número anterior olhava só deals já encerrados | Mensagem corrigida; o score usa a chance real por faixa de idade |
| A equipe era montada a partir dos deals, e 5 vendedores sumiam | Teste no navegador: o filtro não encontrava `Carl Lin` | Leitura direta de `sales_teams.csv` |
| Um score mais alto aparecia abaixo de um mais baixo | Teste no navegador de ordem dos scores | Regra única de ranking, usada na ferramenta e no replay, com teste próprio |
| Em 1º de janeiro, um deal de 67 dias aparecia com cerca de 14% de chance | Revisão da tela: contradizia o achado de que, no início do trimestre, só deals novos fecham. Medido: 0–2,6% | Troca de mês por semana do trimestre |
| A mensagem "peça a decisão" contradizia uma chance baixa | Mesma revisão | Nova mensagem quando a chance é baixa, com teste |

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

## O que eu adicionei

> **Vinicius: escreva esta seção com suas palavras antes de enviar.** Descreva o que você de fato avaliou, testou ou mudou, incluindo sua impressão ao usar a ferramenta como vendedor. Ela não deve ser escrita pela IA.
