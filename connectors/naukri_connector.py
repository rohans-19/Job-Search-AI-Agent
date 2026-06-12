"""
connectors/naukri_connector.py
------------------------------
Mock connector that simulates Naukri.com job listings.

Naukri does not offer a public API, so this connector returns realistic
static data representative of what a real Naukri scraper / partner API
would produce.

Design notes
------------
- Uses parametric generation so the mock data adapts to the requested
  role and location rather than being completely hardcoded.
- Salary values are expressed directly in LPA (no conversion needed).
- The SOURCE_NAME is "Naukri" to make source attribution clear in results.

To swap in a real Naukri integration later, replace the `fetch` method
body with real HTTP calls while keeping the same method signature and
return schema.
"""

import logging
import random
from .base import BaseConnector, normalize

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Realistic Naukri-style company pool for India
# ---------------------------------------------------------------------------
_NAUKRI_COMPANIES = [
    "Infosys",
    "Wipro",
    "TCS",
    "HCL Technologies",
    "Tech Mahindra",
    "Cognizant",
    "Capgemini",
    "Accenture India",
    "Mphasis",
    "L&T Technology Services",
]

_NAUKRI_LOCATIONS = [
    "Bengaluru, Karnataka",
    "Hyderabad, Telangana",
    "Pune, Maharashtra",
    "Chennai, Tamil Nadu",
    "Noida, Uttar Pradesh",
    "Gurgaon, Haryana",
    "Mumbai, Maharashtra",
    "Kolkata, West Bengal",
]

_NAUKRI_TITLE_PREFIXES = [
    "",
    "Senior ",
    "Lead ",
    "Junior ",
    "Associate ",
    "Principal ",
]

_NAUKRI_SALARY_RANGES_LPA = [
    (4.0,  8.0),
    (6.0,  12.0),
    (10.0, 18.0),
    (15.0, 25.0),
    (20.0, 35.0),
    (8.0,  14.0),
]


class NaukriConnector(BaseConnector):
    """
    Mock connector simulating Naukri.com job listings for India.

    Usage:
        connector = NaukriConnector()
        jobs = connector.fetch("Data Engineer", "Bangalore", count=10)
    """

    SOURCE_NAME = "Naukri"

    def __init__(self, seed: int = 42):
        """
        Args:
            seed (int): Random seed for reproducible mock data.
                        Useful in tests; defaults to 42.
        """
        self._seed = seed

    def fetch(self, role: str, location: str, count: int = 10, **kwargs) -> list[dict]:
        """
        Returns mock Naukri job listings adapted to the requested role
        and location.

        Args:
            role     (str): Job title / keyword.
            location (str): Preferred city or region.
            count    (int): Number of mock listings to generate. Max 10.

        Returns:
            list[dict]: Normalized job records.
        """
        rng   = random.Random(self._seed)
        jobs  = []
        count = min(count, len(_NAUKRI_COMPANIES))

        # Shuffle company pool so results vary across roles
        companies = rng.sample(_NAUKRI_COMPANIES, k=count)

        for i, company in enumerate(companies):
            prefix    = rng.choice(_NAUKRI_TITLE_PREFIXES)
            title     = f"{prefix}{role}"
            sal_range = rng.choice(_NAUKRI_SALARY_RANGES_LPA)
            salary    = round(rng.uniform(sal_range[0], sal_range[1]), 1)

            # Prefer user's location; fall back to pool for variety
            job_location = location if i < count // 2 else rng.choice(_NAUKRI_LOCATIONS)

            jobs.append(normalize(
                title      = title,
                company    = company,
                location   = job_location,
                salary_lpa = salary,
                source     = self.SOURCE_NAME,
            ))

        logger.info("[Naukri] Generated %d mock jobs for '%s' in '%s'.", len(jobs), role, location)
        return jobs
