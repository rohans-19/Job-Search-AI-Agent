"""
agents/salary_agent.py
-----------------------
Salary Intelligence Agent.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext
from database import (
    save_historical_salary_range, get_historical_salary_ranges,
    save_user_preferences, initialize_database,
)

logger = logging.getLogger(__name__)

class SalaryIntelligenceAgent(BaseAgent):
    """
    SalaryIntelligenceAgent normalizes salaries, scores suitability,
    records historical trends, and enriches context.enriched_jobs.
    """

    def __init__(self):
        initialize_database()

    def convert_to_lpa(self, val) -> float | None:
        if val is None:
            return None
        try:
            val_float = float(val)
            if val_float <= 0:
                return None
            if val_float >= 100000:
                return round(val_float / 100000.0, 1)
            return round(val_float, 1)
        except (ValueError, TypeError):
            return None

    def compare_salary(self, job_lpa: float | None, expected_lpa: float | None) -> str:
        if job_lpa is None:
            return "Salary not disclosed"
        if expected_lpa is None or expected_lpa <= 0:
            return f"Offered: {job_lpa} LPA"
        diff = job_lpa - expected_lpa
        if diff > 0:
            return f"Exceeds expectation by {diff:.1f} LPA"
        elif diff == 0:
            return "Matches expectation"
        return f"Below expectation by {abs(diff):.1f} LPA"

    def calculate_salary_score(self, job_lpa: float | None, expected_lpa: float | None) -> int:
        if job_lpa is None or expected_lpa is None or expected_lpa <= 0:
            return 0
        if job_lpa >= expected_lpa:
            return 2
        elif job_lpa >= expected_lpa * 0.9:
            return 1
        return 0

    def process_salaries(self, jobs: list[dict], expected_lpa: float | None) -> list[dict]:
        processed = []
        for job in jobs:
            salary_lpa = self.convert_to_lpa(job.get("salary_lpa"))
            enriched = job.copy()
            enriched["salary_lpa"] = salary_lpa
            enriched["normalized_salary"] = f"{salary_lpa} LPA" if salary_lpa else "Not Disclosed"
            enriched["salary_score"] = self.calculate_salary_score(salary_lpa, expected_lpa)
            enriched["salary_comparison"] = self.compare_salary(salary_lpa, expected_lpa)
            processed.append(enriched)
        return processed

    def save_salary_preferences(self, expected_lpa: float) -> bool:
        logger.info("SalaryIntelligenceAgent: Saving expected salary: %s LPA", expected_lpa)
        return save_user_preferences(preferred_salary_lpa=expected_lpa) is not None

    def record_historical_ranges(self, jobs: list[dict], role: str, location: str) -> bool:
        salaries = [j["salary_lpa"] for j in jobs if j.get("salary_lpa") is not None]
        if not salaries:
            return False
        return save_historical_salary_range(
            role, location, min(salaries), max(salaries),
            round(sum(salaries) / len(salaries), 1)
        )

    def get_historical_ranges(self, role: str, location: str) -> list[dict]:
        return get_historical_salary_ranges(role, location)

    def run(self, context: AgentContext) -> AgentContext:
        expected_lpa = self.convert_to_lpa(context.expected_salary)
        if expected_lpa:
            self.save_salary_preferences(expected_lpa)

        context.enriched_jobs = self.process_salaries(context.enriched_jobs, expected_lpa)
        self.record_historical_ranges(
            context.enriched_jobs, context.search_role, context.search_location
        )
        logger.info("SalaryIntelligenceAgent: Processed salaries for %d job(s).",
                    len(context.enriched_jobs))
        return context
