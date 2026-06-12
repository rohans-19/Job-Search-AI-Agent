"""
database.py
-----------
SQLite database helper module for the Job Search AI Agent.

This module is a standalone layer that can be imported by any other module
(app.py, main.py, career_agent.py, etc.) without modifying them.

Tables managed:
  - users              : user profile & preferences
  - saved_jobs         : jobs the user has bookmarked / applied to
  - job_search_history : every search query performed during a session

Database file: career_assistant.db  (created in the project root directory)

Usage:
    from database import (
        initialize_database,
        save_job,
        save_user_preferences,
        get_saved_jobs,
        save_search_history,
    )

    initialize_database()   # call once at application startup
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The database file sits next to this module (project root).
DB_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "career_assistant.db")

# Supported cities for Location Intelligence Agent.
SUPPORTED_CITIES: list[str] = ["Bangalore", "Mumbai", "Delhi", "Pune", "Hyderabad"]

# Module-level logger – inherits the root logger configuration set by callers.
logger = logging.getLogger(__name__)


def get_normalized_city(city: str) -> Optional[str]:
    """
    Normalizes a given city/location string to match one of the supported cities.
    Returns the standard supported city name, or None if it's not supported.
    """
    if not city or not city.strip():
        return None
    loc_lower = city.strip().lower()
    if "bangalore" in loc_lower or "bengaluru" in loc_lower:
        return "Bangalore"
    if "mumbai" in loc_lower or "bombay" in loc_lower:
        return "Mumbai"
    if "delhi" in loc_lower:
        return "Delhi"
    if "pune" in loc_lower:
        return "Pune"
    if "hyderabad" in loc_lower:
        return "Hyderabad"
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    """
    Opens and returns a new SQLite connection with foreign-key enforcement
    and a Row factory so callers can access columns by name.

    Returns:
        sqlite3.Connection: An open connection to career_assistant.db.

    Raises:
        sqlite3.Error: If the connection cannot be established.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row          # dict-like row access
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as exc:
        logger.error("Failed to connect to the database at '%s': %s", DB_PATH, exc)
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def initialize_database() -> bool:
    """
    Creates the database file (if absent) and ensures all required tables
    exist.  Safe to call on every application startup – uses IF NOT EXISTS so
    existing data is never overwritten.

    Tables created:
        users              – one row per user profile / preferences
        saved_jobs         – jobs bookmarked or applied to by the user
        job_search_history – audit log of every search performed

    Returns:
        bool: True if initialisation succeeded, False otherwise.
    """
    create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            preferred_location      TEXT,
            preferred_salary_lpa    REAL,
            preferred_role          TEXT,
            work_from_home_preference TEXT,
            notice_period_days      INTEGER,
            flexibility_preference  TEXT    DEFAULT 'Strict'
        );
    """

    create_saved_jobs_table = """
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title          TEXT    NOT NULL,
            company_name       TEXT,
            location           TEXT,
            salary_lpa         REAL,
            source_platform    TEXT,
            application_status TEXT    DEFAULT 'Saved',
            saved_date         TEXT    DEFAULT (datetime('now', 'localtime'))
        );
    """

    create_job_search_history_table = """
        CREATE TABLE IF NOT EXISTS job_search_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            search_role     TEXT    NOT NULL,
            search_location TEXT,
            timestamp       TEXT    DEFAULT (datetime('now', 'localtime'))
        );
    """

    create_source_quality_stats_table = """
        CREATE TABLE IF NOT EXISTS source_quality_stats (
            source_name        TEXT PRIMARY KEY,
            total_fetches      INTEGER DEFAULT 0,
            successful_fetches INTEGER DEFAULT 0,
            failed_fetches     INTEGER DEFAULT 0,
            total_jobs_yielded INTEGER DEFAULT 0
        );
    """

    create_historical_salary_ranges_table = """
        CREATE TABLE IF NOT EXISTS historical_salary_ranges (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            search_role    TEXT    NOT NULL,
            search_location TEXT,
            min_salary_lpa REAL,
            max_salary_lpa REAL,
            avg_salary_lpa REAL,
            timestamp      TEXT    DEFAULT (datetime('now', 'localtime'))
        );
    """

    create_company_culture_insights_table = """
        CREATE TABLE IF NOT EXISTS company_culture_insights (
            company_name           TEXT    PRIMARY KEY,
            work_life_balance      TEXT,
            career_growth          TEXT,
            salary_competitiveness TEXT,
            remote_friendly        TEXT,
            overall_summary        TEXT,
            last_updated           TEXT    DEFAULT (datetime('now', 'localtime'))
        );
    """

    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_users_table)
            # Migration check: add flexibility_preference to users if missing
            try:
                cursor.execute("PRAGMA table_info(users);")
                cols = [r["name"] for r in cursor.fetchall()]
                if "flexibility_preference" not in cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN flexibility_preference TEXT DEFAULT 'Strict';")
            except Exception as e:
                logger.warning("Migration warning: %s", e)
                
            cursor.execute(create_saved_jobs_table)
            cursor.execute(create_job_search_history_table)
            cursor.execute(create_source_quality_stats_table)
            cursor.execute(create_historical_salary_ranges_table)
            cursor.execute(create_company_culture_insights_table)
            conn.commit()
        logger.info("Database initialised successfully at: %s", DB_PATH)
        return True
    except sqlite3.Error as exc:
        logger.error("Error initialising database: %s", exc)
        return False


# ---------------------------------------------------------------------------

def save_user_preferences(
    preferred_location: Optional[str] = None,
    preferred_salary_lpa: Optional[float] = None,
    preferred_role: Optional[str] = None,
    work_from_home_preference: Optional[str] = None,
    notice_period_days: Optional[int] = None,
    flexibility_preference: Optional[str] = None,
) -> Optional[int]:
    """
    Inserts a new user-preference record into the *users* table.
    """
    sql = """
        INSERT INTO users
            (preferred_location, preferred_salary_lpa, preferred_role,
             work_from_home_preference, notice_period_days, flexibility_preference)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    preferred_location,
                    preferred_salary_lpa,
                    preferred_role,
                    work_from_home_preference,
                    notice_period_days,
                    flexibility_preference,
                ),
            )
            conn.commit()
            row_id: int = cursor.lastrowid
            logger.info("User preferences saved (id=%d).", row_id)
            return row_id
    except sqlite3.Error as exc:
        logger.error("Error saving user preferences: %s", exc)
        return None


def get_user_preferences() -> dict:
    """
    Retrieves the latest user preference record from the users table.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 1;")
            row = cursor.fetchone()
            if row:
                return dict(row)
    except sqlite3.Error as exc:
        logger.error("Error retrieving user preferences: %s", exc)
    return {}


# ---------------------------------------------------------------------------

def save_job(
    job_title: str,
    company_name: Optional[str] = None,
    location: Optional[str] = None,
    salary_lpa: Optional[float] = None,
    source_platform: Optional[str] = None,
    application_status: str = "Saved",
) -> Optional[int]:
    """
    Inserts a new job record into the *saved_jobs* table.

    Args:
        job_title (str):              Title of the job position.  **Required.**
        company_name (str, optional): Hiring company name.
        location (str, optional):     Job location (city / remote).
        salary_lpa (float, optional): Offered salary in Lakhs Per Annum.
        source_platform (str, optional): Where the job was found, e.g. "Adzuna".
        application_status (str):     Current status – defaults to ``"Saved"``.
                                      Typical values: "Saved", "Applied",
                                      "Interview", "Offer", "Rejected".

    Returns:
        int | None: The ``id`` of the newly inserted row, or ``None`` on failure.

    Raises:
        ValueError: If ``job_title`` is empty or None.
    """
    if not job_title or not job_title.strip():
        raise ValueError("'job_title' must be a non-empty string.")

    sql = """
        INSERT INTO saved_jobs
            (job_title, company_name, location, salary_lpa,
             source_platform, application_status)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    job_title.strip(),
                    company_name,
                    location,
                    salary_lpa,
                    source_platform,
                    application_status,
                ),
            )
            conn.commit()
            row_id: int = cursor.lastrowid
            logger.info("Job saved: '%s' at '%s' (id=%d).", job_title, company_name, row_id)
            return row_id
    except sqlite3.Error as exc:
        logger.error("Error saving job '%s': %s", job_title, exc)
        return None


# ---------------------------------------------------------------------------

def get_saved_jobs(application_status: Optional[str] = None) -> list[dict]:
    """
    Retrieves saved jobs from the *saved_jobs* table, optionally filtered by
    application status.

    Args:
        application_status (str, optional): If provided, only rows matching
            this status are returned (case-insensitive).
            Pass ``None`` (default) to fetch all saved jobs.

    Returns:
        list[dict]: A list of job records as plain dictionaries.
                    Returns an empty list if the query fails or no rows match.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()

            if application_status:
                cursor.execute(
                    "SELECT * FROM saved_jobs WHERE LOWER(application_status) = LOWER(?)"
                    " ORDER BY saved_date DESC;",
                    (application_status,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM saved_jobs ORDER BY saved_date DESC;"
                )

            rows = cursor.fetchall()
            jobs = [dict(row) for row in rows]
            logger.info("Retrieved %d saved job(s).", len(jobs))
            return jobs
    except sqlite3.Error as exc:
        logger.error("Error retrieving saved jobs: %s", exc)
        return []


# ---------------------------------------------------------------------------

def save_search_history(
    search_role: str,
    search_location: Optional[str] = None,
) -> Optional[int]:
    """
    Records a job-search query in the *job_search_history* table.

    Call this function each time the user performs a new search so you have
    a full audit trail of what was searched and when.

    Args:
        search_role (str):              The role / keyword that was searched.
                                        **Required.**
        search_location (str, optional): The location filter used in the search.

    Returns:
        int | None: The ``id`` of the newly inserted row, or ``None`` on failure.

    Raises:
        ValueError: If ``search_role`` is empty or None.
    """
    if not search_role or not search_role.strip():
        raise ValueError("'search_role' must be a non-empty string.")

    sql = """
        INSERT INTO job_search_history (search_role, search_location)
        VALUES (?, ?);
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (search_role.strip(), search_location))
            conn.commit()
            row_id: int = cursor.lastrowid
            logger.info(
                "Search history saved: role='%s', location='%s' (id=%d).",
                search_role,
                search_location,
                row_id,
            )
            return row_id
    except sqlite3.Error as exc:
        logger.error("Error saving search history: %s", exc)
        return None


# ---------------------------------------------------------------------------

def get_jobs_by_city(city: str) -> list[dict]:
    """
    Retrieves saved jobs from the saved_jobs table filtered by the normalized city.
    """
    normalized_city = get_normalized_city(city)
    if not normalized_city:
        logger.warning("get_jobs_by_city: '%s' is not in the supported cities list.", city)
        return []
    
    # We will search for jobs where location matches the normalized city or its common variants.
    search_terms = [normalized_city.lower()]
    if normalized_city == "Bangalore":
        search_terms.append("bengaluru")
    elif normalized_city == "Delhi":
        search_terms.append("new delhi")
        
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM saved_jobs WHERE " + " OR ".join(["LOWER(location) LIKE ?" for _ in search_terms]) + " ORDER BY saved_date DESC;"
            params = [f"%{term}%" for term in search_terms]
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Error retrieving jobs by city '%s': %s", city, exc)
        return []


def save_location_preference(city: str) -> bool:
    """
    Saves or updates the user's preferred location (city) in the database.
    If a record exists, we update it. If not, we insert a new preferences row.
    """
    normalized_city = get_normalized_city(city)
    if not normalized_city:
        logger.warning("save_location_preference: '%s' is not a supported city.", city)
        # Store whatever is input but warn
        normalized_city = city.strip()
        
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1;")
            row = cursor.fetchone()
            if row:
                user_id = row["id"]
                cursor.execute(
                    "UPDATE users SET preferred_location = ? WHERE id = ?;",
                    (normalized_city, user_id)
                )
                logger.info("Updated user preferred location to '%s' (id=%d).", normalized_city, user_id)
            else:
                cursor.execute(
                    "INSERT INTO users (preferred_location) VALUES (?);",
                    (normalized_city,)
                )
                logger.info("Inserted new user preferred location: '%s'.", normalized_city)
            conn.commit()
            return True
    except sqlite3.Error as exc:
        logger.error("Error saving location preference: %s", exc)
        return False


def get_preferred_city() -> Optional[str]:
    """
    Retrieves the most recently saved preferred location/city from the users table.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT preferred_location FROM users ORDER BY id DESC LIMIT 1;")
            row = cursor.fetchone()
            if row and row["preferred_location"]:
                return row["preferred_location"].strip()
    except sqlite3.Error as exc:
        logger.error("Error retrieving preferred city: %s", exc)
    return None


def get_location_history() -> list[str]:
    """
    Retrieves the list of unique locations the user has searched for in the past,
    ordered from most recent to oldest.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT search_location FROM job_search_history "
                "WHERE search_location IS NOT NULL AND search_location != '' "
                "ORDER BY timestamp DESC;"
            )
            rows = cursor.fetchall()
            return [row["search_location"] for row in rows]
    except sqlite3.Error as exc:
        logger.error("Error retrieving location history: %s", exc)
        return []


def update_source_quality(source_name: str, success: bool, jobs_yielded: int) -> bool:
    """
    Increments metrics in source_quality_stats.
    Uses INSERT OR IGNORE and then UPDATE for upsert behavior.
    """
    if not source_name:
        return False
        
    try:
        success_inc = 1 if success else 0
        fail_inc = 0 if success else 1
        
        with _get_connection() as conn:
            cursor = conn.cursor()
            # Ensure row exists
            cursor.execute(
                "INSERT OR IGNORE INTO source_quality_stats (source_name) VALUES (?);",
                (source_name,)
            )
            # Update metrics
            cursor.execute(
                "UPDATE source_quality_stats SET "
                "total_fetches = total_fetches + 1, "
                "successful_fetches = successful_fetches + ?, "
                "failed_fetches = failed_fetches + ?, "
                "total_jobs_yielded = total_jobs_yielded + ? "
                "WHERE source_name = ?;",
                (success_inc, fail_inc, jobs_yielded, source_name)
            )
            conn.commit()
            return True
    except sqlite3.Error as exc:
        logger.error("Error updating source quality for '%s': %s", source_name, exc)
        return False


def get_source_quality_stats() -> dict:
    """
    Retrieves all records from source_quality_stats and packages them into a dictionary.
    """
    stats = {}
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM source_quality_stats;")
            rows = cursor.fetchall()
            for row in rows:
                name = row["source_name"]
                total = row["total_fetches"]
                successes = row["successful_fetches"]
                rate = round((successes / total) * 100.0, 1) if total > 0 else 0.0
                stats[name] = {
                    "total_fetches": total,
                    "successful_fetches": successes,
                    "failed_fetches": row["failed_fetches"],
                    "total_jobs_yielded": row["total_jobs_yielded"],
                    "success_rate_percent": rate
                }
    except sqlite3.Error as exc:
        logger.error("Error retrieving source quality stats: %s", exc)
    return stats


def save_historical_salary_range(role: str, location: str, min_val: float, max_val: float, avg_val: float) -> bool:
    """
    Saves a calculated historical salary range for a specific role and location in SQLite.
    """
    if not role or not role.strip():
        return False
        
    sql = """
        INSERT INTO historical_salary_ranges (search_role, search_location, min_salary_lpa, max_salary_lpa, avg_salary_lpa)
        VALUES (?, ?, ?, ?, ?);
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (role.strip(), location.strip() if location else None, min_val, max_val, avg_val))
            conn.commit()
            return True
    except sqlite3.Error as exc:
        logger.error("Error saving historical salary range: %s", exc)
        return False


def get_historical_salary_ranges(role: str, location: str) -> list[dict]:
    """
    Retrieves all recorded historical salary ranges for a given role and location.
    """
    if not role or not role.strip():
        return []
        
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM historical_salary_ranges "
                "WHERE LOWER(search_role) = LOWER(?) AND LOWER(search_location) = LOWER(?) "
                "ORDER BY timestamp DESC;",
                (role.strip(), location.strip() if location else "")
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Error retrieving historical salary ranges: %s", exc)
        return []


# ---------------------------------------------------------------------------

def save_company_culture(company_name: str, insights: dict) -> bool:
    """
    Saves or updates company culture insights in the company_culture_insights table.
    """
    if not company_name or not company_name.strip():
        return False
        
    sql = """
        INSERT OR REPLACE INTO company_culture_insights 
            (company_name, work_life_balance, career_growth, salary_competitiveness, remote_friendly, overall_summary, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now', 'localtime'));
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                sql,
                (
                    company_name.strip(),
                    insights.get("work_life_balance", ""),
                    insights.get("career_growth", ""),
                    insights.get("salary_competitiveness", ""),
                    insights.get("remote_friendly", ""),
                    insights.get("overall_summary", ""),
                ),
            )
            conn.commit()
            return True
    except sqlite3.Error as exc:
        logger.error("Error saving company culture for '%s': %s", company_name, exc)
        return False


def get_company_culture(company_name: str) -> Optional[dict]:
    """
    Retrieves cached company culture insights for a given company.
    """
    if not company_name or not company_name.strip():
        return None
        
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM company_culture_insights WHERE LOWER(company_name) = LOWER(?);",
                (company_name.strip(),)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
    except sqlite3.Error as exc:
        logger.error("Error retrieving company culture for '%s': %s", company_name, exc)
    return None


# ---------------------------------------------------------------------------
# Quick smoke-test (run with: python database.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 55)
    print("  database.py  –  SQLite Layer Smoke Test")
    print("=" * 55)

    # 1. Initialise
    ok = initialize_database()
    print(f"\n[1] initialize_database() -> {'OK' if ok else 'FAILED'}")

    # 2. Save user preferences
    uid = save_user_preferences(
        preferred_location="Bangalore",
        preferred_salary_lpa=12.0,
        preferred_role="Data Engineer",
        work_from_home_preference="Hybrid",
        notice_period_days=30,
    )
    print(f"[2] save_user_preferences() -> inserted id={uid}")

    # 3. Save a couple of jobs
    jid1 = save_job(
        job_title="Data Engineer",
        company_name="Infosys",
        location="Bangalore",
        salary_lpa=14.5,
        source_platform="Adzuna",
        application_status="Saved",
    )
    jid2 = save_job(
        job_title="Senior Data Engineer",
        company_name="Wipro",
        location="Hyderabad",
        salary_lpa=18.0,
        source_platform="MockPlatform",
        application_status="Applied",
    )
    print(f"[3] save_job() x2 -> ids={jid1}, {jid2}")

    # 4. Save search history
    sid = save_search_history("Data Engineer", "Bangalore")
    print(f"[4] save_search_history() -> inserted id={sid}")

    # 5. Fetch all saved jobs
    all_jobs = get_saved_jobs()
    print(f"[5] get_saved_jobs()  -> {len(all_jobs)} record(s)")
    for j in all_jobs:
        print(f"      • [{j['id']}] {j['job_title']} @ {j['company_name']} | status={j['application_status']}")

    # 6. Fetch filtered jobs
    applied = get_saved_jobs(application_status="Applied")
    print(f"[6] get_saved_jobs(status='Applied') -> {len(applied)} record(s)")

    print("\n[DONE] Smoke test complete. Database file:", DB_PATH)
