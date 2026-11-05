"""Configuração única. Tudo vem de variáveis de ambiente (ou do .env, que não vai para o git)."""
import os
from pathlib import Path

from dotenv import load_dotenv

SOLUTION = Path(__file__).resolve().parents[1]          # solution/
load_dotenv(SOLUTION.parent / ".env")

MODEL_PATH = Path(os.getenv("ROUTER_MODEL_PATH", SOLUTION / "models" / "router.joblib"))
CONTENT_PATH = SOLUTION / "app" / "conteudo_aprovado.json"
RUNTIME = Path(os.getenv("RUNTIME_DIR", SOLUTION / "runtime"))  # tickets, eventos, estado do bot
CACHE_DIR = SOLUTION / "outputs" / "llm_cache"                  # respostas do LLM (reprodutível sem chave)
SCENARIOS_PATH = SOLUTION / "experiment" / "cenarios.json"

LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")
LLM_EFFORT = os.getenv("LLM_EFFORT", "low")
# Sem chave, ou OFFLINE=1: usa só o cache; se não houver cache, segue sem LLM (modo degradado).
OFFLINE = os.getenv("OFFLINE", "0") == "1" or not os.getenv("ANTHROPIC_API_KEY")

# Trava de filas sensíveis (ver solution/analysis/04_cost_of_error.py): decisão de apetite a risco.
G_SENS = float(os.getenv("G_SENS", "0.05"))
# Abaixo desta confiança, a fila é incerta demais até para fazer perguntas sobre ela.
MIN_CONF_PERGUNTAR = 0.5
REABRIR_HORAS = 48

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
