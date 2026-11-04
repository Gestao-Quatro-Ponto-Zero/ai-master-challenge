"""Motor do Lead Scorer (Challenge 003 G4 AI Master).

Lê os dados do CRM e a configuração, classifica cada deal aberto em uma de 4 listas
(Foco, Requalificar ou encerrar, Iniciar contato, Automatizar), calcula a nota e escreve
uma explicação em português para o vendedor.

Uso:
    python gerar_scores.py --dados ../data --config config.json --saida saida

Garantia contra vazamento de futuro: toda a lógica roda sobre uma "visão na data de
referência" (função visao_na_data). Essa visão apaga tudo o que aconteceu depois da data,
então nenhuma regra consegue enxergar informação futura.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

LISTA_FOCO = "Foco"
LISTA_REQUALIFICAR = "Requalificar ou encerrar"
LISTA_INICIAR = "Iniciar contato"
LISTA_AUTOMATIZAR = "Automatizar"
ORDEM_LISTAS = [LISTA_FOCO, LISTA_REQUALIFICAR, LISTA_INICIAR, LISTA_AUTOMATIZAR]


# --------------------------------------------------------------------------- formatação
def usd(v: float) -> str:
    return "US$ " + f"{v:,.0f}".replace(",", ".")


def pct(chance: float) -> str:
    if chance == 0:
        return "0%"
    if chance < 0.01:
        return "menos de 1%"
    return f"{chance * 100:.0f}%"


# --------------------------------------------------------------------------- dados
def carregar_config(caminho: str | Path) -> dict:
    cfg = json.loads(Path(caminho).read_text(encoding="utf-8"))
    obrig = ["data_referencia", "inicio_observacao", "valor_minimo_foco_usd", "valor_deal_grande_usd", "idade_alerta_dias"]
    faltando = [k for k in obrig if k not in cfg]
    if faltando:
        raise ValueError(f"config sem os campos: {faltando}")
    cfg.setdefault("correcoes_nome_produto", {})
    cfg.setdefault("mover_chance_zero_para_requalificar", False)
    return cfg


def carregar_dados(pasta: str | Path, cfg: dict) -> pd.DataFrame:
    pasta = Path(pasta)
    p = pd.read_csv(pasta / "sales_pipeline.csv")
    contas = pd.read_csv(pasta / "accounts.csv")
    produtos = pd.read_csv(pasta / "products.csv")
    times = pd.read_csv(pasta / "sales_teams.csv")
    p["product"] = p["product"].replace(cfg["correcoes_nome_produto"])
    for c in ["engage_date", "close_date"]:
        p[c] = pd.to_datetime(p[c])
    p = (p.merge(produtos, on="product", how="left")
          .merge(times, on="sales_agent", how="left")
          .merge(contas, on="account", how="left"))
    sem_preco = p[p.sales_price.isna()]["product"].unique().tolist()
    if sem_preco:
        raise ValueError(f"produtos sem preço no catálogo (corrija em correcoes_nome_produto): {sem_preco}")
    return p


def visao_na_data(p: pd.DataFrame, data_ref: pd.Timestamp) -> pd.DataFrame:
    """Reconstrói o CRM como ele estava no fim do dia data_ref.
    - deals iniciados depois da data somem;
    - deals fechados depois da data voltam a ficar abertos (sem data e sem valor de fechamento);
    - deals em prospecção (sem data) só existem se data_ref for o último dia da base."""
    ultima = max(p.engage_date.max(), p.close_date.max())
    v = p.copy()
    prosp = v.deal_stage == "Prospecting"
    v = v[(prosp & (data_ref >= ultima)) | (~prosp & (v.engage_date <= data_ref))].copy()
    futuro = v.close_date.notna() & (v.close_date > data_ref)
    v.loc[futuro, ["deal_stage"]] = "Engaging"
    v.loc[futuro, ["close_date", "close_value"]] = np.nan
    return v


# --------------------------------------------------------------------------- lógica
def limite_ciclo(v: pd.DataFrame) -> int:
    fech = v[v.close_date.notna()]
    return int((fech.close_date - fech.engage_date).dt.days.max())


def curva_chance(v: pd.DataFrame, data_ref: pd.Timestamp, inicio_obs: pd.Timestamp, limite: int) -> pd.Series:
    """Chance de um deal aberto há X dias acabar ganho, segundo a história até data_ref.
    Safra: deals iniciados entre inicio_obs e (data_ref - limite - 1), cujo desfecho já é conhecido."""
    fim = data_ref - pd.Timedelta(days=limite + 1)
    s = v[(v.engage_date >= inicio_obs) & (v.engage_date <= fim)]
    if len(s) == 0:
        raise ValueError("safra vazia: data de referência cedo demais para estimar a curva")
    ciclo = (s.close_date - s.engage_date).dt.days  # NaN = nunca fechou até a data
    ganho = s.deal_stage == "Won"
    valores = [float(ganho[ciclo.isna() | (ciclo >= idade)].mean()) for idade in range(limite + 1)]
    return pd.Series(valores, index=range(limite + 1), name="chance")


def classificar(v: pd.DataFrame, data_ref: pd.Timestamp, cfg: dict) -> tuple[pd.DataFrame, dict]:
    inicio = pd.Timestamp(cfg["inicio_observacao"])
    lim = limite_ciclo(v)
    curva = curva_chance(v, data_ref, inicio, lim)

    d = v[v.deal_stage.isin(["Engaging", "Prospecting"])].copy()
    d["idade_dias"] = (data_ref - d.engage_date).dt.days
    d["chance"] = d.idade_dias.map(curva)  # NaN em prospecção e acima do limite
    d["valor_esperado"] = d.chance * d.sales_price

    prosp = d.deal_stage == "Prospecting"
    fora_ciclo = ~prosp & (d.idade_dias > lim)
    if cfg["mover_chance_zero_para_requalificar"]:
        fora_ciclo |= ~prosp & (d.chance == 0)
    baixo = ~prosp & ~fora_ciclo & (d.sales_price < cfg["valor_minimo_foco_usd"])
    d["lista"] = np.select([prosp, fora_ciclo, baixo], [LISTA_INICIAR, LISTA_REQUALIFICAR, LISTA_AUTOMATIZAR], LISTA_FOCO)
    grande = d.sales_price >= cfg["valor_deal_grande_usd"]
    d["acao"] = np.select(
        [d.lista == LISTA_FOCO, (d.lista == LISTA_REQUALIFICAR) & grande, d.lista == LISTA_REQUALIFICAR,
         d.lista == LISTA_INICIAR, d.lista == LISTA_AUTOMATIZAR],
        ["Avançar este deal", "Ligar para requalificar", "Encerrar no CRM",
         "Fazer o primeiro contato", "Incluir na cadência automática (mensagens em lote)"], "")

    # nota 0-100: % dos OUTROS deals do Foco que têm valor esperado menor (100 = o maior da empresa, 0 = o menor)
    foco = d.lista == LISTA_FOCO
    d["nota"] = np.nan
    n_foco = int(foco.sum())
    if n_foco > 1:
        abaixo = d.loc[foco, "valor_esperado"].rank(method="min") - 1
        d.loc[foco, "nota"] = (abaixo / (n_foco - 1) * 100).round()
    elif n_foco == 1:
        d.loc[foco, "nota"] = 100

    d["porque"] = d.apply(lambda r: _porque(r, lim, cfg), axis=1)
    d["nota_texto"] = d.apply(_nota_texto, axis=1)
    d["aviso"] = np.where(d.account.isna(), "Empresa não cadastrada: complete o cadastro no CRM", "")

    # ordem dentro de cada lista
    d["_k1"] = np.select([d.lista == LISTA_FOCO, d.lista == LISTA_AUTOMATIZAR], [d.valor_esperado, d.valor_esperado], d.sales_price)
    d["_k0"] = np.where(d.acao == "Ligar para requalificar", 1, 0)
    d = d.sort_values(["lista", "_k0", "_k1", "idade_dias", "opportunity_id"], ascending=[True, False, False, True, True],
                      key=lambda s: s.map(ORDEM_LISTAS.index) if s.name == "lista" else s)
    d["ordem_na_lista"] = d.groupby("lista").cumcount() + 1
    d = d.drop(columns=["_k0", "_k1"])
    meta = {"limite_ciclo_dias": lim, "curva": curva,
            "safra_curva": [str(inicio.date()), str((data_ref - pd.Timedelta(days=lim + 1)).date())]}
    return d, meta


def _porque(r, lim: int, cfg: dict) -> str:
    prod = f"{usd(r.sales_price)} ({r['product']})"
    if r.lista == LISTA_FOCO:
        idade = int(r.idade_dias)
        if r.chance == 0:
            return (f"Na história da empresa, nenhum deal com {idade} dias em negociação foi ganho (chance 0%). "
                    f"Este deal está no limite de {lim} dias: confirme com o cliente se ainda existe interesse. "
                    f"Preço: {prod}.")
        txt = (f"Valor esperado {usd(r.valor_esperado)} = preço {prod} × {pct(r.chance)} de chance. "
               f"Na história da empresa, deals com {idade} dias em negociação foram ganhos {pct(r.chance)} das vezes.")
        if idade >= cfg["idade_alerta_dias"]:
            txt += (f" Atenção: depois de {cfg['idade_alerta_dias']} dias a chance cai rápido, "
                    f"e nenhum deal fechou depois de {lim} dias.")
        return txt
    if r.lista == LISTA_REQUALIFICAR:
        base = f"Aberto há {int(r.idade_dias)} dias. Nenhum deal da história fechou depois de {lim} dias. "
        if r.sales_price >= cfg["valor_deal_grande_usd"]:
            return base + (f"Preço {prod}, igual ou acima de {usd(cfg['valor_deal_grande_usd'])}: vale uma ligação "
                           f"para confirmar se ainda existe interesse antes de encerrar.")
        return base + f"Preço {prod}, abaixo de {usd(cfg['valor_deal_grande_usd'])}: encerre no CRM para limpar o pipeline."
    if r.lista == LISTA_INICIAR:
        return (f"Em prospecção: a base não tem histórico para estimar a chance de deals nesta etapa. "
                f"Ordenado pelo preço: {prod}.")
    return (f"Preço {prod} abaixo do mínimo de {usd(cfg['valor_minimo_foco_usd'])} para atenção individual. "
            f"Valor esperado {usd(r.valor_esperado)} ({pct(r.chance)} de chance para um deal com {int(r.idade_dias)} dias).")


def _nota_texto(r) -> str:
    if r.lista == LISTA_FOCO:
        n = int(r.nota)
        return f"Nota {n} de 100: vale mais (em valor esperado) que {n}% dos outros deals em Foco na empresa"
    return {LISTA_REQUALIFICAR: "Sem nota: fora do ciclo histórico de vendas",
            LISTA_INICIAR: "Sem nota: prospecção não tem histórico de chance",
            LISTA_AUTOMATIZAR: "Sem nota: vai para a cadência automática"}[r.lista]


# --------------------------------------------------------------------------- validação
def volta_no_tempo(p: pd.DataFrame, cfg: dict, corte: str = "2017-09-30") -> dict:
    """Aplica a lógica como se hoje fosse 'corte' e mede quanto da receita ganha depois
    (até a data de referência) estava nos 20% de deals com maior valor esperado."""
    corte, fim = pd.Timestamp(corte), pd.Timestamp(cfg["data_referencia"])
    d, _ = classificar(visao_na_data(p, corte), corte, cfg)
    real = p.set_index("opportunity_id")
    d = d[d.deal_stage == "Engaging"].copy()
    desfecho = real.loc[d.opportunity_id, ["deal_stage", "close_date", "close_value"]].reset_index(drop=True)
    ganhou = (desfecho.deal_stage == "Won") & (desfecho.close_date <= fim)
    d["receita_depois"] = np.where(ganhou.values, desfecho.close_value.fillna(0).values, 0.0)
    n = int(round(len(d) * 0.2))
    total = d.receita_depois.sum()
    nossa = d.sort_values(["valor_esperado", "opportunity_id"], ascending=[False, True], na_position="last").head(n)
    so_valor = d.sort_values(["sales_price", "opportunity_id"], ascending=[False, True]).head(n)
    return {"data_corte": str(corte.date()), "deals_em_negociacao": int(len(d)), "top_n": n,
            "receita_depois_usd": round(float(total), 2),
            "captura_top20_nossa_logica": round(float(nossa.receita_depois.sum() / total), 3),
            "captura_top20_so_valor": round(float(so_valor.receita_depois.sum() / total), 3)}


# --------------------------------------------------------------------------- saída
def gerar(pasta_dados, caminho_config) -> dict:
    cfg = carregar_config(caminho_config)
    p = carregar_dados(pasta_dados, cfg)
    data_ref = pd.Timestamp(cfg["data_referencia"])
    d, meta = classificar(visao_na_data(p, data_ref), data_ref, cfg)

    def limpo(x):
        return None if (x is None or (isinstance(x, float) and np.isnan(x))) else x

    deals = [{
        "id": r.opportunity_id, "vendedor": r.sales_agent, "gerente": r.manager, "regiao": r.regional_office,
        "empresa": limpo(r.account), "setor": limpo(r.sector), "produto": r["product"], "preco_usd": float(r.sales_price),
        "etapa": "Negociação" if r.deal_stage == "Engaging" else "Prospecção",
        "idade_dias": int(r.idade_dias) if pd.notna(r.idade_dias) else None,
        "chance": limpo(round(float(r.chance), 4)) if pd.notna(r.chance) else None,
        "valor_esperado_usd": round(float(r.valor_esperado), 2) if pd.notna(r.valor_esperado) else None,
        "nota": int(r.nota) if pd.notna(r.nota) else None,
        "lista": r.lista, "ordem_na_lista": int(r.ordem_na_lista), "acao": r.acao,
        "porque": r.porque, "nota_texto": r.nota_texto, "aviso": r.aviso or None,
    } for _, r in d.iterrows()]

    resumo = {l: {"deals": int((d.lista == l).sum()), "valor_tabela_usd": float(d.loc[d.lista == l, "sales_price"].sum())}
              for l in ORDEM_LISTAS}
    # equipe completa vem do cadastro de times (inclui vendedores sem nenhum deal)
    times = (pd.read_csv(Path(pasta_dados) / "sales_teams.csv")[["sales_agent", "manager", "regional_office"]]
             .sort_values(["regional_office", "manager", "sales_agent"]))
    return {
        "versao_motor": "1.0",
        "data_referencia": cfg["data_referencia"],
        "parametros": {k: v for k, v in cfg.items() if not k.startswith("_")},
        "limite_ciclo_dias": meta["limite_ciclo_dias"],
        "safra_curva": meta["safra_curva"],
        "curva_chance": [{"idade_dias": int(i), "chance": round(float(c), 4)} for i, c in meta["curva"].items()],
        "resumo_por_lista": resumo,
        "vendedores": [{"vendedor": a, "gerente": m, "regiao": r} for a, m, r in times.itertuples(index=False)],
        "validacao_volta_no_tempo": volta_no_tempo(p, cfg),
        "deals": deals,
    }


def main():
    ap = argparse.ArgumentParser(description="Gera a priorização de deals do Lead Scorer.")
    ap.add_argument("--dados", default=str(Path(__file__).parent.parent / "data"))
    ap.add_argument("--config", default=str(Path(__file__).parent / "config.json"))
    ap.add_argument("--saida", default=str(Path(__file__).parent / "saida"))
    a = ap.parse_args()
    res = gerar(a.dados, a.config)
    out = Path(a.saida); out.mkdir(parents=True, exist_ok=True)
    (out / "deals_priorizados.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    pd.DataFrame(res["deals"]).to_csv(out / "deals_priorizados.csv", index=False, encoding="utf-8")
    print(f"Data de referência: {res['data_referencia']} | limite de ciclo: {res['limite_ciclo_dias']} dias")
    for l, v in res["resumo_por_lista"].items():
        print(f"  {l}: {v['deals']} deals")
    vt = res["validacao_volta_no_tempo"]
    print(f"Volta no tempo ({vt['data_corte']}): top 20% capturou {vt['captura_top20_nossa_logica']:.0%} da receita "
          f"(só valor: {vt['captura_top20_so_valor']:.0%})")
    print(f"Arquivos gerados em {out}/")


if __name__ == "__main__":
    main()
