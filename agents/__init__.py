"""
agents/__init__.py
-------------------
Agents package - exports all agent classes and shared context.
"""

from agents.base_agent import AgentContext, BaseAgent
from agents.resume_agent import ResumeParserAgent
from agents.skills_agent import SkillExtractionAgent
from agents.discovery_agent import JobDiscoveryAgent
from agents.location_agent import LocationIntelligenceAgent
from agents.salary_agent import SalaryIntelligenceAgent
from agents.work_preference_agent import WorkPreferenceAgent
from agents.culture_agent import CompanyCultureAgent
from agents.matching_agent import JobMatchingAgent
from agents.recommendation_agent import RecommendationAgent

__all__ = [
    "AgentContext",
    "BaseAgent",
    "ResumeParserAgent",
    "SkillExtractionAgent",
    "JobDiscoveryAgent",
    "LocationIntelligenceAgent",
    "SalaryIntelligenceAgent",
    "WorkPreferenceAgent",
    "CompanyCultureAgent",
    "JobMatchingAgent",
    "RecommendationAgent",
]
