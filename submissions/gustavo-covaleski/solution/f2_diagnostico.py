import math

import pandas as pd
from scipy.stats import norm

from comum import OUT_DIR, ler_ds1, salvar_json

ROTULO_DURACAO = "variável sintética e inválida (T3); usada só como premissa de variância"
PREMISSA = "premissa (editável), não dado"
VOLUME_ANO = 30000  # premissa do brief
SEMANAS_ANO = 52
ALFA, PODER = 0.05, 0.8
MDE_ALVO_H = 2.0
MIN_N_COMBO = 20
MINUTOS = [2, 3, 4]
REAIS_H = [25, 35, 50]
CH, PR, TP = "Ticket Channel", "Ticket Priority", "Ticket Type"
GRANULARIDADES = {"prioridade": [PR], "canal": [CH], "canal x prioridade": [CH, PR],
                  "canal x prioridade x tipo": [CH, PR, TP]}


def k(alfa=ALFA, poder=PODER):
    return norm.ppf(1 - alfa / 2) + norm.ppf(poder)


def mde(sd, n1, n2, alfa=ALFA, poder=PODER):
    return k(alfa, poder) * sd * math.sqrt(1 / n1 + 1 / n2)


def n_para_mde(sd, alvo, alfa=ALFA, poder=PODER):
    # n1 = n2 = n  =>  alvo = k·sd·√(2/n)
    return math.ceil(2 * (k(alfa, poder) * sd / alvo) ** 2)


def semanas_para_n(n, participacao, volume_ano=VOLUME_ANO, semanas_ano=SEMANAS_ANO):
    return n / (volume_ano / semanas_ano * participacao)


def base_duracao(df):
    d = df[df["Ticket Status"] == "Closed"].copy()
    d["duracao_h"] = (pd.to_datetime(d["Time to Resolution"]) - pd.to_datetime(d["First Response Time"])).dt.total_seconds() / 3600
    return d[d["duracao_h"] > 0]


def nome(chave):
    return " | ".join(chave) if isinstance(chave, tuple) else str(chave)


def main():
    df = ler_ds1()
    d = base_duracao(df)
    sd = float(d["duracao_h"].std(ddof=1))
    n_alvo = n_para_mde(sd, MDE_ALVO_H)

    linhas = []
    for gran, cols in GRANULARIDADES.items():
        n_dur = d.groupby(cols).size()
        n_mde = n_dur[n_dur >= MIN_N_COMBO] if len(cols) == 3 else n_dur
        dois = n_mde.nsmallest(2)
        part = df.groupby(cols).size() / len(df)  # participação no DS1 inteiro (todos os status)
        menor = part.idxmin()
        linhas.append({
            "granularidade": gran, "n_grupos": int(len(part)), "menor_grupo": nome(menor),
            "participacao": round(float(part.min()), 6),
            "n_atual": int(n_dur.get(menor, 0)),
            "grupos_comparados_mde": " vs ".join(nome(i) for i in dois.index),
            "n_comparados": "/".join(str(int(v)) for v in dois.values),
            "mde_atual_h": round(mde(sd, *dois.values), 2),
            "n_para_2h": n_alvo,
            "semanas_para_2h": round(semanas_para_n(n_alvo, float(part.min())), 1),
            "rotulo": f"duração: {ROTULO_DURACAO}; volume e semanas: {PREMISSA}",
        })
    tab = pd.DataFrame(linhas)

    combos = d.groupby([CH, PR, TP])["duracao_h"].agg(["size", "mean"])
    combos = combos[combos["size"] >= MIN_N_COMBO]
    hi, lo = combos["mean"].idxmax(), combos["mean"].idxmin()
    piores = {
        "combinacoes_com_n_ge_20": int(len(combos)),
        "maior_media": {"combinacao": nome(hi), "n": int(combos.at[hi, "size"]), "media_h": round(float(combos.at[hi, "mean"]), 2)},
        "menor_media": {"combinacao": nome(lo), "n": int(combos.at[lo, "size"]), "media_h": round(float(combos.at[lo, "mean"]), 2)},
        "diferenca_h": round(float(combos.at[hi, "mean"] - combos.at[lo, "mean"]), 2),
        "mde_para_esses_n_h": round(mde(sd, combos.at[hi, "size"], combos.at[lo, "size"]), 2),
        "rotulo": ROTULO_DURACAO,
        "teste": "nenhum (descritivo; F0 proíbe teste por segmento)",
    }
    tab = pd.concat([tab, pd.DataFrame([{
        "granularidade": "piores combinações (1.2)", "menor_grupo": "", "participacao": None, "n_atual": None,
        "grupos_comparados_mde": f"{piores['maior_media']['combinacao']} vs {piores['menor_media']['combinacao']}",
        "n_comparados": f"{piores['maior_media']['n']}/{piores['menor_media']['n']}",
        "mde_atual_h": piores["mde_para_esses_n_h"], "n_para_2h": None, "semanas_para_2h": None,
        "rotulo": f"diferença observada {piores['diferenca_h']} h; {ROTULO_DURACAO}"}])], ignore_index=True)
    tab.to_csv(OUT_DIR / "f2_mde.csv", index=False)

    custo = pd.DataFrame([{"min_por_ticket": m, "reais_por_hora": r, "volume_ano": VOLUME_ANO,
                           "custo_anual_triagem_reais": round(VOLUME_ANO * m / 60 * r, 2),
                           "cenario_base": m == 3 and r == 35, "rotulo": PREMISSA}
                          for m in MINUTOS for r in REAIS_H])
    custo.to_csv(OUT_DIR / "f2_custo_triagem.csv", index=False)

    salvar_json({
        "rotulo": PREMISSA,
        "sd_duracao_h": round(sd, 4), "sd_origem": f"DS1, Closed com duração > 0 (n = {len(d)}); {ROTULO_DURACAO}",
        "alfa": ALFA, "poder": PODER, "z_soma": round(k(), 4), "mde_alvo_h": MDE_ALVO_H,
        "volume_ano": VOLUME_ANO, "volume_origem": "brief (~30 mil tickets/ano)", "semanas_ano": SEMANAS_ANO,
        "participacao_origem": "participação observada no DS1 inteiro (8.469 tickets, todos os status)",
        "min_n_combo_mde": MIN_N_COMBO,
        "custo_minutos_grade": MINUTOS, "custo_reais_h_grade": REAIS_H, "custo_base": {"min": 3, "reais_h": 35},
    }, "f2_premissas.json")

    base = custo[custo["cenario_base"]].iloc[0]["custo_anual_triagem_reais"]
    salvar_json({
        "n_base_duracao": int(len(d)), "rotulo_duracao": ROTULO_DURACAO,
        "piores_combinacoes": piores,
        "custo_triagem": {
            "cenario_A": {"custo_anual_base_reais": base,
                          "faixa_reais": [float(custo["custo_anual_triagem_reais"].min()), float(custo["custo_anual_triagem_reais"].max())],
                          "formula_economia": "economia = cobertura_automatica × custo_anual_triagem (cobertura medida na F3; não calculada aqui)",
                          "arquivo": "f2_custo_triagem.csv", "rotulo": PREMISSA},
            "cenario_B": "Economia de triagem = 0; o ganho viria do reroteamento evitado, não calculável (nenhum dataset registra transferência).",
        },
    }, "f2_diagnostico.json")

    print(f"sd duração = {sd:.2f} h ({ROTULO_DURACAO}); n por grupo p/ MDE 2 h = {n_alvo}")
    print(tab[["granularidade", "menor_grupo", "participacao", "n_atual", "n_comparados", "mde_atual_h", "semanas_para_2h"]].to_string(index=False))
    print(f"1.2: diferença {piores['diferenca_h']} h, MDE {piores['mde_para_esses_n_h']} h, {piores['combinacoes_com_n_ge_20']} combinações com n ≥ 20")
    print(f"custo cenário A: base R$ {base:,.0f}; faixa R$ {custo['custo_anual_triagem_reais'].min():,.0f}–{custo['custo_anual_triagem_reais'].max():,.0f}")


if __name__ == "__main__":
    main()
