"""Prepara o painel do atendente.

1. Reclassifica as chamadas já registradas: dá ID sequencial, marca a origem, escreve o resumo em
   português e o motivo em linguagem de atendimento. Guarda uma cópia do arquivo antes de mexer.
2. Traduz para o português os 200 tickets da fila de triagem humana (texto público do Dataset 2,
   sem dado pessoal) e guarda a tradução, para a página não chamar a IA a cada abertura.

Uso: python preparar_painel.py
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime

import pandas as pd
import requests

from config import CONVERSAS, DEEPSEEK_MODELO, DEEPSEEK_URL, LOTE, TRADUCOES, chave_deepseek
from conversa import anonimizar
from registro import formatar_id, motivo_atendimento
from roteador import TRIAGEM

# Origem das chamadas gravadas antes de o campo existir (process log, rodadas 51 a 55): a página foi
# aberta ao Jó às 15:10 UTC de 2026-11-11; entre 15:18 e 15:22 UTC rodaram os meus testes e a bateria.
# Antes de 15:10, tudo foi teste meu.
ABERTURA_PAGINA = datetime.fromisoformat("2026-11-11T15:10:00+00:00")
JANELA_TESTES = (datetime.fromisoformat("2026-11-11T15:18:00+00:00"),
                 datetime.fromisoformat("2026-11-11T15:22:00+00:00"))
MODO = {"IA": "Atendimento por IA", "deepseek": "Atendimento por IA", "sem IA": "Atendimento sem IA"}


def chamar(prompt: str, conteudo: str) -> dict:
    r = requests.post(DEEPSEEK_URL, timeout=60, headers={"Authorization": f"Bearer {chave_deepseek()}"},
                      json={"model": DEEPSEEK_MODELO, "temperature": 0, "response_format": {"type": "json_object"},
                            "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": conteudo}]})
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def origem_antiga(inicio: str) -> str:
    t = datetime.fromisoformat(inicio)
    if t < ABERTURA_PAGINA:
        return "teste"
    if JANELA_TESTES[0] <= t <= JANELA_TESTES[1]:
        return "bateria"
    return "atendimento"


def resumir(textos: list[str]) -> list[str]:
    prompt = ('Para cada conversa da lista, escreva o pedido do cliente em português, em uma frase curta (até 15 '
              'palavras), sem nome, CPF, telefone ou e-mail. Responda só com JSON {"resumos": [...]} na mesma ordem.')
    return chamar(prompt, json.dumps(textos, ensure_ascii=False))["resumos"]


def reclassificar() -> None:
    if not CONVERSAS.exists():
        return
    linhas = [json.loads(x) for x in CONVERSAS.read_text().splitlines() if x.strip()]
    copia = CONVERSAS.with_name(f"conversas-antes-reclassificacao-{datetime.now():%Y%m%d-%H%M%S}.jsonl")
    shutil.copy(CONVERSAS, copia)
    sem_resumo = [i for i, x in enumerate(linhas) if not x.get("resumo_pt")]
    if sem_resumo and chave_deepseek():
        textos = [" / ".join(anonimizar(m["cliente"], linhas[i].get("nome")) for m in linhas[i]["conversa"]
                             if "dado de contato" not in m["cliente"]) for i in sem_resumo]
        for k in range(0, len(textos), 20):
            for i, r in zip(sem_resumo[k:k + 20], resumir(textos[k:k + 20])):
                linhas[i]["resumo_pt"] = r
    for n, x in enumerate(linhas, 1):
        x.setdefault("id", formatar_id(n))
        x.setdefault("origem", origem_antiga(x["inicio"]))
        x["modo"] = MODO.get(x.get("modo"), x.get("modo"))
        x.setdefault("motivo_tecnico", x.get("motivo"))
        x["motivo"] = motivo_atendimento(x["destino"], x["motivo_tecnico"], x["categoria"], x.get("resumo_pt"))
    CONVERSAS.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in linhas))
    por_origem = pd.Series([x["origem"] for x in linhas]).value_counts().to_dict()
    print(f"{len(linhas)} chamadas reclassificadas ({por_origem}); cópia anterior em {copia.name}")


def traduzir_fila() -> None:
    lt = pd.read_csv(LOTE)
    textos = lt[lt.destino == TRIAGEM].sort_values("confianca").head(200)["texto"].tolist()
    feitas = json.loads(TRADUCOES.read_text()) if TRADUCOES.exists() else {}
    faltam = [t for t in textos if t not in feitas]
    prompt = ('Cada item é um ticket de suporte de TI em inglês, sem pontuação e sem algumas palavras de ligação. '
              'Reescreva cada um em português do Brasil como o atendente leria: frases naturais, com pontuação e '
              'conectivos. Tire saudações, datas soltas e assinaturas. Não acrescente fatos que não estão no texto; '
              'se um trecho não fizer sentido, deixe de fora. Responda só com JSON {"traducoes": [...]} na mesma '
              'ordem e com o mesmo número de itens.')
    for k in range(0, len(faltam), 20):
        lote = faltam[k:k + 20]
        saida = chamar(prompt, json.dumps(lote, ensure_ascii=False))["traducoes"]
        if len(saida) == len(lote):
            feitas.update(dict(zip(lote, saida)))
    TRADUCOES.write_text(json.dumps(feitas, ensure_ascii=False, indent=1))
    print(f"fila: {sum(t in feitas for t in textos)} de {len(textos)} tickets traduzidos")


if __name__ == "__main__":
    if not chave_deepseek():
        raise SystemExit("sem chave da IA: a reclassificação faz o resumo e a fila precisa de tradução")
    reclassificar()
    traduzir_fila()
