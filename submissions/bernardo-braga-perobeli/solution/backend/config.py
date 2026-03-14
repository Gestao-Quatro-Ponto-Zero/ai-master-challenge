import os
from pathlib import Path
import hashlib
from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parent
_env_file = _backend_dir / ".env"
if not _env_file.exists():
    _env_file = _backend_dir / ".env.example"
load_dotenv(_env_file)

PROJECT_NAME = "G4 IA - Inteligência de Suporte"
PROJECT_VERSION = "2.0.0"

BASE_DIR = Path(__file__).resolve().parent.parent
DATASETS_DIR = BASE_DIR / "Datasets"
CACHE_DIR = BASE_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

DATASET1_PATH = DATASETS_DIR / "customer_support_tickets.csv"
DATASET2_PATH = DATASETS_DIR / "all_tickets_processed_improved_v3.csv"

# --- Gemini ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GEMINI_LLM_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-2-preview"
GEMINI_EMBEDDING_DIMENSIONS = 768
RAG_TOP_K = 5
DUPLICATE_THRESHOLD = 0.90
RAG_BATCH_SIZE = 100
RAG_MAX_CORPUS = int(os.environ.get("RAG_MAX_CORPUS", "56500"))

TOPIC_LABELS = [
    "Hardware",
    "Suporte RH",
    "Acesso / Login",
    "Diversos",
    "Armazenamento",
    "Compras",
    "Projeto Interno",
    "Direitos Administrativos",
]

TOPIC_LABELS_EN = [
    "Hardware",
    "HR Support",
    "Access",
    "Miscellaneous",
    "Storage",
    "Purchase",
    "Internal Project",
    "Administrative rights",
]

LABEL_MAP_EN_TO_PT = dict(zip(TOPIC_LABELS_EN, TOPIC_LABELS))

SEVERITY_RULES = {
    "critical_keywords": [
        "urgente", "crítico", "emergência", "fora do ar", "indisponível",
        "falha de segurança", "perda de dados", "servidor caiu", "não funciona",
        "bloqueado", "não consigo acessar", "produção", "falha no sistema",
        "hackeado", "comprometido",
        "urgent", "critical", "emergency", "down", "outage", "security breach",
        "data loss", "server crash", "not working", "blocked", "cannot access",
        "production", "system failure", "hack", "compromised",
    ],
    "medium_keywords": [
        "lento", "intermitente", "erro", "bug", "problema", "defeito",
        "atraso", "timeout", "degradado", "parcial",
        "slow", "intermittent", "error", "bug", "issue", "problem",
        "malfunction", "delay", "timeout", "degraded", "partial",
    ],
}

SEVERITY_THRESHOLDS = {
    "confidence_high": 0.70,
    "confidence_low": 0.40,
}

ALERT_THRESHOLDS = {
    "medio_por_dia": 50,
    "critico_por_dia": 10,
}

# --- Fallback (DeBERTa + sentence-transformers, usado quando Gemini não disponível) ---
CLASSIFIER_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

JWT_SECRET = "g4-ia-suporte-secret-key-2026"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


USERS = {
    "agente1@g4suporte.com": {
        "nome": "Carlos Silva",
        "senha_hash": _hash_pw("agente123"),
        "perfil": "agente",
    },
    "agente2@g4suporte.com": {
        "nome": "Ana Costa",
        "senha_hash": _hash_pw("agente123"),
        "perfil": "agente",
    },
    "agente3@g4suporte.com": {
        "nome": "Pedro Santos",
        "senha_hash": _hash_pw("agente123"),
        "perfil": "agente",
    },
    "gestor@g4suporte.com": {
        "nome": "Fernanda Lima",
        "senha_hash": _hash_pw("gestor123"),
        "perfil": "gestor",
    },
    "diretor@g4suporte.com": {
        "nome": "Roberto Mendes",
        "senha_hash": _hash_pw("diretor123"),
        "perfil": "diretor",
    },
}
