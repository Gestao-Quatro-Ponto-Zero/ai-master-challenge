import json
import duckdb
from pathlib import Path

from agno.tools import Toolkit

GOLD_DIR = Path(__file__).resolve().parents[2] / "data/gold"
PLAYBOOK = Path(__file__).resolve().parents[2] / "docs/02-product/04-playbook-cs.md"

METRIC_SQL = {
    "mrr_lost": "SUM(mrr_lost)",
    "churn_count": "SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END)",
    "avg_error_rate": "AVG(error_rate)",
    "avg_satisfaction_score": "AVG(avg_satisfaction_score)",
    "avg_resolution_time": "AVG(avg_resolution_time)",
}

CATEGORY_MAP = {
    "baixo_engajamento": "Categoria 1",
    "problemas_tecnicos": "Categoria 2",
    "experiencia_suporte": "Categoria 3",
    "sinal_downgrade": "Categoria 4",
    "alto_risco_combinado": "Categoria 5",
    "churn_confirmado": "Categoria 6",
}


class ChurnTools(Toolkit):
    def __init__(self):
        super().__init__(name="churn_tools")
        self.register(self.query_risk_accounts)
        self.register(self.query_churn_drivers)
        self.register(self.query_dashboard_fact)
        self.register(self.lookup_cs_playbook)
        self.register(self.detect_anomaly)

    def _conn(self) -> duckdb.DuckDBPyConnection:
        conn = duckdb.connect()
        tables = [
            "gold_dashboard_fact",
            "gold_account_risk",
            "gold_churn_drivers",
            "gold_feature_retention",
            "gold_support_health",
        ]
        for t in tables:
            path = GOLD_DIR / f"{t}.parquet"
            conn.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{path}')")
        return conn

    def query_risk_accounts(self, tier: str = "high", limit: int = 10) -> str:
        """Retorna contas ativas com risco de churn do nível especificado (low/medium/high/critical), ordenadas por MRR decrescente. Inclui sinais individuais e ação recomendada pelo CS."""
        try:
            conn = self._conn()
            rows = conn.execute(
                """
                SELECT account_id, account_name, industry, country,
                       mrr, risk_score, risk_tier,
                       signal_low_usage, signal_high_errors,
                       signal_bad_support, signal_downgrade,
                       days_since_last_usage, open_tickets,
                       last_satisfaction_score, recommended_action
                FROM gold_account_risk
                WHERE risk_tier = ?
                ORDER BY mrr DESC
                LIMIT ?
                """,
                [tier, limit],
            ).fetchall()
            cols = [
                "account_id", "account_name", "industry", "country",
                "mrr", "risk_score", "risk_tier",
                "signal_low_usage", "signal_high_errors",
                "signal_bad_support", "signal_downgrade",
                "days_since_last_usage", "open_tickets",
                "last_satisfaction_score", "recommended_action",
            ]
            total = conn.execute(
                "SELECT COUNT(*) FROM gold_account_risk WHERE risk_tier = ?", [tier]
            ).fetchone()[0]
            accounts = [dict(zip(cols, r)) for r in rows]
            return json.dumps({"accounts": accounts, "total_no_tier": total}, default=str)
        except Exception as e:
            return json.dumps({"erro": str(e)})

    def query_churn_drivers(self, segment_type: str, year_month: str = None) -> str:
        """Retorna drivers de churn por segmento (industry/country/channel/plan) para um período. Se year_month=None, agrega todos os períodos. Inclui churn_rate, MRR perdido e reason_code predominante."""
        try:
            conn = self._conn()
            if year_month:
                rows = conn.execute(
                    """
                    SELECT segment_value,
                           SUM(churned_accounts) AS churned_accounts,
                           SUM(total_accounts)   AS total_accounts,
                           AVG(churn_rate)        AS churn_rate,
                           SUM(mrr_lost)          AS mrr_lost,
                           MAX(top_reason_code)   AS top_reason_code
                    FROM gold_churn_drivers
                    WHERE segment_type = ?
                      AND year_month   = ?
                    GROUP BY segment_value
                    ORDER BY churn_rate DESC
                    """,
                    [segment_type, year_month],
                ).fetchall()
                period = year_month
            else:
                rows = conn.execute(
                    """
                    SELECT segment_value,
                           SUM(churned_accounts) AS churned_accounts,
                           SUM(total_accounts)   AS total_accounts,
                           AVG(churn_rate)        AS churn_rate,
                           SUM(mrr_lost)          AS mrr_lost,
                           MAX(top_reason_code)   AS top_reason_code
                    FROM gold_churn_drivers
                    WHERE segment_type = ?
                    GROUP BY segment_value
                    ORDER BY churn_rate DESC
                    """,
                    [segment_type],
                ).fetchall()
                period = "all"
            cols = ["segment_value", "churned_accounts", "total_accounts",
                    "churn_rate", "mrr_lost", "top_reason_code"]
            rankings = [dict(zip(cols, r)) for r in rows]
            return json.dumps(
                {"segment_type": segment_type, "period": period, "rankings": rankings},
                default=str,
            )
        except Exception as e:
            return json.dumps({"erro": str(e)})

    def query_dashboard_fact(self, sql: str) -> str:
        """Executa SQL analítico nas gold tables. Tabelas disponíveis: gold_dashboard_fact, gold_account_risk, gold_churn_drivers, gold_feature_retention, gold_support_health. Use para análises cruzadas entre tabelas."""
        MUTATING = {"INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "COPY", "ATTACH"}
        sql_upper = sql.upper()
        for kw in MUTATING:
            if kw in sql_upper:
                return json.dumps({"erro": "Apenas SELECT permitido"})

        if "LIMIT" not in sql_upper:
            sql = sql.rstrip("; \n") + " LIMIT 200"

        try:
            conn = self._conn()
            rel = conn.execute(sql)
            cols = [d[0] for d in rel.description]
            rows = rel.fetchall()
            results = [dict(zip(cols, r)) for r in rows]
            payload = json.dumps(
                {"sql_executado": sql, "linhas_retornadas": len(results), "resultados": results},
                default=str,
            )
            if len(payload) > 8000:
                payload = payload[:8000] + '... [truncado]"}'
            return payload
        except Exception as e:
            # Build schema hint
            try:
                conn2 = self._conn()
                schema_lines = []
                for t in ["gold_dashboard_fact", "gold_account_risk", "gold_churn_drivers",
                          "gold_feature_retention", "gold_support_health"]:
                    cols_info = conn2.execute(f"DESCRIBE {t}").fetchall()
                    schema_lines.append(f"{t}: " + ", ".join(f"{c[0]}({c[1]})" for c in cols_info))
                dica = "\n".join(schema_lines)
            except Exception:
                dica = "Não foi possível carregar schemas."
            return json.dumps({"erro": str(e), "dica": dica})

    def lookup_cs_playbook(self, category: str) -> str:
        """Consulta o playbook de CS para uma categoria de problema. DEVE ser chamada antes de qualquer recomendação de retenção. Categorias: baixo_engajamento, problemas_tecnicos, experiencia_suporte, sinal_downgrade, alto_risco_combinado, churn_confirmado."""
        try:
            text = PLAYBOOK.read_text(encoding="utf-8")
            target = CATEGORY_MAP.get(category)
            if not target:
                return text
            sections = text.split("---")
            for section in sections:
                if target in section:
                    return section.strip()
            return text
        except Exception as e:
            return json.dumps({"erro": str(e)})

    def detect_anomaly(self, metric: str, year_month: str) -> str:
        """Compara uma métrica do período com a média histórica dos 6 meses anteriores. Métricas válidas: mrr_lost, churn_count, avg_error_rate, avg_satisfaction_score, avg_resolution_time. Sinaliza desvio >= 20%."""
        if metric not in METRIC_SQL:
            return json.dumps({"erro": f"Métrica inválida. Use: {list(METRIC_SQL.keys())}"})
        agg_expr = METRIC_SQL[metric]
        try:
            conn = self._conn()
            current = conn.execute(
                f"SELECT {agg_expr} FROM gold_dashboard_fact WHERE year_month = ?",
                [year_month],
            ).fetchone()[0]

            hist_avg = conn.execute(
                f"""
                SELECT AVG(period_val) FROM (
                    SELECT year_month, {agg_expr} AS period_val
                    FROM gold_dashboard_fact
                    WHERE year_month < ?
                      AND year_month >= strftime(
                            CAST(? || '-01' AS DATE) - INTERVAL 6 MONTH,
                            '%Y-%m')
                    GROUP BY year_month
                ) sub
                """,
                [year_month, year_month],
            ).fetchone()[0]

            if hist_avg is None or hist_avg == 0:
                deviation_pct = None
                is_anomaly = False
                interpretation = "Histórico insuficiente para comparação."
            else:
                deviation_pct = round((current - hist_avg) / hist_avg * 100, 2)
                is_anomaly = abs(deviation_pct) >= 20
                direction = "acima" if deviation_pct > 0 else "abaixo"
                interpretation = (
                    f"{metric} em {year_month} está {abs(deviation_pct):.1f}% {direction} "
                    f"da média dos 6 meses anteriores ({hist_avg:.2f}). "
                    + ("Anomalia detectada — requer atenção imediata." if is_anomaly else "Dentro do intervalo normal.")
                )

            return json.dumps(
                {
                    "metric": metric,
                    "period": year_month,
                    "current_value": current,
                    "historical_avg_6m": hist_avg,
                    "deviation_pct": deviation_pct,
                    "is_anomaly": is_anomaly,
                    "interpretation": interpretation,
                },
                default=str,
            )
        except Exception as e:
            return json.dumps({"erro": str(e)})
