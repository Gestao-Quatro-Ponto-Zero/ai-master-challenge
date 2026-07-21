from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "ravenstack.db"

REQUIRED_TABLES = {
    "accounts",
    "subscriptions",
    "feature_usage",
    "support_tickets",
    "churn_events",
}

DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
