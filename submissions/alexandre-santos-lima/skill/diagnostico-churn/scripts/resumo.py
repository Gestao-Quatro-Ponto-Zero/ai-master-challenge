"""Imprime o resumo do diagnóstico a partir dos JSONs gerados (o que mudou desde a última rodada fica visível aqui)."""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
d = json.loads((src / "data.json").read_text(encoding="utf-8"))
m = json.loads((src / "mes_uso.json").read_text(encoding="utf-8"))["stats"]
s = json.loads((src / "sugestoes.json").read_text(encoding="utf-8"))
br = lambda v, n=1: f"{v:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")
pc = lambda v, n=1: br(v * 100, n) + "%"
k, df, dt = d["kpis"], d["definicoes"], d["datas"]
mes = {x["mes"]: x for x in d["mensal"]}
ult, ant = d["mensal"][-1], d["mensal"][-13]

linhas = [
    ("CHURN", ""),
    ("% de cada safra que cancela", f"{pc(s['safra']['taxa'])} (faixa {pc(s['safra']['ic'][0])}–{pc(s['safra']['ic'][1])})"),
    ("Cancelamentos/mês, 12 meses", f"{ant['eventos_churn']} → {ult['eventos_churn']} ({br(ult['eventos_churn'] / max(ant['eventos_churn'], 1))}×)"),
    ("Assinaturas ativas, 12 meses", f"{br(ant['assinaturas_ativas'], 0)} → {br(ult['assinaturas_ativas'], 0)} ({br(ult['assinaturas_ativas'] / max(ant['assinaturas_ativas'], 1))}×)"),
    ("Variação explicada pela base", f"{pc(m['r2'], 0)} · elasticidade {br(m['elasticidade'], 2)} (IC {br(m['elasticidade_ic'][0], 2)}–{br(m['elasticidade_ic'][1], 2)})"),
    ("Efeito do mês do ano", f"p = {br(m['p_sazonal'], 3)}"),
    ("Uso × churn, descontada a base", f"ρ = {br(m['rho_controlado'], 2)}, p = {br(m['p_controlado'], 3)}  (cru: ρ = {br(m['rho_cru'], 2)})"),
    ("Uso 90 d antes × depois do churn", f"{br(m['antes_media'])} × {br(m['depois_media'])} · {pc(m['pct_usa_depois'], 0)} seguem usando"),
    ("Variáveis com efeito real", f"{k['variaveis_significativas']} de {k['variaveis_testadas']}"),
    ("QUALIDADE DOS DADOS", ""),
    ("Contas em que os registros discordam", f"{df['so_flag'] + df['so_evento']} de {k['contas']}"),
    ("Anuais encerrados com < 1 ano", f"{dt['anuais_menos_1_ano']} de {dt['anuais_encerradas']}"),
    ("Tickets sem nota de satisfação", pc(k["pct_sem_nota"], 0)),
] + [(a["checagem"], a["resultado"]) for a in d["auditoria"] if a["checagem"].startswith(("Uso fora", "Tickets abertos antes"))] + [
    ("PREVISÃO", ""),
    (f"Base de {br(s['base_atual'], 0)} assinaturas", next(f"{br(c['esperado'], 0)} registros/mês (faixa {br(c['lo'], 0)}–{br(c['hi'], 0)})" for c in s["curva"] if c["base"] == s["base_atual"])),
]
w = max(len(a) for a, _ in linhas)
for a, b in linhas:
    print(f"\n{a}" if not b else f"  {a.ljust(w)}  {b}")
print(f"\nDashboard: {src.parent / 'dist'} (build) · prints da validação em solution/outputs/validacao/")
