"""Gera os exemplos de saída desta pasta a partir dos CSVs e do código da solução.

Uso: python gerar.py   (de dentro de docs/exemplos, depois de instalar solution/requirements.txt)
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "solution"))
import backtest  # noqa: E402
import scoring  # noqa: E402

deals = scoring.load_pipeline()
today = scoring.reference_date(deals)
scored, _ = scoring.score_open_deals(deals, today)
labels = {"foco": "Ligar", "abordar": "Primeiro contato", "reativar": "Reativar por mensagem", "encerrar": "Encerrar"}
bands = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
money = lambda value: f"${int(round(value)):,}".replace(",", ".")  # noqa: E731
pct = lambda a, b: f"{(a / b - 1) * 100:+.0f}%".replace("-", "−")  # noqa: E731

columns = ["opportunity_id", "sales_agent", "regional_office", "account", "product", "sales_price", "deal_stage", "age", "lista", "faixa", "score"]
scored.sort_values(["lista", "valor_esperado", "sales_price"], ascending=[True, False, False])[columns].to_csv(
    HERE / "todas-as-negociacoes-abertas.csv", index=False, encoding="utf-8")


def queue(agent, n=4):
    """As duas partes da tela Hoje, como em `todayParts` (app/app.js), antes de qualquer registro de contato."""
    mine = scored[scored["sales_agent"] == agent]
    goal = mine[mine["lista"] == "foco"].sort_values(["valor_esperado", "sales_price", "opportunity_id"], ascending=[False, False, True])
    extra = pd.concat([
        mine[mine["lista"] == "abordar"].sort_values(["sales_price", "opportunity_id"], ascending=[False, True]),
        mine[mine["lista"] == "reativar"].sort_values(["sales_price", "age"], ascending=[False, True]),
    ])
    extra = pd.concat([extra[extra["account"].notna()], extra[extra["account"].isna()]])  # empresa cadastrada primeiro

    def table(part, start):
        rows = ["| # | Empresa | Produto | Valor | Idade | O que fazer | Chance | Score |", "|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(part.head(n).itertuples(), start):
            age = "não iniciada" if pd.isna(r.age) else f"{int(r.age)} dias"
            chance = bands.get(r.faixa, "Desconhecida" if r.lista == "abordar" else "Nenhuma")
            rows.append(f"| {i} | {r.account if isinstance(r.account, str) else 'Não informada'} | {r.product} | {money(r.sales_price)} | "
                        f"{age} | {labels[r.lista]} | {chance} | {r.score if r.lista == 'foco' else '–'} |")
        return "\n".join(rows)

    counts = mine["lista"].value_counts()
    summary = ", ".join(f"{counts.get(k, 0)} {v.lower()}" for k, v in labels.items())
    text = f"### {agent} ({mine['regional_office'].iloc[0]})\n\nCarteira aberta: {len(mine)} negociações ({summary}).\n\n"
    text += (f"**Meta do dia: {len(goal)} prioridades.** As {min(n, len(goal))} primeiras:\n\n{table(goal, 1)}\n\n" if len(goal)
             else "**Nenhuma prioridade hoje:** nenhuma negociação com chance de fechar.\n\n")
    if len(extra):
        title = "Se sobrar tempo" if len(goal) else "Para abrir conversa"
        text += f"**{title}: {len(extra)} negociações.** As {min(n, len(extra))} primeiras:\n\n{table(extra, len(goal) + 1)}\n"
    return text


result = backtest.run_backtest(deals)
weeks = pd.DataFrame(result["semanas"])
weeks.to_csv(HERE / "teste-historico-por-semana.csv", index=False, encoding="utf-8")
counts = scored["lista"].value_counts()
soon = result["esteMes"]

lines = [
    "# Exemplos de saída\n",
    "Gerados por `gerar.py` a partir dos CSVs originais e do código em `solution/`, com a data do CRM em",
    "31/12/2017. Servem para conferir se a lógica se comporta como descrito, sem precisar abrir a tela.\n",
    f"## Como as {len(scored):,} negociações abertas foram classificadas\n".replace(",", "."),
    "| Lista | Negociações | O que o vendedor faz |\n|---|---|---|",
]
for key, text in [("foco", "Liga, na ordem de preço × chance"), ("abordar", "Primeiro contato, na ordem do preço (chance desconhecida)"),
                  ("reativar", "Uma mensagem com condição especial"), ("encerrar", "Encerra no CRM")]:
    lines.append(f"| {labels[key]} | {counts[key]:,} | {text} |".replace(",", "."))
lines += [
    "\nA lista completa, uma linha por negociação, está em `todas-as-negociacoes-abertas.csv`.\n",
    "## A fila de três vendedores em situações diferentes\n",
    'O que cada um vê em "Hoje", que tem duas partes: em cima a meta do dia (negociações com chance, na ordem',
    'preço × chance) e, embaixo, "se sobrar tempo" (primeiro contato e reativação, com as que têm empresa',
    "cadastrada primeiro). As quatro primeiras linhas de cada parte.\n",
    queue("Kary Hendrixson"), queue("Cassey Cress"), queue("Darcel Schlecht"),
    "Darcel é do escritório Central, que não tem nenhuma negociação com chance de fechar: a tela dele mostra",
    "só o bloco de baixo, e a ferramenta não consegue priorizar além de pôr primeiro as que têm empresa.\n",
    "## O teste histórico\n",
    f"{len(weeks)} semanas, de {weeks['data'].iloc[0]} a {weeks['data'].iloc[-1]}. Receita gerada depois pelas {result['topN']} primeiras",
    "negociações de cada vendedor, em cada método. As regras de comparação têm muitos empates de preço e são",
    "desempatadas por sorteio. O detalhe por semana está em `teste-historico-por-semana.csv`.\n",
    f"| Período | Esta ferramenta | Preço, até {result['regraSimplesDias']} dias | Preço, até {result['regraSimplesDias']} dias, a mais nova primeiro | Preço, entre as que a ferramenta mantém | Só preço | Ao acaso |",
    "|---|---|---|---|---|---|---|",
]
for r in result["resumo"]:
    lines.append(f"| {r['trimestre']} | {money(r['ferramenta'])} | {money(r['precoRecentes'])} | {money(r['precoRecentesNova'])} | "
                 f"{money(r['precoVivas'])} | {money(r['soPreco'])} | {money(r['acaso'])} |")
lines += ["", "Diferença da ferramenta para cada método:\n",
          "| Período | Preço, até 90 dias | Semanas em que ganhou | A mais nova primeiro | Semanas | Entre as que mantém | Semanas | Sem recontagem (só os 7 dias seguintes) |",
          "|---|---|---|---|---|---|---|---|"]
for r in result["resumo"]:
    lines.append(f"| {r['trimestre']} | {pct(r['ferramenta'], r['precoRecentes'])} | {r['semanasGanhas']} de {r['semanas']} | "
                 f"{pct(r['ferramenta'], r['precoRecentesNova'])} | {r['semanasGanhasNova']} de {r['semanas']} | "
                 f"{pct(r['ferramenta'], r['precoVivas'])} | {r['semanasGanhasVivas']} de {r['semanas']} | {pct(r['ferramenta7'], r['precoRecentes7'])} |")
lines += ["", "Trocando o corte de idade da regra simples (vantagem da ferramenta, em %):\n",
          "| Corte | " + " | ".join(k for k in result["sensibilidade"][0] if k != "dias") + " |", "|---|---|---|"]
for row in result["sensibilidade"]:
    lines.append(f"| {row['dias']} dias | " + " | ".join(f"{v:+.1f}".replace(".", ",").replace("-", "−") for k, v in row.items() if k != "dias") + " |")
lines += [
    f"\nNegociações tiradas da lista de ligação ao longo do teste: {result['parados']['distintos']} diferentes. "
    f"Ganhas depois: {result['parados']['ganhos']}. Encerradas como perdidas: {result['parados']['perdidos']}.\n",
    "| Faixa de chance | Observações no teste (negociação × semana) | Ganhas depois |\n|---|---|---|",
]
for b in result["faixas"]:
    lines.append(f"| {bands[b['faixa']]} | {b['deals']:,} | ".replace(",", ".") + f"{b['ganhos'] * 100:.1f}%".replace(".", ",") + " |")
lines += [
    f"\n\"Pode fechar este mês\": as marcadas foram ganhas em 30 dias em {soon['ganhosMarcados'] * 100:.1f}% dos casos; "
    f"as não marcadas que ainda tinham chance, em {soon['ganhosNaoMarcadosVivas'] * 100:.1f}%.\n".replace(".", ",").replace("casos;", "casos;"),
    "Para reproduzir: `python backtest.py` dentro de `solution/`.",
]
(HERE / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("ok:", sorted(p.name for p in HERE.iterdir()))
