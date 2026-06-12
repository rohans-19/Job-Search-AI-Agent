"""
agents/work_preference_agent.py
--------------------------------
Work Preference Agent.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext
from database import save_user_preferences, get_user_preferences, initialize_database

logger = logging.getLogger(__name__)

class WorkPreferenceAgent(BaseAgent):
    """
    WorkPreferenceAgent scores jobs for work-mode and notice period compatibility.
    """

    def __init__(self):
        initialize_database()

    def evaluate_work_mode(self, job_title: str, job_location: str,
                           preferred_mode: str | None) -> int:
        if not preferred_mode or not preferred_mode.strip():
            return 2
        pref = preferred_mode.lower().strip()
        t, l = job_title.lower(), job_location.lower()
        is_remote = "remote" in t or "remote" in l or "wfh" in t
        is_hybrid = "hybrid" in t or "hybrid" in l
        job_mode = "remote" if is_remote else ("hybrid" if is_hybrid else "onsite")
        user_pref = ("remote" if any(k in pref for k in ["remote", "home", "wfh"])
                     else "hybrid" if "hybrid" in pref else "onsite")
        if job_mode == user_pref:
            return 2
        if (user_pref == "hybrid" and job_mode == "remote") or \
           (user_pref == "onsite" and job_mode == "hybrid"):
            return 1
        return 0

    def evaluate_notice_period(self, job_title: str, user_notice_days: int | None,
                               flexibility: str | None = "Strict") -> int:
        if user_notice_days is None:
            return 2
        t = job_title.lower()
        is_immediate = "immediate" in t or "immediate joiner" in t
        flex = (flexibility or "Strict").lower().strip()
        if is_immediate:
            if user_notice_days <= 15:
                return 2
            elif user_notice_days <= 30 and flex == "flexible":
                return 1
            return 0
        if user_notice_days <= 60:
            return 2
        elif user_notice_days <= 90:
            return 1
        return 0

    def score_jobs(self, jobs: list[dict], user_pref: dict | None = None) -> list[dict]:
        if not user_pref:
            user_pref = get_user_preferences()
        pref_mode = user_pref.get("work_from_home_preference")
        notice_days = user_pref.get("notice_period_days")
        flexibility = user_pref.get("flexibility_preference", "Strict")
        scored = []
        for job in jobs:
            w = self.evaluate_work_mode(job.get("title", ""), job.get("location", ""), pref_mode)
            n = self.evaluate_notice_period(job.get("title", ""), notice_days, flexibility)
            enriched = job.copy()
            enriched["work_mode_score"] = w
            enriched["notice_period_score"] = n
            enriched["compatibility_score"] = w + n
            scored.append(enriched)
        return scored

    def save_work_preferences(self, mode: str, notice_days: int, flexibility: str) -> bool:
        return save_user_preferences(
            work_from_home_preference=mode,
            notice_period_days=notice_days,
            flexibility_preference=flexibility
        ) is not None

    def run(self, context: AgentContext) -> AgentContext:
        user_pref = {
            "work_from_home_preference": context.work_mode,
            "notice_period_days": context.notice_days,
            "flexibility_preference": context.flexibility,
        }
        save_user_preferences(
            work_from_home_preference=context.work_mode,
            notice_period_days=context.notice_days,
            flexibility_preference=context.flexibility,
        )
        context.enriched_jobs = self.score_jobs(context.enriched_jobs, user_pref)
        logger.info("WorkPreferenceAgent: Scored %d job(s) for work compatibility.",
                    len(context.enriched_jobs))
        return context
