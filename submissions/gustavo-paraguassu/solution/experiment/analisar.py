"""Lê runtime/eventos.jsonl e calcula as métricas da H9 e o resultado do teste com colegas.

Uso (de dentro de solution/): python experiment/analisar.py [caminho/eventos.jsonl]

Parte 1, operação ao vivo (clientes reais falando com o bot):
  primeira resposta, tempo de atendimento, % que precisou de pergunta, % resolvido sozinho,
  aceitação da sugestão de fila na triagem, transferências, reaberturas, edição do rascunho, CSAT.
Parte 2, experimento (cada colega atende 16 cenários: 8 COM e 8 SEM assistente, alternados):
  tempo por chamado, acerto de fila, comparação pareada por participante.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402

src = Path(sys.argv[1]) if len(sys.argv) > 1 else config.RUNTIME / "eventos.jsonl"
ev = pd.DataFrame([json.loads(x) for x in open(src)])
ev["ts"] = pd.to_datetime(ev["ts"])
R = {}

# ------------------------------------------------------------------ parte 1: operação ao vivo
eh_exp = ev["exp_participante"].notna() if "exp_participante" in ev else pd.Series(False, index=ev.index)
vivo = ev[ev.ticket.notna() & ~eh_exp]
criados = vivo[vivo.evento == "ticket_criado"].set_index("ticket").ts
if len(criados):
    def primeiro(nomes):
        x = vivo[vivo.evento.isin(nomes)].groupby("ticket").ts.min()
        return (x - criados.reindex(x.index)).dt.total_seconds()

    tri = vivo[vivo.evento == "triado"].drop_duplicates("ticket")
    resp = vivo[vivo.evento == "resposta_enviada"]
    defin = vivo[vivo.evento == "fila_definida"]
    csat = vivo[vivo.evento == "csat"]
    n = len(criados)
    R["vivo"] = {
        "tickets": n,
        "primeira_resposta_mediana_s": round(primeiro(["confirmacao_enviada", "pergunta_enviada",
                                                       "resposta_automatica"]).median(), 1),
        "resposta_humana_mediana_s": round(primeiro(["resposta_enviada"]).median(), 1) if len(resp) else None,
        "pct_direto_para_fila": round((tri.destino == "fila").mean() * 100, 1),
        "pct_pergunta_ao_cliente": round(tri.vai_perguntar.mean() * 100, 1),
        "pct_resposta_automatica": round(vivo[vivo.evento == "resposta_automatica"].ticket.nunique() / n * 100, 1),
        "faq_resolvido": int((vivo.evento == "faq_resolvido").sum()),
        "faq_nao_resolvido": int((vivo.evento == "faq_nao_resolvido").sum()),
        "triagem_aceitou_sugestao_pct": round(defin.aceitou_sugestao.mean() * 100, 1) if len(defin) else None,
        "transferencias_por_100": round((vivo.evento == "transferido").sum() / n * 100, 1),
        "reaberturas_por_100": round((vivo.evento == "reaberto").sum() / n * 100, 1),
        "rascunho_enviado_sem_edicao_pct": round((~resp.editado.astype(bool)).mean() * 100, 1) if len(resp) else None,
        "csat_medio": round(csat.nota.mean(), 2) if len(csat) else None,
        "csat_respostas": int(len(csat)),
        "custo_llm_usd": round(tri.custo_usd.fillna(0).sum(), 4),
        "motivos_triagem_humana": tri.motivos.explode().dropna().str.split(r" \(|:").str[0].value_counts().to_dict(),
    }

# ------------------------------------------------------------------ parte 2: experimento
if "exp_participante" in ev:
    x = ev[(ev.evento == "resposta_enviada") & ev.exp_participante.notna()].copy()
    if len(x):
        x["acertou_fila"] = x.fila == x.exp_fila_verdadeira
        g = x.groupby("exp_modo").agg(chamados=("ticket", "count"), tempo_mediano_s=("segundos_atendimento", "median"),
                                      tempo_medio_s=("segundos_atendimento", "mean"),
                                      acerto_fila_pct=("acertou_fila", "mean"))
        g["acerto_fila_pct"] = (g.acerto_fila_pct * 100).round(1)
        sug = ev[(ev.evento == "triado") & eh_exp].drop_duplicates("ticket").set_index("ticket").fila
        com = x[x.exp_modo == "com"].assign(sugestao=lambda d: d.ticket.map(sug))
        errada = com[com.sugestao != com.exp_fila_verdadeira]
        certa = com[com.sugestao == com.exp_fila_verdadeira]
        par = x.pivot_table(index="exp_participante", columns="exp_modo", values="segundos_atendimento",
                            aggfunc="median")
        transf = ev[(ev.evento == "transferido") & ev.exp_participante.notna()]
        R["experimento"] = {
            "participantes": int(x.exp_participante.nunique()),
            "por_modo": g.round(1).to_dict(orient="index"),
            "mediana_por_participante_s": par.round(1).to_dict(orient="index"),
            "participantes_mais_rapidos_com_assistente": int((par.get("com") < par.get("sem")).sum())
            if {"com", "sem"} <= set(par.columns) else None,
            "com_assistente_aceitou_sem_editar_pct": round(
                (~x[x.exp_modo == "com"].editado.astype(bool)).mean() * 100, 1),
            # viés de automação: o atendente corrige a IA quando ela erra? e estraga quando ela acerta?
            "com_sugestao_errada_n": int(len(errada)),
            "com_sugestao_errada_corrigida_pct": round(errada.acertou_fila.mean() * 100, 1) if len(errada) else None,
            "com_sugestao_certa_mantida_pct": round(certa.acertou_fila.mean() * 100, 1) if len(certa) else None,
            "com_transferencias": int(len(transf)),
        }
        if {"com", "sem"} <= set(g.index) and g.loc["sem", "tempo_mediano_s"] > 0:
            R["experimento"]["reducao_tempo_mediano_pct"] = round(
                (1 - g.loc["com", "tempo_mediano_s"] / g.loc["sem", "tempo_mediano_s"]) * 100, 1)

print(json.dumps(R, indent=1, ensure_ascii=False, default=str))
out = config.SOLUTION / "outputs" / "metricas_eventos.json"
if "--salvar" in sys.argv:
    out.write_text(json.dumps(R, indent=1, ensure_ascii=False, default=str))
    print(f"salvo em {out}")
