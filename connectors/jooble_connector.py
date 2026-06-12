"""
connectors/jooble_connector.py
------------------------------
Live connector for the Jooble Jobs API.

API docs: https://jooble.org/api/about

Required credentials (free – request at https://jooble.org/api/about):
    JOOBLE_API_KEY – your Jooble private API key

Jooble endpoint format:
    POST https://jooble.org/api/<API_KEY>
    Body: {"keywords": "<role>", "location": "<location>"}

Salary handling
---------------
Jooble occasionally returns a salary string (e.g. "₹8 LPA", "8-12 LPA",
"$60,000"). This connector attempts a best-effort parse to extract an
LPA float; if parsing fails it stores None.
"""

import logging
import re
import requests
from .base import BaseConnector, normalize

logger = logging.getLogger(__name__)

_JOOBLE_BASE_URL = "https://jooble.org/api/{api_key}"


def _parse_salary_lpa(salary_str: str | None) -> float | None:
    """
    Best-effort parser that extracts an LPA float from a Jooble salary string.

    Handles patterns like:
        "8 LPA", "8-12 LPA", "8 to 12 LPA", "800000", "₹8,00,000"

    Returns:
        float | None: LPA value or None if unparseable.
    """
    if not salary_str:
        return None

    text = salary_str.strip().lower().replace(",", "").replace("₹", "").replace("$", "")

    # Already looks like LPA (contains "lpa" or "lac")
    lpa_match = re.findall(r"(\d+(?:\.\d+)?)", text)
    if not lpa_match:
        return None

    nums = [float(x) for x in lpa_match]

    if "lpa" in text or "lac" in text or "lakh" in text:
        # Average of range, e.g. "8-12 LPA" → 10.0
        return round(sum(nums) / len(nums), 2)

    # Could be a raw rupee figure
    avg_raw = sum(nums) / len(nums)
    if avg_raw >= 100_000:
        return round(avg_raw / 100_000, 2)

    # Probably already in LPA (small number like 8, 12, etc.)
    return round(avg_raw, 2)


class JoobleConnector(BaseConnector):
    """
    Live connector for Jooble (global, India-targeted via location).

    Usage:
        connector = JoobleConnector(api_key="...")
        jobs = connector.fetch("Data Engineer", "Bangalore", count=15)
    """

    SOURCE_NAME = "Jooble"

    def __init__(self, api_key: str):
        """
        Args:
            api_key (str): Jooble private API key.
        """
        if not api_key:
            raise ValueError("JoobleConnector requires an api_key.")
        self._api_key = api_key.strip()

    def _do_fetch(self, role: str, location: str, count: int = 15) -> list[dict]:
        url     = _JOOBLE_BASE_URL.format(api_key=self._api_key)
        payload = {"keywords": role, "location": location, "resultonpage": count}

        jobs: list[dict] = []
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            for raw in data.get("jobs", []):
                salary_lpa = _parse_salary_lpa(raw.get("salary"))

                jobs.append(normalize(
                    title      = raw.get("title", ""),
                    company    = raw.get("company", ""),
                    location   = raw.get("location", ""),
                    salary_lpa = salary_lpa,
                    source     = self.SOURCE_NAME,
                ))

        except requests.exceptions.Timeout:
            logger.error("[Jooble] Request timed out for role='%s', location='%s'.", role, location)
        except requests.exceptions.HTTPError as exc:
            logger.error("[Jooble] HTTP error %s: %s", exc.response.status_code, exc)
        except requests.exceptions.RequestException as exc:
            logger.error("[Jooble] Network error: %s", exc)
        except (KeyError, ValueError, TypeError) as exc:
            logger.error("[Jooble] Unexpected response structure: %s", exc)

        return jobs

    def fetch(self, role: str, location: str, count: int = 15, **kwargs) -> list[dict]:
        """
        Fetches jobs from the Jooble API and returns normalized records.

        Args:
            role     (str): Job title / keyword.
            location (str): City or region.
            count    (int): Maximum results to return. Defaults to 15.

        Returns:
            list[dict]: Normalized job records.
        """
        jobs = self._do_fetch(role, location, count)
        if not jobs and location and "india" not in location.lower():
            fallback_location = f"{location}, India"
            logger.info("[Jooble] 0 jobs returned for '%s' in '%s'. Trying fallback '%s'...", role, location, fallback_location)
            jobs = self._do_fetch(role, fallback_location, count)

        logger.info("[Jooble] Fetched %d jobs for '%s' in '%s'.", len(jobs), role, location)
        return jobs

