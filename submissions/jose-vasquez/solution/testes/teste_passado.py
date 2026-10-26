"""Teste com o passado: a nota funciona?

Em 4 datas de 2017, o motor só enxerga o CRM como estava naquele dia.
Depois conferimos o que aconteceu nos 90 dias seguintes.

1. Foco: se o vendedor trabalhar os 20% do topo da lista, quanto da
   receita dos 90 dias seguintes ele pega? Comparamos:
     - a nota do Lead Scorer
     - a nota só pelo tempo aberta (sem a relação vendedor-cliente)
     - a nota "óbvia": taxa de ganho do vendedor no produto × preço
     - só o maior preço
     - ao acaso (média de 1.000 sorteios, o "feeling")
   Vendas empatadas (mesmo preço, mesma nota) são ordenadas por sorteio,
   com a média de 200 sorteios, para nenhum método ganhar pela ordem do arquivo.
2. Previsão: quanto o CRM promete, quanto o motor prevê e quanto entrou.
3. A chance prevista bate com o que aconteceu?
4. O motor não espia o futuro: mudar tudo o que aconteceu depois da data
   não pode mudar nada do que ele aprendeu.

Grava docs/resultado-teste.txt e docs/resultado-teste.json (lido pela tela).
Termina com erro se a nota não ganhar dos outros jeitos de escolher.

Rodar: python3 solution/testes/teste_passado.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "motor"))
import nota  # noqa: E402

DOCS = Path(__file__).resolve().parents[2] / "docs"
DATAS = ["2017-06-30", "2017-07-31", "2017-08-31", "2017-09-30"]
FOCO = 0.20
SORTEIOS = 1000
EMPATES = 200  # vendas com a mesma nota: a ordem entre elas é sorteada, e tiramos a média


def futuro(df, ab, t):
    """O que aconteceu com cada venda aberta nos 90 dias seguintes."""
    fim = t + pd.Timedelta(days=nota.HORIZONTE)
    real = df.loc[ab.index]
    ganhou = (real.deal_stage == "Won") & (real.close_date <= fim)
    return ganhou, np.where(ganhou, real.close_value, 0.0)


def nota_obvia(visto, ab):
    """Taxa de ganho do vendedor naquele produto (suavizada) × preço."""
    fech = visto[visto.deal_stage.isin(["Won", "Lost"])]
    ganhou = fech.deal_stage.eq("Won")
    geral = ganhou.mean()
    g = ganhou.groupby([fech.sales_agent, fech["product"]]).agg(["sum", "count"])
    taxa = (g["sum"] + geral * 20) / (g["count"] + 20)
    return np.array([taxa.get((s, p), geral) for s, p in zip(ab.sales_agent, ab["product"])]) * ab.sales_price.values


def receita_no_topo(ordem, receita, n):
    return receita[ordem[:n]].sum()


def receita_ordenando(valores, receita, n, rng):
    """Ordena do maior para o menor; empates são desfeitos por sorteio (média de EMPATES sorteios)."""
    valores = np.asarray(valores, dtype=float)
    total = 0.0
    for _ in range(EMPATES):
        p = rng.permutation(len(valores))
        total += receita_no_topo(p[np.argsort(-valores[p], kind="stable")], receita, n)
    return total / EMPATES


def foco_e_previsao(df):
    linhas, previsoes, calibra = [], [], []
    rng = np.random.default_rng(0)
    for data in DATAS:
        t = pd.Timestamp(data)
        visto = nota.ate_a_data(df, t)
        modelo = nota.aprender(df, t)
        ab = nota.abertas_em(visto, t)
        ganhou, receita = futuro(df, ab, t)
        total, n = receita.sum(), int(round(len(ab) * FOCO))

        todas = nota.classificar(ab, modelo, t, visto, separar_sem_cliente=False)
        so_tempo = todas.assign(valor_esperado=[modelo.chance_faixa(d) * p if d <= modelo.prazo_maximo else 0.0
                                                for d, p in zip(todas.dias, todas.sales_price)])
        r = {
            "nota": receita_ordenando(todas.valor_esperado, receita, n, rng),
            "so_tempo": receita_ordenando(so_tempo.valor_esperado, receita, n, rng),
            "obvia": receita_ordenando(nota_obvia(visto, ab), receita, n, rng),
            "preco": receita_ordenando(ab.sales_price, receita, n, rng),
            "acaso": np.mean([receita_no_topo(rng.permutation(len(ab)), receita, n) for _ in range(SORTEIOS)]),
        }
        linhas.append({"data": data, "abertas": len(ab), "foco": n, "receita_90d": total,
                       **{k: v / total for k, v in r.items()}})

        uso = nota.classificar(ab, modelo, t, visto)  # como a ferramenta usa: separa as sem cliente
        previsoes.append({"data": data, "crm": float(ab.sales_price.sum()),
                          "previsao": float(uso.valor_esperado.sum()), "real": float(total)})
        com_cliente = uso[uso.status.isin(["risco", "ativa", "esfriando"])]
        calibra.append(pd.DataFrame({"prevista": com_cliente.chance, "ganhou": ganhou[com_cliente.index]}))
    return pd.DataFrame(linhas), pd.DataFrame(previsoes), pd.concat(calibra)


def sem_espiar_o_futuro(df):
    """Embaralha tudo o que aconteceu depois de t: o que o motor aprende não pode mudar."""
    t = pd.Timestamp(DATAS[0])
    antes = nota.aprender(df, t)
    mexido = df.copy()
    depois = mexido.close_date > t
    rng = np.random.default_rng(1)
    mexido.loc[depois, "deal_stage"] = rng.choice(["Won", "Lost"], depois.sum())
    mexido.loc[depois, "close_date"] = mexido.loc[depois, "close_date"] + pd.to_timedelta(
        rng.integers(-60, 60, depois.sum()), unit="D")
    mexido.loc[depois, "close_date"] = mexido.loc[depois, ["close_date"]].max(axis=1).clip(lower=t + pd.Timedelta(days=1))
    depois_ = nota.aprender(mexido, t)
    return (antes.tabela.equals(depois_.tabela) and antes.relacao == depois_.relacao
            and antes.prazo_maximo == depois_.prazo_maximo and antes.fase_risco == depois_.fase_risco
            and antes.ajuste == depois_.ajuste)


def main():
    df = nota.carregar()
    foco, prev, cal = foco_e_previsao(df)
    media = foco[["nota", "so_tempo", "obvia", "preco", "acaso"]].mean()
    ganha = {k: int((foco.nota > foco[k]).sum()) for k in ["so_tempo", "obvia", "preco", "acaso"]}
    cal["faixa"] = pd.cut(cal.prevista, [0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0])
    tab_cal = cal.groupby("faixa", observed=True).agg(vendas=("ganhou", "size"), prevista=("prevista", "mean"),
                                                      real=("ganhou", "mean"))
    limpo = sem_espiar_o_futuro(df)

    nomes = {"nota": "Nota do Lead Scorer", "so_tempo": "Nota só pelo tempo aberta",
             "obvia": "Nota óbvia (taxa do vendedor no produto × preço)", "preco": "Só o maior preço",
             "acaso": "Ao acaso (feeling)"}
    txt = ["1) Focando nos 20% do topo, quanto da receita dos 90 dias seguintes o vendedor pega?", ""]
    txt.append(foco.assign(**{k: (foco[k] * 100).round(1) for k in nomes}).to_string(index=False))
    txt += ["", "Média das 4 datas:"]
    txt += [f"  {nomes[k]:50} {media[k] * 100:5.1f}%" + (f"   (a nota ganhou em {ganha[k]} de 4 datas)" if k in ganha else "")
            for k in nomes]
    txt += ["", "2) Previsão de receita para os 90 dias seguintes", ""]
    txt.append(prev.assign(crm_vezes_real=(prev.crm / prev.real).round(1),
                           erro_previsao=((prev.previsao / prev.real - 1) * 100).round(0)).round(0).to_string(index=False))
    txt += ["", "3) A chance prevista bate com o que aconteceu? (vendas com cliente, 4 datas)", ""]
    txt.append(tab_cal.round(3).to_string())
    txt += ["", f"4) O motor não espia o futuro: {'OK' if limpo else 'FALHOU'}"]
    DOCS.mkdir(exist_ok=True)
    (DOCS / "resultado-teste.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("\n".join(txt))

    resumo = {
        "datas": DATAS,
        "foco": {k: round(float(media[k]), 3) for k in nomes},
        "ganhou_em": ganha,
        "previsao": [{k: (v if k == "data" else round(v)) for k, v in r.items()} for r in prev.to_dict("records")],
        "calibracao": [{"prevista": round(float(r.prevista), 3), "real": round(float(r.real), 3), "vendas": int(r.vendas)}
                       for r in tab_cal.itertuples()],
    }
    (DOCS / "resultado-teste.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")

    erros = [f"a nota perdeu de '{nomes[k]}' na média" for k in ["so_tempo", "obvia", "preco", "acaso"]
             if media["nota"] <= media[k]]
    if not limpo:
        erros.append("o motor mudou ao mexer no futuro")
    if erros:
        print("\nFALHOU: " + "; ".join(erros))
        sys.exit(1)
    print("\nTudo certo: a nota ganhou de todos os outros jeitos de escolher, e o motor não espia o futuro.")


if __name__ == "__main__":
    main()
