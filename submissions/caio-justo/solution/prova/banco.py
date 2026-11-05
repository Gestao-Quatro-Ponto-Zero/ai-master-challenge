"""Guarda o que os vendedores responderam. Real e demonstração ficam em bancos separados."""
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS checagens (
    negocio TEXT PRIMARY KEY,
    resposta TEXT NOT NULL,
    vendedor TEXT NOT NULL,
    quando TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS resultados (
    negocio TEXT PRIMARY KEY,
    resultado TEXT NOT NULL,
    vendedor TEXT NOT NULL,
    quando TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS adiados (
    negocio TEXT PRIMARY KEY,
    vendedor TEXT NOT NULL,
    quando TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS placar_simulado (
    id INTEGER PRIMARY KEY,
    grupo TEXT NOT NULL,
    vendedor TEXT NOT NULL,
    ganhou INTEGER NOT NULL
);
"""


class Banco:
    def __init__(self, caminho: Path):
        self.conexao = sqlite3.connect(str(caminho), check_same_thread=False)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.executescript(ESQUEMA)

    def checagens(self) -> dict:
        return {
            l["negocio"]: l["resposta"]
            for l in self.conexao.execute("SELECT negocio, resposta FROM checagens")
        }

    def responder_checagem(self, negocio: str, resposta: str, vendedor: str) -> None:
        with self.conexao:
            self.conexao.execute(
                "INSERT OR REPLACE INTO checagens (negocio, resposta, vendedor) VALUES (?, ?, ?)",
                (negocio, resposta, vendedor),
            )

    def desfazer_checagem(self, negocio: str) -> None:
        with self.conexao:
            self.conexao.execute("DELETE FROM checagens WHERE negocio = ?", (negocio,))

    def resultados(self) -> dict:
        return {
            l["negocio"]: l["resultado"]
            for l in self.conexao.execute("SELECT negocio, resultado FROM resultados")
        }

    def registrar_resultado(self, negocio: str, resultado: str, vendedor: str) -> None:
        with self.conexao:
            self.conexao.execute(
                "INSERT OR REPLACE INTO resultados (negocio, resultado, vendedor) VALUES (?, ?, ?)",
                (negocio, resultado, vendedor),
            )

    def desfazer_resultado(self, negocio: str) -> None:
        with self.conexao:
            self.conexao.execute("DELETE FROM resultados WHERE negocio = ?", (negocio,))

    def adiados(self) -> set:
        return {l["negocio"] for l in self.conexao.execute("SELECT negocio FROM adiados")}

    def adiar(self, negocio: str, vendedor: str, adiado: bool) -> None:
        with self.conexao:
            if adiado:
                self.conexao.execute(
                    "INSERT OR REPLACE INTO adiados (negocio, vendedor) VALUES (?, ?)",
                    (negocio, vendedor),
                )
            else:
                self.conexao.execute("DELETE FROM adiados WHERE negocio = ?", (negocio,))

    def placar_simulado(self) -> list:
        return list(self.conexao.execute("SELECT grupo, vendedor, ganhou FROM placar_simulado"))

    def gravar_placar_simulado(self, linhas: list) -> None:
        with self.conexao:
            self.conexao.executemany(
                "INSERT INTO placar_simulado (grupo, vendedor, ganhou) VALUES (?, ?, ?)", linhas
            )

    def limpar(self) -> None:
        with self.conexao:
            for tabela in ("checagens", "resultados", "adiados", "placar_simulado"):
                self.conexao.execute(f"DELETE FROM {tabela}")
