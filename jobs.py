import requests
import logging

def fetch_adzuna_jobs(role: str, location: str, app_id: str, app_key: str, count: int = 15) -> list[dict]:
    """
    Fetches job listings from the Adzuna API (India region).
    """
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": role,
        "where": location,
        "results_per_page": count,
    }
    
    normalized_jobs = []
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        for job in data.get("results", []):
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")
            
            
            if salary_min and salary_max:
                salary_label = f"₹{salary_min:,.0f} - ₹{salary_max:,.0f}"
            elif salary_min:
                salary_label = f"from ₹{salary_min:,.0f}"
            else:
                salary_label = "Not Disclosed"

            median_salary = None
            if salary_min and salary_max:
                median_salary = (float(salary_min) + float(salary_max)) / 2
            elif salary_min:
                median_salary = float(salary_min)

            normalized_jobs.append({
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", "Unknown"),
                "location": job.get("location", {}).get("display_name", ""),
                "salary": salary_label,
                "median_salary_value": median_salary,
                "source": "Adzuna"
            })
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching jobs from Adzuna: {e}")
        
    return normalized_jobs


def fetch_mock_jobs(role: str, location: str) -> list[dict]:
    """
    A mock API simulation for a secondary job source.
    """

    return [
        {
            "title": f"Senior {role}",
            "company": "Tech Innovators Corp",
            "location": location,
            "salary": "₹1,200,000 - ₹1,800,000",
            "median_salary_value": 1500000.0,
            "source": "MockPlatform"
        },
        {
            "title": f"{role} Associate",
            "company": "Global Solutions Ltd",
            "location": f"{location} (Remote)",
            "salary": "Not Disclosed",
            "median_salary_value": None,
            "source": "MockPlatform"
        }
    ]

def get_unified_jobs(role: str, location: str, app_id: str, app_key: str, count: int = 15) -> list[dict]:
    """
    Fetches, standardizes, and deduplicates jobs from all configured sources.
    """
    logging.info(f"Fetching jobs for '{role}' in '{location}'...")
    
    adzuna_jobs = fetch_adzuna_jobs(role, location, app_id, app_key, count)
    mock_jobs = fetch_mock_jobs(role, location)
    
    all_jobs = adzuna_jobs + mock_jobs
    
 
    unique_jobs = []
    seen = set()
    
    for job in all_jobs:
        
        footprint = (job["title"].strip().lower(), job["company"].strip().lower())
        if footprint not in seen:
            seen.add(footprint)
            unique_jobs.append(job)
            
    logging.info(f"Retrieved {len(unique_jobs)} distinct jobs.")
    return unique_jobs
