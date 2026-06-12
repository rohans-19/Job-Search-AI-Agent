"""
agents/skills_agent.py
----------------------
Skill Extraction Agent.
"""

import re
import logging
from agents.base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

# Comprehensive skill vocabulary covering modern tech stacks commonly found in resumes
PREDEFINED_SKILLS = {
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "golang",
    "rust", "php", "swift", "kotlin", "scala", "r", "matlab", "bash", "shell",
    "perl", "dart", "haskell", "elixir",

    # Web Frameworks
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "spring boot", "express", "next.js", "nuxt.js", "rails", "laravel",
    "asp.net", "graphql", "rest api", "grpc",

    # Data Science / ML / AI
    "machine learning", "deep learning", "data analysis", "data science",
    "nlp", "computer vision", "tensorflow", "pytorch", "scikit-learn",
    "keras", "xgboost", "lightgbm", "pandas", "numpy", "matplotlib",
    "seaborn", "opencv", "hugging face", "llm", "generative ai", "rag",
    "langchain", "transformers",

    # Data Engineering
    "sql", "spark", "hadoop", "kafka", "airflow", "dbt", "hive",
    "flink", "databricks", "snowflake", "bigquery", "redshift",
    "data pipeline", "etl", "data warehouse", "data lakehouse",

    # Cloud
    "aws", "azure", "gcp", "google cloud", "s3", "ec2", "lambda",
    "cloudformation", "terraform", "pulumi", "azure devops",

    # DevOps / Infrastructure
    "docker", "kubernetes", "linux", "git", "ci/cd", "jenkins",
    "github actions", "gitlab", "ansible", "helm", "prometheus",
    "grafana", "nginx", "terraform",

    # Databases
    "mongodb", "postgresql", "mysql", "redis", "elasticsearch",
    "cassandra", "dynamodb", "neo4j", "sqlite", "oracle",

    # BI / Analytics
    "powerbi", "tableau", "looker", "excel", "power query",

    # Methodologies
    "agile", "scrum", "devops", "microservices", "system design",
    "object oriented", "tdd", "bdd",

    # Mobile
    "android", "ios", "flutter", "react native",

    # Other
    "blockchain", "cybersecurity", "networking", "embedded systems",
}

class SkillExtractionAgent(BaseAgent):
    """
    SkillExtractionAgent reads context.resume_text and populates context.skills.
    """
    def run(self, context: AgentContext) -> AgentContext:
        resume_text = context.resume_text
        if not resume_text:
            logger.warning("SkillExtractionAgent: No resume text in context.")
            context.skills = []
            return context

        resume_lower = resume_text.lower()
        found_skills = set()

        for skill in PREDEFINED_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, resume_lower):
                found_skills.add(skill)

        context.skills = sorted(list(found_skills))
        logger.info("SkillExtractionAgent: Extracted %d skill(s): %s",
                    len(context.skills), ", ".join(context.skills))
        return context
