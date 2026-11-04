import hashlib
import json
import os
import re
import sqlite3
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from comum import OUT_DIR, SUBMISSAO, normalizar

CACHE_DIR = SUBMISSAO / "modelo_cache"
TIPOS_SEMPRE_HUMANO = {"Refund request", "Cancellation request"}
ORDEM = ["humano decide", "IA sugere", "IA decide"]
PARAMS = "TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)+LogisticRegression(max_iter=2000,random_state=42)"

RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
RE_CARTAO = re.compile(r"\b(?:\d[ -]?){12,15}\d\b")
RE_CPF_11 = re.compile(r"\b\d{11}\b")
# telefone formatado (+55, DDD entre parênteses ou hífen) antes do cartão, senão "+55 11 98765-4321" vira cartão
RE_FONE_FMT = re.compile(r"\+55[\s-]?\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}\b|\(\d{2}\)\s?9?\d{4}[\s-]?\d{4}\b")
RE_FONE_HIFEN = re.compile(r"\b9?\d{4}-\d{4}\b")
RE_FONE = re.compile(r"\b\d{8,}\b")

_modelo = None
_politica = None


def runtime_dir() -> Path:
    # sobrescrevível em teste/latência para não sujar o runtime real
    d = Path(os.environ.get("TRIAGEM_RUNTIME_DIR", SUBMISSAO / "runtime"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def mascarar(texto: str, nome_cliente: str | None = None) -> str:
    t = RE_EMAIL.sub("[EMAIL]", texto)
    t = RE_CPF.sub("[CPF]", t)
    t = RE_FONE_FMT.sub("[TELEFONE]", t)
    t = RE_CARTAO.sub(lambda m: "[CARTAO]" if 13 <= len(re.sub(r"\D", "", m.group())) <= 16 else m.group(), t)
    t = RE_FONE_HIFEN.sub("[TELEFONE]", t)
    t = RE_CPF_11.sub("[CPF]", t)
    t = RE_FONE.sub("[TELEFONE]", t)
    if nome_cliente and nome_cliente.strip():
        t = re.sub(re.escape(nome_cliente.strip()), "[NOME]", t, flags=re.I)
        for parte in nome_cliente.split():
            if len(parte) >= 3:
                t = re.sub(rf"\b{re.escape(parte)}\b", "[NOME]", t, flags=re.I)
    return t


def _treinar():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from comum import SEED, ler_ds2
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    tr = df[df["split_grupo"] == "treino"]
    m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                      LogisticRegression(max_iter=2000, random_state=SEED)).fit(tr["Document"], tr["Topic_group"])
    versao = hashlib.sha256((",".join(map(str, sorted(tr["id"]))) + PARAMS).encode()).hexdigest()[:12]
    return m, versao


def carregar_modelo():
    global _modelo
    if _modelo is None:
        import joblib
        arq = CACHE_DIR / "modelo.joblib"
        if arq.exists():
            _modelo = joblib.load(arq)
        else:
            t0 = time.perf_counter()
            m, versao = _treinar()
            _modelo = {"pipeline": m, "versao": versao, "treino_s": round(time.perf_counter() - t0, 1)}
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump(_modelo, arq)
    return _modelo


def carregar_politica():
    global _politica
    if _politica is None:
        arq = OUT_DIR / "f4_politica_por_categoria.csv"
        tab = pd.read_csv(arq)
        fx = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
        _politica = {"por_categoria": dict(zip(tab["categoria_prevista"], tab["politica"])),
                     "t_decide": fx["faixas"]["ia_decide"]["limiar"],
                     "t_sugere": fx["faixas"]["ia_sugere_humano_confirma"]["limiar"],
                     "versao": hashlib.sha256(arq.read_bytes()).hexdigest()[:12]}
    return _politica


def faixa_para(categoria: str, p_max: float) -> str:
    pol = carregar_politica()
    g = "IA decide" if p_max >= pol["t_decide"] else ("IA sugere" if p_max >= pol["t_sugere"] else "humano decide")
    teto = pol["por_categoria"].get(categoria, "humano decide")
    return ORDEM[min(ORDEM.index(g), ORDEM.index(teto))]


_cache_termos = {}


def _termos(tfidf):
    # get_feature_names_out() monta ~175 mil strings; por chamada custava dezenas de ms
    if id(tfidf) not in _cache_termos:
        _cache_termos[id(tfidf)] = tfidf.get_feature_names_out()
    return _cache_termos[id(tfidf)]


def classificar(texto: str) -> dict:
    m = carregar_modelo()["pipeline"]
    tfidf, lr = m.named_steps["tfidfvectorizer"], m.named_steps["logisticregression"]
    x = tfidf.transform([texto])
    proba = lr.predict_proba(x)[0]
    ordem = np.argsort(-proba)
    i = ordem[0]
    contrib = x.multiply(lr.coef_[i]).tocsr()
    termos = _termos(tfidf)
    top = sorted(zip(contrib.indices, contrib.data), key=lambda t: -t[1])[:5]
    return {"categoria": str(lr.classes_[i]), "p_max": round(float(proba[i]), 4),
            "top2": [{"categoria": str(lr.classes_[j]), "p": round(float(proba[j]), 4)} for j in ordem[:2]],
            "motivo": "termos: " + ", ".join(f"{termos[k]} ({v:.2f})" for k, v in top if v > 0)}


def _db():
    con = sqlite3.connect(runtime_dir() / "idempotencia.sqlite")
    con.execute("CREATE TABLE IF NOT EXISTS eventos (chave TEXT PRIMARY KEY, resultado TEXT)")
    return con


def _chave(evento) -> str:
    if evento.get("event_id"):
        return f"evt:{evento['event_id']}"
    base = normalizar(evento.get("texto") or "") + "|" + str(evento.get("canal") or "")
    return "sha:" + hashlib.sha256(base.encode()).hexdigest()


def _log(linha: dict, arquivo="decisoes.jsonl"):
    with open(runtime_dir() / arquivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def triar(evento: dict) -> dict:
    t0 = time.perf_counter()
    try:
        return _triar(evento, t0)
    except Exception as e:  # contrato: quem chama nunca recebe exceção
        return {"faixa": "humano decide", "motivo": "falha interna", "erro": f"{type(e).__name__}: {e}",
                "duplicado": False, "categoria": None, "p_max": None, "top2": []}


def _triar(evento, t0):
    chave = _chave(evento)
    con = _db()
    try:
        r = con.execute("SELECT resultado FROM eventos WHERE chave = ?", (chave,)).fetchone()
        if r:
            res = json.loads(r[0])
            res["duplicado"] = True
            return res

        texto = mascarar(str(evento.get("texto") or ""), evento.get("nome_cliente"))
        res = {"chave": chave, "categoria": None, "p_max": None, "top2": [], "erro": None, "duplicado": False}
        if len(texto.split()) < 3:
            res.update(faixa="humano decide", motivo="texto insuficiente")
        else:
            try:
                c = classificar(texto)
                res.update(c, faixa=faixa_para(c["categoria"], c["p_max"]))
                if evento.get("tipo_ds1") in TIPOS_SEMPRE_HUMANO:
                    res.update(faixa="humano decide", motivo=f"regra de ação: {evento['tipo_ds1']}; " + c["motivo"])
            except Exception as e:
                res.update(faixa="humano decide", motivo="falha do classificador",
                           erro=f"{type(e).__name__}: {e} | {traceback.format_exc(limit=1).strip()[-200:]}")

        res["faixa_sem_sombra"] = res["faixa"]
        res["modo"] = os.environ.get("TRIAGEM_MODO", "ativo")
        if res["modo"] == "sombra":
            res["faixa"] = "humano decide"

        try:
            mv = carregar_modelo()["versao"]
        except Exception:
            mv = None
        res["latencia_ms"] = round((time.perf_counter() - t0) * 1000, 3)
        _log({"timestamp_utc": datetime.now(timezone.utc).isoformat(), "chave": chave, "event_id": evento.get("event_id"),
              "texto_mascarado": texto[:200], "categoria": res["categoria"], "p_max": res["p_max"], "faixa": res["faixa"],
              "faixa_sem_sombra": res["faixa_sem_sombra"], "motivo": res["motivo"], "modelo_versao": mv,
              "politica_versao": carregar_politica()["versao"], "latencia_ms": res["latencia_ms"], "erro": res["erro"]})
        con.execute("INSERT INTO eventos VALUES (?, ?)", (chave, json.dumps(res, ensure_ascii=False)))
        con.commit()
        return res
    finally:
        con.close()


def registrar_correcao(chave: str, categoria_correta: str, atendente: str) -> None:
    # entrada do próximo ciclo de avaliação; nunca retreina automaticamente
    _log({"timestamp_utc": datetime.now(timezone.utc).isoformat(), "chave": chave,
          "categoria_correta": categoria_correta, "atendente": atendente}, "correcoes.jsonl")
