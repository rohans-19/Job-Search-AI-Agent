import requests
from googlesearch import search
import logging

# Configure basic logging for the module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def fetch_jobs(role: str, location: str, app_id: str, app_key: str, count: int = 10) -> list[dict]:
    """
    Fetches job listings from the Adzuna API (India region).
    
    Args:
        role (str): The job role (e.g., "Python Developer").
        location (str): The job location (e.g., "Bengaluru").
        app_id (str): Adzuna API App ID.
        app_key (str): Adzuna API App Key.
        count (int): Number of results to fetch per page.
        
    Returns:
        list[dict]: A list of job dictionaries, empty list on failure.
    """
    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": role,
        "where": location,
        "results_per_page": count,
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        jobs = []
        for job in data.get("results", []):
            
            # Format salary label cleanly
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")
            
            if salary_min and salary_max:
                salary_label = f"₹{salary_min:,.0f} - ₹{salary_max:,.0f}"
            elif salary_min:
                salary_label = f"from ₹{salary_min:,.0f}"
            else:
                salary_label = "Not Disclosed"

            jobs.append({
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", ""),
                "location": job.get("location", {}).get("display_name", ""),
                "salary": salary_label,
            })
            
        return jobs
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching jobs from Adzuna: {e}")
        return []


def fetch_company_research_links(company_name: str, num_results: int = 3) -> list[str]:
    """
    Fetches the top relevant links for a company using Google Search.
    Includes a fallback search if Google blocks the request.
    
    Args:
        company_name (str): The name of the company to research.
        num_results (int): The number of top URLs to return.
        
    Returns:
        list[str]: A list of URLs relevant to the company.
    """
    if not company_name:
        return []
    
    # Refining the search query to get the most relevant official resources
    query = f"{company_name} company profile OR official site"
    links = []
    
    try:
        # googlesearch-python outputs an iterator of URLs
        for url in search(query, num_results=num_results):
            links.append(url)
            # googlesearch-python's current version respects num_results, 
            # but we break early just in case it yields more.
            if len(links) >= num_results:
                break
    except Exception as e:
        logging.warning(f"googlesearch-python exception: {e}")
        
    # Fallback to DuckDuckGo HTML scraper if Google bot-protection blocked the request
    if not links:
        logging.info("Primary search blocked/empty. Using fallback search...")
        try:
            from bs4 import BeautifulSoup
            url = "https://html.duckduckgo.com/html/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.post(url, data={"q": query}, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href')
                if href and href.startswith('//duckduckgo.com/l/?uddg='):
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    actual_url = parsed.get('uddg', [href])[0]
                    if actual_url not in links:
                        links.append(actual_url)
                elif href and href.startswith('http'):
                    if href not in links:
                        links.append(href)
                
                if len(links) >= num_results:
                    break
        except Exception as e:
            logging.error(f"Fallback search also failed: {e}")
            
    return links


def get_enriched_jobs(role: str, location: str, app_id: str, app_key: str, count: int = 5) -> list[dict]:
    """
    Integrates job search and company research. Fetches jobs from Adzuna 
    and enriches each result with company research links.
    
    Args:
        role (str): Job role.
        location (str): Job location.
        app_id (str): Adzuna API App ID.
        app_key (str): Adzuna API App Key.
        count (int): Max number of jobs to fetch.
        
    Returns:
        list[dict]: A list of structured dictionaries containing job data and research links.
    """
    logging.info(f"Fetching up to {count} jobs for '{role}' in '{location}'...")
    jobs = fetch_jobs(role, location, app_id, app_key, count=count)
    
    if not jobs:
        logging.warning("No jobs found or failed to fetch jobs.")
        return []
        
    enriched_jobs = []
    
    for idx, job in enumerate(jobs, 1):
        company_name = job.get("company", "")
        
        logging.info(f"[{idx}/{len(jobs)}] Researching company: {company_name or 'Unknown'}...")
        links = fetch_company_research_links(company_name) if company_name else []
        
        structured_job = {
            "title": job.get("title", ""),
            "company": company_name,
            "location": job.get("location", ""),
            "salary": job.get("salary", ""),
            "links": links
        }
        enriched_jobs.append(structured_job)
        
    logging.info("Enrichment complete.")
    return enriched_jobs


if __name__ == "__main__":
    import json
    import os
    
    # To test locally, you can set these variables or update them directly
    # e.g. export ADZUNA_APP_ID="your_id"
    TEST_APP_ID = os.environ.get("ADZUNA_APP_ID", "c6f6b204") # Fallback to default in previous script
    TEST_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "5fd40344881248436df8a9b0198ef5c6")

    print("--- Career Integration Agent ---")
    user_role = input("Enter the job role you are looking for (e.g. Python Developer): ").strip()
    user_location = input("Enter the city or location (e.g. Bengaluru): ").strip()

    if user_role and user_location:
        results = get_enriched_jobs(
            role=user_role,
            location=user_location,
            app_id="c6f6b204",
            app_key="5fd40344881248436df8a9b0198ef5c6",
            count=3  # Limit for a quick test
        )
        
        print("\nFinal Structured Output:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("Error: Both role and location are required.")
