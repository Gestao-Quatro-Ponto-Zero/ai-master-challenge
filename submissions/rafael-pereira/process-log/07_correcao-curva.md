# Correção após revisão do Rafael

**Executor:** Claude Sonnet (subagente executor), a pedido do Rafael, com o orquestrador (Claude Opus 5.5) conferindo e commitando. Nenhum git foi rodado pelo executor.
**Data:** 25 e 26/10/2026.

## Interrupção
A execução foi interrompida por limite de uso da API e retomada depois que a cota foi renovada. O aviso veio do orquestrador na própria sessão; não tenho registro do horário da pausa. Ao retomar, conferi o estado dos arquivos antes de continuar: `score.py`, `features.py`, `config.py`, `explain.py` e `validate.py` já estavam reescritos, o `validate.py` estava na seção de avaliação dos cortes, o `docs.py` ainda tinha os renderizadores antigos, o `app.js` e os testes não tinham sido tocados e este arquivo não existia. Nada foi refeito.

## O problema
O Rafael usou a página publicada como vendedor. Na tela dele:
- a chance de ganho era constante (40%) de 0 a 95 dias, o que contradiz o briefing: no corte de 30/09/2017 as taxas foram 50% (0 a 30 dias), 34% (31 a 60), 7% (61 a 90) e 0% (acima de 90);
- o deal do topo da Rosalina Dieter era um GTK 500 com 95 dias e score 100;
- dentro do Foque, a ordem virou uma ordenação por preço (o valor esperado de uma curva plana é o preço vezes uma constante);
- a caixa "Atenção" do Foque admitia o erro em vez de corrigi-lo.

## Diagnóstico (confirmado com números)
Taxa de ganho em 90 dias por idade, nas 7 fotos mensais de treino de hoje (31/03 a 30/09/2017). Reproduzi a tabela do orquestrador; os números batem exatamente.

| Idade na foto | Fotos de fim de trimestre (31/03, 30/06, 30/09) | Fotos de meio de trimestre (30/04, 31/05, 31/07, 31/08) | Todas juntas |
|---|---|---|---|
| 0 a 30 dias | 49,5% (2.055) | 31,7% (2.375) | 40,0% (4.430) |
| 31 a 60 dias | 41,7% (1.449) | 41,9% (1.953) | 41,8% (3.402) |
| 61 a 90 dias | 15,9% (793) | 48,3% (1.541) | 37,3% (2.334) |
| 91 a 105 dias | 0,0% (153) | 39,9% (499) | 30,5% (652) |
| 106 a 120 dias | 0,0% (138) | 22,8% (281) | 15,3% (419) |

Por mês do trimestre (0 a 30 / 31 a 60 / 61 a 90 dias): mês 1, 29,5% / 52,6% / 47,2%; mês 2, 33,8% / 29,0% / 49,8%; mês 3, 49,5% / 41,7% / 15,9%. Os números entre parênteses são casos de treino; a tabela completa está no SCORING (seção 0, bloco `scoring-diagnostico`).

Dois motivos achatavam a curva:
1. **Empilhar fotos de fases diferentes** mistura padrões opostos (queda forte no fim do trimestre, subida no meio), que se cancelam e dão cerca de 40% plano.
2. **O formato "platô + queda"** (`logit = b0 + b1·max(0, idade − joelho)`) impõe chance constante antes do joelho, mesmo se os dados pedirem queda.

A data de referência (31/12) e os cortes de 30/06 e 30/09 são fins de trimestre.

## O que mudou, arquivo a arquivo
- `solution/scorer/config.py`: parâmetros novos (`V2_PSEUDO_COUNT = 0`, `FOQUE_HALF_FRACTION = 0,5`, `LIMPE_MIN_CHANCE = 0,02`, `AGE_SCAN_MAX_DAYS`, `QUARTER_END_PHASE`, `EXPLAIN_CURVE_AGES`, `CURVE_TABLE_AGES`, `DIAGNOSTIC_AGE_BANDS`, `INTRA_FOQUE_MAX_AGE`).
- `solution/scorer/features.py`: `quarter_phase`, `quarter_phase_series` e `same_phase` (fase do trimestre das fotos de treino). `as_of`, `open_at` e `training_set` ficaram como estavam, com as guardas.
- `solution/scorer/score.py`: curva v2 (`PhaseCurve`: faixas de 15 dias, PAVA, interpolação linear), `fit_model` com `FitConfig.curve` ("v2" padrão, "v1" mantida como "v1 (platô)"), limiares a partir da curva (Foque até a chance cair à metade da de um deal novo; Limpe com chance abaixo de 2% ou idade acima do maior ciclo já ganho até T; Reative no meio), `fallback` para todas as fotos se a fase não tem foto (não ocorreu). `pava_nonincreasing`, `BinnedCurve` e `fit_binned_curve` foram movidos do `validate.py` para cá (o `validate.py` continua exportando os nomes). O vendedor continua fora do modelo.
- `solution/scorer/validate.py`: backtest com v2 como curva do produto e v1 ao lado (`cuts_v1`, `media_cortes_v1`, `hoje_v1`); métrica de ordem dentro do Foque (`intra_foque`: Engaging abertos em T com idade de até 90 dias, mesma população para score v1, score v2, valor e recência, AUC e receita no top 20% nos 4 cortes e na média, com bootstrap); diagnóstico por fase (`diagnostico_fases`); sensibilidades (28/02 e a pseudo-contagem do ajuste único); auditoria "VAZADO" com a fase do corte; critério pré-registrado reportado para v2 e v1, com `post_backtest_change = true`.
- `solution/scorer/explain.py`: a frase principal dos cards Foque, Reative e Limpe passa a ser comparativa ("Deals com 81 dias fecharam 7% das vezes; os novos, 50%."), 2 a 4 frases, números por `fmt`; o prazo do Reative e a razão do Limpe dependem de a regra ser a chance ou o ciclo; as 5 linhas de "Como funciona o score" descrevem a curva nova (fotos da mesma fase, chance por idade, limiares).
- `solution/scorer/build.py`: seção `model` do `data.js` com os limiares e a regra do Limpe; o método `score_v1` entra na tabela "Teste no passado"; texto do critério declara a mudança pós-backtest; a nota "No Foque, ..." saiu e entrou a nota da ordem dentro do Foque.
- `solution/scorer/docs.py`: blocos AUTO novos (`scoring-diagnostico`, `scoring-correcao`, `scoring-foque-ordem`, `scoring-curva`, `scoring-modelos-v1`, `scoring-hoje-antes-depois`, `mc-ordem-foque`) e os antigos adaptados à v2 com a v1 ao lado; `foque-plato-sinal` removido.
- `solution/app/app.js`: caixa "Atenção" removida; resumos por lista do modo teste recalculados dos `deals` filtrados (n, ganhos, receita; com um vendedor escolhido, só contagens, sem porcentagem); textos das abas e do prazo conforme os limiares novos. O seletor de vendedores já era agrupado por manager (`optgroup`); só ganhou checagem.
- `solution/app/style.css`: removida a regra `.foque-warning`. `solution/app/index.html`: sem mudança. `solution/app/data-contract.md`: contrato atualizado (`model`, `outcome_summary`, `method`).
- `solution/tools/check_app.py`: três checagens novas (resumos do modo teste seguem filtros e sem % por vendedor; `optgroup` por manager; sem a caixa "Atenção") e o contrato confere os campos novos de `model`. Nenhuma checagem foi afrouxada: console, totais contra o SCORING e contra o JSON continuam.
- Testes: `test_score.py`, `test_explain.py`, `test_features.py`, `test_validate.py`, `test_build.py`, `test_readme.py` e `test_docs_numbers.py` (monotonicidade desde o dia 0; treino só com a fase e antes de T; isolamento das outras fases; fallback; fronteiras das categorias; limiares; métrica intra-Foque com casos de brinquedo e no JSON; frase comparativa; resumos).
- Documentos: `docs/SCORING.md` (reescrito: seção 0 da correção, curva v2, v1 × v2 × baselines, ordem dentro do Foque, limiares, diagnóstico, seção 9 com a declaração de mudança pós-backtest), `docs/MODEL_CARD.md`, `docs/DECISIONS.md` (nove linhas "Correção após revisão do Rafael — ..."), `README.md` (resumo com 5 frases e números novos, tabela de backtest, limitações, item "(execução delegada)" em "Onde a IA errou", evidências) e `process-log/README.md`.
- `solution/data/processed/*` e `solution/briefs/*` foram regenerados pelo build; `app/data.js` também.

## Antes e depois
**Backtest principal (receita ganha capturada pelo top 20%).** O critério pré-registrado passou para as duas curvas.

| Corte | v1 (platô) | v2 (faixas) | Valor | Recência |
|---|---|---|---|---|
| 30/06/2017 | 61,3% | 61,0% | 48,6% | 27,7% |
| 31/07/2017 | 57,9% | 57,4% | 48,7% | 12,8% |
| 31/08/2017 | 60,7% | 59,9% | 48,2% | 31,6% |
| 30/09/2017 | 64,8% | 71,7% | 47,1% | 46,8% |
| **Média** | **61,1%** | **62,5%** | 48,1% | 29,7% |

AUC média do score: 0,64 (v1) e 0,66 (v2). **A v2 piora a receita em três cortes (por menos de um ponto percentual) e melhora em um (cerca de sete pontos).** A média sobe por causa do corte de 30/09.

**Ordem dentro do Foque** (Engaging abertos em T com idade de até 90 dias; mesma população para todos; média dos 4 cortes):

| Método | AUC | Receita no top 20% |
|---|---|---|
| Score v2 | 0,52 | 52,5% |
| Score v1 | 0,51 | 49,7% |
| Ordenar por valor | 0,50 | 49,1% |
| Mais recentes primeiro | 0,56 | 23,5% |
| Aleatório (referência) | 0,50 | 20,1% |

Por corte, receita no top 20%: v2 50,5%, 49,2%, 50,4% e 59,9%; v1 50,7%, 49,2%, 50,4% e 48,5%. Só em 30/09 há diferença real (+11,4 pp, IC de +7,5 a +14,8 pp); em 31/07 e 31/08 os três métodos dão a mesma ordem, porque a curva v2 desses cortes é plana até além de 90 dias (as fotos de treino do 1º e do 2º mês do trimestre mostram os deals de 30 a 90 dias ganhando tanto quanto os novos). **A melhora dentro do Foque é pequena e concentrada em um corte; a AUC fica perto de um sorteio.**

**Listas de hoje (31/12/2017).**

| Lista | v1 (antes) | v2 (depois) |
|---|---|---|
| Foque | até 95 dias: 126 deals, US$ 300.790 | até 61 dias: 60 deals, US$ 123.253 |
| Reative | 96 a 138 dias: 172 deals, US$ 392.775 | 62 a 95 dias: 66 deals, US$ 177.537 |
| Limpe | mais de 138 dias: 1.291 deals, US$ 3.198.664 | mais de 95 dias: 1.463 deals, US$ 3.591.439 |
| Qualifique | 500 deals, US$ 1.073.986 | 500 deals, US$ 1.073.986 |

Os novos limites: Foque termina aos 61 dias (chance de 49,5% para um deal novo; a metade é 24,8%), e o Limpe começa depois de 95 dias, porque a chance cai abaixo de 2% antes de chegar ao maior ciclo já ganho (138 dias). Dos 1.463 do Limpe, 1.291 passam do maior ciclo e 172 entram só pela chance (US$ 392.775: são os deals que a v1 chamava de Reative).

**Chance de hoje, por idade.** v1: 40% de 0 a 95 dias. v2: 49,5% (0 dia), 49,0% (30 dias), 27,0% (60 dias), 6,6% (90 dias), 0,0% (105 dias ou mais).

**Top da Rosalina Dieter (aba Foque e, em seguida, Reative).**

| # | Antes (v1) | Depois (v2) |
|---|---|---|
| 1 | Betasoloin, GTK 500, 95 dias, chance 40%, score 100 | MG Special (conta não informada), 34 dias, chance 49%, score 11 (Foque) |
| 2 | Zoomit, MG Advanced, 81 dias, score 67 | MG Special (conta não informada), 51 dias, chance 37%, score 9 (Foque) |
| 3 | GTX Basic, 70 dias, score 39 | Betasoloin, GTK 500, 95 dias, chance 2%, score 50 (Reative, último dia) |
| 4 a 6 | três MG Special, 74, 51 e 34 dias, score 11 | Zoomit, MG Advanced, 81 dias, chance 14%, score 47 (Reative); GTX Basic, 70 dias, chance 17%, score 24 (Reative); MG Special, 74 dias, chance 16%, score 4 (Reative) |

Contagens da Rosalina: Foque 6, Reative 10, Limpe 34 (US$ 82.431) antes; Foque 2, Reative 4, Limpe 44 (US$ 88.788) depois. A aba Foque dela passou a ter só 2 deals, ambos MG Special de US$ 55; o GTK 500 de 95 dias saiu do Foque e está no último dia do Reative, com chance de 2%. O score 50 do GTK 500 vem da escala de log: o valor esperado (US$ 585) ainda é alto por causa do preço de US$ 26.768.

## Screenshots
Páginas em `file://`, Edge, `app/index.html#vendedor=Rosalina+Dieter&aba=Foque`:
- antes (página publicada): `screenshots/antes-correcao-rosalina-1280.png`, `screenshots/antes-correcao-rosalina-390.png`;
- depois: `screenshots/depois-correcao-rosalina-1280.png` (página inteira) e `screenshots/depois-correcao-rosalina-390.png` (primeira tela de 844 px).

Nos dois "depois": zero erros de console, pageerror e requestfailed, e a caixa "Atenção" não existe mais (nem o elemento `foque-warning`).

## Erros reais encontrados no caminho
1. **A receita de reaproveitamento não servia como estava.** A pseudo-contagem do ajuste único (20 deals rumo à taxa média em cada faixa) deixava a cauda sem nenhum ganho em 13% a 27% de chance (aos 730 dias: 26,9% em 30/06 e 13,1% em 30/09) e fazia o Foque dos cortes de 30/06 e 31/07 nunca terminar (limite de 730 dias); a AUC caía para 0,54 a 0,59. Descartei a pseudo-contagem por esse motivo medido (não por escolher o melhor número do backtest) e reportei a variante como sensibilidade. Mesmo assim, a escolha foi feita com o backtest da v1 à vista.
2. **A auditoria "VAZADO" mudou de conclusão.** O texto antigo dizia que o vazamento de parâmetros "custa pouco". Com a v2 (e a fase do corte), o modelo vazado ganha 7,2 pontos percentuais de receita em 30/09. O parágrafo foi reescrito: a curva v2 é flexível o bastante para o vazamento valer, e é isso que a mutação do futuro protege.
3. **Rascunhos do SCORING com afirmações erradas, pegas ao conferir com o JSON:** "6,9 pontos percentuais" onde a diferença é 7,0 (o texto passou a dizer "cerca de sete"); "dois pontos e meio" onde são 2,3; "a v2 supera a v1 no Brier em três de quatro cortes" onde são dois (fica uma fração de milésimo pior em 30/06 e 31/07); uma explicação do resíduo de calibração em 30/09 ("fotos que ganharam mais") que não medi (virou "não testei a causa"); "os deals de meio de trimestre sobem com a idade" (sobem até 90 dias e caem depois).
4. **Premissas de teste erradas, corrigidas ao rodar:** a captura no top 20% de 3 deals é 0,6 e não 1,0 (K = 0,6 deal); o fallback de fase de 31/07 usa duas fotos (31/03 e 30/04) e não uma; com 60 dias a chance da v2 (27,0%) é menor que 60% da de um deal novo, mas não menor que 50%; um deal sintético de ganho tardio acrescenta uma linha de treino em 31/03 e muda a curva legitimamente (só o maior ciclo é que não pode mudar); a regex do teste de frases lia "menos de 1%" como um "1%".
5. **Falhas de ferramenta, sem efeito no resultado:** um script Python enviado por stdin à linha de comando abriu o interpretador interativo e não aplicou nada (reaplicado como arquivo); um `-replace` do PowerShell escreveu `\n` literal num teste e quebrou a sintaxe (corrigido pela ferramenta de edição); o README estava com final de linha CRLF e o patch não achou o título (normalizado para LF); a primeira tentativa de cortar linhas do `validate.py` errou o número da linha e foi barrada pelo `assert`.
6. **Pré-requisito do teste de links.** O `README.md` já apontava para este arquivo antes de ele existir, e o teste de links quebrados acusou. Resolvido ao escrevê-lo.

## O que não ficou resolvido
- A melhora da v2 sobre a v1 está em um corte, e a v2 foi desenhada depois de ver o backtest: o PASSOU do critério não é teste às cegas (declarado no SCORING, MODEL_CARD e README).
- Três dos quatro cortes treinam com uma foto só (só vale a fase do trimestre do corte).
- A calibração do corte de 30/09 na faixa de 61 a 90 dias melhorou (de 45,6% para 33,7%), mas ainda fica acima do observado (6,7%).
- O teste de atributos não foi repetido sobre a v2.
- Largura da faixa, fase e os limiares de 50% e 2% foram escolhidos sem sensibilidade medida, exceto a pseudo-contagem.
- Entre os deals já resolvidos o score continua empatando com o valor: a vantagem do backtest completo vem de tirar os zumbis do topo.

## Verificação
Rodada na ordem pedida, depois de apagar `app/data.js`, `briefs/*.md` e `data/processed/snapshot_*.csv`: `python -B -m scorer.build --reference-date 2017-12-31`, `python -B -m pytest -p no:cacheprovider`, `python -B -m scorer.docs --check` e `python -B tools\check_app.py --prefix final` (27 checagens). Os quatro saíram com exit 0: build sem erro (Foque 60, Reative 66, Limpe 1.463, Qualifique 500 hoje), 229 testes passando, `scorer.docs --check` sem documento desatualizado e 27 de 27 checagens da interface. Os dois PNGs `depois-correcao-rosalina-*` foram tirados em seguida, com o `data.js` recém-gerado. Não toquei em `docs/ARQUITETURA_PRODUCAO.md` (de outro executor), em `solution/data/raw/` nem em `process-log/00_fase0_exploracao.md`.
