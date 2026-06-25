"""
notifications/digest.py
-----------------------
Scheduler do resumo diário — envia email no horário configurado em .env.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from .config import email_config
from .sender import send_daily_digest

logger = logging.getLogger(__name__)


class DigestScheduler:

    def __init__(self):
        self._task   = None
        self._loader = None
        self._running = False

    def setup(self, loader) -> None:
        self._loader = loader

    async def start(self) -> None:
        if not email_config.digest_enabled or not email_config.is_configured:
            logger.info("DigestScheduler desativado (EMAIL_ENABLED=false ou credenciais ausentes).")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(f"DigestScheduler iniciado — envio diário às {email_config.digest_time}.")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        await asyncio.sleep(5)
        while self._running:
            secs = self._seconds_until_digest()
            logger.info(f"Próximo digest em {secs // 3600}h {(secs % 3600) // 60}min.")
            await asyncio.sleep(secs)
            if self._running:
                await self._send_digest()

    def _seconds_until_digest(self) -> int:
        now = datetime.now()
        hour, minute = map(int, email_config.digest_time.split(":"))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return int((target - now).total_seconds())

    async def _send_digest(self) -> None:
        if not self._loader:
            return
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_sync)
        except Exception as e:
            logger.error(f"DigestScheduler erro: {e}")

    def _send_sync(self) -> None:
        from scoring.engine import score_pipeline
        from alerts.queue import get_alerts_for_user

        pipeline = self._loader.get_active_pipeline()
        metrics  = self._loader.metrics

        if len(pipeline) == 0:
            return

        scored = score_pipeline(pipeline, metrics)

        summary = {
            "total":          len(scored),
            "hot":            int((scored["tier"] == "hot").sum()),
            "warm":           int((scored["tier"] == "warm").sum()),
            "cold":           int((scored["tier"] == "cold").sum()),
            "pipeline_value": float(scored["close_value"].fillna(0).sum()),
        }

        top_deals = scored.head(5).to_dict(orient="records")

        try:
            alerts = get_alerts_for_user({"role": "admin", "id": "system"}, include_dismissed=False)
            alerts_count = len(alerts)
        except Exception:
            alerts_count = 0

        success = send_daily_digest(summary, top_deals, alerts_count)
        if success:
            logger.info(f"Digest enviado para {email_config.recipient}.")

    async def send_now(self) -> bool:
        if not self._loader:
            return False
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sync)
        return True


digest_scheduler = DigestScheduler()