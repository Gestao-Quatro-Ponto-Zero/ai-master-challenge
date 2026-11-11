# Validação do lead score — carga de 31/12/2017

Regra: `regra.py` (decisões 28 a 40; resumo em `desenho.md`, regra completa em `regra-lead-score.html`).
NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS, de 0 a 120.

## Execução carregada no banco

| Item | Valor |
|---|---|
| Execução ativa | `score_execucoes.id = 17`, versão `lead-score-1.0`, referência 31/12/2017, FIT absoluto (O-51), donos atuais |
| Arquivo de carga | `scoring/carga/score_2017-12-31.json` |
| sha256 | `06c9ac888aa541ec0524ad36daa8b31d4437f8f9d373b8ece80b7eda295786e3` |
| Execução 9 | sha256 `de9f5962d01a271fc0ddaa4728bea830f242472c0841282b1dbe851d25d59858` (redistribuição com 30 vendedores). O id 10 foi gasto pelo ensaio |
| Execução 7 | sha256 `f3aab6b5606d0cc2d1f8194e181eb79ca9e61c2f46f7031adf0af57e943e018f` (donos antes da redistribuição). Os ids 6 e 8 foram gastos pelos ensaios, que não deixaram linha |
| Execução anterior | `id = 5`, sha256 `73ce4a8934a172fe352c0bf3156d5941ae778cccf888d97c303fe899fee8aa32` (mesmas notas, texto antigo dos motivos). O id 6 foi gasto pelo ensaio, que não deixou linha |
| Como | Uma transação: `set role system_carga` → `system_iniciar_contexto_sistema` → só INSERT nas 6 tabelas `score_*` → `score_ativar_execucao` → conferências → COMMIT. Antes, um ensaio completo com ROLLBACK |
| Dono do deal | o atual. Sem redistribuição, sem repasse e nenhuma mudança em `core_deals` |
| Evento | `system_eventos` `carga_score` em cada carga (`{deals: 2089, execucao_id: 5}` e `{deals: 2089, execucao_id: 7}`) |

| Tabela | Linhas |
|---|---|
| `score_deals` | 2.089 (= deals abertos: 500 em Prospecting e 1.589 em Engaging) |
| `score_componentes` | 18.255 |
| `score_motivos` | 6.041 (1.863 deals com 3 motivos e 226 com 2) |
| `score_fit_vendedores` | 210 (30 vendedores × 7 produtos, cohort `produto=<produto>`) |
| `score_padroes_conta` | 85 |

Conferências antes do COMMIT, todas aprovadas:
- deals com nota = deals abertos (2.089) e nenhum aberto sem nota;
- nota entre 0 e 89 (dentro de 0–120);
- 0 deals com dono diferente do atual;
- execução ativa = a carregada.

## FIT absoluto (O-51): execução 15

**Regra nova.**
- FIT = 100 × média das conversões ajustadas do vendedor nas características do lead com 10+ fechados na janela. Conversão ajustada = (ganhos + 20 × conversão geral do vendedor) ÷ (fechados + 20).
- Sem característica que conte: a conversão geral do vendedor. Sem histórico: a conversão do time na janela (60,2% no dataset).
- Saiu "50 + 50 × desvio ÷ destaque". O destaque ficou só no motivo.
- Componentes do FIT: a conversão de cada característica (ex.: "Setor finanças: 65", máximo 100), no lugar do desvio.
- Motivos: "O vendedor fecha 62% dos leads com este perfil." e, quando o lead bate no melhor perfil, "Ponto forte do vendedor: série MG (67%).".
- `score_fit_vendedores` grava o FIT absoluto por cohort (`produto=<produto>`), lido pela função `core_rotear_lead`. A função não precisou mudar.

**Carga.**
- Ensaio com ROLLBACK, depois inserção pelo papel de carga e `score_ativar_execucao`. O ensaio gastou o id 14.
- Execução 15, sha256 `5aba6298…db35d`.
- 2.089 deals, nota de 35 a 75, 0 donos diferentes, sem redistribuição.
- `core_deals`: 8.801 deals.
- Componentes 17.790, motivos 6.041, fit_vendedores 210 (FIT de 44 a 77, média 60,2), padrões 85.

**Distribuição do FIT (gravado, inteiro).**

| FIT | Deals |
|---|---|
| 47–49 | 43 |
| 50–54 | 297 |
| 55–59 | 310 |
| 60–64 | 754 |
| 65–69 | 454 |
| 70–74 | 193 |
| 75–77 | 38 |

Com o valor exato, 31 deals ficam com FIT ≥ 75. Gravado e arredondado, são 38, dos quais 30 ativos. O limite para furar a fila e as travas do repasse continuam em 75 (decisão do Leandro).

**Top 5 por nota.**

| Vendedor | Deal | Nota | FIT | HEAT | BONUS | Produto · empresa |
|---|---|---|---|---|---|---|
| Darcel Schlecht | GR8JTX1T | 69 | 63 | 50 | 10 | GTX Pro · Warephase |
| | 9CYYLZ11 | 69 | 62 | 50 | 10 | GTX Basic · Stanredtax |
| | P7UPCSTC | 64 | 63 | 50 | 5 | GTX Pro · Faxquote |
| | YKBJP191 | 64 | 63 | 50 | 5 | GTX Pro · Faxquote |
| | 00400B1S | 58 | 62 | 50 | 0 | GTX Basic · sem empresa |
| Kami Bicknell | 7XRWWM0X | 66 | 63 | 40 | 10 | MG Special · Scotfind |
| | LC93MVYP | 61 | 64 | 55 | 0 | GTX Basic · sem empresa |
| | E1LFK6E3 | 57 | 64 | 40 | 0 | GTX Basic · sem empresa |
| | RYWETTBK | 56 | 63 | 25 | 5 | GTX Basic · Fasehatice |
| | 059K86LU | 56 | 61 | 10 | 10 | GTX Plus Pro · Labdrill |

Top 5 dos 35 vendedores: 175 deals, 97,7% ativos.

**Testes.**
- Python: 13 testes, todos passando. Exemplos novos no dataset: 4ZQTMS3Z com FIT 63,74 e nota 66,62; 1HD5JJM3 com 76,58 e 68,60; F5I33E1I com 68,13 e 47,69. O FIT é conferido como 100 × média deal a deal.
- TS: paridade total com o Python sobre a mesma entrada (2.089 deals: notas, componentes e motivos; FIT por vendedor; padrões; os 3 planos de redistribuição). `rotearLeadNovo()` e os testes dele saíram. `tsc` e build passam.

**Execução 17: características com poucos casos.**
- A pedido da tela, os componentes do FIT passam a trazer também as características que não contam por terem menos de 10 fechados: nome da característica, pontos = fechados, sem máximo. Ex.: "Setor software", 6.
- As notas da 17 são idênticas às da 15 em todos os 2.089 deals.
- Componentes: 17.790 → 20.032. sha256 `06c9ac88…5786e3`. Os ensaios gastaram os ids 14 e 16.
- Testes: Python 13 OK; TS 184 passando (suíte inteira), paridade refeita; `tsc` ok.

**Efeito na redistribuição.** Com o FIT novo, o plano de domingo deixa de ser estável: sobre a foto de entrada ele moveria 352 leads (375 com os 35 vendedores). Nesta carga não houve redistribuição.

## Decisão 49: os 35 vendedores na redistribuição (execução 11)

- **Regra:**
  - elegíveis = os 35 vendedores ativos do time;
  - quem não tem histórico na janela (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin) vale FIT 50 em todo lead, como os sem destaque;
  - motivo: "Vendedor sem histórico: encaixe neutro (50).";
  - limite da semana = ativos ÷ 35, arredondado para cima = 23.
  - Mesma regra no Python (`regra.py`, `redistribuir.py`) e no TS (`src/lib/score/`), com teste de paridade do plano.
- **Proteção nova:** a carga e a redistribuição param se a data de negócio do banco (`system_data_negocio()`) for diferente da data do cálculo.
- **Gravação:**
  - a 1ª tentativa caiu no meio do ensaio (conexão perdida) e não gravou nada;
  - depois: ensaio com ROLLBACK (261 de 261) e COMMIT com 261 trocas, 0 recusadas e o motivo "Redistribuição de domingo.";
  - `acao_reatribuicoes` com esse motivo: 475 → 736;
  - `core_deals`: 8.801 deals (2.089 abertos).

| | Antes (execução 9) | Depois (execução 11) |
|---|---|---|
| Trocas | — | 261 |
| Leads de cada um dos 5 sem histórico | 0 | 23 (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin) |
| Ativos por vendedor | 0 a 31 (35 vendedores) | 9 a 31 |
| FIT médio dos leads sem contato | 77,8 | 73,4 |
| Leads sem contato com FIT ≥ 75 | 265 | 235 |

- **Nas pontas:**
  - Wilburn Farren (sem destaque) fica com 9;
  - Rosalina Dieter, com 19;
  - Vicki Laflamme, Kami Bicknell e Zane Levy ficam acima de 23 (24, 25 e 31), por causa dos ativos em Engaging que não mudam.
- **Execução 11:**
  - 2.089 deals, nota de 0 a 89, 0 donos diferentes;
  - componentes 17.791, motivos 6.041 (115 com "Vendedor sem histórico");
  - top 5: 175 deals (35 vendedores), 94,9% ativos;
  - FIT ≥ 75: 479.

## Redistribuição de domingo (31/12/2017) e execução 9

Regra decidida (cenário B, só equilíbrio): entram só os leads abertos sem contato registrado. O limite da semana é ativos ÷ vendedores elegíveis, arredondado para cima. Os pares lead × vendedor são ordenados por FIT, do maior para o menor.

- **Scripts:**
  - `scoring/redistribuir.py` calcula o plano, só lendo o banco;
  - `scoring/aplicar_redistribuicao.py` grava pelo papel de carga, com uma chamada de `core_repassar_deal(..., 'redistribuicao', ...)` por troca (versão da migration 0033: sem as travas do repasse, recusa lead com contato).
  - O plano é refeito com o estado do banco na hora de gravar.
- **Escopo:** 499 leads sem contato. Dos 500 em Prospecting, 1 ganhou contato nos testes e ficou com o dono.
- **Elegíveis:** 30 vendedores com fechamentos na janela, inclusive Garret Kinder (35 fechados), Donn Cantrell (73) e Reed Clapper (60). Os 5 sem nenhum deal ficam fora, porque não têm FIT.
- **Gravação:**
  - ensaio com ROLLBACK: 475 de 475 sem recusa;
  - depois, COMMIT: 475 trocas, 0 recusadas, 475 linhas em `acao_reatribuicoes` com o motivo "Redistribuição de domingo." e a linha do tempo de cada lead;
  - nenhum UPDATE direto e nenhum DELETE;
  - `core_deals` continua com 8.801 deals (2.089 abertos).

| | Antes | Depois |
|---|---|---|
| Leads que mudaram de dono | — | 475 |
| Ativos por vendedor (com leads) | 6 a 111 (27 vendedores) | 11 a 31 (30 vendedores) |
| FIT médio dos leads sem contato | 49,5 | 77,8 |
| Leads sem contato com FIT ≥ 75 | 48 | 265 |

- **Nas pontas:**
  - Wilburn Farren fica com 11 ativos: sem destaque, FIT 50 para tudo, recebe o que sobra;
  - Zane Levy fica com 31: já tinha 31 ativos em Engaging, que não mudam.
- **Sem lead:** só os 5 sem nenhum deal no dataset (Mei-Mei Johns, Elizabeth Anderson, Natalya Ivanova, Carol Thompson, Carl Lin), porque não têm FIT. Garret, Donn e Reed passaram de 0 para 27 ativos.
- **Execução 9:**
  - o score foi recalculado com os donos novos;
  - 2.089 deals, nota de 0 a 89, 0 donos diferentes;
  - componentes 18.064 (menos que 18.255, porque o FIT do novo dono usa menos características com 10+ fechados);
  - motivos 6.041;
  - top 5: 150 deals (30 vendedores), 94,7% ativos, 0 com 181 dias ou mais;
  - deals com FIT ≥ 75: 509.

## Execução 7: só o texto dos motivos

A 7 troca o texto dos motivos. A regra e os números são os mesmos da 5.

- **Rótulos em português, como na tela:**
  - produto X;
  - série X;
  - setor varejo, saúde e os demais traduzidos pela tabela SETORES do app;
  - empresa de receita pequena, média ou grande;
  - empresa pequena, média ou grande em funcionários;
  - empresa X;
  - sede nos EUA ou fora dos EUA.
- **Terceira pessoa:** "destaque do vendedor", "média do vendedor", "o vendedor não tem um destaque". A mesma frase serve para o vendedor e para o manager.
- **Conferência no banco, 5 × 7, deal a deal:** 2.089 de 2.089 iguais em nota, FIT, HEAT, BONUS, ação, dono, marcadores, valor e dias. Também ficam iguais os pontos dos componentes, o FIT por vendedor e os padrões de conta. Na execução ativa, 0 motivos com "você", "seu" ou "sua" e 0 com rótulo cru.
- **Testes:** dois novos em `test_regra.py` (texto dos motivos e rótulos), 13 no total, todos passando.
- **No ar:** a lista do dia de Anna Snelling segue a nota (70, 69, 67, 67, 64) e mostra o 1º motivo no texto novo.

| Antes (5) | Depois (7) |
|---|---|
| Encaixa no seu destaque: receita media (11 de 15 ganhos nos últimos 3 meses). | Encaixa no destaque do vendedor: empresa de receita média (11 de 15 ganhos nos últimos 3 meses). |
| Encaixe acima da sua média: funcionários pequena (26 de 35 ganhos nos últimos 3 meses). | Encaixe acima da média do vendedor: empresa pequena em funcionários (26 de 35 ganhos nos últimos 3 meses). |
| Encaixe acima da sua média: setor retail (10 de 13 ganhos nos últimos 3 meses). | Encaixe acima da média do vendedor: setor varejo (10 de 13 ganhos nos últimos 3 meses). |
| Encaixe acima da sua média: sede EUA (49 de 74 ganhos nos últimos 3 meses). | Encaixe acima da média do vendedor: sede nos EUA (49 de 74 ganhos nos últimos 3 meses). |
| Você não tem um destaque com casos suficientes nos últimos 3 meses: o encaixe fica neutro (50). | O vendedor não tem um destaque com casos suficientes nos últimos 3 meses: o encaixe fica neutro (50). |
| Fora do seu forte: série GTX (35 de 70 ganhos nos últimos 3 meses, abaixo da sua média). | Fora do forte do vendedor: série GTX (35 de 70 ganhos nos últimos 3 meses, abaixo da média dele). |

## Conferência contra o desenho (dataset limpo, `python -m unittest scoring/test_regra.py`)

13 testes, todos passando.

| Item | Desenho | Obtido |
|---|---|---|
| Exemplo 4ZQTMS3Z | FIT 72,6 · HEAT 40 · BONUS 10 · nota 72,8 | 72,6 · 40 · 10 · 72,8 |
| Exemplo 1HD5JJM3 | 100 · 50 · 0 · 85,0 | 100 · 50 · 0 · 85,0 |
| Exemplo F5I33E1I | 95,8 · 0 · 0 · 67,1 | 95,8 · 0 · 0 · 67,1 |
| FIT por faixa (0–20 / 20–40 / 40–50 / 50 / 50–60 / 60–75 / 75+) | 174 / 423 / 353 / 98 / 349 / 400 / 292 | igual |
| HEAT por faixa (0 / 10 / 25 / 40 / 50 / 55 / 70) | 730 / 749 / 53 / 39 / 500 / 11 / 7 | igual |
| BONUS (0 / 5 / 10) | 1.651 / 208 / 230 | igual |
| Empresas na janela de compra | 0 | 0 |
| Top 5 por vendedor | 135 deals; 77,8% ativos; 38,5% com empresa; 6 com 181 dias ou mais | igual |
| Vendedores sem destaque | Rosalina Dieter, Wilburn Farren | igual |

## Banco × dataset

O cálculo da carga lê o banco. O banco tem 3 deals alterados nos testes da QA:

- **88UBTBQ8:** criado no CRM e perdido em 31/12 (Anna Snelling, MG Special, sem empresa). Ele entra na janela de 3 meses de Anna, e por isso as notas dos 112 deals abertos dela mudam de 1 a 3 pontos em relação ao dataset. Nenhum outro vendedor muda.
- **0D8Y5JA0** (Prospecting) e **B08R55ET** (Engaging): têm contato registrado em 31/12. O fator de contato é 1,0, o mesmo de quem não tem histórico.

Os totais por faixa e o top 5 ficam iguais aos do dataset.

## Distribuições da carga (valores gravados, inteiros)

| Nota | Deals |
|---|---|
| 0–20 | 186 |
| 21–40 | 784 |
| 41–60 | 822 |
| 61–80 | 273 |
| 81–100 | 24 |
| acima de 100 | 0 |

| FIT | Deals |
|---|---|
| 0–20 | 173 |
| 21–40 | 429 |
| 41–49 | 313 |
| 50 | 167 |
| 51–60 | 320 |
| 61–74 | 394 |
| 75 ou mais | 293 |

O 50 inclui o arredondamento de 49,5 a 50,4.

**HEAT** = 0: 730 · 10: 749 · 25: 53 · 40: 39 · 50: 500 · 55: 11 · 70: 7.

**BONUS** = 0: 1.651 · 5: 208 · 10: 230. A janela de compra vale 0 para todas as empresas, porque nenhuma passou no teste contra o calendário geral.

**Ação sugerida:** focar 798 · requalificar 951 (mais de 138 dias) · desistir 340 (mais de 276 dias, valor proposto).

**Marcadores:** esfriou 1.291 · risco_esfriar 141 · atendimento_atrasado 0. Nenhum deal aberto foi criado no CRM, então o atendimento atrasado ainda não se aplica.

Na tela, pela view `core_deals_visao`: faixa de nota alta 98, média 1.063, baixa 928.

## Top 5 por nota (execução 7, igual à 5)

| Vendedor | Deal | Nota | FIT | HEAT | BONUS | Produto · empresa |
|---|---|---|---|---|---|---|
| Violet Mclelland | T6MPH7JC | 89 | 97 | 70 | 0 | MG Special · sem empresa |
| | 07GUKIG3 | 84 | 97 | 55 | 0 | MG Special · sem empresa |
| | 1BW8S7JD | 80 | 97 | 40 | 0 | MG Special · sem empresa |
| | 854QZNWK | 80 | 97 | 40 | 0 | MG Special · sem empresa |
| | PQ84ANKD | 80 | 97 | 40 | 0 | MG Special · sem empresa |
| Moses Frase | 0E8D6TCQ | 85 | 100 | 50 | 0 | GTX Plus Basic · sem empresa |
| | 1HD5JJM3 | 85 | 100 | 50 | 0 | GTX Plus Basic · sem empresa |
| | 7MKYTX69 | 85 | 100 | 50 | 0 | GTX Plus Pro · sem empresa |
| | NWPSEF2I | 85 | 100 | 50 | 0 | GTX Plus Basic · sem empresa |
| | H046CU4Z | 81 | 94 | 50 | 0 | GTX Basic · sem empresa |

## Valores propostos usados (sem decisão final)

- **BONUS:** só a parte do histórico (terços da receita ganha: até US$ 90.110 vale 0, até US$ 127.050 vale 5, acima disso 10). A janela de compra está no código e vale 0.
- **Ação:** desistir acima de 276 dias, o dobro do deal mais longo que já fechou.
- **Vendedor sem destaque:** destaque a menos de 3 pontos da média dele.
- **Padrão da conta na tela:** "Sem padrão". O intervalo típico, o mês habitual e a próxima compra ficam em branco, porque nenhuma empresa tem época de compra própria; a explicação diz isso.

## Fora desta carga

- Redistribuição de domingo (P0).
- Repasse e penalidade.
- Mudança no contrato do app.
- Backtest contra "por valor", "mais novo primeiro" e acaso (seção 3 do desenho).

## Reproduzir

```bash
cd solution
python -m unittest scoring/test_regra.py -v                                    # testes no dataset
python scoring/calcular_score.py                                               # lê o banco e gera scoring/carga/score_2017-12-31.json
python scoring/carregar_score.py scoring/carga/score_2017-12-31.json           # ensaio (ROLLBACK)
python scoring/carregar_score.py scoring/carga/score_2017-12-31.json --aplicar # grava uma execução nova
```

Rodar de novo cria uma execução nova. O sha256 é único por arquivo, então o mesmo arquivo não entra duas vezes.
