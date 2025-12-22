
import json
import feedparser
import requests
import os
from colorama import init, Fore, Style

init(autoreset=True)

CONFIG_PATH = r"c:\Users\pauta\Desktop\pau\bachiller\phipatia\analitzador\config\rss_feeds_zh.json"

def verify_feeds():
    if not os.path.exists(CONFIG_PATH):
        print(f"{Fore.RED}Config file not found: {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"{Fore.CYAN}Verifying feeds from {CONFIG_PATH}...\n")

    for source in data.get('feeds', []):
        name = source.get('nombre')
        print(f"{Fore.BLUE}Checking source: {name}")
        
        for url in source.get('urls', []):
            try:
                # Check accessibility
                response = requests.get(url, timeout=10)
                status_color = Fore.GREEN if response.status_code == 200 else Fore.RED
                print(f"  URL: {url} - Status: {status_color}{response.status_code}")

                if response.status_code == 200:
                    # Check parsing
                    feed = feedparser.parse(response.content)
                    if feed.bozo:
                        print(f"    {Fore.YELLOW}Warning: Feed parsing had issues (bozo=1)")
                        if hasattr(feed, 'bozo_exception'):
                             print(f"    Error: {feed.bozo_exception}")
                    
                    entry_count = len(feed.entries)
                    count_color = Fore.GREEN if entry_count > 0 else Fore.YELLOW
                    print(f"    Entries found: {count_color}{entry_count}")
                    # if entry_count > 0:
                    #     try:
                    #         safe_title = feed.entries[0].title.encode('gbk', 'replace').decode('gbk')
                    #         print(f"    Latest: {safe_title}")
                    #     except:
                    #         print(f"    Latest: {repr(feed.entries[0].title)}")

            except Exception as e:
                print(f"  {Fore.RED}Error checking {url}: {e}")
        print()

if __name__ == "__main__":
    verify_feeds()
