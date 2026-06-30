"""
alerts/scheduler.py
-------------------
Job em background que roda a detecção de alertas periodicamente.

Usa asyncio para não bloquear o servidor FastAPI.
O intervalo padrão é 15 minutos — configurável via ALERT_INTERVAL_MINUTES.

Integração com o lifespan do FastAPI:
    O scheduler é iniciado no startup e parado no shutdown.
"""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Intervalo entre rodadas de detecção (em segundos)
ALERT_INTERVAL_SECONDS = 15 * 60  # 15 minutos


class AlertScheduler:
    """
    Scheduler assíncrono para detecção periódica de alertas.
    Mantém referência ao loader para acessar o pipeline atualizado.
    """

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._loader = None
        self._running = False

    def setup(self, loader) -> None:
        """Injeta o loader após o FastAPI inicializar os dados."""
        self._loader = loader

    async def start(self) -> None:
        """Inicia o loop de detecção em background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("AlertScheduler iniciado.")

    async def stop(self) -> None:
        """Para o scheduler graciosamente."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlertScheduler parado.")

    async def _loop(self) -> None:
        """
        Loop principal: roda detecção imediatamente no startup,
        depois a cada ALERT_INTERVAL_SECONDS.
        """
        # Aguarda o loader estar pronto (startup do FastAPI)
        await asyncio.sleep(3)

        while self._running:
            await self._run_detection()
            await asyncio.sleep(ALERT_INTERVAL_SECONDS)

    async def _run_detection(self) -> None:
        """Executa a detecção em thread separada para não bloquear o event loop."""
        if not self._loader:
            logger.warning("Scheduler: loader não configurado, pulando detecção.")
            return

        try:
            # Roda em thread pool para não bloquear o event loop com pandas
            loop = asyncio.get_event_loop()
            added = await loop.run_in_executor(None, self._detect_sync)
            logger.info(
                f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] "
                f"Detecção concluída: {added} novos alertas."
            )
        except Exception as e:
            logger.error(f"Scheduler: erro na detecção: {e}")

    def _detect_sync(self) -> int:
        """Lógica síncrona de detecção — chamada via executor."""
        from .detector import detect_all_alerts
        from .queue import save_alerts, purge_old_alerts

        # Limpa alertas antigos antes de adicionar novos
        purge_old_alerts()

        pipeline = self._loader.pipeline
        metrics  = self._loader.metrics

        alerts = detect_all_alerts(pipeline, metrics)
        return save_alerts(alerts)

    async def run_now(self) -> int:
        """Força uma rodada de detecção imediata. Usado pela rota /api/alerts/refresh."""
        if not self._loader:
            return 0
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._detect_sync)


# Instância global — compartilhada entre main.py e router
scheduler = AlertScheduler()
