"""13 — Gera a planilha-prova da taxa de "nova assinatura após o fim" (D8), com fórmulas vivas e parâmetros editáveis.
Uso: python -I 13_planilha_renovacao.py <pasta_dados> <saida.xlsx>"""
import sys, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
D, OUT = sys.argv[1], sys.argv[2]
a = pd.read_csv(f"{D}/ravenstack_accounts.csv").set_index("account_id")
s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv")
p = s[~s.is_trial].copy(); p["ini"] = pd.to_datetime(p.start_date); p["fim"] = pd.to_datetime(p.end_date)
p = p.sort_values(["account_id", "ini"]).reset_index(drop=True)
e = p[p.fim.notna()].sort_values(["fim", "subscription_id"]).reset_index(drop=True)
# conferência independente em Python (mesma regra das fórmulas, janela padrão −30/+60)
def nova(x, antes=30, depois=60):
    o = p[(p.account_id == x.account_id) & (p.subscription_id != x.subscription_id) & (p.ini >= x.fim - pd.Timedelta(days=antes)) & (p.ini <= x.fim + pd.Timedelta(days=depois))]
    return int(len(o) > 0)
e["py"] = e.apply(nova, axis=1)
REF = pd.Timestamp("2024-12-31"); el = e[e.fim <= REF - pd.Timedelta(days=60)]
print("Python, janela −30/+60:", el.groupby(["billing_frequency", "auto_renew_flag"]).py.mean().round(3).to_dict(), "total", round(el.py.mean(), 3), "n", len(el))
el2 = e[e.fim <= REF - pd.Timedelta(days=60)].copy(); el2["py0"] = el2.apply(lambda x: nova(x, 0, 60), axis=1)
print("Python, janela 0/+60 (só assinaturas que começam DEPOIS do fim):", round(el2.py0.mean(), 3))

F, B = "Arial", Font(name="Arial", bold=True)
N = Font(name="Arial"); IN = Font(name="Arial", color="0000FF"); LK = Font(name="Arial", color="008000")
Y = PatternFill("solid", fgColor="FFFF00"); H = PatternFill("solid", fgColor="D9E2F3")
DT, PCT, USD = "dd/mm/yyyy", "0.0%", "$#,##0"
wb = Workbook()

# ---------- Leia-me
ws = wb.active; ws.title = "Leia-me"
txt = [
 ("O que esta planilha prova", True),
 ("Quando uma assinatura paga termina, quantas vezes a mesma conta tem outra assinatura paga começando perto dessa data.", False),
 ("", False),
 ("Regra (a mesma das fórmulas da aba Encerradas)", True),
 ("1. Universo: assinaturas pagas (is_trial = False) com end_date preenchido. Fonte: ravenstack_subscriptions.csv.", False),
 ("2. 'Teve nova assinatura' = existe outra assinatura paga da MESMA conta cujo start_date cai entre [fim − dias antes] e [fim + dias depois].", False),
 ("3. Só entram na taxa as assinaturas que terminaram até a data de corte (último dia da base, 31/12/2024, menos 'dias depois'), para todas terem a janela inteira observável.", False),
 ("", False),
 ("Como mexer", True),
 ("Células amarelas na aba Resumo são parâmetros: mude 'dias antes' e 'dias depois' e todas as taxas recalculam.", False),
 ("Teste sugerido: dias antes = 0 conta só assinaturas que começam DEPOIS do fim (nova compra em sentido estrito).", False),
 ("", False),
 ("Conferência", True),
 ("A coluna 'Python conferiu' em Encerradas foi calculada fora da planilha (script 13_planilha_renovacao.py) com a janela padrão −30/+60.", False),
 ("A célula 'Divergências fórmula × Python' no Resumo deve dar 0 com os parâmetros padrão.", False),
 ("", False),
 ("Ressalvas (importantes)", True),
 ("• A base permite várias assinaturas ativas ao mesmo tempo na mesma conta. A coluna 'Outra ativa no fim' mostra isso: uma nova assinatura perto do fim não prova, sozinha, que foi uma renovação daquela.", False),
 ("• A base é sintética (gerada em Python pelo autor do dataset). As assinaturas 'anuais' duram 34 dias na mediana, então não existe um vencimento anual real para observar.", False),
 ("• Cores: azul = parâmetro digitado; verde = valor puxado de outra aba; preto = fórmula.", False),
]
for i, (t, b) in enumerate(txt, 1):
    c = ws.cell(i, 1, t); c.font = B if b else N; c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 120

# ---------- Pagas (dados brutos)
wp = wb.create_sheet("Pagas")
hp = ["subscription_id", "account_id", "start_date", "end_date", "billing_frequency", "auto_renew_flag", "mrr_amount"]
for j, h in enumerate(hp, 1):
    c = wp.cell(1, j, h); c.font = B; c.fill = H
for i, x in enumerate(p.itertuples(), 2):
    vals = [x.subscription_id, x.account_id, x.ini.to_pydatetime(), None if pd.isna(x.fim) else x.fim.to_pydatetime(), x.billing_frequency, bool(x.auto_renew_flag), int(x.mrr_amount)]
    for j, v in enumerate(vals, 1):
        c = wp.cell(i, j, v); c.font = N
        if j in (3, 4): c.number_format = DT
        if j == 7: c.number_format = USD
NP = len(p) + 1
for col, w in zip("ABCDEFG", [16, 12, 12, 12, 17, 15, 12]): wp.column_dimensions[col].width = w
wp.freeze_panes = "A2"; wp.auto_filter.ref = f"A1:G{NP}"
R = lambda col: f"Pagas!${col}$2:${col}${NP}"

# ---------- Resumo (parâmetros + taxas)
wr = wb.create_sheet("Resumo", 1)
wr["A1"] = "Nova assinatura paga após o fim de uma assinatura paga"; wr["A1"].font = Font(name=F, bold=True, size=13)
wr["A3"] = "Parâmetros"; wr["A3"].font = B
wr["A4"] = "Dias antes do fim (janela começa em)"; wr["B4"] = 30
wr["A5"] = "Dias depois do fim (janela termina em)"; wr["B5"] = 60
wr["A6"] = "Último dia da base"; wr["B6"] = REF.to_pydatetime(); wr["B6"].number_format = DT
wr["A7"] = "Data de corte (fim máximo elegível)"; wr["B7"] = "=B6-B5"; wr["B7"].number_format = DT
for c in ("B4", "B5", "B6"): wr[c].font = IN; wr[c].fill = Y
wr["B6"].comment = Comment("Maior data observada na base (31/12/2024). Fonte: ravenstack_subscriptions.csv / churn_events.csv.", "verificacao")
for r in range(4, 8): wr[f"A{r}"].font = N
wr["B7"].font = N
hdr = ["Frequência", "Auto-renew", "Encerradas elegíveis", "Com nova assinatura", "Taxa", "Com outra já ativa no fim", "% com outra já ativa"]
for j, h in enumerate(hdr, 1):
    c = wr.cell(9, j, h); c.font = B; c.fill = H; c.alignment = Alignment(wrap_text=True)
NE = len(e) + 1
E = lambda col: f"Encerradas!${col}$2:${col}${NE}"
grupos = [("annual", False), ("annual", True), ("monthly", False), ("monthly", True)]
for i, (fq, ar) in enumerate(grupos, 10):
    wr.cell(i, 1, fq).font = N; wr.cell(i, 2, ar).font = N
    crit = f'{E("F")},$A{i},{E("G")},$B{i},{E("I")},1'
    wr.cell(i, 3, f"=COUNTIFS({crit})"); wr.cell(i, 4, f"=COUNTIFS({crit},{E('K')},1)")
    wr.cell(i, 5, f"=IF(C{i}=0,0,D{i}/C{i})"); wr.cell(i, 6, f"=COUNTIFS({crit},{E('M')},\">0\")"); wr.cell(i, 7, f"=IF(C{i}=0,0,F{i}/C{i})")
wr.cell(14, 1, "Total").font = B
for col in "CDF": wr[f"{col}14"] = f"=SUM({col}10:{col}13)"
wr["E14"] = "=IF(C14=0,0,D14/C14)"; wr["G14"] = "=IF(C14=0,0,F14/C14)"
for r in range(10, 15):
    for col in "CDF": wr[f"{col}{r}"].font = B if r == 14 else N
    for col in "EG": wr[f"{col}{r}"].number_format = PCT; wr[f"{col}{r}"].font = B if r == 14 else N
wr["A16"] = "Menor taxa entre os 4 grupos"; wr["B16"] = "=MIN(E10:E13)"
wr["A17"] = "Maior taxa entre os 4 grupos"; wr["B17"] = "=MAX(E10:E13)"
wr["A19"] = "Divergências fórmula × Python (deve ser 0 com 30/60)"; wr["B19"] = f"=IF(AND(B4=30,B5=60),SUMPRODUCT(({E('I')}=1)*({E('K')}<>{E('L')})),\"parâmetros alterados\")"
for c in ("B16", "B17"): wr[c].number_format = PCT
for r in (16, 17, 19): wr[f"A{r}"].font = N; wr[f"B{r}"].font = B
wr.column_dimensions["A"].width = 44
for col in "BCDEFG": wr.column_dimensions[col].width = 16

# ---------- Encerradas (uma linha por assinatura encerrada, com a fórmula)
we = wb.create_sheet("Encerradas", 2)
he = ["subscription_id", "account_id", "country", "start_date", "end_date", "billing_frequency", "auto_renew_flag", "mrr_amount",
      "Elegível (fim ≤ corte)", "Início da 1ª nova assinatura na janela", "Teve nova assinatura", "Python conferiu", "Outra já ativa no fim", "Dias entre fim e nova"]
for j, h in enumerate(he, 1):
    c = we.cell(1, j, h); c.font = B; c.fill = H; c.alignment = Alignment(wrap_text=True)
for i, x in enumerate(e.itertuples(), 2):
    vals = [x.subscription_id, x.account_id, a.country.get(x.account_id), x.ini.to_pydatetime(), x.fim.to_pydatetime(), x.billing_frequency, bool(x.auto_renew_flag), int(x.mrr_amount)]
    for j, v in enumerate(vals, 1):
        c = we.cell(i, j, v); c.font = N
        if j in (4, 5): c.number_format = DT
        if j == 8: c.number_format = USD
    we.cell(i, 9, f"=IF(E{i}<=Resumo!$B$7,1,0)").font = N
    we.cell(i, 10, f'=_xlfn.MINIFS({R("C")},{R("B")},B{i},{R("A")},"<>"&A{i},{R("C")},">="&(E{i}-Resumo!$B$4),{R("C")},"<="&(E{i}+Resumo!$B$5))').font = LK
    we.cell(i, 10).number_format = 'dd/mm/yyyy;;"—"'
    we.cell(i, 11, f"=IF(J{i}>0,1,0)").font = N
    we.cell(i, 12, int(x.py)).font = IN
    we.cell(i, 13, f'=COUNTIFS({R("B")},B{i},{R("A")},"<>"&A{i},{R("C")},"<"&E{i},{R("D")},"")+COUNTIFS({R("B")},B{i},{R("A")},"<>"&A{i},{R("C")},"<"&E{i},{R("D")},">="&E{i})').font = LK
    we.cell(i, 14, f'=IF(J{i}>0,J{i}-E{i},"")').font = N
we["L1"].comment = Comment("Calculado em Python (13_planilha_renovacao.py), janela −30/+60. Serve de conferência independente das fórmulas.", "verificacao")
we["M1"].comment = Comment("Quantas outras assinaturas pagas da mesma conta já tinham começado antes deste fim e ainda estavam ativas nele.", "verificacao")
for col, w in zip("ABCDEFGHIJKLMN", [16, 12, 9, 12, 12, 16, 14, 12, 12, 16, 12, 12, 12, 12]): we.column_dimensions[col].width = w
we.freeze_panes = "C2"; we.auto_filter.ref = f"A1:N{NE}"
from openpyxl.workbook.properties import CalcProperties; wb.calculation = CalcProperties(fullCalcOnLoad=True)
wb.save(OUT); print("salvo", OUT, "| pagas", len(p), "| encerradas", len(e))
