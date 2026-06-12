"""
orchestrator.py
---------------
Central Orchestrator for the Agentic AI Career Assistant.

Manages the sequential execution of all 9 agents, validates context state
between steps, and surfaces structured results to callers (CLI / Streamlit).

Pipeline:
    ResumeParserAgent
    → SkillExtractionAgent
    → JobDiscoveryAgent
    → LocationIntelligenceAgent
    → SalaryIntelligenceAgent
    → WorkPreferenceAgent
    → CompanyCultureAgent
    → JobMatchingAgent
    → RecommendationAgent
    → Final Career Advice
"""

import logging
import os
import tempfile
from agents import (
    AgentContext,
    ResumeParserAgent,
    SkillExtractionAgent,
    JobDiscoveryAgent,
    LocationIntelligenceAgent,
    SalaryIntelligenceAgent,
    WorkPreferenceAgent,
    CompanyCultureAgent,
    JobMatchingAgent,
    RecommendationAgent,
)
from database import initialize_database

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    AgentOrchestrator initializes all 9 agents and drives the full pipeline.

    Usage:
        orchestrator = AgentOrchestrator()
        context = orchestrator.build_context(
            search_role="Data Engineer",
            search_location="Bangalore",
            expected_salary=15.0,
            work_mode="Remote",
            notice_days=30,
            flexibility="Flexible",
            resume_bytes=<bytes>,   # optional — raw PDF bytes from file_uploader
        )
        final_context = orchestrator.run_pipeline(context)
        print(final_context.career_advice)
    """

    def __init__(self):
        initialize_database()
        self._pipeline = [
            ("Resume Parser",              ResumeParserAgent()),
            ("Skill Extraction",           SkillExtractionAgent()),
            ("Job Discovery",              JobDiscoveryAgent()),
            ("Location Intelligence",      LocationIntelligenceAgent()),
            ("Salary Intelligence",        SalaryIntelligenceAgent()),
            ("Work Preference",            WorkPreferenceAgent()),
            ("Company Culture",            CompanyCultureAgent()),
            ("Job Matching",               JobMatchingAgent()),
            ("Recommendation",             RecommendationAgent()),
        ]
        logger.info("AgentOrchestrator: Initialized with %d agent(s).", len(self._pipeline))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def build_context(
        self,
        search_role: str,
        search_location: str,
        expected_salary: float | None = None,
        work_mode: str = "Remote",
        notice_days: int = 30,
        flexibility: str = "Strict",
        resume_path: str | None = None,
        resume_bytes: bytes | None = None,
        adzuna_app_id: str | None = None,
        adzuna_app_key: str | None = None,
        jooble_api_key: str | None = None,
    ) -> AgentContext:
        """
        Convenience factory — creates a fully-populated AgentContext.

        If ``resume_bytes`` is supplied (e.g. from Streamlit's file_uploader),
        the bytes are written to a temporary PDF file whose path is stored in
        ``AgentContext.resume_path``.  The temp file is cleaned up inside
        ``run_pipeline()`` after the Resume Parser step completes.
        """
        ctx = AgentContext()
        ctx.search_role      = search_role.strip()
        ctx.search_location  = search_location.strip()
        ctx.expected_salary  = expected_salary
        ctx.work_mode        = work_mode
        ctx.notice_days      = notice_days
        ctx.flexibility      = flexibility
        ctx.adzuna_app_id    = adzuna_app_id
        ctx.adzuna_app_key   = adzuna_app_key
        ctx.jooble_api_key   = jooble_api_key
        ctx._temp_resume_path = None   # track for cleanup

        if resume_bytes:
            # Write bytes to a temp file so ResumeParserAgent can open it
            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False, prefix="resume_upload_"
            )
            tmp.write(resume_bytes)
            tmp.flush()
            tmp.close()
            ctx.resume_path = tmp.name
            ctx._temp_resume_path = tmp.name
            logger.info("AgentOrchestrator: Resume bytes saved to temp file: %s", tmp.name)
        elif resume_path:
            ctx.resume_path = resume_path
        else:
            ctx.resume_path = None

        return ctx

    def run_pipeline(self, context: AgentContext) -> AgentContext:
        """
        Sequentially runs each agent. Logs progress and validates critical
        outputs so a failed step degrades gracefully rather than crashing.
        Cleans up any temp resume file created from resume_bytes.
        """
        logger.info("=" * 60)
        logger.info("AgentOrchestrator: Starting pipeline for role='%s', location='%s'.",
                    context.search_role, context.search_location)

        for step_num, (name, agent) in enumerate(self._pipeline, start=1):
            logger.info("--- Step %d/%d: %s Agent ---",
                        step_num, len(self._pipeline), name)
            try:
                context = agent.run(context)
                self._validate_step(name, context)
            except Exception as exc:
                logger.error("AgentOrchestrator: Step '%s' raised an exception: %s",
                             name, exc, exc_info=True)
                # Degrade gracefully — continue pipeline with partial data.

        # ── Cleanup temp resume file (if created from uploaded bytes) ──
        temp_path = getattr(context, "_temp_resume_path", None)
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info("AgentOrchestrator: Cleaned up temp resume file: %s", temp_path)
            except OSError as e:
                logger.warning("AgentOrchestrator: Could not delete temp file '%s': %s", temp_path, e)

        logger.info("=" * 60)
        logger.info("AgentOrchestrator: Pipeline complete. "
                    "%d job(s) in final output.", len(context.enriched_jobs))
        return context

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_step(self, step_name: str, context: AgentContext) -> None:
        """Warns if a critical output is unexpectedly empty after a step."""
        checks = {
            "Job Discovery": lambda c: c.raw_jobs,
            "Job Matching":  lambda c: c.enriched_jobs,
            "Recommendation": lambda c: c.career_advice,
        }
        if step_name in checks and not checks[step_name](context):
            logger.warning("AgentOrchestrator: '%s' produced empty output.", step_name)


# ---------------------------------------------------------------------------
# Smoke test (python orchestrator.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("  Orchestrator Smoke Test")
    print("=" * 60)

    orchestrator = AgentOrchestrator()
    ctx = orchestrator.build_context(
        search_role="Software Developer",
        search_location="Bangalore",
        expected_salary=15.0,
        work_mode="Remote",
        notice_days=30,
        flexibility="Flexible",
        resume_path=None,  # No resume for smoke test
    )

    final = orchestrator.run_pipeline(ctx)

    print("\n" + "=" * 60)
    print(final.career_advice)
    print("=" * 60)
    print(f"\nSource Stats:")
    for src, stats in final.source_metadata.items():
        print(f"  [{src}] Yield: {stats['total_jobs_yielded']} | "
              f"Success Rate: {stats['success_rate_percent']}%")

    print(f"\nTop 3 Jobs:")
    for i, job in enumerate(final.enriched_jobs[:3], 1):
        print(f"  [{i}] {job['title']} @ {job['company']} "
              f"(Rec: {job.get('recommendation_score', 0)})")
