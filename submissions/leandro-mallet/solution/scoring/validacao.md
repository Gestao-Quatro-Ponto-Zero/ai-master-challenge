# Validação do lead score — carga de 31/12/2017

Regra: `regra.py` (decisões 28 a 40; resumo em `desenho.md`, regra completa em `regra-lead-score.html`).
NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS, de 0 a 120.

## Execução carregada no banco

| Item | Valor |
|---|---|
| Execução | `score_execucoes.id = 5`, versão `lead-score-1.0`, referência 31/12/2017 |
| Arquivo de carga | `scoring/carga/score_2017-12-31.json` |
| sha256 | `73ce4a8934a172fe352c0bf3156d5941ae778cccf888d97c303fe899fee8aa32` |
| Como | Uma transação: `set role system_carga` → `system_iniciar_contexto_sistema` → só INSERT nas 6 tabelas `score_*` → `score_ativar_execucao` → conferências → COMMIT. Antes, um ensaio completo com ROLLBACK |
| Dono do deal | o atual. Sem redistribuição, sem repasse e nenhuma mudança em `core_deals` |
| Evento | `system_eventos` `carga_score` `{deals: 2089, execucao_id: 5}` |

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
- execução ativa = 5.

## Conferência contra o desenho (dataset limpo, `python -m unittest scoring/test_regra.py`)

11 testes, todos passando.

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

## Top 5 por nota (execução 5)

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
