"""
notifications/config.py
-----------------------
Carrega configurações de email do arquivo .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class EmailConfig:
    enabled:        bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    host:           str  = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    port:           int  = int(os.getenv("EMAIL_PORT", "587"))
    user:           str  = os.getenv("EMAIL_USER", "")
    password:       str  = os.getenv("EMAIL_PASSWORD", "")
    from_name:      str  = os.getenv("EMAIL_FROM_NAME", "Lead Scorer")
    recipient:      str  = os.getenv("ALERT_RECIPIENT", "")
    digest_enabled: bool = os.getenv("DAILY_DIGEST_ENABLED", "true").lower() == "true"
    digest_time:    str  = os.getenv("DAILY_DIGEST_TIME", "08:00")  # HH:MM

    @property
    def is_configured(self) -> bool:
        return bool(self.enabled and self.user and self.password and self.recipient)

    @property
    def from_address(self) -> str:
        return f"{self.from_name} <{self.user}>"


email_config = EmailConfig()