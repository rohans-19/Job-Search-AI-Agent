"""
ats.py
------
Lightweight, offline ATS (Applicant Tracking System) analysis.

Given a résumé (plain text + detected skills) and a target job description, it
computes an ATS-style match score, the keywords you're missing, formatting
hygiene flags, and concrete tailoring suggestions — without any external API.

Scoring model (0–100):
  - 55  Skill-keyword coverage   (JD skills present in the résumé)
  - 25  JD term coverage         (important JD words appearing in résumé text)
  - 20  Résumé hygiene           (sections, contact info, length, action verbs)
"""

from __future__ import annotations

import re
from collections import Counter

from agents.skills_agent import PREDEFINED_SKILLS

# Words too common to count as meaningful JD keywords.
_STOPWORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "your", "have",
    "this", "that", "from", "they", "their", "team", "work", "role", "job",
    "must", "should", "can", "able", "who", "what", "when", "where", "why",
    "into", "out", "all", "any", "etc", "per", "via", "use", "using", "used",
    "well", "good", "strong", "looking", "candidate", "candidates", "experience",
    "years", "year", "skills", "skill", "knowledge", "ability", "responsibilities",
    "requirements", "preferred", "plus", "join", "build", "working", "company",
    "we", "is", "to", "of", "in", "on", "as", "an", "or", "be", "at", "by", "a",
}

_ACTION_VERBS = {
    "built", "designed", "developed", "led", "managed", "implemented", "created",
    "optimized", "improved", "delivered", "launched", "automated", "reduced",
    "increased", "architected", "engineered", "shipped", "owned", "scaled",
}

_SECTION_HINTS = {
    "experience": ("experience", "employment", "work history"),
    "education": ("education", "b.tech", "b.e", "bachelor", "master", "degree"),
    "skills": ("skills", "technologies", "tech stack", "tools"),
    "projects": ("projects", "project"),
}


def extract_jd_keywords(jd_text: str, top_n: int = 25) -> dict:
    """
    Extract keywords from a job description.

    Returns:
        {"skills": [...known tech skills in the JD...],
         "terms":  [...other frequent meaningful words...]}
    """
    if not jd_text:
        return {"skills": [], "terms": []}

    low = jd_text.lower()
    jd_skills = sorted({s for s in PREDEFINED_SKILLS
                        if re.search(r'\b' + re.escape(s) + r'\b', low)})

    words = re.findall(r"[a-zA-Z][a-zA-Z+.#-]{2,}", low)
    freq = Counter(w for w in words if w not in _STOPWORDS and len(w) > 2)
    # Drop words already captured as skills.
    skill_tokens = {t for s in jd_skills for t in s.split()}
    terms = [w for w, _ in freq.most_common(top_n * 2)
             if w not in skill_tokens][:top_n]
    return {"skills": jd_skills, "terms": terms}


def _hygiene(resume_text: str) -> tuple[int, list[str]]:
    """Return (score 0-20, list of warnings) for résumé formatting hygiene."""
    low = resume_text.lower()
    score = 0
    warns: list[str] = []

    sections_found = sum(
        1 for hints in _SECTION_HINTS.values() if any(h in low for h in hints)
    )
    score += min(8, sections_found * 2)
    missing = [name for name, hints in _SECTION_HINTS.items()
               if not any(h in low for h in hints)]
    if missing:
        warns.append("Add clear section headers for: " + ", ".join(missing) + ".")

    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
    has_phone = bool(re.search(r"(\+?\d[\d\s-]{7,}\d)", resume_text))
    if has_email:
        score += 3
    else:
        warns.append("No email detected — ATS parsers expect a contact email.")
    if has_phone:
        score += 2
    else:
        warns.append("No phone number detected.")

    words = len(resume_text.split())
    if 300 <= words <= 900:
        score += 4
    elif words < 300:
        warns.append(f"Résumé is short ({words} words) — aim for 400–700 words.")
    else:
        warns.append(f"Résumé is long ({words} words) — trim to 1–2 focused pages.")

    if any(v in low for v in _ACTION_VERBS):
        score += 3
    else:
        warns.append("Start bullet points with action verbs (Built, Led, Optimized…).")

    return min(20, score), warns


def ats_match(resume_text: str, resume_skills: list[str], jd_text: str) -> dict:
    """
    Compute an ATS-style match report.

    Returns a dict:
        {
          "score": int 0-100,
          "verdict": str,
          "skills_matched": [...], "skills_missing": [...],
          "terms_matched": [...], "terms_missing": [...],
          "hygiene_score": int, "warnings": [...], "suggestions": [...],
        }
    """
    kw = extract_jd_keywords(jd_text)
    jd_skills, jd_terms = kw["skills"], kw["terms"]
    resume_skill_set = {s.lower() for s in resume_skills}
    resume_low = resume_text.lower()

    # 1. Skill coverage (55 pts)
    if jd_skills:
        matched_skills = [s for s in jd_skills if s in resume_skill_set]
        missing_skills = [s for s in jd_skills if s not in resume_skill_set]
        skill_pts = 55 * len(matched_skills) / len(jd_skills)
    else:
        matched_skills, missing_skills, skill_pts = [], [], 40.0  # neutral if JD has no tech skills

    # 2. JD term coverage (25 pts)
    if jd_terms:
        matched_terms = [t for t in jd_terms
                         if re.search(r'\b' + re.escape(t) + r'\b', resume_low)]
        missing_terms = [t for t in jd_terms if t not in matched_terms]
        term_pts = 25 * len(matched_terms) / len(jd_terms)
    else:
        matched_terms, missing_terms, term_pts = [], [], 18.0

    # 3. Hygiene (20 pts)
    hygiene_pts, warnings = _hygiene(resume_text)

    score = round(skill_pts + term_pts + hygiene_pts)
    score = max(0, min(100, score))

    if score >= 80:
        verdict = "Excellent — strongly aligned with this role."
    elif score >= 60:
        verdict = "Good — competitive, with a few gaps to close."
    elif score >= 40:
        verdict = "Fair — tailor your résumé before applying."
    else:
        verdict = "Low — significant gaps for this specific role."

    suggestions: list[str] = []
    if missing_skills:
        suggestions.append(
            "Add or emphasise these in-demand skills the JD asks for: "
            + ", ".join(missing_skills[:8]) + "."
        )
    if missing_terms:
        suggestions.append(
            "Mirror the job's language by naturally including terms like: "
            + ", ".join(missing_terms[:8]) + "."
        )
    suggestions.extend(warnings)
    if not suggestions:
        suggestions.append("Great alignment — quantify achievements (%, ₹, time saved) to stand out.")

    return {
        "score": score,
        "verdict": verdict,
        "skills_matched": matched_skills,
        "skills_missing": missing_skills,
        "terms_matched": matched_terms,
        "terms_missing": missing_terms,
        "hygiene_score": hygiene_pts,
        "warnings": warnings,
        "suggestions": suggestions,
    }
