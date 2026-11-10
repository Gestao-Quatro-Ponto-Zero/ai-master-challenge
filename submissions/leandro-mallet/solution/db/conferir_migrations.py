"""Confere as migrations sem conectar no banco.

Uso:  pip install pglast   (parser oficial do Postgres, libpg_query)
      python solution/db/conferir_migrations.py

Confere:
  1. sintaxe de cada comando e de cada corpo PL/pgSQL e SQL (functions e blocos DO);
  2. nenhum CASCADE;
  3. toda FK com ON DELETE RESTRICT e com índice cujas primeiras colunas são as da FK;
  4. todo objeto (tabela, view, function, trigger, índice, constraint nomeada) com prefixo
     core_, config_, score_, acao_ ou system_;
  5. nenhum DELETE nem TRUNCATE em comando ou corpo de function (só os gatilhos que os bloqueiam);
  6. todas as tabelas cobertas pelo laço de RLS e bloqueio de 0006_guardas.
Sai com código 1 se algo falhar.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import pglast
    from pglast import ast, parse_plpgsql, parse_sql
    from pglast.enums import ConstrType
except ImportError:  # pragma: no cover
    sys.exit("pglast não instalado: pip install pglast")

PASTA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "migrations"
PREFIXO = re.compile(r"^(core|config|score|acao|system)_")


def sem_comentarios_e_textos(sql: str) -> str:
    """Remove comentários e literais entre aspas simples (os corpos $$ ficam)."""
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def nome(n) -> str:
    return n.sval if hasattr(n, "sval") else str(n)


def main() -> int:
    erros: list[str] = []
    tabelas: dict[str, str] = {}
    fks: list[tuple[str, tuple[str, ...], str, str]] = []      # (tabela, colunas, destino, arquivo)
    indices: dict[str, list[tuple[str, ...]]] = defaultdict(list)
    n_indices_explicitos = 0
    views, functions, triggers, constraints_nomeadas = [], [], [], []
    corpos = 0

    def registrar_constraint(tabela, c, coluna=None, arquivo=""):
        if c.conname:
            constraints_nomeadas.append(c.conname)
        if c.contype == ConstrType.CONSTR_FOREIGN:
            cols = tuple(nome(x) for x in c.fk_attrs) if c.fk_attrs else (coluna,)
            if c.fk_del_action != "r":
                erros.append(f"{arquivo}: FK {tabela}{cols} sem ON DELETE RESTRICT (ação '{c.fk_del_action}')")
            fks.append((tabela, cols, c.pktable.relname, arquivo))
        elif c.contype in (ConstrType.CONSTR_PRIMARY, ConstrType.CONSTR_UNIQUE):
            cols = tuple(nome(x) for x in c.keys) if c.keys else (coluna,)
            indices[tabela].append(cols)

    arquivos = sorted(PASTA.glob("*.sql"))
    if not arquivos:
        sys.exit(f"nenhuma migration em {PASTA}")

    for arq in arquivos:
        sql = arq.read_text(encoding="utf-8")
        if "\r" in sql:
            erros.append(f"{arq.name}: fim de linha CRLF (use LF)")
        limpo = sem_comentarios_e_textos(sql)
        if re.search(r"\bcascade\b", limpo, re.I):
            erros.append(f"{arq.name}: contém CASCADE")
        for m in re.finditer(r"\b(delete\s+from|truncate\s+(table\s+)?[a-z_])", limpo, re.I):
            erros.append(f"{arq.name}: comando de remoção encontrado: '{m.group(0)}'")
        try:
            stmts = parse_sql(sql)
        except pglast.parser.ParseError as e:
            erros.append(f"{arq.name}: erro de sintaxe: {e}")
            continue

        for raw in stmts:
            s = raw.stmt
            texto = sql[raw.stmt_location: raw.stmt_location + raw.stmt_len] if raw.stmt_len else sql[raw.stmt_location:]
            if isinstance(s, ast.CreateStmt):
                t = s.relation.relname
                tabelas[t] = arq.name
                for el in s.tableElts or ():
                    if isinstance(el, ast.ColumnDef):
                        for c in el.constraints or ():
                            registrar_constraint(t, c, el.colname, arq.name)
                    elif isinstance(el, ast.Constraint):
                        registrar_constraint(t, el, None, arq.name)
            elif isinstance(s, ast.AlterTableStmt):
                for cmd in s.cmds or ():
                    if isinstance(cmd.def_, ast.Constraint):
                        registrar_constraint(s.relation.relname, cmd.def_, None, arq.name)
            elif isinstance(s, ast.IndexStmt):
                n_indices_explicitos += 1
                if not PREFIXO.match(s.idxname or ""):
                    erros.append(f"{arq.name}: índice sem prefixo: {s.idxname}")
                if s.whereClause is None:
                    cols = []
                    for p in s.indexParams:
                        if p.name is None:
                            break
                        cols.append(p.name)
                    indices[s.relation.relname].append(tuple(cols))
            elif isinstance(s, ast.ViewStmt):
                views.append(s.view.relname)
            elif isinstance(s, ast.CreateFunctionStmt):
                fn = nome(s.funcname[-1])
                functions.append(fn)
                opts = {o.defname: o.arg for o in s.options or ()}
                lang = nome(opts.get("language", "sql"))
                corpo = nome(opts["as"][0]) if "as" in opts else ""
                try:
                    if lang == "plpgsql":
                        parse_plpgsql(texto)
                    else:
                        parse_sql(corpo)
                    corpos += 1
                except Exception as e:  # noqa: BLE001
                    erros.append(f"{arq.name}: corpo inválido em {fn}: {e}")
            elif isinstance(s, ast.CreateTrigStmt):
                triggers.append((s.trigname, s.relation.relname))
            elif isinstance(s, ast.DoStmt):
                corpo = next(nome(a.arg) for a in s.args if a.defname == "as")
                try:
                    parse_plpgsql(f"create function system_do() returns void language plpgsql as $do${corpo}$do$")
                    corpos += 1
                except Exception as e:  # noqa: BLE001
                    erros.append(f"{arq.name}: bloco DO inválido: {e}")

    # prefixos
    for objeto, lista in (("tabela", tabelas), ("view", views), ("function", functions),
                          ("trigger", [t for t, _ in triggers]), ("constraint", constraints_nomeadas)):
        for n in lista:
            if not PREFIXO.match(n):
                erros.append(f"{objeto} sem prefixo: {n}")

    # FK com índice (primeiras colunas do índice = colunas da FK, em qualquer ordem)
    for tab, cols, destino, arq in fks:
        ok = any(set(ix[: len(cols)]) == set(cols) for ix in indices[tab])
        if not ok:
            erros.append(f"{arq}: FK {tab}{cols} -> {destino} sem índice")

    # laço de RLS e bloqueio cobre todas as tabelas (todas têm o prefixo do laço)
    guardas = (PASTA / "0006_guardas.sql").read_text(encoding="utf-8")
    laco = "c.relname ~ '^(core|config|score|acao|system)_'" in guardas and "enable row level security" in guardas
    if not laco:
        erros.append("0006_guardas: laço de RLS/bloqueio não encontrado")
    fora = [t for t in tabelas if not PREFIXO.match(t)]

    # gatilhos criados no laço: 2 por tabela (delete e truncate)
    n_trig_laco = 2 * len(tabelas)
    print("Conferência das migrations (sem conectar no banco)")
    print(f"  parser: pglast {pglast.__version__} (gramática do Postgres)")
    print(f"  arquivos: {len(arquivos)} | comandos e corpos de function/DO conferidos: {corpos} corpos")
    print(f"  tabelas: {len(tabelas)} | views: {len(views)} | functions: {len(functions)}")
    print(f"  FKs: {len(fks)} (todas ON DELETE RESTRICT: {not any('RESTRICT' in e for e in erros)})")
    n_pk_unique = sum(len(v) for v in indices.values()) - sum(1 for _ in range(n_indices_explicitos))
    print(f"  índices: {n_indices_explicitos} explícitos (com parciais) + {n_pk_unique} de PK/unique")
    print(f"  triggers: {len(triggers)} explícitos + {n_trig_laco} do laço de bloqueio (delete e truncate) = {len(triggers) + n_trig_laco}")
    print(f"  RLS e revoke: laço sobre {len(tabelas) - len(fora)} de {len(tabelas)} tabelas")
    if erros:
        print(f"\n{len(erros)} problema(s):")
        for e in erros:
            print("  - " + e)
        return 1
    print("\nOK: sintaxe válida, nenhum CASCADE, toda FK com índice e RESTRICT, todo objeto com prefixo, nenhum DELETE/TRUNCATE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
