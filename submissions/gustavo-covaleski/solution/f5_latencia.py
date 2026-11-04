import os
import tempfile
import time

import numpy as np
import pandas as pd

from comum import OUT_DIR, SEED, ler_ds2, salvar_json


def main():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["TRIAGEM_RUNTIME_DIR"] = tmp  # runtime temporário: não suja runtime/
        os.environ.pop("TRIAGEM_MODO", None)
        import triagem
        triagem.carregar_modelo()
        triagem.carregar_politica()
        df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
        amostra = df[df["split_grupo"] == "holdout"].sample(1000, random_state=SEED)
        lat, faixas = [], []
        for t in amostra.itertuples():
            t0 = time.perf_counter()
            r = triagem.triar({"event_id": f"lat-{t.id}", "texto": t.Document})
            lat.append((time.perf_counter() - t0) * 1000)
            faixas.append(r["faixa"])
        n_log = sum(1 for _ in open(os.path.join(tmp, "decisoes.jsonl"), encoding="utf-8"))
    saida = {"n": 1000, "seed": SEED, "escopo": "triar() de ponta a ponta: idempotência (sqlite), mascaramento, classificação, faixa, log JSONL",
             "p50_ms": round(float(np.percentile(lat, 50)), 2), "p95_ms": round(float(np.percentile(lat, 95)), 2),
             "media_ms": round(float(np.mean(lat)), 2), "total_por_1000_s": round(sum(lat) / 1000, 2),
             "linhas_no_log": n_log, "faixas": pd.Series(faixas).value_counts().to_dict()}
    salvar_json(saida, "f5_latencia.json")
    print(saida)


if __name__ == "__main__":
    main()
