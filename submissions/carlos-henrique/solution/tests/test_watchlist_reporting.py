from pathlib import Path

def test_exact_report_and_figure_inventory():
    root=Path(__file__).parents[1]
    reports={p.name for p in (root/"reports").glob("watchlist-*.md")} | {p.name for p in (root/"reports").glob("intervention-watchlist.md")}
    assert reports == {"intervention-watchlist.md","watchlist-methodology.md","watchlist-rules.md","watchlist-validation.md","watchlist-explainability.md"}
    figures={p.name for p in (root/"reports/figures").glob("watchlist-*.png")}
    assert figures == {"watchlist-queue-distribution.png","watchlist-priority-distribution.png","watchlist-rule-overlap.png","watchlist-quality-confidence.png","watchlist-mrr-by-queue.png","watchlist-evidence-map.png"}
