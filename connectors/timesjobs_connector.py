"""
connectors/timesjobs_connector.py
----------------------------------
Mock connector that simulates TimesJobs.com job listings.

TimesJobs does not offer a public API, so this connector returns realistic
static data representative of what a real TimesJobs scraper / partner API
would produce.

Design notes
------------
- Data pool is independently curated from the Naukri mock so that the
  two sources produce distinct (non-duplicate) listings.
- Salary values are expressed directly in LPA.
- The SOURCE_NAME is "TimesJobs" for clear attribution in results.

To swap in a real TimesJobs integration later, replace the `fetch` method
body with real HTTP calls while keeping the same method signature and
return schema.
"""

import logging
import random
from .base import BaseConnector, normalize

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Realistic TimesJobs-style data pool for India
# ---------------------------------------------------------------------------
_TIMESJOBS_COMPANIES = [
    "Zoho Corporation",
    "Freshworks",
    "Ola",
    "Swiggy",
    "Razorpay",
    "Byju's",
    "Paytm",
    "Groww",
    "Myntra",
    "Flipkart",
]

_TIMESJOBS_LOCATIONS = [
    "Bengaluru, Karnataka",
    "Hyderabad, Telangana",
    "Delhi NCR",
    "Pune, Maharashtra",
    "Mumbai, Maharashtra",
    "Chennai, Tamil Nadu",
    "Ahmedabad, Gujarat",
    "Jaipur, Rajasthan",
]

_TIMESJOBS_TITLE_SUFFIXES = [
    "",
    " - Immediate Joiner",
    " (Hybrid)",
    " (Remote)",
    " - Fresher Welcome",
    " (3+ Years)",
]

_TIMESJOBS_SALARY_RANGES_LPA = [
    (3.0,  6.0),
    (5.0,  9.0),
    (8.0,  15.0),
    (12.0, 22.0),
    (18.0, 30.0),
    (7.0,  13.0),
]


class TimesJobsConnector(BaseConnector):
    """
    Mock connector simulating TimesJobs.com job listings for India.

    Usage:
        connector = TimesJobsConnector()
        jobs = connector.fetch("Data Engineer", "Bangalore", count=10)
    """

    SOURCE_NAME = "TimesJobs"

    def __init__(self, seed: int = 99):
        """
        Args:
            seed (int): Random seed for reproducible mock data.
                        Defaults to 99 (different from NaukriConnector's 42
                        so the two sources produce distinct orderings).
        """
        self._seed = seed

    def fetch(self, role: str, location: str, count: int = 10, **kwargs) -> list[dict]:
        """
        Returns mock TimesJobs job listings adapted to the requested role
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
        count = min(count, len(_TIMESJOBS_COMPANIES))

        companies = rng.sample(_TIMESJOBS_COMPANIES, k=count)

        for i, company in enumerate(companies):
            suffix    = rng.choice(_TIMESJOBS_TITLE_SUFFIXES)
            title     = f"{role}{suffix}"
            sal_range = rng.choice(_TIMESJOBS_SALARY_RANGES_LPA)
            salary    = round(rng.uniform(sal_range[0], sal_range[1]), 1)

            # Mix user location with pool for variety
            job_location = location if i % 2 == 0 else rng.choice(_TIMESJOBS_LOCATIONS)

            jobs.append(normalize(
                title      = title,
                company    = company,
                location   = job_location,
                salary_lpa = salary,
                source     = self.SOURCE_NAME,
            ))

        logger.info("[TimesJobs] Generated %d mock jobs for '%s' in '%s'.", len(jobs), role, location)
        return jobs
