"""
connectors/adzuna_connector.py
------------------------------
Live connector for the Adzuna Jobs API (India region).

API docs: https://developer.adzuna.com/

Required credentials (free tier):
    ADZUNA_APP_ID  – your Adzuna App ID
    ADZUNA_APP_KEY – your Adzuna App Key

Salary conversion
-----------------
Adzuna returns raw annual figures (₹) not LPA.
This connector converts them:
    salary_lpa = raw_annual_value / 100_000
"""

import logging
import requests
from .base import BaseConnector, normalize, redact

logger = logging.getLogger(__name__)

_ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/in/search/1"


def _raw_to_lpa(value: float | None) -> float | None:
    """Convert a raw annual rupee figure to Lakhs Per Annum."""
    if value is None:
        return None
    lpa = float(value) / 100_000.0
    return round(lpa, 2)


class AdzunaConnector(BaseConnector):
    """
    Live connector for Adzuna (India).

    Usage:
        connector = AdzunaConnector(app_id="...", app_key="...")
        jobs = connector.fetch("Data Engineer", "Bangalore", count=15)
    """

    SOURCE_NAME = "Adzuna"

    def __init__(self, app_id: str, app_key: str):
        """
        Args:
            app_id  (str): Adzuna App ID.
            app_key (str): Adzuna App Key.
        """
        if not app_id or not app_key:
            raise ValueError("AdzunaConnector requires both app_id and app_key.")
        self._app_id  = app_id.strip()
        self._app_key = app_key.strip()

    def fetch(self, role: str, location: str, count: int = 15, **kwargs) -> list[dict]:
        """
        Fetches jobs from the Adzuna India API and returns normalized records.

        Args:
            role     (str): Job title / keyword.
            location (str): City or region (e.g. "Bangalore").
            count    (int): Maximum results to return. Defaults to 15.

        Returns:
            list[dict]: Normalized job records.
        """
        params = {
            "app_id":          self._app_id,
            "app_key":         self._app_key,
            "what":            role,
            "where":           location,
            "results_per_page": count,
        }

        jobs: list[dict] = []
        try:
            response = requests.get(_ADZUNA_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            for raw in data.get("results", []):
                salary_min = raw.get("salary_min")
                salary_max = raw.get("salary_max")

                # Use midpoint for LPA if both bounds are available.
                if salary_min and salary_max:
                    avg_raw    = (float(salary_min) + float(salary_max)) / 2
                    salary_lpa = _raw_to_lpa(avg_raw)
                elif salary_min:
                    salary_lpa = _raw_to_lpa(float(salary_min))
                else:
                    salary_lpa = None

                jobs.append(normalize(
                    title      = raw.get("title", ""),
                    company    = raw.get("company", {}).get("display_name", ""),
                    location   = raw.get("location", {}).get("display_name", ""),
                    salary_lpa = salary_lpa,
                    source     = self.SOURCE_NAME,
                ))

        except requests.exceptions.Timeout:
            logger.error("[Adzuna] Request timed out for role='%s', location='%s'.", role, location)
        except requests.exceptions.HTTPError as exc:
            logger.error("[Adzuna] HTTP error %s: %s", exc.response.status_code,
                         redact(exc, self._app_id, self._app_key))
        except requests.exceptions.RequestException as exc:
            logger.error("[Adzuna] Network error: %s", redact(exc, self._app_id, self._app_key))
        except (KeyError, ValueError, TypeError) as exc:
            logger.error("[Adzuna] Unexpected response structure: %s",
                         redact(exc, self._app_id, self._app_key))

        logger.info("[Adzuna] Fetched %d jobs for '%s' in '%s'.", len(jobs), role, location)
        return jobs
