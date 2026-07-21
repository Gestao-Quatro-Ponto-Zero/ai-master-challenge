import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from config import DATABASE_PATH, REQUIRED_TABLES
from services.database_service import get_connection, validate_database
from services.risk_service import get_risk_accounts


class RavenStackAppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_database_exists_and_tables_exist(self):
        self.assertTrue(DATABASE_PATH.exists())
        validate_database()
        with get_connection() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        self.assertTrue(REQUIRED_TABLES.issubset(tables))

    def test_can_read_all_tables(self):
        with get_connection() as connection:
            for table in REQUIRED_TABLES:
                total = connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                self.assertGreater(total, 0)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    def test_kpis_have_no_infinite_values(self):
        response = self.client.get("/api/kpis")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()["data"]
        self.assertGreater(data["total_accounts"], 0)
        for value in data.values():
            if isinstance(value, (int, float)):
                self.assertFalse(math.isinf(value))

    def test_risk_score_bounds(self):
        rows = get_risk_accounts({})
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertGreaterEqual(row["risk_score"], 0)
            self.assertLessEqual(row["risk_score"], 100)
            self.assertGreaterEqual(row["value_score"], 0)
            self.assertLessEqual(row["value_score"], 100)

    def test_missing_account_returns_404(self):
        response = self.client.get("/api/accounts/ACCOUNT_DOES_NOT_EXIST")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.get_json()["success"])

    def test_invalid_filter_is_controlled(self):
        response = self.client.get("/api/kpis?unknown_filter=x")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
