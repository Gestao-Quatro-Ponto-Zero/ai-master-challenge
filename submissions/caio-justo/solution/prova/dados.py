"""Lê os CSVs do CRM e corrige os problemas conhecidos do dataset."""
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"

# O dataset termina em 31/12/2017; essa data faz o papel de "hoje".
HOJE = date(2017, 12, 31)

# "GTXPro" no pipeline e "GTX Pro" no catálogo: sem isso, 1.480 linhas ficam sem preço.
APELIDOS_PRODUTO = {"GTXPro": "GTX Pro"}
CORRECOES_SETOR = {"technolgy": "technology"}


@dataclass(frozen=True)
class Negocio:
    id: str
    vendedor: str
    manager: str
    regiao: str
    produto: str
    serie: str
    preco: int
    conta: Optional[str]
    setor: Optional[str]
    receita: Optional[float]
    estagio: str
    inicio: Optional[date]
    fim: Optional[date]
    valor: int

    @property
    def fechado(self) -> bool:
        return self.estagio in ("Won", "Lost")

    @property
    def ganho(self) -> bool:
        return self.estagio == "Won"

    @property
    def ciclo(self) -> Optional[int]:
        return (self.fim - self.inicio).days if self.fechado else None

    def idade(self, hoje: date = HOJE) -> Optional[int]:
        return (hoje - self.inicio).days if self.inicio else None


def _ler(nome: str, pasta: Path) -> list:
    with open(pasta / nome, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def _data(texto: str) -> Optional[date]:
    return date.fromisoformat(texto) if texto else None


def carregar(pasta: Path = PASTA_DADOS) -> list:
    contas = {c["account"]: c for c in _ler("accounts.csv", pasta)}
    produtos = {p["product"]: p for p in _ler("products.csv", pasta)}
    times = {t["sales_agent"]: t for t in _ler("sales_teams.csv", pasta)}
    negocios = []
    for linha in _ler("sales_pipeline.csv", pasta):
        nome_produto = APELIDOS_PRODUTO.get(linha["product"], linha["product"])
        produto = produtos[nome_produto]
        time = times[linha["sales_agent"]]
        conta = contas.get(linha["account"])
        setor = conta["sector"] if conta else None
        negocios.append(
            Negocio(
                id=linha["opportunity_id"],
                vendedor=linha["sales_agent"],
                manager=time["manager"],
                regiao=time["regional_office"],
                produto=nome_produto,
                serie=produto["series"],
                preco=int(produto["sales_price"]),
                conta=linha["account"] or None,
                setor=CORRECOES_SETOR.get(setor, setor),
                receita=float(conta["revenue"]) if conta else None,
                estagio=linha["deal_stage"],
                inicio=_data(linha["engage_date"]),
                fim=_data(linha["close_date"]),
                valor=int(linha["close_value"] or 0),
            )
        )
    return negocios
