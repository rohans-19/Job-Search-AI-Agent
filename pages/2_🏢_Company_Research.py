"""
pages/2_🏢_Company_Research.py
------------------------------
Company research & culture insights page.

Given a company name, surfaces:
  - Culture scores (WLB, growth, salary competitiveness, remote-friendliness)
    via the Company Culture Agent (DB cache + web scraping fallback).
  - Top research links (official site, profiles) via company.fetch_company_research_links.
"""

import streamlit as st

import config  # noqa: F401  (loads .env)
from database import initialize_database, get_company_culture
from agents.culture_agent import CompanyCultureAgent
import ui_common as ui

initialize_database()
st.set_page_config(page_title="Company Research", page_icon="🏢", layout="wide")
ui.inject_css()

ui.render_hero("🏢 Company Research",
               "Look up culture insights and authoritative links for any employer.",
               badge="Company Culture Intelligence Agent")


def _score_block(label: str, value: str, good: set[str]) -> str:
    color = "#166534" if value in good else "#92400e"
    bg = "#dcfce7" if value in good else "#fef3c7"
    return (f'<div style="flex:1; min-width:140px; background:{bg}; border-radius:12px; '
            f'padding:0.9rem 1rem; margin:0.3rem;">'
            f'<div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em; '
            f'color:#64748b; font-weight:600;">{label}</div>'
            f'<div style="font-size:1.15rem; font-weight:700; color:{color}; margin-top:0.2rem;">'
            f'{value}</div></div>')


st.markdown('<div class="search-card"><h3>🔎 Research a Company</h3>', unsafe_allow_html=True)
col_in, col_btn = st.columns([4, 1])
with col_in:
    company = st.text_input("Company name", placeholder="e.g. Infosys, Razorpay, Google",
                            label_visibility="collapsed")
with col_btn:
    go = st.button("Research")
st.markdown("</div>", unsafe_allow_html=True)

if not (go and company.strip()):
    st.markdown(
        '<div style="text-align:center; padding:2rem; color:#94a3b8;">'
        '<div style="font-size:3rem;">🏢</div>'
        '<p style="color:#64748b; margin-top:0.6rem;">Enter a company name and click '
        '<strong style="color:#3b82f6;">Research</strong>.</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()

company = company.strip()
cached = get_company_culture(company)
if cached:
    st.caption(f"📦 Loaded from cache (last updated {cached.get('last_updated', 'recently')}).")

with st.spinner(f"Gathering culture intelligence for **{company}**…"):
    try:
        insights = CompanyCultureAgent().get_culture_insights(company)
    except Exception as exc:  # noqa: BLE001
        st.error(ui.friendly_api_error(exc))
        st.stop()

st.markdown(f"### 🏢 {company}")
wlb = insights.get("work_life_balance", "Moderate")
growth = insights.get("career_growth", "Moderate")
salary = insights.get("salary_competitiveness", "Average")
remote = insights.get("remote_friendly", "Hybrid")
summary = insights.get("overall_summary", "")

blocks = (
    _score_block("Work-Life Balance", wlb, {"Excellent", "Good"})
    + _score_block("Career Growth", growth, {"High", "Good"})
    + _score_block("Salary Competitiveness", salary, {"High", "Competitive"})
    + _score_block("Remote Friendly", remote, {"Yes", "Hybrid"})
)
st.markdown(f'<div style="display:flex; flex-wrap:wrap; margin:0.5rem 0 1rem;">{blocks}</div>',
            unsafe_allow_html=True)

if summary:
    st.markdown(
        f'<div style="background:#f8fafc; border-left:3px solid #6366f1; border-radius:8px; '
        f'padding:0.9rem 1.1rem; color:#475569; line-height:1.5;">{summary}</div>',
        unsafe_allow_html=True,
    )

# ── Research links ────────────────────────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### 🔗 Authoritative Links")
with st.spinner("Finding official sources…"):
    try:
        from company import fetch_company_research_links
        links = fetch_company_research_links(company, num_results=4)
    except Exception as exc:  # noqa: BLE001
        links = []
        st.caption(f"Link lookup unavailable: {exc}")

if links:
    for url in links:
        st.markdown(f"- [{url}]({url})")
else:
    st.info("No links could be retrieved automatically. Try searching the company on "
            "[Glassdoor](https://www.glassdoor.co.in) or "
            "[LinkedIn](https://www.linkedin.com/company/).")

st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.caption("Culture scores are heuristic estimates synthesised from public review signals "
           "and cached locally. Always validate with first-hand research before deciding.")
