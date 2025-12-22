
from src.feeds_list import load_feeds, load_feeds_zh
import logging

# Config logger to avoid noise
logging.basicConfig(level=logging.ERROR)

def test_feeds():
    print("Testing feeds metadata...")
    
    # Test Normal Feeds (feeds.json)
    # create a dummy feeds.json if needed or use existing
    # We'll try to load the real one, handling if it doesn't exist
    
    try:
        feeds = load_feeds('config/feeds.json')
        if feeds:
            print(f"Loaded {len(feeds)} normal feeds.")
            first = feeds[0]
            print(f"Sample feed metadata: {first.get('procedencia')}, {first.get('idioma')}")
            if first.get('procedencia') == 'España':
                print("SUCCESS: Normal feeds have 'España' origin.")
            else:
                print("FAILURE: Normal feeds missing 'España' origin.")
        else:
            print("WARNING: No normal feeds loaded (file missing or empty?).")
    except Exception as e:
        print(f"Error loading normal feeds: {e}")

    # Test Chinese Feeds (rss_feeds_zh.json)
    try:
        feeds_zh = load_feeds_zh('config/rss_feeds_zh.json')
        if feeds_zh:
            print(f"Loaded {len(feeds_zh)} Chinese feeds.")
            first = feeds_zh[0]
            print(f"Sample ZH feed metadata: {first.get('procedencia')}, {first.get('idioma')}")
            if first.get('procedencia') == 'China':
                print("SUCCESS: Chinese feeds have 'China' origin.")
            else:
                print("FAILURE: Chinese feeds missing 'China' origin.")
        else:
            print("WARNING: No Chinese feeds loaded.")

    except Exception as e:
        print(f"Error loading Chinese feeds: {e}")

if __name__ == "__main__":
    test_feeds()
