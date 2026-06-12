import streamlit as st
import pandas as pd
import io
import re
import html as html_lib
from database import initialize_database, save_job, save_search_history, save_user_preferences, get_saved_jobs, SUPPORTED_CITIES
from agents.location_agent import LocationIntelligenceAgent
from agents.salary_agent import SalaryIntelligenceAgent
from agents.skills_agent import PREDEFINED_SKILLS
from orchestrator import AgentOrchestrator
import config  # loads .env automatically

try:
    import PyPDF2
    _PDF_AVAILABLE = True
except ImportError:
    _PDF_AVAILABLE = False

# Initialize database
initialize_database()


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Search AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hero ── */
    .hero {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 20px;
        padding: 2.5rem 2.5rem 2rem;
        margin-bottom: 1.8rem;
        text-align: center;
        color: white;
    }
    .hero h1 { font-size: 2.4rem; font-weight: 700; margin-bottom: 0.3rem; }
    .hero p  { font-size: 1.05rem; opacity: 0.75; margin: 0; }
    .hero .badge {
        display: inline-block;
        background: rgba(99,179,237,0.18);
        color: #63b3ed;
        border: 1px solid #63b3ed55;
        border-radius: 20px;
        padding: 0.2rem 0.9rem;
        font-size: 0.78rem;
        margin-bottom: 0.9rem;
        font-weight: 500;
    }

    /* ── Search card ── */
    .search-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 2rem 2.2rem 1.6rem;
        box-shadow: 0 4px 28px rgba(0,0,0,0.09);
        margin-bottom: 2rem;
        border: 1px solid #e8edf4;
    }
    .search-card h3 {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 1.2rem 0;
        padding-bottom: 0.7rem;
        border-bottom: 2px solid #f1f5f9;
    }
    .section-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.3rem;
    }
    .required-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        background: #ef4444;
        border-radius: 50%;
        margin-left: 4px;
        vertical-align: middle;
    }

    /* ── Job card ── */
    .job-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border-left: 4px solid #3b82f6;
        transition: box-shadow 0.2s;
    }
    .job-card:hover { box-shadow: 0 6px 24px rgba(59,130,246,0.15); }

    .job-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.3rem;
    }
    .job-company {
        font-size: 0.95rem;
        color: #3b82f6;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .tag {
        display: inline-block;
        background: #f1f5f9;
        color: #475569;
        border-radius: 8px;
        padding: 0.2rem 0.7rem;
        font-size: 0.82rem;
        font-weight: 500;
        margin-right: 0.4rem;
        margin-top: 0.3rem;
    }
    .tag-salary { background: #d1fae5; color: #065f46; }
    .apply-btn {
        display: inline-block;
        background: #3b82f6;
        color: white !important;
        border-radius: 8px;
        padding: 0.35rem 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        margin-top: 0.8rem;
    }
    .apply-btn:hover { background: #2563eb; }

    /* ── Stats strip ── */
    .stats-strip {
        background: linear-gradient(90deg, #3b82f6 0%, #6366f1 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: white;
        font-weight: 600;
        text-align: center;
        margin-bottom: 1.8rem;
        font-size: 1rem;
    }

    /* ── Streamlit overrides ── */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #6366f1);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.88; }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        border: 1.5px solid #e2e8f0;
        font-size: 0.93rem;
        padding: 0.55rem 0.85rem;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.14);
    }

    .divider-soft {
        border: none;
        border-top: 1px dashed #e2e8f0;
        margin: 1.2rem 0;
    }

    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_skills_from_bytes(pdf_bytes: bytes) -> list[str]:
    """
    Lightweight instant skill extraction from uploaded PDF bytes.
    Used for the UI preview BEFORE the full pipeline runs.
    Returns a sorted list of detected skill strings.
    """
    if not _PDF_AVAILABLE or not pdf_bytes:
        return []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        raw = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        found = set()
        for skill in PREDEFINED_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', raw):
                found.add(skill)
        return sorted(found)
    except Exception:
        return []


def _skill_chip_html(skills: list[str]) -> str:
    """Render a list of skills as coloured inline pill badges."""
    COLORS = [
        ("#dbeafe", "#1d4ed8"),  # blue
        ("#dcfce7", "#166534"),  # green
        ("#fef9c3", "#854d0e"),  # yellow
        ("#fce7f3", "#9d174d"),  # pink
        ("#ede9fe", "#5b21b6"),  # purple
        ("#ffedd5", "#9a3412"),  # orange
    ]
    chips = []
    for i, skill in enumerate(skills):
        bg, fg = COLORS[i % len(COLORS)]
        chips.append(
            f'<span style="background:{bg}; color:{fg}; border-radius:20px; '
            f'padding:3px 10px; font-size:0.78rem; font-weight:600; '
            f'margin:3px 4px 3px 0; display:inline-block;">'
            f'{skill}</span>'
        )
    return "".join(chips)


def fetch_jobs(query: str, location: str, app_id: str, app_key: str, jooble_key: str,
               count: int = 10, expected_salary_lpa: float = None,
               work_prefs: dict = None,
               resume_bytes: bytes = None) -> list[dict]:
    """Delegates to AgentOrchestrator and maps enriched jobs to the UI schema."""
    try:
        orchestrator = AgentOrchestrator()
        context = orchestrator.build_context(
            search_role=query,
            search_location=location,
            expected_salary=expected_salary_lpa,
            work_mode=(work_prefs or {}).get("work_from_home_preference", "Remote"),
            notice_days=(work_prefs or {}).get("notice_period_days", 30),
            flexibility=(work_prefs or {}).get("flexibility_preference", "Strict"),
            resume_bytes=resume_bytes,
            adzuna_app_id=app_id,
            adzuna_app_key=app_key,
            jooble_api_key=jooble_key,
        )
        final = orchestrator.run_pipeline(context)

        # Store pipeline outputs in session state
        st.session_state["source_metadata"] = final.source_metadata
        st.session_state["salary_agent"] = SalaryIntelligenceAgent()
        st.session_state["pipeline_skills"] = final.skills  # skills detected by pipeline

        jobs = []
        for job in final.enriched_jobs:
            sal_lpa = job.get("salary_lpa")
            salary_label = job.get("normalized_salary", "Salary not disclosed")
            comparison = job.get("salary_comparison", "N/A")
            jobs.append({
                "title":               job.get("title", "N/A"),
                "company":             job.get("company", "Unknown"),
                "location":            job.get("location", "Unknown"),
                "salary_label":        salary_label,
                "salary_lpa":          sal_lpa,
                "salary_comparison":   comparison,
                "compatibility_score": job.get("compatibility_score", 0),
                "culture_wlb":         job.get("culture_wlb", "Moderate"),
                "culture_growth":      job.get("culture_growth", "Moderate"),
                "culture_salary":      job.get("culture_salary", "Average"),
                "culture_remote":      job.get("culture_remote", "Hybrid"),
                "culture_summary":     job.get("culture_summary", ""),
                "culture_score":       job.get("culture_score", 0),
                "recommendation_score": job.get("recommendation_score", 0),
                "matched_skills":      job.get("matched_skills", []),
                "description": (
                    f"Source: {job.get('source')} | "
                    f"Match: {job.get('match_score', 0)} | "
                    f"Culture: +{job.get('culture_score', 0)} | "
                    f"Rec Score: {job.get('recommendation_score', 0)}"
                ),
                "url":            "#",
                "created":        "",
                "source":         job.get("source"),
                "location_score": job.get("location_score", 0),
                "salary_score":   job.get("salary_score", 0),
            })
        return jobs
    except Exception as e:
        st.error(f"Error running agentic pipeline: {e}")
        return []


def render_job_card(job: dict, rank: int):
    """Renders a single job listing as a styled HTML card.
    All dynamic text is html-escaped to prevent broken markup from API data.
    """
    # --- Escape every dynamic text value ---
    e = html_lib.escape  # shorthand

    title          = e(str(job.get("title", "N/A")))
    company        = e(str(job.get("company", "Unknown")))
    location       = e(str(job.get("location", "Unknown")))
    salary_label   = e(str(job.get("salary_label", "Salary not disclosed")))
    desc           = e(str(job.get("description", "")))
    culture_wlb    = e(str(job.get("culture_wlb", "Moderate")))
    culture_growth = e(str(job.get("culture_growth", "Moderate")))
    culture_salary = e(str(job.get("culture_salary", "Average")))
    culture_remote = e(str(job.get("culture_remote", "Hybrid")))
    culture_sum    = e(str(job.get("culture_summary", "")))

    apply_html = (
        f'<a class="apply-btn" href="{e(job["url"])}" target="_blank">Apply now &rarr;</a>'
        if job.get("url") and job["url"] != "#"
        else ""
    )

    # --- Skill match badges (only shown when resume was uploaded) ---
    matched = job.get("matched_skills", [])
    skill_badge_html = ""
    if matched:
        badges = " ".join(
            f'<span style="background:#dcfce7; color:#166534; border-radius:20px; '
            f'padding:2px 8px; font-size:0.75rem; font-weight:600; margin:2px 3px 2px 0; '
            f'display:inline-block;">&#10003; {e(s)}</span>'
            for s in matched[:6]
        )
        skill_badge_html = (
            '<div style="margin-top:0.5rem;">'
            '<span style="font-size:0.75rem; color:#166534; font-weight:600;">'
            '&#11088; Resume skills matched:</span> ' + badges + '</div>'
        )

    card_html = (
        '<div class="job-card">'
        f'<div class="job-title">#{rank} &nbsp; {title}</div>'
        f'<div class="job-company">&#127962; &nbsp;{company}</div>'
        f'<span class="tag">&#128205; {location}</span>'
        f'<span class="tag tag-salary">&#128176; {salary_label}</span>'
        + skill_badge_html
        + f'<p style="margin:0.8rem 0 0.4rem; color:#64748b; font-size:0.88rem; line-height:1.55;">{desc}</p>'
        '<div style="margin-top:0.8rem; padding:0.6rem 0.8rem; background-color:#f8fafc; '
        'border-radius:8px; border-left:3px solid #6366f1; font-size:0.82rem;">'
        '<strong style="color:#4f46e5;">&#127962; Company Culture Insights</strong><br/>'
        f'&#9878; <strong>WLB:</strong> {culture_wlb} &nbsp;&bull;&nbsp; '
        f'&#128640; <strong>Growth:</strong> {culture_growth} &nbsp;&bull;&nbsp; '
        f'&#128181; <strong>Salary Comp:</strong> {culture_salary} &nbsp;&bull;&nbsp; '
        f'&#127968; <strong>Remote Friendly:</strong> {culture_remote}<br/>'
        f'<span style="color:#475569; display:block; margin-top:0.3rem; line-height:1.4;">{culture_sum}</span>'
        '</div>'
        + apply_html
        + '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)



# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <div class="badge">Agentic AI Pipeline &nbsp;·&nbsp; 9 Intelligent Agents</div>
        <h1>💼 Job Search AI</h1>
        <p>Fill in all fields below to get personalized, real-time job recommendations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar: API credentials + Saved Jobs ─────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ API Credentials")
    st.caption("Keys are pre-loaded from `.env`. Edit here to override for this session.")
    app_id = st.text_input(
        "Adzuna App ID",
        value=config.ADZUNA_APP_ID or "",
        type="default",
        placeholder="Set ADZUNA_APP_ID in .env",
    )
    app_key = st.text_input(
        "Adzuna App Key",
        value=config.ADZUNA_APP_KEY or "",
        type="password",
        placeholder="Set ADZUNA_APP_KEY in .env",
    )
    jooble_key = st.text_input(
        "Jooble API Key",
        value=config.JOOBLE_API_KEY or "",
        type="password",
        placeholder="Set JOOBLE_API_KEY in .env",
    )
    st.divider()
    st.markdown("### 📂 Saved Jobs")
    _loc_agent = LocationIntelligenceAgent()
    filter_city = st.selectbox(
        "Filter saved jobs by city",
        options=["All Cities"] + SUPPORTED_CITIES,
        index=0,
    )
    if filter_city == "All Cities":
        saved_list = get_saved_jobs()
    else:
        saved_list = _loc_agent.get_jobs_by_city(filter_city)

    if saved_list:
        st.write(f"Showing **{len(saved_list)}** saved job(s).")
        with st.expander("Show Saved Jobs", expanded=True):
            for j in saved_list:
                st.write(f"**{j['job_title']}**")
                st.caption(f"{j['company_name']} | {j['location']} | {j['application_status']}")
                st.divider()
    else:
        st.caption(f"No saved jobs found for {filter_city}.")
    st.divider()
    st.caption("© 2025 Job Search AI")


# ── Main Search Form ───────────────────────────────────────────────────────────
st.markdown(
    '<div class="search-card"><h3>🔍 Search Parameters <span style="font-size:0.72rem; color:#ef4444; font-weight:500; margin-left:6px;">● required fields</span></h3>',
    unsafe_allow_html=True,
)

# ── Resume Upload Section ──────────────────────────────────────────────────────
st.markdown('<div class="section-label">📄 Upload Resume (PDF) — <em style="font-weight:400; color:#64748b;">Optional · Skills will be auto-detected and boost your results</em></div>', unsafe_allow_html=True)

uploaded_resume = st.file_uploader(
    "Upload Resume PDF",
    type=["pdf"],
    label_visibility="collapsed",
    key="resume_uploader",
    help="Upload your resume as a PDF. The AI will extract your skills and use them to find better-matched jobs.",
)

resume_bytes = None
preview_skills = []

if uploaded_resume is not None:
    resume_bytes = uploaded_resume.read()
    # Instant skill preview (without running the full pipeline)
    preview_skills = _extract_skills_from_bytes(resume_bytes)
    col_status, _ = st.columns([3, 1])
    with col_status:
        st.success(f"✅ **{uploaded_resume.name}** uploaded ({len(resume_bytes) // 1024} KB)")
    if preview_skills:
        st.markdown(
            f'<div style="margin: 0.5rem 0 0.8rem 0;">'
            f'<span style="font-size:0.82rem; color:#166534; font-weight:700;">'
            f'🎯 {len(preview_skills)} skills detected from your resume:</span><br/>'
            f'<div style="margin-top:5px;">{_skill_chip_html(preview_skills)}</div></div>',
            unsafe_allow_html=True,
        )
    elif not _PDF_AVAILABLE:
        st.warning("⚠️ PyPDF2 not installed. Run: `pip install PyPDF2` then restart the app.")
    else:
        st.info("ℹ️ No standard tech skills detected — the resume will still be parsed by the AI pipeline.")
else:
    st.caption("💡 No resume uploaded — search will use your Job Role and preferences only.")

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)

# Row 1 — Role & Location
col_r, col_l = st.columns([2, 2])
with col_r:
    st.markdown('<div class="section-label">Job Role <span class="required-dot"></span></div>', unsafe_allow_html=True)
    role = st.text_input(
        "Job Role",
        placeholder="e.g. Python Developer, Data Scientist, DevOps Engineer…",
        label_visibility="collapsed",
        key="input_role",
    )

with col_l:
    st.markdown('<div class="section-label">City / Location <span class="required-dot"></span></div>', unsafe_allow_html=True)
    city = st.selectbox(
        "City",
        options=SUPPORTED_CITIES,
        index=0,
        label_visibility="collapsed",
        key="input_city",
    )

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)

# Row 2 — Salary & Results count
col_s, col_c = st.columns([2, 2])
with col_s:
    st.markdown('<div class="section-label">Expected Salary (LPA) <span class="required-dot"></span></div>', unsafe_allow_html=True)
    expected_salary = st.slider(
        "Expected Salary",
        min_value=0.0,
        max_value=100.0,
        value=12.0,
        step=0.5,
        label_visibility="collapsed",
        key="input_salary",
        help="Set your expected annual salary in Lakhs Per Annum (LPA). Jobs will be scored based on this.",
    )
    st.caption(f"Selected: ₹ **{expected_salary:.1f} LPA**")

with col_c:
    st.markdown('<div class="section-label">Results to Fetch <span class="required-dot"></span></div>', unsafe_allow_html=True)
    results_count = st.slider(
        "Results",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        label_visibility="collapsed",
        key="input_count",
        help="Number of job listings to fetch from each API connector.",
    )
    st.caption(f"Fetching up to **{results_count}** results per source")

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)

# Row 3 — Work Preferences
st.markdown('<div class="section-label">Work Preferences <span class="required-dot"></span></div>', unsafe_allow_html=True)
col_wm, col_np, col_fl = st.columns(3)

with col_wm:
    work_mode = st.selectbox(
        "Work Mode",
        options=["Remote", "Hybrid", "Onsite"],
        index=0,
        key="input_work_mode",
        help="Your preferred work arrangement. Jobs will be scored for compatibility.",
    )

with col_np:
    notice_days = st.selectbox(
        "Notice Period",
        options=[0, 15, 30, 45, 60, 90, 120, 180],
        index=2,
        format_func=lambda x: f"{x} days" if x > 0 else "Immediate",
        key="input_notice",
        help="How many days notice you need to give your current employer.",
    )

with col_fl:
    flexibility = st.selectbox(
        "Flexibility",
        options=["Strict", "Flexible"],
        index=1,
        key="input_flex",
        help="'Flexible' allows partial matches for notice period. 'Strict' requires exact match.",
    )

# ── Search button ──────────────────────────────────────────────────────────────
st.markdown("<br/>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    search = st.button("🚀 Search Jobs", key="search_btn")

st.markdown("</div>", unsafe_allow_html=True)

# ── Validation & Results ───────────────────────────────────────────────────────

if search:
    # Validate required fields
    errors = []
    if not role.strip():
        errors.append("**Job Role** cannot be empty.")

    if errors:
        for e in errors:
            st.error(f"⚠️ {e}")
    else:
        work_prefs = {
            "work_from_home_preference": work_mode,
            "notice_period_days": notice_days,
            "flexibility_preference": flexibility,
        }

        # Show a summary of the search parameters
        skills_info = ""
        if preview_skills:
            top_skills = ", ".join(preview_skills[:5])
            skills_info = f" · 🎯 Resume skills: **{top_skills}**" + (" +more" if len(preview_skills) > 5 else "")
        st.info(
            f"🔍 Searching for **{role.strip()}** in **{city}** · "
            f"Salary: ₹{expected_salary:.1f} LPA · "
            f"Work Mode: {work_mode} · "
            f"Notice: {notice_days} days · "
            f"Flexibility: {flexibility}"
            + skills_info
        )

        spinner_msg = (
            f"Running 9-agent pipeline for **{role.strip()}** in **{city}**"
            + (f" with {len(preview_skills)} resume skills…" if preview_skills else "…")
        )
        with st.spinner(spinner_msg):
            jobs = fetch_jobs(
                role.strip(), city,
                app_id.strip(), app_key.strip(), jooble_key.strip(),
                results_count, expected_salary, work_prefs,
                resume_bytes=resume_bytes,
            )

        if not jobs:
            st.warning("⚠️ No jobs found for that search. Try a broader role, different city, or adjust salary expectations.")
        else:
            # Save search history & user preferences
            save_search_history(role.strip(), city)
            save_user_preferences(
                preferred_location=city,
                preferred_role=role.strip(),
                work_from_home_preference=work_mode,
                notice_period_days=notice_days,
                flexibility_preference=flexibility,
            )

            # ── Stats strip ──
            disclosed = [j for j in jobs if j.get("salary_lpa")]
            avg_salary = (
                f"₹{sum(j['salary_lpa'] for j in disclosed) / len(disclosed):.1f} LPA"
                if disclosed else "N/A"
            )
            st.markdown(
                f'<div class="stats-strip">'
                f'Found <strong>{len(jobs)}</strong> listings · '
                f'Avg advertised salary: <strong>{avg_salary}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Connector Source Quality ──
            if "source_metadata" in st.session_state:
                with st.expander("📊 Connector Source Quality Stats", expanded=False):
                    st.write("Performance and yield metrics across integrated platforms:")
                    meta = st.session_state["source_metadata"]
                    df_stats = pd.DataFrame([
                        {
                            "Platform": src,
                            "Successful Fetches": stats["successful_fetches"],
                            "Total Attempts": stats["total_fetches"],
                            "Success Rate": f"{stats['success_rate_percent']}%",
                            "Jobs Discovered": stats["total_jobs_yielded"],
                        }
                        for src, stats in meta.items()
                    ])
                    st.dataframe(df_stats, use_container_width=True, hide_index=True)

            # ── Historical Salary Trends ──
            _sal_agent = st.session_state.get("salary_agent")
            historical_stats = _sal_agent.get_historical_ranges(role.strip(), city) if _sal_agent else []
            if historical_stats:
                with st.expander("📈 Historical Salary Trends", expanded=False):
                    st.write(f"Historical salary ranges logged for **{role.strip()}** in **{city}**:")
                    df_hist = pd.DataFrame([
                        {
                            "Date/Time": h["timestamp"],
                            "Min Salary": f"₹{h['min_salary_lpa']:.1f} LPA",
                            "Max Salary": f"₹{h['max_salary_lpa']:.1f} LPA",
                            "Avg Salary": f"₹{h['avg_salary_lpa']:.1f} LPA",
                        }
                        for h in historical_stats
                    ])
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)

            # ── Metrics ──
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Results", len(jobs))
            m2.metric("With Salary Info", len(disclosed))
            m3.metric("Unique Locations", len({j["location"] for j in jobs}))

            # ── Tabs ──
            tab_cards, tab_table, tab_csv = st.tabs(["📋  Job Cards", "📊  Table View", "⬇️  Download CSV"])

            with tab_cards:
                for i, job in enumerate(jobs, 1):
                    render_job_card(job, i)
                    btn_key = f"save_btn_{i}_{job['company']}_{job['title']}"
                    if st.button(f"💾 Save: {job['title']} at {job['company']}", key=btn_key):
                        saved_id = save_job(
                            job_title=job["title"],
                            company_name=job["company"],
                            location=job["location"],
                            salary_lpa=job.get("salary_lpa"),
                            source_platform=job.get("source", "Unknown"),
                            application_status="Saved",
                        )
                        if saved_id:
                            st.success("Job saved successfully!")
                            st.rerun()

            with tab_table:
                df = pd.DataFrame([
                    {
                        "Recommendation Score": j.get("recommendation_score", 0),
                        "Title": j["title"],
                        "Company": j["company"],
                        "Location": j["location"],
                        "Salary": j["salary_label"],
                        "Salary vs Expectation": j.get("salary_comparison", "N/A"),
                        "Location Score": j.get("location_score", 0),
                        "Work Pref Score": j.get("compatibility_score", 0),
                        "Culture WLB": j.get("culture_wlb", "Moderate"),
                        "Culture Growth": j.get("culture_growth", "Moderate"),
                        "Culture Salary": j.get("culture_salary", "Average"),
                        "Culture Remote": j.get("culture_remote", "Hybrid"),
                        "Source": j.get("source", "Unknown"),
                    }
                    for j in jobs
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)

            with tab_csv:
                df_full = pd.DataFrame(jobs)
                csv = df_full.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download results as CSV",
                    data=csv,
                    file_name=f"jobs_{role.replace(' ', '_')}_{city.replace(' ', '_')}.csv",
                    mime="text/csv",
                )

# ── Empty state ────────────────────────────────────────────────────────────────
else:
    st.markdown(
        """
        <div style="text-align:center; padding: 2.5rem 1rem; color: #94a3b8;">
            <div style="font-size:3.5rem;">🔍</div>
            <p style="font-size:1.05rem; margin-top:0.9rem; color: #64748b;">
                Fill in the search parameters above and hit <strong style="color:#3b82f6;">Search Jobs</strong> to get started.
            </p>
            <p style="font-size:0.88rem; color: #94a3b8; margin-top:0.4rem;">
                All fields marked with <span style="color:#ef4444;">●</span> are required for best results.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
