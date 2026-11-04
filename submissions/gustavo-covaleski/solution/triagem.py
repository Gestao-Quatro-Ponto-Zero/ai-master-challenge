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

from comum import OUT_DIR, SUBMISSAO

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

CATEGORIAS = ["Access", "Administrative rights", "HR Support", "Hardware", "Internal Project",
              "Miscellaneous", "Purchase", "Storage"]

# detector de injeção: critério fixado na spec F6 ANTES de medir; não ajustar depois de ver o resultado
RE_INJECAO = re.compile(r"ignore|instruction|system:|categoria|category|classify|classifique|[{}]", re.I)
DETECTOR_PADRAO = "off"  # decidido pela regra de adoção da F6 (falso positivo ≤ 1% do holdout); ver f6_detector.json


def detectar_injecao(texto: str) -> bool:
    t = texto.lower()
    if RE_INJECAO.search(t):
        return True
    return any(len(re.findall(rf"\b{re.escape(c.lower())}\b", t)) >= 3 for c in CATEGORIAS)


def detector_ligado() -> bool:
    return os.environ.get("TRIAGEM_DETECTOR", DETECTOR_PADRAO) == "on"


_politica = None


def runtime_dir() -> Path:
    # sobrescrevível em teste/latência para não sujar o runtime real
    d = Path(os.environ.get("TRIAGEM_RUNTIME_DIR", SUBMISSAO / "runtime"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def cpf_valido(digitos: str) -> bool:
    d = [int(c) for c in re.sub(r"\D", "", digitos)]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        resto = sum(v * (n + 1 - i) for i, v in enumerate(d[:n])) * 10 % 11
        if resto % 10 != d[n]:
            return False
    return True


def mascarar(texto: str, nome_cliente: str | None = None) -> str:
    t = RE_EMAIL.sub("[EMAIL]", texto)
    t = RE_CPF.sub("[CPF]", t)
    t = RE_FONE_FMT.sub("[TELEFONE]", t)
    t = RE_CARTAO.sub(lambda m: "[CARTAO]" if 13 <= len(re.sub(r"\D", "", m.group())) <= 16 else m.group(), t)
    t = RE_FONE_HIFEN.sub("[TELEFONE]", t)
    # 11 dígitos: CPF só se passar no dígito verificador; senão é celular (DDD + 9 + 8 dígitos)
    t = RE_CPF_11.sub(lambda m: "[CPF]" if cpf_valido(m.group()) else "[TELEFONE]", t)
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
    return m, versao_atual()


def versao_atual() -> str:
    # F8: hash do arquivo de splits + parâmetros, para que o arquivo do cache identifique a versão
    splits = hashlib.sha256((OUT_DIR / "f1_splits.csv").read_bytes()).hexdigest()
    return hashlib.sha256((splits + PARAMS).encode()).hexdigest()[:12]


def cache_dir() -> Path:
    return Path(os.environ.get("TRIAGEM_CACHE_DIR", CACHE_DIR))


_modelos = {}


def carregar_modelo():
    """TRIAGEM_MODELO_VERSAO fixa uma versão já guardada (rollback); sem ela, usa a atual e treina se faltar.
    Versões antigas nunca são apagadas."""
    import joblib
    pedida = os.environ.get("TRIAGEM_MODELO_VERSAO")
    versao = pedida or versao_atual()
    arq = cache_dir() / f"modelo_{versao}.joblib"
    chave = str(arq)
    if chave not in _modelos:
        if arq.exists():
            _modelos[chave] = joblib.load(arq)
        elif pedida:
            # rollback para versão inexistente: não treina; triar() cai no fallback "falha do classificador"
            raise FileNotFoundError(f"modelo {pedida} não está em {cache_dir()}")
        else:
            t0 = time.perf_counter()
            m, v = _treinar()
            modelo = {"pipeline": m, "versao": v, "treino_s": round(time.perf_counter() - t0, 1)}
            arq.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(modelo, arq)
            _modelos[chave] = modelo
    return _modelos[chave]


def carregar_politica():
    global _politica
    if _politica is None:
        # F8: limiares e política escolhidos fora do holdout; f3_faixas.json e f4_politica_*.csv ficam como histórico
        arq = OUT_DIR / "f8_politica_por_categoria.csv"
        arq_fx = OUT_DIR / "f8_faixas.json"
        tab = pd.read_csv(arq)
        lim = json.loads(arq_fx.read_text(encoding="utf-8"))["limiares"]
        _politica = {"por_categoria": dict(zip(tab["categoria_prevista"], tab["politica"])),
                     "t_decide": lim["t_decide"] if lim["t_decide"] is not None else 1.01,
                     "t_sugere": lim["t_sugere"] if lim["t_sugere"] is not None else 1.01,
                     "versao": hashlib.sha256(arq.read_bytes() + arq_fx.read_bytes()).hexdigest()[:12]}
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


JANELA_S = 600
ESPERA_DUPLICADO_S = 2.0


def _db():
    con = sqlite3.connect(runtime_dir() / "idempotencia.sqlite", timeout=5)
    con.execute("CREATE TABLE IF NOT EXISTS eventos (chave TEXT PRIMARY KEY, resultado TEXT)")
    con.commit()
    return con


def _chaves(evento, agora=None) -> tuple[str, str | None]:
    """(chave a gravar, chave da janela anterior a consultar)."""
    if evento.get("event_id"):
        return f"evt:{evento['event_id']}", None
    # texto bruto: normalizar() troca dígitos por 0 e fazia "pedido 1111" colidir com "pedido 2222"
    base = str(evento.get("texto") or "").strip() + "|" + str(evento.get("canal") or "")
    janela = int((time.time() if agora is None else agora) // JANELA_S)
    h = lambda j: "sha:" + hashlib.sha256(f"{base}|{j}".encode()).hexdigest()
    return h(janela), h(janela - 1)


def _reservar(con, evento):
    """Reserva a chave antes de processar. Devolve (chave_reservada, None) ou (None, chave_existente)."""
    atual, anterior = _chaves(evento)
    if anterior and con.execute("SELECT 1 FROM eventos WHERE chave = ?", (anterior,)).fetchone():
        return None, anterior
    cur = con.execute("INSERT OR IGNORE INTO eventos (chave, resultado) VALUES (?, NULL)", (atual,))
    con.commit()
    return (atual, None) if cur.rowcount == 1 else (None, atual)


def _duplicado(con, chave):
    fim = time.monotonic() + ESPERA_DUPLICADO_S
    while True:
        r = con.execute("SELECT resultado FROM eventos WHERE chave = ?", (chave,)).fetchone()
        if r and r[0] is not None:
            res = json.loads(r[0])
            break
        if time.monotonic() >= fim:
            res = {"chave": chave, "status": "em_processamento", "faixa": "humano decide", "motivo": "duplicado em processamento",
                   "categoria": None, "p_max": None, "top2": [], "erro": None}
            break
        time.sleep(0.05)
    res["duplicado"] = True
    _log({"tipo": "duplicado", "chave": chave, "timestamp_utc": datetime.now(timezone.utc).isoformat()})
    return res


def _log(linha: dict, arquivo="decisoes.jsonl"):
    # append no Windows não é atômico entre processos: serializa a escrita com um lock em sqlite
    lock = sqlite3.connect(runtime_dir() / "log.lock", timeout=10, isolation_level=None)
    try:
        lock.execute("BEGIN IMMEDIATE")
        with open(runtime_dir() / arquivo, "a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
        lock.execute("COMMIT")
    finally:
        lock.close()


def triar(evento: dict) -> dict:
    t0 = time.perf_counter()
    try:
        return _triar(evento, t0)
    except Exception as e:  # contrato: quem chama nunca recebe exceção
        return {"faixa": "humano decide", "motivo": "falha interna", "erro": f"{type(e).__name__}: {e}",
                "duplicado": False, "categoria": None, "p_max": None, "top2": []}


def _triar(evento, t0):
    con = _db()
    try:
        chave, existente = _reservar(con, evento)
        if chave is None:
            return _duplicado(con, existente)
        try:
            return _processar(con, evento, chave, t0)
        except Exception:
            # libera a reserva para que a reentrega processe; triar() devolve "falha interna"
            con.execute("DELETE FROM eventos WHERE chave = ?", (chave,))
            con.commit()
            raise
    finally:
        con.close()


def _processar(con, evento, chave, t0):
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
            if detector_ligado() and detectar_injecao(texto):
                res.update(faixa="humano decide", motivo="possível injeção; " + res["motivo"])
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
    con.execute("UPDATE eventos SET resultado = ? WHERE chave = ?", (json.dumps(res, ensure_ascii=False), chave))
    con.commit()
    return res


def registrar_correcao(chave: str, categoria_correta: str, atendente: str, observacao: str = "") -> bool:
    # entrada do próximo ciclo de avaliação; nunca retreina automaticamente. Devolve False em vez de lançar.
    try:
        if categoria_correta not in CATEGORIAS:
            return False
        _log({"timestamp_utc": datetime.now(timezone.utc).isoformat(), "chave": chave,
              "categoria_correta": categoria_correta, "atendente": atendente,
              "observacao_mascarada": mascarar(str(observacao))[:200]}, "correcoes.jsonl")
        return True
    except Exception:
        return False
