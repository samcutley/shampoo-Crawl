"""
Database configuration and session management
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/cybersec_intel.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    base_url TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    scraping_config TEXT, -- JSON config for scraping
                    last_scraped TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT,
                    summary TEXT,
                    content TEXT,
                    content_hash TEXT,
                    publication_date TIMESTAMP,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
                    analysis_attempts INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
            """)
            
            # AI Analysis results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    analysis_data TEXT NOT NULL, -- JSON data
                    confidence_score REAL,
                    processing_time_seconds REAL,
                    ai_model_used TEXT,
                    prompt_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # IOCs table for easier querying
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS iocs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    ioc_type TEXT NOT NULL, -- ip, domain, url, hash, email, etc.
                    ioc_value TEXT NOT NULL,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # CVEs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    cve_id TEXT NOT NULL,
                    description TEXT,
                    severity TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Threat actors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threat_actors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    actor_name TEXT NOT NULL,
                    motivation TEXT,
                    attribution_confidence TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Malware families table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS malware_families (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    family_name TEXT NOT NULL,
                    malware_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Industries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS industries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    industry_name TEXT NOT NULL,
                    impact_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Regions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS regions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    region_name TEXT NOT NULL,
                    impact_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            """)
            
            # Scraping jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    job_type TEXT NOT NULL, -- full_scrape, incremental, single_page
                    status TEXT DEFAULT 'pending', -- pending, running, completed, failed
                    pages_scraped INTEGER DEFAULT 0,
                    articles_found INTEGER DEFAULT 0,
                    articles_new INTEGER DEFAULT 0,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_analysis_status ON articles(analysis_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_iocs_type_value ON iocs(ioc_type, ioc_value)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cves_cve_id ON cves(cve_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_threat_actors_name ON threat_actors(actor_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_malware_families_name ON malware_families(family_name)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_insert(self, query: str, params: tuple = None):
        """Execute insert query and return last row id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid

# Global database instance
db_manager = DatabaseManager()