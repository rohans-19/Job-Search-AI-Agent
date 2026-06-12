"""
agents/discovery_agent.py
--------------------------
Job Discovery Agent — Live API connectors only.

Active connectors (real-time data):
  - Adzuna  : requires ADZUNA_APP_ID + ADZUNA_APP_KEY in .env
  - Jooble  : requires JOOBLE_API_KEY in .env

Mock connectors (Naukri, TimesJobs) have been intentionally removed.
"""

import logging
from agents.base_agent import BaseAgent, AgentContext
from database import update_source_quality, get_source_quality_stats, initialize_database
from connectors.adzuna_connector import AdzunaConnector
from connectors.jooble_connector import JoobleConnector
from connectors.aggregator import _deduplicate, _sort_by_relevance, _persist_jobs
import config

logger = logging.getLogger(__name__)

class JobDiscoveryAgent(BaseAgent):
    """
    JobDiscoveryAgent fetches jobs from live API connectors only, deduplicates,
    persists to SQLite, and populates context.raw_jobs and context.source_metadata.

    If context.skills is populated (by SkillExtractionAgent from a resume),
    the top 3 skills are appended to the search query for more targeted results.
    """
    def run(self, context: AgentContext) -> AgentContext:
        initialize_database()
        role = context.search_role.strip()
        location = context.search_location.strip()

        if not role or not location:
            logger.error("JobDiscoveryAgent: role and location are required.")
            context.raw_jobs = []
            context.source_metadata = {}
            return context

        count = config.JOB_FETCH_COUNT

        # ── Build skill-enriched query ─────────────────────────────────────────
        # Append top 3 skills from resume (if any) to the search role for richer results
        skill_terms = context.skills[:3] if context.skills else []
        if skill_terms:
            enriched_role = f"{role} {' '.join(skill_terms)}"
            logger.info(
                "JobDiscoveryAgent: Enriching query with resume skills: '%s' → '%s'",
                role, enriched_role
            )
        else:
            enriched_role = role
            logger.info("JobDiscoveryAgent: No resume skills — using base role query: '%s'", role)

        # ── Resolve Credentials (Context Overrides > .env Config) ──────────────
        adzuna_id = context.adzuna_app_id or config.ADZUNA_APP_ID
        adzuna_key = context.adzuna_app_key or config.ADZUNA_APP_KEY
        jooble_key = context.jooble_api_key or config.JOOBLE_API_KEY

        # ── Build live connector registry ──────────────────────────────────────
        connector_instances = {}

        if adzuna_id and adzuna_key:
            connector_instances["Adzuna"] = AdzunaConnector(adzuna_id, adzuna_key)
            logger.info("JobDiscoveryAgent: Adzuna connector enabled.")
        else:
            logger.warning("JobDiscoveryAgent: Adzuna skipped — App ID or Key not set.")

        if jooble_key:
            connector_instances["Jooble"] = JoobleConnector(jooble_key)
            logger.info("JobDiscoveryAgent: Jooble connector enabled.")
        else:
            logger.warning("JobDiscoveryAgent: Jooble skipped — API key not set.")

        if not connector_instances:
            logger.error("JobDiscoveryAgent: No live API credentials found. "
                         "Set ADZUNA_APP_ID/KEY or JOOBLE_API_KEY in your .env file or input them in the UI sidebar.")
            context.raw_jobs = []
            context.source_metadata = {}
            return context

        # ── Fetch from each live connector ─────────────────────────────────────
        all_jobs = []
        for name, connector in connector_instances.items():
            success, yielded = False, 0
            try:
                results = connector.fetch(enriched_role, location, count=count)
                yielded = len(results)
                all_jobs.extend(results)
                success = True
                logger.info("JobDiscoveryAgent: [%s] fetched %d job(s).", name, yielded)
            except Exception as exc:
                logger.error("JobDiscoveryAgent: [%s] failed: %s", name, exc)
            update_source_quality(name, success, yielded)

        unique_jobs = _deduplicate(all_jobs)
        _persist_jobs(unique_jobs)
        sorted_jobs = _sort_by_relevance(unique_jobs)

        context.raw_jobs = sorted_jobs
        context.source_metadata = get_source_quality_stats()
        logger.info("JobDiscoveryAgent: %d unique real-time job(s) discovered.", len(sorted_jobs))
        return context
