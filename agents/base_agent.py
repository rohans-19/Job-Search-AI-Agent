"""
agents/base_agent.py
--------------------
Base agent classes and AgentContext definition for the Agentic AI Career Assistant.
"""

from typing import Optional, Any

class AgentContext:
    """
    AgentContext represents the shared state and memory of the agentic pipeline.
    Agents communicate by reading from and writing to this shared context.
    """
    def __init__(self):
        # 1. Inputs from User/Caller
        self.resume_path: Optional[str] = None
        self.search_role: str = ""
        self.search_location: str = ""
        self.expected_salary: Optional[float] = None
        
        # User preferences details
        self.work_mode: str = "Remote"
        self.notice_days: int = 30
        self.flexibility: str = "Strict"

        # Credentials overrides from UI
        self.adzuna_app_id: Optional[str] = None
        self.adzuna_app_key: Optional[str] = None
        self.jooble_api_key: Optional[str] = None
        
        # 2. Intermediate state
        self.resume_text: str = ""
        self.skills: list[str] = []
        
        # 3. Job Listings
        self.raw_jobs: list[dict] = []
        self.source_metadata: dict = {}
        self.enriched_jobs: list[dict] = []
        
        # 4. Final Output Insights
        self.career_advice: str = ""

class BaseAgent:
    """
    BaseAgent is the interface for all agents in the system.
    """
    def run(self, context: AgentContext) -> AgentContext:
        """
        Executes the agent's logic. Reads data from context, performs work,
        and returns the mutated or updated context.
        """
        raise NotImplementedError("Each agent must implement the run() method.")
