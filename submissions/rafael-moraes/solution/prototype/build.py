"""Monta index.html (arquivo único, roda offline) a partir de src/ e dos JSON gerados pela análise.
Uso: python build.py   (depois de 05_exportar_modelo.py e de gerar health_ds1.json)
"""
from pathlib import Path
here = Path(__file__).parent
html = (here / "src/template.html").read_text(encoding="utf-8")
for key, path in {"/*__GLOSSARY__*/": "src/glossary_pt.js", "/*__ENGINE__*/": "src/engine.js", "/*__HEALTH__*/": "src/health.js", "/*__MODEL__*/": "model.json",
                  "/*__EVAL__*/": "eval.json", "/*__QUEUE__*/": "queue_sample.json", "/*__HEALTH_DS1__*/": "health_ds1.json"}.items():
    html = html.replace(key, (here / path).read_text(encoding="utf-8"))
(here / "index.html").write_text(html, encoding="utf-8")
print("index.html:", round((here / "index.html").stat().st_size / 1e6, 2), "MB")
