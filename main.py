import os
import json
import logging
from resume_parser import extract_resume_text
from skills import extract_skills
from jobs import get_unified_jobs
from matcher import match_jobs
from company import fetch_company_research_links


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def prompt_user_input(prompt_text: str, required: bool = True) -> str:
    """Helper to cleanly prompt the user with validation."""
    while True:
        val = input(prompt_text).strip().strip('"').strip("'")
        if val:
            return val
        if not required:
            return ""
        print("This field is required. Please try again.")

def main():
    print("=========================================")
    print("        AI Career Assistant CLI        ")
    print("=========================================")
    
    
    print("\n--- 1. Search Preferences ---")
    role = prompt_user_input("Enter the job role you are looking for (e.g. Data Analyst): ")
    location = prompt_user_input("Enter your preferred city (e.g. Mumbai): ")
    salary_input = prompt_user_input("Enter your minimum salary requirement (or press Enter to skip): ", required=False)
    
    min_salary = None
    if salary_input:
        try:
            min_salary = float(salary_input.replace(",", ""))
        except ValueError:
            logging.warning("Could not parse salary as a number. Ignoring salary requirement.")

    
    print("\n--- 2. Resume Upload ---")
    resume_path = prompt_user_input("Enter the path to your PDF resume: ")
    resume_text = extract_resume_text(resume_path)
    
    if not resume_text:
        print("Failed to extract text from the resume. Proceeding with 0 skills.")
        skills = []
    else:
        
        skills = extract_skills(resume_text)
        print(f"Detected Skills ({len(skills)}): {', '.join(skills)}")
        
    
    print("\n--- 3. Fetching Jobs ---")

    app_id = os.environ.get("ADZUNA_APP_ID", "c6f6b204")
    app_key = os.environ.get("ADZUNA_APP_KEY", "5fd40344881248436df8a9b0198ef5c6")
    
    all_jobs = get_unified_jobs(role, location, app_id, app_key, count=15)
    
    if not all_jobs:
        print("No jobs found for these parameters.")
        return

   
    print("\n--- 4. Matching Jobs to your Profile ---")
    ranked_jobs = match_jobs(all_jobs, skills, location, min_salary)
    
    top_matches = ranked_jobs[:5]
    
 
    print(f"\n--- 5. Top {len(top_matches)} Job Matches ---")
    for idx, job in enumerate(top_matches, 1):
        print(f"\n[{idx}] {job['title']}")
        print(f"    Company : {job['company']}")
        print(f"    Location: {job['location']}")
        print(f"    Salary  : {job['salary']}")
        print(f"    Source  : {job['source']}")
        print(f"    Score   : {job['match_score']} point(s)")
        
       
        if job["company"] and job["company"].lower() != "unknown":
            print(f"    Researching '{job['company']}'...")
            links = fetch_company_research_links(job["company"])
            if links:
                print("    Company Links:")
                for link in links:
                    print(f"      - {link}")
            else:
                print("    Company Links: None found.")
        else:
            print("    Company Links: Skipped (no valid company name).")

    print("\n=========================================")
    print("   Application Run Complete! Good luck!  ")
    print("=========================================")

if __name__ == "__main__":
    main()
