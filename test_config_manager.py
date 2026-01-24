import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from config_manager import config
    config.load_all()
    print("Configuration loaded successfully!")
    print(f"App config loaded: {config.app_config is not None}")
    print(f"Feeds config loaded: {config.feeds_config is not None}")
    if config.feeds_config:
        print(f"Number of feeds sources: {len(config.feeds_config.feeds)}")
    print(f"Keywords config loaded: {config.keywords_config is not None}")
    if config.keywords_config:
        print(f"Number of keywords: {len(config.keywords_config.keywords)}")
except Exception as e:
    print(f"Error loading config: {e}")
