"""Quanto tempo a operação pode recuperar, como fórmula.

O Dataset 1 não mede tempo (não tem data de abertura, e metade das resoluções
vem antes da primeira resposta). Então não existe "horas desperdiçadas" medidas.
O que dá pra fazer com honestidade é uma conta com cada premissa na mesa, em
três cenários, pra quem tem o número real da operação trocar e refazer.

Uso: python3 solution/diagnostico/conta.py
"""
import csv
from collections import Counter
from pathlib import Path

TESTE = Path(__file__).resolve().parents[1] / "teste"

# ---------------------------------------------------------------- premissas
# Cada uma com a origem. "Premissa" = número que eu arbitrei e precisa ser medido.
VOLUME_ANO = 30_000          # brief do desafio ("~30.000 tickets por ano")
CENARIOS = {
    #                 tempo humano   leitura+triagem   revisão de     custo da hora
    #                 por ticket     poupada pelo      cada ticket    do atendente
    #                 (min)          resumo (min)      da IA (min)    (R$)
    "pessimista": dict(aht=8,  triagem=1.5, revisao=1.0, hora=25),
    "base":       dict(aht=12, triagem=3.0, revisao=0.5, hora=35),
    "otimista":   dict(aht=18, triagem=5.0, revisao=0.25, hora=45),
}
# aht: premissa. Mercado costuma falar em 8 a 20 min por atendimento escrito.
# triagem: premissa. Tempo de ler o histórico, achar o pedido e entender o caso,
#          que o resumo da IA já entrega pronto.
# revisao: premissa. No começo, alguém confere por amostragem o que a IA respondeu.
# hora: premissa. Salário de atendente com encargos, dividido pelas horas do mês.


def mistura():
    """Quanto de cada ação, pelos gabaritos dos 110 tickets de teste.
    Os testes foram escritos pra ser difíceis, então a parte da IA aqui é
    conservadora: uma operação real tem mais dúvida simples."""
    acoes = Counter()
    for nome in ("gabarito_preenchido.csv", "referencia_novos.csv"):
        with open(TESTE / nome, encoding="utf-8-sig") as f:
            acoes.update(r["acao"] for r in csv.DictReader(f))
    total = sum(acoes.values())
    return {a: acoes[a] / total for a in "ABCDE"}, total


def conta(p, m):
    ia = m["A"] + m["B"]           # a IA resolve sozinha
    resumo = m["C"]                # a IA entrega o caso mastigado
    horas_ia = VOLUME_ANO * ia * (p["aht"] - p["revisao"]) / 60
    horas_resumo = VOLUME_ANO * resumo * p["triagem"] / 60
    horas = horas_ia + horas_resumo
    return horas, horas * p["hora"], horas / (220 * 8)  # 220 dias úteis de 8 horas = 1 pessoa por ano


def main():
    m, n = mistura()
    print(f"Mistura de ações nos {n} tickets de teste: " + ", ".join(f"{a} {v:.0%}" for a, v in m.items()))
    print(f"A IA resolve sozinha (A+B): {m['A'] + m['B']:.0%} · resumo pro atendente (C): {m['C']:.0%}\n")
    print(f"{'cenário':<12}{'horas/ano':>12}{'R$/ano':>14}{'pessoas':>10}")
    for nome, p in CENARIOS.items():
        horas, reais, pessoas = conta(p, m)
        print(f"{nome:<12}{horas:>12,.0f}{reais:>14,.0f}{pessoas:>10.1f}".replace(",", "."))
    print("\nFórmula: volume x [%IA x (tempo humano - revisão) + %resumo x triagem poupada] / 60")
    print("Antes de liberar: medir em modo sombra até erro perigoso ficar perto de zero (nos 30 tickets novos: 7 na versão 1, 1 na versão 2).")


if __name__ == "__main__":
    main()
