"""
interview.py
------------
Offline, text-based mock-interview engine.

Provides a curated question bank (role-specific + behavioural + India-specific
HR rounds) and a deterministic answer-feedback engine that scores a typed answer
on structure, specificity, relevance, and delivery — no external LLM required.

If you later add an LLM key you can swap `evaluate_answer` for a model call;
the return shape is intentionally simple.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Question bank
# ---------------------------------------------------------------------------
# Each question: text + the keywords a strong answer tends to touch.

_BEHAVIOURAL = [
    {"q": "Tell me about yourself and your career journey so far.",
     "kw": ["experience", "role", "project", "skills", "team"]},
    {"q": "Describe a challenging problem you solved. What was the impact?",
     "kw": ["problem", "approach", "solution", "result", "impact"]},
    {"q": "Tell me about a time you disagreed with a teammate. How did you handle it?",
     "kw": ["conflict", "communication", "resolved", "outcome", "team"]},
    {"q": "Describe a project you're most proud of and your specific contribution.",
     "kw": ["project", "built", "led", "result", "ownership"]},
    {"q": "Tell me about a time you failed and what you learned.",
     "kw": ["failure", "learned", "improved", "feedback", "change"]},
]

_INDIA_HR = [
    {"q": "What is your current notice period, and how soon can you join?",
     "kw": ["notice", "days", "join", "buyout", "serve"]},
    {"q": "What are your salary expectations (in LPA), and how flexible are you?",
     "kw": ["lpa", "expectation", "current", "negotiable", "market"]},
    {"q": "Why are you looking to leave your current company?",
     "kw": ["growth", "learning", "opportunity", "challenge", "role"]},
    {"q": "Are you open to relocation or a hybrid/onsite arrangement?",
     "kw": ["relocate", "remote", "hybrid", "onsite", "flexible"]},
    {"q": "Where do you see yourself in three to five years?",
     "kw": ["goal", "grow", "lead", "skills", "responsibility"]},
]

_ROLE_QUESTIONS: dict[str, list[dict]] = {
    "data scientist": [
        {"q": "How do you handle an imbalanced dataset in a classification problem?",
         "kw": ["resampling", "smote", "class weight", "precision", "recall", "auc"]},
        {"q": "Explain the bias–variance tradeoff with an example.",
         "kw": ["bias", "variance", "overfitting", "underfitting", "regularization"]},
        {"q": "Walk me through how you'd evaluate a model beyond accuracy.",
         "kw": ["precision", "recall", "f1", "roc", "confusion matrix"]},
    ],
    "machine learning engineer": [
        {"q": "How would you deploy and monitor an ML model in production?",
         "kw": ["docker", "api", "monitoring", "drift", "ci/cd", "latency"]},
        {"q": "What causes training–serving skew and how do you prevent it?",
         "kw": ["features", "pipeline", "consistency", "preprocessing", "skew"]},
        {"q": "How do you decide between batch and real-time inference?",
         "kw": ["latency", "throughput", "cost", "batch", "streaming"]},
    ],
    "data engineer": [
        {"q": "Design a pipeline to ingest and process daily sales data at scale.",
         "kw": ["etl", "spark", "airflow", "partition", "warehouse", "schedule"]},
        {"q": "How do you handle late-arriving or duplicate data in a pipeline?",
         "kw": ["idempotent", "dedup", "watermark", "upsert", "ordering"]},
        {"q": "Explain partitioning and how it improves query performance.",
         "kw": ["partition", "pruning", "scan", "performance", "cost"]},
    ],
    "backend developer": [
        {"q": "How would you design a rate limiter for a public API?",
         "kw": ["token bucket", "redis", "throttle", "limit", "distributed"]},
        {"q": "Explain how you'd keep a REST API secure.",
         "kw": ["auth", "jwt", "validation", "https", "rate limit"]},
        {"q": "How do you debug a slow database query?",
         "kw": ["index", "explain", "query plan", "n+1", "cache"]},
    ],
    "frontend developer": [
        {"q": "How do you optimise the load performance of a web app?",
         "kw": ["lazy", "bundle", "cache", "lighthouse", "code splitting"]},
        {"q": "Explain how you manage state in a large React application.",
         "kw": ["state", "context", "redux", "hooks", "props"]},
        {"q": "How do you make a UI accessible?",
         "kw": ["aria", "contrast", "keyboard", "semantic", "screen reader"]},
    ],
    "devops engineer": [
        {"q": "Walk me through a CI/CD pipeline you'd build for a microservice.",
         "kw": ["ci/cd", "docker", "kubernetes", "test", "deploy", "rollback"]},
        {"q": "How do you manage secrets and configuration across environments?",
         "kw": ["secrets", "vault", "env", "config", "encryption"]},
        {"q": "How would you set up monitoring and alerting for production?",
         "kw": ["prometheus", "grafana", "alert", "metrics", "logs"]},
    ],
}

_FILLERS = ["um", "uh", "basically", "actually", "you know", "kind of",
            "sort of", "like ", "literally", "stuff", "things"]
_STAR_CUES = {
    "situation": ["situation", "context", "when", "project", "at the time"],
    "task": ["task", "goal", "responsible", "needed to", "had to"],
    "action": ["i ", "we ", "implemented", "built", "designed", "decided", "led"],
    "result": ["result", "impact", "reduced", "increased", "improved", "%", "saved", "grew"],
}


def get_question_set(role: str, n_role: int = 3, n_behav: int = 2, n_hr: int = 2) -> list[dict]:
    """
    Assemble an interview set for a role: role-specific + behavioural + India HR.
    Falls back to behavioural-heavy set if the role isn't in the bank.
    """
    key = (role or "").strip().lower()
    role_qs: list[dict] = []
    for rk, qs in _ROLE_QUESTIONS.items():
        if rk == key or rk in key or key in rk:
            role_qs = qs
            break

    out = []
    for q in role_qs[:n_role]:
        out.append({**q, "round": "Technical"})
    for q in _BEHAVIOURAL[:n_behav]:
        out.append({**q, "round": "Behavioural"})
    for q in _INDIA_HR[:n_hr]:
        out.append({**q, "round": "HR"})
    return out


def available_roles() -> list[str]:
    """Roles with a dedicated technical question bank."""
    return sorted(r.title() for r in _ROLE_QUESTIONS)


def evaluate_answer(answer: str, keywords: list[str]) -> dict:
    """
    Score a typed answer (0–100) and return structured feedback.

    Returns:
        {"score": int, "strengths": [...], "improvements": [...],
         "word_count": int, "star": {part: bool}}
    """
    text = (answer or "").strip()
    low = text.lower()
    words = text.split()
    wc = len(words)

    strengths: list[str] = []
    improvements: list[str] = []

    if wc == 0:
        return {"score": 0, "strengths": [],
                "improvements": ["No answer provided — try to speak for 45–90 seconds."],
                "word_count": 0, "star": {k: False for k in _STAR_CUES}}

    # 1. Length (25)
    if 60 <= wc <= 220:
        length_pts = 25
        strengths.append("Good answer length — concise but complete.")
    elif wc < 60:
        length_pts = round(25 * wc / 60)
        improvements.append(f"Answer is short ({wc} words). Aim for 60–200 words with a concrete example.")
    else:
        length_pts = 18
        improvements.append(f"Answer is long ({wc} words). Tighten it — interviewers prefer focused answers.")

    # 2. STAR structure (30)
    star = {part: any(cue in low for cue in cues) for part, cues in _STAR_CUES.items()}
    star_hits = sum(star.values())
    star_pts = round(30 * star_hits / 4)
    if star_hits >= 3:
        strengths.append("Strong structure — your answer follows the STAR pattern.")
    else:
        missing = [p for p, ok in star.items() if not ok]
        improvements.append("Use the STAR method — add a clear " + ", ".join(missing) + ".")

    # 3. Specificity / metrics (20)
    has_metric = bool(re.search(r"\d", text))
    spec_pts = 20 if has_metric else 6
    if has_metric:
        strengths.append("Includes concrete numbers — quantified impact stands out.")
    else:
        improvements.append("Add measurable impact (%, ₹, time saved, scale).")

    # 4. Relevance to expected keywords (25)
    if keywords:
        hit = [k for k in keywords if k in low]
        rel_pts = round(25 * len(hit) / len(keywords))
        if hit:
            strengths.append("Covers key points: " + ", ".join(hit) + ".")
        miss = [k for k in keywords if k not in low]
        if miss:
            improvements.append("Consider mentioning: " + ", ".join(miss[:5]) + ".")
    else:
        rel_pts = 18

    # 5. Filler penalty
    filler_count = sum(low.count(f) for f in _FILLERS)
    penalty = min(10, filler_count * 2)
    if filler_count >= 3:
        improvements.append(f"Reduce filler words ({filler_count} found) for a crisper delivery.")

    score = max(0, min(100, length_pts + star_pts + spec_pts + rel_pts - penalty))
    return {"score": score, "strengths": strengths, "improvements": improvements,
            "word_count": wc, "star": star}
