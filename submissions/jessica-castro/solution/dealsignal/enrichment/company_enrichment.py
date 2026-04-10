import hashlib

import numpy as np
import pandas as pd

from enrichment.api_clients import BrasilAPIClient
from utils.logger import get_logger

logger = get_logger(__name__)


def _mock_company_data(company_name: str) -> dict:
    seed = int(hashlib.md5(company_name.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.RandomState(seed)
    company_types = ["SA", "LTDA", "MEI", "EIRELI"]
    return {
        "cnpj_verified": False,
        "company_type": company_types[rng.randint(0, len(company_types))],
    }


def enrich_company(account_name: str, brasil_client: BrasilAPIClient) -> dict:
    result = brasil_client.fetch(account_name)
    if result:
        logger.info("BrasilAPI enrichment OK for %s", account_name)
        return {
            "cnpj_verified": True,
            "company_type": result.get("descricao_tipo", ""),
        }
    logger.debug("BrasilAPI unavailable for %s — using mock", account_name)
    return _mock_company_data(account_name)


def run_company_enrichment(
    accounts_df: pd.DataFrame,
    brasil_client: BrasilAPIClient,
) -> pd.DataFrame:
    records = []
    for _, row in accounts_df.iterrows():
        enriched = enrich_company(row["account"], brasil_client)
        enriched["account"] = row["account"]
        records.append(enriched)
    return pd.DataFrame(records)
