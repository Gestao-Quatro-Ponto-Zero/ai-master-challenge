"""Estado do protótipo (tickets e configuração do grupo) e o log de eventos que mede H9.

Cada clique e cada mensagem vira uma linha em runtime/eventos.jsonl, com horário. É daí que saem
tempo de primeira resposta, transferências, reaberturas, edições e CSAT (experiment/analisar.py).
Nada de texto do cliente vai para o log sem máscara de PII, e o cliente aparece só como hash.
"""
import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from . import config

_lock = threading.Lock()


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def evento(nome: str, ticket: str | None = None, **dados):
    config.RUNTIME.mkdir(parents=True, exist_ok=True)
    linha = {"ts": agora(), "evento": nome, "ticket": ticket, **dados}
    with _lock, open(config.RUNTIME / "eventos.jsonl", "a") as f:
        f.write(json.dumps(linha, ensure_ascii=False, default=str) + "\n")


@dataclass
class Ticket:
    id: str
    chat_cliente: int | None          # None em ticket de experimento (não há cliente real)
    cliente: str                      # hash
    status: str = "novo"              # novo | aguardando_cliente | auto_respondido | com_atendente | respondido | confirmando_reabertura | fechado
    mensagens: list = field(default_factory=list)  # texto mascarado
    perguntou: bool = False
    forcar_humano: bool = False
    fila: str | None = None           # fila atual do card
    triagem: dict | None = None
    decisao: dict | None = None
    rascunho: str = ""
    card: dict | None = None          # {"chat": id, "msg": id, "thread": id, "postado": ts}
    inicio_atendimento: str | None = None  # 1º card desta rodada de atendimento (o tempo conta daqui)
    respondido_em: str | None = None
    exp: dict | None = None           # {"participante", "modo": com|sem, "cenario", "fila_verdadeira"}
    pendente: str | None = None       # mensagem aguardando o cliente dizer se é o mesmo assunto


class Estado:
    def __init__(self):
        self.path = config.RUNTIME / "estado.json"
        d = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.grupo: int | None = d.get("grupo")
        self.topicos: dict = d.get("topicos", {})          # fila|triagem|exp:P1 -> thread id
        self.tickets: dict[str, Ticket] = {k: Ticket(**v) for k, v in d.get("tickets", {}).items()}
        self.prompts: dict = d.get("prompts", {})          # msg id do pedido de texto -> ticket id
        self.rodadas: dict = d.get("rodadas", {})          # participante -> {"fila": [...], "i": n}
        self.humano_proximo: list = d.get("humano_proximo", [])  # clientes que pediram pessoa antes de descrever
        self.seq: int = d.get("seq", 0)

    def salvar(self):
        config.RUNTIME.mkdir(parents=True, exist_ok=True)
        d = {"grupo": self.grupo, "topicos": self.topicos, "prompts": self.prompts, "rodadas": self.rodadas,
             "humano_proximo": self.humano_proximo, "seq": self.seq,
             "tickets": {k: asdict(v) for k, v in self.tickets.items()}}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1, default=str))
        tmp.replace(self.path)

    def novo_id(self, prefixo="T") -> str:
        self.seq += 1
        return f"{prefixo}{self.seq:04d}"

    def aberto_do_cliente(self, chat: int) -> Ticket | None:
        abertos = [t for t in self.tickets.values() if t.chat_cliente == chat and t.exp is None]
        return max(abertos, key=lambda t: t.id) if abertos else None
