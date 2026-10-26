# Bloco 4 — ferramenta: interface e verificação

## Parte A — interface construída em paralelo (contra fixture)

### Objetivo

Construir a interface estática (`solution/app/{index.html, style.css, app.js}`), o contrato do `data.js` (`solution/app/data-contract.md`) e o script de verificação Playwright (`solution/tools/check_app.py`) ENQUANTO outro executor escreve o motor Python (`scorer/`). Sem o `data.js` real, a interface foi desenvolvida contra uma fixture de números falsos, que fica fora da submissão. A Parte B (outro executor, depois do build real) troca a fixture pelo `python -m scorer.build`, liga as checagens numéricas e faz a passada de atritos com screenshots oficiais.

### Executor

Claude Sonnet (subagente executor, em paralelo ao bloco 2/3). Especificação: seções "Bloco comum", "E6 — Bloco 4a" (itens 3 e 4) e "E7 — Bloco 4b" (item 1) de `process-log/plano_execucao_opus.md`, mais `docs/SCOPE.md` e `CLAUDE.md`.

### O que foi feito (comandos e arquivos)

1. **Leitura:** plano de execução (691 linhas; li em blocos com `offset`, até o fim da E7 e o início da E8), `docs/SCOPE.md`, `CLAUDE.md`, `scorer/fmt.py` e `scorer/config.py` (só para copiar o formato PT-BR e os nomes), cabeçalhos dos 4 CSVs de `data/raw/` (somente leitura).
2. **Contrato:** escrevi `solution/app/data-contract.md` antes do código (campos, tipos, nulos, ordem de exibição, invariantes, desvios do plano). O executor do `build.py` deve implementar exatamente aquilo.
3. **Fixture (fora da submissão):** `scratchpad\make_fixture.py` lê os CSVs reais, normaliza "GTXPro" para "GTX Pro", monta o snapshot "hoje" (31/12/2017: Engaging + 500 Prospecting) e os de teste 30/09/2017 e 30/06/2017 (deals abertos naquela data reconstruídos pelas datas, desfecho real até 31/12/2017) e grava `scratchpad\ui-dev\data.js`.
   - **Os números da fixture são falsos.** A curva é um placeholder (`P = σ(b0 + b1·max(0, idade − joelho)/30)`, com `b0`, `b1` e joelhos escolhidos à mão: 70, 90 e 95 dias; "Limpe" a partir do maior ciclo ganho até a data), o backtest é inventado (valores do protótipo do plano, rotulados `[FIXTURE]` em todo texto que vai à tela) e o `generated_by` diz "FIXTURE". Só os volumes por categoria e os desfechos reais (quem ganhou/perdeu/ficou aberto) saem dos dados; as contagens por lista de "hoje" coincidiram com o protótipo do plano (126 / 172 / 1.291 / 500) por acaso das regras escolhidas, não como validação de nada.
   - Tamanho: 3,70 MB com 6.184 deals em 3 snapshots. O campo `why` pesa 48% (1,76 MB). Aviso para o `build.py`: a meta é < 4 MB; se passar, reduzir `why` primeiro.
4. **Interface:** `index.html`, `style.css`, `app.js`. Detalhes na seção "Decisões".
5. **Verificação:** `solution/tools/check_app.py`. Cópia de trabalho em `scratchpad\ui-dev\` (3 arquivos do app + `data.js` da fixture), sincronizada com `scratchpad\sync.ps1`.
   ```
   Set-Location $SOL
   & $PY -B tools\check_app.py --app-dir "$SP\ui-dev" --shots-dir "$SP\ui-shots" --skip-numbers --prefix fixture
   ```
6. Testes auxiliares no scratchpad (nada disso vai para a submissão): `dev_shot.py` (screenshots avulsos), `contrast.py` (razão de contraste WCAG dos tokens), `mutate.py` (12 mutantes do app), `test_numbers.py` (funções numéricas com arquivos sintéticos) e `test_xss.py` (HTML hostil e nomes longos).

### Resultados

**Saída final do check contra a fixture** (exit 0; linhas longas cortadas a 175 caracteres aqui):

```
[PASSOU] estático: nenhum número escrito à mão no HTML/JS
[PASSOU] estático: contraste AA dos tokens de cor (claro e escuro) - 35 pares de cor, claro e escuro, todos >= AA
[PASSOU] estático: funciona em file:// (sem fetch, CDN ou módulos) e HTML bem formado
data.js: 3 snapshots, 6184 deals, 35 vendedores
[PASSOU] data.js obedece ao data-contract.md (somas, ordem, nulos, outcome)
[PASSOU] data-testid do plano presentes (modo hoje e modo teste) - 18 data-testid do plano presentes
[PASSOU] (a) sem filtro, modo hoje: abas = summary do data.js e frase de ação - {'Foque': 126, 'Reative': 172, 'Limpe': 1291, 'Qualifique': 500}
[PASSOU] (b) filtros vendedor/manager/região = recontagem do data.js (ordem preservada)
[PASSOU] filtros em cascata (região > manager > vendedor) e Limpar
[PASSOU] estado no location.hash (vendedor, aba, modo) sobrevive a recarregar
[PASSOU] (c) modo teste: data-n/data-pct = outcome_summary; selos; Qualifique indisponível
[PASSOU] (d) 'Como funciona' abre com exatamente 5 linhas
[PASSOU] (e) 1º card expande (2 a 4 frases, detalhes) e funciona por teclado
[PASSOU] (f) vendedor sem deals mostra o estado vazio explicativo - 5 vendedores sem deals e 3 só com fechados
[PASSOU] 'Mostrar mais' acrescenta a próxima página na mesma ordem - Limpe: 30 -> 60 de 1.291
[PASSOU] 'Carteira do time': só contagens, ordem alfabética, some com vendedor único
[PASSOU] abas navegáveis por setas/Home/End
[PASSOU] nenhuma tela mostra undefined/NaN/null - 6 telas
[PASSOU] sem data.js: aviso 'Rode python -m scorer.build'
[PULADO] numérica (a) / (b) / (c) - pulado (--skip-numbers)
[PASSOU] layout: sem rolagem horizontal, ação acima da dobra, alvos de toque >= 44px - 1280x800 e 390x844 em 5 vistas
[PASSOU] screenshots fixture_<vista>_<largura>.png - 10 arquivos
[PASSOU] console: zero erros, pageerror e requestfailed (todas as páginas abertas)

21 passaram, 0 falharam, 3 puladas, de 24 checagens
RESULTADO: PASSOU
```

**Teste dos testes (mutação).** Para saber se as checagens não passam por acaso, quebrei o app de propósito, um defeito por vez, numa cópia (`mutate.py`), e rodei o check. Os 12 mutantes foram pegos: filtro de região ignorado; expandir sem mostrar as outras frases; número escrito à mão (`'Mostrar mais 30 '`); contagem da aba +1; cards em ordem invertida; selo de desfecho removido; "Como funciona" com 4 linhas; `console.error` extra; `min-width` que causa rolagem horizontal; `min-height` de 30px nos controles; porcentagem na carteira do time; mensagem do estado vazio trocada. Mais 4 mutantes no `data.js` (soma de `summary` errada, `outcome` nulo no teste, `why` com 1 frase, `n_open` errado): todos pegos pela checagem do contrato.

**As funções numéricas** (`numbers_a/b/c`) foram testadas com arquivos sintéticos derivados da fixture (`test_numbers.py`): passam com arquivos coerentes, FALHAM com arquivo ausente (regra do plano), FALHAM com `n` ou `pct_ganhos` alterado. Elas dependem de nomes de chave que ainda não existem (ver Pendências).

**Contraste.** `contrast.py` achou 1 falha real nos tokens iniciais (linha âmbar da lista Reative a 2,77:1 contra o branco, abaixo dos 3:1 de elementos de interface). Corrigi (`#bf7600`). Depois: 35 pares, claro e escuro, todos acima de AA (4,5:1 para texto, 3:1 para bordas).

**HTML hostil.** `test_xss.py` injetou `<img onerror=...>` como nome de conta e em uma frase do `why`, mais um nome de conta de 150 caracteres sem espaço e um produto de 96 caracteres: nada executou (`window.__xss` ficou indefinido), o texto apareceu literal e não houve rolagem horizontal em 390 nem em 1280.

### O que o contrato fechou (resumo; texto completo em `app/data-contract.md`)

`window.LEAD_DATA = {meta, people, snapshots[], backtest}`.

- `meta`: `reference_date`, `horizon_days`, `generated_by`.
- `people`: `agents[] {name, manager, region, has_deals, n_open}` (os 35, inclusive os 5 sem deals), `managers[] {name, region}`, `regions[]`.
- `snapshots[]` (o 1º é o "hoje"; depois os de teste, do mais recente ao mais antigo): `date`, `mode`, `label`, `model {knot_days, p_fresh, halving_days, limpe_after_days}`, `how_it_works` (exatamente 5), `summary` (as 4 listas, com `n`, `valor_tabela`, `valor_esperado`), `outcome_summary` (só no teste: Foque, Reative, Limpe com `n`, `pct_ganhos`, `receita_ganha`) e `deals[]`.
- `deals[]` já na ordem de exibição (agrupados por categoria; Foque/Reative por valor esperado; Limpe e Qualifique por preço); a interface só filtra, nunca reordena.
- `backtest`: `headline`, `criterion_text`, `notes[]`, `metrics[] {key, label, kind}` e `rows[]` em formato longo (`cut`, `cut_label`, `method`, `method_label`, `auc`, `ganhos_top20`, `receita_top20`).

**Desvios do plano E6 item 3** (todos aditivos, justificados no contrato): `label` por snapshot; `backtest.criterion_text`, `notes` e `metrics` (este leva os títulos das tabelas, com "top 20%", para o `data.js`, para nenhum número ficar escrito à mão na interface); `outcome_summary` omitido em "hoje"; `Qualifique` com zeros no `summary` dos snapshots de teste; frações (0 a 1) em todo o arquivo.

### Autoverificação do checkpoint

- Abre em `file://` sem erro de console, `pageerror` ou `requestfailed` (todas as páginas abertas pelo check): sim, contra a fixture.
- Sem fetch, CDN, módulos ES nem build: `check_estrutura` confirma por varredura do código.
- Nenhum número escrito à mão no HTML/JS: `check_sem_numeros_a_mao` (dígitos no texto visível do HTML; datas, US$ e % literais; strings do `app.js` com número solto). Exceção declarada: `PAGE_SIZE = 30` (parâmetro de layout, o plano manda 30 por vez) e os literais `'0'`/`'1'` estruturais.
- Todos os `data-testid` do plano existem (inclusive os do modo teste); acrescentei `test-banner`, `scope-label`, `instruction`, `empty-state` (com `data-kind`), `show-more`, `shown-count`, `team-details`, `backtest-panel`, `backtest-headline`, `how-btn`, `back-to-today`, `backtest-results`, `no-data`.
- Frase de ação acima da dobra em 1280×800 e 390×844 nas vistas `inicio`, `vendedor` e `modo-teste` (o check mede `y + altura` do `action-summary` contra a altura da janela).
- Os screenshots de fixture ficaram em `scratchpad\ui-shots\` e NÃO foram salvos em `process-log/screenshots/` (os oficiais saem com dados reais, na Parte B).

### O que deu errado / iterações (erros reais, antes e depois)

Não houve erro de console em nenhuma rodada. O que apareceu foi visual, de dados vazios e do próprio check.

1. **Vendedor com mais deals abertos caía numa tela vazia.** Na fixture, Darcel Schlecht tem 194 deals abertos e 0 em Foque e 0 em Reative (83 Limpe, 111 Qualifique). Com a aba "Foque" fixa, a tela mostrava a mensagem de lista vazia. Antes: aba padrão = Foque. Depois: `aba` ausente no hash significa "automática" e abre a 1ª lista que tem deals (no modo teste, pula Qualifique); a escolha explícita da pessoa vai para o hash (`aba=Limpe`). Isso vale para a Parte B: com dados reais o vendedor "mais carregado" pode estar no mesmo caso.
2. **Vendedor sem deals: a explicação ficava abaixo da dobra.** PNG `d_semdeals_390.png` (scratchpad): 4 abas com zeros e a linha-instrução "Avance estes deals primeiro..." na frente do aviso. Depois: a frase de ação vira "Carl Lin não tem deals no CRM (cadastro sem pipeline)", as abas e a instrução somem enquanto não houver deal na seleção e o estado vazio vem logo abaixo.
3. **Tabela da carteira do time em 390px quebrava os cabeçalhos no meio da palavra** ("Foq / ue", "Reati / ve"). Causa: `overflow-wrap: anywhere` do `body` com colunas numéricas estreitas. Depois: colunas numéricas `white-space: nowrap`, padding menor e cabeçalho de .78rem em ≤ 600px.
4. **Tabelas do "Teste no passado" em 390px** quebravam as datas ("30/0 6/20 17") e as palavras dos cabeçalhos ("Orden ar por valor"), e a última coluna ficava cortada. Depois: `overflow-wrap: normal` nas tabelas e 1ª coluna com quebra só entre palavras; as 4 colunas de métodos cabem em 330px.
5. **Filtros em 768px (tablet).** "Todos os vendedores — escolha seu nome" aparecia cortado numa grade de 4 colunas. Depois: até 860px o seletor do vendedor ocupa a linha inteira e manager, região e Limpar ficam na linha de baixo.
6. **Contraste.** Linha âmbar 2,77:1 (ver Resultados) e borda dos campos e botões (`--border`) em ~1,4:1 contra o fundo (campos de formulário pedem 3:1). Depois: `--reative-l` mais escuro e um token `--control` para bordas de campos e botões (4,35:1 no claro; 5,12:1 no escuro).
7. **Detalhe do card em 390px** com rótulo em cima do valor ficava longo (7 pares, 14 linhas). Depois: duas colunas (rótulo | valor) também no celular.
8. **Screenshot com hover preso.** No PNG `card-aberto` o card seguinte aparecia tingido de verde, porque o mouse ficou parado onde o clique foi dado. Depois: `page.mouse.move(0, 0)` antes de cada captura.
9. **Falso positivo no meu próprio check.** A 1ª versão da varredura de números nas strings do `app.js` usava uma regex que misturava aspas simples e duplas e acusou `'<span class="l1">'`, `'&#39;'` e `'0'`. Depois: tokenizador de strings JS (ignora comentários e regex) e a regra "número solto" (dígito que não faz parte de um nome como `l1`), com `&#39;` e os literais `'0'`/`'1'` tolerados.
10. **Detalhes de ferramenta.** `Set-Content -Encoding utf8` do PowerShell 5.1 gravou BOM no `dev_shot.py` (o Python aceitou); o PowerShell descarta argumento vazio (`""`) ao chamar o Python, então o script de screenshot passou a usar `-` como "sem hash"; no relatório do check o hash saiu como `##vendedor=...` (corrigido).

### Decisões (todas "decisão autônoma do Claude")

- **Aba automática** (item 1 acima): hash sem `aba` = 1ª lista com deals.
- **Estado no `location.hash`** com `URLSearchParams` e `history.replaceState` (não empilha histórico a cada filtro; cai para `location.hash = ...` se o navegador recusar); chaves `vendedor`, `manager`, `regiao`, `modo` (data do snapshot; ausente = hoje) e `aba`. Um `hashchange` (hash editado à mão ou link colado) re-renderiza. Funciona em `file://` (o check recarrega a página com o hash e confere).
- **Cascata dos filtros:** região limita os managers; manager limita os vendedores; escolher um filtro mais amplo que exclui o mais estreito derruba o mais estreito (trocar de manager zera o vendedor que não pertence a ele); Limpar zera os três (mantém modo e aba).
- **Resumo do modo teste global:** os blocos `backtest-summary-<Cat>` mostram o `outcome_summary` do snapshot inteiro e não mudam com os filtros, com a frase "(todos os vendedores; os filtros não mudam estes números)". Motivo: decisão 4 do CLAUDE.md (sem taxa de vitória por vendedor; p = 0,26 entre vendedores, compatível com ruído). O desfecho de cada deal continua visível no selo do card.
- **Carteira do time** só com contagens por lista, ordem alfabética sem acento, nome do vendedor como botão que o seleciona; alerta de higiene ("Sem deals no CRM (cadastro sem pipeline)" / "Sem deals abertos"). Fica fechada com a empresa toda e abre quando há filtro de manager ou região. Some com vendedor único.
- **Seletor do vendedor:** `optgroup` "Time de {manager} — {região}"; sufixo "(sem deals no CRM)" para `has_deals=false` e "(sem deals abertos)" quando o vendedor tem deals no CRM mas nenhum no snapshot ativo (esse 2º sufixo é extra; o plano só pediu o 1º).
- **Qualifique no modo teste:** a aba continua clicável, mostra "—" e "indisponível no teste", `data-count="0"`, e o painel traz "Indisponível no modo teste: o CRM não registra quando o deal entrou em Prospecting."
- **Cards** em coluna única (a ordem da lista é o ranking; grade de 2 colunas misturaria a leitura). "Mostrar mais N" move o foco para o 1º card novo. Clique em qualquer lugar do card (fora do detalhe, e sem texto selecionado) expande; o botão interno cobre teclado e leitor de tela (`aria-expanded`, `aria-controls`). A 1ª frase do `why` é a única visível ao recolher; as demais ficam em `<p hidden>` do mesmo `card-why` (que carrega `data-n`).
- **Urgência no card:** "faltam N dias para a chance começar a cair" (Foque) e "faltam N dias para virar Limpe" (Reative), de `days_to_knot` e `days_to_limpe`, para o vendedor ver o prazo sem expandir.
- **Backtest como 3 tabelas empilhadas** (métrica principal primeiro), em vez de seletor de métrica: tudo visível, sem estado. Melhor valor da linha em negrito (inclusive quando a recência ganha em AUC) e linha do corte ativo destacada. `criterion_text` e `notes` aparecem, para a falha ou o empate não ficarem escondidos.
- **Tema escuro** via `prefers-color-scheme` (custo baixo: só tokens de cor). Todas as cores saem de variáveis CSS; um check de contraste valida os dois temas.
- **`check_app.py`:** além de (a)–(f), checagens extras: invariantes do contrato, cascata, hash, teclado, "Mostrar mais", carteira do time, nenhum `undefined/NaN/null` na tela, testids, estrutura sem fetch/CDN, varredura de números à mão, contraste e layout (rolagem horizontal, ação acima da dobra, alvos ≥ 44px). Sai com 2 (não 1) se o `data.js` não existe, para distinguir "falta o build" de "checagem falhou". A vista `vendedor` usa por padrão o vendedor com mais deals em Foque + Reative (mostra a tela principal); `--agent "Nome"` troca (o plano pede, na passada T1, o vendedor com mais deals abertos).
- **Linhas propostas para `docs/DECISIONS.md`** (o orquestrador consolida; o formato é o do plano):
  - `| 2026-10-25 | Bloco 4 — Contrato do data.js fechado em app/data-contract.md: label por snapshot, backtest.metrics/criterion_text/notes, outcome_summary só no teste, frações (0 a 1) (decisão autônoma do Claude) | só "rows + headline", como no plano | interface sem número escrito à mão: títulos de tabela e ressalvas vêm do build; um data.js de 3,70 MB na fixture (meta < 4 MB) |`
  - `| 2026-10-25 | Bloco 4 — Estado da tela no location.hash (vendedor, manager, regiao, modo, aba) com replaceState (decisão autônoma do Claude) | localStorage; um hash novo por clique | funciona em file:// e no Pages, link compartilhável, sem estado escondido; recarregar restaura (checado por Playwright) |`
  - `| 2026-10-25 | Bloco 4 — Aba padrão = 1ª lista com deals do filtro, não sempre Foque (decisão autônoma do Claude) | Foque fixo | na fixture o vendedor com mais deals abertos (194) tem 0 em Foque e 0 em Reative; a tela inicial seria vazia |`
  - `| 2026-10-25 | Bloco 4 — "Carteira do time" só com contagens, em ordem alfabética, sem taxa de vitória (decisão autônoma do Claude) | taxa de vitória por vendedor; ordenar por Limpe | decisão 4 do CLAUDE.md: diferença entre vendedores compatível com ruído (p=0,26) |`
  - `| 2026-10-25 | Bloco 4 — Resumo de resultado do modo teste é do snapshot inteiro e não muda com os filtros (decisão autônoma do Claude) | recalcular por vendedor/manager | evita taxa de ganho por vendedor com poucos deals; o desfecho de cada deal continua no card |`
  - `| 2026-10-25 | Bloco 4 — Vendedor sem deals: frase de ação vira aviso, abas e instrução somem (decisão autônoma do Claude) | mostrar 4 abas com zero | no PNG de fixture a explicação ficava abaixo da dobra do celular, atrás de 4 zeros |`
  - `| 2026-10-25 | Bloco 4 — check_app.py com checagens extras além de (a)–(f) e testado por mutação (decisão autônoma do Claude) | só as checagens do plano | 12 mutantes do app e 4 do data.js, todos reprovados pelo check; a varredura de número à mão sustenta a regra "nenhum número escrito à mão" |`
  - `| 2026-10-25 | Bloco 4 — Tema escuro por prefers-color-scheme e cores por tokens com contraste AA verificado por script (decisão autônoma do Claude) | só tema claro | custo baixo; 35 pares de cor acima de 4,5:1 (texto) e 3:1 (bordas), nos dois temas |`

### Pendências para a Parte B

1. **Gerar o `data.js` real** com `python -m scorer.build` conforme `app/data-contract.md` e rodar o check completo. O check já valida as invariantes do contrato (soma de `summary`, ordem por categoria, `n_open`, `outcome` nulo/não nulo, 2 a 4 frases): se o build divergir, é o 1º lugar onde aparece.
2. **Ligar as checagens numéricas** (sem `--skip-numbers`). `numbers_a/b/c` fazem suposições que o motor ainda não confirmou:
   - `backtest_metrics.json["hoje"]` contém, em algum nível, um dict `{Foque: {n, ...}, Reative: {...}, Limpe: {...}}` (ou uma lista de linhas com chave `categoria`/`category`/`cat`); `backtest_metrics.json["cuts"]` é uma lista em que cada corte tem a data ISO em algum valor de string e, em algum nível, a tabela por categoria com `n` e uma das chaves `pct_ganhos`, `pct_won`, `win_rate`, `taxa_ganho`, `pct_won_of_all` (fração ou porcentagem);
   - `snapshot_<data>.csv` tem as colunas `vendedor`, `manager`, `região` (ou `regiao`) e `categoria` (a comparação ignora acento e maiúsculas);
   - `docs/SCORING.md` traz o bloco `<!-- AUTO:scoring-hoje -->` com as contagens formatadas ("1.291").
   - Se os nomes reais forem outros, ajustar só `_find_cat_table`, `_pick` e `_load_snapshot_csv` em `check_app.py`.
3. **Screenshots oficiais** (`antes`, `depois`, `final`) com dados reais; `--agent` para o vendedor com mais deals abertos, se for a persona da tarefa T1.
4. **Passada de atritos (T1 a T5) com dados reais.** O que eu vi na fixture e NÃO tratei, para o executor da Parte B reavaliar com os dados reais e a sua própria passada (não são os "3 atritos" pré-escritos, só observações):
   - em 390px, com um vendedor escolhido, os filtros empilhados empurram o 1º card para depois da dobra (a linha-instrução começa em y ≈ 760 de 844 no PNG de fixture `fixture_vendedor_390.png`); a ação e as 4 abas cabem acima da dobra;
   - em 390px a linha 2 do card (score, valor, idade, chance) não cabe numa linha e "chance 40%" cai sozinha;
   - em 1280px o card ocupa a largura toda com texto só à esquerda.
5. **Tamanho do `data.js`:** fixture com 6.184 deals = 3,70 MB, 48% em `why`. Os dados reais podem passar de 4 MB; nesse caso encurtar `why` ou o `how_it_works` antes de mexer no contrato.
6. **Briefs** (`briefs/*.md`), item 5 do E6: não são desta parte.

---

## Parte B — build real, checagens com dados reais e passada de atritos

### Objetivo

Trocar a fixture pelo `python -m scorer.build` de verdade, ligar as checagens numéricas do `check_app.py`, olhar os screenshots como vendedor (tarefas T1 a T5) e corrigir os 3 atritos mais importantes, com os pares `antes_` e `depois_`.

### Executor

Claude Sonnet (subagente executor). Execução da especificação E6 (itens 2, 5 e 6) e E7 de `process-log/plano_execucao_opus.md`. As decisões marcadas "(decisão autônoma do Claude)" são do executor.

### O que foi feito (comandos e arquivos)

1. **`solution/scorer/build.py`** (novo, em funções puras): `people_section`, `build_snapshot`, `backtest_section` (adaptador do `backtest_metrics.json`), `check_contract`, `check_against_metrics`, `build_data`, `write_data_js`, `write_snapshot_csv`, `write_briefs` e `main`. A sequência do `main` é a do plano: apaga `app/data.js`, `briefs/*.md` e `data/processed/snapshot_*.csv`; `clean` (grava `deals.csv` e `facts.json`); `validate.run_backtest`; snapshots (hoje, 30/09 e 30/06); CSVs; `data.js`; briefs; `docs.inject` em todos os documentos cobertos; resumo e tamanho do `data.js`.
2. **`solution/tests/test_build.py`** (22 testes): contrato, desfechos, pessoas, `data.js` (parse de volta e determinismo), CSVs, briefs e um build completo numa pasta temporária (`--out-root`, dois builds seguidos com bytes idênticos, e remoção de saídas antigas).
3. **`solution/scorer/explain.py`**: só a linha 5 do `how_it_works`, trocando o "top 20%" escrito à mão por `config.TOP_FRAC`.
4. **`solution/app/{app.js, style.css}`**: as 3 correções de atrito (tabela abaixo). `index.html` e `data-contract.md` não mudaram.
5. **Build real:** `Set-Location $SOL; & $PY -B -m scorer.build --reference-date 2017-12-31`. Apaguei `briefs/.gitkeep` antes.
6. **Checagens:** `& $PY -B tools\check_app.py --prefix antes|depois|final` (sem `--skip-numbers`), `pytest` completo e `scorer.docs --check`.
7. **Passada T1 a T5:** li com a ferramenta Read os 10 PNGs `antes_*` e mais 6 capturas avulsas de vistas que o `check_app` não tira (Reative, Limpe e time de um manager, em 390 e 1280), feitas por um script no scratchpad (`shots.py`; ficam fora da submissão).

### Resultados

| Item | Resultado | Fonte |
|---|---|---|
| `python -m scorer.build --reference-date 2017-12-31` | exit 0 | saída do comando |
| Listas de hoje | Foque 126, Reative 172, Limpe 1.291, Qualifique 500 (2.089 deals) | `app/data.js`, igual a `backtest_metrics.json["hoje"]` (o build faz `assert`) |
| Teste 30/09/2017 | Foque 1.684, Reative 195, Limpe 530 (2.409 deals); ganhos até 31/12: 33,2%, 0,0%, 0,0% | `app/data.js` (`outcome_summary`), igual a `cuts[].categorias` |
| Teste 30/06/2017 | Foque 1.229, Reative 308, Limpe 149 (1.686 deals); ganhos: 48,5%, 4,2%, 0,0% | idem |
| Tamanho do `data.js` | 3.886.606 bytes (3,71 MB; meta: menos de 4 MB) sem encurtar nenhuma frase | `Get-Item app\data.js` |
| Briefs | 27 (vendedores com deal aberto) + `README.md` = 28 arquivos `.md` | `briefs/` |
| Snapshots CSV | `snapshot_2017-12-31.csv`, `snapshot_2017-09-30.csv`, `snapshot_2017-06-30.csv` | `data/processed/` |
| Dois builds seguidos | `data.js` com o mesmo SHA-256 | `Get-FileHash` |
| `backtest_metrics.json` depois do build | 56.954 bytes, igual ao de antes (o build o regrava, o backtest é determinístico) | `data/processed/` |
| `pytest` | 199 passed em 71 s | saída do comando |
| `scorer.docs --check` | exit 0 (5 documentos sem mudanças) | saída do comando |
| `check_app.py --prefix antes`, `depois` e `final` | 24 passaram, 0 falharam, 0 puladas, de 24 checagens, nas três rodadas | saída do comando |

As checagens numéricas (a), (b) e (c) passaram com os arquivos reais: contagens da UI = `backtest_metrics.json["hoje"]` = bloco AUTO `scoring-hoje` do SCORING; filtros da UI (vendedor Darcel Schlecht, manager Melvin Marxen, região Central) = o mesmo filtro no `snapshot_2017-12-31.csv`; modo teste: `data-n` e `data-pct` das 3 listas nos dois cortes = categorias dos cortes. As funções numéricas do `check_app.py` não precisaram de ajuste: os nomes `categorias`, `n`, `pct_ganhos`, `cut` e as colunas `vendedor`, `manager`, `regiao`, `categoria` já casavam com o que o `validate.py` e o `build.py` gravam (a busca de `_find_cat_table` achou as tabelas dentro de `hoje` e de `cuts[]`).

**Painel "Teste no passado"** (texto gerado pelo `build.py` a partir do JSON; nenhum número digitado):

- "A recência (mais recentes primeiro) tem AUC maior que o score em 3 de 4 cortes (30/06/2017, 31/08/2017, 30/09/2017)."
- "A menor vantagem do score na receita capturada sobre o melhor dos outros métodos foi de +9,2 pp (corte de 31/07/2017)."
- "A recência é instável na receita: no corte de 31/07/2017 ela capturou só 13% da receita, contra 58% do score."
- "Só entre os deals já resolvidos (fechados até 31/12/2017), o score e ordenar por valor empatam na receita capturada (diferença máxima de 0,5 pp nos cortes): a vantagem do score vem de achar os zumbis."
- "No Foque, deals com 61 dias ou mais ganharam menos em 90 dias do que os de 0 a 30 dias nos cortes de fim de trimestre: 30/06/2017 (-17,4 pp), 30/09/2017 (-41,3 pp). ... Hoje, 69 dos 126 deals do Foque estão nessa faixa."

### Passada "vendedor na segunda de manhã" (T1 a T5)

| Tarefa | O que fiz e o que atrapalhou |
|---|---|
| T1: "sou o vendedor com mais deals abertos; quais 3 deals ataco hoje e por quê?" | Zane Levy (o `check_app` escolhe quem tem mais Foque + Reative; Darcel Schlecht, com 194 deals abertos, tem 0 nas duas e cai na aba Limpe). Em `antes_vendedor_390.png` o seletor, o manager, a região e o Limpar ocupam quase metade da tela e a linha-instrução da lista começa em y ≈ 760 de 844: o 1º card não aparece. Em `antes_vendedor_1280.png` os 3 primeiros ficam visíveis, mas cada card é uma faixa de 1.060 px com uma frase de 130 caracteres à esquerda e nada à direita. O "porquê" visível é só a 1ª frase, igual em todos ("Aberto há N dias... 40% dos casos"); o que diferencia o 1º do 3º (valor) está no selo de score e no preço, na linha de cima. Anotado, não corrigido (ver Pendências). |
| T2: "o que está esfriando e quanto tempo tenho?" | `antes_reative` (scratchpad): a aba Reative mostra a instrução e, em cada card, "faltam N dias para virar Limpe". Respondeu bem; o mesmo problema da dobra em 390 px. |
| T3: "quanto do meu pipeline é lixo e o que faço?" | `antes_limpe_390` (scratchpad): a frase de ação traz "limpe 57 do CRM (US$ 127.517 parados)" e a instrução diz "Confirme com o cliente e encerre ou atualize no CRM". Respondeu. |
| T4: "no celular (390 px), consigo fazer T1?" | Não de primeira: precisa rolar. Em `antes_card-aberto_390.png`, a linha 2 do card (score, preço, idade, chance) não cabe e "chance 40%" cai sozinha numa linha; o prazo vem numa 3ª linha verde. |
| T5: "como manager, o que do meu time precisa de atenção?" | `antes_manager_1280` (scratchpad): a "Carteira do time" mostra as contagens por vendedor, em ordem alfabética, com o alerta de quem não tem deals. Dá para achar quem tem mais Limpe lendo a coluna; não há destaque nem total. Decisão de projeto (sem taxa por vendedor), anotada nas Pendências. |

### Os 3 atritos corrigidos

| # | Atrito | Antes | Correção | Depois |
|---|---|---|---|---|
| 1 | Com o vendedor escolhido, no celular o 1º card fica fora da tela (T1, T2, T4) | `antes_vendedor_390.png`: filtros empilhados e abas 2x2 altas; a linha-instrução começa em y ≈ 760 de 844 | CSS em ≤ 600 px: manager e região lado a lado, Limpar na linha do rótulo do vendedor, abas com nome e contagem na mesma linha (valor embaixo) | `depois_vendedor_390.png`: instrução em y = 571, 1º card em y = 692 e a 1ª frase visível (medido com Playwright) |
| 2 | "chance 40%" cai sozinha numa linha e o prazo vira uma 3ª linha solta (T4) | `antes_card-aberto_390.png` | `app.js`: linha 2 = score, preço, chance; linha 3 = "há N dias · a chance começa a cair em N dias" (ou "vira Limpe em N dias"), em texto corrido | `depois_card-aberto_390.png`: 3 linhas arrumadas; texto do prazo mais curto |
| 3 | Em 1280 px o card é uma faixa larga com frase de 130 caracteres, sem uso da direita, e o detalhe expandido deixa um vazio e repete o preço (T1) | `antes_card-aberto_1280.png` | CSS ≥ 900 px: card em duas colunas (cabeçalho à esquerda, frases à direita) e detalhe em 3 pares por linha; o par "Valor de tabela" saiu do detalhe (o preço já está no cabeçalho) | `depois_card-aberto_1280.png` e `depois_vendedor_1280.png`: 3 cards inteiros acima da dobra de 800 px (eram 2 e meio), com as frases numa coluna de cerca de 90 caracteres |

Os pares `antes_`/`depois_` das outras vistas (`inicio`, `modo-teste`, `como-funciona`) também existem; só mudam pelas correções acima. Todas as checagens do `check_app` continuaram verdes depois das mudanças, inclusive "ação acima da dobra" e "alvos de toque ≥ 44 px" (o Limpar absoluto e as abas compactas mantêm 44 px).

### Autoverificação do checkpoint

- [x] `python -m scorer.build --reference-date 2017-12-31` com exit 0 e `data.js` determinístico.
- [x] `pytest` completo: 199 passed. `scorer.docs --check`: exit 0.
- [x] `check_app.py --prefix final`: exit 0, 24 de 24 (incluindo as 3 numéricas, o contrato, o console sem erro, a rolagem horizontal e o toque ≥ 44 px).
- [x] PNGs `final_*_390.png` e `final_*_1280.png` (5 vistas) e 3 pares `antes_`/`depois_` com os atritos.
- [x] `data.js` abaixo de 4 MB (3,71 MB) sem encurtar frases.
- [x] `gitw.py status`: "FORA da pasta da submissão: nada"; sem `__pycache__` nem `.pytest_cache` na submissão (Python com `-B`, pytest com `-p no:cacheprovider`).
- [x] Nenhum número escrito à mão no HTML/JS (`check_sem_numeros_a_mao`) nem no texto gerado: títulos, headline, critério e ressalvas saem do JSON via `fmt`.
- [x] O vendedor não entra no score: o `build.py` não lê o vendedor para nada além de filtro e brief (e o brief diz isso no rodapé).

### O que deu errado / iterações (erros reais, antes e depois)

1. **Bloco de código morto no meu `build.py`.** Ao gravar o arquivo deixei em `outcomes_by_id` um `if ... if False else False` e um laço sem efeito, entre dois laços de verdade. A sessão foi interrompida por limite de uso da API e eu só vi isso ao retomar e reler o arquivo. Antes: dois laços (o primeiro nunca fazia nada). Depois: um laço `zip(closed, ...)`, coberto por `test_outcomes_only_count_closings_up_to_the_reference_date`. O mesmo para `snapshot_label`, que tinha dois condicionais embutidos numa f-string; passou a usar um `prefix`.
2. **`pytest` travado por mais de 5 minutos (CPU a 100%).** Na 1ª execução do `test_build.py` o 6º teste não terminava. Causa: eu escrevi `assert "nan" not in <o JSON inteiro de 3,8 MB>.lower()`. A substring "nan" existe em nomes de contas e pessoas, o assert falhava, e o pytest tentou renderizar a string de 3,8 MB na mensagem de falha. Antes: processo preso. Depois: o teste usa `json.dumps(allow_nan=False)` (que levanta erro se houver NaN) e uma regex de palavra inteira (`nan`, `nat`, `none`, `null`) só nas frases `why`. Lição: nunca afirmar sobre strings enormes dentro de `assert`.
3. **O formato do JSON do backtest era outro.** A Fase 1 foi escrita contra um formato provisório (`methods`, `cuts[].methods`). O real usa `metodos`, `categorias`, `config.method_labels` e `criterion`. Antes: o adaptador do build lia `methods`. Depois: só o bloco "ADAPTADOR" do `build.py` mudou (as chaves lidas estão listadas no comentário do bloco); `test_backtest_rows_carry_the_metrics_json_values` compara as linhas do `data.js` com o JSON real.
4. **O teste do build completo não precisou de bootstrap reduzido.** O plano previa reduzir bootstrap e sementes por parâmetro; medi `validate.run_backtest` em 7,3 s e o teste completo (2 builds) em cerca de 25 s. Removi os parâmetros `--bootstrap-reps` e `--random-seeds` que eu tinha criado na Fase 1 (não serviriam: os padrões das funções do `validate` são fixados na definição).
5. **`check_app` verde na primeira rodada real.** As funções numéricas (a), (b) e (c) não precisaram de ajuste e o `check_contrato` não achou nada no `data.js` real. Não houve bug de checagem a registrar nesta rodada.
6. **Seletores truncados em 390 px depois da correção 1.** O 1º screenshot (`tmp`, descartado) mostrou "Todos os manager" cortado nos dois seletores lado a lado. Antes: `padding` de 12 px. Depois: `padding` lateral de 8/6 px e fonte de .95rem nos seletores de filtro em ≤ 600 px (`depois_vendedor_390.png`).
7. **`test_readme.py` (do executor do README) falhou 2 vezes antes do `final`.** Ele exige `final_inicio_390.png` e `final_inicio_1280.png`; os PNGs só existem depois de `check_app.py --prefix final`. Rodei o `final` e o teste passou (199 passed). Não é bug do build.

### Decisões

13 linhas "Bloco 4" em `docs/DECISIONS.md` (as 8 propostas na Parte A, consolidadas, mais 5 desta parte), todas "(decisão autônoma do Claude)". Resumo das desta parte:

- `build.py` em funções puras, com o formato do JSON do backtest num único bloco adaptador e `assert` do contrato e das métricas dentro do build.
- `Perdido` sai com `close_value` nulo; snapshot de teste só com data anterior à referência.
- Briefs só para quem tem deal aberto (27 de 35); Foque e Reative mostram a 1ª e a 3ª frases.
- Ressalvas do painel "Teste no passado" calculadas do JSON.
- Os 3 atritos corrigidos.
- O backtest do build vale para `config.DEFAULT_REFERENCE_DATE` (limitação).

### Pendências

- **"Por quê" do Foque:** a 1ª frase de um card do Foque é a mesma para todos ("Aberto há N dias ... 40% dos casos"), porque a chance é plana até o joelho. O que diferencia o ranking (valor) está no preço e no selo de score, não na frase. Mudar a frase é trabalho do `explain.py` (por exemplo, abrir com o valor esperado) e fica para uma revisão.
- **Carteira do time:** sem destaque nem totais. Mantida assim por causa da decisão 4 (sem taxa por vendedor); um total por lista poderia entrar sem violar a decisão.
- **`--reference-date` diferente de 2017-12-31:** o `clean` aceita, mas o `validate.run_backtest` fixa 31/12/2017 em "hoje" e nos "só resolvidos"; o `assert` do build acusa a divergência em vez de gerar um `data.js` incoerente.
- **Tamanho do `data.js`:** 3,71 MB, com folga pequena. O campo `why` pesa cerca de metade; se o Foque crescer, encurtar as frases antes de mexer no contrato.
- **Linha 5 do "Como funciona" nos snapshots de teste:** mostra a média dos 4 cortes (inclusive cortes posteriores à data do snapshot). É a descrição da validação, não um parâmetro do modelo; as linhas 1 a 4 vêm do modelo do corte. Vale uma frase no SCORING.
- **Commit do bloco 4** pelo orquestrador ("bloco 4: ferramenta").