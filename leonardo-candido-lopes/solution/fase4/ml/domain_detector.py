"""Fase 4 — Etapa 5: detector de domínio (roda ANTES do classificador IT).
Treino: python domain_detector.py   |   Uso: DomainDetector.load().predict(texto)

Saídas: IT_INTERNAL | FINANCIAL_COMMERCIAL | OUT_OF_SCOPE | INDETERMINATE
- Classificador binário TF-IDF + LR: positivos = D2 (split de TREINO apenas), negativos = D1 com Ticket Subject
  em {Refund request, Delivery problem, Payment issue, Product recommendation, Cancellation request}.
- INDETERMINATE: < MIN_TOKENS tokens úteis OU confiança do detector max(p,1-p) < t_uncertain (1º percentil no val).
- OUT_OF_SCOPE: similaridade cosseno máxima com os exemplos de treino < t_oos (1º percentil no val in-domain).
- v1 (descartada): banda fixa 0,30/0,70 + cobertura de vocabulário -> não empírica; 'company lunch' saía IT_INTERNAL.
"""
import json, joblib
import numpy as np, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
import re
from collections import Counter
from text_prep import preprocess, _stem

# Tokens de estilo (saudação/fecho/dias/meses) — mesma lista de boilerplate da Fase 2 (analysis/eda_d2_clean.py), stemizada.
# Removidos para que o detector não aprenda "e-mail corporativo (D2) vs. template B2C (D1)" em vez de domínio.
_STYLE = {_stem(w) for w in ("hi hello dear please thank thanks regards kind best pm am re sent monday tuesday wednesday thursday friday "
          "saturday sunday january february march april may june july august september october november december fw fwd cheers ca la si help need team guys").split()}
TEMPLATE_MIN_COUNT = 20   # frases do D1 que se repetem em >= 20 tickets são templates (aleatórios, independentes do assunto) -> removidas


def preprocess_domain(text):
    return " ".join(t for t in preprocess(text).split() if t not in _STYLE)


def d1_negative_text(df):
    """Assunto + frases da descrição que NÃO são templates. Evidência: as frases-template técnicas
    (ex.: 'I'm unable to access my account') aparecem aleatoriamente em tickets de reembolso/entrega (variáveis independentes, Fase 2)."""
    split = lambda t: [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", t) if x.strip()]
    sents = df["Ticket Description"].map(split)
    cnt = Counter(x for l in sents for x in set(l))
    resid = sents.map(lambda l: " ".join(x for x in l if cnt[x] < TEMPLATE_MIN_COUNT))
    return df["Ticket Subject"] + ". " + resid, int(sum(1 for v in cnt.values() if v >= TEMPLATE_MIN_COUNT))

SEED = 42
NEG_SUBJECTS = ["Refund request", "Delivery problem", "Payment issue", "Product recommendation", "Cancellation request"]
EXCLUDED_SUBJECTS_NOTE = "Assuntos técnicos B2C do D1 (Software bug, Hardware issue, Account access, Network problem etc.) NÃO usados no treino: ambíguos com TI."
MIN_TOKENS = 2
ABSTAIN_Q = 0.01   # limiares = 1º percentil no val in-domain (aceita-se ~1% de abstenção em casos conhecidos)
PATH = "model/domain_detector.pkl"


class DomainDetector:
    """v2: limiares empíricos (abstenção-alvo de 1% no val in-domain) para incerteza e OUT_OF_SCOPE."""
    def __init__(self, pipe, t_uncertain, t_oos, ref_matrix):
        self.pipe, self.t_uncertain, self.t_oos, self.ref = pipe, t_uncertain, t_oos, ref_matrix

    def max_sim(self, texts):
        """similaridade cosseno máxima com os exemplos de treino (IT + FC) no espaço TF-IDF do detector."""
        X = self.pipe.named_steps["tfidf"].transform(texts)
        return np.asarray((X @ self.ref.T).max(axis=1).todense()).ravel()

    def predict(self, text):
        pp = preprocess_domain(text); n = len(pp.split())
        p_it = float(self.pipe.predict_proba([text])[0][list(self.pipe.classes_).index("IT")])
        conf = max(p_it, 1 - p_it); sim = float(self.max_sim([text])[0])
        if n < MIN_TOKENS:
            d, why = "INDETERMINATE", f"apenas {n} token(s) útil(eis) após pré-processamento (< {MIN_TOKENS})"
        elif sim < self.t_oos:
            d, why = "OUT_OF_SCOPE", f"similaridade máx. com treino {sim:.3f} < t_oos {self.t_oos:.3f}"
        elif conf < self.t_uncertain:
            d, why = "INDETERMINATE", f"confiança do detector {conf:.3f} < t_uncertain {self.t_uncertain:.3f}"
        else:
            d = "IT_INTERNAL" if p_it >= 0.5 else "FINANCIAL_COMMERCIAL"
            why = f"P(IT)={p_it:.3f}; confiança {conf:.3f} >= {self.t_uncertain:.3f}; sim {sim:.3f} >= {self.t_oos:.3f}"
        return dict(domain=d, p_it=round(p_it, 4), detector_conf=round(conf, 4), max_sim_train=round(sim, 4), n_tokens=n, reason=why)

    def save(self, path=PATH): joblib.dump(self, path)

    @staticmethod
    def load(path=PATH): return joblib.load(path)


def train():
    tr = pd.read_csv("splits/train.csv"); va = pd.read_csv("splits/val.csv")
    d1 = pd.read_csv("../../data/customer_support_tickets.csv")
    neg = d1[d1["Ticket Subject"].isin(NEG_SUBJECTS)].copy()
    d1["text"], n_templates = d1_negative_text(d1)
    neg = d1[d1["Ticket Subject"].isin(NEG_SUBJECTS)].copy()
    other_d1 = d1[~d1["Ticket Subject"].isin(NEG_SUBJECTS)].copy()
    # balanceamento por amostragem do lado positivo (D2 treino) para ~2x negativos; class_weight='balanced' no LR
    pos_tr = tr.sample(n=min(len(tr), 3 * len(neg)), random_state=SEED)
    neg_tr, neg_va = train_test_split(neg, test_size=0.25, random_state=SEED, stratify=neg["Ticket Subject"])
    pos_va = va.sample(n=min(len(va), 3 * len(neg_va)), random_state=SEED)
    Xtr = pd.concat([pos_tr.Document, neg_tr.text]); ytr = ["IT"] * len(pos_tr) + ["FC"] * len(neg_tr)
    Xva = pd.concat([pos_va.Document, neg_va.text]); yva = np.array(["IT"] * len(pos_va) + ["FC"] * len(neg_va))
    pipe = Pipeline([("tfidf", TfidfVectorizer(preprocessor=preprocess_domain, ngram_range=(1, 2), sublinear_tf=True, min_df=2, max_features=50000)),
                     ("clf", LogisticRegression(C=1.0, max_iter=1000, class_weight="balanced"))]).fit(Xtr, ytr)
    pit = pipe.predict_proba(Xva)[:, list(pipe.classes_).index("IT")]
    # limiares empíricos: menor th_it com precisão IT >= 0.99 no val; maior th_fc com precisão FC >= 0.99
    grid = np.round(np.arange(0.05, 0.96, 0.05), 2); tbl = []
    for t in grid:
        mi = pit >= t; mf = pit <= t
        tbl.append(dict(t=float(t), it_cov=round(float(mi[yva == "IT"].mean()), 4), it_prec=round(float((yva[mi] == "IT").mean()), 4) if mi.any() else None,
                        fc_cov=round(float(mf[yva == "FC"].mean()), 4), fc_prec=round(float((yva[mf] == "FC").mean()), 4) if mf.any() else None))
    ref = pipe.named_steps["tfidf"].transform(Xtr)
    det = DomainDetector(pipe, 0.0, 0.0, ref)
    conf_va = np.maximum(pit, 1 - pit); sim_va = det.max_sim(Xva)
    t_uncertain = float(np.quantile(conf_va, ABSTAIN_Q)); t_oos = float(np.quantile(sim_va, ABSTAIN_Q))
    det.t_uncertain, det.t_oos = round(t_uncertain, 4), round(t_oos, 4)
    # referência: similaridade máx. de textos D1 técnicos (não usados) e de casos OOS não existem no dado -> reportar distribuição
    pred = np.where(pit >= 0.5, "IT", "FC")
    # D1 técnicos (não usados no treino): para onde vão?
    o = [det.predict(x)["domain"] for x in other_d1.text.sample(500, random_state=SEED)]
    meta = dict(n_d1_template_sentences_removed=n_templates, neg_subjects=NEG_SUBJECTS, n_neg_total=int(len(neg)), n_neg_train=int(len(neg_tr)), n_neg_val=int(len(neg_va)),
                n_pos_train=int(len(pos_tr)), n_pos_val=int(len(pos_va)), excluded_note=EXCLUDED_SUBJECTS_NOTE,
                val_f1_macro_at_0_5=round(float(f1_score(yva, pred, average="macro")), 4), val_report=classification_report(yva, pred, digits=4, output_dict=True),
                threshold_table_val=tbl, t_uncertain=det.t_uncertain, t_oos=det.t_oos, abstain_quantile=ABSTAIN_Q, min_tokens=MIN_TOKENS, val_conf_quantiles=np.quantile(conf_va,[0,.01,.05,.5]).round(4).tolist(), val_sim_quantiles=np.quantile(sim_va,[0,.01,.05,.5]).round(4).tolist(),
                d1_technical_sample500_domains=pd.Series(o).value_counts().to_dict(),
                top_features_IT=[], top_features_FC=[])
    coef = pipe.named_steps["clf"].coef_[0]; fn = pipe.named_steps["tfidf"].get_feature_names_out()
    sgn = 1 if pipe.classes_[1] == "IT" else -1
    order = np.argsort(sgn * coef)
    meta["top_features_IT"] = fn[order[-20:]][::-1].tolist(); meta["top_features_FC"] = fn[order[:20]].tolist()
    det.save()
    json.dump(meta, open("evaluation/domain_detector_results.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: meta[k] for k in ["val_f1_macro_at_0_5", "t_uncertain", "t_oos", "val_conf_quantiles", "val_sim_quantiles", "d1_technical_sample500_domains", "top_features_IT", "top_features_FC"]}, indent=1))


if __name__ == "__main__":
    import domain_detector  # garante que o pickle referencie domain_detector.DomainDetector (não __main__)
    domain_detector.train()
