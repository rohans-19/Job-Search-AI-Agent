"""
connectors/aggregator.py
------------------------
Orchestrator that coordinates all job-source connectors.

Responsibilities
----------------
1. Call every registered connector in sequence (easy to parallelise later).
2. Merge all results into a single flat list.
3. Deduplicate on (title.lower(), company.lower()) — first occurrence wins.
4. Persist every unique job to the SQLite database via database.save_job().
5. Sort deduplicated jobs by salary_lpa descending (highest first); jobs
   without a salary fall to the bottom.
6. Return the final unified list.

Public API
----------
    get_all_jobs(
        role,
        location,
        adzuna_app_id  = None,   # overrides .env / ADZUNA_APP_ID
        adzuna_app_key = None,   # overrides .env / ADZUNA_APP_KEY
        jooble_api_key = None,   # overrides .env / JOOBLE_API_KEY
        count          = None,   # overrides .env / JOB_FETCH_COUNT
    ) -> list[dict]

Each dict in the returned list conforms to the canonical schema:

    {
        "title":      str,
        "company":    str,
        "location":   str,
        "salary_lpa": float | None,
        "source":     str,
    }
"""

import logging
import os
import sys

# ---------------------------------------------------------------------------
# Allow running this file directly from its directory for quick tests.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from .adzuna_connector    import AdzunaConnector
from .jooble_connector    import JoobleConnector
from .naukri_connector    import NaukriConnector
from .timesjobs_connector import TimesJobsConnector
from database import initialize_database, save_job
import config  # loads .env automatically on first import

logger = logging.getLogger(__name__)



# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _deduplicate(jobs: list[dict]) -> list[dict]:
    """
    Remove duplicate jobs using (title, company) as the fingerprint.

    The first occurrence of each (title, company) pair is kept; subsequent
    duplicates (even from different sources) are silently discarded.

    Args:
        jobs (list[dict]): Raw merged job list (may contain duplicates).

    Returns:
        list[dict]: Deduplicated list preserving original insertion order.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[dict] = []

    for job in jobs:
        key = (job["title"].strip().lower(), job["company"].strip().lower())
        if key not in seen:
            seen.add(key)
            unique.append(job)

    duplicates_removed = len(jobs) - len(unique)
    if duplicates_removed:
        logger.info("Deduplication removed %d duplicate(s).", duplicates_removed)

    return unique


def _sort_by_relevance(jobs: list[dict]) -> list[dict]:
    """
    Sort jobs by salary_lpa descending; jobs without salary go last.

    Using a tuple sort key: (has_salary, salary_lpa) so that:
        - has_salary=True  (1) comes before has_salary=False (0) when reversed.
        - Within jobs that have a salary, higher LPA ranks first.

    Args:
        jobs (list[dict]): Deduplicated job list.

    Returns:
        list[dict]: Sorted list (highest salary first, None-salary last).
    """
    return sorted(
        jobs,
        key=lambda j: (j["salary_lpa"] is not None, j["salary_lpa"] or 0.0),
        reverse=True,
    )


def _persist_jobs(jobs: list[dict]) -> None:
    """
    Persist every job in the list to the SQLite database.

    Errors are logged but never propagated so a DB failure cannot break
    the caller's control flow.

    Args:
        jobs (list[dict]): Normalized, deduplicated job records.
    """
    saved_count  = 0
    failed_count = 0

    for job in jobs:
        try:
            result = save_job(
                job_title       = job["title"],
                company_name    = job["company"],
                location        = job["location"],
                salary_lpa      = job["salary_lpa"],
                source_platform = job["source"],
                application_status = "Fetched",   # auto-fetched, not user-bookmarked
            )
            if result:
                saved_count += 1
            else:
                failed_count += 1
        except Exception as exc:
            logger.error("Failed to persist job '%s': %s", job.get("title"), exc)
            failed_count += 1

    logger.info(
        "DB persistence: %d saved, %d failed (out of %d total).",
        saved_count, failed_count, len(jobs),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_jobs(
    role: str,
    location: str,
    adzuna_app_id: str  | None = None,
    adzuna_app_key: str | None = None,
    jooble_api_key: str | None = None,
    count: int | None = None,
) -> list[dict]:
    """
    Fetch jobs from all registered connectors, merge, deduplicate,
    persist to SQLite, and return sorted results.

    Credentials priority
    --------------------
    For each credential the resolution order is:
        1. Explicit argument passed by the caller.
        2. Value loaded from .env (via config.py).
    This means callers can simply call ``get_all_jobs(role, location)``
    and all keys are picked up from the .env file automatically.

    Connector activation rules
    --------------------------
    - **Adzuna**    – activated when ADZUNA_APP_ID + ADZUNA_APP_KEY are set.
    - **Jooble**    – activated when JOOBLE_API_KEY is set.
    - **Naukri**    – always active (mock; no credentials required).
    - **TimesJobs** – always active (mock; no credentials required).

    Args:
        role           (str):       Job title / keyword to search.
        location       (str):       Preferred city or region.
        adzuna_app_id  (str|None):  Override for ADZUNA_APP_ID.  Pass None to use .env.
        adzuna_app_key (str|None):  Override for ADZUNA_APP_KEY. Pass None to use .env.
        jooble_api_key (str|None):  Override for JOOBLE_API_KEY. Pass None to use .env.
        count          (int|None):  Override for JOB_FETCH_COUNT. Pass None to use .env.

    Returns:
        list[dict]: Unified, deduplicated, sorted job records.
                    Each record matches the canonical schema:
                    {title, company, location, salary_lpa, source}

    Raises:
        ValueError: If `role` or `location` are empty.
    """
    if not role or not role.strip():
        raise ValueError("'role' must be a non-empty string.")
    if not location or not location.strip():
        raise ValueError("'location' must be a non-empty string.")

    role     = role.strip()
    location = location.strip()

    # --- Resolve credentials: explicit arg > .env value ---
    _adzuna_id  = adzuna_app_id  or config.ADZUNA_APP_ID
    _adzuna_key = adzuna_app_key or config.ADZUNA_APP_KEY
    _jooble_key = jooble_api_key or config.JOOBLE_API_KEY
    _count      = count          if count is not None else config.JOB_FETCH_COUNT

    logger.info(
        "get_all_jobs: role='%s', location='%s', count=%d.", role, location, _count
    )

    # Ensure tables exist before any persistence attempt.
    initialize_database()

    # ------------------------------------------------------------------
    # 1. Build connector registry
    # ------------------------------------------------------------------
    connectors = []

    if _adzuna_id and _adzuna_key:
        try:
            connectors.append(AdzunaConnector(_adzuna_id, _adzuna_key))
            logger.info("Adzuna connector registered.")
        except ValueError as exc:
            logger.warning("Adzuna connector skipped: %s", exc)
    else:
        logger.info("Adzuna connector skipped (ADZUNA_APP_ID / ADZUNA_APP_KEY not set in .env).")

    if _jooble_key:
        try:
            connectors.append(JoobleConnector(_jooble_key))
            logger.info("Jooble connector registered.")
        except ValueError as exc:
            logger.warning("Jooble connector skipped: %s", exc)
    else:
        logger.info("Jooble connector skipped (JOOBLE_API_KEY not set in .env).")

    # Mock connectors are always on.
    connectors.append(NaukriConnector())
    connectors.append(TimesJobsConnector())
    logger.info("Naukri + TimesJobs mock connectors registered.")

    # ------------------------------------------------------------------
    # 2. Fetch from all connectors
    # ------------------------------------------------------------------
    all_jobs: list[dict] = []

    for connector in connectors:
        try:
            results = connector.fetch(role, location, count=_count)
            logger.info(
                "[%s] returned %d job(s).", connector.SOURCE_NAME, len(results)
            )
            all_jobs.extend(results)
        except Exception as exc:
            # One failing connector must not abort the whole pipeline.
            logger.error(
                "[%s] fetch() raised an unexpected exception: %s",
                connector.SOURCE_NAME, exc,
            )

    logger.info("Total raw results before deduplication: %d.", len(all_jobs))

    # ------------------------------------------------------------------
    # 3. Deduplicate
    # ------------------------------------------------------------------
    unique_jobs = _deduplicate(all_jobs)
    logger.info("Unique jobs after deduplication: %d.", len(unique_jobs))

    # ------------------------------------------------------------------
    # 4. Persist to SQLite
    # ------------------------------------------------------------------
    _persist_jobs(unique_jobs)

    # ------------------------------------------------------------------
    # 5. Sort by relevance (salary descending)
    # ------------------------------------------------------------------
    sorted_jobs = _sort_by_relevance(unique_jobs)

    logger.info("get_all_jobs: returning %d job(s).", len(sorted_jobs))
    return sorted_jobs


# ---------------------------------------------------------------------------
# Quick smoke-test (python -m connectors.aggregator  OR  python aggregator.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Job Aggregator  -  Smoke Test")
    print("  Credentials loaded automatically from .env")
    print("=" * 60)

    # No credentials passed — they are read from .env via config.py
    results = get_all_jobs(
        role     = "Data Engineer",
        location = "Bangalore",
    )

    print(f"\nReturned {len(results)} unique job(s):\n")
    for i, job in enumerate(results, 1):
        salary = f"{job['salary_lpa']} LPA" if job["salary_lpa"] else "Not Disclosed"
        print(f"  [{i}] {job['title']}")
        print(f"       Company  : {job['company']}")
        print(f"       Location : {job['location']}")
        print(f"       Salary   : {salary}")
        print(f"       Source   : {job['source']}")
        print()

    print("[DONE] Smoke test complete.")

