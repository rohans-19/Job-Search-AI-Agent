"""
pages/4_📊_Analytics.py
-----------------------
Job-search performance analytics.

Aggregates locally persisted data (search history, tracked applications,
connector quality, saved-job salaries) into a single dashboard so the user can
see how their search is going over time.
"""

import pandas as pd
import streamlit as st

import config  # noqa: F401  (loads .env)
from database import (
    initialize_database, get_search_history, get_application_stats,
    get_source_quality_stats, get_saved_jobs, get_tracked_jobs,
)
import ui_common as ui

initialize_database()
st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
ui.inject_css()

ui.render_hero("📊 Search Analytics",
               "How your job hunt is trending across searches, applications and sources.",
               badge="Local Analytics · No data leaves your machine")

history = get_search_history(limit=200)
app_stats = get_application_stats()
source_stats = get_source_quality_stats()
tracked = get_tracked_jobs()
all_saved = get_saved_jobs()

# ── Top-line KPIs ─────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Searches", len(history))
k2.metric("Tracked Applications", len(tracked))
k3.metric("Jobs Persisted", len(all_saved))
applied_plus = sum(app_stats.get(s, 0) for s in ("Applied", "Interview", "Offer"))
k4.metric("Applied or Further", applied_plus)

if not history and not tracked and not source_stats:
    st.info("📭 No analytics yet. Run a few searches and track some jobs to populate this dashboard.")
    st.stop()

# ── Application funnel ─────────────────────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### 🎯 Application Funnel")
if app_stats:
    funnel_order = ["Saved", "Applied", "Interview", "Offer", "Rejected"]
    funnel = pd.DataFrame(
        {"Stage": funnel_order, "Count": [app_stats.get(s, 0) for s in funnel_order]}
    ).set_index("Stage")
    st.bar_chart(funnel, height=280)
    offers = app_stats.get("Offer", 0)
    applied = app_stats.get("Applied", 0) + app_stats.get("Interview", 0) + offers
    if applied:
        st.caption(f"Offer conversion: **{round(100 * offers / applied)}%** of applied-or-further roles "
                   f"reached an offer.")
else:
    st.caption("No tracked applications yet.")

# ── Searches over time + popular roles/cities ─────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
colA, colB = st.columns(2)

with colA:
    st.markdown("### 🔍 Most Searched Roles")
    if history:
        roles = pd.Series([h["search_role"] for h in history if h.get("search_role")])
        top_roles = roles.value_counts().head(8)
        if not top_roles.empty:
            st.bar_chart(top_roles, height=260)
    else:
        st.caption("No search history yet.")

with colB:
    st.markdown("### 📍 Most Searched Cities")
    if history:
        cities = pd.Series([h["search_location"] for h in history if h.get("search_location")])
        top_cities = cities.value_counts().head(8)
        if not top_cities.empty:
            st.bar_chart(top_cities, height=260)
    else:
        st.caption("No search history yet.")

# ── Salary distribution of saved jobs ─────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### 💰 Salary Distribution (Saved Jobs)")
salaries = [j["salary_lpa"] for j in all_saved if j.get("salary_lpa")]
if salaries:
    s = pd.Series(salaries)
    c1, c2, c3 = st.columns(3)
    c1.metric("Min LPA", f"₹{s.min():.1f}")
    c2.metric("Median LPA", f"₹{s.median():.1f}")
    c3.metric("Max LPA", f"₹{s.max():.1f}")
    bins = pd.cut(s, bins=[0, 5, 10, 15, 20, 30, 50, 1000],
                  labels=["0-5", "5-10", "10-15", "15-20", "20-30", "30-50", "50+"])
    st.bar_chart(bins.value_counts().sort_index(), height=260)
else:
    st.caption("No salary data on saved jobs yet.")

# ── Connector reliability ─────────────────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### 🔌 Connector Reliability")
if source_stats:
    df = pd.DataFrame([
        {"Platform": s, "Success Rate %": d["success_rate_percent"],
         "Jobs Yielded": d["total_jobs_yielded"], "Attempts": d["total_fetches"]}
        for s, d in source_stats.items()
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
    chart_df = df.set_index("Platform")[["Jobs Yielded"]]
    st.bar_chart(chart_df, height=240)
else:
    st.caption("No connector activity recorded yet.")

# ── Recent searches table ─────────────────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
with st.expander("🕑 Recent Search History"):
    if history:
        st.dataframe(pd.DataFrame([
            {"Role": h["search_role"], "Location": h["search_location"], "When": h["timestamp"]}
            for h in history[:50]
        ]), use_container_width=True, hide_index=True)
    else:
        st.caption("No search history yet.")
