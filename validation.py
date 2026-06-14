"""
validation.py
-------------
Centralised input validation for the Job Search AI Agent UI.

Keeps all "is this input acceptable?" logic in one place so both the
Streamlit pages and the CLI can share the same rules and error messages.

Every validator returns a ``ValidationResult`` so callers can render a clean,
user-friendly message instead of letting a raw exception bubble up.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Hard limits — kept conservative so a malformed upload can't exhaust memory
# or send junk to the downstream APIs.
MAX_RESUME_BYTES: int = 10 * 1024 * 1024          # 10 MB
MIN_RESUME_BYTES: int = 100                        # anything smaller isn't a real PDF
PDF_MAGIC: bytes = b"%PDF"                          # valid PDFs start with this
MAX_ROLE_LEN: int = 100
MIN_ROLE_LEN: int = 2
MAX_SALARY_LPA: float = 1000.0                      # ₹1000 LPA upper sanity bound


@dataclass
class ValidationResult:
    """Outcome of a validation check."""
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:           # allows `if result:`
        return self.ok


def validate_resume_upload(file_name: str | None, data: bytes | None) -> ValidationResult:
    """
    Validates an uploaded resume file's name, size and magic bytes.

    Args:
        file_name: Original filename from the uploader (may be None).
        data:      Raw bytes of the uploaded file (may be None).

    Returns:
        ValidationResult with human-readable errors/warnings.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if data is None:
        return ValidationResult(False, ["No file received. Please choose a PDF resume."])

    if file_name and not file_name.lower().endswith(".pdf"):
        errors.append("Resume must be a **.pdf** file. Other formats are not supported.")

    size = len(data)
    if size < MIN_RESUME_BYTES:
        errors.append("The uploaded file looks empty or corrupted (too small to be a real PDF).")
    elif size > MAX_RESUME_BYTES:
        errors.append(
            f"Resume is too large ({size / 1_048_576:.1f} MB). "
            f"Maximum allowed is {MAX_RESUME_BYTES // 1_048_576} MB."
        )

    # Magic-byte check — catches files renamed to .pdf that aren't PDFs.
    if size >= len(PDF_MAGIC) and not data[:len(PDF_MAGIC)].startswith(PDF_MAGIC):
        errors.append("This file is not a valid PDF (missing the `%PDF` header).")

    if size and not errors and size > 5 * 1024 * 1024:
        warnings.append("Large PDF — skill extraction may take a few extra seconds.")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def validate_search_params(
    role: str | None,
    location: str | None,
    expected_salary: float | None,
) -> ValidationResult:
    """
    Validates the core job-search parameters before the pipeline runs.

    Returns:
        ValidationResult. ``warnings`` are non-blocking (e.g. unusually high salary).
    """
    errors: list[str] = []
    warnings: list[str] = []

    role_clean = (role or "").strip()
    if not role_clean:
        errors.append("**Job Role** cannot be empty.")
    elif len(role_clean) < MIN_ROLE_LEN:
        errors.append(f"**Job Role** must be at least {MIN_ROLE_LEN} characters.")
    elif len(role_clean) > MAX_ROLE_LEN:
        errors.append(f"**Job Role** is too long (max {MAX_ROLE_LEN} characters).")
    elif not any(c.isalpha() for c in role_clean):
        errors.append("**Job Role** must contain letters (e.g. 'Python Developer').")

    if not (location or "").strip():
        errors.append("**City / Location** is required.")

    if expected_salary is not None:
        if expected_salary < 0:
            errors.append("**Expected Salary** cannot be negative.")
        elif expected_salary > MAX_SALARY_LPA:
            errors.append(f"**Expected Salary** seems unrealistic (max {MAX_SALARY_LPA:.0f} LPA).")
        elif expected_salary == 0:
            warnings.append("Expected salary is 0 LPA — salary scoring will be skipped.")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def has_any_api_credentials(adzuna_id: str | None,
                            adzuna_key: str | None,
                            jooble_key: str | None) -> bool:
    """
    True if at least one live connector can run.

    Adzuna needs BOTH id and key; Jooble needs only its key.
    """
    adzuna_ok = bool((adzuna_id or "").strip()) and bool((adzuna_key or "").strip())
    jooble_ok = bool((jooble_key or "").strip())
    return adzuna_ok or jooble_ok
