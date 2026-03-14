import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from enrichment.api_clients import BuiltWithClient, SimilarwebClient
from enrichment.company_enrichment import run_company_enrichment, BrasilAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)


def _mock_digital_data(company_name: str) -> dict:
    seed = int(hashlib.md5(company_name.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.RandomState(seed)
    tech_stack_count = int(rng.randint(3, 40))
    return {
        "digital_maturity_index": float(rng.beta(2, 5)),
        "digital_presence_score": float(rng.beta(2, 5)),
        "tech_stack_count": tech_stack_count,
        "uses_modern_stack": bool(tech_stack_count > 20),
        "website_traffic_estimate": int(np.exp(rng.normal(10, 1.5))),
        "enrichment_source": "mock",
    }


def _parse_builtwith(data: dict) -> dict:
    try:
        techs = data.get("Results", [{}])[0].get("Result", {}).get("Paths", [{}])[0].get("Technologies", [])
        count = len(techs)
        return {
            "digital_maturity_index": min(count / 50, 1.0),
            "tech_stack_count": count,
            "uses_modern_stack": count > 20,
            "enrichment_source": "builtwith",
        }
    except Exception:
        return {}


def _parse_similarweb(data: dict) -> dict:
    try:
        rank = data.get("similar_rank", {}).get("rank", 10_000_000)
        score = max(0.0, 1.0 - rank / 10_000_000)
        traffic = max(0, int(10_000_000 / max(rank, 1)))
        return {
            "digital_presence_score": score,
            "website_traffic_estimate": traffic,
            "enrichment_source": "similarweb",
        }
    except Exception:
        return {}


def enrich_digital(
    company_name: str,
    builtwith_client: BuiltWithClient,
    similarweb_client: SimilarwebClient,
) -> dict:
    mock = _mock_digital_data(company_name)
    domain = company_name.lower().replace(" ", "") + ".com"

    bw_data = builtwith_client.fetch(domain)
    if bw_data:
        parsed = _parse_builtwith(bw_data)
        if parsed:
            mock.update(parsed)
            logger.info("BuiltWith enrichment OK for %s", company_name)

    sw_data = similarweb_client.fetch(domain)
    if sw_data:
        parsed = _parse_similarweb(sw_data)
        if parsed:
            mock.update(parsed)
            logger.info("Similarweb enrichment OK for %s", company_name)

    return mock


def run_enrichment(
    accounts_df: pd.DataFrame,
    output_path: str,
    force: bool = False,
) -> pd.DataFrame:
    output = Path(output_path)
    if output.exists() and not force:
        logger.info("Enriched accounts cache found at %s — skipping enrichment", output_path)
        return pd.read_csv(output_path)

    logger.info("Starting enrichment for %d accounts", len(accounts_df))

    brasil_client = BrasilAPIClient()
    builtwith_client = BuiltWithClient()
    similarweb_client = SimilarwebClient()

    company_df = run_company_enrichment(accounts_df, brasil_client)

    digital_records = []
    for _, row in accounts_df.iterrows():
        digital = enrich_digital(row["account"], builtwith_client, similarweb_client)
        digital["account"] = row["account"]
        digital_records.append(digital)
    digital_df = pd.DataFrame(digital_records)

    enriched = accounts_df.merge(company_df, on="account", how="left")
    enriched = enriched.merge(digital_df, on="account", how="left")

    output.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(output_path, index=False)
    logger.info("Saved enriched accounts to %s", output_path)
    return enriched
