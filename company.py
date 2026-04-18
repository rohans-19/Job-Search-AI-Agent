import requests
import logging
from googlesearch import search

def fetch_company_research_links(company_name: str, num_results: int = 3) -> list[str]:
    """
    Fetches the top relevant links for a company using Google Search.
    Includes a fallback DuckDuckGo scraper if Google blocks the automated request.
    
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
