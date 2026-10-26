# Bloco 5 — MODEL_CARD, README e verificação de números

## Objetivo

Escrever `docs/MODEL_CARD.md` e o `README.md` da submissão no formato do template do G4 (`ai-master-challenge/templates/submission-template.md`), com todo número saindo de arquivo gerado, e estender `scorer.docs` e os testes para que o README e o MODEL_CARD sejam regenerados e conferidos como os demais documentos. Especificação: seções "Bloco comum" e "E8 — Bloco 5" de `process-log/plano_execucao_opus.md`. Ninguém respondeu perguntas; as decisões abaixo são do executor (decisão autônoma do Claude).

## Executor

Claude Sonnet (subagente executor). Execução da especificação E8 de `process-log/plano_execucao_opus.md`, planejada pelo Claude Opus em modo somente leitura. Fontes lidas: `CLAUDE.md`, `docs/{SCOPE,DATA_QUALITY,SCORING,DECISIONS}.md`, `process-log/{00_fase0_exploracao,00..04,plano_execucao_opus}.md`, `facts.json`, `backtest_metrics.json`, `scorer/docs.py`, `scorer/config.py` e o template. O `04_bloco-4.md` estava em andamento (só a Parte A); `DECISIONS.md`, `build.py`, `app/*` e os screenshots são de outro executor e não foram tocados.

## O que foi feito (comandos)

Ordem seguida, para não quebrar o build do outro executor:

1. **`scorer/docs.py` (só acréscimos):** cinco renderizadores AUTO novos, registrados com `@_scoring_block` (devolvem o aviso de "backtest não rodado" se o JSON não existir): `mc-desempenho` (média dos cortes e pior corte, que é o de menor margem do score sobre o melhor baseline), `mc-recalibracao`, `readme-backtest`, `readme-hoje` e `readme-achados` (os cinco achados do resultado, com números e listas de cortes calculados do JSON).
2. **`scorer/config.py` (só acréscimos):** `RECALIBRATION_SHIFT_PP = 10` (o "X pp" do model card) e `RECALIBRATION_MIN_BAND_N = 100`.
3. **Escrita** de `docs/MODEL_CARD.md` e `README.md`, com os blocos AUTO vazios nos marcadores.
4. **Testes:** `tests/test_readme.py` (novo, 20 casos: títulos na ordem do template, separadores, última linha, resumo com 3 a 5 frases, abertura e fecho do resumo, LinkedIn, `[RASCUNHO — Rafael revisar]`, rótulo de origem em cada erro da IA, tabela de ferramentas, limitações obrigatórias, itens 0 a 6 do workflow, setup com o placeholder do Pages, seções do model card, links relativos, screenshots) e `tests/test_docs_numbers.py` (5 casos de mutação: troca um número do README ou do MODEL_CARD reais e exige que o verificador acuse).
5. **SÓ NO FIM:** `README.md` e `MODEL_CARD.md` entraram em `config.COVERED_DOCS`; `& $PY -B -m scorer.docs` (preencheu os blocos) e `& $PY -B -m scorer.docs --check` (exit 0).
6. Conferência independente das afirmações da prosa contra o JSON, com um script no scratchpad (fora da submissão): `verify_claims.py`.

## Resultados

Números dos blocos AUTO (fonte: `solution/data/processed/backtest_metrics.json`):

- Critério pré-registrado: PASSOU, sem ajuste.
- Receita média no top 20%: score 61,1%, valor 48,1%, recência 29,7%, aleatório 20,0%.
- AUC média: score 0,64, recência 0,70. A recência ganha em AUC em 3 dos 4 cortes (30/06, 31/08 e 30/09; 0,83 contra 0,65 em 30/09); o score só em 31/07.
- Resolvidos: o score fica em 48,7% de receita média contra 49,0% do valor (diferença máxima de 0,5 pp em um corte): empate.
- Foque de hoje: 69 dos 126 deals têm 61 dias ou mais; nos fins de trimestre testados, esses deals ganharam −17,4 pp (30/06) e −41,3 pp (30/09) em relação aos de até 30 dias.
- Limpe de hoje: 1.291 deals, US$ 3.198.664 de valor de tabela (US$ 3,2 mi, citado no resumo).
- Alerta de recalibração com X = 10 pp: 7 das 24 faixas de idade com 100 deals ou mais teriam acendido no backtest (o bloco `mc-recalibracao` imprime a contagem).

Saídas dos comandos (cwd `$SOL`): ver "Autoverificação".

### Números conferidos e divergências encontradas

Todos os números da prosa do README e do MODEL_CARD passam pelo verificador (`unmatched_numbers`); os dos blocos AUTO são regenerados. Além disso, `verify_claims.py` conferiu as afirmações que o verificador não cobre (contagens pequenas e frases como "três dos quatro cortes"). Divergências e correções:

| # | Divergência | Onde | Correção |
|---|---|---|---|
| 1 | A tarefa dizia "a recência ganha em AUC nos fins de trimestre". Pelo JSON ela ganha em 3 dos 4 cortes: 30/06 (0,73 contra 0,66), 31/08 (0,66 contra 0,63) e 30/09 (0,83 contra 0,65). 31/08 não é fim de trimestre | `readme-achados`, resumo, limitações | Redação exata: "em 3 dos 4 cortes", com as datas geradas do JSON |
| 2 | A tarefa dizia que o pytest travou "por assert nan". O bloco 3 registra uma execução que passou de 10 minutos, causa não diagnosticada (provável estado intermediário de um arquivo do outro executor). Nada nos logs menciona um `assert` com "nan" (a palavra aparece só como termo proibido nas frases de explicação) | README, "Onde a IA errou" | Segui os logs: o episódio diz "causa não diagnosticada". Não inventei uma causa |
| 3 | O verificador de números reprovou o primeiro README: "1280" e "390" (largura dos screenshots no texto do link) e "2,77" (contraste da linha âmbar) | README | Texto do link passou a "versão para computador/celular"; o contraste virou "abaixo do mínimo de elementos de interface". Os nomes dos arquivos `final_inicio_1280.png` ficam só no destino do link, que o verificador ignora |
| 4 | Dois testes meus falharam por erro do teste: a mutação de "61,1%" para "61,2%" e de "0,996" para "0,997" não era acusada porque 61,2% e 0,997 também existem nos JSONs (o verificador prova que o número existe nos fatos, não que está no lugar certo) | `test_docs_numbers.py` | Troquei os valores da mutação para 0,931 e 93,1% (depois de 66,6% também existir no pool), que não existem nos JSONs. É o limite do verificador, já descrito no log do bloco 2 |
| 5 | `test_model_card_has_the_required_sections` falhou: procurava "Limpe significa confirmar" e o texto tem negrito no meio ("Limpe significa **confirmar com o cliente**") | `test_readme.py` | O teste remove `**` antes de procurar |
| 6 | Os screenshots `final_inicio_*.png` e `05_bloco-5.md` não existiam quando o README ficou pronto, e o teste de links acusou os dois | README | `05_bloco-5.md` é este arquivo. Os screenshots são do executor do bloco 4: o teste `test_screenshot_files_linked_by_the_readme_exist` falha até eles existirem (esperado) |

Revisão numérica do SCORING (item 5 da E8): todo número e frase do SCORING foi conferido contra o JSON (o teste de números passa, e `verify_claims.py` conferiu as frases com contagens: Reative com 0% a 23% de ganhos, Limpe com zero ganhos nos 4 cortes, região pior fora da amostra em 3 de 4 cortes, AUC de `has_account` de 0,72 a 0,79, 16 deals de Reative para Foque, 81 e 183 abertos que ainda podem fechar). Nenhuma divergência no SCORING, no SCOPE nem no DATA_QUALITY.

## Autoverificação do checkpoint

- [x] `python -m scorer.docs` e `python -m scorer.docs --check`: exit 0 (cinco documentos, "sem mudanças" na segunda rodada).
- [x] Títulos do README iguais ao template, mesma ordem (`test_titles_appear_once_and_in_template_order`); resumo com 5 frases (`test_executive_summary_has_at_most_five_sentences`); `[RASCUNHO — Rafael revisar]` no início de "O que eu adicionei".
- [x] "O que eu adicionei" baseado só em `00_fase0_exploracao.md` (escolha do 003 pela governança; não contornar o bloqueio do Kaggle; backtest temporal; vendedor fora do score; 138 dias não vira regra; model card; não usar Streamlit).
- [x] "Onde a IA errou": cada item está marcado "(fase 0, com Rafael)" ou "(autocorreção na execução autônoma)" e existe nos logs 00 a 04 (episódios: métrica otimista, win rate de 82%, plano por atributos, MG Special, justificativa da pergunta 3, generalização sobre os AUCs, protótipo não monotônico, tolerância pós-hoc de 7 dias, `beats` em ponto flutuante, teste de vazamento que não provava nada, previsão do plano sobre a recência, rascunho do SCORING, pytest travado, contraste e tela vazia).
- [x] Limitações com as três exigidas: executores parados por limite de API entre 16:28 e 19:01, dulwich em vez de git, ausência de chat-exports.
- [ ] Screenshots: ver "Pendências".
- [x] Não toquei em `build.py`, `test_build.py`, `app/*`, `tools/check_app.py`, `briefs/`, `04_bloco-4.md`, `screenshots/` nem `DECISIONS.md`. Não rodei git.

## O que deu errado / iterações

1. Primeira execução de `pytest tests/test_readme.py tests/test_docs_numbers.py`: 7 falhas (divergências 3 a 6 acima). Depois das correções, ver "Autoverificação".
2. Nome de alias no PowerShell: um helper `sl` para ler trechos de log colidiu com o alias `sl` (Set-Location) e falhou em todas as chamadas, sem efeito em arquivos. Passei a ler com a ferramenta Read.

## Decisões (todas "decisão autônoma do Claude")

`DECISIONS.md` pertence ao outro executor neste momento e não foi editado. Linhas propostas para o orquestrador consolidar:

```
| 2026-10-25 | Bloco 5 — README no formato exato do template, com "Como rodar (setup)" como subseção de Solução e a ferramenta de verificação opcional (decisão autônoma do Claude) | Pôr o setup num título próprio fora da Solução | O template permite "o formato que melhor comunicar" dentro da Solução; manter os títulos obrigatórios e a ordem permite teste automático (`test_readme.py`) |
| 2026-10-25 | Bloco 5 — Resultados do README e do MODEL_CARD saem de cinco blocos AUTO novos (`readme-achados`, `readme-backtest`, `readme-hoje`, `mc-desempenho`, `mc-recalibracao`); os dois arquivos entram em COVERED_DOCS (decisão autônoma do Claude) | Digitar os números na prosa | Cada número é regenerado do JSON e a prosa passa pelo verificador; a mutação de 5 números reais é acusada |
| 2026-10-25 | Bloco 5 — Recalibração por gatilho de X = 10 pp (`config.RECALIBRATION_SHIFT_PP`), só em faixas com 100 deals ou mais (decisão autônoma do Claude) | Recalibrar só a cada trimestre; X = 5 pp | No backtest, 7 de 24 faixas (corte x idade) com 100 deals ou mais ficaram a mais de 10 pp da taxa observada; com 5 pp o alerta quase sempre acenderia. X é parâmetro, não resultado |
| 2026-10-25 | Bloco 5 — Model card em 8 seções, com "Uso NÃO pretendido" (avaliar vendedores, forecast, encerrar deals automaticamente) e riscos com mitigação (decisão autônoma do Claude) | Model card só com métricas | O ângulo de governança do Rafael (fase 0) pede limites e responsabilidade, não só desempenho |
| 2026-10-25 | Bloco 5 — "Resultados" diz "a recência ganha em AUC em 3 dos 4 cortes", não "nos fins de trimestre" (decisão autônoma do Claude) | Repetir a frase da tarefa | 31/08 não é fim de trimestre e a recência também ganha lá (0,66 contra 0,63) |
```

Escolhas de código sem linha própria: o "pior corte" do `mc-desempenho` é o de menor margem do score sobre o melhor baseline (31/07); "fins de trimestre" no achado do Foque são os cortes com mês 3, 6, 9 ou 12 (30/06 e 30/09).

## Pendências

- **Screenshots do README:** `process-log/screenshots/final_inicio_1280.png` e `final_inicio_390.png` não existiam quando este bloco terminou (a pasta só tinha `.gitkeep`). Eles são do executor da Parte B do bloco 4 (`python tools/check_app.py --prefix final`). Até lá, `test_screenshot_files_linked_by_the_readme_exist` falha (2 casos); o resto da suíte dos dois arquivos passa.
- **`DECISIONS.md`:** consolidar as cinco linhas acima.
- **Bloco 6:** a revisão independente pode derrubar frases do README; os campos "Pages" e "data de envio" continuam como placeholders (`[ativar — Rafael]`, `[preencher ao abrir o PR]`).
- **"O que eu adicionei":** é um rascunho do Claude baseado só na fase 0; o Rafael precisa revisar.
- O commit do bloco 5 é feito pelo orquestrador ("bloco 5: documentação e model card"). Não rodei git.
