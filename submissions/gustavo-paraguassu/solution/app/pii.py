"""Mascara dados pessoais antes de qualquer coisa sair da máquina (LLM) ou ir para log."""
import hashlib
import re

_PADROES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[cpf]"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[cartao]"),
    (re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b"), "[telefone]"),
]


def mascarar(texto: str) -> str:
    for padrao, troca in _PADROES:
        texto = padrao.sub(troca, texto)
    return texto


def anonimo(identificador) -> str:
    """Id estável e não reversível (para log): mesmo usuário, mesmo código."""
    return hashlib.sha256(f"g4-suporte:{identificador}".encode()).hexdigest()[:10]
