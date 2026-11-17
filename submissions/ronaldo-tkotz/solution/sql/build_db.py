"""Constrói a camada SQL de confiança do desafio 001 (SQLite).

Uso: python -I build_db.py <pasta_dos_csv> <arquivo.db>
Recria o banco do zero a cada execução e imprime o relatório de qualidade.
Etapas: CSV -> raw_* (texto puro) -> 01_schema.sql -> 02_tipagem.sql -> reconciliação -> 03_checagens.sql
"""
import csv, hashlib, os, sqlite3, sys
from datetime import datetime, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
TABELAS = {  # tabela tipada: (arquivo, chave para alinhar raw x tipada)
    "accounts":        ("ravenstack_accounts.csv",        ("account_id", "account_id")),
    "subscriptions":   ("ravenstack_subscriptions.csv",   ("subscription_id", "subscription_id")),
    "feature_usage":   ("ravenstack_feature_usage.csv",   ("_linha", "usage_pk")),
    "support_tickets": ("ravenstack_support_tickets.csv", ("ticket_id", "ticket_id")),
    "churn_events":    ("ravenstack_churn_events.csv",    ("churn_event_id", "churn_event_id")),
}
DATAS = {"accounts": ["signup_date"], "subscriptions": ["start_date", "end_date"],
         "feature_usage": ["usage_date"], "support_tickets": ["submitted_at", "closed_at"],
         "churn_events": ["churn_date"]}


def sql(nome):
    with open(os.path.join(AQUI, nome), encoding="utf-8") as f:
        return f.read()


def main(pasta, db):
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(sql("01_schema.sql"))
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 1) CSV -> raw_* (todas as colunas TEXT, valor intocado)
    for tabela, (arquivo, _) in TABELAS.items():
        caminho = os.path.join(pasta, arquivo)
        with open(caminho, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
        with open(caminho, newline="", encoding="utf-8") as f:
            leitor = csv.reader(f)
            cab = next(leitor)
            linhas = [r for r in leitor]
        assert all(len(r) == len(cab) for r in linhas), f"{arquivo}: registro com nº de campos errado"
        cols = ", ".join(f'"{c}" TEXT NOT NULL' for c in cab)
        con.execute(f'CREATE TABLE raw_{tabela} (_linha INTEGER PRIMARY KEY, {cols})')
        ph = ", ".join("?" * (len(cab) + 1))
        con.executemany(f"INSERT INTO raw_{tabela} VALUES ({ph})",
                        ([i] + r for i, r in enumerate(linhas, start=1)))
        con.execute("INSERT INTO dq_carga (tabela, arquivo, registros_csv, sha256, carregado_em) VALUES (?,?,?,?,?)",
                    (tabela, arquivo, len(linhas), sha, agora))
    con.commit()

    # 2) raw -> tipadas (qualquer violação de tipo, domínio, PK ou FK aborta aqui)
    try:
        con.executescript("BEGIN;" + sql("02_tipagem.sql") + "COMMIT;")
    except sqlite3.DatabaseError as e:
        print("CARGA BLOQUEADA:", e)
        sys.exit(1)

    # 3) Reconciliação raw x tipada
    chks = []
    for tabela, (arquivo, (kraw, ktip)) in TABELAS.items():
        nraw = con.execute(f"SELECT count(*) FROM raw_{tabela}").fetchone()[0]
        ntip = con.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
        con.execute("UPDATE dq_carga SET linhas_raw=?, linhas_tipadas=? WHERE tabela=?", (nraw, ntip, tabela))
        chks.append(("E01_" + tabela, "estrutura", tabela, "registros do CSV que não chegaram à tabela tipada",
                     "bloqueante", nraw - ntip, nraw, None))
        cols_tip = [r[1] for r in con.execute(f"PRAGMA table_info({tabela})")]
        cols_raw = [r[1] for r in con.execute(f"PRAGMA table_info(raw_{tabela})")]
        perdas = 0
        for c in set(cols_tip) & set(cols_raw):
            nr = con.execute(f"SELECT count(*) FROM raw_{tabela} WHERE \"{c}\" <> ''").fetchone()[0]
            nt = con.execute(f"SELECT count(\"{c}\") FROM {tabela}").fetchone()[0]
            perdas += nr - nt
        chks.append(("E02_" + tabela, "estrutura", tabela, "valores não vazios do CSV que viraram NULL na tipagem",
                     "bloqueante", perdas, nraw * len(cols_raw), None))
        divergem = 0
        for c in DATAS[tabela]:
            divergem += con.execute(f"""
                SELECT count(*) FROM raw_{tabela} r JOIN {tabela} t ON t.{ktip} = r.{kraw}
                WHERE r.{c} <> '' AND (substr(t.{c},1,10) <> r.{c} AND t.{c} <> r.{c}
                      OR (length(r.{c}) = 10 AND t.{c} <> r.{c} || ' 00:00:00')
                      OR (length(r.{c}) > 10 AND t.{c} <> r.{c}))""").fetchone()[0]
        chks.append(("E03_" + tabela, "estrutura", tabela,
                     "datas cuja data ou hora mudou na padronização (sem hora -> 00:00:00; com hora -> mantida)",
                     "bloqueante", divergem, None, None))
    con.executemany("INSERT INTO dq_checks VALUES (?,?,?,?,?,?,?,?)", chks)
    con.executescript(sql("03_checagens.sql"))
    con.executescript(sql("04_views.sql"))
    con.commit()

    # 4) Relatório
    print(f"Banco: {os.path.basename(db)}  (SQLite {sqlite3.sqlite_version})\n")
    print("CARGA")
    for r in con.execute("SELECT tabela, registros_csv, linhas_raw, linhas_tipadas, substr(sha256,1,12) FROM dq_carga"):
        print(f"  {r[0]:16} csv={r[1]:>6}  raw={r[2]:>6}  tipada={r[3]:>6}  sha256={r[4]}…")
    print("\nPADRÃO DE DATAS (amostra por coluna: CSV -> banco)")
    for tabela, cols in DATAS.items():
        kraw, ktip = TABELAS[tabela][1]
        for c in cols:
            ex = con.execute(f"SELECT r.{c}, t.{c} FROM raw_{tabela} r JOIN {tabela} t ON t.{ktip}=r.{kraw} WHERE r.{c}<>'' LIMIT 1").fetchone()
            mn, mx = con.execute(f"SELECT min({c}), max({c}) FROM {tabela}").fetchone()
            nul = con.execute(f"SELECT count(*) - count({c}) FROM {tabela}").fetchone()[0]
            print(f"  {tabela}.{c:13} '{ex[0]}' -> '{ex[1]}'   faixa {mn} .. {mx}   nulos={nul}")
    print("\nVIEWS")
    for (v,) in con.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name").fetchall():
        n = con.execute(f"SELECT count(*) FROM {v}").fetchone()[0]
        ncol = len(con.execute(f"PRAGMA table_info({v})").fetchall())
        print(f"  {v:20} linhas={n:>6}  colunas={ncol}")
    print("\nCHECAGENS")
    for sev in ("bloqueante", "alerta", "info"):
        print(f"  [{sev}]")
        for r in con.execute("SELECT check_id, tabela, regra, violacoes, base, tratamento FROM dq_checks WHERE severidade=? ORDER BY check_id", (sev,)):
            base = f"/{r[4]}" if r[4] is not None else ""
            trat = f"  -> {r[5]}" if r[5] else ""
            print(f"    {r[0]:22} {r[3]:>6}{base:8} {r[1]}: {r[2]}{trat}")
    nb = con.execute("SELECT count(*) FROM dq_checks WHERE severidade='bloqueante' AND violacoes>0").fetchone()[0]
    print(f"\nVEREDITO: {'ESTRUTURA VÁLIDA (0 checagens bloqueantes)' if nb == 0 else f'{nb} CHECAGENS BLOQUEANTES FALHARAM'}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
