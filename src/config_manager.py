"""
Centralized configuration manager using Pydantic for validation.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DownloaderConfig(BaseModel):
    timeout: int = 15
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    delay_between_requests_same_domain: float = 1.0
    user_agent: str = "Mozilla/5.0 (compatible; RSSChinaBot/1.0)"
    headers: Dict[str, str] = {}

class ExtractorConfig(BaseModel):
    min_text_length_ok: int = 200
    min_text_length_warning: int = 100
    favor_precision: bool = True
    include_tables: bool = True
    include_comments: bool = False
    include_links: bool = False
    domain_selectors: Dict[str, List[str]] = {}

class CleanerConfig(BaseModel):
    max_consecutive_newlines: int = 2
    normalize_unicode: bool = True
    remove_common_fragments: bool = True
    remove_patterns: List[str] = []

class EnricherConfig(BaseModel):
    extract_metadata: bool = True
    detect_language: bool = True
    metadata_fields: Dict[str, str] = {}

class OutputConfig(BaseModel):
    jsonl_path: str = "data/articles_full.jsonl"
    csv_path: str = "data/articles_full.csv"
    failed_path: str = "data/failed_extractions.jsonl"
    report_path: str = "data/extraction_report.json"
    csv_encoding: str = "utf-8-sig"
    include_html_in_output: bool = False

class LoggingConfig(BaseModel):
    log_file: str = "logs/article_extractor.log"
    log_level: str = "INFO"
    max_log_size: int = 10485760
    backup_count: int = 5

class AppConfig(BaseModel):
    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)
    cleaner: CleanerConfig = Field(default_factory=CleanerConfig)
    enricher: EnricherConfig = Field(default_factory=EnricherConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

class FeedSource(BaseModel):
    nombre: str
    urls: List[str]

class FeedsConfig(BaseModel):
    feeds: List[FeedSource]

class KeywordsConfig(BaseModel):
    keywords: List[str]

class ConfigManager:
    """Manages application configuration loading and validation."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.app_config: Optional[AppConfig] = None
        self.feeds_config: Optional[FeedsConfig] = None
        self.keywords_config: Optional[KeywordsConfig] = None

    def load_all(self) -> None:
        """Loads all configuration files."""
        self.load_app_config()
        self.load_feeds_config()
        self.load_keywords_config()

    def load_app_config(self, filename: str = "extractor_config.yaml") -> AppConfig:
        path = self.config_dir / filename
        if not path.exists():
            logger.warning(f"Config file {path} not found. Using defaults.")
            self.app_config = AppConfig()
            return self.app_config
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self.app_config = AppConfig(**data)
            logger.info(f"Loaded app config from {path}")
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            self.app_config = AppConfig()
            
        return self.app_config

    def load_feeds_config(self, filename: str = "feeds.json") -> FeedsConfig:
        path = self.config_dir / filename
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.feeds_config = FeedsConfig(**data)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            # Return empty config rather than crashing
            self.feeds_config = FeedsConfig(feeds=[])
        return self.feeds_config

    def load_keywords_config(self, filename: str = "keywords.json") -> KeywordsConfig:
        path = self.config_dir / filename
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.keywords_config = KeywordsConfig(**data)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            self.keywords_config = KeywordsConfig(keywords=[])
        return self.keywords_config

# Global instance
config = ConfigManager()
