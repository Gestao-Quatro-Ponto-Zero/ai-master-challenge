"""Cron job entry point for Railway — executa o pipeline e termina.

Uso no Railway:
  1. Service Settings → Cron Schedule → "0 9 * * 1" (seg 09:00 UTC)
  2. Start Command: python cron_runner.py
"""

import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cron")


def main():
    logger.info("=" * 50)
    logger.info("Cron: Pipeline semanal de churn")
    result = subprocess.run(
        [sys.executable, "run.py", "--config", "config/ravenstack.yaml", "--output", "output"],
        capture_output=True, text=True,
    )
    logger.info("Saída:\n%s", result.stdout)
    if result.returncode != 0:
        logger.error("Erro:\n%s", result.stderr)
        sys.exit(1)
    logger.info("Pipeline concluído com sucesso!")


if __name__ == "__main__":
    main()
