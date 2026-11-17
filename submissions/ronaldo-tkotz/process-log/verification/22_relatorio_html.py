"""22 — Gera a versão em página (HTML) do relatório, a partir do Markdown (D52).

Uso: uv run --with markdown python -I 22_relatorio_html.py [caminho_do_banco]
Lê ../../solution/relatorio-churn.md e o banco (padrão: ../../solution/app/data/ravenstack.db).
Escreve ../../solution/relatorio-churn.html: um arquivo só, sem dependência externa além das fontes,
com os números do topo e os dois gráficos calculados do banco, e o Markdown original embutido
no botão "Baixar o relatório (.md)".
"""
import html, json, os, re, sqlite3, sys

import markdown

AQUI = os.path.dirname(os.path.abspath(__file__))
SOL = os.path.join(AQUI, "..", "..", "solution")
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SOL, "app", "data", "ravenstack.db")
MD_PATH = os.path.join(SOL, "relatorio-churn.md")
OUT = os.path.join(SOL, "relatorio-churn.html")

c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()
br = lambda x, d=1: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------------------------------------------------------- números do topo (do banco)
contas, churn = q("select count(*), sum(churn_flag) from accounts")[0]
mrr_duvida = q("""select sum(s.mrr_amount) from subscriptions s join accounts a using(account_id)
                  where a.churn_flag=1 and s.end_date is null and s.is_trial=0""")[0][0]
setores = q("select industry, count(*), sum(churn_flag) from accounts group by 1 order by 1.0*sum(churn_flag)/count(*) desc")
dev = next(s for s in setores if s[0] == "DevTools")
resto = (sum(s[1] for s in setores if s[0] != "DevTools"), sum(s[2] for s in setores if s[0] != "DevTools"))
lista = list(__import__("csv").DictReader(open(os.path.join(SOL, "contas-em-risco.csv"), encoding="utf-8")))
lista_a = [r for r in lista if r["lista"].startswith("A")]
mrr_a = sum(int(r["mrr_ativo"]) for r in lista_a)

# soma de sinais × churn_flag para as 500 contas, com a mesma regra do 21 (sem o evento de 90 dias).
# O CSV só tem as contas da fila, então o 21 roda de novo aqui (saída silenciada; o CSV que ele
# reescreve sai idêntico, porque a regra é determinística).
import contextlib, io, runpy
argv0 = sys.argv
sys.argv = [os.path.join(AQUI, "21_sinais_e_contas.py"), DB]
with contextlib.redirect_stdout(io.StringIO()):
    ns21 = runpy.run_path(sys.argv[0], run_name="sinais")
sys.argv = argv0
gradiente = []
for k in range(0, 5):
    g = [a for a in ns21["contas"].values() if min(4, a["n_sinais"] - a["evento_90d"]) == k]
    gradiente.append((k, len(g), sum(a["churn_flag"] for a in g)))
media = churn / contas


# ---------------------------------------------------------------- gráficos (SVG, cores pelos tokens do tema)
def barras_setor():
    w, h, esq, dir_, lin = 560, 232, 112, 120, 34
    maxv = 0.35
    x = lambda v: esq + (w - esq - dir_) * v / maxv
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="g1t"><title id="g1t">Taxa de churn por setor: '
           + "; ".join(f"{s[0]} {br(100*s[2]/s[1])}%" for s in setores) + "</title>"]
    for v in (0, 0.1, 0.2, 0.3):
        out.append(f'<line class="grade" x1="{x(v):.1f}" x2="{x(v):.1f}" y1="8" y2="{h-44}"/>'
                   f'<text class="eixo" x="{x(v):.1f}" y="{h-28}" text-anchor="middle">{int(v*100)}%</text>')
    out.append(f'<line class="media" x1="{x(media):.1f}" x2="{x(media):.1f}" y1="6" y2="{h-44}"/>'
               f'<text class="eixo forte" x="{x(media):.1f}" y="{h-8}" text-anchor="middle">média da base: {br(100*media,0)}%</text>')
    for i, (nome, n, ch) in enumerate(setores):
        y = 14 + i * lin
        t = ch / n
        cls = "barra destaque" if nome == "DevTools" else "barra"
        out.append(f'<text class="rot" x="{esq-10}" y="{y+15}" text-anchor="end">{nome}</text>'
                   f'<rect class="{cls}" x="{esq}" y="{y}" width="{x(t)-esq:.1f}" height="22" rx="3"/>'
                   f'<text class="val" x="{x(t)+8:.1f}" y="{y+15}">{br(100*t)}% · {ch} de {n}</text>')
    out.append("</svg>")
    return "".join(out)


def colunas_sinais():
    w, h, base, topo, esq = 560, 214, 172, 18, 40
    maxv = 0.45
    y = lambda v: base - (base - topo) * v / maxv
    banda = (w - esq - 10) / len(gradiente)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="g2t"><title id="g2t">Taxa de churn pela quantidade de sinais da conta: '
           + "; ".join(f"{k} sinais {br(100*ch/n)}% ({n} contas)" for k, n, ch in gradiente) + "</title>"]
    for v in (0, 0.1, 0.2, 0.3, 0.4):
        out.append(f'<line class="grade" x1="{esq}" x2="{w-10}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>'
                   f'<text class="eixo" x="{esq-6}" y="{y(v)+4:.1f}" text-anchor="end">{int(v*100)}%</text>')
    for i, (k, n, ch) in enumerate(gradiente):
        t = ch / n
        cx = esq + banda * i + banda / 2
        cls = "barra destaque" if k == 4 else "barra"
        out.append(f'<rect class="{cls}" x="{cx-30:.1f}" y="{y(t):.1f}" width="60" height="{base-y(t):.1f}" rx="3"/>'
                   f'<text class="val" x="{cx:.1f}" y="{y(t)-7:.1f}" text-anchor="middle">{br(100*t)}%</text>'
                   f'<text class="rot" x="{cx:.1f}" y="{base+17}" text-anchor="middle">{k if k < 4 else "4+"} {"sinal" if k == 1 else "sinais"}</text>'
                   f'<text class="eixo" x="{cx:.1f}" y="{base+33}" text-anchor="middle">{n} contas</text>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- Markdown → HTML
md_src = open(MD_PATH, encoding="utf-8").read()
cabeca, corpo = md_src.split("\n---\n", 1)
titulo = re.search(r"^# (.+)$", cabeca, re.M).group(1)
meta = [l for l in cabeca.splitlines()[1:] if l.strip()]


def md(t):
    t = re.sub(r"^( {2,3})(?=\S)", "    ", t, flags=re.M)  # listas aninhadas com 2–3 espaços → 4
    t = re.sub(r"(?<![(<`\[])(https://[^\s)<]+)", r"<\1>", t)
    h = markdown.markdown(t, extensions=["tables", "sane_lists"])
    h = h.replace("<table>", '<div class="tabela"><table>').replace("</table>", "</table></div>")
    return h


def ancora(m):
    texto = re.sub(r"<[^>]+>", "", m.group(2))
    slug = re.sub(r"[^a-z0-9]+", "-", texto.lower().translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))).strip("-")
    return f'<h{m.group(1)} id="sec-{slug}">{m.group(2)}</h{m.group(1)}>'


corpo_html = re.sub(r"<h([23])>(.*?)</h\1>", ancora, md(corpo))
secoes = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', corpo_html)
nav = "".join(f'<a href="#{s}">{re.sub(r"<[^>]+>", "", t)}</a>' for s, t in secoes)
meta_html = "".join(f"<p>{markdown.markdown(l)[3:-4]}</p>" for l in meta)

kpis = [
    (f"{br(100*churn/contas,0)}%", f"das contas com churn ({churn} de {contas})"),
    (f"US$ {br(mrr_duvida/1e6,2)} mi", f"de MRR em contas que o CRM diz canceladas e o faturamento ainda cobra"),
    (f"{br(100*dev[2]/dev[1],0)}% × {br(100*resto[1]/resto[0],0)}%", "churn em DevTools contra o resto da base, o único corte significativo"),
    (f"{len(lista_a)} contas", f"com 3 sinais ou mais, somando US$ {br(mrr_a/1e6,2)} mi de MRR: a fila do CS"),
]
kpi_html = "".join(f'<div class="kpi"><strong>{v}</strong><span>{html.escape(d)}</span></div>' for v, d in kpis)

pagina = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diagnóstico de churn da RavenStack</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  /* Relatório de diagnóstico: papel claro, tinta azul-ardósia; laranja = churn (o problema), azul = base/receita. Coluna de leitura única, gráficos e números antes do texto. */
  --papel: #f5f6f8; --folha: #ffffff; --tinta: #1b2331; --suave: #566173; --linha: #dde2ea;
  --churn: #c24d1c; --churn-fundo: #fbeee7; --base: #9aa6b8; --azul: #2c64c4;
  --f-titulo: "IBM Plex Serif", Georgia, serif; --f-texto: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif; --f-mono: "IBM Plex Mono", ui-monospace, monospace;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --papel: #11151c; --folha: #181d26; --tinta: #e6e9ef; --suave: #9ba5b5; --linha: #2a313d;
    --churn: #ee7a45; --churn-fundo: #2c1d16; --base: #5b6678; --azul: #6d9ef0; color-scheme: dark;
  }}
}}
:root[data-theme="dark"] {{
  --papel: #11151c; --folha: #181d26; --tinta: #e6e9ef; --suave: #9ba5b5; --linha: #2a313d;
  --churn: #ee7a45; --churn-fundo: #2c1d16; --base: #5b6678; --azul: #6d9ef0; color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
body {{ background: var(--papel); color: var(--tinta); font: 16px/1.6 var(--f-texto); }}
.topo {{ background: var(--folha); border-bottom: 1px solid var(--linha); }}
.faixa {{ max-width: 1080px; margin: 0 auto; padding: 28px 24px 22px; display: grid; gap: 14px; }}
.linha-topo {{ display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-start; justify-content: space-between; }}
h1 {{ font: 600 2.1rem/1.15 var(--f-titulo); margin: 0; text-wrap: balance; }}
.meta {{ color: var(--suave); font-size: .9rem; display: grid; gap: 4px; max-width: 78ch; }}
.meta p {{ margin: 0; }}
.acoes {{ display: grid; gap: 6px; justify-items: end; }}
button {{ font: 600 .95rem var(--f-texto); color: #fff; background: var(--churn); border: 0; border-radius: 6px; padding: 10px 16px; cursor: pointer; }}
button:hover {{ filter: brightness(1.08); }}
button:focus-visible, a:focus-visible {{ outline: 3px solid var(--azul); outline-offset: 2px; }}
#aviso {{ font-size: .8rem; color: var(--suave); min-height: 1.2em; }}
nav {{ display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: .88rem; }}
nav a {{ color: var(--suave); text-decoration: none; border-bottom: 1px solid var(--linha); }}
nav a:hover {{ color: var(--tinta); border-color: var(--churn); }}
main {{ max-width: 1080px; margin: 0 auto; padding: 24px; display: grid; gap: 24px; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
.kpi {{ background: var(--folha); border: 1px solid var(--linha); border-top: 3px solid var(--churn); border-radius: 6px; padding: 14px 16px; display: grid; gap: 4px; }}
.kpi strong {{ font: 600 1.6rem/1.1 var(--f-titulo); font-variant-numeric: tabular-nums; }}
.kpi span {{ color: var(--suave); font-size: .86rem; line-height: 1.4; }}
.graficos {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }}
figure {{ margin: 0; background: var(--folha); border: 1px solid var(--linha); border-radius: 6px; padding: 16px; display: grid; gap: 8px; }}
figcaption {{ display: grid; gap: 2px; }}
figcaption b {{ font-weight: 600; }}
figcaption span {{ color: var(--suave); font-size: .85rem; }}
svg {{ width: 100%; height: auto; display: block; }}
svg text {{ font-family: var(--f-texto); font-size: 13px; fill: var(--tinta); font-variant-numeric: tabular-nums; }}
svg .eixo {{ fill: var(--suave); font-size: 11.5px; }}
svg .forte {{ fill: var(--tinta); font-weight: 600; }}
svg .val {{ font-weight: 600; paint-order: stroke; stroke: var(--folha); stroke-width: 4px; stroke-linejoin: round; }}
svg .grade {{ stroke: var(--linha); }}
svg .media {{ stroke: var(--tinta); stroke-dasharray: 4 4; opacity: .6; }}
svg .barra {{ fill: var(--base); }}
svg .destaque {{ fill: var(--churn); }}
article {{ background: var(--folha); border: 1px solid var(--linha); border-radius: 6px; padding: 8px clamp(18px, 4vw, 48px) 32px; }}
article > * {{ max-width: 74ch; }}
article > .tabela {{ max-width: none; }}
article h2 {{ font: 600 1.55rem/1.25 var(--f-titulo); margin: 2.2rem 0 .6rem; padding-top: 1.2rem; border-top: 1px solid var(--linha); text-wrap: balance; }}
article h2:first-child {{ border-top: 0; margin-top: 1rem; }}
article h3 {{ font: 600 1.15rem/1.3 var(--f-texto); margin: 1.8rem 0 .4rem; }}
article p, article li {{ margin: .45rem 0; }}
article ul, article ol {{ padding-left: 1.4rem; }}
article strong {{ font-weight: 600; }}
article code {{ font: .86em var(--f-mono); background: var(--papel); border: 1px solid var(--linha); border-radius: 4px; padding: 0 4px; }}
article a {{ color: var(--azul); }}
article hr {{ display: none; }}
.tabela {{ overflow-x: auto; margin: 1rem 0; border: 1px solid var(--linha); border-radius: 6px; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; font-variant-numeric: tabular-nums; }}
th {{ text-align: left; font-weight: 600; background: var(--papel); }}
th, td {{ padding: 8px 12px; border-bottom: 1px solid var(--linha); vertical-align: top; }}
tr:last-child td {{ border-bottom: 0; }}
td strong {{ color: var(--churn); }}
footer {{ max-width: 1080px; margin: 0 auto; padding: 0 24px 40px; color: var(--suave); font-size: .82rem; }}
@media (max-width: 520px) {{ h1 {{ font-size: 1.6rem; }} .acoes {{ justify-items: start; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
</head>
<body>
<header class="topo">
  <div class="faixa">
    <div class="linha-topo">
      <div>
        <h1>{html.escape(titulo)}</h1>
      </div>
      <div class="acoes">
        <button type="button" id="baixar">Baixar o relatório (.md)</button>
        <span id="aviso" role="status" aria-live="polite"></span>
      </div>
    </div>
    <div class="meta">{meta_html}</div>
    <nav aria-label="Seções do relatório">{nav}</nav>
  </div>
</header>
<main>
  <section class="kpis" aria-label="Números principais">{kpi_html}</section>
  <section class="graficos" aria-label="Gráficos">
    <figure>
      <figcaption><b>Churn por setor</b><span>% das contas de cada setor com <code>churn_flag</code>; a linha tracejada é a média da base</span></figcaption>
      {barras_setor()}
    </figure>
    <figure>
      <figcaption><b>Churn pela quantidade de sinais da conta</b><span>sinais observáveis somados (sem o churn recente); a última coluna tem só {gradiente[-1][1]} contas</span></figcaption>
      {colunas_sinais()}
    </figure>
  </section>
  <article>
{corpo_html}
  </article>
</main>
<footer>Gerado por <code>process-log/verification/22_relatorio_html.py</code> a partir de <code>solution/relatorio-churn.md</code> e do banco <code>solution/app/data/ravenstack.db</code>.</footer>
<script>
const MD = {json.dumps(md_src, ensure_ascii=False).replace("</", "<\\/")};
const NOME = "relatorio-churn.md";
const aviso = document.getElementById("aviso");
function baixarPeloNavegador() {{
  const url = URL.createObjectURL(new Blob([MD], {{ type: "text/markdown;charset=utf-8" }}));
  const a = document.createElement("a");
  a.href = url; a.download = NOME; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}}
document.getElementById("baixar").addEventListener("click", async () => {{
  aviso.textContent = "";
  const temClaude = window.claude && typeof window.claude.use === "function";
  if (!temClaude) {{ baixarPeloNavegador(); return; }}
  try {{
    const downloads = await window.claude.use("downloads");
    if (!downloads) {{ baixarPeloNavegador(); return; }}
    await downloads.save({{ filename: NOME, data: MD }});
    aviso.textContent = "Arquivo salvo.";
  }} catch (e) {{
    const code = e && e.code;
    if (code === "declined") aviso.textContent = "Download cancelado.";
    else if (code === "rate_limited") aviso.textContent = "Já há um pedido de download aberto. Tente de novo em instantes.";
    else baixarPeloNavegador();
  }}
}});
</script>
</body>
</html>
"""
open(OUT, "w", encoding="utf-8").write(pagina)
print(f"{os.path.relpath(OUT, AQUI)}: {len(pagina):,} bytes; seções: {[re.sub(r'<[^>]+>', '', t) for _, t in secoes]}")
print("gradiente:", gradiente)
