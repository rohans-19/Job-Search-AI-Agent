def match_jobs(jobs: list[dict], skills: list[str], pref_location: str, min_salary: float = None) -> list[dict]:
    """
    Scores and sorts a list of jobs based on skills, location, and salary matches.

    Matching Logic:
    - +1 for each user skill found in the job title.
    - +1 if requested location is a substring of the job location.
    - +1 if job's median salary meets or exceeds min_salary.

    Args:
        jobs (list[dict]): The list of standardized job dictionaries.
        skills (list[str]): The extracted skills from the user's resume.
        pref_location (str): The preferred job location.
        min_salary (float, optional): The minimum acceptable salary.

    Returns:
        list[dict]: A sorted list of jobs augmented with a 'match_score' key, descending.
    """
    scored_jobs = []
    
    pref_loc_lower = pref_location.lower().strip()
    
    for job in jobs:
        score = 0
        job_title_lower = job["title"].lower()
        job_loc_lower = job["location"].lower()
        
       
        for skill in skills:
            if skill.lower() in job_title_lower:
                score += 1
                
        
        if pref_loc_lower in job_loc_lower:
            score += 1
            
        
        if min_salary is not None:
            job_salary = job.get("median_salary_value")
            if job_salary is not None and job_salary >= min_salary:
                score += 1
                
        
        job_scored = job.copy()
        job_scored["match_score"] = score
        scored_jobs.append(job_scored)
        
    
    scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    return scored_jobs
