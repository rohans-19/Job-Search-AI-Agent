import re
import logging


PREDEFINED_SKILLS = {
    "python", "java", "sql", "machine learning", "data analysis", 
    "react", "javascript", "node.js", "c++", "aws", "docker", 
    "kubernetes", "git", "linux", "html", "css", "c#", "ruby", 
    "golang", "rust", "php", "typescript", "swift", "kotlin", 
    "django", "flask", "spring boot", "tensorflow", "pytorch", 
    "scikit-learn", "pandas", "numpy", "powerbi", "tableau", 
    "agile", "scrum", "devops", "ci/cd", "mongodb", "postgresql", 
    "mysql", "redis", "elasticsearch"
}

def extract_skills(resume_text: str) -> list[str]:
    """
    Extracts predefined skills from resume text.
    
    Args:
        resume_text (str): The cleaned text extracted from a resume.
        
    Returns:
        list[str]: A list of deduplicated skills found in the resume.
    """
    if not resume_text:
        return []
        
    resume_lower = resume_text.lower()
    found_skills = set()
    
    for skill in PREDEFINED_SKILLS:
        # Use regex to find whole-word matches to avoid partial matching
        # e.g. "java" shouldn't match inside "javascript"
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, resume_lower):
            found_skills.add(skill)
            
    extracted = sorted(list(found_skills))
    logging.info(f"Extracted {len(extracted)} skills from resume.")
    return extracted
