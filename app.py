import streamlit as st
import requests
import pandas as pd

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
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hero gradient header ── */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%);
        border-radius: 20px;
        padding: 3rem 2.5rem 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .hero h1 { font-size: 2.6rem; font-weight: 700; margin-bottom: 0.4rem; }
    .hero p  { font-size: 1.1rem; opacity: 0.8; margin: 0; }
    .hero .badge {
        display: inline-block;
        background: rgba(99,179,237,0.2);
        color: #63b3ed;
        border: 1px solid #63b3ed55;
        border-radius: 20px;
        padding: 0.2rem 0.9rem;
        font-size: 0.8rem;
        margin-bottom: 1rem;
        font-weight: 500;
    }

    /* ── Search card ── */
    .search-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
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
        font-size: 1.15rem;
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
    .tag-salary {
        background: #d1fae5;
        color: #065f46;
    }

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

    /* ── Metric cards ── */
    .metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    .metric-box {
        flex: 1;
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .metric-box .val { font-size: 1.6rem; font-weight: 700; color: #1e293b; }
    .metric-box .lbl { font-size: 0.78rem; color: #94a3b8; font-weight: 500; }

    /* ── Streamlit overrides ── */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6, #6366f1);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover { opacity: 0.9; }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        border: 1.5px solid #e2e8f0;
        font-size: 0.95rem;
        padding: 0.6rem 0.9rem;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
    }

    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def fetch_jobs(query: str, location: str, app_id: str, app_key: str, count: int = 10) -> list[dict]:
    """
    Calls the Adzuna Jobs API and returns a list of job dicts.
    Returns an empty list on any error so the UI degrades gracefully.
    """
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "where": location,
        "results_per_page": count,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't reach Adzuna — {e}")
        return []

    data = resp.json()
    jobs = []
    for job in data.get("results", []):
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")

        if salary_min and salary_max:
            salary_label = f"₹{salary_min:,.0f} – ₹{salary_max:,.0f} / yr"
        elif salary_min:
            salary_label = f"from ₹{salary_min:,.0f}"
        else:
            salary_label = "Salary not disclosed"

        jobs.append({
            "title": job.get("title", "N/A"),
            "company": job["company"]["display_name"],
            "location": job["location"]["display_name"],
            "salary_label": salary_label,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "description": job.get("description", "")[:200].strip() + "…",
            "url": job.get("redirect_url", "#"),
            "created": job.get("created", ""),
        })

    return jobs


def render_job_card(job: dict, rank: int):
    """Renders a single job listing as a styled HTML card."""
    desc = job["description"] if job["description"] else ""
    apply_html = (
        f'<a class="apply-btn" href="{job["url"]}" target="_blank">Apply now →</a>'
        if job["url"] != "#"
        else ""
    )

    st.markdown(
        f"""
        <div class="job-card">
            <div class="job-title">#{rank} &nbsp; {job['title']}</div>
            <div class="job-company">🏢 &nbsp;{job['company']}</div>
            <span class="tag">📍 {job['location']}</span>
            <span class="tag tag-salary">💰 {job['salary_label']}</span>
            <p style="margin:0.8rem 0 0.4rem; color:#64748b; font-size:0.88rem; line-height:1.55;">{desc}</p>
            {apply_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Hero ───────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="hero">
        <div class="badge">Powered by Adzuna</div>
        <h1>💼 Job Search AI</h1>
        <p>Find your next opportunity — just tell us the role and city.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── API credentials (sidebar) ──────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ API Credentials")
    st.caption("Get free keys at [adzuna.com/api](https://developer.adzuna.com/)")
    app_id  = st.text_input("App ID",  value="c6f6b204",                 type="default")
    app_key = st.text_input("App Key", value="5fd40344881248436df8a9b0198ef5c6", type="password")
    st.divider()
    results_per_page = st.slider("Results to fetch", min_value=5, max_value=50, value=10, step=5)
    st.caption("© 2025 Job Search AI")

# ── Search form ────────────────────────────────────────────────────────────────

with st.container():
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        role = st.text_input("Job role", placeholder="e.g. Python Developer, Data Scientist…", label_visibility="collapsed")
    with col2:
        city = st.text_input("City", placeholder="e.g. Bengaluru, Mumbai, Delhi…", label_visibility="collapsed")
    with col3:
        search = st.button("Search Jobs")

# ── Results ────────────────────────────────────────────────────────────────────

if search:
    if not role.strip() or not city.strip():
        st.warning("Please fill in both a job role and a city before searching.")
    elif not app_id.strip() or not app_key.strip():
        st.error("Add your Adzuna API credentials in the sidebar first.")
    else:
        with st.spinner(f"Searching for **{role}** roles in **{city}**…"):
            jobs = fetch_jobs(role.strip(), city.strip(), app_id.strip(), app_key.strip(), results_per_page)

        if not jobs:
            st.info("No jobs found for that search. Try a broader role or a different city.")
        else:
            # ── Stats strip ──
            disclosed = [j for j in jobs if j["salary_min"]]
            avg_salary = (
                f"₹{sum(j['salary_min'] for j in disclosed) / len(disclosed):,.0f}"
                if disclosed else "N/A"
            )
            st.markdown(
                f'<div class="stats-strip">'
                f'Found <strong>{len(jobs)}</strong> listings · '
                f'Avg advertised salary: <strong>{avg_salary}</strong>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Metric boxes ──
            m1, m2, m3 = st.columns(3)
            m1.metric("Total results", len(jobs))
            m2.metric("With salary info", len(disclosed))
            m3.metric("Cities found", len({j["location"] for j in jobs}))

            # ── Tabs: Cards | Table | Download ──
            tab_cards, tab_table, tab_csv = st.tabs(["📋  Job Cards", "📊  Table View", "⬇️  Download CSV"])

            with tab_cards:
                for i, job in enumerate(jobs, 1):
                    render_job_card(job, i)

            with tab_table:
                df = pd.DataFrame([
                    {
                        "Title": j["title"],
                        "Company": j["company"],
                        "Location": j["location"],
                        "Salary": j["salary_label"],
                        "Apply": j["url"],
                    }
                    for j in jobs
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)

            with tab_csv:
                df_full = pd.DataFrame(jobs)
                csv = df_full.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name=f"jobs_{role.replace(' ', '_')}_{city.replace(' ', '_')}.csv",
                    mime="text/csv",
                )

# ── Empty state ────────────────────────────────────────────────────────────────
else:
    st.markdown(
        """
        <div style="text-align:center; padding: 3rem 1rem; color: #94a3b8;">
            <div style="font-size:4rem;">🔍</div>
            <p style="font-size:1.1rem; margin-top:1rem;">
                Type a role and city above, then hit <strong>Search Jobs</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
