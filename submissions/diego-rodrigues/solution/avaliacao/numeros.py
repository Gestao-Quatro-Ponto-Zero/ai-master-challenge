"""Única fonte dos números citados no README, nos docs e na tela. Imprime com rótulo e fonte e grava app/data/eval.json."""
from __future__ import annotations

import json
from pathlib import Path

from avaliacao.backtest import NUMERO_CONTROLE, RODADAS_ALEATORIO, backtest, razao_com_ic
from avaliacao.permutacao import historico, permutacao
from motor.carregar import carregar

RAIZ = Path(__file__).parent.parent
REPETICOES_PERMUTACAO = 1000
LIMITE_SINAL = 0.05
ATRIBUTOS = [
    ("conta", "conta"),
    ("vendedor", "vendedor"),
    ("gerente", "gerente"),
    ("regiao", "região"),
    ("setor", "setor da conta"),
    ("porte", "porte da conta (quartil de funcionários)"),
    ("produto", "produto"),
    (["vendedor", "produto"], "vendedor × produto"),
]


def calcular() -> dict:
    config = json.loads((RAIZ / "config.json").read_text(encoding="utf-8"))
    dados = carregar(RAIZ / "data")

    tabela = backtest(dados, config)
    det = backtest(dados, config, detalhado=True)
    soma = {c: float(tabela[c].sum()) for c in tabela.columns if c.startswith("valor_")}
    acerto = {c: float(tabela[c].mean()) for c in tabela.columns if c.startswith("acerto_")}

    razoes = {}
    for a, b in [("relogio", "preco_prazo"), ("relogio", "preco_138")]:
        razao, lo, hi = razao_com_ic(det, a, b)
        razoes[f"{a} / {b}"] = {"razao": float(razao), "ic_inferior": float(lo), "ic_superior": float(hi)}

    h = historico(dados, config)
    permutacoes = {}
    for chave, rotulo in ATRIBUTOS:
        p = permutacao(h, chave, estratificar_por="mes_do_trimestre", n=REPETICOES_PERMUTACAO)["p"]
        permutacoes[rotulo] = {"p": p, "sinal": bool(p < LIMITE_SINAL)}
    p_vendedor_controlado = permutacao(
        h, "vendedor", estratificar_por=["mes_do_trimestre", "gerente"], n=REPETICOES_PERMUTACAO
    )["p"]

    pipe = dados.pipeline
    fechados = pipe[pipe.deal_stage.isin(["Won", "Lost"])]
    abertos = pipe[pipe.deal_stage.isin(["Engaging", "Prospecting"])]
    vazamento = {
        "fechados": int(len(fechados)),
        "fechados_sem_conta": int(fechados.account.isna().sum()),
        "abertos": int(len(abertos)),
        "abertos_sem_conta": int(abertos.account.isna().sum()),
    }

    return {
        "vazamento_do_campo_conta": vazamento,
        "tabela": tabela.to_dict("records"),
        "somas": soma,
        "acerto_medio": acerto,
        "fracao_do_teto": {
            "relogio": soma["valor_relogio"] / soma["valor_oraculo"],
            "preco_prazo": soma["valor_preco_prazo"] / soma["valor_oraculo"],
        },
        "razoes": razoes,
        "permutacao": permutacoes,
        "permutacao_vendedor_controlado_por_gerente": {
            "p": p_vendedor_controlado, "sinal": bool(p_vendedor_controlado < LIMITE_SINAL)},
        "parametros": {
            "rodadas_aleatorio": RODADAS_ALEATORIO,
            "repeticoes_permutacao": REPETICOES_PERMUTACAO,
            "numero_controle": NUMERO_CONTROLE,
            "reamostragens_intervalo": 5000,
        },
    }


def imprimir(e: dict) -> None:
    print("1. Backtest por corte (fonte: avaliacao/backtest.py)")
    for linha in e["tabela"]:
        print(f"   {linha['corte']}  vivos {linha['vivos']:>5}  fechar {linha['fila_fechar']:>5}"
              f"  relógio {linha['valor_relogio']:>8}  preço/prazo {linha['valor_preco_prazo']:>8}"
              f"  aleatório (média) {linha['valor_aleatorio']:>10.0f}  oráculo {linha['valor_oraculo']:>8}")
    print("\n2. Valor total ganho (fonte: avaliacao/backtest.py)")
    for nome, v in e["somas"].items():
        print(f"   {nome:<22} {v:>14,.0f}")
    print("\n3. Taxa média de acerto (fonte: avaliacao/backtest.py)")
    for nome, v in e["acerto_medio"].items():
        print(f"   {nome:<22} {v:.3f}")
    print(f"   relógio ÷ aleatório (taxa de acerto) = {e['acerto_medio']['acerto_relogio'] / e['acerto_medio']['acerto_aleatorio']:.2f}")
    print("\n4. Fração do teto, o oráculo que conhece o futuro = 1 (fonte: avaliacao/backtest.py)")
    for nome, v in e["fracao_do_teto"].items():
        print(f"   {nome:<12} {v:.3f}")
    print("\n5. Razão de valor ganho com IC 95%, reamostragem de vendedores (fonte: avaliacao/backtest.py)")
    for nome, r in e["razoes"].items():
        print(f"   {nome:<26} {r['razao']:.3f}   IC 95% [{r['ic_inferior']:.3f}, {r['ic_superior']:.3f}]")
    print(f"\n6. Atributos do deal: p-valor de {REPETICOES_PERMUTACAO} repetições, controle por mês do trimestre (fonte: avaliacao/permutacao.py)")
    for rotulo, v in e["permutacao"].items():
        print(f"   {rotulo:<42} p = {v['p']:.3f}")
    p = e["permutacao_vendedor_controlado_por_gerente"]["p"]
    print(f"   {'vendedor, controlado também por gerente':<42} p = {p:.3f}")
    v = e["vazamento_do_campo_conta"]
    print("\n7. Campo conta preenchido depois do desfecho (fonte: data/sales_pipeline.csv)")
    print(f"   fechados sem conta: {v['fechados_sem_conta']} de {v['fechados']}")
    print(f"   abertos sem conta:  {v['abertos_sem_conta']} de {v['abertos']}")


def gravar(e: dict, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "eval.json").write_text(json.dumps(e, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def main() -> None:
    e = calcular()
    imprimir(e)
    gravar(e, RAIZ / "app" / "data")


if __name__ == "__main__":
    main()
