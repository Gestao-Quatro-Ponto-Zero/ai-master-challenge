"""Assistência técnica autorizada mais perto do cliente: bases de exemplo e regra de proximidade.

Pedido do Jó (2026-11-12, chamadas 87 e 88): a assistência indicada é sempre a mais perto do endereço do
cadastro, depois de confirmar com o cliente que ele está nesse endereço; se não estiver, vale o CEP de onde ele
está. Nenhuma base do case traz endereço (Dataset 1: nome, e-mail, idade, gênero, produto e data da compra), então
o cadastro e a rede abaixo são DE EXEMPLO, fictícios, só para demonstrar o fluxo. Numa operação real, as duas
listas vêm do cadastro de clientes e da rede autorizada da empresa.

Proximidade sem serviço externo: o CEP brasileiro é organizado por região (1º dígito = região, 3 primeiros =
cidade ou setor). Mais perto = maior começo de CEP igual; empate, menor diferença numérica. É uma aproximação
por região postal, não distância em quilômetros. Funções puras, sem rede.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Assistencia:
    nome: str
    endereco: str
    bairro: str
    cidade: str
    uf: str
    cep: str

    def texto(self) -> str:
        return f"{self.nome}, {self.endereco}, {self.bairro}, {self.cidade}/{self.uf}, CEP {formatar_cep(self.cep)}"


@dataclass(frozen=True)
class Cadastro:
    bairro: str
    cidade: str
    uf: str
    cep: str


# Rede de exemplo (fictícia): uma assistência por capital ou polo, endereços de exemplo.
ASSISTENCIAS = [
    Assistencia("Assistência Autorizada São Paulo (exemplo)", "Av. Paulista, 1000", "Bela Vista", "São Paulo", "SP",
                "01310100"),
    Assistencia("Assistência Autorizada Campinas (exemplo)", "Av. Francisco Glicério, 1000", "Centro", "Campinas",
                "SP", "13012100"),
    Assistencia("Assistência Autorizada Rio de Janeiro (exemplo)", "Av. Rio Branco, 100", "Centro", "Rio de Janeiro",
                "RJ", "20040002"),
    Assistencia("Assistência Autorizada Belo Horizonte (exemplo)", "Av. Afonso Pena, 1000", "Centro",
                "Belo Horizonte", "MG", "30130002"),
    Assistencia("Assistência Autorizada Curitiba (exemplo)", "Rua XV de Novembro, 500", "Centro", "Curitiba", "PR",
                "80020310"),
    Assistencia("Assistência Autorizada Porto Alegre (exemplo)", "Av. Borges de Medeiros, 500", "Centro Histórico",
                "Porto Alegre", "RS", "90020022"),
    Assistencia("Assistência Autorizada Salvador (exemplo)", "Av. Sete de Setembro, 500", "Centro", "Salvador", "BA",
                "40060001"),
    Assistencia("Assistência Autorizada Recife (exemplo)", "Av. Conde da Boa Vista, 500", "Boa Vista", "Recife", "PE",
                "50060002"),
    Assistencia("Assistência Autorizada Brasília (exemplo)", "SCS Quadra 2, Bloco A", "Asa Sul", "Brasília", "DF",
                "70302000"),
]

# Cadastro de exemplo (fictício): CPF de demonstração, válido pelos dígitos verificadores, ligado a um endereço.
# Fica no README para quem avalia testar o caminho "está no endereço do cadastro".
CADASTROS = {
    "10000000108": Cadastro("Cambuí", "Campinas", "SP", "13025000"),
    "20000000299": Cadastro("Pinheiros", "São Paulo", "SP", "05422000"),
    "30000000388": Cadastro("Copacabana", "Rio de Janeiro", "RJ", "22020001"),
    "40000000477": Cadastro("Savassi", "Belo Horizonte", "MG", "30140071"),
    "50000000566": Cadastro("Batel", "Curitiba", "PR", "80420090"),
    "60000000655": Cadastro("Moinhos de Vento", "Porto Alegre", "RS", "90570020"),
    "70000000744": Cadastro("Barra", "Salvador", "BA", "40140110"),
    "80000000833": Cadastro("Boa Viagem", "Recife", "PE", "51020000"),
    "90000000922": Cadastro("Asa Norte", "Brasília", "DF", "70710000"),
    "10000001090": Cadastro("Centro", "Sorocaba", "SP", "18035000"),
}

SIM = r"^\s*(sim|s|isso|isso mesmo|estou|to|tô|correto|certo|exato|confirmo|yes)\b"
NAO = r"^\s*(n[ãa]o|nao|n|negativo|no)\b|\bn[ãa]o estou\b|\bmudei\b|\boutro endere[çc]o\b"


def formatar_cep(cep: str) -> str:
    return f"{cep[:5]}-{cep[5:]}"


def cep_valido(texto: str) -> str | None:
    """CEP de 8 dígitos escrito pelo cliente ("13025-000", "13025000"), só os dígitos."""
    m = re.search(r"(?<!\d)(\d{5})-?(\d{3})(?!\d)", texto.replace(".", ""))
    if not m:
        return None
    cep = m.group(1) + m.group(2)
    return None if cep == "0" * 8 else cep


def mascarar_cep(cep: str | None) -> str:
    return f"{cep[:5]}-***" if cep else "não informado"


def buscar_cadastro(cpf: str | None) -> Cadastro | None:
    return CADASTROS.get(cpf or "")


def resposta_sim_nao(texto: str) -> bool | None:
    t = texto.lower()
    if re.search(NAO, t):
        return False
    if re.search(SIM, t):
        return True
    return None


def mais_proxima(cep: str, rede: list[Assistencia] = ASSISTENCIAS) -> Assistencia:
    """Maior começo de CEP igual; empate, menor diferença numérica."""
    def chave(a: Assistencia) -> tuple[int, int]:
        comum = next((i for i, (x, y) in enumerate(zip(cep, a.cep)) if x != y), len(cep))
        return (-comum, abs(int(cep) - int(a.cep)))
    return min(rede, key=chave)
