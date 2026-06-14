"""
pages/1_📄_Resume_Analysis.py
-----------------------------
Résumé upload, analysis & ATS optimization.

Parses a PDF résumé, extracts and categorises skills, scores role-fit, and runs
a full ATS match against a pasted job description (keyword optimization + skills
gap analysis). Exports a tailored one-page skills profile PDF (résumé version).
"""

import streamlit as st

import config  # noqa: F401  (loads .env)
from database import initialize_database  # noqa: F401
from validation import validate_resume_upload
from exporters import resume_profile_to_pdf, is_pdf_available
from ats import ats_match
import ui_common as ui

initialize_database()
st.set_page_config(page_title="Resume Analysis", page_icon="📄", layout="wide")
ui.inject_css()

ui.render_hero("Résumé Analysis & ATS",
               "Extract skills, score role-fit, and tailor your résumé to beat applicant tracking systems.",
               badge="Resume Parser · Skill Extraction · ATS")

existing = st.session_state.get("resume_bytes")
existing_name = st.session_state.get("resume_name", "previously uploaded résumé")

st.markdown('<div class="search-card"><h3>Upload Résumé (PDF)</h3>', unsafe_allow_html=True)
uploaded = st.file_uploader("Upload Résumé PDF", type=["pdf"], label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

resume_bytes = None
if uploaded is not None:
    raw = uploaded.read()
    v = validate_resume_upload(uploaded.name, raw)
    if not v.ok:
        for err in v.errors:
            st.error(err)
    else:
        resume_bytes = raw
        st.session_state["resume_bytes"] = raw
        st.session_state["resume_name"] = uploaded.name
elif existing:
    st.info(f"Using **{existing_name}** from your current session. Upload a new file to replace it.")
    resume_bytes = existing

if not resume_bytes:
    st.markdown(
        '<div style="text-align:center; padding:2.4rem; color:#a1a1aa;">'
        '<div style="font-size:2.6rem;">⌁</div>'
        '<p style="color:#71717a; margin-top:0.6rem;">Upload a PDF résumé to begin analysis.</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()

if not ui.PDF_AVAILABLE:
    st.warning("PyPDF2 is not installed. Run `pip install PyPDF2` and restart the app.")
    st.stop()

text = ui.extract_text_from_pdf_bytes(resume_bytes)
skills = ui.extract_skills_from_pdf_bytes(resume_bytes)
word_count = len(text.split()) if text else 0
categorized = ui.categorize_skills(skills)

if not text:
    st.error("Could not extract any text from this PDF. It may be a scanned image — "
             "export a text-based PDF and retry.")
    st.stop()

# ── Overview tiles ────────────────────────────────────────────────────────────
tiles = (ui.render_tile("Skills detected", str(len(skills)), ui.ACCENT)
         + ui.render_tile("Word count", f"{word_count:,}")
         + ui.render_tile("Domains covered", str(len(categorized))))
st.markdown(f'<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.8rem; margin-bottom:1rem;">{tiles}</div>',
            unsafe_allow_html=True)

if not skills:
    st.warning("No standard tech skills detected. The text was read, but no known skill keywords matched.")
else:
    st.markdown("### Skills by category")
    for category, items in categorized.items():
        st.markdown(f"**{category}** · {len(items)}")
        st.markdown(ui.skill_chip_html(items), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:0.5rem;'></div>", unsafe_allow_html=True)

# ── ATS match against a job description ───────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### ATS Match — paste a job description")
st.caption("Paste the JD you're targeting. We score keyword coverage, surface missing terms, "
           "and check résumé hygiene the way an ATS would.")
jd = st.text_area("Job description", height=180, label_visibility="collapsed",
                  placeholder="Paste the full job description here…")

highlights: list[str] = []
target_for_pdf = ""
if jd and jd.strip():
    report = ats_match(text, skills, jd)
    score = report["score"]
    color = ui.ACCENT if score >= 60 else ("#b45309" if score >= 40 else "#b91c1c")
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:1.2rem; background:#fff; '
        f'border:1px solid var(--border); border-radius:18px; padding:1.2rem 1.5rem; margin:0.6rem 0 1rem;">'
        f'<div style="font-family:Outfit; font-size:3rem; font-weight:800; color:{color};">{score}'
        f'<span style="font-size:1rem; color:#a1a1aa;">/100</span></div>'
        f'<div><div style="font-weight:700; color:var(--ink);">{ui.html_lib.escape(report["verdict"])}</div>'
        f'<div style="color:var(--muted); font-size:0.85rem; margin-top:0.2rem;">'
        f'{len(report["skills_matched"])} of {len(report["skills_matched"])+len(report["skills_missing"])} '
        f'JD skills matched · hygiene {report["hygiene_score"]}/20</div></div></div>',
        unsafe_allow_html=True,
    )
    st.progress(score / 100)

    cga, cgb = st.columns(2)
    with cga:
        st.markdown("**✓ Matched skills**")
        if report["skills_matched"]:
            st.markdown(ui.skill_chip_html(report["skills_matched"]), unsafe_allow_html=True)
            highlights = [f"Proven experience with {s}" for s in report["skills_matched"]]
        else:
            st.caption("None of the JD's tech skills were found in your résumé.")
    with cgb:
        st.markdown("**△ Missing skills (add these)**")
        if report["skills_missing"]:
            st.markdown(ui.skill_chip_html(report["skills_missing"]), unsafe_allow_html=True)
        else:
            st.caption("You cover all the JD's tech skills. 🎯")

    if report["terms_missing"]:
        st.markdown("**Keywords to mirror from the JD**")
        st.markdown(ui.skill_chip_html(report["terms_missing"][:15]), unsafe_allow_html=True)

    st.markdown("**Suggestions**")
    for s in report["suggestions"]:
        st.markdown(f"- {s}")
    target_for_pdf = "ATS-tailored"

# ── Quick role-fit (no JD needed) ─────────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### Quick role-fit check")
target_role = st.text_input("Target role", placeholder="e.g. Machine Learning Engineer")

ROLE_EXPECTATIONS = {
    "data scientist": ["python", "machine learning", "sql", "pandas", "numpy"],
    "machine learning engineer": ["python", "pytorch", "tensorflow", "machine learning", "docker", "aws"],
    "data engineer": ["python", "sql", "spark", "airflow", "etl", "aws"],
    "backend developer": ["python", "java", "sql", "rest api", "docker", "microservices"],
    "frontend developer": ["javascript", "typescript", "react", "angular", "vue"],
    "devops engineer": ["docker", "kubernetes", "terraform", "ci/cd", "aws", "linux"],
    "full stack developer": ["javascript", "react", "node.js", "sql", "docker"],
}
if target_role:
    key = target_role.strip().lower()
    expected = ROLE_EXPECTATIONS.get(key)
    if not expected:
        for rk, exp in ROLE_EXPECTATIONS.items():
            if rk in key or key in rk:
                expected = exp
                break
    if expected:
        have = [s for s in expected if s in {sk.lower() for sk in skills}]
        missing = [s for s in expected if s not in {sk.lower() for sk in skills}]
        pct = round(100 * len(have) / len(expected))
        st.progress(pct / 100, text=f"Role match: {pct}% ({len(have)}/{len(expected)} key skills)")
        if have:
            st.success("You already have: " + ", ".join(have))
            highlights = highlights or [f"Proven experience with {h}" for h in have]
        if missing:
            st.warning("Consider strengthening: " + ", ".join(missing))
        target_for_pdf = target_for_pdf or target_role.strip()
    else:
        st.info("No predefined template for that role. Try: Data Scientist, ML Engineer, "
                "Data Engineer, Backend/Frontend Developer, DevOps Engineer.")

# ── Export tailored profile ───────────────────────────────────────────────────
st.markdown('<hr class="divider-soft"/>', unsafe_allow_html=True)
st.markdown("### Export skills profile (résumé version)")
summary = (f"Candidate with {len(skills)} recognised technical skills across "
           f"{len(categorized)} domains."
           + (f" Tailored for {target_for_pdf} applications." if target_for_pdf else ""))

if is_pdf_available():
    pdf = resume_profile_to_pdf(
        skills=skills, target_role=target_for_pdf, summary=summary,
        categorized=categorized, highlights=highlights or None,
    )
    st.download_button("Download skills-profile PDF", data=pdf or b"",
                       file_name="skills_profile.pdf", mime="application/pdf",
                       disabled=pdf is None)
else:
    st.info("Install `reportlab` to enable PDF profile export (`pip install reportlab`).")
