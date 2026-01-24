"""
Scraper for El País articles.
"""
import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

def scrape_elpais_article(url: str, retries: int = 3) -> Optional[Dict[str, str]]:
    """
    Extracts text from an El País news article.
    
    Args:
        url: News URL
        retries: Number of retries for failed requests
        
    Returns:
        dict with title and text, or None if failed
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "Título no encontrado"
            
            # Extract article text
            # El País uses 'article' tag or specific classes depending on version
            article_body = soup.find('article')
            
            if not article_body:
                # Fallback implementation
                article_body = soup.find('div', class_='article_body')
            
            if article_body:
                # Find all paragraphs
                paragraphs = article_body.find_all('p')
                text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            else:
                logger.warning(f"Could not find article body for {url}")
                text = ""
            
            if not text:
                return None
                
            return {
                'titulo': title,
                'texto': text
            }
            
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            logger.warning(f"Attempt {attempt+1}/{retries} failed for {url}: {e}. Retrying in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
            
    logger.error(f"Failed to scrape {url} after {retries} attempts")
    return None
