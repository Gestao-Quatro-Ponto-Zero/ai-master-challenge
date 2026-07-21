"""
FASE 2b — Comparacao TF-IDF vs LLM zero-shot (Haiku / Sonnet / Opus).
Mede acuracia HONESTA na MESMA amostra do conjunto de teste + custo real + latencia.
A chave e lida de um arquivo em tempo de execucao e NUNCA e impressa.
"""
import argparse, time, sys, random
import concurrent.futures as cf
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
import anthropic

KEY_PATH = r"D:\Projetos\Case G4\data\anthropic_key.txt.txt"
D2 = r"D:\Projetos\Case G4\data\challenge-002-support\all_tickets_processed_improved_v3.csv"
MODEL_PATH = r"D:\Projetos\Case G4\solution-draft\model\ticket_classifier.joblib"

CATS = ["Access", "Administrative rights", "HR Support", "Hardware",
        "Internal Project", "Miscellaneous", "Purchase", "Storage"]

MODEL_IDS = {"haiku": "claude-haiku-4-5", "sonnet": "claude-sonnet-5", "opus": "claude-opus-4-8"}
# precos por 1M tokens (input, output) — Sonnet em preco introdutorio (vale ate 2026-08-31)
PRICES = {"haiku": (1.0, 5.0), "sonnet": (2.0, 10.0), "opus": (5.0, 25.0)}

SYSTEM = (
    "You are an IT support ticket classifier. Classify the ticket into EXACTLY ONE of these "
    "8 categories, using the exact category name:\n"
    "Access, Administrative rights, HR Support, Hardware, Internal Project, Miscellaneous, Purchase, Storage.\n"
    "Respond with ONLY the category name and nothing else."
)

# chave lida do arquivo — nunca impressa
_key = open(KEY_PATH, encoding="utf-8-sig").read().strip()
client = anthropic.Anthropic(api_key=_key, max_retries=4)


def match_cat(resp: str):
    r = resp.strip().strip('.').strip('"').strip().lower()
    for c in CATS:
        if c.lower() == r:
            return c
    hits = [c for c in CATS if c.lower() in r]
    if hits:
        return max(hits, key=len)  # prefere o nome mais longo (evita match espurio curto)
    return None


def classify(model_key: str, text: str):
    kwargs = dict(model=MODEL_IDS[model_key], max_tokens=30, system=SYSTEM,
                  messages=[{"role": "user", "content": text[:4000]}])
    if model_key == "sonnet":
        kwargs["thinking"] = {"type": "disabled"}  # Sonnet 5 liga adaptive por padrao; desligar
    last = None
    for attempt in range(6):
        try:
            t0 = time.time()
            resp = client.messages.create(**kwargs)
            dt = time.time() - t0
            out = "".join(b.text for b in resp.content if b.type == "text")
            return out, resp.usage.input_tokens, resp.usage.output_tokens, dt
        except anthropic.APIError as e:
            status = getattr(e, "status_code", None)
            retryable = isinstance(e, anthropic.APIConnectionError) or status == 429 or (status is not None and status >= 500)
            if retryable and attempt < 5:
                last = e
                time.sleep(min(2 ** attempt, 20) + random.random())
                continue
            raise
    raise last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--models", default="haiku,sonnet,opus")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    # recria o MESMO split do TF-IDF e amostra N do conjunto de teste
    df = pd.read_csv(D2).dropna(subset=["Document", "Topic_group"])
    df = df[df["Document"].astype(str).str.strip() != ""]
    X, y = df["Document"].astype(str), df["Topic_group"]
    _, Xte, _, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    test_df = pd.DataFrame({"text": Xte.values, "label": yte.values})
    sample = test_df.sample(n=args.n, random_state=1).reset_index(drop=True)
    print(f"Amostra: {len(sample)} tickets do conjunto de teste | modelos: {models}")

    # baseline TF-IDF na MESMA amostra
    pipe = joblib.load(MODEL_PATH)
    tfidf_pred = pipe.predict(sample["text"].tolist())
    tfidf_acc = (tfidf_pred == sample["label"].values).mean()
    print(f"\nTF-IDF (mesma amostra): acuracia = {tfidf_acc*100:.1f}%")

    # LLMs
    tasks = [(m, i, sample.at[i, "text"], sample.at[i, "label"]) for m in models for i in range(len(sample))]
    stats = {m: dict(correct=0, unmatched=0, err=0, tin=0, tout=0, lat=0.0, n=0) for m in models}
    err_samples = []

    def run(task):
        m, i, text, true = task
        try:
            out, tin, tout, dt = classify(m, text)
            pred = match_cat(out)
            return (m, pred, true, tin, tout, dt, None, out)
        except Exception as e:
            return (m, None, true, 0, 0, 0.0, f"{type(e).__name__}: {str(e)[:120]}", None)

    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for (m, pred, true, tin, tout, dt, err, raw) in ex.map(run, tasks):
            s = stats[m]
            s["n"] += 1; s["tin"] += tin; s["tout"] += tout; s["lat"] += dt
            if err:
                s["err"] += 1
                if len(err_samples) < 5:
                    err_samples.append(err)
            elif pred is None:
                s["unmatched"] += 1
                if len(err_samples) < 5:
                    err_samples.append(f"unmatched output: {raw!r}")
            elif pred == true:
                s["correct"] += 1
            done += 1
            if done % 200 == 0:
                print(f"  ... {done}/{len(tasks)} chamadas")

    # resultados
    print("\n" + "=" * 78)
    print(f"RESULTADO — acuracia na mesma amostra de {len(sample)} tickets")
    print("=" * 78)
    print(f"{'Modelo':<14}{'Acuracia':>10}{'Nao-parse':>11}{'Erros':>7}{'Custo US$':>11}{'ms/ticket':>11}")
    print(f"{'TF-IDF':<14}{tfidf_acc*100:>9.1f}%{'-':>11}{'-':>7}{'~0.00':>11}{'<1':>11}")
    for m in models:
        s = stats[m]
        acc = s["correct"] / s["n"] if s["n"] else 0
        pin, pout = PRICES[m]
        cost = s["tin"] / 1e6 * pin + s["tout"] / 1e6 * pout
        msper = (s["lat"] / s["n"] * 1000) if s["n"] else 0
        print(f"{m:<14}{acc*100:>9.1f}%{s['unmatched']:>11}{s['err']:>7}{cost:>11.4f}{msper:>11.0f}")

    total_cost = sum(stats[m]["tin"] / 1e6 * PRICES[m][0] + stats[m]["tout"] / 1e6 * PRICES[m][1] for m in models)
    print(f"\nCusto total gasto: US$ {total_cost:.4f}")
    if err_samples:
        print("\nAmostras de erro/nao-parse:")
        for e in err_samples:
            print("  -", e)
    # projecao de producao (passe completo nos 47.837)
    print("\n--- Projecao: custo de 1 passe completo nos 47.837 tickets ---")
    for m in models:
        s = stats[m]
        if s["n"]:
            scale = 47837 / s["n"]
            pin, pout = PRICES[m]
            proj = (s["tin"] * scale) / 1e6 * pin + (s["tout"] * scale) / 1e6 * pout
            print(f"  {m:<8}: ~US$ {proj:.0f}")
    print("  TF-IDF  : ~US$ 0 (roda local)")


if __name__ == "__main__":
    main()
