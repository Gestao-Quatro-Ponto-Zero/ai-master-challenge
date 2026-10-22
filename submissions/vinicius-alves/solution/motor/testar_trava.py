"""Testa a trava com frases que nunca podem sair e frases que precisam passar.

Uso: python3 solution/motor/testar_trava.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redacao import trava  # noqa: E402

TEM_QUE_BARRAR = [
    "Seu reembolso cai até sexta.",
    "O dinheiro volta em 2 dias.",
    "Em até 5 dias úteis você recebe.",
    "Chega amanhã, pode ficar tranquila.",
    "Seu reembolso foi aprovado!",
    "Confirmamos que seu reembolso foi aprovado.",
    "O estorno está garantido.",
    "Vamos devolver em dobro.",
    "Cabe indenização sim.",
    "Posso te dar um desconto de 20%.",
    "Aplico o cupom pra você agora.",
    "É normal, pode continuar usando.",
    "Pode usar normalmente, não tem problema.",
    "Foi erro nosso, desculpa.",
    "Sabemos que a culpa é nossa.",
]

TEM_QUE_PASSAR = [
    "Uma pessoa do time vai te responder por aqui.",
    "Você tem até 7 dias do recebimento pra devolver, sem precisar justificar.",
    "O prazo pra aparecer na fatura depende do seu banco.",
    "Pare de usar o aparelho agora e desligue da tomada.",
    "Não consigo aplicar desconto por aqui.",
    "Não é normal. Pare de usar o aparelho.",
    "O valor volta inteiro, com o frete.",
    "Já abri o pedido de estorno da cobrança repetida.",
    "A loja tem até 30 dias pra resolver o defeito.",
]


def main():
    falhas = 0
    for frase in TEM_QUE_BARRAR:
        if not trava(frase):
            falhas += 1
            print(f"DEIXOU PASSAR: {frase}")
    for frase in TEM_QUE_PASSAR:
        achados = trava(frase)
        if achados:
            falhas += 1
            print(f"BARROU SEM PRECISAR: {frase} -> {achados}")
    total = len(TEM_QUE_BARRAR) + len(TEM_QUE_PASSAR)
    print(f"{total - falhas}/{total} frases certas "
          f"({len(TEM_QUE_BARRAR)} que tinham que ser barradas, {len(TEM_QUE_PASSAR)} que tinham que passar)")
    return falhas


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
