"""
FASE 2c — Opus com prompt CAPRICHADO (definicoes do dataset + few-shot + regras de
desambiguacao) na MESMA amostra de 500. Salva detalhe POR CLASSE pra mostrar ONDE o
LLM erra vs TF-IDF. Testa a hipotese: erros do LLM se concentram em Miscellaneous /
Administrative rights (categorias de convencao). Chave lida de arquivo, nunca impressa.
"""
import time, random, sys
import concurrent.futures as cf
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
import anthropic

KEY_PATH = r"D:\Projetos\Case G4\data\anthropic_key.txt.txt"
D2 = r"D:\Projetos\Case G4\data\challenge-002-support\all_tickets_processed_improved_v3.csv"
MODEL_PATH = r"D:\Projetos\Case G4\solution-draft\model\ticket_classifier.joblib"
MODEL_ID = "claude-opus-4-8"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
PRICE_IN, PRICE_OUT = 5.0, 25.0

CATS = ["Access", "Administrative rights", "HR Support", "Hardware",
        "Internal Project", "Miscellaneous", "Purchase", "Storage"]

SYSTEM = """You are an IT service-desk ticket classifier for one specific organization. Classify each ticket into EXACTLY ONE of these 8 categories. Use THIS organization's definitions below — they are dataset-specific, not generic dictionary meanings.

- Hardware: physical devices and their connectivity — laptops, monitors, phones, RAM, cables, docking stations, meeting-room / AV equipment.
- HR Support: HR systems and people processes — new starters, leavers, leave/absence, timesheets, org changes, Oracle HR.
- Access: accounts, credentials and permissions to reach a system — passwords, user accounts, software licenses, Git / repository / Confluence access, joining a system as a user.
- Administrative rights: ELEVATED rights to install or update software on a machine — installing/upgrading Windows, Outlook, Exchange or other software that needs local admin.
- Storage: file, mailbox and disk storage — shared folders, mailbox almost full / quota, file permissions on folders, disk space.
- Purchase: procurement — purchase orders (PO), buying/ordering devices or items.
- Internal Project: internal engineering/project work — code, build pipelines, project environment setup.
- Miscellaneous: catch-all for one-off admin requests that do not fit the above — generic approvals, group-membership changes, name changes, and similar loose requests.

Disambiguation rules (follow the convention, not intuition):
- A plain approval, a group-membership add/remove, or a name change is Miscellaneous — even if it mentions access or a device.
- Installing or upgrading software that needs local admin is Administrative rights, NOT Access. Access is about being granted an account/permission/license, not installing software.
- A shared-folder or mailbox-quota request is Storage, NOT Access, even though it mentions permissions.

Respond with ONLY the exact category name, nothing else."""

_key = open(KEY_PATH, encoding="utf-8-sig").read().strip()
client = anthropic.Anthropic(api_key=_key, max_retries=4)


def match_cat(resp: str):
    r = resp.strip().strip('.').strip('"').strip().lower()
    for c in CATS:
        if c.lower() == r:
            return c
    hits = [c for c in CATS if c.lower() in r]
    return max(hits, key=len) if hits else None


def classify(messages):
    last = None
    for attempt in range(6):
        try:
            t0 = time.time()
            resp = client.messages.create(model=MODEL_ID, max_tokens=30, system=SYSTEM, messages=messages)
            dt = time.time() - t0
            out = "".join(b.text for b in resp.content if b.type == "text")
            return out, resp.usage.input_tokens, resp.usage.output_tokens, dt
        except anthropic.APIError as e:
            status = getattr(e, "status_code", None)
            if (isinstance(e, anthropic.APIConnectionError) or status == 429 or (status and status >= 500)) and attempt < 5:
                last = e
                time.sleep(min(2 ** attempt, 20) + random.random())
                continue
            raise
    raise last


def main():
    df = pd.read_csv(D2).dropna(subset=["Document", "Topic_group"])
    df = df[df["Document"].astype(str).str.strip() != ""]
    X, y = df["Document"].astype(str), df["Topic_group"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    train_df = pd.DataFrame({"text": Xtr.values, "label": ytr.values})
    test_df = pd.DataFrame({"text": Xte.values, "label": yte.values})
    sample = test_df.sample(n=N, random_state=1).reset_index(drop=True)

    # few-shot: 1 exemplo curto (>=40 chars) por categoria, do TREINO (sem vazamento)
    fewshot = []
    for c in CATS:
        sub = train_df[train_df.label == c].copy()
        sub["L"] = sub.text.str.len()
        cand = sub[sub.L >= 40].sort_values("L")
        row = (cand.iloc[0] if len(cand) else sub.sort_values("L").iloc[0])
        fewshot.append((row.text, c))
    fs_msgs = []
    for ex_text, ex_label in fewshot:
        fs_msgs += [{"role": "user", "content": ex_text}, {"role": "assistant", "content": ex_label}]
    print(f"Amostra: {len(sample)} tickets | few-shot: {len(fewshot)} exemplos | modelo: {MODEL_ID} (prompt caprichado)")

    # TF-IDF na mesma amostra
    pipe = joblib.load(MODEL_PATH)
    tfidf_pred = pipe.predict(sample["text"].tolist())

    # Opus-fair
    def run(i):
        msgs = fs_msgs + [{"role": "user", "content": sample.at[i, "text"][:4000]}]
        try:
            out, tin, tout, dt = classify(msgs)
            return i, match_cat(out), tin, tout, dt, None
        except Exception as e:
            return i, None, 0, 0, 0.0, f"{type(e).__name__}: {str(e)[:100]}"

    preds = [None] * len(sample)
    tin = tout = 0
    lat = 0.0
    errs = 0
    done = 0
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        for i, pred, a, b, dt, err in ex.map(run, range(len(sample))):
            preds[i] = pred
            tin += a; tout += b; lat += dt
            if err:
                errs += 1
            done += 1
            if done % 100 == 0:
                print(f"  ... {done}/{len(sample)}")

    sample["tfidf"] = tfidf_pred
    sample["opus"] = preds
    tfidf_acc = (sample["tfidf"] == sample["label"]).mean()
    opus_acc = (sample["opus"] == sample["label"]).mean()
    cost = tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT

    print("\n" + "=" * 72)
    print("OPUS CAPRICHADO vs TF-IDF — mesma amostra de 500")
    print("=" * 72)
    print(f"TF-IDF          : {tfidf_acc*100:.1f}%")
    print(f"Opus (ingenuo)  : 47.0%   (da Fase 2b, prompt cru)")
    print(f"Opus (caprichado): {opus_acc*100:.1f}%   custo US$ {cost:.3f} | {lat/len(sample)*1000:.0f} ms/ticket | erros {errs}")

    print("\n--- ACURACIA POR CLASSE (recall) — onde cada um erra ---")
    print(f"{'Categoria':<24}{'n':>5}{'TF-IDF':>9}{'Opus-fair':>11}")
    for c in CATS:
        sub = sample[sample["label"] == c]
        if len(sub) == 0:
            continue
        t = (sub["tfidf"] == c).mean() * 100
        o = (sub["opus"] == c).mean() * 100
        print(f"{c:<24}{len(sub):>5}{t:>8.0f}%{o:>10.0f}%")

    # pra onde o Opus manda os erros (confusao das piores classes)
    print("\n--- Para onde o Opus classifica 'Miscellaneous' e 'Administrative rights' reais ---")
    for c in ["Miscellaneous", "Administrative rights"]:
        sub = sample[sample["label"] == c]
        vc = sub["opus"].value_counts()
        print(f"  {c} (n={len(sub)}): " + ", ".join(f"{k}={v}" for k, v in vc.items()))


if __name__ == "__main__":
    main()
