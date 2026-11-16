"""Registro das chamadas para o painel do atendente: ID, situação e motivo em linguagem de atendimento.

Funções puras sobre o registro salvo em saida/conversas.jsonl, usadas pela conversa (ao salvar), pelo
painel e pela reclassificação das chamadas antigas.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

PREFIXO = "ATD-"
BRT = timezone(timedelta(hours=-3))
SITUACAO = {"IA atendendo": "Em atendimento pela IA", "resolvida pela IA": "Resolvida pela IA",
            "pessoa executa": "Reembolso ou cancelamento (time decide)", "cliente desistiu": "Cliente desistiu",
            "triagem humana": "Com o time (IA fora do ar)", "fila": "Encaminhada ao time",
            "assistência técnica": "Encaminhada à assistência técnica",
            "assunto incerto": "Com o time (assunto incerto)",
            "departamento especializado": "Departamento especializado (atenção)"}
# Destinos em que uma pessoa precisa fechar a chamada com um posicionamento (Jó, 2026-11-16).
COM_PESSOA = ("pessoa executa", "triagem humana", "assunto incerto", "departamento especializado")
CANAL_ROTULO = {"chat": "Chat", "e-mail": "E-mail", "rede social": "Rede social", "telefone": "Telefone"}
ROBO_ANTERIOR = "Robô anterior"
ORIGEM = {"atendimento": "Atendimento", "bateria": "Teste automático", "teste": "Teste interno"}


def formatar_id(n: int) -> str:
    return f"{PREFIXO}{n:05d}"


def proximo_id(caminho: Path) -> str:
    """Próximo ID sequencial, a partir do maior ID já registrado."""
    maior = 0
    if caminho.exists():
        for linha in caminho.read_text().splitlines():
            if linha.strip():
                m = re.search(r"(\d+)$", json.loads(linha).get("id", "") or "")
                maior = max(maior, int(m.group(1)) if m else 0)
    return formatar_id(maior + 1)


def normalizar_busca(texto: str) -> str | None:
    """Aceita "ATD-00044", "atd44", "44"; devolve o ID no formato do registro."""
    m = re.search(r"(\d+)", texto or "")
    return formatar_id(int(m.group(1))) if m else None


def hora_brt(iso: str) -> str:
    return datetime.fromisoformat(iso).astimezone(BRT).strftime("%d/%m/%Y %H:%M")


def motivo_atendimento(destino: str, motivo_tecnico: str, categoria: str, resumo_pt: str | None,
                       detalhes: dict | None = None) -> str:
    """Motivo para quem atende: o que o cliente pediu e por que a chamada está onde está."""
    relato = f" Relato: {resumo_pt.rstrip('.')}." if resumo_pt else ""
    tecnico = (motivo_tecnico or "").lower()
    if destino == "IA atendendo":
        return f"A IA ainda está atendendo o cliente; nada foi passado ao time.{relato}"
    if destino == "resolvida pela IA":
        return f"Resolvida pela IA: o cliente confirmou que deu certo.{relato}"
    if destino == "assistência técnica":
        indicada = (detalhes or {}).get("assistencia")
        onde = f" Assistência indicada: {indicada}." if indicada else ""
        return (f"Defeito de aparelho: depois dos passos de verificação, o cliente foi orientado a levar à assistência "
                f"técnica autorizada da empresa.{onde}{relato}")
    if destino == "departamento especializado":
        det = detalhes or {}
        return (f"ATENÇÃO: pedido que mexe em política, site ou infraestrutura. Nada foi executado nem alterado; "
                f"encaminhado ao departamento de {det.get('departamento') or 'especialidade a definir'}, que precisa dar "
                f"o posicionamento ao cliente.{relato}")
    if destino == "assunto incerto":
        return (f"Assunto incerto (mais provável: {categoria}): a IA não tinha confiança para resolver sozinha. Uma "
                f"pessoa do time assume e precisa fechar com o posicionamento do caso.{relato}")
    if destino == "fila":
        return f"Assunto identificado como {categoria}; encaminhada ao time de {categoria}.{relato}"
    if destino == "pessoa executa":
        tipo = next((t for t in ("reembolso", "cancelamento", "cobrança duplicada", "cobrança indevida",
                                 "alteração de cobrança") if tecnico.startswith(t)), "ação sobre dinheiro ou contrato")
        det = detalhes or {}
        extra = "".join(f" {rot}: {det[c] or 'não informado'}." for c, rot in (("pedido", "Pedido"), ("valor", "Valor"))
                        if c in det)
        rotulo = f"Pedido de {tipo}" if not tipo.startswith("cobrança") else f"Pedido sobre {tipo}"
        return f"{rotulo}: precisa de análise e decisão de uma pessoa do time.{extra}{relato}"
    if destino == "triagem humana":
        if "sem ia" in tecnico:
            return f"Atendimento feito sem IA; uma pessoa do time assume a conversa.{relato}"
        if "indisponível" in tecnico:
            return f"O atendimento por IA ficou fora do ar durante a conversa; o caso passou direto ao time.{relato}"
        if "não descrito" in tecnico or "não descreveu" in tecnico:
            return "O cliente não explicou o problema mesmo depois de 3 perguntas; o time precisa entrar em contato."
        return (f"Depois de 3 perguntas, o assunto ainda não ficou claro (mais provável: {categoria}); "
                f"o time precisa fazer a triagem.{relato}")
    if destino == "cliente desistiu":
        quando = (" durante a coleta dos detalhes do pedido" if "detalhes" in tecnico
                  else " durante a coleta dos dados de contato" if "coleta" in tecnico else "")
        return f"O cliente desistiu do atendimento{quando}; nada foi encaminhado.{relato}"
    return motivo_tecnico


def canal_de(x: dict) -> str:
    """Canal da chamada para o painel; com a rede social de entrada como etiqueta."""
    canal = CANAL_ROTULO.get(x.get("canal") or "chat", "Chat")
    return f"{canal} · {x['rede']}" if x.get("rede") else canal


def pendente_posicionamento(x: dict) -> bool:
    """Chamada que passou para uma pessoa e ainda não recebeu o posicionamento do caso."""
    return x.get("destino") in COM_PESSOA and not x.get("em_andamento") and not x.get("posicionamento")


def literal(texto: str | None) -> str:
    """Mostra o texto como está: sem isso, a máscara "***.***.003-88" vira itálico e negrito no painel (régua 2.4,
    2026-11-12) e o atendente lê "..003-88"."""
    t = (texto or "").replace("\\", "\\\\").replace("*", "\\*").replace("_", "\\_").replace("`", "\\`")
    return sem_link(t)


def sem_link(texto: str | None) -> str:
    """Texto do cliente (ou da IA) exibido no painel sem virar imagem ou link do markdown.

    Achado da régua de 2026-11-11 com o link público: quem conversa poderia escrever ![x](https://...) e o
    navegador de quem abre o painel carregaria a imagem de fora. O HTML já é escapado pelo Streamlit.
    """
    return (texto or "").replace("![", "!\\[").replace("](", "]\\(")
