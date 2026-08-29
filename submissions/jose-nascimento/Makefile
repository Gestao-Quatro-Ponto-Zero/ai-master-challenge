# ============================================================================
# Makefile — pipeline reprodutível em UM comando (Iterações 06–07)
# `make all` == `./run.sh` (fonte única de verdade; SEM lógica duplicada).
# Ver: solution/README.md e process-log/decisions/iteration-06-reproducibility-decisions.md
# ============================================================================
SHELL := /bin/bash
# Interpretador do pipeline: override via `make PYTHON=...` ou `PYTHON=... make`
# (mesma convenção do run.sh: `PY="${PYTHON:-python3}"`). Exportado para os
# recipes (inclusive `./run.sh` em `all`).
PYTHON ?= python3
export PYTHON
export PYTHONDONTWRITEBYTECODE := 1

.PHONY: all verify stage-01 stage-02 stage-03 stage-04 stage-05 stage-07 clean-derived

# `make` (default) e `make all` executam o MESMO pipeline do run.sh.
all:
	./run.sh

# Executa apenas o verificador estrutural (não regenera nada).
# Nota: com falha, o GNU make encapsula o exit 1 do script como exit 2
# (convenção do make); o script direto retorna exit 1.
verify:
	$(PYTHON) solution/src/06_verify_pipeline.py

# Estágios individuais (úteis para debug; `all` é a fonte única da entrega).
stage-01:
	$(PYTHON) solution/src/01_ingest_audit.py

stage-02:
	$(PYTHON) solution/src/02_reconcile_churn.py

stage-03:
	$(PYTHON) solution/src/03_root_cause.py

stage-04:
	$(PYTHON) solution/src/04_lifecycle_watchlist.py

stage-05:
	$(PYTHON) solution/src/05_actions_impact.py

stage-07:
	$(PYTHON) solution/src/07_generate_executive_report.py

# ---------------------------------------------------------------------------
# clean-derived — remove SOMENTE artefatos derivados regeneráveis (lista
# explícita). NUNCA apaga data/raw/ (dados commitados) nem process-log/.
# Regeneração integral: ./run.sh (ou make all).
# ---------------------------------------------------------------------------
DERIVED := \
	solution/evidence/01_audit_report.md \
	solution/evidence/02_consistency_report.md \
	solution/evidence/03_root_cause_report.md \
	solution/evidence/04_lifecycle_watchlist_report.md \
	solution/evidence/05_action_plan.md \
	solution/report-executivo.md \
	solution/data/processed/account_month.csv \
	solution/data/processed/README.md \
	solution/docs/analytical-contract.md \
	solution/out/tables/t01_monthly_series.csv \
	solution/out/tables/t02_cohort_km.csv \
	solution/out/tables/t02a_cohort_km_month.csv \
	solution/out/tables/t02b_cohort_km_at_risk.csv \
	solution/out/tables/t03_onboarding_buckets.csv \
	solution/out/tables/t03b_onboarding_accounts.csv \
	solution/out/tables/t03c_cac_equivalent.csv \
	solution/out/tables/t05_usage_monthly.csv \
	solution/out/tables/t06_support_monthly.csv \
	solution/out/tables/t07_segments.csv \
	solution/out/tables/t08_reasons.csv \
	solution/out/tables/t09_causality.csv \
	solution/out/tables/t10_hypothesis_verdicts.csv \
	solution/out/tables/t11_account_lifecycle.csv \
	solution/out/tables/t12_reactivation_recurrence.csv \
	solution/out/tables/t13_state_cycles.csv \
	solution/out/tables/t14_backtest_temporal.csv \
	solution/out/tables/t14b_backtest_detail.csv \
	solution/out/tables/t15_priority_segments.csv \
	solution/out/tables/t15b_segment_overlap.csv \
	solution/out/tables/t16_watchlist_top20.csv \
	solution/out/tables/t17_rank_comparison.csv \
	solution/out/tables/t18_actions_prioritized.csv \
	solution/out/tables/t19_impact_sensitivity.csv \
	solution/out/tables/t20_measurement_plan.csv \
	solution/out/tables/t21_watchlist_split_actions.csv \
	solution/out/charts/a_monthly_events_and_rate.png \
	solution/out/charts/b_km_by_signup_quarter.png \
	solution/out/charts/c_onboarding_exposure_by_duration.png \
	solution/out/charts/d_usage_volume_vs_intensity.png \
	solution/out/charts/It04_c_lifecycle_vs_current_mrr.png \
	solution/out/charts/It04_d_backtest_lift.png

clean-derived:
	@test -f solution/src/01_ingest_audit.py || { echo "ERRO: rode do diretório da submissão (submissions/jose-nascimento/)." >&2; exit 1; }
	@test -f solution/data/raw/ravenstack_accounts.csv || { echo "ERRO: data/raw/ ausente — recusando apagar qualquer coisa." >&2; exit 1; }
	@echo "Aviso: apagando APENAS os artefatos derivados regeneráveis da lista explícita abaixo ($(words $(DERIVED)) arquivos — contagem derivada da lista, não hardcoded)."
	@echo "       data/raw/ e process-log/ NUNCA são apagados. Regenere com ./run.sh (ou make all)."
	@rm -f $(DERIVED)
	@echo "OK: artefatos derivados removidos ($(words $(DERIVED)) arquivos; ver lista acima)."