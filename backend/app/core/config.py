"""
Configuration management for the cybersecurity intelligence platform
"""

import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path
import json

class LlamaServerConfig(BaseModel):
    base_url: str = Field(default="http://127.0.0.1:8081", description="LLaMA server base URL")
    api_key: str = Field(default="fdghjkljhgffhfjklkjhfdgjkhgf", description="API key")
    model_name: str = Field(default="qwen38bQ4", description="Model name")
    timeout: int = Field(default=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

class ScrapingConfig(BaseModel):
    max_concurrent_requests: int = Field(default=5, description="Max concurrent scraping requests")
    request_delay: float = Field(default=1.0, description="Delay between requests in seconds")
    max_pages_per_source: int = Field(default=10, description="Max pages to scrape per source")
    user_agent: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", description="User agent string")
    timeout: int = Field(default=30, description="Request timeout")
    max_retries: int = Field(default=3, description="Max retry attempts")

class DatabaseConfig(BaseModel):
    db_path: str = Field(default="data/cybersec_intel.db", description="SQLite database path")
    backup_interval_hours: int = Field(default=24, description="Database backup interval")
    max_backup_files: int = Field(default=7, description="Maximum backup files to keep")

class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", description="Logging level")
    log_dir: str = Field(default="logs", description="Log directory")
    max_file_size_mb: int = Field(default=100, description="Max log file size in MB")
    backup_count: int = Field(default=5, description="Number of backup log files")

class WorkerConfig(BaseModel):
    max_workers: int = Field(default=4, description="Maximum number of worker processes")
    queue_size: int = Field(default=1000, description="Maximum queue size")
    worker_timeout: int = Field(default=600, description="Worker timeout in seconds")

class SchedulerConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable scheduled scraping")
    scraping_interval_hours: int = Field(default=6, description="Scraping interval in hours")
    analysis_interval_minutes: int = Field(default=30, description="Analysis interval in minutes")
    cleanup_interval_days: int = Field(default=7, description="Cleanup interval in days")

class SourceConfig(BaseModel):
    name: str
    base_url: str
    source_type: str  # "news", "blog", "advisory", "research"
    is_active: bool = True
    scraping_config: Dict = {}

class Config(BaseModel):
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=12000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Component configurations
    llama_server: LlamaServerConfig = Field(default_factory=LlamaServerConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    worker: WorkerConfig = Field(default_factory=WorkerConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    
    # Sources configuration
    sources: List[SourceConfig] = Field(default_factory=list)
    
    # Analysis configuration
    analysis_prompt_version: str = Field(default="cybersec_intel_extractor_v2.0")
    min_content_length: int = Field(default=500, description="Minimum content length for analysis")
    max_content_length: int = Field(default=50000, description="Maximum content length for analysis")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Default sources configuration
DEFAULT_SOURCES = [
    {
        "name": "BleepingComputer Security",
        "base_url": "https://www.bleepingcomputer.com/news/security/",
        "source_type": "news",
        "is_active": True,
        "scraping_config": {
            "listing_schema": {
                "name": "News Items",
                "baseSelector": "#bc-home-news-main-wrap > li",
                "fields": [
                    {
                        "name": "article_url",
                        "selector": ".bc_latest_news_img a",
                        "type": "attribute",
                        "attribute": "href",
                        "default": ""
                    },
                    {
                        "name": "categories",
                        "selector": ".bc_latest_news_category span.bc_news_cat a",
                        "type": "text",
                        "default": ""
                    },
                    {
                        "name": "title",
                        "selector": ".bc_latest_news_text h4 a",
                        "type": "text",
                        "default": ""
                    },
                    {
                        "name": "summary",
                        "selector": ".bc_latest_news_text > p",
                        "type": "text",
                        "default": ""
                    },
                    {
                        "name": "date",
                        "selector": ".bc_news_date",
                        "type": "text",
                        "default": ""
                    },
                    {
                        "name": "time",
                        "selector": ".bc_news_time",
                        "type": "text",
                        "default": ""
                    }
                ]
            },
            "article_schema": {
                "name": "Article Content",
                "baseSelector": "div.article_section",
                "fields": [
                    {
                        "name": "post_content",
                        "selector": ".articleBody",
                        "type": "text",
                        "default": ""
                    }
                ]
            },
            "page_url_pattern": "{base_url}/page/{page_num}/",
            "target_elements": ["div.bc_latest_news"],
            "excluded_selectors": ["div.ia_ad", ".cz-related-article-wrapp", ".cz-news-story-title-section"],
            "max_pages": 5
        }
    },
    {
        "name": "KrebsOnSecurity",
        "base_url": "https://krebsonsecurity.com",
        "source_type": "blog",
        "is_active": True,
        "scraping_config": {
            "listing_schema": {
                "name": "Blog Posts",
                "baseSelector": "article.post",
                "fields": [
                    {
                        "name": "article_url",
                        "selector": "h2.entry-title a",
                        "type": "attribute",
                        "attribute": "href",
                        "default": ""
                    },
                    {
                        "name": "title",
                        "selector": "h2.entry-title a",
                        "type": "text",
                        "default": ""
                    },
                    {
                        "name": "summary",
                        "selector": ".entry-content p:first-of-type",
                        "type": "text",
                        "default": ""
                    },
                    {
                        "name": "date",
                        "selector": ".entry-date",
                        "type": "text",
                        "default": ""
                    }
                ]
            },
            "article_schema": {
                "name": "Article Content",
                "baseSelector": "article.post",
                "fields": [
                    {
                        "name": "post_content",
                        "selector": ".entry-content",
                        "type": "text",
                        "default": ""
                    }
                ]
            },
            "page_url_pattern": "{base_url}/page/{page_num}/",
            "max_pages": 3
        }
    }
]

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file or environment variables"""
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return Config(**config_data)
    
    # Load from environment or use defaults
    config = Config()
    
    # Add default sources if none configured
    if not config.sources:
        config.sources = [SourceConfig(**source) for source in DEFAULT_SOURCES]
    
    return config

def save_config(config: Config, config_path: str = "config/config.json"):
    """Save configuration to file"""
    config_dir = Path(config_path).parent
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config.dict(), f, indent=2)

# Global configuration instance
settings = load_config()