"""Camada de IA (OpenAI) — interpretação e texto EM CIMA do motor, nunca no lugar dele.

O motor (scoring/calibração/alertas) é determinístico, calibrado e testado; um LLM
calculando probabilidade seria pior e impossível de auditar. Aqui o LLM só transforma
fatos prontos em decisão e texto:

  1. briefing        — a semana do vendedor / do manager / da RevOps
  2. explicar_deal   — o "Por que score X?" num parágrafo, com o próximo passo
  3. perguntar       — chat com tool calling sobre as consultas existentes
  4. plano_resgate   — a lista de resgate virando plano por vendedor
  5. rascunho        — e-mail de follow-up / requalificação, nota de encerramento
  6. analise_winloss — 3 a 5 insights do trimestre para o manager

Regras contra alucinação (o ponto mais importante):
- o LLM recebe só FATOS prontos, já formatados como devem aparecer ("US$ 4.821", "41%");
- todo número da resposta é conferido contra os fatos; se não bater, refaz uma vez e
  depois cai no texto-template;
- frases que atribuem chance a vendedor/conta/setor (que os dados mostram não prever
  nada) são bloqueadas;
- sem chave (LEAD_SCORER_OPENAI_API_KEY), tudo cai no template — a demo nunca quebra;
- respostas ficam em cache (memória + disco) e cada chamada é registrada em logs/ia.jsonl.

Credencial exclusiva deste projeto: a chave é passada explicitamente ao cliente, então
o SDK nunca pega um OPENAI_API_KEY genérico do ambiente."""
import hashlib
import json
import logging
import re
import time
from datetime import date, datetime
from typing import Callable, Optional

from . import config, consultas
from .motor import Visao, registros
from .scoring import ORDEM_ACOES, horizonte, usd

logger = logging.getLogger("lead_scorer")

# Muda quando prompt/fatos mudam de formato — invalida o cache antigo
VERSAO_PROMPT = "v1"

SISTEMA = """Você é o assistente de vendas do Lead Scorer, escrevendo para vendedores e managers de um time comercial brasileiro.

Regras inegociáveis:
1. Use SOMENTE os fatos do JSON recebido. Todo número que você escrever precisa aparecer no JSON exatamente como está lá (ex.: "US$ 4.821", "41%", "27 dias", "31/12/2017"). Nunca calcule, some, subtraia, arredonde ou estime números novos.
2. Nunca diga que um vendedor, conta, setor, produto ou porte tem mais (ou menos) chance de ganhar — os dados deste time mostram que isso não prevê o resultado. Argumente sempre com tempo (há quantos dias o deal está em Engaging, quanto falta para o fim do trimestre), valor e a ação recomendada.
3. Não invente fatos sobre o cliente (contatos, reuniões, necessidades, objeções) que não estejam no JSON.
4. Português do Brasil, direto, sem floreio, sem elogios, sem emoji. Termine com o próximo passo concreto."""

# Padrões que denunciam a narrativa proibida (regra 2)
_PROIBIDO = [
    re.compile(r"perfil\s+(bom|ótimo|otimo|ideal|favorável|favoravel|promissor|vencedor)", re.I),
    re.compile(r"(vendedor|vendedora|conta|cliente|setor|porte|produto)[^.\n]{0,50}"
               r"(alta|maior|boa|ótima|otima|melhor)\s+(chance|probabilidade|taxa de (ganho|conversão|conversao))", re.I),
]


# ── Formatação dos fatos (exatamente como devem aparecer no texto) ────────────

def _pct(x: Optional[float]) -> Optional[str]:
    return None if x is None else f"{round(x * 100)}%"


def _dbr(d) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return d.strftime("%d/%m/%Y")


def _dias(n: Optional[int]) -> Optional[str]:
    return None if n is None else f"{n} dias"


def _proximo_passo(d: dict) -> str:
    for a in d.get("alertas") or []:
        if a.get("acao_sugerida"):
            return a["acao_sugerida"]
    return {
        "Atacar agora": "Peça a decisão do cliente esta semana.",
        "Nutrir": "Mantenha o contato e avance a proposta.",
        "Requalificar": "Pergunte se o projeto continua; se sim, encerre este e abra uma oportunidade nova.",
        "Primeiro contato": "Agende o primeiro contato e mova para Engaging.",
        "Encerrar": "Encerre como Lost para limpar o pipeline.",
    }.get(d.get("acao"), "Agende o próximo contato.")


def fato_deal(d: dict, completo: bool = False) -> dict:
    f = {
        "id": d["opportunity_id"],
        "conta": d.get("conta") or "conta não preenchida",
        "produto": d["produto"],
        "vendedor": d["agente"],
        "stage": d["stage"],
        "dias_em_engaging": _dias(d.get("idade_dias")),
        "acao": d["acao"],
        "score": str(d["score"]),
        "chance_no_prazo": _pct(d.get("probabilidade")) or "n/d (sem data de engajamento)",
        "faixa_da_chance": (f"{_pct(d['prob_min'])} a {_pct(d['prob_max'])}"
                            if d.get("prob_min") is not None and d.get("prob_max") is not None else None),
        "valor_esperado": usd(d.get("valor_esperado") or 0),
        "valor_se_fechar": usd(d.get("valor_liquido") or 0),
        "proximo_passo": _proximo_passo(d),
    }
    if completo:
        f["motivos_do_score"] = [m["texto"] for m in d.get("motivos") or []]
        f["alertas"] = [{"titulo": a["titulo"], "mensagem": a["mensagem"], "acao": a["acao_sugerida"]}
                        for a in d.get("alertas") or []]
    return f


def _fato_alerta(a: dict) -> dict:
    f = {"tipo": a["tipo"], "severidade": a["severidade"], "titulo": a["titulo"],
         "mensagem": a["mensagem"], "acao": a["acao_sugerida"]}
    if a.get("opportunity_id"):
        f.update({"id": a["opportunity_id"], "vendedor": a.get("agente"), "conta": a.get("conta") or "conta não preenchida"})
    if a.get("redistribuicao"):
        f["redistribuicao"] = [f"{r['conta'] or 'sem conta'} · {r['produto']} → {r['para']}" for r in a["redistribuicao"]]
    return f


def _fato_vendedor(m: dict) -> dict:
    return {
        "vendedor": m["agente"], "manager": m["manager"],
        "meta": usd(m["meta"]) if m.get("meta") else None,
        "fechado": usd(m["fechado_trimestre"]),
        "pct_meta": _pct(m.get("pct_meta")),
        "cobertura": None if m.get("cobertura") is None else f"{m['cobertura']:.1f}×".replace(".", ","),
        "carga": None if m.get("carga_rel") is None else f"{m['carga_rel']:.1f}×".replace(".", ","),
        "deals_em_atacar_agora": str(m.get("n_atacar") or 0),
        "pct_deals_sem_conta": _pct(m.get("pct_sem_conta")),
    }


def _fato_emergencia(e: dict) -> dict:
    tri = e["trimestre"]
    return {
        "modo_emergencia_ativo": e["ativa"],
        "fim_do_trimestre": _dbr(tri["fim"]),
        "dias_para_fechar_o_trimestre": _dias(tri["dias_restantes"]),
        "pct_trimestre_decorrido": _pct(tri["pct_decorrido"]),
        "meta": usd(e["meta"]) if e.get("meta") else None,
        "fechado": usd(e["fechado"]),
        "pct_meta": _pct(e.get("pct_meta")),
        "falta_para_a_meta": usd(e["falta"]),
        "projecao": usd(e["projecao"]),
        "lista_de_resgate": {"n_deals": str(e["resgate"]["n"]), "valor_se_todos_fecharem": usd(e["resgate"]["valor"]),
                             "cobre_a_meta": e["resgate"]["cobre_a_meta"]},
    }


# ── Infra: cliente, cache, log, validação ─────────────────────────────────────

_cliente_openai = None
_cache_memoria: dict[str, dict] = {}
_perguntas_hoje: dict[str, int] = {}


def ia_ativa() -> bool:
    return bool(config.OPENAI_API_KEY)


def status() -> dict:
    return {"ativa": ia_ativa(), "provedor": "openai", "modelo": config.LLM_MODELO if ia_ativa() else None}


def _cliente():
    global _cliente_openai
    if _cliente_openai is None:
        from openai import OpenAI
        # api_key explícita: nunca herda um OPENAI_API_KEY genérico do ambiente
        _cliente_openai = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.LLM_TIMEOUT_S, max_retries=2)
    return _cliente_openai


def _chamar(mensagens: list, json_saida: bool = False, max_tokens: int = 700, ferramentas: Optional[list] = None):
    """Uma chamada ao chat completions. Devolve a `message` da 1ª escolha.
    Isolada aqui para os testes substituírem sem rede."""
    kwargs = {"model": config.LLM_MODELO, "messages": mensagens, "max_tokens": max_tokens, "temperature": 0.2}
    if json_saida:
        kwargs["response_format"] = {"type": "json_object"}
    if ferramentas:
        kwargs["tools"] = ferramentas
    return _cliente().chat.completions.create(**kwargs).choices[0].message


def _chave(funcao: str, fatos) -> str:
    bruto = json.dumps([VERSAO_PROMPT, config.LLM_MODELO, funcao, fatos], ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()[:32]


def _cache_ler(chave: str) -> Optional[dict]:
    if chave in _cache_memoria:
        return _cache_memoria[chave]
    arq = config.IA_CACHE_DIR / f"{chave}.json"
    if arq.exists():
        try:
            _cache_memoria[chave] = json.loads(arq.read_text(encoding="utf-8"))
            return _cache_memoria[chave]
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _cache_gravar(chave: str, resultado: dict) -> None:
    _cache_memoria[chave] = resultado
    try:
        config.IA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (config.IA_CACHE_DIR / f"{chave}.json").write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        logger.warning("Não consegui gravar o cache da IA: %s", e)


def _registrar(evento: dict) -> None:
    """Prompt, fatos, resposta e modelo de cada chamada — depuração e auditoria."""
    try:
        config.IA_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(config.IA_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "modelo": config.LLM_MODELO, **evento},
                               ensure_ascii=False, default=str) + "\n")
    except OSError as e:
        logger.warning("Não consegui gravar o log da IA: %s", e)


_NUMERO = re.compile(r"\d+(?:[.,]\d+)*")


def problemas_no_texto(texto: str, fonte: str) -> list[str]:
    """Números que não existem nos fatos + frases proibidas. Números até 10 passam
    (enumeração '1.', '3 deals' de uma lista que o próprio modelo está contando)."""
    problemas = []
    for n in set(_NUMERO.findall(texto or "")):
        limpo = n.rstrip(".,")
        if limpo.isdigit() and int(limpo) <= 10:
            continue
        if limpo not in fonte:
            problemas.append(f"o número {limpo} não está nos fatos")
    for padrao in _PROIBIDO:
        m = padrao.search(texto or "")
        if m:
            problemas.append(f"frase proibida (atribui chance a vendedor/conta/setor): '{m.group(0)}'")
    return problemas


def _gerar(funcao: str, fatos: dict, instrucao: str, template: str,
           json_saida: bool = False, max_tokens: int = 700) -> dict:
    """Fluxo comum: cache → (sem chave: template) → LLM → validação → 1 retry → template."""
    chave = _chave(funcao, fatos)
    em_cache = _cache_ler(chave)
    if em_cache:
        return {**em_cache, "cache": True}
    if not ia_ativa():
        return {"texto": template, "fonte": "template", "motivo": "IA não configurada"}

    fonte = json.dumps(fatos, ensure_ascii=False)
    mensagens = [{"role": "system", "content": SISTEMA},
                 {"role": "user", "content": f"{instrucao}\n\nFATOS (JSON):\n{fonte}"}]
    for tentativa in (1, 2):
        inicio = time.perf_counter()
        try:
            texto = (_chamar(mensagens, json_saida=json_saida, max_tokens=max_tokens).content or "").strip()
        except Exception as e:  # rede, cota, chave inválida — a tela nunca quebra por isso
            logger.warning("IA (%s) falhou: %s", funcao, e)
            _registrar({"funcao": funcao, "tentativa": tentativa, "erro": str(e), "fatos": fatos})
            return {"texto": template, "fonte": "template", "motivo": "falha na chamada da IA"}
        problemas = problemas_no_texto(texto, fonte)
        _registrar({"funcao": funcao, "tentativa": tentativa, "instrucao": instrucao, "fatos": fatos, "resposta": texto,
                    "problemas": problemas, "ms": round((time.perf_counter() - inicio) * 1000)})
        if not problemas:
            resultado = {"texto": texto, "fonte": "ia", "modelo": config.LLM_MODELO}
            _cache_gravar(chave, resultado)
            return resultado
        mensagens += [{"role": "assistant", "content": texto},
                      {"role": "user", "content": "Sua resposta quebrou as regras: " + "; ".join(problemas)
                       + ". Reescreva usando somente números que aparecem nos FATOS, copiados exatamente."}]
    return {"texto": template, "fonte": "template", "motivo": "a resposta da IA não passou na validação"}


# ── 1. Briefing de segunda-feira ──────────────────────────────────────────────

def _fatos_briefing(v: Visao, agente: Optional[str], manager: Optional[str]) -> dict:
    deals, met = consultas.recorte(v, agente=agente, manager=manager)
    emerg = consultas.emergencia(v, agente=agente, manager=manager)
    atacar = [fato_deal(d) for d in registros(deals[deals.acao == "Atacar agora"].head(5))]
    criticos = [_fato_alerta(a) for lista in deals.alertas for a in lista
                if a["severidade"] == "critico" and a["na_fila"]][:5]
    zumbis = deals[deals.fora_do_ciclo]
    publico = "vendedor" if agente else "manager" if manager else "revops"
    fatos = {
        "publico": publico,
        "nome": agente or manager or "Head de Revenue Operations",
        "data": _dbr(v.data),
        "trimestre": _fato_emergencia(emerg),
        "deals_abertos": str(len(deals)),
        "atacar_agora": atacar,
        "alertas_criticos": criticos,
        "limpeza": {"para_encerrar": str(int((zumbis.acao == "Encerrar").sum())),
                    "para_requalificar": str(int((zumbis.acao == "Requalificar").sum()))},
    }
    if publico != "vendedor":
        ritmo = met[met.pct_meta.notna()]
        atras = ritmo[ritmo.pct_meta < v.trimestre.pct_decorrido].sort_values("pct_meta")
        fatos["vendedores_atras_do_ritmo"] = [_fato_vendedor(m) for m in registros(atras.head(5))]
        fatos["alertas_do_time"] = [_fato_alerta(a) for a in consultas.alertas(v, agente=agente, manager=manager)["time"]
                                    if a["tipo"] != "emergencia"]
    return fatos


def _template_briefing(f: dict) -> str:
    t = f["trimestre"]
    linhas = []
    if t["meta"]:
        linhas.append(f"Ritmo: {t['pct_meta']} da meta com {t['pct_trimestre_decorrido']} do trimestre decorrido "
                      f"(faltam {t['falta_para_a_meta']} e {t['dias_para_fechar_o_trimestre']}).")
    if t["modo_emergencia_ativo"]:
        linhas.append(f"Modo emergência ativo: projeção de {t['projecao']} abaixo da meta de {t['meta']}.")
    if f["atacar_agora"]:
        linhas.append("Feche estes: " + "; ".join(f"{d['conta']} · {d['produto']} ({d['valor_esperado']} esperado)"
                                                 for d in f["atacar_agora"][:3]) + ".")
    if f["limpeza"]["para_encerrar"] != "0" or f["limpeza"]["para_requalificar"] != "0":
        linhas.append(f"Limpe: {f['limpeza']['para_encerrar']} deals para encerrar e "
                      f"{f['limpeza']['para_requalificar']} para requalificar.")
    atras = f.get("vendedores_atras_do_ritmo", [])[:3]
    if atras:
        linhas.append("Atrás do ritmo: " + ", ".join(f"{v['vendedor']} ({v['pct_meta']} da meta)" for v in atras) + ".")
    if f["publico"] == "vendedor":
        passo = f["atacar_agora"][0]["proximo_passo"] if f["atacar_agora"] else "reativar os deals em Prospecting."
    elif t["modo_emergencia_ativo"]:
        passo = "revisar a lista de resgate com os vendedores atrás do ritmo ainda hoje."
    else:
        passo = "revisar com o time os deals em 'Atacar agora' e aprovar a limpeza dos fora do ciclo."
    linhas.append("Próximo passo: " + passo)
    return " ".join(linhas)


def briefing(v: Visao, agente: Optional[str] = None, manager: Optional[str] = None) -> dict:
    f = _fatos_briefing(v, agente, manager)
    if f["publico"] == "vendedor":
        instrucao = (f"Escreva o briefing de segunda-feira para o vendedor {f['nome']}, em até 120 palavras: uma frase "
                     "sobre o ritmo do trimestre; 'Feche estes:' com até 3 deals de atacar_agora (conta, produto, valor "
                     "esperado); 'Limpe:' com a contagem da limpeza; termine com o próximo passo.")
    else:
        instrucao = (f"Escreva o briefing de segunda-feira para {f['nome']} ({f['publico']}), em até 150 palavras: ritmo "
                     "do recorte, quem está atrás do ritmo, os alertas do time mais importantes e o próximo passo de gestão.")
    r = _gerar("briefing", f, instrucao, _template_briefing(f))
    r["deals_citados"] = [d["id"] for d in f["atacar_agora"]] + [a["id"] for a in f["alertas_criticos"] if a.get("id")]
    return r


# ── 2. Explicação do deal ─────────────────────────────────────────────────────

def explicar_deal(v: Visao, opportunity_id: str) -> Optional[dict]:
    d = consultas.deal(v, opportunity_id)
    if d is None:
        return None
    f = fato_deal(d, completo=True)
    f["prazo"] = _dbr(horizonte(v.data).fim)
    template = (f"Score {f['score']} ({f['acao']}). " + " ".join(f["motivos_do_score"])
                + f" Próximo passo: {f['proximo_passo']}")
    instrucao = (f"Explique ao vendedor, num parágrafo de até 90 palavras, por que este deal tem score {f['score']} e "
                 "a ação recomendada. Use os motivos do score e os alertas. Termine com o próximo passo concreto.")
    return _gerar("explicar_deal", f, instrucao, template)


# ── 3. Pergunte ao pipeline (tool calling) ────────────────────────────────────

_FILTROS = {
    "agente": {"type": "string", "description": "Nome exato do vendedor"},
    "manager": {"type": "string", "description": "Nome exato do manager"},
    "regiao": {"type": "string", "enum": ["Central", "East", "West"]},
}

FERRAMENTAS = [
    {"type": "function", "function": {
        "name": "consultar_pipeline",
        "description": "Deals abertos ordenados por prioridade (ação, depois valor esperado), com score, chance no prazo e próximo passo.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": {
            **_FILTROS, "stage": {"type": "string", "enum": ["Prospecting", "Engaging"]},
            "acao": {"type": "string", "enum": ORDEM_ACOES},
            "limite": {"type": "integer", "description": "Quantos deals (máx. 20)"}}}}},
    {"type": "function", "function": {
        "name": "consultar_deal", "description": "Um deal com score, motivos do score e alertas.",
        "parameters": {"type": "object", "additionalProperties": False, "required": ["opportunity_id"],
                       "properties": {"opportunity_id": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "consultar_emergencia",
        "description": "Meta × fechado × projeção do trimestre e a lista de resgate (deals que fecham o gap).",
        "parameters": {"type": "object", "additionalProperties": False, "properties": _FILTROS}}},
    {"type": "function", "function": {
        "name": "consultar_time",
        "description": "Métricas por vendedor: % da meta, cobertura, carga × capacidade, deals sem conta.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": _FILTROS}}},
    {"type": "function", "function": {
        "name": "consultar_alertas", "description": "Alertas do recorte, do mais grave para o mais leve.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": {
            **_FILTROS, "severidade": {"type": "string", "enum": ["critico", "atencao", "lembrete"]},
            "limite": {"type": "integer", "description": "Quantos alertas (máx. 20)"}}}}},
    {"type": "function", "function": {
        "name": "consultar_winloss",
        "description": "Ganhos e perdas do trimestre até a data, por produto e por vendedor (descritivo, não preditivo).",
        "parameters": {"type": "object", "additionalProperties": False, "properties": _FILTROS}}},
    {"type": "function", "function": {
        "name": "consultar_cross_sell", "description": "Contas que compraram uma série e nunca outra.",
        "parameters": {"type": "object", "additionalProperties": False, "properties": {
            **_FILTROS, "limite": {"type": "integer", "description": "Quantas (máx. 20)"}}}}},
]


def _limite(args: dict) -> int:
    return max(1, min(int(args.pop("limite", 10) or 10), 20))


def _fato_winloss(w: dict) -> dict:
    def linhas(lista):
        return [{"nome": r["nome"], "ganhos": str(r["ganhos"]), "perdas": str(r["perdas"]),
                 "win_rate": _pct(r["win_rate"]), "valor_ganho": usd(r["valor_ganho"])} for r in lista[:10]]
    return {"periodo": f"{_dbr(w['periodo']['inicio'])} a {_dbr(w['periodo']['fim'])}",
            "ganhos": str(w["ganhos"]), "perdas": str(w["perdas"]), "win_rate": _pct(w["win_rate"]),
            "valor_ganho": usd(w["valor_ganho"]),
            "perdas_na_zona_de_risco": f"{w['perdas_na_zona_de_risco']} perdas até o {w['zona_risco_dias']}º dia",
            "por_produto": linhas(w["por_produto"]), "por_vendedor": linhas(w["por_vendedor"])}


def executar_ferramenta(v: Visao, nome: str, args: dict) -> dict:
    """Roda a consulta pedida pelo LLM e devolve fatos JÁ FORMATADOS (a mesma regra:
    o modelo só copia números)."""
    args = {k: val for k, val in (args or {}).items() if val not in (None, "")}
    try:
        if nome == "consultar_pipeline":
            n = _limite(args)
            p = consultas.pipeline(v, limite=n, **args)
            return {"total_deals": str(p["resumo"]["total"]),
                    "valor_esperado_total": usd(p["resumo"]["valor_esperado_total"]),
                    "por_acao": {a: f"{r['n']} deals" for a, r in p["resumo"]["por_acao"].items()},
                    "deals": [fato_deal(d) for d in p["deals"]]}
        if nome == "consultar_deal":
            d = consultas.deal(v, args["opportunity_id"])
            return fato_deal(d, completo=True) if d else {"erro": "deal não encontrado entre os abertos nesta data"}
        if nome == "consultar_emergencia":
            e = consultas.emergencia(v, **args)
            return {**_fato_emergencia(e), "primeiros_da_lista_de_resgate": [fato_deal(d) for d in e["resgate"]["deals"][:10]]}
        if nome == "consultar_time":
            t = consultas.time(v, **args)
            return {"pct_trimestre_decorrido": _pct(t["trimestre"]["pct_decorrido"]),
                    "vendedores": [_fato_vendedor(m) for m in t["vendedores"]]}
        if nome == "consultar_alertas":
            n = _limite(args)
            a = consultas.alertas(v, **args)
            return {"contagem": {k: str(c) for k, c in a["contagem"].items()},
                    "alertas": [_fato_alerta(x) for x in a["alertas"][:n]]}
        if nome == "consultar_winloss":
            return _fato_winloss(consultas.winloss(v, **args))
        if nome == "consultar_cross_sell":
            n = _limite(args)
            cs = consultas.cross_sell(v, limite=n, **args)
            return {"total": str(cs["total"]), "sugestoes": [
                {"conta": s["conta"], "ja_compra": ", ".join(s["series_compradas"]), "oferecer": s["produto_sugerido"],
                 "valor_historico": usd(s["valor_historico"]), "vendedor": s["agente"]} for s in cs["sugestoes"]]}
    except consultas.FiltroInvalido as e:
        return {"erro": str(e)}
    except (KeyError, TypeError, ValueError) as e:
        return {"erro": f"argumentos inválidos: {e}"}
    return {"erro": f"ferramenta desconhecida: {nome}"}


def _contexto_chat(v: Visao) -> str:
    met = v.metricas
    return (f"\n\nContexto: a data de referência é {_dbr(v.data)}; o trimestre fecha em {_dbr(v.trimestre.fim)}. "
            f"Managers: {', '.join(sorted(met.manager.unique()))}. Regiões: Central, East, West. "
            "Use as ferramentas para buscar os fatos antes de responder; nunca responda números de memória. "
            "Se a pergunta não puder ser respondida com as ferramentas, diga isso. Resposta em até 150 palavras.")


def perguntar(v: Visao, pergunta: str, historico: Optional[list] = None) -> dict:
    historico = [m for m in (historico or [])[-6:] if m.get("role") in ("user", "assistant") and m.get("content")]
    if not ia_ativa():
        return {"texto": "A IA não está configurada neste ambiente (LEAD_SCORER_OPENAI_API_KEY). As respostas estão nas "
                         "abas Prioridades, Alertas e Time.", "fonte": "template", "ferramentas": []}

    hoje = date.today().isoformat()
    if _perguntas_hoje.get(hoje, 0) >= config.IA_MAX_PERGUNTAS_DIA:
        return {"texto": "Limite diário de perguntas atingido. Tente amanhã.", "fonte": "template", "ferramentas": []}
    _perguntas_hoje[hoje] = _perguntas_hoje.get(hoje, 0) + 1

    chave = _chave("perguntar", [v.data.date().isoformat(), pergunta, historico])
    if (em_cache := _cache_ler(chave)):
        return {**em_cache, "cache": True}

    mensagens = [{"role": "system", "content": SISTEMA + _contexto_chat(v)}, *historico, {"role": "user", "content": pergunta}]
    fontes, usadas, corrigiu = [pergunta], [], False
    for _ in range(6):  # teto de idas e voltas com ferramentas
        try:
            msg = _chamar(mensagens, max_tokens=800, ferramentas=FERRAMENTAS)
        except Exception as e:
            logger.warning("IA (perguntar) falhou: %s", e)
            _registrar({"funcao": "perguntar", "pergunta": pergunta, "erro": str(e)})
            return {"texto": "Não consegui consultar a IA agora. Tente de novo em instantes.", "fonte": "template", "ferramentas": usadas}

        if msg.tool_calls:
            mensagens.append({"role": "assistant", "content": msg.content, "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in msg.tool_calls]})
            for c in msg.tool_calls:
                try:
                    args = json.loads(c.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = None
                resultado = executar_ferramenta(v, c.function.name, args) if isinstance(args, dict) else {"erro": "argumentos não são JSON válido"}
                texto_resultado = json.dumps(resultado, ensure_ascii=False)
                fontes.append(texto_resultado)
                usadas.append(c.function.name)
                mensagens.append({"role": "tool", "tool_call_id": c.id, "content": texto_resultado})
            continue

        texto = (msg.content or "").strip()
        problemas = problemas_no_texto(texto, "\n".join(fontes))
        _registrar({"funcao": "perguntar", "pergunta": pergunta, "ferramentas": usadas, "resposta": texto, "problemas": problemas})
        if problemas and not corrigiu:
            corrigiu = True
            mensagens += [{"role": "assistant", "content": texto},
                          {"role": "user", "content": "Sua resposta quebrou as regras: " + "; ".join(problemas)
                           + ". Reescreva usando somente números que vieram das ferramentas, copiados exatamente."}]
            continue
        if problemas:
            return {"texto": "Não consegui montar uma resposta confiável para essa pergunta. Tente reformular ou veja as abas "
                             "Prioridades, Alertas e Time.", "fonte": "template", "ferramentas": usadas}
        ids = sorted(set(re.findall(r"\b[0-9A-Z]{8}\b", texto)) & set(v.deals.opportunity_id))
        resultado = {"texto": texto, "fonte": "ia", "modelo": config.LLM_MODELO, "ferramentas": usadas, "deals_citados": ids}
        _cache_gravar(chave, resultado)
        return resultado
    return {"texto": "A pergunta exigiu consultas demais. Tente algo mais específico.", "fonte": "template", "ferramentas": usadas}


# ── 4. Plano de resgate ───────────────────────────────────────────────────────

def plano_resgate(v: Visao, agente: Optional[str] = None, manager: Optional[str] = None) -> dict:
    e = consultas.emergencia(v, agente=agente, manager=manager)
    if not e["ativa"]:
        return {"texto": "Sem modo emergência neste recorte: a projeção bate a meta ou não estamos no último mês do trimestre.",
                "fonte": "template"}
    por_vendedor: dict[str, list] = {}
    for d in e["resgate"]["deals"]:
        por_vendedor.setdefault(d["agente"], []).append({
            "id": d["opportunity_id"], "conta": d.get("conta") or "conta não preenchida", "produto": d["produto"],
            "dias_em_engaging": _dias(d["idade_dias"]), "chance_no_trimestre": _pct(d["prob_trimestre"]),
            "valor_se_fechar": usd(d["valor_liquido"])})
    f = {**_fato_emergencia(e), "deals_por_vendedor": por_vendedor}
    # Template legível: 1 bullet por vendedor (até 8), os 3 primeiros deals de cada
    bullets = [f"- **{vend}**: " + "; ".join(f"{x['conta']} · {x['produto']} ({x['valor_se_fechar']})" for x in deals[:3])
               for vend, deals in list(por_vendedor.items())[:8]]
    resto = len(por_vendedor) - 8
    template = "\n".join(
        [f"Faltam {f['falta_para_a_meta']} em {f['dias_para_fechar_o_trimestre']}. Ordem de ataque por vendedor:", *bullets]
        + ([f"- e mais {resto} vendedores na lista completa da ferramenta."] if resto > 0 else []))
    instrucao = ("Transforme a lista de resgate num plano de ataque por vendedor, em até 220 palavras. Para cada vendedor: "
                 "a ordem dos deals (conta, produto, valor se fechar) e um argumento curto por deal baseado em tempo, prazo "
                 "e valor. Formato: uma linha '**Vendedor**' seguida de bullets '- '. Termine com o próximo passo do manager.")
    return _gerar("plano_resgate", f, instrucao, template, max_tokens=900)


# ── 5. Rascunhos ──────────────────────────────────────────────────────────────

TIPOS_RASCUNHO = {
    "followup": "e-mail de follow-up para o cliente pedindo a decisão, cordial e objetivo",
    "requalificacao": "e-mail para o cliente perguntando se o projeto ainda está de pé e qual o melhor próximo passo",
    "encerramento": "nota INTERNA de encerramento para registrar no CRM (não é para o cliente)",
}


def rascunho(v: Visao, opportunity_id: str, tipo: str) -> Optional[dict]:
    if tipo not in TIPOS_RASCUNHO:
        raise ValueError(f"tipo deve ser um de: {', '.join(TIPOS_RASCUNHO)}")
    d = consultas.deal(v, opportunity_id)
    if d is None:
        return None
    conta = d.get("conta") or "conta não preenchida"
    saudacao = f"Olá, equipe {d['conta']}," if d.get("conta") else "Olá,"
    f = {"tipo": tipo, "conta": conta, "produto": d["produto"], "vendedor": d["agente"],
         "dias_em_engaging": _dias(d.get("idade_dias")), "fim_do_trimestre": _dbr(v.trimestre.fim)}
    templates = {
        "followup": (f"{d['produto']} — próximos passos",
                     f"{saudacao}\n\nRetomando nossa conversa sobre o {d['produto']}: conseguimos avançar com a "
                     f"decisão até {f['fim_do_trimestre']}? Se houver alguma pendência do lado de vocês, me diga o que "
                     f"falta que eu resolvo.\n\nAbraço,\n{d['agente']}"),
        "requalificacao": (f"{d['produto']} — o projeto continua?",
                           f"{saudacao}\n\nFaz um tempo que conversamos sobre o {d['produto']}. O projeto ainda "
                           f"está nos planos de vocês? Se sim, qual seria o melhor próximo passo? Se a prioridade mudou, "
                           f"sem problema — me avise para eu organizar por aqui.\n\nAbraço,\n{d['agente']}"),
        "encerramento": (f"Encerramento — {conta} · {d['produto']}",
                         f"Deal {d['opportunity_id']} encerrado como Lost: {f['dias_em_engaging']} em Engaging, além do "
                         f"maior ciclo já fechado no histórico. Sem resposta de requalificação. Responsável: {d['agente']}."),
    }
    assunto_t, corpo_t = templates[tipo]
    instrucao = (f"Escreva um {TIPOS_RASCUNHO[tipo]}, em até 120 palavras, assinado por {d['agente']}. "
                 + ("" if tipo == "encerramento" else
                    "NÃO mencione score, chance, probabilidade, '138 dias' nem nenhum dado interno da ferramenta. ")
                 + 'Responda em JSON: {"assunto": "...", "corpo": "..."}.')
    r = _gerar("rascunho", f, instrucao, json.dumps({"assunto": assunto_t, "corpo": corpo_t}, ensure_ascii=False),
               json_saida=True)
    try:
        conteudo = json.loads(r["texto"])
        r.update({"assunto": str(conteudo["assunto"]), "corpo": str(conteudo["corpo"])})
    except (json.JSONDecodeError, KeyError, TypeError):
        r.update({"assunto": assunto_t, "corpo": corpo_t, "fonte": "template"})
    r.pop("texto", None)
    return r


# ── 6. Análise de win-loss narrada ────────────────────────────────────────────

def analise_winloss(v: Visao, agente: Optional[str] = None, manager: Optional[str] = None) -> dict:
    w = _fato_winloss(consultas.winloss(v, agente=agente, manager=manager))
    bm = v.bm
    f = {"escopo": agente or manager or "todos os times", **w,
         "regras_do_historico": {
             "ganho_no_ultimo_mes_do_trimestre": _pct(bm.win_fim_trimestre),
             "ganho_nos_outros_meses": _pct(bm.win_fora_trimestre),
             "maior_ciclo_ja_fechado": _dias(bm.ciclo_max_dias),
         },
         "ritmo": [_fato_vendedor(m) for m in consultas.time(v, agente=agente, manager=manager)["vendedores"][:8]]}
    template = "\n".join([
        f"- **Trimestre até agora**: {w['ganhos']} ganhos e {w['perdas']} perdas ({w['win_rate']}), {w['valor_ganho']} fechados.",
        f"- **Perdas cedo**: {w['perdas_na_zona_de_risco']} — follow-up nas primeiras semanas evita parte delas.",
        f"- **Fim de trimestre**: no histórico, {f['regras_do_historico']['ganho_no_ultimo_mes_do_trimestre']} de ganho no "
        f"último mês contra {f['regras_do_historico']['ganho_nos_outros_meses']} nos outros.",
        "- **Próximo passo**: revisar com o time os deals em 'Atacar agora' e limpar os fora do ciclo.",
    ])
    instrucao = ("Escreva de 3 a 5 insights para o manager sobre o trimestre, cada um como bullet '- **Título**: texto' "
                 "(até 35 palavras por bullet). Descreva o que aconteceu (ganhos, perdas, valor, ritmo); não diga que um "
                 "vendedor, produto ou conta 'tem mais chance'. O último bullet é '**Próximo passo**'.")
    return _gerar("winloss", f, instrucao, template, max_tokens=900)
