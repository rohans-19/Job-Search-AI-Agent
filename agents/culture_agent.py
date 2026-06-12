"""
agents/culture_agent.py
------------------------
Company Culture Intelligence Agent.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext
from company_culture_agent import CompanyCultureAgent as _CultureCore

logger = logging.getLogger(__name__)

class CompanyCultureAgent(BaseAgent):
    """
    CompanyCultureAgent enriches each job in context.enriched_jobs with
    WLB, career growth, salary competitiveness, and remote-friendliness scores
    from the CompanyCultureAgent core (which uses DB cache + web scraping).
    """

    def __init__(self):
        self._core = _CultureCore()

    def get_culture_insights(self, company_name: str) -> dict:
        return self._core.get_culture_insights(company_name)

    def run(self, context: AgentContext) -> AgentContext:
        enriched = []
        for job in context.enriched_jobs:
            company = job.get("company", "Unknown")
            culture = self._core.get_culture_insights(company)
            enriched_job = job.copy()
            enriched_job["culture_wlb"]    = culture.get("work_life_balance", "Moderate")
            enriched_job["culture_growth"] = culture.get("career_growth", "Moderate")
            enriched_job["culture_salary"] = culture.get("salary_competitiveness", "Average")
            enriched_job["culture_remote"] = culture.get("remote_friendly", "Hybrid")
            enriched_job["culture_summary"] = culture.get("overall_summary", "")
            enriched.append(enriched_job)

        context.enriched_jobs = enriched
        logger.info("CompanyCultureAgent: Culture insights attached to %d job(s).",
                    len(context.enriched_jobs))
        return context
