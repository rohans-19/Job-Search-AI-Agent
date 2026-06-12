"""
agents/recommendation_agent.py
--------------------------------
Recommendation Agent.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

class RecommendationAgent(BaseAgent):
    """
    RecommendationAgent scores company culture alignment, re-ranks jobs by
    recommendation_score, and produces a natural-language career_advice summary.
    """

    def _culture_score(self, job: dict, preferred_mode: str) -> int:
        score = 0
        if job.get("culture_wlb") in ["Excellent", "Good"]:
            score += 1
        if job.get("culture_growth") == "High":
            score += 1
        if job.get("culture_salary") in ["High", "Competitive"]:
            score += 1

        remote = (job.get("culture_remote") or "").lower()
        user_mode = preferred_mode.lower()
        if any(k in user_mode for k in ["remote", "home", "wfh"]) and remote == "yes":
            score += 1
        elif "hybrid" in user_mode and remote == "hybrid":
            score += 1
        elif all(k not in user_mode for k in ["remote", "hybrid"]) and remote == "no":
            score += 1
        return score

    def recommend_jobs(self, jobs: list[dict],
                       user_prefs: dict | None = None) -> list[dict]:
        if not user_prefs:
            user_prefs = {}
        preferred_mode = user_prefs.get("work_from_home_preference", "Remote")

        recommended = []
        for job in jobs:
            c_score = self._culture_score(job, preferred_mode)
            enriched = job.copy()
            enriched["culture_score"] = c_score
            enriched["recommendation_score"] = job.get("match_score", 0) + c_score
            recommended.append(enriched)

        recommended.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommended

    def _build_career_advice(self, top_jobs: list[dict], context: AgentContext) -> str:
        if not top_jobs:
            return "No matching jobs found. Try broadening your search role or location."

        top = top_jobs[0]
        lines = [
            f"🎯 Career Advice for {context.search_role} in {context.search_location}",
            "=" * 60,
            f"\n✅ Top Recommendation: {top['title']} at {top['company']}",
            f"   📍 Location    : {top.get('location', 'N/A')}",
            f"   💰 Salary      : {top.get('normalized_salary', 'Not Disclosed')}",
            f"   ⭐ Rec Score   : {top.get('recommendation_score', 0)} "
            f"(Match: {top.get('match_score', 0)} + Culture: {top.get('culture_score', 0)})",
            f"\n🏢 Company Culture — {top.get('company')}:",
            f"   ⚖️  WLB              : {top.get('culture_wlb', 'N/A')}",
            f"   🚀 Career Growth     : {top.get('culture_growth', 'N/A')}",
            f"   💵 Salary Comp.      : {top.get('culture_salary', 'N/A')}",
            f"   🏠 Remote Friendly   : {top.get('culture_remote', 'N/A')}",
            f"   📝 {top.get('culture_summary', '')}",
        ]

        if len(top_jobs) > 1:
            lines.append("\n📋 Other Strong Matches:")
            for job in top_jobs[1:4]:
                lines.append(
                    f"   • {job['title']} at {job['company']} "
                    f"(Score: {job.get('recommendation_score', 0)}, "
                    f"WLB: {job.get('culture_wlb', 'N/A')})"
                )

        if context.skills:
            lines.append(f"\n🛠️  Skills detected: {', '.join(context.skills[:10])}")

        lines.append("\n💡 Next Steps:")
        lines.append("   1. Apply to the top-recommended role above immediately.")
        lines.append("   2. Tailor your resume to highlight matching skills.")
        lines.append("   3. Research the company's interview process on Glassdoor/LinkedIn.")
        lines.append("   4. Prepare questions about the team culture and growth trajectory.")

        return "\n".join(lines)

    def run(self, context: AgentContext) -> AgentContext:
        user_prefs = {
            "work_from_home_preference": context.work_mode,
            "notice_period_days":        context.notice_days,
            "flexibility_preference":    context.flexibility,
        }
        context.enriched_jobs = self.recommend_jobs(context.enriched_jobs, user_prefs)
        context.career_advice = self._build_career_advice(context.enriched_jobs[:5], context)
        logger.info("RecommendationAgent: Generated career advice. Top %d job(s) re-ranked.",
                    len(context.enriched_jobs))
        return context
