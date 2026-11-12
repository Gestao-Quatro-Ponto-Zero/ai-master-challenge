"""Valida um briefing gerado por IA contra os fatos que o sustentam.

O texto chega aqui ANTES de `preencher`: todo número tem que estar dentro de um
marcador `{chave}`, nunca escrito à mão. `preencher` substitui os marcadores depois.
"""
from __future__ import annotations

import re

PROIBIDAS = ["garantido", "garante", "certeza", "vai fechar", "com certeza"]
# só prazo curto (28 dias): "decidem mais tarde no trimestre" é afirmação válida da fila preparar
TERMOS_DECISAO_IMINENTE = ["próximas semanas", "em breve", "devem decidir", "vai decidir", "vão decidir"]

_MARCADOR = re.compile(r"\{([a-z_0-9]+)\}")
_NOME_PROPRIO = re.compile(r"[A-ZÀ-Ú][a-zà-úA-ZÀ-Ú0-9]*(?:\s+[A-ZÀ-Ú][a-zà-úA-ZÀ-Ú0-9]*)+")


def _eh_moeda(chave: str) -> bool:
    return chave.startswith("valor") or chave.startswith("ve_")


def _formatar(valor) -> str:
    if isinstance(valor, float):
        if valor != valor:  # NaN
            return "indefinido"
        if valor.is_integer():
            return str(int(valor))
    return str(valor)


def marcadores_validos(fatos: dict) -> dict[str, str]:
    m: dict[str, str] = {}
    for chave, valor in fatos.items():
        if chave == "foco":
            continue
        if isinstance(valor, bool):
            continue
        if isinstance(valor, (int, float)):
            m[chave] = _valor_moeda(valor) if _eh_moeda(chave) else _formatar(valor)
        elif isinstance(valor, str):
            m[chave] = valor
    for i, item in enumerate(fatos.get("foco", []), start=1):
        m[f"produto_{i}"] = item["produto"]
        m[f"conta_{i}"] = item["conta"] if item.get("conta") else "conta não registrada no CRM"
        m[f"valor_{i}"] = _valor_moeda(item["valor"])
        m[f"idade_{i}"] = _formatar(item["idade"])
        m[f"dias_restantes_{i}"] = _formatar(item["dias_restantes"]) if item.get("dias_restantes") is not None else "indefinido"
        m[f"fila_{i}"] = item["fila"]
    return m


def _valor_moeda(v: float) -> str:
    return "US$ " + f"{v:,.0f}".replace(",", ".")


def validar(texto: str, fatos: dict) -> tuple[bool, str]:
    marcadores = marcadores_validos(fatos)

    sem_marcadores = _MARCADOR.sub("", texto)
    if re.search(r"\d", sem_marcadores):
        return False, "número fora de um marcador {chave}"

    for nome_marcador in _MARCADOR.findall(texto):
        if nome_marcador not in marcadores:
            return False, f"marcador desconhecido: {{{nome_marcador}}}"

    conhecidos = {v for v in marcadores.values() if v and not v[0].isdigit()}
    for seq in _NOME_PROPRIO.findall(sem_marcadores):
        if not any(seq == v or seq in v or v in seq for v in conhecidos):
            return False, f"nome não reconhecido nos fatos: {seq}"

    baixo = texto.lower()
    for p in PROIBIDAS:
        if p in baixo:
            return False, f"palavra proibida: {p}"

    if fatos.get("n_fechar", 0) == 0:
        for termo in TERMOS_DECISAO_IMINENTE:
            if termo in baixo:
                return False, "afirma chance de decisão quando a tabela não sustenta nenhuma chance"

    return True, ""


def preencher(texto: str, fatos: dict) -> str:
    marcadores = marcadores_validos(fatos)
    return _MARCADOR.sub(lambda m: marcadores.get(m.group(1), m.group(0)), texto)
