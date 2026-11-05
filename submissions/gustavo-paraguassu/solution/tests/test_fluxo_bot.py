"""Teste de ponta a ponta do bot, sem Telegram e sem chave de API.

Um "Telegram falso" registra cada mensagem/clique; as mensagens do cliente são os cenários do
experimento (triagem em cache). Cobre: /configurar, pergunta ao cliente, modo degradado (texto
novo sem LLM), Enviar, CSAT, Outra fila, Editar, reabertura e uma rodada inteira do experimento.

Uso (de dentro de solution/):  python -m tests.test_fluxo_bot
"""
import asyncio
import json
import os
import sys
import tempfile
from itertools import count
from types import SimpleNamespace as NS

os.environ["OFFLINE"] = "1"
os.environ["RUNTIME_DIR"] = tempfile.mkdtemp(prefix="bot_teste_")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "teste")

from app import config, telegram_bot as tb  # noqa: E402
from app.engine import Motor  # noqa: E402

GRUPO, CLIENTE = -100123, 555
ids = count(1000)


class Bot:
    def __init__(self):
        self.enviadas = []

    async def send_message(self, chat_id, text, **kw):
        m = NS(message_id=next(ids), chat_id=chat_id, text=text, **kw)
        self.enviadas.append(m)
        return m

    async def edit_message_reply_markup(self, *a, **kw):
        pass

    async def send_chat_action(self, *a, **kw):
        pass

    async def create_forum_topic(self, chat_id, name):
        return NS(message_thread_id=next(ids), name=name)

    def ultima(self, chat):
        return [m for m in self.enviadas if m.chat_id == chat][-1]


bot = Bot()
ctx = NS(bot=bot, args=[], error=None)


class Msg:
    def __init__(self, chat, text, reply_to=None):
        self.chat, self.text, self.reply_to_message = chat, text, reply_to

    async def reply_text(self, text, **kw):
        return await bot.send_message(self.chat, text, **kw)


def upd(chat, text=None, user=7, forum=False, reply_to=None, data=None):
    q = None
    if data:
        q = NS(data=data, message=NS(chat=NS(id=chat)))
        q.answer = lambda *a, **k: asyncio.sleep(0)
        q.edit_message_text = lambda *a, **k: asyncio.sleep(0)
        q.edit_message_reply_markup = lambda *a, **k: asyncio.sleep(0)
    return NS(effective_chat=NS(id=chat, is_forum=forum), effective_user=NS(id=user, first_name="Ana"),
              message=Msg(chat, text, reply_to), callback_query=q)


def botoes(m):
    return [b.callback_data for linha in m.reply_markup.inline_keyboard for b in linha]


def card_do(tid):
    return next(m for m in reversed(bot.enviadas) if m.chat_id == GRUPO and m.text.startswith(f"<b>{tid}</b>"))


async def main():
    tb.motor = Motor()
    cen = json.loads(config.SCENARIOS_PATH.read_text())

    await tb.cmd_configurar(upd(GRUPO, "/configurar", forum=True), ctx)
    assert len(tb.estado.topicos) == 9, tb.estado.topicos

    # 1) cliente manda um cenário; se o bot perguntar algo, responde (texto novo -> sem LLM, modo degradado)
    await tb.msg_cliente(upd(CLIENTE, cen[0]["texto_pt"]), ctx)
    t = tb.estado.aberto_do_cliente(CLIENTE)
    if t.status == "aguardando_cliente":
        await tb.msg_cliente(upd(CLIENTE, "é isso mesmo, desde ontem"), ctx)
    if t.status == "auto_respondido":
        await tb.botao(upd(CLIENTE, data=f"faq|{t.id}|0"), ctx)
    assert t.status == "com_atendente", t.status
    card = card_do(t.id)
    if "env|" not in " ".join(botoes(card)):                    # foi para a triagem: escolhe a 1ª sugestão
        await tb.botao(upd(GRUPO, data=botoes(card)[0]), ctx)
        card = card_do(t.id)
    await tb.botao(upd(GRUPO, data=f"env|{t.id}"), ctx)
    assert t.status == "respondido"
    await tb.botao(upd(CLIENTE, data=f"csat|{t.id}|4"), ctx)
    # clique duplo no Enviar não reenvia
    n = len(bot.enviadas)
    await tb.botao(upd(GRUPO, data=f"env|{t.id}"), ctx)
    assert len(bot.enviadas) == n
    # cliente volta a escrever dentro de 48h -> reabre
    await tb.msg_cliente(upd(CLIENTE, "voltou a acontecer"), ctx)
    assert t.status == "com_atendente"
    # o card reaberto está numa fila: transferir para outra gera o evento "transferido"
    outra = next(q for q in tb.ORDEM if q != t.fila)
    await tb.botao(upd(GRUPO, data=f"out|{t.id}"), ctx)
    await tb.botao(upd(GRUPO, data=f"fil|{t.id}|{tb.ORDEM.index(outra)}"), ctx)
    assert t.fila == outra
    await tb.botao(upd(GRUPO, data=f"env|{t.id}"), ctx)

    # 2) outro cliente: Outra fila -> escolhe -> Editar -> responde com texto próprio
    await tb.msg_cliente(upd(CLIENTE + 1, cen[1]["texto_pt"], user=8), ctx)
    t2 = tb.estado.aberto_do_cliente(CLIENTE + 1)
    if t2.status == "aguardando_cliente":
        await tb.botao(upd(CLIENTE + 1, data=f"hum|{t2.id}"), ctx)    # pede pessoa em vez de responder
    if t2.status == "auto_respondido":
        await tb.botao(upd(CLIENTE + 1, data=f"faq|{t2.id}|0"), ctx)
    await tb.botao(upd(GRUPO, data=f"out|{t2.id}"), ctx)
    await tb.botao(upd(GRUPO, data=f"fil|{t2.id}|{tb.ORDEM.index('Storage')}"), ctx)
    assert t2.fila == "Storage"
    await tb.botao(upd(GRUPO, data=f"edt|{t2.id}"), ctx)
    pedido = bot.ultima(GRUPO)
    await tb.resposta_atendente(upd(GRUPO, "Oi! Já liberei, confere aí?", reply_to=NS(message_id=pedido.message_id)), ctx)
    assert t2.status == "respondido" and bot.ultima(CLIENTE + 1).text.startswith("Como foi")

    # 3) rodada do experimento: COM -> Enviar; SEM -> escolhe a fila verdadeira e digita
    ctx.args = ["P1"]
    await tb.cmd_rodada(upd(GRUPO, "/rodada P1", forum=True), ctx)
    for _ in range(16):
        r = tb.estado.rodadas["P1"]
        cid, modo = r["seq"][r["i"]]
        tx = tb.estado.tickets[f"P1-{cid}"]
        if modo == "com":
            await tb.botao(upd(GRUPO, data=f"env|{tx.id}"), ctx)
        else:
            await tb.botao(upd(GRUPO, data=f"fil|{tx.id}|{tb.ORDEM.index(tx.exp['fila_verdadeira'])}"), ctx)
            pedido = bot.ultima(GRUPO)
            await tb.resposta_atendente(upd(GRUPO, "Recebido, vamos tratar.", reply_to=NS(message_id=pedido.message_id)), ctx)
    assert tb.estado.rodadas["P1"]["i"] == 16
    assert "concluída" in bot.ultima(GRUPO).text

    eventos = [json.loads(x) for x in open(config.RUNTIME / "eventos.jsonl")]
    tipos = {}
    for ev in eventos:
        tipos[ev["evento"]] = tipos.get(ev["evento"], 0) + 1
    print("eventos:", tipos)
    for obrig in ["grupo_configurado", "ticket_criado", "triado", "card_postado", "resposta_enviada", "csat",
                  "reaberto", "transferido", "rodada_concluida"]:
        assert obrig in tipos, obrig
    assert not any(ev["evento"] == "erro" for ev in eventos)
    print(f"OK: fluxo completo sem Telegram nem API. Eventos em {config.RUNTIME / 'eventos.jsonl'}")
    return config.RUNTIME


if __name__ == "__main__":
    rt = asyncio.run(main())
    if "--manter" in sys.argv:
        print(rt)
