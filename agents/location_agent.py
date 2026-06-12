"""
agents/location_agent.py
-------------------------
Location Intelligence Agent.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext
from database import (
    SUPPORTED_CITIES, get_normalized_city,
    save_location_preference, get_preferred_city,
    get_location_history, get_jobs_by_city, save_search_history,
)

logger = logging.getLogger(__name__)

class LocationIntelligenceAgent(BaseAgent):
    """
    LocationIntelligenceAgent enriches jobs with location_score,
    saves location preference, and ranks by city match.
    """

    # Keep backward-compatible helper methods for app.py sidebar use
    def save_location_preference(self, city: str) -> bool:
        return save_location_preference(city)

    def get_jobs_by_city(self, city: str) -> list[dict]:
        return get_jobs_by_city(city)

    def get_preferred_city(self) -> str | None:
        return get_preferred_city()

    def get_location_history(self) -> list[str]:
        return get_location_history()

    def rank_jobs_by_location(self, jobs: list[dict], preferred_city: str | None = None) -> list[dict]:
        if not preferred_city:
            preferred_city = get_preferred_city()

        pref_normalized = get_normalized_city(preferred_city) if preferred_city else None

        enriched = []
        for job in jobs:
            job_city = get_normalized_city(job.get("location", ""))
            loc_score = 0
            if pref_normalized and job_city == pref_normalized:
                loc_score = 2
            elif job_city in SUPPORTED_CITIES:
                loc_score = 1
            enriched_job = job.copy()
            enriched_job["location_score"] = loc_score
            enriched.append(enriched_job)

        return sorted(enriched, key=lambda x: x["location_score"], reverse=True)

    def run(self, context: AgentContext) -> AgentContext:
        preferred_city = context.search_location

        # Save preference and history to SQLite
        save_location_preference(preferred_city)
        save_search_history(context.search_role, preferred_city)

        context.enriched_jobs = self.rank_jobs_by_location(
            context.raw_jobs, preferred_city
        )
        logger.info("LocationIntelligenceAgent: Ranked %d job(s) by location.",
                    len(context.enriched_jobs))
        return context
