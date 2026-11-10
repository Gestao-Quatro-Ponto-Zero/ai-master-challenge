# Verificação independente — Challenge 003

**Resultado: 1 BLOQUEIA, 2 CORRIGE e 1 OBSERVAÇÃO de ambiente.** Os números centrais resistiram ao recálculo independente. A explicação de cinco negócios no passado usa fatos futuros e muda o próximo passo; a régua também anuncia um fim de prazo que não representa todos os negócios. Há ainda uma chamada incompleta na tabela de comandos.

Estado examinado: `e7f62abf5a7b50e172b0005bc82bb3147db9249f`, branch `submission/daniel-resende`. Início medido com `date`: **10/11/2026, 18:55:54 -0300**. Não consultei outra sessão nem relatório de outro verificador. `process-log/` só foi aberto depois das verificações dos itens 1–7.

Para conciliar a execução dos comandos que geram arquivos com a proibição de escrever na solução, copiei a submissão, sem `process-log/`, para `.verif/runtime/submissions/daniel-resende/`. Executei nela os comandos do README, usando Python **3.12.13**, sem instalar pacotes. Os CSVs do recálculo próprio são os originais. Todos os arquivos escritos pelo verificador e pelas execuções temporárias ficam em `.verif/`. `git diff --exit-code -- submissions/daniel-resende` retornou **0**, sem saída.

Os scripts próprios citados abaixo ficam nesta pasta. `independent.py` e `ai-independent.py` não importam código da submissão. `ui-text.cjs` executa as funções de montagem de texto de `app.js` em um DOM mínimo, expondo funções em memória e desativando apenas a inicialização da página; **não é um navegador nem prova de layout**. Node é uma ferramenta do verificador, não uma dependência acrescentada à solução.

## Achados

### 1. BLOQUEIA — explicação histórica usa janeiro e troca a ação do score

**Afirmação atacada:** a segunda do passado usa apenas o que se sabia naquela data; a IA só redige o próximo passo escolhido pelo score; os textos existem somente para a segunda padrão.

**Comando exato, da raiz do clone:**

```bash
node .verif/ui-text.cjs
```

**Saída observada, seção `PAST_TOOLTIP_WITH_AI GWOOPZE8`:** na segunda **02/10/2017**, Cassey Cress, negócio `GWOOPZE8`, a mesma explicação contém:

```text
Próximo passo: Confirmar esta semana se segue de pé, porque está com o prazo acabando e faltam 47 dias de prazo.
Aberto há 0 dias; 138 dias restantes no prazo, até 17/02/2018.
O negócio de GTX Plus Basic com Cheers está aberto há 91 dias, e faltam 47 dias de prazo. [...] Cerca de 26 em cada 100 [...] (conta de 31/12/2017).
Cerca de 51 em cada 100 [...] (conta de 01/10/2017).
```

O score histórico traz `days_open=0`, `days_left=138`, `cooling=false`, `play=trabalhar`. Com a IA ausente, o mesmo comando produz **“Próximo passo: Trabalhar esta semana.”**, coerente com esse score.

**Deveria sair:** idade 0, 138 dias restantes, ação `trabalhar` e conta de 01/10/2017. Os fatos de janeiro não deveriam participar dessa explicação. A evidência futura tem lugar identificado em `after`; aqui ela entra como descrição e orientação da própria segunda histórica.

**Causa e alcance:** `app.js:196` busca `reason` e `next_step` somente pelo ID do negócio, sem conferir a segunda de `textos.json`; a linha 202 prefere o texto da IA ao `PLAY[d.play]`. Há cinco negócios afetados em 02/10: `GWOOPZE8`, `EM1BA4EK`, `GXIVJQPG`, `MG1YUTUE`, `QNB3SCN9`. Todos têm idade histórica 0 e texto com idade 91. Não encontrei esse vazamento nos blocos ou na ordem dos arquivos do score: o defeito é na orientação apresentada pela interface.

### 2. CORRIGE — régua anuncia 138 dias como fim do prazo, ignorando o outro limite

**Afirmação atacada:** a linha do tempo representa o prazo do negócio, que termina pelo primeiro dos limites: idade máxima ou fim do trimestre seguinte.

**Comando exato:**

```bash
node .verif/ui-text.cjs
```

**Saída observada:**

```text
BORIS_TIMELINE_LABELS ... abriu agora 90 fim do prazo: 138 dias ponto = negócio no prazo
QUARTER_TRUNCATES_MAX_AGE 34 of115
```

O registro `BORIS_NGTVHTFH`, emitido pelo mesmo comando, tem `days_open=12`, `days_left=89`, `deadline=2018-03-31`, `window_end=2018-03-31`. Pela idade máxima isolada faltariam **126** dias; o prazo efetivo é menor por causa do trimestre. Isso acontece em **34 dos 115** negócios no prazo da segunda padrão.

**Deveria sair:** a régua deveria distinguir o limite máximo por idade do fim efetivo de cada negócio, ou declarar junto dela que o trimestre pode encerrar o prazo antes. A tabela individual calcula 89 corretamente; o rótulo da figura sugere outro horizonte. `app.js:222` posiciona o ponto só pela idade, e a linha 242 chama o limite comum de **“fim do prazo”**. Essa divergência textual é verificável sem render; a percepção visual em navegador permanece indeterminada.

### 3. CORRIGE — chamada de confirmação abreviada não executa como escrita

**Afirmação atacada:** a tabela oferece comandos para rodar da raiz. Na linha da validação, oferece `python3 submissions/daniel-resende/solution/validate.py` e, como segundo trecho de código, apenas `confirm.py`.

**Comando exato**, executado de `.verif/runtime/`, a raiz da cópia temporária:

```bash
confirm.py
```

**Saiu:** `/bin/bash: line 1: confirm.py: command not found`, **exit 127**.

**Deveria sair:** a confirmação executada por uma chamada completa de Python e caminho, como as demais linhas da tabela. A chamada expandida `python3.12 submissions/daniel-resende/solution/confirm.py` funciona, exit 0, mas exige que o leitor complete a instrução. Registro como defeito documental pela exigência desta verificação de seguir a tabela literalmente, sem adivinhar comandos; não é falha do script de confirmação.

### 4. OBSERVAÇÃO — comando principal não abriu a porta 8000 neste ambiente

**Afirmação atacada:** o comando do README inicia o aplicativo em `127.0.0.1:8000`.

**Comando exato executado da raiz, na cópia temporária:**

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 -u .verif/runtime/submissions/daniel-resende/solution/run.py --port 8000
```

**Saiu:** os seis arquivos de score e o índice foram construídos, depois `OSError: [Errno 98] Address already in use`, **exit 1**.

**Deveria sair:** servidor iniciado nessa porta. A porta já ocupada é uma restrição do ambiente, não um defeito demonstrado da submissão. Não abri nem investiguei o serviço que a ocupava. O mesmo programa com `--port 8765`, executado de `.verif/runtime/`, iniciou e serviu os arquivos com HTTP 200. A porta 8000 ficou, portanto, **INDETERMINADA** como teste completo de execução neste clone.

## Setup e comandos da tabela

Diretório de execução dos comandos abaixo: `.verif/runtime/`. Prefixo comum: `PYTHONDONTWRITEBYTECODE=1`. Nenhuma instalação; `requirements.txt` tem **0 bytes**.

| Comando executado | Resultado medido |
|---|---|
| `python3.12 submissions/daniel-resende/solution/build.py` | exit 0; seis scores e índice |
| `python3.12 submissions/daniel-resende/solution/check_contract.py` | exit 0; contrato e seis segundas conferidos |
| `python3.12 -m unittest discover -s submissions/daniel-resende/solution/tests` | exit 0; 21 testes |
| `python3.12 submissions/daniel-resende/solution/numbers.py` | exit 0; números do README reproduzidos |
| `python3.12 submissions/daniel-resende/solution/drift.py` | exit 0; janela estável |
| `python3.12 submissions/daniel-resende/solution/validate.py` | exit 0 |
| `python3.12 submissions/daniel-resende/solution/confirm.py` | exit 0 |
| `python3.12 submissions/daniel-resende/solution/ai/check.py` | exit 0; 148 textos, 0 falhas |
| `python3.12 submissions/daniel-resende/solution/ai/generate.py` | exit 0; 0 itens a gerar, 148 já armazenados; nenhuma chamada ao modelo |

Saídas integrais: `command-1.txt` a `command-9.txt`, nessa ordem. Também executei `python3.12 submissions/daniel-resende/solution/audit.py`, exit 0. O `confirm.py` foi executado com seu caminho completo: o nome aparece abreviado na tabela do README, ao lado de `validate.py`.

O servidor alternativo respondeu HTTP **200** para `/`, `/app.js`, `/out/index.json`, `/out/score-2018-01-01.json`, `/ai/textos.json`, fonte WOFF2 e imagem clara. Foi encerrado pelo verificador após a inspeção HTTP. Isso verifica entrega dos recursos, não execução do JavaScript em navegador.

## Recálculo próprio dos CSVs

**Comando:** `python3.12 .verif/independent.py`, **exit 0**; saída integral em `independent-output.txt`. Lê os quatro CSVs: **8.800 oportunidades, 85 contas, 7 produtos e 35 vendedores**. Não soma negócios repetidos entre cortes: usa conjuntos de IDs.

Maior duração de ganho: **138 dias**. Fechamentos depois do trimestre seguinte: **1 de 6.711**, portanto **6.710 dentro**. A exceção é `Q7C5MJ4W`, **Lost**, engajado em 30/06/2017 e fechado em 01/11/2017. Confere com o README.

Em cada corte, o máximo foi aprendido somente com ganhos já fechados até ali; foi 138 em todos. Abertos foram reconstruídos pela entrada até o corte e ausência de fechamento conhecido até o corte.

| Corte | Vencidos no corte | Ganhos em qualquer momento até o fim dos dados |
|---|---:|---:|
| 2017-06-01 | 84 | 0 |
| 2017-06-16 | 109 | 0 |
| 2017-07-01 | 350 | 0 |
| 2017-07-08 — confirmação | 350 | 0 |
| 2017-07-16 | 350 | 0 |
| 2017-08-01 | 350 | 0 |
| 2017-08-16 | 350 | 0 |
| 2017-08-24 — confirmação | 384 | 0 |
| 2017-09-01 | 411 | 0 |
| 2017-09-16 | 471 | 0 |
| 2017-09-24 — confirmação | 504 | 0 |
| 2017-10-02 | 717 | 0 |

**União dos doze cortes:** **717 distintos**, **0 ganhos, 1 perdido, 716 abertos**. **União somente das três confirmações:** **504 distintos**, **0 ganhos, 0 perdidos, 504 abertos**. O README informa corretamente os 717; o segundo total está na saída de `confirm.py`. Não interpretei a confirmação como independente: o README declara expressamente a sobreposição e o desenho da regra após observar o dataset completo.

| Segunda padrão, corte 31/12/2017 | Recálculo | Valor de tabela |
|---|---:|---:|
| No prazo | 115 | US$ 235.930 |
| Para iniciar, sem data | 500 | US$ 1.073.986 |
| Vencidos | 1.474 | US$ 3.656.299 |

Também conferiram independentemente: **1.425 de 2.089** abertos sem conta; **18 de 35** vendedores sem negócio no prazo; Central com todos os **500** para iniciar e nenhum no prazo; East com **45** e West com **70** no prazo; **52 empates em 98 pares vizinhos**; **7 preços**.

A tabela do tempo também foi refeita: **4.767** negócios no grupo elegível; aos **0/30/60/90/120/138** dias, **47/42/39/26/4/0** ganhos por 100. Aos 90 dias, os recálculos de agosto e outubro deram **38 e 33**, respectivamente.

Os seis valores de ganho no top 5 citados no README foram reproduzidos por `numbers.py` e `confirm.py`: **432.044/396.111**, **321.094/295.729**, **238.551/229.454**. Essa parte é reprodução dos scripts da submissão, não uma segunda implementação do ranking experimental. Nenhum número quantitativo de resultado do README ficou sem script identificado. `python3.12 .verif/integrity.py`, exit 0, confirmou igualdade byte a byte das saídas guardadas de números, validação e confirmação com as execuções desta verificação.

## O que tentei quebrar e resistiu

- **Reconstrução temporal e blocos:** `python3.12 .verif/independent.py`, exit 0. Comparei todos os IDs dos seis arquivos emitidos, não só os totais: **0 divergências**. Em 02/10/2017, corte 01/10, eram **2.434 abertos: 1.717 no prazo e 717 vencidos**. Nas cinco segundas antigas, vencidos **92/350/350/420/717**, na ordem cronológica, sem ganhos posteriores.
- **Vazamento para bloco, ordem ou ação no núcleo:** `PYTHONDONTWRITEBYTECODE=1 python3.12 .verif/leakage.py`, exit 0. Alterei em memória data e valor de fechamento, etapa final e duração de **1.973 fechamentos futuros**, além da conta nas **8.800** linhas. Blocos, posições e `play` de 02/10 ficaram iguais. A leitura de `world_at`, `fit_rules`, `is_dead` e `build_monday` é coerente com essa prova: o desfecho conhecido serve ao ajuste histórico; desfecho futuro não entra na ordenação; conta só aparece para exibição. O achado 1 ocorre depois, na interface.
- **Dia exato do prazo:** `python3.12 .verif/independent.py`, exit 0: `0OESOJNN`, James Ascencio, permanece no prazo em **05/06/2017**, com idade 138 no corte e `window_end` nessa segunda. `leakage.py` também testa em memória um caso sintético de limite trimestral na própria segunda: **31/12/2018**, `alive`, `days_left=0`; na segunda seguinte, `clean`. Não acrescentei esse caso aos CSVs.
- **Fechados como trabalho:** a comparação de todos os IDs dos seis scores excluiu todos os negócios fechados até o respectivo corte. Negócios que fecharam depois aparecem corretamente na reconstrução histórica, com desfecho identificado em `after`.
- **Gestor e vendedores:** `independent.py`, exit 0, comparou somas dos vendedores a cada gestor, regional e total nos seis arquivos, incluindo valores e contagem de prazo acabando; nenhuma divergência. A ordem dos negócios no prazo também confere com valor, dias restantes e ID.
- **Estados vazios e conta ausente:** `node .verif/ui-text.cjs`, exit 0. Anna Snelling: **0/55/57**, orienta começar pelos negócios para iniciar. Kary Hendrixson: **12/0/91**, declara não haver negócio para iniciar. Carl Lin: **0/0/0**, declara ausência dos três grupos. Carl também está entre os cinco vendedores sem qualquer linha no CRM, além de estar entre os oito sem trabalho aberto. Os registros sem conta carregam `null`/`sem_conta`; `dealTip` mostra “sem conta registrada”, sem inventar cliente. Há **80** negócios no prazo sem conta na segunda padrão.
- **Percentual por negócio:** leitura de `app.js` e execução de `ui-text.cjs`: não há percentual individual. A conta por faixa aparece com data e a frase explícita “não é a chance deste negócio”. Isso não elimina a contradição temporal do achado 1.
- **Regra congelada:** `sha256sum submissions/daniel-resende/solution/validate.py`, exit 0: **336760fdcc511cde2ad5d28e9437dd0b061a222b18f2f5f03e2a38164abca212**, igual ao hash fornecido.

## Vendedor sem treinamento — leitura em três linhas

Trabalhar os negócios “No prazo”, seguindo a lista e abrindo a explicação para ver o próximo passo.  
Iniciar os negócios “Para iniciar” e registrar a data; se essa lista estiver vazia, não há nada nela para começar.  
Encerrar os “Vencidos” no CRM; se os três grupos estiverem vazios, a página não apresenta trabalho.

Essa é minha interpretação das palavras de `app.js`, inclusive explicações abertas; não é resultado de entrevista com vendedor. **INDETERMINADO** quais palavras um vendedor real desconheceria. O vocabulário que exige repertório é: **pipeline, CRM, engajar/engajados/engajamento, IA, ID**, a notação **US$** e os nomes técnicos dos produtos (**GTK 500, GTX Basic, GTX Plus Basic, GTX Plus Pro, GTX Pro, MG Advanced, MG Special**). “Preço/valor de tabela”, “prazo acabando” e o prazo do trimestre têm explicação acessível pela interface. A primeira vista informa a lista; a ação dos negócios no prazo aparece na explicação ou no resumo.

## Textos de IA

`python3.12 .verif/ai-independent.py`, **exit 0**: **148 alvos, 263 partes e 1.374 marcadores**. Comparei todos os fatos com os scores emitidos, refiz o preenchimento, conferi ausência de dígitos fora de marcadores e presença de modelo e data em todos os registros. São **115 negócios, 27 vendedores e 6 gestores**.

Escolhi e li **30 textos**: 20 negócios distribuídos pelo arquivo, 7 resumos de vendedores e 3 gestores, identificados em `ai-independent-output.txt`. Incluem conta presente/ausente e prazo acabando. Nessa amostra não encontrei julgamento de chance, promessa de fechamento ou ação além do bloco, da ordem e do próximo passo permitidos. Também examinei os modelos de frase distintos. A observação é sobre o conteúdo de janeiro; não valida seu uso no passado.

Depois dessa conferência rodei novamente `PYTHONDONTWRITEBYTECODE=1 python3.12 submissions/daniel-resende/solution/ai/check.py`, de `.verif/runtime/`: **exit 0, “148 texts, 0 failures”**. O check próprio não detecta o achado 1 porque valida o arquivo contra janeiro, sem testar a seleção da segunda na interface.

## Processo, repositório e pendências

Somente ao final li `process-log/DIARIO.md`, os inícios dos prompts e o registro do baseline. Comandos: `cat submissions/daniel-resende/process-log/DIARIO.md`, `head -n 8 submissions/daniel-resende/process-log/prompts/*.md` e `head` dos arquivos de baseline, todos **exit 0**. O diário identifica ferramentas e papéis, liga prompts às etapas e descreve erros e correções: por exemplo, cálculo que excluía negócios nunca fechados, contagem duplicada entre cortes e problemas de concordância dos textos. Há prompts de correção correspondentes. Isso demonstra a documentação desses acontecimentos; não autentica por si só cada hora ou saída narrada. As cópias declaradas como **Trecho** não foram tratadas como falha.

`python3.12 .verif/integrity.py`, **exit 0**: **100 caminhos versionados**, 79 arquivos textuais examinados; nenhum padrão de chave das famílias verificadas e nenhuma pasta de ambiente/cache/saída de build versionada. Valores que parecessem segredo não seriam impressos. A busca cobre formatos usuais de chaves OpenAI/Anthropic, AWS, GitHub, Slack e cabeçalhos de chave privada; não prova ausência de qualquer segredo de formato desconhecido.

**INDETERMINADO — comparação exigida com upstream:** `git show-ref --verify refs/remotes/upstream/main` retornou **128**, referência ausente. Não fiz fetch nem qualquer operação que alterasse Git. Como verificação adicional, `git diff --name-only origin/main HEAD`, **exit 0**, encontrou **89 caminhos**, todos dentro de `submissions/daniel-resende/`; `origin/main` é `4aed364d572fabe0f1fff1f0c6f32960b30fe575`. Falta a referência exigida para afirmar que essa base é exatamente `upstream/main`.

Comparação com `templates/submission-template.md`, via `cat` do template e README, **exit 0**: ainda estão sem preenchimento efetivo **Ferramentas usadas**, **Workflow**, **Onde a IA errou e como corrigi**, **O que eu adicionei que a IA sozinha não faria** e **Evidências**. O contêiner **Process Log — Como usei IA** conserva a instrução do template; a data de envio segue `[data]`. **São pendências da etapa final, não achados nesta rodada**, conforme o escopo pedido.

**INDETERMINADO — página renderizada:** a tentativa `cua.createBrowserTab("iab", "http://127.0.0.1:8765/", { visible: false })` retornou **“The browser access host is unavailable”**. Não inspecionei a renderização, cliques reais, rolagem, teclado, temas nem celular. Os testes de produto acima usam os arquivos emitidos e as palavras/funções de `app.js`, como permitido no pedido. Capturas do processo não substituíram observação própria da versão executada.

**INDETERMINADO — nova geração pelo modelo:** o comando de geração foi executado, mas fez zero chamadas por encontrar todos os textos armazenados. Não apaguei textos nem forcei regeneração; portanto não confirmei instalação/login do Claude Code ou uma nova resposta do modelo.

**Tempo real gasto: 12.63 minutos (12 min 38 s).** Encerramento medido com `date`: 2026-11-10T19:08:32-03:00.
