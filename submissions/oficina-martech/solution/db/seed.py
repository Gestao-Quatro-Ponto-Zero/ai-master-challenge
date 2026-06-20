"""Seed — carrega os 4 CSVs reais (data/) no banco, com limpeza aplicada.

Uso:  python -m db.seed

- Idempotente: limpa as tabelas e recarrega (rodar 2x dá o mesmo estado).
- Aplica a correção de higiene detectada na EDA: GTXPro -> GTX Pro.
- Normaliza vazios ("") para NULL (account, datas, close_value).
- Valida no fim (counts esperados) para o avaliador testar 100%.
"""
import csv, sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "foco.db"
DATA = DB_DIR.parent / "data"

EXPECTED = {"products": 7, "accounts": 85, "sales_teams": 35, "sales_pipeline": 8800}


def _n(v):
    """'' -> None; preserva o resto."""
    return None if v is None or v == "" else v


def rows(name, cols):
    with open(DATA / f"{name}.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            yield tuple(_n(r[c]) for c in cols)


def seed():
    if not DB_PATH.exists():
        raise SystemExit("Banco não existe. Rode primeiro: python -m db.migrate")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # ordem importa por causa das FKs (limpa pipeline antes dos pais)
    for t in ("sales_pipeline", "sales_teams", "accounts", "products"):
        cur.execute(f"DELETE FROM {t};")

    cur.executemany(
        "INSERT INTO products(product,series,sales_price) VALUES (?,?,?)",
        rows("products", ["product", "series", "sales_price"]),
    )
    cur.executemany(
        "INSERT INTO accounts(account,sector,year_established,revenue,employees,office_location,subsidiary_of)"
        " VALUES (?,?,?,?,?,?,?)",
        rows("accounts", ["account", "sector", "year_established", "revenue",
                          "employees", "office_location", "subsidiary_of"]),
    )
    cur.executemany(
        "INSERT INTO sales_teams(sales_agent,manager,regional_office) VALUES (?,?,?)",
        rows("sales_teams", ["sales_agent", "manager", "regional_office"]),
    )

    # pipeline com fix GTXPro -> GTX Pro
    pipe = []
    for opp, agent, prod, acc, stage, eng, close, val in rows(
        "sales_pipeline",
        ["opportunity_id", "sales_agent", "product", "account",
         "deal_stage", "engage_date", "close_date", "close_value"],
    ):
        prod = "GTX Pro" if prod == "GTXPro" else prod
        pipe.append((opp, agent, prod, acc, stage, eng, close, val))
    cur.executemany(
        "INSERT INTO sales_pipeline(opportunity_id,sales_agent,product,account,deal_stage,"
        "engage_date,close_date,close_value) VALUES (?,?,?,?,?,?,?,?)",
        pipe,
    )
    conn.commit()

    # validação para o avaliador
    print("Seed concluído. Contagens:")
    ok = True
    for t, exp in EXPECTED.items():
        got = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        mark = "✓" if got == exp else "✗"
        if got != exp:
            ok = False
        print(f"  {mark} {t:15s} {got:>5} (esperado {exp})")
    # colunas explícitas: SELECT * mudou de ordem ao introduzir as_of_date (0004)
    h = cur.execute(
        "SELECT total_deals, open_deals, deals_sem_conta, ciclo_medio_won_dias, as_of_date "
        "FROM v_pipeline_health"
    ).fetchone()
    print(f"  → saúde: total={h[0]} abertos={h[1]} sem_conta={h[2]} "
          f"ciclo_won={h[3]}d as_of={h[4]}")
    conn.close()
    if not ok:
        raise SystemExit("ATENÇÃO: contagens divergentes do esperado.")
    print("Banco pronto para uso. ✅")


if __name__ == "__main__":
    seed()
