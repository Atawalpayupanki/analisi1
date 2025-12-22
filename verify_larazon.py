import requests
from bs4 import BeautifulSoup
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.article_extractor import extract_article_text
from src.article_downloader import download_article_html

def test_larazon():
    print("Fetching La Razón RSS to get a valid recent URL...")
    rss_url = "https://www.larazon.es/rss/portada.xml"
    try:
        r = requests.get(rss_url, timeout=10)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')
        if not items:
            print("No items found in RSS")
            return
            
        # Try first 3 items
        for item in items[:3]:
            url = item.link.text.strip()
            print(f"\nTesting URL: {url}")
            
            result = download_article_html(url)
            if not result.html:
                print("  Download failed")
                continue
                
            extracted = extract_article_text(result.html, url)
            print(f"  Status: {extracted.extraction_status}")
            print(f"  Method: {extracted.extraction_method}")
            print(f"  Text Len: {len(extracted.text or '')}")
            
            if extracted.text:
                print(f"  Snippet: {extracted.text[:100].replace(chr(10), ' ')}...")
                
            if extracted.extraction_status == 'ok' and len(extracted.text or '') > 500:
                print("  SUCCESS: Good extraction")
                return
        
        print("\nCould not successfully extract from the first 3 articles.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_larazon()
