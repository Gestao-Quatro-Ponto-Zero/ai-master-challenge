# PLAN — Challenge 002 (Redesign de Suporte) — Alan Gattiboni

Método: rolling-wave. Só o bloco atual vem detalhado. Ao fechar um bloco,
decupamos o próximo. Ciclo por tarefa: arquitetar, instruir Codinho, executar,
verificar, aprovar, commit.

Princípios: Incrementalidade, Modularidade, Zero dívida técnica.

---

## Bloco 0 — Fundação _(fechado)_

- [x] Fork do repo
- [x] Clone + branch `submission/alan-gattiboni`
- [x] README scaffold (template) + commit (`3e92232`)
- [x] Estrutura de pastas: `solution/`, `solution/datasets/`,
      `process-log/screenshots/`, `process-log/chat-exports/`, `docs/`
- [x] `docs/PLAN.md` criado e versionado
- [x] Ambiente confirmado: Python 3.12.4, `requirements.txt` congelado (pandas
      2.3.3, numpy 2.2.6, matplotlib 3.11.0, seaborn 0.13.2, scikit-learn 1.9.0,
      jupyterlab 4.6.1, ipykernel 7.3.0)
- [x] Datasets validados (`df.shape`, `df.columns`) e confrontados com o brief.
      Divergências: 8.469 tickets reais para o Dataset 1 (a contagem de ~30K do
      brief é linha física, não ticket); Dataset 1 sintético; datasets não
      cruzáveis. Insumo do Ato 1.
- [x] Seção `## Reprodução` na capa (`README.md`): pré-requisitos, setup do
      venv, download manual com os 2 links do Kaggle, sanity check dos
      `df.shape` (8.469 / 47.837)

---

## Bloco 1 — EDA adversarial _(fechado)_

Auditar cada fonte e concluir num veredito de qualidade. Onde o dado falha,
provar onde e como.

**Regras do bloco:**

- Cada hipótese (D1 sintético, nulos estruturais, não-cruzáveis, Miscellaneous
  preguiçoso) é uma pergunta testada para refutar ou comprovar.
- Cada achado é uma célula com evidência crua: contagem, amostra ou gráfico.
- Um módulo de auditoria por dataset, sem estado compartilhado.
- Bloco de auditoria e veredito. Medallion, gate e classificador são blocos
  posteriores.

- [x] **1.0** Scaffold do notebook: imports, load dos 2 CSVs com dtype seguro,
      esqueleto de seções. Roda e carrega sem erro.
- [x] **1.1** D1 — integridade e semântica dos nulos. Nulos 100% estruturais por
      `Ticket Status`, zero violações de coerência.
- [x] **1.2** D1 — sinteticidade. 100% das descrições com placeholder cru;
      metadados categóricos com entropia normalizada acima de 0,999 (uniformes,
      sem sinal de negócio).
- [x] **1.3** D2 — distribuição de classes. Top-3 em 66,18%; `Miscellaneous`
      difuso confirmado.
- [x] **1.4** D2 — sinal do texto. Vocabulário discriminativo por classe com
      ruído residual de pré-processamento.
- [x] **1.5** Cruzabilidade. Sem coluna, taxonomia ou identificador em comum.
- [x] **1.6** Veredito por fonte: dict `verdict` renderizado em tabela, com
      PASS/WARN/FAIL por dimensão.

**Pronto quando:** notebook roda ponta a ponta, cada hipótese testada com
evidência, veredito PASS/WARN/FAIL por fonte legível em minutos.

## Bloco 2 — Diagnóstico operacional _(a decupar)_

Gargalos, drivers de satisfação, desperdício quantificado.

## Bloco 3 — Proposta de automação _(a decupar)_

O que automatizar, o que não, fluxo desenhado ponta a ponta.

## Bloco 4 — Protótipo funcional _(a decupar)_

Classificador e o que o dado permitir. Métrica real em holdout.

## Bloco 5 — Empacotamento _(a decupar)_

README final, process log completo, PR.
