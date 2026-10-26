# Bloco 1 — escopo (SCOPE.md) e as quatro perguntas do briefing

## Objetivo

Fechar o escopo em `docs/SCOPE.md` (no máximo 2 páginas) e responder às 4 perguntas em aberto da seção 9 do briefing. No PROMPTS.md, o bloco 1 manda fazer as perguntas ao Rafael e esperar. No modo autônomo, o PROMPT_AUTONOMO.md (seção 3) manda responder sozinho, com justificativa. Nenhuma pergunta foi feita e ninguém respondeu: as decisões abaixo são do executor.

## Executor

Claude Sonnet (subagente executor). Execução da especificação E2 de `process-log/plano_execucao_opus.md`, planejada pelo Claude Opus em modo somente leitura.

## O que foi feito (comandos)

1. **Leitura.**
   - Plano de execução: a primeira leitura veio truncada em 514 de 755 linhas, e li o restante com `offset`. Li também as etapas E3 a E12, só para manter o SCOPE coerente com a métrica do backtest (E5) e com a interface (E6).
   - `CLAUDE.md` (já no contexto da sessão), `docs/briefing.md`, `PROMPTS.md`, `PROMPT_AUTONOMO.md`, `process-log/00_fase0_exploracao.md`, `docs/DECISIONS.md` e `process-log/00_bloco-0.md`.
   - Do repositório do desafio, com `Get-Content -Encoding utf8`: `README.md`, `challenges/build-003-lead-scorer/README.md`, `submission-guide.md`, `CONTRIBUTING.md` e `templates/submission-template.md`.
   - Fontes de números: `process-log/outputs/bloco0_eda.txt`, `bloco0_eda2.txt`, `bloco0_snapshot.txt` e `bloco0_conferencia.txt`; `solution/data/raw/products.csv` (somente leitura).
   - `GUIA.md` não foi lido, porque a E2 não o lista.
2. **Estado inicial.** `Get-ChildItem` na submissão (sem `data/raw`), `Get-Content` de `products.csv`, contagem de CR/LF/BOM do `DECISIONS.md` (só LF, sem BOM, termina em `|` + LF) e `gitw.py status` (tudo "nada").
3. **Conferência de fatos antes de citar** (`python -B -I`, script no scratchpad fora da submissão, lendo `raw/*.csv`; nada foi gravado em `$SUB`). Saída transcrita em "Resultados".
4. **Escrita do SCOPE.** Foram quatro versões (ver "O que deu errado"). Contagem de palavras a cada versão com `-split '\s+'`.
5. **Extração dos números do SCOPE** com um script do scratchpad que imita as regras do futuro `test_docs_numbers` (US$, porcentagens, decimais com vírgula, inteiros de 100 ou mais ou com ponto de milhar; sem datas, anos nem código inline). Resultado: 46 tokens, cada um conferido na tabela "Números do SCOPE × fonte".
6. **DECISIONS.** Acrescentei 10 linhas "Bloco 1" ao fim (ferramenta Edit ancorada na última linha existente; nenhuma linha apagada) e conferi que cada linha tem 4 campos.
7. **Este log.**

## Resultados

### Arquivos

- `docs/SCOPE.md` (novo): 7 seções `##` numeradas.
- `docs/DECISIONS.md` (acrescentado): linhas 19 a 28 do arquivo (as 10 últimas), todas "Bloco 1".
- `process-log/01_bloco-1.md` (este arquivo).

### Saída da conferência de fatos (passo 3)

Transcrita do terminal. Não foi salva em arquivo, porque a E2 não prevê um `outputs/bloco1_*.txt`. Os números que o SCOPE usa vêm dos arquivos `bloco0_*.txt`; esta saída só confirma duas coisas que eles não mostram.

```
deals por produto (todos os estagios): GTX Basic 1866, MG Special 1651, GTX Pro 1480,
  MG Advanced 1412, GTX Plus Basic 1383, GTX Plus Pro 968, GTK 500 40
produto de maior preco de tabela: GTK 500, sales_price 26768
fechados GTK 500: 25
Engaging 1589 zumbi 1291 0.8125 valor zumbi 3198664 valor engaging 3892229
Prospecting 500 valor 1073986
sem conta 1425 {'Engaging': 1088, 'Prospecting': 337}
agentes com deal: 30
```

### As 4 perguntas (o que o PROMPTS pedia ao Rafael)

**Q1 — Quatro listas ou uma lista única priorizada?**

- **Opções:** (a) quatro listas em abas; (b) lista única com etiqueta em cada card; (c) lista única mais uma aba "Todos" (considerei e descartei).
- **Recomendação do plano:** (a).
- **Decisão (decisão autônoma do Claude):** (a). Cada lista é ordenada pelo score; Limpe e Qualifique, pelo valor de tabela.
- **Justificativa:**
  - A dor 1 do briefing é "falta uma lista do que largar", e a dor 2 é "falta um alerta de urgência". Cada dor pede uma lista própria.
  - Numa fila única ordenada por valor esperado, os 1.291 Engaging acima de 138 dias (81% de 1.589) afundariam para o fim e ninguém os limparia. Isso é justamente o pipeline inflado (US$ 3,2 mi de US$ 3,9 mi).
  - Os 500 Prospecting não têm `engage_date`, então não têm score e não entram numa fila ordenada por score.
- **Alternativas descartadas:** a aba "Todos" recriaria a lista única e acrescentaria uma aba; a ordenação de Limpe por score foi trocada por valor de tabela porque ali a pergunta é "qual o maior estrago no CRM", e não "qual tem mais chance" (segue o `order_for_list` da E4).
- **Evidência contrária:** nenhuma.

**Q2 — Qual é a tela padrão: vendedor ou manager?**

- **Opções:** (a) vendedor, com o manager como a mesma tela filtrada; (b) manager como padrão; (c) duas telas separadas; (d) exigir a escolha do nome antes de mostrar qualquer coisa (considerei e descartei).
- **Recomendação do plano:** (a).
- **Decisão (decisão autônoma do Claude):** (a). O seletor "Quem é você?" fica no topo e a escolha vai para o endereço (`#vendedor=...`). A visão do manager é a mesma tela filtrada por manager ou região, mais uma "Carteira do time" só com contagens.
- **Justificativa:** o vendedor é o usuário principal (30 com deals contra 6 managers; CLAUDE.md). A taxa de vitória por vendedor é compatível com ruído (qui-quadrado p=0,26), então não entra na carteira do time.
- **Alternativas descartadas:**
  - (b) serve a 6 pessoas em vez de 30.
  - (c) dobra a manutenção, porque o manager vê os mesmos dados filtrados.
  - (d) deixaria a primeira tela vazia, e a checagem da E7 espera as contagens totais sem filtro.
- **Evidência contrária:** nenhuma.

**Q3 — O que vale mais no Foque: maior valor esperado ou menor idade com valor alto?**

- **Opções:** (a) maior valor esperado (chance × preço de tabela), com a urgência à parte; (b) menor idade com valor alto; (c) menos dias até o próximo limiar como ordenação principal (considerei e descartei).
- **Recomendação do plano:** (a), com a justificativa "a chance é praticamente estável enquanto o deal é jovem, então, entre os vivos, quem decide é o valor".
- **Decisão (decisão autônoma do Claude):** (a), e a urgência aparece como "faltam X dias".
- **Evidência contrária à justificativa do plano:** o briefing mostra a chance caindo dentro dos 90 dias, e não estável. Na foto de 30/09/2017, os ganhos depois foram 50% (até 30 dias), 34% (31 a 60) e 7% (61 a 90); na de 30/06/2017, 53%, 45% e 22% (`bloco0_conferencia.txt`). A estabilidade perto de 40% vem de um protótipo do planejador, em fotos mensais agrupadas, que eu não consegui verificar. Pode ser verdade nas fotos agrupadas e falsa numa foto só, e isso será checado no bloco 3. Por isso o SCOPE não afirma que a chance é estável.
- **Justificativa adotada:**
  - A idade já está dentro da chance; ordenar por idade e por chance contaria a idade duas vezes.
  - O dinheiro é concentrado: 3 produtos dão 83,5% da receita ganha, e o MG Special, o segundo produto em número de deals, dá 0,4% (`bloco0_conferencia.txt`). Ordenar só pela idade trataria igual um MG Special e um GTX Pro.
  - "Valor alto" exigiria um corte arbitrário em (b).
  - (c) ignora o valor: o deal mais perto de esfriar iria ao topo mesmo valendo pouco. A urgência fica como desempate e como o texto "faltam X dias".

**Q4 — O modo teste (backtest) entra na interface?**

- **Opções:** (a) entra, com 2 datas passadas; (b) fica só nos documentos.
- **Recomendação do plano:** (a).
- **Decisão (decisão autônoma do Claude):** (a). O custo é de cerca de 30 minutos (briefing, seção 9).
- **Justificativa:** é o que deixa a Head de RevOps ver o que o score teria recomendado e o que aconteceu, e é o diferencial mais forte do projeto (briefing, seção 9). A CLAUDE.md, decisão 6, já exige validação temporal; a tela torna isso visível.
- **Limite registrado:** a lista Qualifique fica indisponível no modo teste, porque o CRM não registra quando o deal entrou em Prospecting (500 deals sem `engage_date`).
- **Evidência contrária:** nenhuma.

### Números do SCOPE × fonte

| Número no SCOPE | Valor na fonte | Fonte |
|---|---|---|
| 1.589 Engaging; 1.291 (81%); 138 dias | 1589; 1291 (0,812); máximo 138 | `bloco0_eda2.txt` (linhas 2 e 3) |
| US$ 3,2 mi de US$ 3,9 mi | 3.198.664 de 3.892.229 | `bloco0_eda2.txt` |
| 30 vendedores com deals; 6 managers | 30 no pipeline; 6 linhas em "WIN RATE by manager" | `bloco0_eda2.txt`; `bloco0_eda.txt` |
| 50% / 34% / 7% / 0% (foto de 30/09) | 0,502 / 0,343 / 0,067 / 0,000 | `bloco0_conferencia.txt` |
| 83,5% e 0,4% | 0,8352 (top 3) e 0,0044 (MG Special) | `bloco0_conferencia.txt` |
| p=0,26; p=0,37 | 0,2639; 0,3719 | `bloco0_eda2.txt` |
| 60% a 65% de win rate | 0,603 a 0,648 por produto; setor, região e manager dentro da faixa | `bloco0_eda.txt` |
| AUC ≈ 0,50 (numéricas) | 0,493 a 0,498 | `bloco0_eda.txt` (Single-feature AUC) |
| 0,51 a 0,54 (target encoding dentro da amostra) | 0,507 (região) a 0,54 (vendedor) | `bloco0_eda.txt` |
| 63% | 0,632 | `bloco0_eda.txt` (OVERALL) |
| 500 Prospecting; US$ 1,07 mi | 500; 1.073.986 | `bloco0_eda.txt`; `bloco0_eda2.txt` |
| 1.425 sem conta, todos abertos | 1.425 (1.088 Engaging e 337 Prospecting) | `bloco0_eda.txt` (NULLS; stage vs null dates) |
| 8.800 linhas | SHAPE (8800, 8) | `bloco0_eda.txt` |
| 66% a 134%, média de 100% | 0,657 a 1,342; média 0,996 | `bloco0_eda.txt` |
| 82% e cerca de 61% depois | 0,821; 0,617, 0,614 e 0,603 | `bloco0_eda.txt` (WIN RATE by close quarter) |
| MG Special é o 2º em número de deals | fechados: GTX Basic 1.436, MG Special 1.223; todos os estágios: 1.866 e 1.651 | `bloco0_eda.txt`; saída do passo 3 |
| GTK 500: maior preço, 25 deals fechados | 26.768; 25 | `products.csv`; `bloco0_eda.txt` (n = 25); saída do passo 3 |
| Cerca de 30 minutos (modo teste) | briefing, seção 9 | `docs/briefing.md` |
| 4 cortes; 200 sorteios; top 20%; empate de até 1 ponto percentual | E5 do plano | `plano_execucao_opus.md` |

### Tamanho do SCOPE

1.175 palavras (contando só tokens com letra ou número) e 1.219 pelo `-split '\s+'`, que é a conta do critério da E2 (limite 1.300). Está acima do alvo de cerca de 1.100 pedido ao executor. Não cortei mais porque os cortes seguintes tirariam alternativas descartadas, critérios checáveis ou riscos específicos do dataset.

## Autoverificação do checkpoint

Critérios "Pronto quando" da E2, rodados depois que os três arquivos estavam prontos (ver o bloco "Verificação final" no fim deste arquivo para a saída dos comandos).

- [x] `docs/SCOPE.md` existe, com 7 títulos `##` numerados.
- [x] Contagem do critério (`-split '\s+'`) abaixo de 1.300.
- [x] Este log contém "Q1", "Q2", "Q3" e "Q4".
- [x] DECISIONS ganhou 4 linhas ou mais "Bloco 1" (foram 10).
- [x] `gitw.py status` mostra "nada" fora da pasta.

Autoverificação das decisões (no lugar de esperar o ok do Rafael):

- **Cada decisão tem opções, escolha e número.** Sim, nas 4 perguntas acima e nas linhas do DECISIONS.
- **Alguma decisão contradiz a CLAUDE.md?** Não. Quatro listas (decisão 5), vendedor fora do score (decisão 4), validação temporal (decisão 6), página estática (decisão 1), PT-BR (decisão 7).
- **Algum número do SCOPE não tem fonte?** Nenhum. Os que exigem ajuste no bloco 2 estão em "Pendências".
- **Algum número do briefing foi repetido sem conferir?** Um estava errado (MG Special). Ver "O que deu errado", item 3.
- **O SCOPE antecipa resultados que ainda não existem?** Não cita nenhum número do modelo (joelho, P de um deal novo, contagens de Foque e Reative, métricas do backtest). Ele fixa só o desenho: métrica primária, quatro cortes, empate de até 1 ponto percentual e ajuste único.

## O que deu errado / iterações

1. **Leitura truncada do plano.** A primeira leitura parou na linha 514 de 755, no meio da E6. Li o restante antes de escrever, para o SCOPE ficar coerente com E5 e E6.
2. **Rascunho acima do limite.** A primeira versão completa do SCOPE tinha 1.772 palavras (por `-split '\s+'`; limite duro 1.300). Foram três escritas completas (1.772, 1.325 e 1.250) e uma série de edições pontuais até 1.219. O que saiu pelo caminho: os motivos entre parênteses de cada item de "fora do escopo", o item "Head de RevOps" da seção 2 (a Head aparece agora na decisão do modo teste), a citação literal do briefing, o item separado de documentação nos critérios (fundido no de código) e o preço do GTK 500.
3. **Erro factual no briefing, encontrado antes de publicar.** O briefing (seção 7) diz "MG Special tem o maior volume de deals". A primeira versão do SCOPE repetia isso ("com mais deals"). Antes de manter a frase, conferi: entre os fechados, GTX Basic tem 1.436 e MG Special 1.223 (`bloco0_eda.txt`); em todos os estágios, 1.866 contra 1.651. O SCOPE agora diz "o segundo em número de deals". Não editei o briefing (fora do escopo desta etapa); a divergência está no DECISIONS e em "Pendências".
4. **Justificativa do plano para a Q3 não se sustenta numa foto só.** Detalhado na Q3 acima. Adotei a decisão do plano e troquei a justificativa.
5. **Generalização indevida sobre os atributos.** A versão 2 do SCOPE dizia "fora da amostra, os atributos têm AUC ≈ 0,50". Isso vale só para as variáveis numéricas (cálculo direto, sem ajuste). Para os categóricos, a fase 0 só mediu um target encoding dentro da amostra, que deu 0,51 a 0,54. A versão final diz exatamente isso e chama esse valor de inflado.
6. **Afirmação sem verificação.** "Ordenar só por valor leva aos zumbis" estava assertivo. Como não calculei a composição do topo por valor, mudei para "tende a levar".
7. **Falha de ferramenta, sem efeito.** Uma tentativa de aplicar cortes ao SCOPE por um script PowerShell que procurava texto com quebra de linha CRLF falhou ("nao achei"), porque o arquivo usa LF. Nenhum arquivo foi gravado. Refiz com a ferramenta Edit.

Alternativas consideradas e descartadas, além das listadas nas perguntas:

- **Pôr as duas dores entre aspas, como fala da Head.** Descartado antes de escrever: seriam falas inventadas. O SCOPE usa "paráfrase do briefing". A frase literal do briefing (14 palavras) estava nas primeiras versões e saiu na final, por tamanho.
- **Citar o preço do GTK 500 (US$ 26.768) e a razão entre o maior e o menor preço de tabela** (US$ 55 do MG Special contra US$ 26.768). Tiraria força do argumento da Q3 e criaria números que não estão no `facts.json` planejado. O SCOPE diz só "maior preço do catálogo".
- **Fixar no SCOPE as faixas de 90 e 138 dias para Foque, Reative e Limpe.** Descartado: a CLAUDE.md pede curva estimada e limiares vindos dos dados. O SCOPE trata 90 e 138 como ponto de partida.
- **Pôr no SCOPE a tabela "critério do challenge × verificação".** Descartado por tamanho (as barras e o cabeçalho contam como palavras na checagem). Usei uma lista.

## Decisões

Dez linhas "Bloco 1" em `docs/DECISIONS.md` (linhas 19 a 28 do arquivo), todas com a marca "(decisão autônoma do Claude)":

1. Pergunta 1: quatro listas em abas, com a ordenação de cada uma.
2. Pergunta 2: tela do vendedor como padrão; o manager vê a mesma tela filtrada.
3. Pergunta 3: maior valor esperado no Foque; a justificativa do plano não foi usada.
4. Pergunta 4: o modo teste entra; Qualifique fica indisponível nele.
5. Lista "fora do escopo".
6. Tratamento de Prospecting (Qualifique, sem score) e de deal sem conta ("Conta não informada").
7. Critérios de sucesso, com a métrica primária fixada antes do código.
8. Concentração da receita citada como 83,5%, e não 83% (divergência 1 do bloco 0).
9. MG Special citado como o segundo em número de deals.
10. O SCOPE não fixa os limiares das listas.

**Fora do escopo (do SCOPE):** escrever no CRM ou integrar com ele; login; forecast financeiro; avaliação de desempenho de vendedores; score para Prospecting; tempo real; sugestão de preço ou desconto; notificações.

**Compromissos de desenho que o SCOPE assume e que os próximos blocos precisam cumprir:**

- 4 cortes de backtest; métrica primária = receita ganha capturada pelo top 20%; vencer valor, recência e aleatório (média e percentil 95 de 200 sorteios) em todos os cortes; empate de até 1 ponto percentual não vence; um único ajuste (E5).
- Teste de mutação do futuro e teste de permutação de vendedores (E4).
- Cards de 2 a 4 frases; "Como funciona" com 5 linhas; frase de ação na primeira tela; 3 deals de Foque em até 2 interações; 3 atritos corrigidos com antes e depois (E6 e E7).
- Cada lista ordenada como diz a Q1; Limpe e Qualifique por valor de tabela (E4 e E6).

## Pendências

- **Bloco 2 (`facts.py` e `test_docs_numbers`).** O SCOPE cita números que precisam existir no `facts.json`, além dos que o plano já lista: 0,51 e 0,54 (AUC do target encoding dentro da amostra; a E3 lista só "AUCs numéricas"); 63% (win rate dos fechados); 66%, 134% e 100% (razão `close_value` / tabela); 61% (win rate dos trimestres seguintes ao primeiro); US$ 1,07 mi (valor de Prospecting); 25 (fechados do GTK 500, abaixo de 100, então o teste não o confere). Se algum faltar, acrescentar o cálculo ou corrigir o texto, e registrar.
- **Bloco 2: "GTK 500".** O número 500 do nome do produto casa por coincidência com os 500 Prospecting. O teste de números deveria ignorar nomes de produto, para não aceitar um número pelo motivo errado.
- **Briefing, seção 7.** A frase "MG Special tem o maior volume de deals" está errada (GTX Basic tem mais). O briefing não foi editado. O README e o DATA_QUALITY não devem repeti-la.
- **Bloco 3.** Checar se a chance de ganho em 90 dias é estável de 0 a cerca de 90 dias nas fotos agrupadas (hipótese do plano) ou cai desde cedo (as duas fotos do briefing). A resposta muda o texto da Q3 no SCORING, não a decisão.
- **README (bloco 5).** A seção "Onde a IA errou" pode usar, como "(autocorreção na execução autônoma)", os itens 3 a 5 de "O que deu errado" acima.
- O commit do bloco 1 é feito pelo orquestrador, com a mensagem "bloco 1: escopo". Não rodei git nem `gitw.py commit`.
- Os arquivos novos (`SCOPE.md` e este log) ficam ignorados pelo `.gitignore` do repositório: o commit precisa de `git add -f`, que o `gitw.py` já faz.

## Verificação final

Rodada em PowerShell depois que os três arquivos estavam prontos.

| Critério da E2 | Comando | Resultado |
|---|---|---|
| `SCOPE.md` existe | `Test-Path docs\SCOPE.md` | True |
| 7 títulos `##` numerados | `[regex]::Matches($scope,'(?m)^## [1-7]\. ').Count` | 7 |
| No máximo 1.300 palavras | `($scope -split '\s+').Count -le 1300` | 1219, True |
| Log contém Q1 a Q4 | `-match` de cada um | True |
| DECISIONS com 4 linhas "Bloco 1" ou mais | `Select-String -Pattern 'Bloco 1'` | 10 (24 linhas de dados no total) |
| Nada fora da pasta | `gitw.py status` | "FORA da pasta da submissão: nada"; 1 arquivo não preparado (`docs\DECISIONS.md`, esperado) |

Também conferi que os tamanhos dos arquivos que não podiam ser tocados (CLAUDE.md, PROMPTS.md, GUIA.md, PROMPT_AUTONOMO.md, `docs\briefing.md`, `plano_execucao_opus.md`, `00_bloco-0.md`, `00_fase0_exploracao.md` e os três scripts) são os mesmos de antes do início, e que não há `__pycache__` na submissão. Os scripts auxiliares de contagem e de extração de números ficaram no scratchpad, fora da submissão.
