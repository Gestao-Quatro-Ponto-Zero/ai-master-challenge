"""Configuração do pipeline, lida de variáveis de ambiente (ou do .env na raiz do monorepo)."""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

MONOREPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=MONOREPO_ROOT / ".env", extra="ignore")

    supabase_url: str
    supabase_secret_key: SecretStr
    database_url: SecretStr

    kaggle_mcp_url: str = "https://www.kaggle.com/mcp"
    kaggle_dataset: str = "rivalytics/saas-subscription-and-churn-analytics-dataset"
    kaggle_mcp_token: SecretStr | None = None

    raw_bucket: str = "raw"
    batch_size: int = 5000
