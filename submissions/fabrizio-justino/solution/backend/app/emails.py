"""E-mails automáticos para os envolvidos, em dois públicos:

- EQUIPE (cada vendedor): briefing da semana, ritmo, lista de resgate e plano (se a
  emergência estiver ligada), "Atacar agora", críticos, um rascunho de follow-up pronto
  e a limpeza do pipeline;
- GESTÃO (cada manager + a Head de RevOps com a visão consolidada): briefing do time,
  ritmo por vendedor, alertas de gestão (sobrecarga com redistribuição, time sem deal
  fechável, limpeza, qualidade de dado), plano de resgate do time e análise de win-loss.

Os textos vêm da camada de IA (ia.py) — com fallback para template, então o e-mail sai
mesmo sem chave. Por segurança o padrão é só GERAR os arquivos (saida_emails/<data>/);
enviar exige LEAD_SCORER_EMAIL_MODO=enviar, SMTP configurado e config/destinatarios.json
(o .exemplo usa endereços @example.com e nunca é usado para envio real).

Uso (agendar toda segunda 7h no Agendador de Tarefas do Windows / cron):
    python -m app.emails --data 2017-12-04
    python -m app.emails --data 2017-12-04 --modo enviar --publico gestao
"""
import argparse
import html
import json
import logging
import re
import smtplib
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from . import config, consultas, ia
from .motor import Visao, registros
from .scoring import usd

logger = logging.getLogger("lead_scorer")

COR = {"primaria": "#0F5E73", "texto": "#0B1A20", "suave": "#6B7280", "borda": "#E5E7EB", "fundo": "#F5F5F5",
       "critico": "#E11D48", "atencao": "#D97706", "lembrete": "#0284C7", "ok": "#059669"}


@dataclass
class Email:
    publico: str          # 'equipe' | 'gestao'
    papel: str            # 'vendedor' | 'manager' | 'revops'
    nome: str
    para: list[str]
    assunto: str
    html: str
    texto: str
    fontes_ia: dict = field(default_factory=dict)   # seção → 'ia' | 'template'

    @property
    def slug(self) -> str:
        return f"{self.publico}-{re.sub(r'[^a-z0-9]+', '-', self.nome.lower()).strip('-')}"


# ── Destinatários ─────────────────────────────────────────────────────────────

def _email_exemplo(nome: str) -> str:
    return re.sub(r"[^a-z.]", "", nome.lower().replace(" ", ".")) + "@example.com"


def gerar_destinatarios_exemplo(v: Visao) -> None:
    """Escreve config/destinatarios.exemplo.json com todos do time (endereços
    @example.com, reservados para documentação — nunca entregam)."""
    t = v.dados.times
    conteudo = {
        "_leia": "Copie para destinatarios.json e troque pelos e-mails reais. Este arquivo nunca é usado para envio real.",
        "vendedores": {n: _email_exemplo(n) for n in sorted(t.sales_agent)},
        "managers": {n: _email_exemplo(n) for n in sorted(t.manager.unique())},
        "revops": ["head.revops@example.com"],
    }
    config.DESTINATARIOS_EXEMPLO.parent.mkdir(parents=True, exist_ok=True)
    config.DESTINATARIOS_EXEMPLO.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")


def carregar_destinatarios(v: Visao, para_envio: bool) -> dict:
    if config.DESTINATARIOS.exists():
        return json.loads(config.DESTINATARIOS.read_text(encoding="utf-8"))
    if para_envio:
        raise RuntimeError(f"Envio real exige {config.DESTINATARIOS} (copie e edite o destinatarios.exemplo.json).")
    if not config.DESTINATARIOS_EXEMPLO.exists():
        gerar_destinatarios_exemplo(v)
    return json.loads(config.DESTINATARIOS_EXEMPLO.read_text(encoding="utf-8"))


# ── Blocos de HTML (inline, compatível com clientes de e-mail) ────────────────

def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _rich(texto: str) -> str:
    """Texto da IA/template → HTML: parágrafos, bullets '- ' e **negrito**."""
    partes, lista = [], []

    def negrito(s: str) -> str:
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", _e(s))

    def fecha_lista():
        if lista:
            partes.append("<ul style='margin:6px 0 10px 18px;padding:0'>" + "".join(lista) + "</ul>")
            lista.clear()

    for linha in (texto or "").splitlines():
        linha = linha.strip()
        if not linha:
            fecha_lista()
        elif linha.startswith(("- ", "• ")):
            lista.append(f"<li style='margin:3px 0'>{negrito(linha[2:])}</li>")
        else:
            fecha_lista()
            partes.append(f"<p style='margin:6px 0'>{negrito(linha)}</p>")
    fecha_lista()
    return "".join(partes)


def _selo(fonte: str) -> str:
    rotulo, cor = ("gerado por IA", COR["primaria"]) if fonte == "ia" else ("texto automático", COR["suave"])
    return f"<span style='font-size:11px;color:{cor};border:1px solid {cor};border-radius:10px;padding:1px 7px'>{rotulo}</span>"


def _secao(titulo: str, corpo: str, cor: str = COR["primaria"], selo: str = "") -> str:
    return (f"<div style='margin:18px 0;padding:14px 16px;border:1px solid {COR['borda']};border-left:4px solid {cor};"
            f"border-radius:8px;background:#fff'>"
            f"<div style='font-size:12px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;color:{cor};"
            f"margin-bottom:6px'>{_e(titulo)} {selo}</div>{corpo}</div>")


def _tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    if not linhas:
        return f"<p style='color:{COR['suave']};margin:4px 0'>Nada por aqui.</p>"
    th = "".join(f"<th style='text-align:left;padding:6px 8px;font-size:11px;color:{COR['suave']};"
                 f"border-bottom:1px solid {COR['borda']}'>{_e(c)}</th>" for c in cabecalho)
    trs = "".join("<tr>" + "".join(f"<td style='padding:6px 8px;border-bottom:1px solid {COR['borda']};font-size:13px'>{c}</td>"
                                   for c in linha) + "</tr>" for linha in linhas)
    return f"<table style='width:100%;border-collapse:collapse'><tr>{th}</tr>{trs}</table>"


def _barra_ritmo(pct_meta: Optional[float], pct_tri: float) -> str:
    if pct_meta is None:
        return f"<span style='color:{COR['suave']}'>sem meta</span>"
    cor = COR["critico"] if pct_meta < pct_tri else COR["ok"]
    largura = round(min(pct_meta, 1) * 100)
    marcador = round(min(pct_tri, 1) * 100)
    return (f"<div style='position:relative;height:10px;background:{COR['fundo']};border-radius:5px;width:160px'>"
            f"<div style='height:10px;width:{largura}%;background:{cor};border-radius:5px'></div>"
            f"<div style='position:absolute;top:-2px;left:{marcador}%;width:2px;height:14px;background:{COR['texto']}'></div></div>"
            f"<div style='font-size:11px;color:{COR['suave']}'>{round(pct_meta * 100)}% da meta · "
            f"{round(pct_tri * 100)}% do trimestre</div>")


def _pagina(titulo: str, subtitulo: str, corpo: str, data_ref: str) -> str:
    return (f"<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>{_e(titulo)}</title></head>"
            f"<body style='margin:0;background:{COR['fundo']};font-family:Segoe UI,Arial,sans-serif;color:{COR['texto']}'>"
            f"<div style='max-width:680px;margin:0 auto;padding:20px'>"
            f"<div style='background:{COR['primaria']};color:#fff;padding:16px 20px;border-radius:10px'>"
            f"<div style='font-size:20px;font-weight:bold'>{_e(titulo)}</div>"
            f"<div style='font-size:13px;opacity:.8'>{_e(subtitulo)}</div></div>{corpo}"
            f"<p style='font-size:12px;color:{COR['suave']};margin-top:24px'>Gerado pelo Lead Scorer com os dados de "
            f"{_e(data_ref)}. Detalhes e explicação de cada score: <a href='{_e(config.URL_APP)}' style='color:{COR['primaria']}'>"
            f"{_e(config.URL_APP)}</a>. Textos marcados como \"gerado por IA\" foram escritos a partir dos números do "
            f"motor e conferidos automaticamente.</p></div></body></html>")


def _texto_puro(html_str: str) -> str:
    sem_tags = re.sub(r"<head>.*?</head>", "", html_str, flags=re.S)
    sem_tags = re.sub(r"<(br|/p|/tr|/li|/div)>", "\n", sem_tags)
    sem_tags = re.sub(r"<[^>]+>", " ", sem_tags)
    return re.sub(r"[ \t]+", " ", html.unescape(sem_tags)).replace(" \n", "\n").strip()


def _chance(d: dict) -> str:
    p = d.get("probabilidade")
    return "n/d" if p is None else f"{round(p * 100)}%"


def _linhas_deals(deals: list[dict]) -> list[list[str]]:
    return [[_e(d.get("conta") or "conta não preenchida") + f"<br><span style='color:{COR['suave']};font-size:11px'>"
             f"{_e(d['produto'])} · {_e(d['opportunity_id'])}</span>",
             _chance(d), usd(d.get("valor_esperado") or 0),
             _e(ia.fato_deal(d)["proximo_passo"])] for d in deals]


def _vezes(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:.1f}×".replace(".", ",")


def _bloco_alertas(lista: list[dict]) -> str:
    if not lista:
        return f"<p style='color:{COR['suave']};margin:4px 0'>Nenhum alerta nesta semana.</p>"
    itens = []
    for a in lista:
        cor = COR[a["severidade"]]
        extra = ""
        if a.get("redistribuicao"):
            extra = "<br>" + "<br>".join(f"↳ {_e(r['conta'] or 'sem conta')} · {_e(r['produto'])} → <strong>{_e(r['para'])}</strong>"
                                         for r in a["redistribuicao"])
        quem = f" <span style='color:{COR['suave']}'>({_e(a.get('conta') or 'sem conta')} · {_e(a.get('agente'))})</span>" \
            if a.get("opportunity_id") else ""
        itens.append(f"<li style='margin:6px 0'><strong style='color:{cor}'>{_e(a['titulo'])}</strong>{quem}<br>"
                     f"{_e(a['mensagem'])}<br><em>→ {_e(a['acao_sugerida'])}</em>{extra}</li>")
    return "<ul style='margin:4px 0 4px 18px;padding:0'>" + "".join(itens) + "</ul>"


# ── E-mail da EQUIPE (vendedor) ───────────────────────────────────────────────

def montar_vendedor(v: Visao, agente: str, para: list[str]) -> Optional[Email]:
    deals, met = consultas.recorte(v, agente=agente)
    m = registros(met)[0]
    if deals.empty and not m.get("meta"):
        return None  # sem pipeline e sem histórico: nada a dizer
    fontes = {}
    corpo = []
    tri = v.trimestre
    falta = max((m.get("meta") or 0) - m["fechado_trimestre"], 0)
    zumbis = deals[deals.fora_do_ciclo]
    atacar = registros(deals[deals.acao == "Atacar agora"].head(5))

    # Resumo de 3 linhas — a maioria lê só isso, no celular
    linhas_resumo = []
    if atacar:
        linhas_resumo.append("<strong>Feche:</strong> " + ", ".join(
            _e(f"{d.get('conta') or 'sem conta'} ({d['produto']})") for d in atacar[:3]))
    if len(zumbis):
        linhas_resumo.append(f"<strong>Encerre ou requalifique:</strong> {len(zumbis)} deals fora do ciclo")
    if m.get("meta"):
        linhas_resumo.append(f"<strong>Falta:</strong> {usd(falta)} para a meta em {tri.dias_restantes} dias")
    if linhas_resumo:
        corpo.append(f"<div style='margin:16px 0;padding:12px 16px;background:#fff;border-radius:8px;font-size:15px;"
                     f"line-height:1.6'>{'<br>'.join(linhas_resumo)}</div>")

    b = ia.briefing(v, agente=agente)
    fontes["briefing"] = b["fonte"]
    # O briefing-template repete o resumo e as tabelas abaixo — só entra quando a IA escreveu
    if b["fonte"] == "ia":
        corpo.append(_secao("Sua semana", _rich(b["texto"]), selo=_selo(b["fonte"])))

    corpo.append(_secao("Ritmo do trimestre", _barra_ritmo(m.get("pct_meta"), tri.pct_decorrido)
                        + (f"<p style='margin:8px 0 0'>Meta {usd(m['meta'])} · fechado {usd(m['fechado_trimestre'])} · "
                           f"faltam {usd(falta)} em {tri.dias_restantes} dias.</p>" if m.get("meta") else "")))

    emerg = consultas.emergencia(v, agente=agente)
    if emerg["ativa"]:
        plano = ia.plano_resgate(v, agente=agente)
        fontes["plano_resgate"] = plano["fonte"]
        r = emerg["resgate"]
        mostrados = r["deals"][:8]
        # Nunca prometer o que a lista não entrega: o texto depende de ela cobrir a meta
        cobertura = (f"Os {r['n']} deals da sua lista de resgate somam {usd(r['valor'])} se fecharem e cobrem o que falta."
                     if r["cobre_a_meta"] else
                     f"Mesmo fechando todos os {r['n']} deals que ainda cabem no trimestre ({usd(r['valor'])}), "
                     f"a meta não é batida — priorize os maiores.")
        if r["n"] > len(mostrados):
            cobertura += f" Abaixo, os {len(mostrados)} primeiros; a lista completa está na ferramenta."
        # O template do plano repete a tabela — o texto do plano só entra quando a IA escreveu
        texto_plano = (_rich(plano["texto"]) if plano["fonte"] == "ia" else "") + f"<p style='margin:4px 0'>{_e(cobertura)}</p>"
        linhas = [[_e(d.get("conta") or "conta não preenchida") + f"<br><span style='color:{COR['suave']};font-size:11px'>"
                   f"{_e(d['produto'])} · {d['idade_dias']} dias em Engaging</span>",
                   f"{round(d['prob_trimestre'] * 100)}%", usd(d["valor_liquido"])] for d in mostrados]
        corpo.append(_secao(f"Emergência: faltam {usd(emerg['falta'])} para a sua meta",
                            texto_plano + _tabela(["Deal (ordem de ataque)", "Chance no trimestre", "Se fechar"], linhas),
                            cor=COR["critico"], selo=_selo(plano["fonte"]) if plano["fonte"] == "ia" else ""))

    corpo.append(_secao("Atacar agora", _tabela(["Deal", "Chance", "Valor esperado", "Próximo passo"], _linhas_deals(atacar)),
                        cor=COR["ok"]))

    criticos = [a for lista in deals.alertas for a in lista if a["severidade"] == "critico" and a["na_fila"]]
    corpo.append(_secao("Alertas críticos de hoje", _bloco_alertas(criticos[:3]), cor=COR["critico"]))

    # Rascunho pronto para o deal crítico mais valioso (ou o 1º de "Atacar agora")
    alvo = criticos[0]["opportunity_id"] if criticos else (atacar[0]["opportunity_id"] if atacar else None)
    if alvo:
        r = ia.rascunho(v, alvo, "followup")
        fontes["rascunho"] = r["fonte"]
        corpo.append(_secao("Rascunho pronto para enviar ao cliente",
                            f"<p style='margin:4px 0'><strong>Assunto:</strong> {_e(r['assunto'])}</p>"
                            f"<div style='white-space:pre-wrap;background:{COR['fundo']};padding:10px;border-radius:6px;"
                            f"font-size:13px'>{_e(r['corpo'])}</div>", selo=_selo(r["fonte"])))

    if len(zumbis):
        requal =registros(zumbis[zumbis.acao == "Requalificar"].sort_values("valor", ascending=False).head(5))
        corpo.append(_secao(
            f"Limpeza: {len(zumbis)} deals fora do ciclo",
            f"<p style='margin:4px 0'>{int((zumbis.acao == 'Encerrar').sum())} para encerrar e "
            f"{int((zumbis.acao == 'Requalificar').sum())} para requalificar. Nenhum deal do histórico ganhou depois de "
            f"{v.bm.ciclo_max_dias} dias em Engaging — requalificar é perguntar ao cliente e, se o projeto continuar, "
            f"encerrar este e abrir uma oportunidade nova.</p>"
            + _tabela(["Requalificar primeiro", "Dias", "Valor de tabela"],
                      [[_e(d.get("conta") or "conta não preenchida") + f" · {_e(d['produto'])}", str(d["idade_dias"]),
                        usd(d["valor"])] for d in requal]),
            cor=COR["atencao"]))

    n_atacar = len(deals[deals.acao == "Atacar agora"])
    assunto = f"[Lead Scorer] Sua semana: {n_atacar} deals para atacar"
    if emerg["ativa"]:
        assunto += f" · EMERGÊNCIA: faltam {usd(emerg['falta'])}"
    pagina = _pagina(f"Bom dia, {agente.split()[0]}", f"Briefing de segunda · {v.data.strftime('%d/%m/%Y')}",
                     "".join(corpo), v.data.strftime("%d/%m/%Y"))
    return Email("equipe", "vendedor", agente, para, assunto, pagina, _texto_puro(pagina), fontes)


# ── E-mail da GESTÃO (manager ou RevOps) ──────────────────────────────────────

def montar_gestor(v: Visao, manager: Optional[str], para: list[str]) -> Email:
    papel = "manager" if manager else "revops"
    nome = manager or "Head de Revenue Operations"
    fontes = {}
    corpo = []
    tri = v.trimestre

    b = ia.briefing(v, manager=manager)
    fontes["briefing"] = b["fonte"]
    corpo.append(_secao("Resumo da semana", _rich(b["texto"]), selo=_selo(b["fonte"])))

    emerg = consultas.emergencia(v, manager=manager)
    if emerg["meta"]:
        corpo.append(_secao("Meta do trimestre", _barra_ritmo(emerg["pct_meta"], tri.pct_decorrido)
                            + f"<p style='margin:8px 0 0'>Meta {usd(emerg['meta'])} · fechado {usd(emerg['fechado'])} · "
                              f"projeção {usd(emerg['projecao'])} · {tri.dias_restantes} dias para fechar.</p>",
                            cor=COR["critico"] if emerg["ativa"] else COR["primaria"]))
    if emerg["ativa"]:
        plano = ia.plano_resgate(v, manager=manager)
        fontes["plano_resgate"] = plano["fonte"]
        corpo.append(_secao(f"Plano de resgate: faltam {usd(emerg['falta'])}", _rich(plano["texto"]),
                            cor=COR["critico"], selo=_selo(plano["fonte"])))

    t = consultas.time(v, manager=manager)
    if papel == "revops":
        corpo.append(_secao("Times", _tabela(
            ["Manager", "Ritmo", "Cobertura", "Carga", "Atacar"],
            [[_e(x["manager"]) + f"<br><span style='color:{COR['suave']};font-size:11px'>{_e(x['regiao'])}</span>",
              _barra_ritmo(x.get("pct_meta"), tri.pct_decorrido),
              _vezes(x.get("cobertura")), _vezes(x.get("carga_rel")), str(int(x["n_atacar"] or 0))]
             for x in t["times"]])))
    corpo.append(_secao("Ritmo por vendedor", _tabela(
        ["Vendedor", "Ritmo", "Cobertura", "Carga", "Sem conta", "Atacar"],
        [[_e(x["agente"]), _barra_ritmo(x.get("pct_meta"), tri.pct_decorrido),
          _vezes(x.get("cobertura")), _vezes(x.get("carga_rel")),
          "—" if x.get("pct_sem_conta") is None else f"{round(x['pct_sem_conta'] * 100)}%", str(x["n_atacar"])]
         for x in t["vendedores"] if x.get("deals_abertos") or x.get("meta")])))

    alertas_time = [a for a in consultas.alertas(v, manager=manager)["time"] if a["tipo"] != "emergencia"]
    corpo.append(_secao("Alertas de gestão", _bloco_alertas(alertas_time), cor=COR["atencao"]))

    w = ia.analise_winloss(v, manager=manager)
    fontes["winloss"] = w["fonte"]
    corpo.append(_secao("Análise do trimestre (ganhos e perdas)", _rich(w["texto"]), selo=_selo(w["fonte"])))

    pct = emerg.get("pct_meta")
    assunto = f"[Lead Scorer] Gestão · {nome}: " + (f"{round(pct * 100)}% da meta" if pct is not None else "resumo da semana")
    if emerg["ativa"]:
        assunto += f" · EMERGÊNCIA: faltam {usd(emerg['falta'])}"
    pagina = _pagina(nome, f"Visão de gestão · {v.data.strftime('%d/%m/%Y')}", "".join(corpo), v.data.strftime("%d/%m/%Y"))
    return Email("gestao", papel, nome, para, assunto, pagina, _texto_puro(pagina), fontes)


# ── Geração, gravação e envio ─────────────────────────────────────────────────

def listar(v: Visao, para_envio: bool = False) -> list[dict]:
    """Quem recebe o quê, sem montar os e-mails (rápido — usado pela interface)."""
    dest = carregar_destinatarios(v, para_envio)
    com_pipeline = set(v.deals.agente) | set(v.metricas[v.metricas.meta.notna()].agente)
    itens = [{"publico": "equipe", "papel": "vendedor", "nome": n, "para": [dest["vendedores"].get(n)]}
             for n in sorted(com_pipeline) if dest["vendedores"].get(n)]
    itens += [{"publico": "gestao", "papel": "manager", "nome": n, "para": [dest["managers"].get(n)]}
              for n in sorted(v.metricas.manager.unique()) if dest["managers"].get(n)]
    if dest.get("revops"):
        itens.append({"publico": "gestao", "papel": "revops", "nome": "Head de Revenue Operations", "para": dest["revops"]})
    return itens


def montar(v: Visao, papel: str, nome: str, para: list[str]) -> Optional[Email]:
    if papel == "vendedor":
        return montar_vendedor(v, nome, para)
    return montar_gestor(v, nome if papel == "manager" else None, para)


def enviar(email: Email) -> bool:
    destinos = [config.EMAIL_REDIRECIONAR] if config.EMAIL_REDIRECIONAR else email.para
    if not all([config.SMTP_HOST, config.SMTP_USER, config.SMTP_PASSWORD]):
        raise RuntimeError("SMTP não configurado: preencha LEAD_SCORER_SMTP_* no backend/.env.")
    if any(d.endswith("@example.com") for d in destinos):
        raise RuntimeError("Destinatário @example.com — use config/destinatarios.json com endereços reais.")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = email.assunto + (f" (para {', '.join(email.para)})" if config.EMAIL_REDIRECIONAR else "")
    msg["From"] = config.SMTP_FROM
    msg["To"] = ", ".join(destinos)
    msg.attach(MIMEText(email.texto, "plain", "utf-8"))
    msg.attach(MIMEText(email.html, "html", "utf-8"))
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as servidor:
        servidor.starttls()
        servidor.login(config.SMTP_USER, config.SMTP_PASSWORD)
        servidor.sendmail(config.SMTP_FROM, destinos, msg.as_string())
    return True


def executar(v: Visao, modo: str = config.EMAIL_MODO, publico: str = "todos", nome: Optional[str] = None) -> dict:
    """Monta, grava (sempre) e envia (se modo='enviar') os e-mails do dia."""
    if modo not in ("arquivo", "enviar"):
        raise ValueError("modo deve ser 'arquivo' ou 'enviar'.")
    pasta = config.EMAIL_SAIDA / v.data.date().isoformat()
    pasta.mkdir(parents=True, exist_ok=True)
    resultado = {"data": v.data.date().isoformat(), "modo": modo, "pasta": str(pasta), "emails": []}
    for item in listar(v, para_envio=(modo == "enviar")):
        if publico != "todos" and item["publico"] != publico:
            continue
        if nome and item["nome"] != nome:
            continue
        email = montar(v, item["papel"], item["nome"], item["para"])
        if email is None:
            continue
        (pasta / f"{email.slug}.html").write_text(email.html, encoding="utf-8")
        registro = {"publico": email.publico, "papel": email.papel, "nome": email.nome, "para": email.para,
                    "assunto": email.assunto, "arquivo": f"{email.slug}.html", "fontes_ia": email.fontes_ia, "enviado": False}
        if modo == "enviar":
            try:
                registro["enviado"] = enviar(email)
            except Exception as e:  # um e-mail com problema não derruba os outros
                registro["erro"] = str(e)
                logger.error("Falha ao enviar para %s: %s", email.nome, e)
        resultado["emails"].append(registro)

    # Índice para abrir no navegador e conferir antes de ligar o envio
    linhas = "".join(f"<li>[{_e(r['publico'])}] <a href='{_e(r['arquivo'])}'>{_e(r['nome'])}</a> — {_e(r['assunto'])}"
                     f"{' ✓ enviado' if r['enviado'] else ''}{' ✗ ' + _e(r['erro']) if r.get('erro') else ''}</li>"
                     for r in resultado["emails"])
    (pasta / "index.html").write_text(f"<!doctype html><meta charset='utf-8'><title>E-mails {resultado['data']}</title>"
                                      f"<h2>E-mails de {resultado['data']} ({modo})</h2><ul>{linhas}</ul>", encoding="utf-8")
    (pasta / "resumo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def _cli() -> None:
    from .dados import carregar
    from .motor import Motor

    p = argparse.ArgumentParser(description="Gera/envia os e-mails do Lead Scorer (equipe e gestão).")
    p.add_argument("--data", help="Data de referência YYYY-MM-DD (padrão: data final do dataset)")
    p.add_argument("--modo", choices=["arquivo", "enviar"], default=config.EMAIL_MODO)
    p.add_argument("--publico", choices=["todos", "equipe", "gestao"], default="todos")
    p.add_argument("--nome", help="Só um destinatário (nome do vendedor, do manager ou 'Head de Revenue Operations')")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    motor = Motor(carregar(config.DATA_DIR))
    r = executar(motor.visao(a.data), modo=a.modo, publico=a.publico, nome=a.nome)
    enviados = sum(1 for e in r["emails"] if e["enviado"])
    print(f"{len(r['emails'])} e-mails gerados em {r['pasta']} ({enviados} enviados). IA: {ia.status()}")


if __name__ == "__main__":
    _cli()
