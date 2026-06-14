"""
connectors/base.py
------------------
Defines the canonical normalized job schema and the abstract base class
that every connector must implement.

Normalized job schema
---------------------
Every connector MUST return a list of dicts matching exactly this shape:

    {
        "title":      str,   # job title
        "company":    str,   # company / employer name
        "location":   str,   # city / region (e.g. "Bangalore, India")
        "salary_lpa": float | None,  # salary in Lakhs Per Annum; None if unknown
        "source":     str,   # platform name (e.g. "Adzuna", "Jooble")
    }

Design notes
------------
- Using an abstract base class enforces the interface contract at definition
  time rather than at runtime, making it easy to add new connectors later.
- The `normalize` static method can be called by connectors to produce a
  guaranteed-safe dict even if some fields are missing from the raw API
  response.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


def redact(text: object, *secrets: str | None) -> str:
    """Return ``str(text)`` with any of ``secrets`` replaced by '***REDACTED***'.

    Connectors embed API keys in request URLs/query strings. The `requests`
    library copies the full URL into its exception messages, so logging a raw
    exception would leak the key into the application logs. Always route
    connector error text through this helper before logging.
    """
    out = str(text)
    for secret in secrets:
        if secret:
            out = out.replace(secret, "***REDACTED***")
    return out


def normalize(
    title: str,
    company: str,
    location: str,
    salary_lpa: float | None,
    source: str,
) -> dict:
    """
    Returns a canonical normalized job dict.

    All string fields are stripped; missing/falsy strings are replaced with
    "Unknown" so downstream code never has to deal with empty strings.

    Args:
        title     (str):         Job title.
        company   (str):         Hiring company name.
        location  (str):         Job location string.
        salary_lpa(float|None):  Salary in Lakhs Per Annum, or None.
        source    (str):         Source platform name.

    Returns:
        dict: Normalized job record.
    """
    return {
        "title":      (title.strip()    if title    else "Unknown Title"),
        "company":    (company.strip()  if company  else "Unknown Company"),
        "location":   (location.strip() if location else "Unknown Location"),
        "salary_lpa": float(salary_lpa) if salary_lpa is not None else None,
        "source":     (source.strip()   if source   else "Unknown"),
    }


class BaseConnector(ABC):
    """
    Abstract base class for all job-source connectors.

    Subclasses must implement:
        fetch(role, location, **kwargs) -> list[dict]

    The returned list must contain dicts produced by the `normalize()`
    helper above (or structurally identical dicts).
    """

    # Human-readable name of the platform this connector wraps.
    SOURCE_NAME: str = "Unknown"

    @abstractmethod
    def fetch(self, role: str, location: str, **kwargs) -> list[dict]:
        """
        Fetch job listings for the given role and location.

        Args:
            role     (str): Job title / keyword to search for.
            location (str): Preferred city or region.
            **kwargs:       Connector-specific parameters (API keys, counts…).

        Returns:
            list[dict]: A list of normalized job dicts (see module docstring).
        """
        ...  # pragma: no cover
