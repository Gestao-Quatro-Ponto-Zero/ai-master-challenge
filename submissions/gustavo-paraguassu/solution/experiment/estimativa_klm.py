"""ESTIMATIVA (não medição) do tempo de atendimento COM e SEM assistente, pelo modelo KLM.

KLM (Keystroke-Level Model, Card, Moran & Newell, 1980) estima o tempo de uma tarefa de tela
somando tempos-padrão de cada operação: ler, decidir, apontar/tocar, digitar. Serve para prever
antes de testar com pessoas; NÃO mede viés de automação nem acerto humano de fila. O teste com
pessoas não foi feito (ver process-log D12): este número é um piso de ordem de grandeza.

Roda sobre os 160 chamados em português de 05_pt_eval.py, com o card exatamente como o bot mostra
(resumo, campos, resposta pronta), vindo do cache: não precisa de chave.
Uso (de dentro de solution/): python experiment/estimativa_klm.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402
from app.engine import Motor  # noqa: E402

# Operadores KLM (s). Valores clássicos; faixa = digitador bom / médio / lento (celular).
OP = {
    "K": {"baixo": 0.20, "base": 0.28, "alto": 0.50},      # por caractere digitado
    "P": {"baixo": 1.10, "base": 1.10, "alto": 1.10},      # apontar/tocar um alvo
    "B": {"baixo": 0.10, "base": 0.10, "alto": 0.10},      # clicar
    "M": {"baixo": 1.35, "base": 1.35, "alto": 1.35},      # preparação mental (decidir)
    "leitura_wpm": {"baixo": 250, "base": 200, "alto": 150},
}
# Parâmetros de comportamento (premissas, não KLM)
PAR = {
    "chars_resposta_digitada": {"baixo": 60, "base": 120, "alto": 200},   # SEM: escreve do zero
    "pct_edita_rascunho": {"baixo": 0.10, "base": 0.20, "alto": 0.40},    # COM: ajusta a pronta
    "chars_edicao": {"baixo": 20, "base": 40, "alto": 80},
    "fracao_le_mensagem_com": {"baixo": 0.3, "base": 0.5, "alto": 1.0},   # COM: o resumo já vem pronto
}
HICK_8 = 0.15 * np.log2(8 + 1)   # escolher 1 entre 8 filas (lei de Hick-Hyman, b≈0,15 s/bit)


def palavras(t: str) -> int:
    return len(str(t).split())


def tempos(c: dict, cen: str) -> dict:
    o = {k: v[cen] for k, v in OP.items()}
    p = {k: v[cen] for k, v in PAR.items()}
    ler = lambda n: n / o["leitura_wpm"] * 60  # noqa: E731
    PB = o["P"] + o["B"]
    # SEM: lê tudo, decide a fila entre 8, toca, escreve a resposta, envia
    sem_fila = ler(c["w_msg"]) + o["M"] + HICK_8 + PB
    sem = sem_fila + PB + o["M"] + p["chars_resposta_digitada"] * o["K"] + PB
    # COM: lê resumo + campos + resposta pronta (+ parte da mensagem), confere, envia; às vezes edita
    com_fila = ler(c["w_resumo"] + c["w_campos"] + p["fracao_le_mensagem_com"] * c["w_msg"]) + o["M"] + PB
    com = com_fila + ler(c["w_rascunho"]) + PB + p["pct_edita_rascunho"] * (PB + o["M"] + p["chars_edicao"] * o["K"] + PB)
    return {"sem_fila": sem_fila, "sem_total": sem, "com_fila": com_fila, "com_total": com}


motor = Motor()
pt = pd.read_csv(config.SOLUTION / "outputs" / "pt_eval_haiku.csv")
linhas = []
for texto in pt.texto_pt:
    tri, meta, d = motor.processar(texto, ja_perguntou=True)
    assert meta["fonte"] == "cache", "esperado cache: rode analysis/05_pt_eval.py antes"
    campos = " ".join(f"{k} {v}" for k, v in tri.campos.model_dump().items() if v)
    linhas.append({"w_msg": palavras(texto), "w_resumo": palavras(tri.resumo_pt), "w_campos": palavras(campos),
                   "w_rascunho": palavras(d.rascunho)})
df = pd.DataFrame(linhas)

R = {"_aviso": "ESTIMATIVA por modelo KLM, não medição com pessoas", "n_chamados": len(df),
     "palavras_medianas": df.median().to_dict(), "operadores": OP, "premissas": PAR, "cenarios": {}}
for cen in ["baixo", "base", "alto"]:
    t = pd.DataFrame([tempos(r, cen) for r in df.to_dict(orient="records")])
    m = t.median()
    R["cenarios"][cen] = {
        "sem_total_s": round(m.sem_total, 1), "com_total_s": round(m.com_total, 1),
        "reducao_total_pct": round((1 - m.com_total / m.sem_total) * 100, 1),
        "sem_so_fila_s": round(m.sem_fila, 1), "com_so_fila_s": round(m.com_fila, 1),
        "reducao_fila_pct": round((1 - m.com_fila / m.sem_fila) * 100, 1),
    }
print(json.dumps(R, indent=1, ensure_ascii=False))
(config.SOLUTION / "outputs" / "estimativa_klm.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))
