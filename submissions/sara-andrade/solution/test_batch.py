from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

try:
    from triage import route_ticket
except ImportError:
    from .triage import route_ticket

ROOT = Path(__file__).resolve().parents[1]
SOLUTION = Path(__file__).resolve().parent


def load_batch() -> pd.DataFrame:
    candidates = [
        ROOT / "data" / "all_tickets_processed_improved_v3.csv",
        ROOT / "all_tickets_processed_improved_v3.csv",
        Path("/mnt/data/all_tickets_processed_improved_v3.csv"),
    ]
    for path in candidates:
        if path.exists():
            df = pd.read_csv(path)
            sample = df.sample(100, random_state=42).copy()
            sample["text"] = sample["Document"]
            sample["expected_category"] = sample["Topic_group"]
            sample["domain_hint"] = "b2e_it"
            return sample[["text", "expected_category", "domain_hint"]]

    sample_path = SOLUTION / "examples" / "sample_tickets.csv"
    if sample_path.exists():
        return pd.read_csv(sample_path)

    raise FileNotFoundError("Não encontrei dataset completo nem solution/examples/sample_tickets.csv")


def main():
    df = load_batch()
    rows = []
    for _, row in df.iterrows():
        res = route_ticket(
            text=str(row["text"]),
            priority="Medium",
            channel="Internal portal" if row.get("domain_hint") == "b2e_it" else "Email",
            source_context=row.get("domain_hint", "auto"),
        )
        rows.append(
            {
                "route": res["route"],
                "domain": res["domain"],
                "predicted_topic": res["predicted_topic"],
                "topic_confidence": res["topic_confidence"],
                "expected_category": row.get("expected_category"),
                "text_preview": str(row["text"])[:140],
            }
        )

    out = pd.DataFrame(rows)
    output_dir = SOLUTION / "outputs" / "batch"
    output_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_dir / "batch_triage_results.csv", index=False)

    summary = out["route"].value_counts(normalize=False).to_dict()
    summary_pct = (out["route"].value_counts(normalize=True) * 100).round(1).to_dict()

    print("Distribuição de rotas:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nPercentual:")
    print(json.dumps(summary_pct, indent=2, ensure_ascii=False))
    print(f"\nArquivo salvo em: {output_dir / 'batch_triage_results.csv'}")


if __name__ == "__main__":
    main()
