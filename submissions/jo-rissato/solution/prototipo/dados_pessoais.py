"""Nome, CPF, telefone e e-mail do cliente: extração, validação e máscara. Funções puras.

Esses dados nunca vão para a IA externa (regra do Jó de 2026-11-03: dado pessoal só em IA local no
Brasil). A coleta é feita por este código, e o que fica salvo em log vai mascarado.
"""
from __future__ import annotations

import re

RECUSA = r"\b(prefiro n[ãa]o|n[ãa]o (quero|vou|posso) (informar|passar|dar|falar)|n[ãa]o tenho|sem (cpf|e-?mail|telefone))\b"
_NAO_NOME = set("""oi olá ola bom boa dia tarde noite tudo bem obrigado obrigada sim não nao ok preciso ajuda
quero meu minha o a é e de do da hello hi""".split())


def so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def recusou(texto: str) -> bool:
    return re.search(RECUSA, texto.lower()) is not None


def extrair_nome(texto: str) -> str | None:
    """Nome do cliente a partir de "meu nome é X", "me chamo X", "sou o X" ou de uma resposta curta."""
    t = texto.strip()
    m = re.search(r"(?:meu nome [ée]|me chamo|pode me chamar de|sou (?:o|a)|aqui [ée] (?:o|a)|my name is|i am|i'm)"
                  r"\s+([A-Za-zÀ-ÿ'][A-Za-zÀ-ÿ'-]+)", t, flags=re.IGNORECASE)
    if m:
        candidato = m.group(1)
    else:
        palavras = re.findall(r"[A-Za-zÀ-ÿ'][A-Za-zÀ-ÿ'-]*", t)
        if not 1 <= len(palavras) <= 3 or len(t) > 40:
            return None
        candidato = next((p for p in palavras if p.lower() not in _NAO_NOME), None)
        if candidato is None:
            return None
    if candidato.lower() in _NAO_NOME or len(candidato) < 2:
        return None
    return candidato[0].upper() + candidato[1:].lower()


def cpf_valido(texto: str) -> str | None:
    """Devolve os 11 dígitos se o CPF for válido pelos dígitos verificadores."""
    d = so_digitos(texto)
    if len(d) != 11 or d == d[0] * 11:
        return None
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if dv != int(d[n]):
            return None
    return d


def telefone_valido(texto: str) -> str | None:
    """Telefone brasileiro com DDD (fixo de 10 ou celular de 11 dígitos), com ou sem +55."""
    d = so_digitos(texto)
    if len(d) in (12, 13) and d.startswith("55"):
        d = d[2:]
    if len(d) not in (10, 11) or not 11 <= int(d[:2]) <= 99:
        return None
    if len(d) == 11 and d[2] != "9":
        return None
    return d


def email_valido(texto: str) -> str | None:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", texto)
    return m.group(0).lower() if m else None


def mascarar_cpf(d: str | None) -> str:
    return f"***.***.{d[6:9]}-{d[9:]}" if d else "não informado"


def mascarar_telefone(d: str | None) -> str:
    return f"({d[:2]}) *****-{d[-4:]}" if d else "não informado"


def mascarar_email(e: str | None) -> str:
    if not e:
        return "não informado"
    usuario, dominio = e.split("@", 1)
    return f"{usuario[0]}***@{dominio}"
