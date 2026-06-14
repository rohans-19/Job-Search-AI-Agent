"""
ui_common.py
------------
Shared Streamlit UI building blocks used across every page so the multi-page
app has one consistent, premium look & feel.

Design system (see DESIGN.md):
  - Type      : Outfit (display) · Plus Jakarta Sans (body) · JetBrains Mono (numbers)
  - Neutrals  : Zinc canvas (#fafafa) / pure white surfaces / charcoal ink (#18181b)
  - Accent    : a single desaturated Emerald (#059669) — no purple, no neon glows
  - Surfaces  : 1px zinc borders, large radii, soft tinted diffusion shadows

Exposes:
  - inject_css()            : global stylesheet (call once per page, top of file).
  - render_hero(...)        : the page header.
  - render_job_card(...)    : a styled job listing card.
  - skill_chip_html(...)    : skill pill badges.
  - categorize_skills(...)  : group flat skill list into human categories.
  - extract_skills_from_pdf_bytes(...) / extract_text_from_pdf_bytes(...)
  - status_pill_html(...)   : coloured application-status badge.
  - friendly_api_error(...) : map an exception to a clear user message.
"""

from __future__ import annotations

import io
import re
import html as html_lib

import streamlit as st

from agents.skills_agent import PREDEFINED_SKILLS

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Design tokens (kept in one place so pages can reference them)
# ---------------------------------------------------------------------------
INK = "#18181b"        # zinc-900 — primary text
MUTED = "#71717a"      # zinc-500 — secondary text
CANVAS = "#fafafa"     # zinc-50  — page background
SURFACE = "#ffffff"
BORDER = "#e4e4e7"     # zinc-200
ACCENT = "#059669"     # emerald-600
ACCENT_DARK = "#047857"
ACCENT_SOFT_BG = "#ecfdf5"
ACCENT_SOFT_FG = "#047857"


# ---------------------------------------------------------------------------
# Skill categorisation map
# ---------------------------------------------------------------------------
_SKILL_CATEGORIES: dict[str, set[str]] = {
    "Languages": {
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "golang",
        "rust", "php", "swift", "kotlin", "scala", "r", "matlab", "bash", "shell",
        "perl", "dart", "haskell", "elixir",
    },
    "Web & Frameworks": {
        "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
        "spring boot", "express", "next.js", "nuxt.js", "rails", "laravel",
        "asp.net", "graphql", "rest api", "grpc",
    },
    "Data Science / ML / AI": {
        "machine learning", "deep learning", "data analysis", "data science",
        "nlp", "computer vision", "tensorflow", "pytorch", "scikit-learn",
        "keras", "xgboost", "lightgbm", "pandas", "numpy", "matplotlib",
        "seaborn", "opencv", "hugging face", "llm", "generative ai", "rag",
        "langchain", "transformers",
    },
    "Data Engineering": {
        "sql", "spark", "hadoop", "kafka", "airflow", "dbt", "hive",
        "flink", "databricks", "snowflake", "bigquery", "redshift",
        "data pipeline", "etl", "data warehouse", "data lakehouse",
    },
    "Cloud": {
        "aws", "azure", "gcp", "google cloud", "s3", "ec2", "lambda",
        "cloudformation", "terraform", "pulumi", "azure devops",
    },
    "DevOps / Infra": {
        "docker", "kubernetes", "linux", "git", "ci/cd", "jenkins",
        "github actions", "gitlab", "ansible", "helm", "prometheus",
        "grafana", "nginx",
    },
    "Databases": {
        "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
        "cassandra", "dynamodb", "neo4j", "sqlite", "oracle",
    },
    "BI & Analytics": {"powerbi", "tableau", "looker", "excel", "power query"},
    "Methodologies": {
        "agile", "scrum", "devops", "microservices", "system design",
        "object oriented", "tdd", "bdd",
    },
    "Mobile": {"android", "ios", "flutter", "react native"},
    "Other": {"blockchain", "cybersecurity", "networking", "embedded systems"},
}


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

def inject_css() -> None:
    """Inject the shared glassmorphism stylesheet. Safe to call on every page."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        :root {
            --ink:#0f172a; --muted:#64748b; --canvas:#eef2f7; --surface:#ffffff;
            --border:rgba(148,163,184,0.28); --accent:#059669; --accent-dark:#047857;
            --accent-soft:#ecfdf5;
            --glass:rgba(255,255,255,0.62);
            --glass-strong:rgba(255,255,255,0.78);
            --glass-border:rgba(255,255,255,0.65);
            --glass-shadow:0 12px 40px -16px rgba(15,23,42,0.22), inset 0 1px 0 rgba(255,255,255,0.6);
            --blur:saturate(180%) blur(20px);
        }

        html, body, [class*="css"], .stMarkdown, p, span, div, label, input, textarea, button {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        h1, h2, h3, h4, .hero h1, .job-title { font-family: 'Outfit', sans-serif; letter-spacing:-0.02em; color: var(--ink); }

        /* ── Ambient gradient backdrop (the canvas glass sits on) ── */
        .stApp {
            background:
                radial-gradient(circle at 12% 18%, rgba(16,185,129,0.20), transparent 42%),
                radial-gradient(circle at 88% 12%, rgba(45,212,191,0.18), transparent 40%),
                radial-gradient(circle at 78% 88%, rgba(59,130,246,0.14), transparent 45%),
                radial-gradient(circle at 20% 92%, rgba(99,102,241,0.12), transparent 45%),
                linear-gradient(135deg, #eef2f7 0%, #e6eef0 50%, #eaf0f6 100%);
            background-attachment: fixed;
        }
        .block-container { padding-top: 2.2rem; }

        /* ── Hero (dark frosted glass) ── */
        .hero {
            position: relative; overflow: hidden;
            background: linear-gradient(135deg, rgba(15,23,42,0.92) 0%, rgba(19,49,43,0.90) 55%, rgba(6,78,74,0.90) 100%);
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
            border-radius: 28px; padding: 2.7rem 2.7rem 2.4rem;
            margin-bottom: 1.8rem; color: #f8fafc;
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: 0 30px 70px -34px rgba(6,78,74,0.55), inset 0 1px 0 rgba(255,255,255,0.12);
        }
        .hero::after {
            content:""; position:absolute; top:-45%; right:-12%; width:420px; height:420px;
            background: radial-gradient(circle, rgba(16,185,129,0.40) 0%, rgba(16,185,129,0) 70%);
            pointer-events:none;
        }
        .hero::before {
            content:""; position:absolute; bottom:-55%; left:-8%; width:360px; height:360px;
            background: radial-gradient(circle, rgba(45,212,191,0.28) 0%, rgba(45,212,191,0) 70%);
            pointer-events:none;
        }
        .hero h1 { font-size: 2.4rem; font-weight: 800; margin: 0 0 0.4rem; line-height:1.05; color:#f8fafc; position:relative; }
        .hero p  { font-size: 1.02rem; color: rgba(248,250,252,0.74); margin: 0; max-width: 60ch; position:relative; }
        .hero .badge {
            display: inline-flex; align-items:center; gap:6px; position:relative;
            background: rgba(16,185,129,0.18); color: #6ee7b7;
            border: 1px solid rgba(110,231,183,0.36); border-radius: 999px;
            padding: 0.3rem 0.95rem; font-size: 0.72rem; margin-bottom: 1rem;
            font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
            -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);
        }

        /* ── Glass cards / panels ── */
        .search-card {
            background: var(--glass);
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
            border-radius: 24px; padding: 2rem 2.2rem 1.7rem;
            box-shadow: var(--glass-shadow); margin-bottom: 2rem;
            border: 1px solid var(--glass-border);
        }
        .search-card h3 {
            font-size: 1.08rem; font-weight: 700; color: var(--ink); margin: 0 0 1.2rem;
            padding-bottom: 0.7rem; border-bottom: 1px solid rgba(148,163,184,0.22);
        }
        .section-label {
            font-size: 0.74rem; font-weight: 700; color: var(--muted); text-transform: uppercase;
            letter-spacing: 0.07em; margin-bottom: 0.35rem;
        }
        .required-dot {
            display:inline-block; width:6px; height:6px; background:var(--accent);
            border-radius:50%; margin-left:5px; vertical-align:middle;
            box-shadow:0 0 0 3px rgba(5,150,105,0.18);
        }

        /* ── Glass job card ── */
        .job-card {
            background: var(--glass-strong);
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
            border-radius: 20px; padding: 1.5rem 1.8rem; margin-bottom: 1.1rem;
            box-shadow: var(--glass-shadow);
            border: 1px solid var(--glass-border); border-left: 3px solid var(--accent);
            transition: box-shadow .25s cubic-bezier(.16,1,.3,1), transform .25s cubic-bezier(.16,1,.3,1);
        }
        .job-card:hover { transform: translateY(-3px); box-shadow: 0 26px 50px -26px rgba(5,150,105,0.40), inset 0 1px 0 rgba(255,255,255,0.6); }
        .job-title { font-size: 1.12rem; font-weight: 700; color: var(--ink); margin-bottom: 0.2rem; }
        .job-company { font-size: 0.92rem; color: var(--accent-dark); font-weight: 600; margin-bottom: 0.6rem; }
        .mono { font-family:'JetBrains Mono', monospace; }

        .tag {
            display:inline-block; background:rgba(241,245,249,0.7); color:#475569; border:1px solid rgba(148,163,184,0.3);
            border-radius:999px; padding:0.2rem 0.7rem; font-size:0.78rem; font-weight:600;
            margin-right:0.35rem; margin-top:0.3rem;
        }
        .tag-salary { background: rgba(236,253,245,0.85); color: var(--accent-dark); border-color:rgba(110,231,183,0.5); }
        .tag-score  { background:rgba(255,247,237,0.85); color:#9a3412; border-color:rgba(254,215,170,0.7); }
        .tag-score .mono { font-weight:600; }

        .apply-btn {
            display:inline-block; background:var(--ink); color:#fff !important; border-radius:11px;
            padding:0.42rem 1.05rem; font-size:0.84rem; font-weight:600; text-decoration:none !important;
            margin-top:0.85rem; transition: transform .15s ease, box-shadow .2s ease;
            box-shadow:0 8px 18px -10px rgba(15,23,42,0.6);
        }
        .apply-btn:hover { transform: translateY(-1px); }
        .apply-btn:active { transform: translateY(0px) scale(0.98); }

        /* ── Stats strip (frosted dark) ── */
        .stats-strip {
            background: linear-gradient(100deg, rgba(15,23,42,0.92) 0%, rgba(6,78,74,0.90) 100%);
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
            border-radius: 16px; border:1px solid rgba(255,255,255,0.12);
            padding: 1rem 1.5rem; color: #f8fafc; font-weight: 600; text-align: center;
            margin-bottom: 1.6rem; font-size: 0.98rem;
            box-shadow:0 18px 40px -24px rgba(6,78,74,0.5);
        }
        .stats-strip .mono, .stats-strip strong { color:#6ee7b7; }

        /* ── Score tiles ── */
        .tile {
            border-radius:18px; padding:1rem 1.15rem; border:1px solid var(--glass-border);
            background:var(--glass); -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
            box-shadow: var(--glass-shadow);
        }
        .tile .lbl { font-size:0.7rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); font-weight:700; }
        .tile .val { font-size:1.5rem; font-weight:800; font-family:'Outfit',sans-serif; margin-top:0.15rem; }

        /* ── Streamlit control overrides ── */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
            color: #fff; border: 1px solid rgba(255,255,255,0.18); border-radius: 12px;
            padding: 0.6rem 1.5rem; font-size: 0.92rem; font-weight: 600; width: 100%;
            transition: transform .15s ease, box-shadow .2s ease, filter .2s ease;
            box-shadow: 0 10px 24px -10px rgba(5,150,105,0.7);
        }
        .stButton > button:hover { filter:brightness(1.06); transform: translateY(-1px); box-shadow:0 16px 30px -12px rgba(5,150,105,0.75); }
        .stButton > button:active { transform: translateY(1px) scale(0.99); }

        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] > div {
            border-radius: 12px !important; border: 1.5px solid var(--border) !important;
            font-size: 0.93rem; background: rgba(255,255,255,0.7) !important;
            -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
        }
        div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(5,150,105,0.16) !important;
        }

        /* file uploader, expander & tabs as glass */
        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255,255,255,0.55) !important; border-radius:16px !important;
            border:1.5px dashed rgba(148,163,184,0.45) !important;
            -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
        }
        [data-testid="stExpander"] {
            border:1px solid var(--glass-border) !important; border-radius:16px !important;
            background: var(--glass) !important; overflow:hidden;
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
        }
        .stTabs [data-baseweb="tab-list"] { gap:6px; }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.5); border-radius:12px 12px 0 0;
            padding:0.4rem 1rem;
        }
        .stTabs [aria-selected="true"] { background: var(--glass-strong); color: var(--accent-dark); }

        [data-testid="stMetric"] {
            background: var(--glass); border:1px solid var(--glass-border); border-radius:16px;
            padding:0.8rem 1rem; box-shadow: var(--glass-shadow);
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
        }
        [data-testid="stMetricValue"] { font-family:'Outfit',sans-serif; font-weight:800; color:var(--ink); }

        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.55);
            -webkit-backdrop-filter: var(--blur); backdrop-filter: var(--blur);
            border-right:1px solid var(--glass-border);
        }

        .divider-soft { border:none; border-top:1px solid rgba(148,163,184,0.25); margin: 1.2rem 0; }
        .status-pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.72rem; font-weight:700; }
        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, badge: str | None = None) -> None:
    """Render the page header used at the top of each page."""
    badge_html = f'<div class="badge">{html_lib.escape(badge)}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="hero">
            {badge_html}
            <h1>{html_lib.escape(title)}</h1>
            <p>{html_lib.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tile(label: str, value: str, color: str | None = None) -> str:
    """Return HTML for a single metric tile (use inside a flex row)."""
    col = color or INK
    return (f'<div class="tile"><div class="lbl">{html_lib.escape(label)}</div>'
            f'<div class="val" style="color:{col};">{html_lib.escape(value)}</div></div>')


# ---------------------------------------------------------------------------
# Skill helpers
# ---------------------------------------------------------------------------

_CHIP_PALETTE = [
    ("#ecfdf5", "#047857"), ("#eff6ff", "#1d4ed8"), ("#fef9c3", "#854d0e"),
    ("#fdf2f8", "#9d174d"), ("#f5f3ff", "#5b21b6"), ("#fff7ed", "#9a3412"),
]


def skill_chip_html(skills: list[str]) -> str:
    """Render a flat skill list as coloured inline pill badges."""
    chips = []
    for i, skill in enumerate(skills):
        bg, fg = _CHIP_PALETTE[i % len(_CHIP_PALETTE)]
        chips.append(
            f'<span style="background:{bg}; color:{fg}; border-radius:999px; '
            f'padding:3px 11px; font-size:0.78rem; font-weight:600; '
            f'margin:3px 4px 3px 0; display:inline-block;">{html_lib.escape(skill)}</span>'
        )
    return "".join(chips)


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    """Group a flat list of skills into named categories (non-empty buckets only)."""
    result: dict[str, list[str]] = {}
    for category, members in _SKILL_CATEGORIES.items():
        hits = sorted(s for s in skills if s.lower() in members)
        if hits:
            result[category] = hits
    known = {s for members in _SKILL_CATEGORIES.values() for s in members}
    leftover = sorted(s for s in skills if s.lower() not in known)
    if leftover:
        result.setdefault("Other", [])
        result["Other"].extend(leftover)
    return result


def extract_skills_from_pdf_bytes(pdf_bytes: bytes | None) -> list[str]:
    """Quick offline skill detection from raw PDF bytes (no pipeline run)."""
    if not PDF_AVAILABLE or not pdf_bytes:
        return []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        raw = " ".join(page.extract_text() or "" for page in reader.pages).lower()
        found = {skill for skill in PREDEFINED_SKILLS
                 if re.search(r'\b' + re.escape(skill) + r'\b', raw)}
        return sorted(found)
    except Exception:
        return []


def extract_text_from_pdf_bytes(pdf_bytes: bytes | None) -> str:
    """Return cleaned plain text from PDF bytes, or '' on failure."""
    if not PDF_AVAILABLE or not pdf_bytes:
        return ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        raw = " ".join(page.extract_text() or "" for page in reader.pages)
        return re.sub(r"\s+", " ", raw).strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Job card
# ---------------------------------------------------------------------------

def render_job_card(job: dict, rank: int) -> None:
    """Render a single job listing as a styled HTML card. All text is escaped."""
    e = html_lib.escape
    title = e(str(job.get("title", "N/A")))
    company = e(str(job.get("company", "Unknown")))
    location = e(str(job.get("location", "Unknown")))
    salary_label = e(str(job.get("salary_label", "Salary not disclosed")))
    desc = e(str(job.get("description", "")))
    rec_score = job.get("recommendation_score", 0)
    culture_wlb = e(str(job.get("culture_wlb", "Moderate")))
    culture_growth = e(str(job.get("culture_growth", "Moderate")))
    culture_salary = e(str(job.get("culture_salary", "Average")))
    culture_remote = e(str(job.get("culture_remote", "Hybrid")))
    culture_sum = e(str(job.get("culture_summary", "")))

    apply_html = (
        f'<a class="apply-btn" href="{e(str(job.get("url")))}" target="_blank">View role &rarr;</a>'
        if job.get("url") and job["url"] != "#" else ""
    )

    matched = job.get("matched_skills", [])
    skill_badge_html = ""
    if matched:
        badges = " ".join(
            f'<span style="background:#ecfdf5; color:#047857; border-radius:999px; '
            f'padding:2px 9px; font-size:0.74rem; font-weight:600; margin:2px 3px 2px 0; '
            f'display:inline-block;">&#10003; {e(s)}</span>' for s in matched[:6]
        )
        skill_badge_html = (
            '<div style="margin-top:0.55rem;">'
            '<span style="font-size:0.74rem; color:#047857; font-weight:700; '
            'text-transform:uppercase; letter-spacing:0.04em;">Resume skills matched</span> '
            + badges + '</div>'
        )

    card_html = (
        '<div class="job-card">'
        f'<div class="job-title"><span class="mono" style="color:#a1a1aa;">{rank:02d}</span> &nbsp;{title}</div>'
        f'<div class="job-company">{company}</div>'
        f'<span class="tag">{location}</span>'
        f'<span class="tag tag-salary">{salary_label}</span>'
        f'<span class="tag tag-score">Rec <span class="mono">{e(str(rec_score))}</span></span>'
        + skill_badge_html
        + f'<p style="margin:0.8rem 0 0.4rem; color:var(--muted); font-size:0.86rem; line-height:1.55;">{desc}</p>'
        '<div style="margin-top:0.8rem; padding:0.7rem 0.9rem; background:#fafafa; '
        'border-radius:12px; border:1px solid #f1f1f3; font-size:0.82rem;">'
        '<strong style="color:var(--ink);">Company culture</strong><br/>'
        f'<strong>WLB:</strong> {culture_wlb} &nbsp;&middot;&nbsp; '
        f'<strong>Growth:</strong> {culture_growth} &nbsp;&middot;&nbsp; '
        f'<strong>Pay:</strong> {culture_salary} &nbsp;&middot;&nbsp; '
        f'<strong>Remote:</strong> {culture_remote}<br/>'
        f'<span style="color:var(--muted); display:block; margin-top:0.3rem; line-height:1.45;">{culture_sum}</span>'
        '</div>'
        + apply_html
        + '</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)


STATUS_COLORS = {
    "Saved":     ("#f4f4f5", "#3f3f46"),
    "Applied":   ("#eff6ff", "#1d4ed8"),
    "Interview": ("#fff7ed", "#9a3412"),
    "Offer":     ("#ecfdf5", "#047857"),
    "Rejected":  ("#fef2f2", "#b91c1c"),
    "Fetched":   ("#f4f4f5", "#71717a"),
}


def status_pill_html(status: str) -> str:
    """Coloured status badge for the application tracker."""
    bg, fg = STATUS_COLORS.get(status, ("#f4f4f5", "#71717a"))
    return (f'<span class="status-pill" style="background:{bg}; color:{fg};">'
            f'{html_lib.escape(status)}</span>')


# ---------------------------------------------------------------------------
# Error messaging
# ---------------------------------------------------------------------------

def _redact_secrets(text: str) -> str:
    """Strip any configured API keys out of a string before showing it."""
    import config
    for secret in (config.ADZUNA_APP_ID, config.ADZUNA_APP_KEY, config.JOOBLE_API_KEY):
        if secret:
            text = text.replace(secret, "***")
    return text


def friendly_api_error(exc: Exception) -> str:
    """Translate a raw exception into a clear, actionable user message."""
    text = str(exc).lower()
    if any(k in text for k in ("timeout", "timed out")):
        return ("The job APIs took too long to respond. Check your internet "
                "connection and try again in a moment.")
    if any(k in text for k in ("connection", "name resolution", "getaddrinfo", "max retries")):
        return ("Could not reach the job APIs. You may be offline, or the service is "
                "temporarily unavailable. Please retry shortly.")
    if any(k in text for k in ("401", "403", "unauthorized", "forbidden", "invalid api")):
        return ("An API rejected the request — your credentials may be invalid or expired. "
                "Re-check your Adzuna / Jooble keys in the sidebar or `.env`.")
    if "429" in text or "rate limit" in text:
        return ("The job API rate limit was hit. Wait a minute before searching again, "
                "or reduce the number of results requested.")
    return f"Something went wrong while contacting the job APIs: {_redact_secrets(str(exc))}"
