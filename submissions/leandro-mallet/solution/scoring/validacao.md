# Validação do lead score — carga de 31/12/2017

Regra: `regra.py` (decisões 28 a 40, FIT absoluto da O-51 e perguntas P0 a P6 decididas; resumo em `desenho.md`, regra vigente em `regra-lead-score.html`).
As versões anteriores (FIT relativo, execuções 5 a 11) estão em [`../historico/score-versao-anterior.md`](../historico/score-versao-anterior.md).
NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS, de 0 a 120.

## Execução carregada no banco

| Item | Valor |
|---|---|
| Execução ativa | `score_execucoes.id = 17`, versão `lead-score-1.0`, referência 31/12/2017, FIT absoluto (O-51), donos atuais |
| Arquivo de carga | `scoring/carga/score_2017-12-31.json` |
| sha256 | `06c9ac888aa541ec0524ad36daa8b31d4437f8f9d373b8ece80b7eda295786e3` |
| Execução 13 | rodada forçada corrigida da redistribuição (O-45): 35 elegíveis, limite 23, 257 trocas, FIT relativo |
| Como | Uma transação: `set role system_carga` → `system_iniciar_contexto_sistema` → só INSERT nas 6 tabelas `score_*` → `score_ativar_execucao` → conferências → COMMIT. Antes, um ensaio completo com ROLLBACK |
| Dono do deal | o atual no banco, que já inclui as redistribuições gravadas (execuções 9, 11 e 13). A carga do score só lê o dono: não muda `core_deals` |
| Evento | `system_eventos` `carga_score` em cada carga (`{deals: 2089, execucao_id: <id>}`) |

| Tabela | Linhas |
|---|---|
| `score_deals` | 2.089 (= deals abertos: 500 em Prospecting e 1.589 em Engaging) |
| `score_componentes` | 20.032 |
| `score_motivos` | 6.041 (1.863 deals com 3 motivos e 226 com 2) |
| `score_fit_vendedores` | 210 (30 vendedores com histórico × 7 produtos, cohort `produto=<produto>`, FIT absoluto) |
| `score_padroes_conta` | 85 |

Conferências antes do COMMIT, todas aprovadas:
- deals com nota = deals abertos (2.089) e nenhum aberto sem nota;
- nota entre 35 e 75 (dentro de 0–120);
- 0 deals com dono diferente do atual;
- execução ativa = a carregada.

## FIT absoluto (O-51): execuções 15 e 17

**Regra.**
- FIT = 100 × média das conversões ajustadas do vendedor nas características do lead com 10+ fechados na janela. Conversão ajustada = (ganhos + 20 × conversão geral do vendedor) ÷ (fechados + 20).
- Sem característica que conte: a conversão geral do vendedor. Sem histórico: a conversão do time na janela (60,2% no dataset).
- O destaque do vendedor aparece só no motivo.
- Componentes do FIT: a conversão de cada característica (ex.: "Setor finanças: 65", máximo 100).
- Motivos: "O vendedor fecha 62% dos leads com este perfil." e, quando o lead bate no melhor perfil, "Ponto forte do vendedor: série MG (67%).".
- `score_fit_vendedores` grava o FIT absoluto por cohort (`produto=<produto>`), lido pela função `core_rotear_lead`. A função não precisou mudar.

**Carga.**
- Ensaio com ROLLBACK, depois inserção pelo papel de carga e `score_ativar_execucao`. O ensaio gastou o id 14.
- Execução 15, sha256 `5aba6298…db35d`.
- 2.089 deals, nota de 35 a 75, 0 donos diferentes do banco (a carga não troca dono).
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

**Efeito na redistribuição.** Com o FIT novo, o plano de domingo deixa de ser estável: sobre a foto de entrada ele moveria 352 leads (375 com os 35 vendedores). Esse plano não foi aplicado; a próxima redistribuição de domingo já usa o FIT absoluto.

## Rodada forçada corrigida da redistribuição (O-45): execução 13

- Rodada pela rotina diária, com a regra da decisão 49 e o FIT relativo (antes da O-51).
- 35 elegíveis, limite da semana 23, 257 trocas, execução 13.
- Gravada por `core_repassar_deal` com origem `redistribuicao` e o motivo "Redistribuição de domingo.", sem UPDATE direto e sem DELETE.
- `acao_reatribuicoes` com esse motivo, conferido no banco: 1.254 linhas = 475 (execução 9) + 261 (execução 11) + 261 (execução 12, rotina diária) + 257 (execução 13).

## Banco × dataset

O cálculo da carga lê o banco. O banco tem 3 deals alterados nos testes da QA:

- **88UBTBQ8:** criado no CRM e perdido em 31/12 (Anna Snelling, MG Special, sem empresa). Ele entra na janela de 3 meses de Anna, e por isso as notas dos deals abertos dela diferem das do dataset. Nenhum outro vendedor muda.
- **0D8Y5JA0** (Prospecting) e **B08R55ET** (Engaging): têm contato registrado em 31/12. O fator de contato é 1,0, o mesmo de quem não tem histórico.

## Valores usados

- **BONUS (P3, P4):** a parte do histórico pontua (terços da receita ganha: até US$ 90.110 vale 0, até US$ 127.050 vale 5, acima disso 10). A janela de compra está no código e vale 0.
- **Ação:** desistir acima de 276 dias, o dobro do deal mais longo que já fechou.
- **Limites (decisão 51):** ficam como estão: FIT ≥ 75 para furar a fila, repasse com FIT ≥ 75, até 3 pontos abaixo do dono e top 5.
- **Máximo de repasses e penalidade (P5, P6):** em branco, sem valor decidido.
- **Padrão da conta na tela:** "Sem padrão". O intervalo típico, o mês habitual e a próxima compra ficam em branco, porque nenhuma empresa tem época de compra própria; a explicação diz isso.

## Fora da carga do score

- A carga do score não troca dono. A redistribuição de domingo e o repasse rodam à parte, pela função `core_repassar_deal` (seção da O-45).
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
