"""
Comparação: classificador simples (TF-IDF + regressão logística) x LLM (Gemini, zero-shot).

Pergunta de negócio: vale pagar um LLM para classificar tickets, ou o modelo simples resolve?

Como rodar (de dentro da pasta solution):
    python -m pip install google-genai
    set GEMINI_API_KEY=sua_chave_aqui        (Windows CMD; a chave fica só nesta janela)
    python comparar_llm.py

Opcional:
    set GEMINI_MODEL=gemini-2.5-flash        (modelo a usar)
    set AMOSTRA=200                          (quantidade de tickets)
    set PRECO_ENTRADA_USD=0.30               (US$ por 1 milhão de tokens de entrada, conforme a tabela do Google)
    set PRECO_SAIDA_USD=2.50                 (US$ por 1 milhão de tokens de saída)

A chave NUNCA vai para o código nem para o GitHub: ela é lida da variável de ambiente.
Saída: resultados_llm.md
"""
import json
import os
import re
import time
from pathlib import Path

import numpy as np

import triagem

SAIDA = Path(__file__).resolve().parent / "resultados_llm.md"
MODELO = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
N = int(os.environ.get("AMOSTRA", "200"))
LOTE = 10  # tickets por chamada, para caber no limite gratuito de requisições
PRECO_IN = float(os.environ.get("PRECO_ENTRADA_USD", "0.30"))
PRECO_OUT = float(os.environ.get("PRECO_SAIDA_USD", "2.50"))

CATEGORIAS = ["Access", "Administrative rights", "HR Support", "Hardware",
              "Internal Project", "Miscellaneous", "Purchase", "Storage"]

PROMPT = """You are triaging internal IT service desk tickets.
Classify EACH ticket into exactly one of these categories:
- Access: access to systems, folders, accounts, passwords, logins
- Administrative rights: admin permissions, elevated rights, installing software that needs admin
- HR Support: HR matters, employees, leave, contracts, payroll, onboarding/offboarding of people
- Hardware: laptops, screens, keyboards, printers, phones, physical equipment and their failures
- Internal Project: internal projects, project tasks, project tools and deliverables
- Miscellaneous: anything that does not clearly fit the others
- Purchase: buying equipment, licenses, purchase orders, quotes, invoices from vendors
- Storage: shared drives, folders space, disk/storage quotas, file storage

The texts are lowercased and without punctuation or numbers.
Answer ONLY with a JSON list, one object per ticket, in the same order:
[{"id": <id>, "category": "<one of the categories>"}]

Tickets:
"""


def montar_prompt(lote):
    linhas = [f'{{"id": {i}, "text": {json.dumps(t[:1500])}}}' for i, t in lote]
    return PROMPT + "\n".join(linhas)


def extrair_json(texto):
    m = re.search(r"\[.*\]", texto, re.S)
    if not m:
        raise ValueError("resposta sem JSON")
    return json.loads(m.group(0))


def main():
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        raise SystemExit("Defina a chave antes: set GEMINI_API_KEY=sua_chave (ver instruções no topo do arquivo).")
    from google import genai  # pip install google-genai
    cliente = genai.Client(api_key=chave)

    # mesma divisão treino/teste da avaliação oficial; a amostra sai SÓ do teste
    pacote, teste = triagem.treinar(salvar=False)
    amostra = teste.sample(N, random_state=123)
    y = amostra["Topic_group"].to_numpy()

    # 1) Modelo simples
    t0 = time.perf_counter()
    pred_simples = pacote["modelo"].predict(pacote["vetorizador"].transform(amostra["texto"]))
    tempo_simples = time.perf_counter() - t0

    # 2) LLM, em lotes
    pred_llm = np.array([""] * N, dtype=object)
    tok_in = tok_out = 0
    falhas = 0
    t0 = time.perf_counter()
    itens = list(enumerate(amostra["Document"].tolist()))
    for k in range(0, N, LOTE):
        lote = itens[k:k + LOTE]
        for tentativa in range(3):
            try:
                resp = cliente.models.generate_content(model=MODELO, contents=montar_prompt(lote))
                for item in extrair_json(resp.text):
                    cat = str(item.get("category", "")).strip()
                    pred_llm[int(item["id"])] = cat if cat in CATEGORIAS else "INVÁLIDA"
                uso = getattr(resp, "usage_metadata", None)
                if uso:
                    tok_in += getattr(uso, "prompt_token_count", 0) or 0
                    tok_out += (getattr(uso, "candidates_token_count", 0) or 0) + (getattr(uso, "thoughts_token_count", 0) or 0)
                break
            except Exception as e:  # limite de requisições, JSON quebrado etc.
                print(f"  lote {k // LOTE + 1}: tentativa {tentativa + 1} falhou ({str(e)[:90]}); esperando...")
                time.sleep(20)
        else:
            falhas += len(lote)
        print(f"lote {k // LOTE + 1}/{(N + LOTE - 1) // LOTE} ok")
        time.sleep(6)  # respeita o limite gratuito de requisições por minuto
    tempo_llm = time.perf_counter() - t0

    respondidos = pred_llm != ""
    acc_simples = (pred_simples == y).mean()
    acc_llm = (pred_llm[respondidos] == y[respondidos]).mean() if respondidos.any() else float("nan")
    acc_simples_mesmos = (pred_simples[respondidos] == y[respondidos]).mean() if respondidos.any() else float("nan")
    custo_usd = tok_in / 1e6 * PRECO_IN + tok_out / 1e6 * PRECO_OUT
    custo_por_mil = custo_usd / max(respondidos.sum(), 1) * 1000
    concordam = (pred_llm[respondidos] == pred_simples[respondidos]).mean()

    L = ["# Classificador simples x LLM (zero-shot)", "",
         f"- Amostra: {N} tickets do conjunto de teste (nunca vistos pelo modelo simples)",
         f"- LLM: {MODELO}, sem exemplos (zero-shot), {LOTE} tickets por chamada",
         f"- Tickets respondidos pelo LLM: {respondidos.sum()} de {N} (falhas: {falhas})", "",
         "| | Modelo simples | LLM |", "|---|---|---|",
         f"| Acerto (mesmos tickets) | {acc_simples_mesmos:.1%} | {acc_llm:.1%} |",
         f"| Tempo para classificar a amostra | {tempo_simples:.2f} s | {tempo_llm:.0f} s (inclui pausas do limite gratuito) |",
         f"| Custo estimado por 1.000 tickets | ~US$ 0 (roda local) | ~US$ {custo_por_mil:.3f} |", "",
         f"- Os dois concordam em {concordam:.1%} dos tickets.",
         f"- Tokens: {tok_in:,} de entrada e {tok_out:,} de saída.".replace(",", "."),
         f"- Preço usado: US$ {PRECO_IN} (entrada) e US$ {PRECO_OUT} (saída) por 1 milhão de tokens. "
         "Confira a tabela atual do Google; no plano gratuito o custo é zero, com limite de uso.",
         f"- Acerto do modelo simples na amostra inteira: {acc_simples:.1%}"]
    SAIDA.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
