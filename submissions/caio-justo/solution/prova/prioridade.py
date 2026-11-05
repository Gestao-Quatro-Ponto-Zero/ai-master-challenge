"""Classifica os negócios abertos, dá a nota de prioridade e explica o porquê.

A nota não é chance de fechar: os testes mostraram que os dados não sustentam
essa previsão. A regra vem do replay do histórico (analysis/RESULTADOS.md): tira
da fila o que passou do maior ciclo registrado e ordena o resto pelo preço, com o
negócio mais antigo primeiro no empate. As duas versões de "preço sem parados"
empataram em negócios ganhos e venceram "preço" e "preço x janela".
"""
from bisect import bisect_right
from dataclasses import dataclass
from datetime import date

from .dados import HOJE

ATIVO = "ativo"
PARADO = "parado"
QUALIFICAR = "qualificar"
ULTIMA_CHAMADA_DIAS = 30


@dataclass(frozen=True)
class Curva:
    """Quanto tempo os negócios já encerrados levaram para encerrar."""

    ciclos: tuple

    @classmethod
    def de(cls, negocios, ate: date = None) -> "Curva":
        ciclos = sorted(
            n.ciclo for n in negocios if n.fechado and (ate is None or n.fim < ate)
        )
        return cls(tuple(ciclos))

    @property
    def limite(self) -> int:
        return self.ciclos[-1] if self.ciclos else 0

    def janela(self, idade: int) -> float:
        """Parcela dos encerrados que durou mais do que `idade` dias."""
        if not self.ciclos:
            return 1.0
        return (len(self.ciclos) - bisect_right(self.ciclos, idade)) / len(self.ciclos)


def situacao(negocio, curva: Curva, hoje: date = HOJE) -> str:
    if negocio.estagio == "Prospecting":
        return QUALIFICAR
    return PARADO if negocio.idade(hoje) > curva.limite else ATIVO


def montar_notas(abertos, curva: Curva, hoje: date = HOJE) -> dict:
    """Nota de 0 a 100: a posição do negócio entre os ativos, por preço e idade."""
    ativos = [n for n in abertos if situacao(n, curva, hoje) == ATIVO]
    ordem = sorted(ativos, key=lambda n: (n.preco, n.idade(hoje), n.id))
    total = len(ordem)
    return {n.id: round(100 * (i + 1) / total) for i, n in enumerate(ordem)}


def motivos(negocio, curva: Curva, nota: int = None, hoje: date = HOJE) -> list:
    """Frases em linguagem de vendedor, geradas só com os fatos do negócio."""
    lista = []
    tipo = situacao(negocio, curva, hoje)
    if tipo == QUALIFICAR:
        lista.append(
            f"Ainda não foi trabalhado. Preço de tabela de ${negocio.preco:,}".replace(",", ".")
        )
    elif tipo == PARADO:
        dias = negocio.idade(hoje)
        lista.append(
            f"Aberto há {dias} dias. Nenhum negócio encerrado passou de {curva.limite} dias"
        )
    else:
        dias = negocio.idade(hoje)
        preco = f"{negocio.preco:,}".replace(",", ".")
        if nota is not None:
            lista.append(f"Preço de tabela de ${preco}: nota {nota} de 100 entre os negócios ativos")
        else:
            lista.append(f"Preço de tabela de ${preco}")
        restante = curva.limite - dias
        if restante <= ULTIMA_CHAMADA_DIAS:
            lista.append(f"Aberto há {dias} dias: faltam {restante} para passar do maior ciclo já registrado")
        else:
            lista.append(f"Aberto há {dias} dias: ainda dentro do tempo normal, que chega a {curva.limite}")
    if not negocio.conta:
        lista.append("Sem conta preenchida no CRM")
    return lista


def proxima_acao(negocio, curva: Curva, hoje: date = HOJE) -> str:
    tipo = situacao(negocio, curva, hoje)
    if tipo == QUALIFICAR:
        return "Preencher a conta e decidir se vale engajar" if not negocio.conta else "Decidir se vale engajar"
    if tipo == PARADO:
        return "Confirmar se ainda existe negócio"
    if not negocio.conta:
        return "Preencher a conta e marcar o próximo passo com o cliente"
    if curva.limite - negocio.idade(hoje) <= ULTIMA_CHAMADA_DIAS:
        return "Pedir a decisão do cliente nesta semana"
    return "Marcar o próximo passo com o cliente"
