"""
Armazenamento em memória para o protótipo G4 IA - Inteligência de Suporte.
Gerencia tickets, agentes, alertas e contadores sem dependências externas.
"""

from datetime import datetime, timedelta
from collections import defaultdict
from schemas import (
    DetalheTicket, StatusTicket, NivelSeveridade,
    InfoAgente, StatusAgente, InfoAlerta,
)
import uuid


class BancoDados:
    def __init__(self):
        self.tickets: dict[str, DetalheTicket] = {}
        self.agentes: dict[str, InfoAgente] = {}
        self.alertas: list[InfoAlerta] = []
        self._contadores: dict[str, int] = defaultdict(int)

    # --- Tickets ---

    def adicionar_ticket(self, ticket: DetalheTicket) -> DetalheTicket:
        self.tickets[ticket.id] = ticket
        self._contadores[f"severidade:{ticket.severidade.value}"] += 1
        self._contadores[f"categoria:{ticket.categoria}"] += 1
        self._contadores["total"] += 1
        self.recalcular_cargas_agentes()
        return ticket

    def obter_ticket(self, ticket_id: str) -> DetalheTicket | None:
        return self.tickets.get(ticket_id)

    def listar_tickets(
        self,
        status: StatusTicket | None = None,
        severidade: NivelSeveridade | None = None,
        nome_agente: str | None = None,
        limite: int = 50,
        offset: int = 0,
    ) -> list[DetalheTicket]:
        resultado = list(self.tickets.values())
        if status:
            resultado = [t for t in resultado if t.status == status]
        if severidade:
            resultado = [t for t in resultado if t.severidade == severidade]
        if nome_agente:
            resultado = [t for t in resultado if t.agente_responsavel == nome_agente]

        ordem = {NivelSeveridade.CRITICO: 0, NivelSeveridade.MEDIO: 1, NivelSeveridade.BAIXO: 2}
        resultado.sort(key=lambda t: (ordem.get(t.severidade, 9), t.criado_em))
        return resultado[offset: offset + limite]

    def atualizar_status_ticket(
        self, ticket_id: str, status: StatusTicket, nome_agente: str | None = None
    ) -> DetalheTicket | None:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return None
        ticket.status = status
        if nome_agente:
            ticket.agente_responsavel = nome_agente
        if status == StatusTicket.RESOLVIDO:
            ticket.resolvido_em = datetime.utcnow()
        self.recalcular_cargas_agentes()
        return ticket

    # --- Agentes ---

    def definir_status_agente(self, nome: str, status: StatusAgente) -> InfoAgente:
        if nome in self.agentes:
            self.agentes[nome].status = status
            self.agentes[nome].ultimo_acesso = datetime.utcnow()
        else:
            self.agentes[nome] = InfoAgente(
                nome=nome,
                status=status,
                tickets_atribuidos=0,
                ultimo_acesso=datetime.utcnow(),
            )
        self.recalcular_cargas_agentes()
        return self.agentes[nome]

    def obter_agentes_online(self) -> list[InfoAgente]:
        return [a for a in self.agentes.values() if a.status != StatusAgente.OFFLINE]

    def atribuir_ticket_agente(self, nome_agente: str) -> None:
        self.recalcular_cargas_agentes()

    def recalcular_cargas_agentes(self) -> None:
        carga_aberta = defaultdict(int)
        for ticket in self.tickets.values():
            if (
                ticket.agente_responsavel
                and ticket.status != StatusTicket.RESOLVIDO
            ):
                carga_aberta[ticket.agente_responsavel] += 1

        for nome, agente in self.agentes.items():
            agente.tickets_atribuidos = carga_aberta.get(nome, 0)

    # --- Alertas ---

    def adicionar_alerta(self, tipo: str, mensagem: str, severidade: NivelSeveridade, contagem: int, limite: int) -> InfoAlerta:
        alerta = InfoAlerta(
            id=str(uuid.uuid4())[:8],
            tipo=tipo,
            mensagem=mensagem,
            severidade=severidade,
            contagem=contagem,
            limite=limite,
            disparado_em=datetime.utcnow(),
        )
        self.alertas.append(alerta)
        return alerta

    def obter_alertas(self, apenas_ativos: bool = False) -> list[InfoAlerta]:
        if apenas_ativos:
            return [a for a in self.alertas if not a.reconhecido]
        return list(self.alertas)

    # --- Métricas ---

    def obter_metricas(self, periodo: str = "dia") -> dict:
        agora = datetime.utcnow()
        if periodo == "dia":
            corte = agora - timedelta(days=1)
        elif periodo == "semana":
            corte = agora - timedelta(weeks=1)
        else:
            corte = agora - timedelta(days=30)

        filtrados = [t for t in self.tickets.values() if t.criado_em >= corte]
        por_severidade = defaultdict(int)
        por_status = defaultdict(int)
        por_categoria = defaultdict(int)
        horas_resolucao = []
        auto_resolvidos = 0

        for t in filtrados:
            por_severidade[t.severidade.value] += 1
            por_status[t.status.value] += 1
            por_categoria[t.categoria] += 1
            if t.severidade == NivelSeveridade.BAIXO and t.status == StatusTicket.RESOLVIDO:
                auto_resolvidos += 1
            if t.resolvido_em and t.criado_em:
                delta = (t.resolvido_em - t.criado_em).total_seconds() / 3600
                horas_resolucao.append(delta)

        total = len(filtrados)
        return {
            "periodo": periodo,
            "total_tickets": total,
            "por_severidade": dict(por_severidade),
            "por_status": dict(por_status),
            "por_categoria": dict(por_categoria),
            "tempo_medio_resolucao_horas": (sum(horas_resolucao) / len(horas_resolucao)) if horas_resolucao else None,
            "auto_resolvidos": auto_resolvidos,
            "pct_auto_resolvidos": (auto_resolvidos / total * 100) if total > 0 else 0,
        }

    def obter_top_motivos(self, periodo: str = "dia", severidade: str = "todos") -> list[dict]:
        agora = datetime.utcnow()
        if periodo == "dia":
            corte = agora - timedelta(days=1)
        elif periodo == "semana":
            corte = agora - timedelta(weeks=1)
        else:
            corte = agora - timedelta(days=30)

        filtrados = [t for t in self.tickets.values() if t.criado_em >= corte]
        if severidade != "todos":
            filtrados = [t for t in filtrados if t.severidade.value == severidade]

        contagem_cat = defaultdict(int)
        for t in filtrados:
            contagem_cat[t.categoria] += 1

        total = sum(contagem_cat.values())
        motivos = []
        for cat, qtd in sorted(contagem_cat.items(), key=lambda x: -x[1]):
            motivos.append({
                "categoria": cat,
                "quantidade": qtd,
                "percentual": round(qtd / total * 100, 1) if total > 0 else 0,
            })
        return motivos

    def verificar_limites_alerta(self, limites: dict) -> list[InfoAlerta]:
        metricas = self.obter_metricas("dia")
        novos_alertas = []
        por_sev = metricas["por_severidade"]

        qtd_medio = por_sev.get("medio", 0)
        qtd_critico = por_sev.get("critico", 0)

        if qtd_medio >= limites.get("medio_por_dia", 50):
            alerta = self.adicionar_alerta(
                "volume_medio",
                f"Volume de tickets médios atingiu {qtd_medio} (limite: {limites['medio_por_dia']})",
                NivelSeveridade.MEDIO,
                qtd_medio,
                limites["medio_por_dia"],
            )
            novos_alertas.append(alerta)

        if qtd_critico >= limites.get("critico_por_dia", 10):
            alerta = self.adicionar_alerta(
                "volume_critico",
                f"Volume de tickets críticos atingiu {qtd_critico} (limite: {limites['critico_por_dia']})",
                NivelSeveridade.CRITICO,
                qtd_critico,
                limites["critico_por_dia"],
            )
            novos_alertas.append(alerta)

        return novos_alertas


db = BancoDados()
