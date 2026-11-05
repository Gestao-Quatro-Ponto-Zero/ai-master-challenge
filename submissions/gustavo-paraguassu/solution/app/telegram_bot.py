"""Adaptador Telegram: o cliente fala com o bot no privado; os atendentes trabalham num grupo
com Tópicos, um tópico por fila + "Triagem humana". Toda a decisão fica em engine.py.

Rodar (de dentro de solution/):  python -m app.telegram_bot
Comandos no grupo de atendentes:  /configurar   (uma vez: cria os tópicos)
                                  /rodada P1    (teste com colegas: ver experiment/PROTOCOLO.md)
"""
import asyncio
import difflib
import html
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from telegram import ForceReply, InlineKeyboardButton as B, InlineKeyboardMarkup as KB, ReplyParameters, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler,
                          filters)

from . import config, engine, pii
from .engine import CONTEUDO, FILAS, Motor
from .store import Estado, Ticket, agora, evento

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("bot")

ORDEM = list(FILAS)                 # índice estável para callback_data (limite de 64 bytes)
MSG = CONTEUDO["mensagens"]
LIMITE_DIARIO = 30                  # mensagens por cliente por dia que passam pelo LLM (custo/abuso)
estado = Estado()
motor: Motor | None = None
uso_diario: dict = defaultdict(int)
e = html.escape


def quem(update: Update) -> str:
    return pii.anonimo(update.effective_user.id) if update.effective_user else "?"


def nome_atendente(update: Update) -> str:
    u = update.effective_user
    return e(u.first_name) if u else "atendente"


def exp_campos(t: Ticket) -> dict:
    return {"exp_" + k: v for k, v in (t.exp or {}).items()}


# ------------------------------------------------------------------------------------------- card
def card_html(t: Ticket, destino: str, nota: str = "") -> str:
    d, tri = t.decisao or {}, t.triagem or {}
    sem = bool(t.exp and t.exp["modo"] == "sem")
    linhas = [f"<b>{t.id}</b>" + (f" · 🧪 {e(t.exp['participante'])} · modo {'SEM' if sem else 'COM'} assistente"
                                   if t.exp else "")]
    if nota:
        linhas.append(nota)
    if not sem:
        f = FILAS[t.fila]
        linhas.append(f"{f['topico']} · confiança {d['conf']:.0%} (limiar {d['limiar']:.0%})")
        if destino == "triagem" and not t.exp:
            linhas.append("🔎 <b>Escolha a fila.</b> Sugestões: " +
                          ", ".join(f"{e(FILAS[q]['nome_pt'])} {p:.0%}" for q, p in d["top3"]))
        if d.get("motivos"):
            linhas.append("⚠️ " + e("; ".join(d["motivos"])))
        linhas.append(f"<i>Resumo:</i> {e(tri.get('resumo_pt', ''))}")
        campos = {k: v for k, v in tri.get("campos", {}).items() if v}
        if campos:
            linhas.append("<b>Campos</b>\n" + "\n".join(f"• {e(k)}: {e(str(v))}" for k, v in campos.items()))
        falta = engine.faltando(t.fila, tri.get("campos", {}))
        if falta:
            linhas.append("❓ Ainda falta: " + e(", ".join(falta)))
    linhas.append("<b>Mensagem do cliente</b>\n<blockquote>" + e("\n".join(t.mensagens)) + "</blockquote>")
    if sem:
        linhas.append("Escolha a fila e depois escreva a resposta ao cliente.")
    elif destino == "fila" or t.exp:
        linhas.append("<b>Resposta sugerida</b> (conteúdo aprovado)\n<blockquote>" + e(t.rascunho) + "</blockquote>")
    return "\n\n".join(linhas)[:4000]


def teclado_filas(t: Ticket) -> KB:
    bt = [B(FILAS[q]["topico"], callback_data=f"fil|{t.id}|{i}") for i, q in enumerate(ORDEM)]
    return KB([bt[i:i + 2] for i in range(0, len(bt), 2)])


def teclado_card(t: Ticket, destino: str) -> KB:
    if t.exp and t.exp["modo"] == "sem":
        return teclado_filas(t)
    if destino == "triagem" and not t.exp:
        top = [B(f"➡️ {FILAS[q]['nome_pt']} {p:.0%}", callback_data=f"fil|{t.id}|{ORDEM.index(q)}")
               for q, p in t.decisao["top3"]]
        return KB([top, [B("🔀 Outra fila", callback_data=f"out|{t.id}")]])
    return KB([[B("✅ Enviar", callback_data=f"env|{t.id}"), B("✏️ Editar", callback_data=f"edt|{t.id}"),
                B("🔀 Outra fila", callback_data=f"out|{t.id}")]])


async def postar_card(ctx, t: Ticket, destino: str, nota: str = ""):
    if t.exp:
        thread = estado.topicos[f"exp:{t.exp['participante']}"]
    else:
        thread = estado.topicos["triagem" if destino == "triagem" else t.fila]
    msg = await ctx.bot.send_message(estado.grupo, card_html(t, destino, nota), parse_mode=ParseMode.HTML,
                                     reply_markup=teclado_card(t, destino), message_thread_id=thread)
    t.card = {"chat": estado.grupo, "msg": msg.message_id, "thread": thread, "postado": agora(), "destino": destino}
    t.inicio_atendimento = t.inicio_atendimento or t.card["postado"]
    t.status = "com_atendente"
    evento("card_postado", t.id, destino=destino, fila=t.fila, **exp_campos(t))
    estado.salvar()


async def fechar_card(ctx, t: Ticket, rodape: str):
    """Tira os botões do card e registra o que aconteceu com ele."""
    try:  # pode já estar sem botões (modo sem assistente): não pode impedir o rodapé
        await ctx.bot.edit_message_reply_markup(t.card["chat"], t.card["msg"], reply_markup=None)
    except Exception as ex:
        log.info("fechar_card %s (botões): %s", t.id, ex)
    try:
        await ctx.bot.send_message(t.card["chat"], rodape, parse_mode=ParseMode.HTML,
                                   message_thread_id=t.card["thread"],
                                   reply_parameters=ReplyParameters(message_id=t.card["msg"]))
    except Exception as ex:  # card antigo apagado etc.: não pode derrubar o fluxo
        log.warning("fechar_card %s: %s", t.id, ex)


# ------------------------------------------------------------------------------------ cliente
def teclado_humano(t_id: str) -> KB:
    return KB([[B("🙋 Falar com uma pessoa", callback_data=f"hum|{t_id}")]])


async def triar(ctx, t: Ticket):
    """Roda o núcleo e executa a decisão: perguntar, responder sozinho ou mandar para atendente."""
    await ctx.bot.send_chat_action(t.chat_cliente, ChatAction.TYPING)
    tri, meta, d = await asyncio.to_thread(motor.processar, "\n".join(t.mensagens), t.perguntou, t.forcar_humano)
    t.triagem, t.decisao, t.rascunho, t.fila = tri.model_dump(), d.to_dict(), d.rascunho, d.fila
    evento("triado", t.id, fila=d.fila, conf=round(d.conf, 3), limiar=d.limiar, destino=d.destino,
           motivos=d.motivos, faltando=d.faltando, vai_perguntar=bool(d.pergunta), auto=d.auto,
           riscos=tri.sinais_de_risco, discordancia_llm=d.discordancia_llm, llm_fonte=meta.get("fonte"),
           llm_modelo=meta.get("model"), custo_usd=meta.get("custo_usd"), latencia_llm_s=meta.get("latencia_s"))
    if d.pergunta:
        t.status, t.perguntou = "aguardando_cliente", True
        await ctx.bot.send_message(t.chat_cliente, d.pergunta, reply_markup=teclado_humano(t.id))
        evento("pergunta_enviada", t.id, campos=d.faltando)
    elif d.auto:
        t.status = "auto_respondido"
        await ctx.bot.send_message(t.chat_cliente, CONTEUDO["respostas_automaticas"][d.auto]["texto"],
                                   reply_markup=KB([[B("✅ Resolveu", callback_data=f"faq|{t.id}|1"),
                                                     B("🙋 Falar com um atendente", callback_data=f"faq|{t.id}|0")]]))
        evento("resposta_automatica", t.id, tipo=d.auto)
    else:
        await postar_card(ctx, t, d.destino)
        await confirmar(ctx, t, d.destino)
    estado.salvar()


async def confirmar(ctx, t: Ticket, destino: str):
    f = FILAS[t.fila]
    txt = (MSG["confirmacao_fila"].format(ticket=t.id, equipe=f["nome_pt"], prazo=f["prazo"]) if destino == "fila"
           else MSG["confirmacao_triagem"].format(ticket=t.id))
    await ctx.bot.send_message(t.chat_cliente, txt)
    evento("confirmacao_enviada", t.id, destino=destino)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = estado.aberto_do_cliente(update.effective_chat.id)
    extra = ""
    if t and t.status in ("respondido", "auto_respondido", "aguardando_cliente", "confirmando_reabertura"):
        evento("encerrado", t.id, motivo="start", status_anterior=t.status)
        t.status = "fechado"
        estado.salvar()
    elif t and t.status == "com_atendente":
        extra = f"\n\n(O chamado {t.id} continua aberto com a equipe.)"
    await update.message.reply_text(MSG["boas_vindas"] + extra, reply_markup=teclado_humano("-"))
    evento("start", cliente=quem(update))


async def cmd_configurar_privado(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/configurar é para o grupo de atendentes: me adicione lá como administrador "
                                    "e mande o comando no grupo.")


async def novo_ticket(ctx, chat: int, cliente: str, texto: str, responder):
    chave = (chat, date.today().isoformat())
    uso_diario[chave] += 1
    if uso_diario[chave] > LIMITE_DIARIO:
        return await responder("Você atingiu o limite de chamados de hoje. Tente amanhã.")
    t = Ticket(id=estado.novo_id(), chat_cliente=chat, cliente=cliente, mensagens=[texto])
    if chat in estado.humano_proximo:
        estado.humano_proximo.remove(chat)
        t.forcar_humano = True
    estado.tickets[t.id] = t
    evento("ticket_criado", t.id, canal="telegram", cliente=t.cliente, chars=len(texto), pediu_humano=t.forcar_humano)
    await triar(ctx, t)


async def reabrir(ctx, t: Ticket, texto: str):
    t.mensagens.append(texto)
    evento("reaberto", t.id, fila=t.fila, confirmado_pelo_cliente=True)
    t.inicio_atendimento = None
    await ctx.bot.send_message(t.chat_cliente, MSG["reaberto"].format(ticket=t.id))
    await postar_card(ctx, t, "fila", nota=f"🔁 <b>REABERTO</b> pelo cliente. Nova mensagem: {e(texto)}")


async def msg_cliente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    texto = pii.mascarar(update.message.text or "")
    if not texto.strip():
        return
    if not estado.grupo:
        return await update.message.reply_text("O suporte ainda não foi configurado (falta o /configurar no grupo).")
    t = estado.aberto_do_cliente(chat)
    if t and t.status == "aguardando_cliente":
        t.mensagens.append(texto)
        evento("cliente_respondeu", t.id, chars=len(texto))
        return await triar(ctx, t)
    if t and t.status == "com_atendente":
        t.mensagens.append(texto)
        evento("mensagem_adicional", t.id, chars=len(texto))
        await ctx.bot.send_message(estado.grupo, f"💬 <b>{t.id}</b>, nova mensagem do cliente:\n<blockquote>{e(texto)}"
                                   "</blockquote>", parse_mode=ParseMode.HTML, message_thread_id=t.card["thread"])
        estado.salvar()
        return
    if t and t.status == "auto_respondido":
        t.mensagens.append(texto)
        evento("faq_nao_resolvido", t.id, via="mensagem")
        await postar_card(ctx, t, "fila", nota="🙋 Depois da resposta automática, o cliente escreveu de novo.")
        return await confirmar(ctx, t, "fila")
    if t and t.status == "confirmando_reabertura":       # escreveu de novo sem clicar: junta na pendência
        t.pendente = f"{t.pendente}\n{texto}" if t.pendente else texto
        return estado.salvar()
    if t and t.status == "respondido" and t.respondido_em and \
            datetime.now(timezone.utc) - datetime.fromisoformat(t.respondido_em) < timedelta(hours=config.REABRIR_HORAS):
        # Reabertura é métrica (H9): só conta se o cliente disser que é o mesmo assunto.
        t.status, t.pendente = "confirmando_reabertura", texto
        resumo = (t.triagem or {}).get("resumo_pt", "")[:80]
        await update.message.reply_text(
            f"É sobre o chamado {t.id} ({resumo}) ou é um assunto novo?",
            reply_markup=KB([[B(f"🔁 Sobre o {t.id}", callback_data=f"reab|{t.id}"),
                              B("🆕 Assunto novo", callback_data=f"novo|{t.id}")]]))
        return estado.salvar()
    await novo_ticket(ctx, chat, quem(update), texto, update.message.reply_text)


async def msg_nao_texto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por enquanto eu só leio texto. Pode descrever em uma mensagem?")


# ------------------------------------------------------------------------------------ botões
async def botao(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    acao, tid, *arg = q.data.split("|")
    if acao == "hum" and tid == "-":
        if q.message.chat.id not in estado.humano_proximo:
            estado.humano_proximo.append(q.message.chat.id)
        estado.salvar()
        evento("pediu_humano", None, cliente=quem(update), antes_de_descrever=True)
        return await q.edit_message_text(MSG["pedir_descricao_humano"])
    t = estado.tickets.get(tid)
    if t is None:
        return await q.edit_message_text("Este chamado não existe mais.")
    if acao in ("env", "edt", "out", "fil") and t.status != "com_atendente":
        return await q.answer("Este chamado já foi tratado.")

    if acao == "hum":                                    # cliente pediu pessoa durante a pergunta
        await q.edit_message_reply_markup(None)
        if t.status == "aguardando_cliente":
            evento("pediu_humano", t.id, durante="pergunta")
            t.decisao["motivos"] = t.decisao.get("motivos", []) + ["cliente pediu atendente"]
            await postar_card(ctx, t, "triagem", nota="🙋 Cliente pediu atendente antes de responder a pergunta.")
            await confirmar(ctx, t, "triagem")
    elif acao == "faq":                                  # resposta automática resolveu?
        await q.edit_message_reply_markup(None)
        if arg[0] == "1":
            evento("faq_resolvido", t.id)
            t.status, t.respondido_em = "respondido", agora()
            await pedir_csat(ctx, t)
        else:
            evento("faq_nao_resolvido", t.id)
            await postar_card(ctx, t, "fila", nota="🙋 A resposta automática não resolveu; cliente pediu atendente.")
            await confirmar(ctx, t, "fila")
    elif acao in ("reab", "novo"):
        if t.status != "confirmando_reabertura":
            return await q.edit_message_reply_markup(None)
        texto, t.pendente = t.pendente or "", None
        if acao == "reab":
            await q.edit_message_text(f"Certo, é sobre o {t.id}.")
            await reabrir(ctx, t, texto)
        else:
            evento("encerrado", t.id, motivo="cliente_abriu_assunto_novo")
            t.status = "fechado"
            await q.edit_message_text("Certo, vou abrir um chamado novo.")
            await novo_ticket(ctx, t.chat_cliente, t.cliente, texto, q.message.reply_text)
        estado.salvar()
    elif acao == "csat":
        evento("csat", t.id, nota=int(arg[0]), fila=t.fila)
        await q.edit_message_text(f"{MSG['obrigado_csat']} ({arg[0]}/5)")
    elif acao == "env":
        await finalizar(ctx, update, t, t.rascunho, editado=False)
    elif acao == "edt":
        p = await ctx.bot.send_message(estado.grupo, f"✏️ <b>{t.id}</b>: <b>responda a esta mensagem</b> com o texto "
                                       f"final para o cliente. Sugestão:\n<code>{e(t.rascunho)}</code>",
                                       parse_mode=ParseMode.HTML, message_thread_id=t.card["thread"],
                                       reply_markup=ForceReply(selective=False, input_field_placeholder="Texto final"))
        estado.prompts[str(p.message_id)] = t.id
        evento("edicao_iniciada", t.id, por=quem(update), **exp_campos(t))
        estado.salvar()
    elif acao == "out":
        await q.edit_message_reply_markup(teclado_filas(t))
        evento("outra_fila_aberta", t.id, por=quem(update), **exp_campos(t))
    elif acao == "fil":
        await escolher_fila(ctx, update, t, ORDEM[int(arg[0])])


async def escolher_fila(ctx, update: Update, t: Ticket, nova: str):
    antiga, origem = t.fila, t.card["destino"]
    por = quem(update)
    if t.exp and t.exp["modo"] == "sem":                 # experimento sem assistente: escolhe e digita
        t.fila = nova
        evento("fila_escolhida", t.id, fila=nova, por=por, **exp_campos(t))
        await ctx.bot.edit_message_reply_markup(t.card["chat"], t.card["msg"], reply_markup=None)
        p = await ctx.bot.send_message(estado.grupo, f"✏️ <b>{t.id}</b> → {e(FILAS[nova]['nome_pt'])}. "
                                       "<b>Responda a esta mensagem</b> com o texto para o cliente.",
                                       parse_mode=ParseMode.HTML, message_thread_id=t.card["thread"],
                                       reply_markup=ForceReply(selective=False, input_field_placeholder="Resposta"))
        estado.prompts[str(p.message_id)] = t.id
        return estado.salvar()
    tipo = "fila_definida" if origem == "triagem" else "transferido"
    evento(tipo, t.id, de=antiga, para=nova, sugestao_modelo=t.decisao["fila"],
           aceitou_sugestao=nova == t.decisao["fila"], por=por, **exp_campos(t))
    t.fila, t.rascunho = nova, engine.rascunho(nova, (t.triagem or {}).get("campos", {}))
    await fechar_card(ctx, t, f"➡️ {nome_atendente(update)} enviou para <b>{e(FILAS[nova]['nome_pt'])}</b>.")
    await postar_card(ctx, t, "fila", nota=f"{'🔎 Fila definida na triagem' if tipo == 'fila_definida' else '🔀 Transferido'}"
                      f" (de {e(FILAS[antiga]['nome_pt'])}).")


async def finalizar(ctx, update: Update, t: Ticket, texto: str, editado: bool):
    seg = (datetime.now(timezone.utc) - datetime.fromisoformat(t.inicio_atendimento)).total_seconds()
    sim = round(difflib.SequenceMatcher(None, t.rascunho, texto).ratio(), 3)
    evento("resposta_enviada", t.id, editado=editado, similaridade_rascunho=sim, segundos_atendimento=round(seg, 1),
           fila=t.fila, por=quem(update), **exp_campos(t))
    await fechar_card(ctx, t, f"✅ {nome_atendente(update)} respondeu em {seg:.0f}s"
                      f"{' (editado)' if editado else ''}.")
    if t.exp:
        t.status = "respondido"
        estado.rodadas[t.exp["participante"]]["i"] += 1
        estado.salvar()
        return await proximo_cenario(ctx, t.exp["participante"])
    await ctx.bot.send_message(t.chat_cliente, texto)
    t.status, t.respondido_em = "respondido", agora()
    await pedir_csat(ctx, t)
    estado.salvar()


async def pedir_csat(ctx, t: Ticket):
    await ctx.bot.send_message(t.chat_cliente, MSG["csat"].format(ticket=t.id), reply_markup=KB(
        [[B(str(n), callback_data=f"csat|{t.id}|{n}") for n in range(1, 6)]]))
    evento("csat_pedido", t.id)
    estado.salvar()


async def resposta_atendente(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Atendente respondeu a um pedido de texto (Editar, ou modo sem assistente)."""
    alvo = update.message.reply_to_message
    tid = estado.prompts.pop(str(alvo.message_id), None) if alvo else None
    if not tid or tid not in estado.tickets or estado.tickets[tid].status != "com_atendente":
        return
    await finalizar(ctx, update, estado.tickets[tid], update.message.text, editado=True)


# ------------------------------------------------------------------------------- grupo / setup
async def cmd_configurar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if estado.grupo and estado.grupo != chat.id:
        return await update.message.reply_text("Já estou configurado em outro grupo. Para trocar, apague "
                                               "solution/runtime/estado.json e reinicie.")
    if not chat.is_forum:
        return await update.message.reply_text("Ative os Tópicos do grupo (Editar grupo → Tópicos) e me torne "
                                               "administrador com permissão de gerenciar tópicos. Depois, /configurar.")
    estado.grupo = chat.id
    for chave, nome in [("triagem", "🔎 Triagem humana")] + [(q, FILAS[q]["topico"]) for q in ORDEM]:
        if chave not in estado.topicos:
            estado.topicos[chave] = (await ctx.bot.create_forum_topic(chat.id, nome)).message_thread_id
    estado.salvar()
    evento("grupo_configurado", None, topicos=len(estado.topicos))
    await update.message.reply_text("Pronto: um tópico por fila + Triagem humana. Os chamados chegam aqui.")


async def cmd_rodada(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/rodada P1: 16 cenários do Dataset 2, alternando COM e SEM assistente (contrabalanceado)."""
    if update.effective_chat.id != estado.grupo or not ctx.args:
        return await update.message.reply_text("Use no grupo de atendentes: /rodada P1")
    p = ctx.args[0].upper()[:8]
    n = int("".join(c for c in p if c.isdigit()) or 1)
    cen = json.loads(config.SCENARIOS_PATH.read_text())
    a, b = cen[:8], cen[8:16]
    com, sem = (a, b) if n % 2 else (b, a)          # participante ímpar: COM no bloco A; par: COM no bloco B
    pares = [(com[i], sem[i]) for i in range(8)]
    seq = [x for c, s in pares for x in ((c, "com"), (s, "sem"))[:: (1 if n % 2 else -1)]]
    chave = f"exp:{p}"
    if chave not in estado.topicos:
        estado.topicos[chave] = (await ctx.bot.create_forum_topic(estado.grupo, f"🧪 Experimento {p}")).message_thread_id
    estado.rodadas[p] = {"seq": [[c["id"], m] for c, m in seq], "i": 0}
    estado.salvar()
    evento("rodada_iniciada", None, participante=p, n=len(seq))
    await ctx.bot.send_message(estado.grupo, f"🧪 Rodada <b>{e(p)}</b>: 16 chamados, um por vez. Em metade você tem "
                               "o assistente (fila sugerida + campos + resposta pronta); na outra, só a mensagem. "
                               "Trabalhe no seu ritmo normal: o tempo de cada chamado é medido.",
                               parse_mode=ParseMode.HTML, message_thread_id=estado.topicos[chave])
    await proximo_cenario(ctx, p)


async def proximo_cenario(ctx, p: str):
    r = estado.rodadas[p]
    if r["i"] >= len(r["seq"]):
        evento("rodada_concluida", None, participante=p)
        return await ctx.bot.send_message(estado.grupo, f"🏁 Rodada {e(p)} concluída. Obrigado!",
                                          message_thread_id=estado.topicos[f"exp:{p}"])
    cid, modo = r["seq"][r["i"]]
    c = next(x for x in json.loads(config.SCENARIOS_PATH.read_text()) if x["id"] == cid)
    t = Ticket(id=f"{p}-{cid}", chat_cliente=None, cliente="experimento", mensagens=[c["texto_pt"]],
               exp={"participante": p, "modo": modo, "cenario": cid, "fila_verdadeira": c["fila_verdadeira"],
                    "ordem": r["i"] + 1})
    tri, meta, d = await asyncio.to_thread(motor.processar, c["texto_pt"], True)
    t.triagem, t.decisao, t.rascunho, t.fila = tri.model_dump(), d.to_dict(), d.rascunho, d.fila
    estado.tickets[t.id] = t
    evento("triado", t.id, fila=d.fila, conf=round(d.conf, 3), destino=d.destino, motivos=d.motivos,
           llm_fonte=meta.get("fonte"), **exp_campos(t))
    await postar_card(ctx, t, d.destino)


async def erro(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.exception("erro no handler", exc_info=ctx.error)
    evento("erro", None, tipo=type(ctx.error).__name__, detalhe=str(ctx.error)[:300])


def main():
    global motor
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Defina TELEGRAM_BOT_TOKEN no .env (crie o bot com o @BotFather).")
    motor = Motor()
    log.info("LLM: %s (%s)", "OFFLINE/cache" if config.OFFLINE else config.LLM_MODEL, config.LLM_EFFORT)
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    privado, grupo = filters.ChatType.PRIVATE, filters.ChatType.GROUPS
    app.add_handler(CommandHandler("start", cmd_start, filters=privado))
    app.add_handler(CommandHandler("configurar", cmd_configurar, filters=grupo))
    app.add_handler(CommandHandler("configurar", cmd_configurar_privado, filters=privado))
    app.add_handler(CommandHandler("rodada", cmd_rodada, filters=grupo))
    app.add_handler(MessageHandler(privado & filters.TEXT & ~filters.COMMAND, msg_cliente))
    app.add_handler(MessageHandler(privado & ~filters.TEXT & ~filters.COMMAND, msg_nao_texto))
    app.add_handler(MessageHandler(grupo & filters.REPLY & filters.TEXT & ~filters.COMMAND, resposta_atendente))
    app.add_handler(CallbackQueryHandler(botao))
    app.add_error_handler(erro)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
