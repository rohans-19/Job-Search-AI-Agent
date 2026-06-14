"""
pages/5_🎤_Mock_Interview.py
----------------------------
Text-based AI mock interview with instant feedback.

Generates a role-specific interview set (Technical + Behavioural + India HR),
collects typed answers, and scores each with structured feedback (STAR
structure, specificity, relevance, delivery) — fully offline.
"""

import streamlit as st

import config  # noqa: F401  (loads .env)
from database import initialize_database, SUPPORTED_CITIES  # noqa: F401
from interview import get_question_set, available_roles, evaluate_answer
import ui_common as ui

initialize_database()
st.set_page_config(page_title="Mock Interview", page_icon="🎤", layout="wide")
ui.inject_css()

ui.render_hero("Mock Interview",
               "Practice a role-specific interview and get instant, structured feedback on every answer.",
               badge="Technical · Behavioural · India HR rounds")

# ── Setup ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="search-card"><h3>Set up your interview</h3>', unsafe_allow_html=True)
c1, c2 = st.columns([3, 1])
with c1:
    roles = available_roles()
    default_role = st.session_state.get("results", {}).get("role", "")
    role = st.text_input("Target role", value=default_role,
                         placeholder="e.g. Data Scientist, Backend Developer")
with c2:
    st.markdown('<div class="section-label">Bank has</div>', unsafe_allow_html=True)
    st.caption(", ".join(roles))
start = st.button("🎬 Start / Restart interview")
st.markdown("</div>", unsafe_allow_html=True)

if start:
    st.session_state["interview_set"] = get_question_set(role or "general")
    st.session_state["interview_role"] = role or "General"
    st.session_state["interview_results"] = {}

qset = st.session_state.get("interview_set")
if not qset:
    st.markdown(
        '<div style="text-align:center; padding:2.4rem; color:#a1a1aa;">'
        '<div style="font-size:2.6rem;">◎</div>'
        '<p style="color:#71717a; margin-top:0.6rem;">Enter a role and start your mock interview.</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()

st.markdown(f"### Interview for **{st.session_state.get('interview_role', 'General')}** · "
            f"{len(qset)} questions")

results = st.session_state.setdefault("interview_results", {})

for i, item in enumerate(qset):
    round_color = {"Technical": "#1d4ed8", "Behavioural": "#9a3412", "HR": "#047857"}.get(item["round"], "#71717a")
    st.markdown(
        f'<div style="margin-top:1.1rem;"><span class="status-pill" '
        f'style="background:#f4f4f5; color:{round_color};">{item["round"]}</span> '
        f'<span style="font-weight:700; font-family:Outfit; color:var(--ink);"> Q{i+1}.</span> '
        f'<span style="color:var(--ink);">{ui.html_lib.escape(item["q"])}</span></div>',
        unsafe_allow_html=True,
    )
    ans = st.text_area("Your answer", key=f"ans_{i}", height=120,
                       label_visibility="collapsed", placeholder="Type your answer…")
    if st.button("Get feedback", key=f"fb_{i}"):
        results[i] = evaluate_answer(ans, item.get("kw", []))

    fb = results.get(i)
    if fb:
        score = fb["score"]
        color = ui.ACCENT if score >= 70 else ("#b45309" if score >= 45 else "#b91c1c")
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:0.8rem; margin:0.3rem 0 0.5rem;">'
            f'<span style="font-family:Outfit; font-weight:800; font-size:1.6rem; color:{color};">{score}'
            f'<span style="font-size:0.8rem; color:#a1a1aa;">/100</span></span>'
            f'<span class="mono" style="color:var(--muted); font-size:0.8rem;">{fb["word_count"]} words · '
            f'STAR {sum(fb["star"].values())}/4</span></div>',
            unsafe_allow_html=True,
        )
        if fb["strengths"]:
            with st.expander("What worked", expanded=True):
                for s in fb["strengths"]:
                    st.markdown(f"- ✓ {s}")
        if fb["improvements"]:
            with st.expander("How to improve", expanded=True):
                for s in fb["improvements"]:
                    st.markdown(f"- △ {s}")

# ── Summary ───────────────────────────────────────────────────────────────────
if results:
    st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
    answered = [r["score"] for r in results.values()]
    avg = round(sum(answered) / len(answered))
    color = ui.ACCENT if avg >= 70 else ("#b45309" if avg >= 45 else "#b91c1c")
    st.markdown("### Session summary")
    tiles = (ui.render_tile("Answered", f"{len(answered)}/{len(qset)}")
             + ui.render_tile("Average score", f"{avg}/100", color)
             + ui.render_tile("Best answer", f"{max(answered)}/100", ui.ACCENT))
    st.markdown(f'<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.8rem;">{tiles}</div>',
                unsafe_allow_html=True)
    if avg >= 70:
        st.success("Strong session — you're interview-ready. Keep quantifying impact.")
    elif avg >= 45:
        st.info("Solid base — focus on STAR structure and concrete metrics to level up.")
    else:
        st.warning("Keep practising — structure each answer with Situation, Task, Action, Result.")
