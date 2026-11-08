"""Camadas: SQL e SQLAlchemy ficam só na persistência; services, routers e treinador usam repositórios."""
import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"


def imports(path: Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            out.add(base)
            out |= {f"{base}.{a.name}" for a in node.names}
    return out


def test_api_and_trainer_never_touch_sql_drivers_or_raw_sessions():
    banned = ("sqlite3", "sqlalchemy", "lead_core.db.session", "lead_core.db.connect")
    for pkg in ("lead_api", "lead_trainer"):
        for path in (SRC / pkg).rglob("*.py"):
            bad = {i for i in imports(path) if i.startswith(banned)}
            assert not bad, f"{path.relative_to(SRC)} importa {bad}: use um repositório"


def test_sqlalchemy_is_confined_to_the_persistence_package():
    for path in (SRC / "lead_core").rglob("*.py"):
        if "persistence" in path.parts:
            continue
        assert not any(i.startswith("sqlalchemy") for i in imports(path)), path


def test_raw_sql_strings_are_not_used_outside_core_db_and_persistence():
    for pkg in ("lead_api", "lead_trainer"):
        for path in (SRC / pkg).rglob("*.py"):
            text = path.read_text().upper()
            for keyword in ("SELECT ", "INSERT INTO", "UPDATE ", "DELETE FROM"):
                assert keyword not in text.replace("UPDATE  ", ""), f"{path.name} contém SQL ({keyword.strip()})"


def test_orm_never_creates_schema():
    for path in (SRC / "lead_core" / "persistence").rglob("*.py"):
        assert "create_all" not in path.read_text(), "o DDL é o arquivo schema_v1.sql, não o ORM"
