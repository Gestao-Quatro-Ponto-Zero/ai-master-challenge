from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração por variáveis de ambiente com prefixo G4_ (ex.: G4_JWT_SECRET)."""

    model_config = SettingsConfigDict(env_prefix="G4_", env_file=".env", extra="ignore")

    artifact_dir: Path = Path("artifacts")
    data_dir: Path = Path("data")          # usado só pelo job de retreino (o treinamento lê daqui)
    db_path: Path = Path("var/app.db")
    jwt_secret: str = "dev-secret-troque-em-producao-0123456789"
    jwt_ttl_minutes: int = 480
    show_probability: bool = True          # mostra p_win ("Chance"); o front avisa se a calibração ainda não é útil
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    rate_limit_per_minute: int = 120       # /score/what-if e rotas de escrita
