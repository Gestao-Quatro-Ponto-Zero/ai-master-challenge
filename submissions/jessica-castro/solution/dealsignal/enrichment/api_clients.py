import os
from typing import Optional

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils.logger import get_logger

logger = get_logger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "DealSignal/1.0"})
TIMEOUT = (3, 10)


def _retry_decorator():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
        reraise=False,
    )


class BrasilAPIClient:
    BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"

    def fetch(self, cnpj: str) -> Optional[dict]:
        try:
            resp = SESSION.get(f"{self.BASE_URL}/{cnpj}", timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            logger.debug("BrasilAPI returned %s for %s", resp.status_code, cnpj)
            return None
        except Exception as e:
            logger.debug("BrasilAPI error for %s: %s", cnpj, e)
            return None


class BuiltWithClient:
    BASE_URL = "https://api.builtwith.com/v21/api.json"

    def fetch(self, domain: str) -> Optional[dict]:
        api_key = os.getenv("BUILTWITH_API_KEY")
        if not api_key:
            logger.debug("BUILTWITH_API_KEY not set, skipping")
            return None
        try:
            resp = SESSION.get(
                self.BASE_URL,
                params={"KEY": api_key, "LOOKUP": domain},
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.debug("BuiltWith returned %s for %s", resp.status_code, domain)
            return None
        except Exception as e:
            logger.debug("BuiltWith error for %s: %s", domain, e)
            return None


class SimilarwebClient:
    BASE_URL = "https://api.similarweb.com/v1/similar-rank"

    def fetch(self, domain: str) -> Optional[dict]:
        api_key = os.getenv("SIMILARWEB_API_KEY")
        if not api_key:
            logger.debug("SIMILARWEB_API_KEY not set, skipping")
            return None
        try:
            resp = SESSION.get(
                f"{self.BASE_URL}/{domain}/rank",
                params={"api_key": api_key},
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.debug("Similarweb returned %s for %s", resp.status_code, domain)
            return None
        except Exception as e:
            logger.debug("Similarweb error for %s: %s", domain, e)
            return None
