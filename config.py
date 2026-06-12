"""
config.py
---------
Central configuration loader for the Job Search AI Agent.

This is the ONLY place where environment variables are read.
Every other module that needs an API key or config value
MUST import from here — no `os.environ.get()` scattered in source files.

How it works
------------
1. python-dotenv is used to load the .env file from the project root.
2. Each variable is exposed as a typed module-level constant.
3. If a required variable is missing, a clear warning is logged
   (connectors are simply skipped rather than crashing the app).

Usage
-----
    from config import ADZUNA_APP_ID, ADZUNA_APP_KEY, JOOBLE_API_KEY, JOB_FETCH_COUNT

.env variables managed here
----------------------------
    ADZUNA_APP_ID     – Adzuna API App ID
    ADZUNA_APP_KEY    – Adzuna API App Key
    JOOBLE_API_KEY    – Jooble private API key
    JOB_FETCH_COUNT   – results per connector fetch (default: 15)
"""

import os
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Load .env from the project root (directory where this file lives)
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
_ENV_FILE = _ROOT / ".env"

try:
    from dotenv import load_dotenv
    loaded = load_dotenv(dotenv_path=_ENV_FILE, override=False)
    if loaded:
        logging.getLogger(__name__).info("config.py: .env loaded from %s", _ENV_FILE)
    else:
        logging.getLogger(__name__).warning(
            "config.py: .env not found at %s — using system environment only.", _ENV_FILE
        )
except ImportError:
    logging.getLogger(__name__).warning(
        "python-dotenv is not installed. "
        "Install it with: pip install python-dotenv\n"
        "Falling back to system environment variables only."
    )

# ---------------------------------------------------------------------------
# Adzuna API credentials
# ---------------------------------------------------------------------------
ADZUNA_APP_ID:  str | None = os.environ.get("ADZUNA_APP_ID") or None
ADZUNA_APP_KEY: str | None = os.environ.get("ADZUNA_APP_KEY") or None

# ---------------------------------------------------------------------------
# Jooble API credentials
# ---------------------------------------------------------------------------
JOOBLE_API_KEY: str | None = os.environ.get("JOOBLE_API_KEY") or None

# ---------------------------------------------------------------------------
# General settings
# ---------------------------------------------------------------------------
JOB_FETCH_COUNT: int = int(os.environ.get("JOB_FETCH_COUNT", "15"))

# ---------------------------------------------------------------------------
# Startup diagnostics (visible only when logging is at INFO level or lower)
# ---------------------------------------------------------------------------
_logger = logging.getLogger(__name__)

def _status(name: str, value: str | None) -> str:
    return f"SET ({value[:4]}...)" if value else "NOT SET"

_logger.info("ADZUNA_APP_ID  : %s", _status("ADZUNA_APP_ID",  ADZUNA_APP_ID))
_logger.info("ADZUNA_APP_KEY : %s", _status("ADZUNA_APP_KEY", ADZUNA_APP_KEY))
_logger.info("JOOBLE_API_KEY : %s", _status("JOOBLE_API_KEY", JOOBLE_API_KEY))
_logger.info("JOB_FETCH_COUNT: %d", JOB_FETCH_COUNT)


if __name__ == "__main__":
    # Quick check: python config.py
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("\n--- config.py diagnostics ---")
    print(f"  ADZUNA_APP_ID  : {_status('ADZUNA_APP_ID',  ADZUNA_APP_ID)}")
    print(f"  ADZUNA_APP_KEY : {_status('ADZUNA_APP_KEY', ADZUNA_APP_KEY)}")
    print(f"  JOOBLE_API_KEY : {_status('JOOBLE_API_KEY', JOOBLE_API_KEY)}")
    print(f"  JOB_FETCH_COUNT: {JOB_FETCH_COUNT}")
    print()
