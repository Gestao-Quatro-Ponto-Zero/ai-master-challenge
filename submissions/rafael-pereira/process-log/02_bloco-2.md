# Bloco 2 — curadoria de dados, investigações 2a, 2b e 2c e infraestrutura de números

## Objetivo

Deixar a base limpa, reprodutível e documentada, sem nenhum scoring ainda, e montar a infraestrutura "todo número sai de script": `config`, `fmt`, `clean`, `facts` e `docs`, mais os testes que comparam o texto dos documentos com os arquivos gerados. Decidir, com número e critério definido antes de olhar o resultado, as investigações 2a (win rate de 82% no 1º trimestre de 2017), 2b (vendedores sem deals) e 2c (`close_value` contra preço de tabela). Zerar também as pendências que o bloco 1 deixou para este bloco.

## Executor

Claude Sonnet (subagente executor). Execução da especificação E3 de `process-log/plano_execucao_opus.md`, planejada pelo Claude Opus em modo somente leitura. Nenhuma pergunta foi feita; as decisões abaixo são do executor (decisão autônoma do Claude).

## O que foi feito (comandos)

1. **Leitura.**
   - Plano de execução (755 linhas): li em duas chamadas, linhas 1 a 400 e 400 a 755, sem truncamento. Li também E4 a E12, só para saber como `clean.py`, `config.py`, `fmt.py`, `facts.json` e `docs.py` serão usados; nada dessas etapas foi implementado.
   - `CLAUDE.md` (no contexto), `docs/briefing.md`, `docs/SCOPE.md`, `PROMPTS.md` (bloco 2), `PROMPT_AUTONOMO.md`, `process-log/00_fase0_exploracao.md`, `process-log/01_bloco-1.md` (seção Pendências), `docs/DECISIONS.md`, `process-log/00_bloco-0.md` (primeiras 60 linhas, para o formato).
   - Scripts de referência `process-log/scripts/{eda,eda2,snapshot}.py` e as saídas `process-log/outputs/bloco0_*.txt` (só leitura).
   - Cabeçalhos dos 4 CSVs brutos em `solution/data/raw`.
2. **Exploração descartável** (scripts no scratchpad, fora da submissão): `explore2.py` calculou os meses de fechamento, as coortes, o cruzamento de trimestres, os vendedores sem deals e a razão `close_value` / tabela, para eu escolher a forma dos critérios. Nada foi gravado em `$SUB`.
3. **Código** em `solution/scorer/`: `__init__.py`, `config.py`, `fmt.py`, `clean.py`, `facts.py`, `docs.py`. Funções puras, com docstring curta; `clean.py` não altera DataFrames de entrada (testado).
4. **Primeira geração:** `Set-Location $SOL; & $PY -B -m scorer.clean`. Inspecionei o `facts.json` inteiro e os blocos AUTO renderizados.
5. **Documentos:** `docs/DATA_QUALITY.md` (tabela de 11 linhas, seções 2a, 2b e 2c, vazamento por conta ausente; 8 blocos AUTO) e 10 linhas "Bloco 2" no `docs/DECISIONS.md` (sem apagar nenhuma). `docs/SCOPE.md` não foi alterado: todos os seus números casaram.
6. **Testes:** `test_clean.py` (12), `test_docs_numbers.py` (11), `test_facts.py` (6) e `test_fmt.py` (11). Os dois últimos não estavam na lista da E3; entraram porque os números de `facts.json` e a formatação são o contrato dos blocos seguintes.
7. **Verificações extras** (scratchpad):
   - `python -m scorer.clean` duas vezes: SHA-256 de `deals.csv` e de `facts.json` idênticos nas duas.
   - `--reference-date 2017-09-30 --out-dir <scratchpad>`: roda sem erro com outra data (não toca em `data/processed`).
   - Mutação do verificador: troquei um número de cada vez nos documentos reais (6 trocas) e o `unmatched_numbers` acusou as 6 (ver "Resultados").
8. **Limpeza:** apaguei os `.gitkeep` de `scorer`, `tests` e `data/processed` (as pastas ganharam arquivos). Rodei Python com `-B` ou `PYTHONDONTWRITEBYTECODE=1` e o pytest com `-p no:cacheprovider`; conferi no fim que não há `__pycache__` nem `.pytest_cache` na submissão.

## Resultados

### Arquivos criados ou alterados

- Novos: `solution/scorer/{__init__,config,fmt,clean,facts,docs}.py`; `solution/tests/{test_clean,test_docs_numbers,test_facts,test_fmt}.py`; `solution/data/processed/{deals.csv,facts.json}`; `docs/DATA_QUALITY.md`; este log.
- Alterado: `docs/DECISIONS.md` (34 linhas de dados no total; as 10 últimas são "Bloco 2").
- Removidos: 3 arquivos `.gitkeep` (aparecem como exclusões no `gitw.py status`).

### Saída dos comandos (cwd `$SOL`)

| Comando | Resultado |
|---|---|
| `& $PY -m scorer.clean` | exit 0; "deals.csv: 8800 linhas, 23 colunas"; deals abertos 2.089 |
| `& $PY -m scorer.docs` | exit 0; `DATA_QUALITY.md` e `SCOPE.md` "sem mudanças" (na primeira vez, `DATA_QUALITY.md` foi "atualizado": os blocos AUTO estavam vazios) |
| `& $PY -m pytest -p no:cacheprovider` | exit 0; 40 passed in 1.71s |
| `& $PY -m scorer.docs --check` | exit 0 |
| `(Import-Csv "$SOL\data\processed\deals.csv").Count` | 8800 |
| `& $PY "$PM\tools\gitw.py" status` | "FORA da pasta da submissão: nada"; 4 não preparados (`DECISIONS.md` e os 3 `.gitkeep` removidos) |

### Números reproduzidos (fonte: `solution/data/processed/facts.json`)

| Item | Esperado (plano ou briefing) | Calculado | Chave em `facts.json` |
|---|---|---|---|
| Estágios | 4.238 / 2.473 / 1.589 / 500 | 4.238 / 2.473 / 1.589 / 500 | `pipeline.deals_por_estagio` |
| Win rate dos fechados | 63,2% | 0,6315 | `pipeline.win_rate_fechados` |
| Linhas GTXPro | 1.480 | 1.480 | `qualidade.linhas_gtxpro` |
| Setor com erro | "technolgy" | 12 contas, 1.165 deals | `qualidade.contas_com_setor_technolgy` |
| Sem conta | 1.425 = 1.088 + 337; 0 fechados | 1.425 = 1.088 + 337; 0 fechados; 68,2% dos abertos | `qualidade.sem_conta` |
| Prospecting sem data | 500 | 500 | `qualidade.prospecting_sem_engage_date` |
| Vendedores | 35 / 30 / 5 | 35 / 30 / 5 | `evidencia_2b_vendedores` |
| Ciclo máximo; medianas ganho / perdido | 138; 57 / 14 | 138; 57 / 14 | `ciclos` |
| Perdidos em até 14 dias | 1.249 | 1.249 | `ciclos.perdidos_ciclo_rapido` |
| Qui-quadrado produto / vendedor | 0,37 / 0,26 | 0,3719 / 0,2639 | `atributos.qui_quadrado_p` |
| Correlação do vendedor H1 x H2 | 0,57 | 0,5727 | `atributos.correlacao_vendedor_h1_h2` |
| AUC das numéricas | cerca de 0,50 | 0,493 a 0,498 | `atributos.auc_numericas` |
| Faixas de idade em 31/12 | 110 / 188 / 1.291 | 110 / 188 / 1.291 | `idade_hoje.faixas` |
| Valor dos 1.291 / do Engaging | 3.198.664 / 3.892.229 | 3.198.664 / 3.892.229 | `idade_hoje` |
| Prospecting | US$ 1,07 mi | 1.073.986 | `prospecting.valor_tabela` |
| Concentração top 3 | 83,5% | 0,8352 | `produtos.receita_ganha_top3_share` |
| Snapshot 30/09, `pct_ganhos` | 0,502 / 0,343 / 0,067 / 0 / 0 | 0,502 / 0,343 / 0,067 / 0 / 0 | `fotos_do_briefing.2017-09-30` |
| Snapshot 30/06, `pct_ganhos` | 0,529 / 0,445 / 0,216 / 0 | 0,529 / 0,445 / 0,216 / 0 | `fotos_do_briefing.2017-06-30` |

Pendências herdadas do bloco 1, todas cobertas em `facts.json`:

| Número do SCOPE | Chave | Valor |
|---|---|---|
| 0,51 e 0,54 (AUC de target encoding na própria amostra, inflado) | `atributos.auc_categoricas_target_encoding_na_amostra_inflado` | 0,5068 (região) a 0,5401 (vendedor) |
| 63% | `pipeline.win_rate_fechados` | 0,6315 |
| 66%, 134%, 100% | `evidencia_2c_close_value.geral` | mín. 0,6573; máx. 1,3418; média 0,9965 |
| cerca de 61% | `evidencia_2a_q1.win_rate_depois_do_primeiro_trimestre` | 0,6113 |
| US$ 1,07 mi | `prospecting.valor_tabela` | 1.073.986 |
| 25 fechados do GTK 500 | `produtos.deals_fechados_do_produto_maior_preco` | 25 |
| 83,5% | `produtos.receita_ganha_top3_share` | 0,8352 |
| GTX Basic acima de MG Special em deals | `produtos.deals_por_produto` e `deals_fechados_por_produto` | 1.866 contra 1.651 (todos) e 1.436 contra 1.223 (fechados) |

### Investigações: critério, número, decisão

| Investigação | Critério (definido antes de olhar o resultado) | Número medido | Decisão |
|---|---|---|---|
| 2a (i) | O 1º trimestre só tem fechamentos em março | 0 fechamentos fora de março; 647 no trimestre | Vale |
| 2a (ii) | Win rate de março a até 5 pp da média de jun, set e dez | 82,1% contra 80,2% (+1,9 pp) | Vale |
| 2a (iii) | Ciclo mínimo de cada coorte engajada antes do 1º fechamento a até 7 dias do piso do recorte | Folgas de 2, 5, 3, 7 e 4 dias (ciclos mínimos 123, 96, 63, 36 e 5); maior folga 7 | Vale no limite (ver "O que deu errado", item 3) |
| 2a, veredito | As três condições | Artefato de recorte confirmado | (a) win rate por trimestre só com ressalva; (b) fotos de treino a partir de 31/03/2017; (c) 28/02 só como sensibilidade no bloco 3; (d) artefatos do gerador documentados e não explorados |
| 2b | Zero deals em qualquer estágio = "cadastro sem pipeline" | 35 no cadastro, 30 com deals, 5 sem; 27 com deal aberto; 3 só com fechados | Os 5 aparecem no filtro sob o manager com "(sem deals no CRM)", na "Carteira do time" com zeros e alerta, sem brief (o índice de briefs os lista); os 3 só com fechados mostram "sem deals abertos" |
| 2c | Média por produto em [0,95; 1,05] e variação entre trimestres de até 3 pp | Média por produto de 0,985 a 1,004; variação de 0,46 pp (0,5 pp) | Vale: o valor do deal aberto é `sales_price`; `close_value` só como desfecho no backtest |
| Vazamento | Sem conta = nunca fechou? | 1.425 sem conta, todos abertos | `has_account` e qualquer categoria "desconhecido" de setor ou porte ficam proibidos como variável |

Evidências completas (mês a mês, coortes, cruzamento, posição no trimestre, razão por produto e trimestre, lista dos vendedores) estão nos blocos AUTO de `docs/DATA_QUALITY.md`.

### Divergências em relação ao esperado no plano

- **Cruzamento de trimestres.** O plano esperava "só Q ou Q+1". Há 1 exceção: um deal engajado no 2º trimestre de 2017 e fechado no 4º. As demais 6.710 linhas seguem a regra (3.522 no mesmo trimestre, 3.188 no seguinte). A exceção está no `facts.json` (`fechados_fora_da_regra_q_q1`) e no DATA_QUALITY.
- Todo o resto bateu com o esperado, inclusive os 10 win rates mensais (Mar 82,1%, Abr 48,6%, Mai 54,4%, Jun 82,8%, Jul 49,1%, Ago 56,8%, Set 79,2%, Out 49,3%, Nov 52,9%, Dez 78,5%), os ciclos mínimos das coortes (123, 96, 63, 36, 5), os 27 vendedores com deal aberto, os 5 sem deals (um por time, menos o de Dustin Brinkmann), os 3 só com fechados (Donn Cantrell, Garret Kinder, Reed Clapper) e a razão média 0,996 (mín. 0,657, máx. 1,342).
- **Dois achados além do plano**, que reforçam a decisão e entraram no DATA_QUALITY: (1) todos os 1.779 fechamentos do 1º mês de cada trimestre (abr, jul, out) têm ciclo de até 14 dias, mediana 7, e 49,0% de win rate, contra 80,7% no 3º mês; (2) o win rate das coortes antigas cai do 100% (out/2016, só 7 deals) para 66% (fev/2017), o gradiente que se espera quando o recorte tira os fechamentos rápidos, que têm win rate menor (0,535 nos ciclos de até 7 dias contra 0,756 acima de 120, em `process-log/outputs/bloco0_eda.txt`).

### Verificador de números: o que ele aceita e o que acusa

Nos documentos reais, 0 números sem fonte: `DATA_QUALITY.md` com 50 tokens conferidos e `SCOPE.md` com 38. Troquei um número de cada vez, em cópia na memória, para ver se o verificador acusa:

| Troca | Acusado? |
|---|---|
| DATA_QUALITY: "1.480" por "1.840" | sim (linha 9) |
| DATA_QUALITY: "82,1%" por "82,3%" | sim |
| DATA_QUALITY: "US$ 3,2 mi" por "US$ 3,3 mi" | sim |
| DATA_QUALITY: "1.088" por "1.089" | sim |
| SCOPE: "83,5%" por "84,5%" | sim |
| SCOPE: "US$ 1,07 mi" por "US$ 1,7 mi" | sim |

Limites do verificador (decisão registrada no DECISIONS): só confere inteiros a partir de 100 (ou com ponto de milhar), US$, porcentagens e decimais com vírgula; aceita o token se algum valor de `facts.json` ou de `ALLOWED_CONSTANTS`, arredondado à precisão exibida, bater. Isso prova que o número existe nos fatos, não que está no contexto certo. Contagens pequenas como "25 deals" ou "30 vendedores" não são conferidas pelo texto; os fatos por trás delas estão em `test_facts.py`.

## Autoverificação do checkpoint

O PROMPTS manda mostrar o resumo de 2a, 2b e 2c e esperar o ok do Rafael; no modo autônomo, o resumo está na tabela acima e as perguntas abaixo foram respondidas por mim.

- **"Pronto quando" da E3:**
  - [x] `scorer.clean`, `scorer.docs`, `pytest` e `scorer.docs --check` com exit 0.
  - [x] `Import-Csv deals.csv` com 8.800 linhas.
  - [x] `facts.json` com as chaves `evidencia_2a_q1`, `evidencia_2b_vendedores` e `evidencia_2c_close_value`.
  - [x] `gitw.py status`: "FORA da pasta da submissão: nada".
- **Os critérios foram definidos antes do resultado?** Quase todos: o plano já trazia as condições (i) e (ii) com ±5 pp e os limites do 2c. A tolerância de 7 dias da condição (iii) foi escolhida depois de uma rodada exploratória, e vale no limite. Isso está dito no DATA_QUALITY, no DECISIONS e abaixo.
- **Alguma decisão contradiz o CLAUDE.md?** Não. Mantive a data de referência como parâmetro (decisão 2), o vendedor fora de qualquer lógica (decisão 4: nenhum campo de vendedor vira variável; ele só aparece em `facts.json` para mostrar que é ruído) e nenhuma métrica dentro da amostra como resultado (decisão 6): os AUCs de target encoding saem com a chave `..._na_amostra_inflado`.
- **O SCOPE ficou coerente?** Sim, sem edição: nenhum número dele falhou. A frase do SCOPE "possível artefato de recorte, o bloco 2 investiga" descreve o risco como ele era no bloco 1; o resultado ("confirmado") está no DATA_QUALITY.
- **Algum número do briefing foi repetido sem conferir?** Não. Um erro conhecido do bloco 1 (MG Special como maior volume) agora aparece corrigido em `facts.json` (`produto_com_mais_deals`: GTX Basic). O briefing continua sem edição.
- **Ficou algum dado fora do repositório?** Não. Scripts auxiliares só no scratchpad.

## O que deu errado / iterações

1. **Colisão de nome na exploração.** No `explore2.py` usei `c["eq"]` (trimestre de engajamento) e depois chamei `c.eq`, que é o método `DataFrame.eq`; o cruzamento saiu com o cabeçalho `<bound method DataFrame.eq ...>`. No código final as colunas são variáveis locais com outros nomes (`engage_quarter`, `close_quarter`).
2. **Primeira ideia da condição (iii), descartada.** Pensei em "o ciclo mínimo das coortes antigas é maior que 14 dias". Falha na coorte de fev/2017 (ciclo mínimo 5, porque um deal engajado em 26/02 pode fechar em 03/03). Troquei por uma comparação com o piso que o recorte impõe (dias entre o último dia da coorte e o 1º fechamento): as folgas são de 2 a 7 dias nas 5 coortes, e não há ciclo curto em nenhuma delas.
3. **A tolerância de 7 dias é pós-hoc.** Ela só foi fixada depois de ver as folgas na exploração (2, 5, 3, 7 e 4), e a maior folga é exatamente 7. A condição vale no limite; com tolerância de 5, reprovaria a coorte de jan/2017. Por isso o `facts.json` traz um reforço sem tolerância (0% de ciclos de até 14 dias nas coortes com piso de 14 dias ou mais, contra no mínimo 28% nas coortes sem recorte) e as condições (i) e (ii) sustentam o veredito sozinhas. Registrado no DATA_QUALITY e no DECISIONS.
4. **Dois erros no meu próprio teste do verificador, achados na revisão antes da primeira execução.** O primeiro rascunho do pool de brinquedo usava 0,8125 e esperava que "81,2%" fosse aceito, mas 81,25 arredonda para 81,3 (metade para cima); troquei para 0,81246. O exemplo de número errado "0,63" era aceito de verdade (0,632 arredonda para 0,63); troquei por "0,64". Nenhum teste falhou por isso, porque corrigi antes de rodar.
5. **Ajustes depois de ler o `facts.json` gerado:** o ciclo máximo por trimestre de engajamento saía como `138.0` (float por causa do NaN) e passou a inteiro; os quartis de porte tinham rótulos de intervalo (`(8.999, 1238.0]`) e ganharam `q1_menores` a `q4_maiores`. Os demais ciclos e os preços já tinham sido convertidos para inteiro antes da primeira geração.
6. **Smoke test com outra data de referência.** Com `--reference-date 2017-09-30` as três faixas de idade somavam menos que `engaging_total` (751 + 193 + 530 contra 1.589), porque 115 deals foram engajados depois dessa data e ficam sem idade. `idade_hoje` passou a contar só os Engaging com idade definida (na data padrão, nada muda: 1.589).
7. **Os testes passaram na primeira execução completa** (40 de 40). Para não confiar só nisso, fiz a mutação do verificador (seção "Resultados").
8. **pandas 3:** nenhum erro nem aviso de depreciação nos comandos e no pytest.

## Decisões

Dez linhas "Bloco 2" em `docs/DECISIONS.md`, todas marcadas "(decisão autônoma do Claude)":

1. 2a: artefato de recorte, win rate por trimestre só com ressalva.
2. 2a: fotos de treino a partir de 31/03/2017; 28/02 só como sensibilidade. **Texto de transparência (obrigatório):** o planejador (Opus) viu num protótipo que começar em 28/02 piora o modelo do corte de 30/06; a regra foi justificada a priori, mas escolhida depois de ver isso, por isso 28/02 é reportado como sensibilidade.
3. 2a: tolerância de 7 dias na condição (iii), escolhida depois de ver a exploração.
4. 2b: tratamento dos vendedores sem deals.
5. 2c: o valor do deal aberto é `sales_price`.
6. Artefatos do gerador documentados e não explorados.
7. `has_account` e categorias "desconhecido" proibidos como variável.
8. O que o teste de números confere e ignora (e o que não confere).
9. AUCs de target encoding rotulados como inflados na chave do `facts.json`.
10. `age_days` e `cycle_days` como float com NaN; `age_days` NaN com engajamento posterior à referência.

Escolhas de código sem linha própria: `docs.py` guarda o verificador (`unmatched_numbers`) além do `inject`, em vez de um módulo à parte; os renderizadores AUTO se registram com `@docs.block("nome")`; `join_all` compara com o número de linhas da entrada (a conferência de 8.800 está nos testes); o `ALLOWED_CONSTANTS` é um dicionário número para comentário, ligado às constantes de `config.py` em vez de números soltos; o arredondamento de `fmt.round_half_up` é metade para cima, depois de descartar o ruído de ponto flutuante (14.499999999999998 vale 14,5), e o verificador usa a mesma função.

## Pendências

- **Commit do bloco 2** pelo orquestrador ("bloco 2: curadoria de dados"). Os arquivos novos estão ignorados pelo `.gitignore` do repositório (precisam de `git add -f`, que o `gitw.py` já faz). Os 3 `.gitkeep` removidos aparecem como exclusões.
- **Bloco 3 (E4):**
  - `deals.csv` é gravado para a data de referência 2017-12-31; `age_days` só vale para essa data. O estado histórico deve ser reconstruído por `as_of(T)` a partir das datas.
  - `config.FIRST_SNAPSHOT` já é 2017-03-31, e `SENSITIVITY_FIRST_SNAPSHOT` é 2017-02-28.
  - `has_account` pode ir ao `training_set` só para diagnóstico.
  - `employees` e `year_established` são float (NaN nos 1.425 sem conta).
  - `facts._auc` é privado; a E5 pode reaproveitar ou mover a função para `validate.py`.
- **Bloco 3 (E5):** para cobrir o SCORING no teste de números, acrescentar o caminho em `config.COVERED_DOCS`; o teste e o `number_pool` já leem `backtest_metrics.json` se existir. Novos renderizadores entram com `@docs.block`. Se o SCORING citar uma constante de desenho que não é fato, entra em `config.ALLOWED_CONSTANTS` com comentário.
- **SCORING / DATA_QUALITY:** a frase do SCOPE sobre o "possível artefato de recorte" agora tem resultado (confirmado). O SCORING deve repetir a ressalva do 28/02 (transparência acima) e mostrar a sensibilidade.
- **Teste de números:** não confere inteiros abaixo de 100 nem se o número está no contexto certo (ver "Resultados").
- **Briefing, seção 7:** continua com a frase errada sobre o MG Special; o README e o DATA_QUALITY não a repetem.
