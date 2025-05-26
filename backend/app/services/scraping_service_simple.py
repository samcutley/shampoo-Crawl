"""
Simplified scraping service using requests and BeautifulSoup
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup

from ..core.config import settings
from ..core.logging_config import get_logger
from ..db.database import db_manager

logger = get_logger("scraping")

class ScrapingService:
    """Simplified scraping service using requests and BeautifulSoup"""
    
    def __init__(self):
        self.max_workers = getattr(settings, 'MAX_WORKERS', 4)
        self.request_delay = getattr(settings, 'REQUEST_DELAY', 1.0)
        self.max_retries = getattr(settings, 'MAX_RETRIES', 3)
        self.timeout = getattr(settings, 'REQUEST_TIMEOUT', 30)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    async def scrape_source(self, source_id: int, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a single source and return results"""
        start_time = time.time()
        
        try:
            source_name = source_config.get('name', f'Source-{source_id}')
            base_url = source_config['base_url']
            source_type = source_config.get('source_type', 'website')
            
            logger.info(f"Starting scrape for source: {source_name}")
            
            if source_type == 'rss':
                results = await self._scrape_rss_feed(base_url, source_id)
            elif source_type == 'website':
                results = await self._scrape_website(base_url, source_id, source_config)
            else:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            processing_time = time.time() - start_time
            
            # Update source last_scraped timestamp
            self._update_source_timestamp(source_id)
            
            logger.info(f"Completed scrape for {source_name} in {processing_time:.2f}s. "
                       f"Found {results['articles_found']} articles, {results['articles_new']} new")
            
            return {
                'source_id': source_id,
                'source_name': source_name,
                'status': 'completed',
                'processing_time': processing_time,
                **results
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error scraping source {source_id}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'source_id': source_id,
                'status': 'failed',
                'error': error_msg,
                'processing_time': processing_time,
                'articles_found': 0,
                'articles_new': 0
            }
    
    async def _scrape_rss_feed(self, feed_url: str, source_id: int) -> Dict[str, Any]:
        """Scrape RSS feed for articles"""
        try:
            response = self.session.get(feed_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse RSS content
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            articles_found = len(items)
            articles_new = 0
            
            for item in items:
                article_data = self._parse_rss_item(item, source_id)
                if article_data and self._save_article(article_data):
                    articles_new += 1
            
            return {
                'articles_found': articles_found,
                'articles_new': articles_new
            }
        except Exception as e:
            logger.error(f"Error scraping RSS feed {feed_url}: {e}")
            raise
    
    async def _scrape_website(self, base_url: str, source_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape website for articles"""
        try:
            # Add a small delay to be respectful
            time.sleep(1)
            response = self.session.get(base_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article links based on configuration
            article_links = self._extract_article_links(soup, base_url, config)
            logger.info(f"DEBUG: Found {len(article_links)} article links")
            if article_links:
                logger.info(f"DEBUG: First few links: {article_links[:3]}")
            
            articles_found = len(article_links)
            articles_new = 0
            
            # Process first 10 articles for demo
            max_articles = getattr(settings, 'MAX_ARTICLES_PER_SOURCE', 10)
            for link in article_links[:max_articles]:
                try:
                    time.sleep(self.request_delay)  # Rate limiting
                    article_response = self.session.get(link, timeout=self.timeout)
                    article_response.raise_for_status()
                    
                    article_data = self._parse_article_content(article_response.text, link, source_id)
                    if article_data and self._save_article(article_data):
                        articles_new += 1
                except Exception as e:
                    logger.error(f"Error scraping article {link}: {e}")
                    continue
            
            return {
                'articles_found': articles_found,
                'articles_new': articles_new
            }
        except Exception as e:
            logger.error(f"Error scraping website {base_url}: {e}")
            raise
    
    def _parse_rss_item(self, item, source_id: int) -> Optional[Dict[str, Any]]:
        """Parse RSS item into article data"""
        try:
            title = item.find('title')
            link = item.find('link')
            description = item.find('description')
            pub_date = item.find('pubDate')
            
            if not title or not link:
                return None
            
            url = link.text.strip()
            content_hash = hashlib.md5(url.encode()).hexdigest()
            
            return {
                'source_id': source_id,
                'url': url,
                'title': title.text.strip() if title else '',
                'summary': description.text.strip() if description else '',
                'content': '',
                'content_hash': content_hash,
                'publication_date': self._parse_date(pub_date.text if pub_date else None),
                'scraped_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error parsing RSS item: {e}")
            return None
    
    def _parse_article_content(self, html: str, url: str, source_id: int) -> Optional[Dict[str, Any]]:
        """Parse article HTML content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else ''
            
            # Extract main content
            content_selectors = ['article', '.content', '.post-content', '.entry-content', 'main']
            content = ''
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    break
            
            if not content:
                # Fallback to body content
                body = soup.find('body')
                content = body.get_text().strip() if body else ''
            
            # Generate content hash
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Extract summary (first 500 chars)
            summary = content[:500] + '...' if len(content) > 500 else content
            
            return {
                'source_id': source_id,
                'url': url,
                'title': title,
                'summary': summary,
                'content': content,
                'content_hash': content_hash,
                'publication_date': datetime.utcnow(),
                'scraped_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error parsing article content from {url}: {e}")
            return None
    
    def _extract_article_links(self, soup: BeautifulSoup, base_url: str, config: Dict[str, Any]) -> List[str]:
        """Extract article links from page"""
        links = []
        
        # Get selectors from config or use defaults
        scraping_config = config.get('scraping_config', {})
        selectors = scraping_config.get('link_selectors', [
            'a[href*="/article/"]',
            'a[href*="/post/"]',
            'a[href*="/blog/"]',
            'a[href*="/news/"]',
            '.article-link a',
            '.post-title a',
            'h2 a',
            'h3 a'
        ])
        
        logger.info(f"DEBUG: Using selectors: {selectors}")
        
        for selector in selectors:
            elements = soup.select(selector)
            logger.info(f"DEBUG: Selector '{selector}' found {len(elements)} elements")
            for elem in elements:
                href = elem.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, base_url):
                        links.append(full_url)
                        logger.info(f"DEBUG: Added valid link: {full_url}")
        
        return list(set(links))  # Remove duplicates
    
    def _is_valid_article_url(self, url: str, base_url: str) -> bool:
        """Check if URL is a valid article URL"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Must be from same domain
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Skip common non-article paths
            skip_patterns = ['/tag/', '/category/', '/author/', '/page/', '/search/', 
                           '/login/', '/register/', '/contact/', '/about/']
            
            for pattern in skip_patterns:
                if pattern in url.lower():
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _save_article(self, article_data: Dict[str, Any]) -> bool:
        """Save article to database"""
        try:
            # Check if article already exists
            existing = db_manager.execute_query(
                "SELECT id FROM articles WHERE url = ?",
                (article_data['url'],)
            )
            
            if existing:
                return False  # Article already exists
            
            # Insert new article
            query = """
                INSERT INTO articles (source_id, url, title, summary, content, content_hash, 
                                    publication_date, scraped_at, analysis_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """
            
            params = (
                article_data['source_id'],
                article_data['url'],
                article_data['title'],
                article_data['summary'],
                article_data['content'],
                article_data['content_hash'],
                article_data['publication_date'],
                article_data['scraped_at']
            )
            
            db_manager.execute_insert(query, params)
            return True
            
        except Exception as e:
            logger.error(f"Error saving article {article_data.get('url', 'unknown')}: {e}")
            return False
    
    def _update_source_timestamp(self, source_id: int):
        """Update source last_scraped timestamp"""
        try:
            query = "UPDATE sources SET last_scraped = ?, updated_at = ? WHERE id = ?"
            params = (datetime.utcnow(), datetime.utcnow(), source_id)
            db_manager.execute_insert(query, params)
        except Exception as e:
            logger.error(f"Error updating source timestamp for {source_id}: {e}")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except Exception:
            return None

# Global service instance
scraping_service = ScrapingService()