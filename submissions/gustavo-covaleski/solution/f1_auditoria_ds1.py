import re
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import chisquare, kruskal
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_transformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from comum import OUT_DIR, REVISAO_DIR, SEED, ler_ds1, salvar_csv_excel, salvar_json

VOLUME_BRIEF = 30000
RE_TEMPLATE = re.compile(r"\{[^{}]+\}")
RE_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
SUSPEITA_T3 = "variável de tempo sob suspeita (T3)"


def pct(x, n):
    return round(100 * x / n, 2) if n else None


def t1(df):
    return {"linhas": len(df), "ticket_id_unicos": int(df["Ticket ID"].nunique()), "volume_brief": VOLUME_BRIEF}


def t2(df):
    r = {}
    for c in ["Ticket Description", "Ticket Subject", "Resolution"]:
        s = df[c].dropna().astype(str)
        achados = s.str.findall(RE_TEMPLATE)
        cont = Counter(m for lst in achados for m in lst)
        r[c] = {
            "pct_linhas_com_marcador": pct((achados.str.len() > 0).sum(), len(df)),
            "n_linhas_com_marcador": int((achados.str.len() > 0).sum()),
            "top5_marcadores": cont.most_common(5),
        }
    return r


def t3(df):
    r = {}
    for c in ["First Response Time", "Time to Resolution"]:
        ts = pd.to_datetime(df[c], errors="coerce")
        nao_nulo = df[c].notna().sum()
        r[c] = {
            "tipo": "timestamp" if ts.notna().sum() == nao_nulo else "misto/duração",
            "min": str(ts.min()), "max": str(ts.max()), "pct_nulo": pct(df[c].isna().sum(), len(df)),
        }
    frt, ttr = pd.to_datetime(df["First Response Time"]), pd.to_datetime(df["Time to Resolution"])
    closed = (df["Ticket Status"] == "Closed") & frt.notna() & ttr.notna()
    antes = (ttr < frt) & closed
    r["closed_com_os_dois"] = int(closed.sum())
    r["n_resolucao_antes_1a_resposta"] = int(antes.sum())
    r["pct_resolucao_antes_1a_resposta"] = pct(antes.sum(), closed.sum())
    return r


def duracao_h(df):
    return (pd.to_datetime(df["Time to Resolution"]) - pd.to_datetime(df["First Response Time"])).dt.total_seconds() / 3600


def t4(df):
    cols = {}
    for c in df.columns:
        if df[c].dtype == object or str(df[c].dtype).startswith("str"):
            amostra = df[c].dropna().astype(str).head(200)
            if len(amostra) and amostra.str.match(r"^\d{4}-\d{2}-\d{2}").all():
                ts = pd.to_datetime(df[c], errors="coerce")
                cols[c] = {"min": str(ts.min()), "max": str(ts.max())}
    candidatos = [c for c in df.columns if re.search(r"open|creat|abert|submit", c, re.I)]
    return {"colunas_de_data": cols, "colunas_candidatas_a_abertura": candidatos,
            "existe_data_de_abertura": bool(candidatos)}


def t5(df, usar_duracao):
    y_all = df["Customer Satisfaction Rating"]
    r = {
        "contagem_por_nota": {str(int(k)): int(v) for k, v in y_all.value_counts().sort_index().items()},
        "pct_nulo": pct(y_all.isna().sum(), len(df)),
        "nulos_por_status": df.assign(nulo=y_all.isna()).groupby("Ticket Status")["nulo"].agg(["sum", "count"])
        .rename(columns={"sum": "nulos", "count": "total"}).to_dict(orient="index"),
    }
    obs = y_all.value_counts().sort_index().values
    q = chisquare(obs)
    r["quiquadrado_uniforme"] = {"estatistica": round(float(q.statistic), 4), "p": round(float(q.pvalue), 4)}

    sub = df[y_all.notna()].copy()
    sub["duracao_h"] = duracao_h(sub)
    y = sub["Customer Satisfaction Rating"].astype(int).values
    cats = ["Ticket Type", "Ticket Priority", "Ticket Channel", "Product Purchased", "Customer Gender"]
    cv = StratifiedKFold(5, shuffle=True, random_state=SEED)

    def avaliar(nums, rotulo):
        pre = make_column_transformer((OneHotEncoder(handle_unknown="ignore"), cats), (StandardScaler(), nums))
        modelo = make_pipeline(pre, LogisticRegression(max_iter=2000))
        s = cross_validate(modelo, sub[cats + nums], rotulo, cv=cv, scoring=["accuracy", "f1_macro"])
        return {m: {"media": round(float(s[f"test_{m}"].mean()), 4), "dp": round(float(s[f"test_{m}"].std()), 4)}
                for m in ["accuracy", "f1_macro"]}

    rng = np.random.default_rng(SEED)
    y_emb = rng.permutation(y)
    maj = np.bincount(y).argmax()
    modelos = {"n": int(len(sub)),
               "classe_majoritaria": {"classe": int(maj), "accuracy": round(float((y == maj).mean()), 4),
                                      "f1_macro": round(float(_f1_maj(y, maj)), 4)},
               "modelo_sem_duracao": avaliar(["Customer Age"], y),
               "rotulo_embaralhado_sem_duracao": avaliar(["Customer Age"], y_emb)}
    if usar_duracao:
        modelos["modelo_com_duracao"] = avaliar(["Customer Age", "duracao_h"], y)
        modelos["rotulo_embaralhado_com_duracao"] = avaliar(["Customer Age", "duracao_h"], y_emb)
    r["modelo"] = modelos
    return r


def _f1_maj(y, maj):
    from sklearn.metrics import f1_score
    return f1_score(y, np.full_like(y, maj), average="macro")


def t6(df):
    d = df[df["Ticket Status"] == "Closed"].copy()
    d["duracao_h"] = duracao_h(d)
    d = d[d["duracao_h"] > 0]
    r = {"aviso": SUSPEITA_T3, "n_closed_duracao_positiva": int(len(d))}
    for c in ["Ticket Priority", "Ticket Channel", "Ticket Type"]:
        grupos = {k: g["duracao_h"].values for k, g in d.groupby(c)}
        h = kruskal(*grupos.values())
        r[c] = {"grupos": {k: {"n": int(len(v)), "mediana_h": round(float(np.median(v)), 2)} for k, v in grupos.items()},
                "H": round(float(h.statistic), 4), "p": round(float(h.pvalue), 4)}
    return r


def t7(df):
    st = df["Ticket Status"]
    def cruz(col):
        return df.assign(nulo=df[col].isna()).groupby("Ticket Status")["nulo"].agg(["sum", "count"]) \
            .rename(columns={"sum": "nulos", "count": "total"}).to_dict(orient="index")
    return {"contagem_por_status": st.value_counts().to_dict(),
            "pct_nao_closed": pct((st != "Closed").sum(), len(df)),
            "status_x_1a_resposta_nula": cruz("First Response Time"),
            "status_x_resolucao_nula": cruz("Time to Resolution"),
            "status_x_csat_nulo": cruz("Customer Satisfaction Rating")}


def t8(df):
    res = df["Resolution"]
    top = res.value_counts().head(5)
    # texto de ticket não entra no repositório: os 5 valores vão para planning/
    salvar_csv_excel(pd.DataFrame({"resolution": [str(k)[:80] for k in top.index], "n": top.values}),
                     REVISAO_DIR / "f1_ds1_resolution_top5.csv")
    return {"ticket_type_valores": df["Ticket Type"].value_counts().to_dict(),
            "n_tipos": int(df["Ticket Type"].nunique()), "tipos_no_brief": 3,
            "colunas_dado_pessoal": ["Customer Name", "Customer Email", "Customer Age", "Customer Gender"],
            "emails_validos_regex": int(df["Customer Email"].dropna().astype(str).str.match(RE_EMAIL).sum()),
            "emails_nao_nulos": int(df["Customer Email"].notna().sum()),
            "resolution_pct_nulo": pct(res.isna().sum(), len(df)),
            "resolution_valores_unicos": int(res.nunique()),
            "resolution_top5_contagens": [int(v) for v in top.values]}


def main():
    df = ler_ds1()
    a = {"T1": t1(df), "T2": t2(df), "T3": t3(df), "T4": t4(df)}
    t3_confirma = a["T3"]["pct_resolucao_antes_1a_resposta"] > 10
    a["T5"] = t5(df, usar_duracao=True)
    a["T6"], a["T7"], a["T8"] = t6(df), t7(df), t8(df)
    salvar_json(a, "f1_ds1_auditoria.json")

    m = a["T5"]["modelo"]
    f1_mod, f1_emb = m["modelo_sem_duracao"]["f1_macro"], m["rotulo_embaralhado_sem_duracao"]["f1_macro"]
    sem_sinal_modelo = f1_mod["media"] - f1_emb["media"] < 2 * max(f1_mod["dp"], f1_emb["dp"])
    uniforme = a["T5"]["quiquadrado_uniforme"]["p"] >= 0.05
    t6_ps = [a["T6"][c]["p"] for c in ["Ticket Priority", "Ticket Channel", "Ticket Type"]]
    pct_tpl = a["T2"]["Ticket Description"]["pct_linhas_com_marcador"]

    def conf(b):
        return "s" if b else "n"

    fatos = [
        ("T1", "~8.469 linhas, brief fala em ~30 mil",
         f"{a['T1']['linhas']} linhas, {a['T1']['ticket_id_unicos']} Ticket ID únicos",
         conf(a["T1"]["linhas"] < VOLUME_BRIEF / 2),
         "Uma linha no README; extrapolações usam o volume do brief (30 mil) como premissa editável"),
        ("T2", "variável de template não preenchida",
         f"Description {pct_tpl}%; Subject {a['T2']['Ticket Subject']['pct_linhas_com_marcador']}%; "
         f"Resolution {a['T2']['Resolution']['pct_linhas_com_marcador']}%",
         conf(pct_tpl > 0), "Texto do DS1 fora de qualquer NLP; DS1 entra só por metadados"),
        ("T3", "~49,3% dos Closed com resolução antes da 1ª resposta",
         f"{a['T3']['pct_resolucao_antes_1a_resposta']}% de {a['T3']['closed_com_os_dois']} Closed com os dois tempos",
         conf(t3_confirma), "Horas do DS1 não valem como diagnóstico; Q1 segue pelo ramo MDE + instrumentação"),
        ("T4", "não existe data de abertura",
         f"colunas de data: {list(a['T4']['colunas_de_data'])}; candidatas a abertura: {a['T4']['colunas_candidatas_a_abertura']}",
         conf(not a["T4"]["existe_data_de_abertura"]),
         "Espera até a 1ª resposta não é mensurável; vira o evento ticket_criado"),
        ("T5", "CSAT se comporta como uniforme",
         f"qui² p={a['T5']['quiquadrado_uniforme']['p']}; macro-F1 modelo {f1_mod['media']}±{f1_mod['dp']} "
         f"vs embaralhado {f1_emb['media']}±{f1_emb['dp']}; "
         "critério de confirmação definido após ver os dados; aceito pelo Gustavo no portão F1",
         "s" if (uniforme and sem_sinal_modelo) else ("parcial" if (uniforme or sem_sinal_modelo) else "n"),
         "Não afirmar fator de satisfação; CSAT por ticket ligado a eventos entra na instrumentação"),
        ("T6", "sem gargalo por segmento (prioridade/canal/tipo)",
         f"Kruskal-Wallis p: prioridade {t6_ps[0]}, canal {t6_ps[1]}, tipo {t6_ps[2]} ({SUSPEITA_T3})",
         conf(all(p >= 0.05 for p in t6_ps)), "Sem gargalo por segmento afirmável a partir do DS1"),
        ("T7", "~67,3% dos tickets não estão Closed",
         f"{a['T7']['pct_nao_closed']}% não Closed",
         conf(a["T7"]["pct_nao_closed"] > 50),
         "Análise de tempo cobre só os Closed; Pending mistura espera do cliente com espera do atendente"),
        ("T8", "tipos além dos 3 do brief; dado pessoal",
         f"{a['T8']['n_tipos']} tipos; {a['T8']['emails_validos_regex']} e-mails válidos por regex; "
         f"Resolution {a['T8']['resolution_pct_nulo']}% nulo, {a['T8']['resolution_valores_unicos']} únicos",
         conf(a["T8"]["n_tipos"] > 3),
         "Tipos extras (reembolso, cancelamento) entram na política da F4; dado pessoal do DS1 entra no golden set de mascaramento"),
    ]
    fatos = pd.DataFrame(fatos, columns=["teste", "armadilha", "resultado", "confirmada (s/n/parcial)", "consequencia_aplicada"])
    nao_conf = fatos["confirmada (s/n/parcial)"] != "s"
    fatos.loc[nao_conf, "consequencia_aplicada"] = "NÃO CONFIRMADA: aplicar ramo 'se não confirmar' da spec F1 (ver report)"
    salvar_csv_excel(fatos, OUT_DIR / "f1_ds1_fatos.csv")
    for _, f in fatos.iterrows():
        print(f"{f['teste']} [{f['confirmada (s/n/parcial)']}] {f['resultado']}")


if __name__ == "__main__":
    main()
