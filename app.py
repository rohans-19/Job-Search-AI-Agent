"""
app.py
------
Job Search AI — main dashboard (Streamlit multi-page app home).

This page runs the 9-agent pipeline and renders an interactive, filterable,
sortable job-search dashboard. Sibling pages live in ./pages:
  - Resume Analysis
  - Company Research
  - Application Tracker
  - Analytics

Results are cached in st.session_state so other pages (and the export buttons)
can reuse the most recent search without re-running the pipeline.
"""

import pandas as pd
import streamlit as st

import config  # loads .env automatically
from database import (
    initialize_database, save_job, save_search_history, save_user_preferences,
    get_saved_jobs, SUPPORTED_CITIES, VALID_APPLICATION_STATUSES,
)
from agents.location_agent import LocationIntelligenceAgent
from agents.salary_agent import SalaryIntelligenceAgent
from orchestrator import AgentOrchestrator
from validation import (
    validate_resume_upload, validate_search_params, has_any_api_credentials,
)
from exporters import jobs_to_csv, jobs_to_pdf, is_pdf_available
import ui_common as ui

initialize_database()

st.set_page_config(
    page_title="Job Search AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.inject_css()


# ── Pipeline call ────────────────────────────────────────────────────────────
def run_search(role, location, app_id, app_key, jooble_key,
               count, expected_salary, work_prefs, resume_bytes):
    """Run the orchestrator and map enriched jobs to the UI schema.

    Returns (jobs, error_message). On success error_message is None.
    """
    try:
        orchestrator = AgentOrchestrator()
        ctx = orchestrator.build_context(
            search_role=role, search_location=location,
            expected_salary=expected_salary,
            work_mode=work_prefs.get("work_from_home_preference", "Remote"),
            notice_days=work_prefs.get("notice_period_days", 30),
            flexibility=work_prefs.get("flexibility_preference", "Strict"),
            resume_bytes=resume_bytes,
            adzuna_app_id=app_id, adzuna_app_key=app_key, jooble_api_key=jooble_key,
        )
        final = orchestrator.run_pipeline(ctx)

        st.session_state["source_metadata"] = final.source_metadata
        st.session_state["pipeline_skills"] = final.skills

        jobs = []
        for job in final.enriched_jobs:
            jobs.append({
                "title": job.get("title", "N/A"),
                "company": job.get("company", "Unknown"),
                "location": job.get("location", "Unknown"),
                "salary_label": job.get("normalized_salary", "Salary not disclosed"),
                "salary_lpa": job.get("salary_lpa"),
                "salary_comparison": job.get("salary_comparison", "N/A"),
                "compatibility_score": job.get("compatibility_score", 0),
                "culture_wlb": job.get("culture_wlb", "Moderate"),
                "culture_growth": job.get("culture_growth", "Moderate"),
                "culture_salary": job.get("culture_salary", "Average"),
                "culture_remote": job.get("culture_remote", "Hybrid"),
                "culture_summary": job.get("culture_summary", ""),
                "culture_score": job.get("culture_score", 0),
                "recommendation_score": job.get("recommendation_score", 0),
                "matched_skills": job.get("matched_skills", []),
                "description": (
                    f"Source: {job.get('source')} | "
                    f"Match: {job.get('match_score', 0)} | "
                    f"Culture: +{job.get('culture_score', 0)} | "
                    f"Rec Score: {job.get('recommendation_score', 0)}"
                ),
                "url": "#",
                "source": job.get("source"),
                "location_score": job.get("location_score", 0),
                "salary_score": job.get("salary_score", 0),
            })
        return jobs, None
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a clean message
        return [], ui.friendly_api_error(exc)


# ── Hero ──────────────────────────────────────────────────────────────────────
ui.render_hero(
    "💼 Job Search AI",
    "Personalized, real-time job recommendations powered by 9 intelligent agents.",
    badge="Agentic AI Pipeline · 9 Intelligent Agents",
)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ API Credentials")
    st.caption("Server keys stay hidden. They are never shown here — only their status.")

    def _cred_row(label: str, configured: bool) -> None:
        badge = ("<span style='color:#10b981;font-weight:700;'>● Configured</span>"
                 if configured
                 else "<span style='color:#f59e0b;font-weight:700;'>○ Not set</span>")
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"font-size:0.85rem;margin:0.15rem 0;'>"
            f"<span>{label}</span>{badge}</div>",
            unsafe_allow_html=True,
        )

    _cred_row("Adzuna App ID", bool(config.ADZUNA_APP_ID))
    _cred_row("Adzuna App Key", bool(config.ADZUNA_APP_KEY))
    _cred_row("Jooble API Key", bool(config.JOOBLE_API_KEY))

    with st.expander("🔑 Override keys for this session", expanded=False):
        st.caption("Leave blank to use the keys configured on the server. "
                   "Values entered here are not saved or displayed after submit.")
        app_id_override = st.text_input("Adzuna App ID", value="", type="password",
                                        placeholder="Override Adzuna App ID")
        app_key_override = st.text_input("Adzuna App Key", value="", type="password",
                                         placeholder="Override Adzuna App Key")
        jooble_override = st.text_input("Jooble API Key", value="", type="password",
                                        placeholder="Override Jooble API Key")

    # Effective credentials: a session override takes precedence over the
    # server-configured key. Secrets themselves are never written into widgets.
    app_id = (app_id_override.strip() or config.ADZUNA_APP_ID or "")
    app_key = (app_key_override.strip() or config.ADZUNA_APP_KEY or "")
    jooble_key = (jooble_override.strip() or config.JOOBLE_API_KEY or "")

    if has_any_api_credentials(app_id, app_key, jooble_key):
        st.success("✅ At least one live connector is configured.")
    else:
        st.warning("⚠️ No API keys set — searches will return no live jobs. "
                   "Add keys in the override panel or your server `.env`.")

    st.divider()
    st.markdown("### 📂 Saved Jobs")
    _loc_agent = LocationIntelligenceAgent()
    filter_city = st.selectbox("Filter saved jobs by city", ["All Cities"] + SUPPORTED_CITIES)
    saved_list = (get_saved_jobs() if filter_city == "All Cities"
                  else _loc_agent.get_jobs_by_city(filter_city))
    if saved_list:
        st.write(f"Showing **{len(saved_list)}** saved job(s).")
        with st.expander("Show Saved Jobs", expanded=False):
            for j in saved_list:
                st.write(f"**{j['job_title']}**")
                st.caption(f"{j['company_name']} | {j['location']} | {j['application_status']}")
    else:
        st.caption(f"No saved jobs found for {filter_city}.")
    st.divider()
    st.caption("Use the page nav above to explore Resume Analysis, Company "
               "Research, the Application Tracker and Analytics.")


# ── Search form ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="search-card"><h3>🔍 Search Parameters '
    '<span style="font-size:0.72rem; color:#ef4444; font-weight:500; margin-left:6px;">'
    '● required fields</span></h3>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-label">📄 Upload Resume (PDF) — '
            '<em style="font-weight:400; color:#64748b;">Optional · skills auto-detected to boost results</em></div>',
            unsafe_allow_html=True)
uploaded_resume = st.file_uploader("Upload Resume PDF", type=["pdf"],
                                   label_visibility="collapsed", key="resume_uploader")

resume_bytes = None
preview_skills = []
if uploaded_resume is not None:
    raw = uploaded_resume.read()
    v = validate_resume_upload(uploaded_resume.name, raw)
    if not v.ok:
        for err in v.errors:
            st.error(f"⚠️ {err}")
    else:
        resume_bytes = raw
        for w in v.warnings:
            st.info(f"ℹ️ {w}")
        preview_skills = ui.extract_skills_from_pdf_bytes(resume_bytes)
        st.session_state["resume_bytes"] = resume_bytes
        st.session_state["resume_name"] = uploaded_resume.name
        st.success(f"✅ **{uploaded_resume.name}** uploaded ({len(resume_bytes) // 1024} KB)")
        if preview_skills:
            st.markdown(
                f'<div style="margin:0.5rem 0 0.8rem 0;">'
                f'<span style="font-size:0.82rem; color:#166534; font-weight:700;">'
                f'🎯 {len(preview_skills)} skills detected:</span><br/>'
                f'<div style="margin-top:5px;">{ui.skill_chip_html(preview_skills)}</div></div>',
                unsafe_allow_html=True,
            )
        elif not ui.PDF_AVAILABLE:
            st.warning("⚠️ PyPDF2 not installed. Run `pip install PyPDF2` and restart.")
        else:
            st.info("ℹ️ No standard tech skills detected — the AI pipeline will still parse it.")
else:
    st.caption("💡 No resume uploaded — search will use your Job Role and preferences only.")

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)

col_r, col_l = st.columns([2, 2])
with col_r:
    st.markdown('<div class="section-label">Job Role <span class="required-dot"></span></div>', unsafe_allow_html=True)
    role = st.text_input("Job Role", placeholder="e.g. Python Developer, Data Scientist…",
                         label_visibility="collapsed", key="input_role")
with col_l:
    st.markdown('<div class="section-label">City / Location <span class="required-dot"></span></div>', unsafe_allow_html=True)
    city = st.selectbox("City", SUPPORTED_CITIES, label_visibility="collapsed", key="input_city")

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)

col_s, col_c = st.columns([2, 2])
with col_s:
    st.markdown('<div class="section-label">Expected Salary (LPA)</div>', unsafe_allow_html=True)
    expected_salary = st.slider("Expected Salary", 0.0, 100.0, 12.0, 0.5,
                                label_visibility="collapsed", key="input_salary")
    st.caption(f"Selected: ₹ **{expected_salary:.1f} LPA**")
with col_c:
    st.markdown('<div class="section-label">Results to Fetch</div>', unsafe_allow_html=True)
    results_count = st.slider("Results", 5, 50, 10, 5, label_visibility="collapsed", key="input_count")
    st.caption(f"Fetching up to **{results_count}** results per source")

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown('<div class="section-label">Work Preferences</div>', unsafe_allow_html=True)
col_wm, col_np, col_fl = st.columns(3)
with col_wm:
    work_mode = st.selectbox("Work Mode", ["Remote", "Hybrid", "Onsite"], key="input_work_mode")
with col_np:
    notice_days = st.selectbox("Notice Period", [0, 15, 30, 45, 60, 90, 120, 180], index=2,
                               format_func=lambda x: f"{x} days" if x > 0 else "Immediate", key="input_notice")
with col_fl:
    flexibility = st.selectbox("Flexibility", ["Strict", "Flexible"], index=1, key="input_flex")

st.markdown("<br/>", unsafe_allow_html=True)
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    search = st.button("🚀 Search Jobs", key="search_btn")
st.markdown("</div>", unsafe_allow_html=True)


# ── Handle search ───────────────────────────────────────────────────────────
if search:
    v = validate_search_params(role, city, expected_salary)
    for w in v.warnings:
        st.info(f"ℹ️ {w}")
    if not v.ok:
        for err in v.errors:
            st.error(f"⚠️ {err}")
    elif not has_any_api_credentials(app_id, app_key, jooble_key):
        st.error("🔑 No API credentials configured. Add an Adzuna App ID + Key, or a "
                 "Jooble API Key, in the sidebar (or your `.env` file) before searching.")
    else:
        work_prefs = {
            "work_from_home_preference": work_mode,
            "notice_period_days": notice_days,
            "flexibility_preference": flexibility,
        }
        with st.spinner(f"Running 9-agent pipeline for **{role.strip()}** in **{city}**…"):
            jobs, err = run_search(role.strip(), city, app_id.strip(), app_key.strip(),
                                   jooble_key.strip(), results_count, expected_salary,
                                   work_prefs, resume_bytes)
        if err:
            st.error(err)
        elif not jobs:
            st.warning("⚠️ No jobs found. Try a broader role, a different city, or adjust salary.")
        else:
            save_search_history(role.strip(), city)
            save_user_preferences(preferred_location=city, preferred_role=role.strip(),
                                  preferred_salary_lpa=expected_salary,
                                  work_from_home_preference=work_mode,
                                  notice_period_days=notice_days,
                                  flexibility_preference=flexibility)
            st.session_state["results"] = {"jobs": jobs, "role": role.strip(), "city": city}


# ── Results section (reads from session_state so filters don't re-run pipeline) ──
results = st.session_state.get("results")
if results:
    jobs = results["jobs"]
    role_used, city_used = results["role"], results["city"]

    st.markdown(f"### 📈 Results for **{role_used}** in **{city_used}**")

    # Filters & sorting
    with st.container():
        f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
        with f1:
            sort_by = st.selectbox("Sort by", ["Recommendation Score", "Salary (high→low)",
                                               "Match Score", "Title (A→Z)"], key="sort_by")
        with f2:
            sources = sorted({j.get("source") or "Unknown" for j in jobs})
            source_filter = st.multiselect("Source", sources, default=sources, key="src_filter")
        with f3:
            min_score = st.slider("Min rec score", 0, 12, 0, key="min_score")
        with f4:
            only_salary = st.checkbox("Only with salary info", value=False, key="only_salary")

    view = [j for j in jobs
            if (j.get("source") or "Unknown") in source_filter
            and j.get("recommendation_score", 0) >= min_score
            and (not only_salary or j.get("salary_lpa"))]

    if sort_by == "Salary (high→low)":
        view.sort(key=lambda j: (j.get("salary_lpa") is not None, j.get("salary_lpa") or 0), reverse=True)
    elif sort_by == "Match Score":
        view.sort(key=lambda j: j.get("compatibility_score", 0), reverse=True)
    elif sort_by == "Title (A→Z)":
        view.sort(key=lambda j: j.get("title", "").lower())
    else:
        view.sort(key=lambda j: j.get("recommendation_score", 0), reverse=True)

    disclosed = [j for j in view if j.get("salary_lpa")]
    avg_salary = (f"₹{sum(j['salary_lpa'] for j in disclosed) / len(disclosed):.1f} LPA"
                  if disclosed else "N/A")
    st.markdown(
        f'<div class="stats-strip">Showing <strong>{len(view)}</strong> of '
        f'<strong>{len(jobs)}</strong> listings · Avg advertised salary: '
        f'<strong>{avg_salary}</strong></div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Visible Results", len(view))
    m2.metric("With Salary Info", len(disclosed))
    m3.metric("Unique Locations", len({j["location"] for j in view}))

    # Connector source quality
    if "source_metadata" in st.session_state and st.session_state["source_metadata"]:
        with st.expander("📊 Connector Source Quality Stats"):
            meta = st.session_state["source_metadata"]
            st.dataframe(pd.DataFrame([
                {"Platform": s, "Successful": d["successful_fetches"],
                 "Attempts": d["total_fetches"], "Success Rate": f"{d['success_rate_percent']}%",
                 "Jobs Found": d["total_jobs_yielded"]}
                for s, d in meta.items()
            ]), use_container_width=True, hide_index=True)

    # Historical salary trends
    _sal_agent = SalaryIntelligenceAgent()
    hist = _sal_agent.get_historical_ranges(role_used, city_used)
    if hist:
        with st.expander("📈 Historical Salary Trends"):
            st.dataframe(pd.DataFrame([
                {"Date/Time": h["timestamp"], "Min": f"₹{h['min_salary_lpa']:.1f}",
                 "Max": f"₹{h['max_salary_lpa']:.1f}", "Avg": f"₹{h['avg_salary_lpa']:.1f}"}
                for h in hist
            ]), use_container_width=True, hide_index=True)

    tab_cards, tab_table, tab_export = st.tabs(["📋 Job Cards", "📊 Table View", "⬇️ Export"])

    with tab_cards:
        if not view:
            st.info("No jobs match the current filters. Loosen them above.")
        for i, job in enumerate(view, 1):
            ui.render_job_card(job, i)
            c1, c2 = st.columns([2, 3])
            with c1:
                status = st.selectbox("Status", VALID_APPLICATION_STATUSES[:5],
                                      key=f"status_{i}_{job['company']}_{job['title']}",
                                      label_visibility="collapsed")
            with c2:
                if st.button(f"💾 Track: {job['title']} @ {job['company']}",
                             key=f"save_{i}_{job['company']}_{job['title']}"):
                    saved_id = save_job(job_title=job["title"], company_name=job["company"],
                                        location=job["location"], salary_lpa=job.get("salary_lpa"),
                                        source_platform=job.get("source", "Unknown"),
                                        application_status=status)
                    if saved_id:
                        st.success(f"Saved as **{status}** — see the Application Tracker page.")

    with tab_table:
        st.dataframe(pd.DataFrame([
            {"Rec Score": j.get("recommendation_score", 0), "Title": j["title"],
             "Company": j["company"], "Location": j["location"], "Salary": j["salary_label"],
             "vs Expectation": j.get("salary_comparison", "N/A"),
             "Work Pref": j.get("compatibility_score", 0),
             "Culture WLB": j.get("culture_wlb", "Moderate"),
             "Source": j.get("source", "Unknown")}
            for j in view
        ]), use_container_width=True, hide_index=True)

    with tab_export:
        st.write("Download your filtered results:")
        e1, e2 = st.columns(2)
        with e1:
            st.download_button("⬇️ Download CSV", data=jobs_to_csv(view),
                               file_name=f"jobs_{role_used.replace(' ', '_')}.csv",
                               mime="text/csv", use_container_width=True)
        with e2:
            if is_pdf_available():
                pdf = jobs_to_pdf(view, role_used, city_used)
                st.download_button("⬇️ Download PDF report", data=pdf or b"",
                                   file_name=f"jobs_{role_used.replace(' ', '_')}.pdf",
                                   mime="application/pdf", use_container_width=True,
                                   disabled=pdf is None)
            else:
                st.button("⬇️ PDF (install reportlab)", disabled=True, use_container_width=True)
                st.caption("Run `pip install reportlab` to enable PDF export.")
else:
    st.markdown(
        """
        <div style="text-align:center; padding: 2.5rem 1rem; color: #94a3b8;">
            <div style="font-size:3.5rem;">🔍</div>
            <p style="font-size:1.05rem; margin-top:0.9rem; color: #64748b;">
                Fill in the parameters above and hit
                <strong style="color:#3b82f6;">Search Jobs</strong> to get started.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
