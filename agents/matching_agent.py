"""
agents/matching_agent.py
-------------------------
Job Matching Agent.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

class JobMatchingAgent(BaseAgent):
    """
    JobMatchingAgent computes an aggregate match_score for each job by
    summing skill matches (title + description), location_score,
    salary_score, and compatibility_score.
    """

    def match_jobs(self, jobs: list[dict], skills: list[str],
                   pref_location: str, min_salary: float | None = None) -> list[dict]:
        pref_loc_lower = pref_location.lower().strip()
        scored = []
        for job in jobs:
            score = 0
            title_lower = job.get("title", "").lower()
            loc_lower   = job.get("location", "").lower()
            # Include job description for richer skill matching
            desc_lower  = job.get("description", "").lower()

            # --- Skill match: check both title and description ---
            matched_skills = []
            for skill in skills:
                skill_lower = skill.lower()
                if skill_lower in title_lower or skill_lower in desc_lower:
                    score += 1
                    matched_skills.append(skill)

            # Store matched skills on the job dict so UI can display them
            job["matched_skills"] = matched_skills

            # --- Location match ---
            if "location_score" in job:
                score += job["location_score"]
            elif pref_loc_lower and pref_loc_lower in loc_lower:
                score += 1

            # --- Salary match ---
            if "salary_score" in job:
                score += job["salary_score"]
            elif min_salary is not None:
                job_salary = job.get("salary_lpa")
                if job_salary and job_salary >= min_salary:
                    score += 1

            # --- Work preference match ---
            if "compatibility_score" in job:
                score += job["compatibility_score"]

            enriched = job.copy()
            enriched["match_score"] = score
            scored.append(enriched)

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored

    def run(self, context: AgentContext) -> AgentContext:
        context.enriched_jobs = self.match_jobs(
            context.enriched_jobs,
            context.skills,
            context.search_location,
            context.expected_salary,
        )
        logger.info("JobMatchingAgent: Ranked %d job(s) by match score.",
                    len(context.enriched_jobs))
        return context
