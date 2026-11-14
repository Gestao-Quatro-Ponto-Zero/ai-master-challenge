"""Validação e máscara de nome, CPF, telefone e e-mail."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from dados_pessoais import (cpf_valido, email_valido, extrair_nome, mascarar_cpf, mascarar_email,  # noqa: E402
                            mascarar_telefone, recusou, telefone_valido)


@pytest.mark.parametrize("texto, nome", [
    ("Ana", "Ana"), ("ana paula", "Ana"), ("Meu nome é João", "João"), ("me chamo carla silva", "Carla"),
    ("sou o Pedro", "Pedro"), ("Oi, aqui é a Beatriz", "Beatriz"),
    ("oi", None), ("bom dia", None), ("meu notebook não liga desde ontem depois da atualização", None),
])
def test_extrair_nome(texto, nome):
    assert extrair_nome(texto) == nome


@pytest.mark.parametrize("texto, ok", [
    ("123.456.789-09", True), ("12345678909", True), ("111.111.111-11", False), ("123.456.789-00", False),
    ("1234", False), ("meu cpf é 123.456.789-09", True),
])
def test_cpf(texto, ok):
    assert (cpf_valido(texto) is not None) == ok


@pytest.mark.parametrize("texto, ok", [
    ("(11) 91234-5678", True), ("+55 19 99876-5432", True), ("1933334444", True), ("91234-5678", False),
    ("(11) 81234-5678", False), ("(01) 91234-5678", False),
])
def test_telefone(texto, ok):
    assert (telefone_valido(texto) is not None) == ok


def test_email():
    assert email_valido("é ana.teste@exemplo.com.br") == "ana.teste@exemplo.com.br"
    assert email_valido("ana arroba exemplo") is None


def test_recusa():
    assert recusou("prefiro não informar")
    assert recusou("não tenho e-mail")
    assert not recusou("123.456.789-09")


def test_mascaras_nao_mostram_o_dado_inteiro():
    assert mascarar_cpf("12345678909") == "***.***.789-09"
    assert mascarar_telefone("11912345678") == "(11) *****-5678"
    assert mascarar_email("ana.teste@exemplo.com") == "a***@exemplo.com"
    assert mascarar_cpf(None) == "não informado"
