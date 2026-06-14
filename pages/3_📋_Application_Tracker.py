"""
pages/3_📋_Application_Tracker.py
--------------------------------
Track saved job applications as Kanban-style cards grouped by status.

Lets the user move a job through the pipeline
(Saved → Applied → Interview → Offer / Rejected), delete entries, and export
the full tracker to CSV / PDF.
"""

import streamlit as st

import config  # noqa: F401  (loads .env)
from database import (
    initialize_database, get_tracked_jobs, get_application_stats,
    update_application_status, delete_saved_job, VALID_APPLICATION_STATUSES,
)
from exporters import jobs_to_csv, jobs_to_pdf, is_pdf_available
import ui_common as ui

initialize_database()
st.set_page_config(page_title="Application Tracker", page_icon="📋", layout="wide")
ui.inject_css()

ui.render_hero("📋 Application Tracker",
               "Manage every job you're pursuing, from Saved to Offer.",
               badge="Pipeline Persistence · SQLite")

# Pipeline stages shown as columns (Fetched/auto rows are excluded by the query).
STAGES = ["Saved", "Applied", "Interview", "Offer", "Rejected"]

stats = get_application_stats()
total = sum(stats.values())

cols = st.columns(len(STAGES))
for col, stage in zip(cols, STAGES):
    col.metric(stage, stats.get(stage, 0))

if total == 0:
    st.info("📭 No tracked applications yet. Go to **Job Search**, run a search, and click "
            "**Track** on any job card to add it here.")
    st.stop()

jobs = get_tracked_jobs()

# ── Export bar ────────────────────────────────────────────────────────────────
export_rows = [
    {"title": j["job_title"], "company": j["company_name"], "location": j["location"],
     "salary_label": (f"₹{j['salary_lpa']:.1f} LPA" if j["salary_lpa"] else "N/A"),
     "salary_lpa": j["salary_lpa"], "source": j["source_platform"],
     "status": j["application_status"], "saved_date": j["saved_date"]}
    for j in jobs
]
e1, e2, _ = st.columns([1, 1, 3])
with e1:
    st.download_button("⬇️ CSV", data=jobs_to_csv(export_rows),
                       file_name="application_tracker.csv", mime="text/csv",
                       use_container_width=True)
with e2:
    if is_pdf_available():
        pdf = jobs_to_pdf(export_rows, role="Tracked Applications")
        st.download_button("⬇️ PDF", data=pdf or b"", file_name="application_tracker.pdf",
                           mime="application/pdf", use_container_width=True, disabled=pdf is None)
    else:
        st.button("⬇️ PDF (install reportlab)", disabled=True, use_container_width=True)

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)

# ── Kanban columns ────────────────────────────────────────────────────────────
stage_cols = st.columns(len(STAGES))
for col, stage in zip(stage_cols, STAGES):
    with col:
        st.markdown(f"#### {stage} ({stats.get(stage, 0)})")
        stage_jobs = [j for j in jobs if j["application_status"] == stage]
        if not stage_jobs:
            st.caption("—")
        for j in stage_jobs:
            sal = f"₹{j['salary_lpa']:.1f} LPA" if j["salary_lpa"] else "Salary N/A"
            st.markdown(
                f'<div style="background:#fff; border-radius:10px; padding:0.7rem 0.8rem; '
                f'margin-bottom:0.5rem; box-shadow:0 1px 6px rgba(0,0,0,0.06); '
                f'border-left:3px solid #3b82f6;">'
                f'<div style="font-weight:700; font-size:0.9rem; color:#1e293b;">{ui.html_lib.escape(j["job_title"])}</div>'
                f'<div style="font-size:0.8rem; color:#3b82f6;">{ui.html_lib.escape(j["company_name"] or "Unknown")}</div>'
                f'<div style="font-size:0.75rem; color:#64748b; margin-top:0.2rem;">'
                f'📍 {ui.html_lib.escape(j["location"] or "—")} · 💰 {sal}</div>'
                f'<div style="font-size:0.7rem; color:#94a3b8; margin-top:0.2rem;">'
                f'{ui.html_lib.escape(j["source_platform"] or "")} · {ui.html_lib.escape(str(j["saved_date"]))}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            new_status = st.selectbox(
                "Move to", VALID_APPLICATION_STATUSES[:5],
                index=VALID_APPLICATION_STATUSES[:5].index(stage),
                key=f"move_{j['id']}", label_visibility="collapsed",
            )
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Update", key=f"upd_{j['id']}", use_container_width=True):
                    if new_status != stage and update_application_status(j["id"], new_status):
                        st.toast(f"Moved to {new_status}")
                        st.rerun()
            with b2:
                if st.button("🗑️", key=f"del_{j['id']}", use_container_width=True):
                    if delete_saved_job(j["id"]):
                        st.toast("Deleted")
                        st.rerun()
