"""
Enhanced scraping service with parallel processing and error handling
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from ..core.config import settings
from ..core.logging_config import get_logger
from ..db.database import db_manager

logger = get_logger("scraping")

class ScrapingService:
    """Enhanced scraping service with parallel processing and error handling"""
    
    def __init__(self):
        self.max_concurrent = settings.scraping.max_concurrent_requests
        self.request_delay = settings.scraping.request_delay
        self.max_retries = settings.scraping.max_retries
        self.timeout = settings.scraping.timeout
        self.user_agent = settings.scraping.user_agent
        
        # Semaphore to limit concurrent requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def scrape_source(self, source_config: Dict) -> Dict:
        """
        Scrape a complete source with parallel processing
        
        Args:
            source_config: Source configuration dictionary
            
        Returns:
            Dictionary with scraping results and statistics
        """
        start_time = time.time()
        source_name = source_config.get("name", "Unknown")
        
        logger.info(
            "Starting source scraping",
            source_name=source_name,
            base_url=source_config.get("base_url")
        )
        
        # Create or get source record
        source_id = self._get_or_create_source(source_config)
        
        # Create scraping job record
        job_id = db_manager.execute_insert(
            """INSERT INTO scraping_jobs 
               (source_id, job_type, status, started_at) 
               VALUES (?, ?, ?, ?)""",
            (source_id, "full_scrape", "running", datetime.utcnow())
        )
        
        try:
            # Get scraping configuration
            scraping_config = source_config.get("scraping_config", {})
            max_pages = scraping_config.get("max_pages", settings.scraping.max_pages_per_source)
            
            # Scrape listing pages to get article URLs
            article_urls = await self._scrape_listing_pages(
                source_config, max_pages, job_id
            )
            
            logger.info(
                "Found articles for scraping",
                source_name=source_name,
                article_count=len(article_urls)
            )
            
            # Scrape article content in parallel
            results = await self._scrape_articles_parallel(
                article_urls, source_config, source_id, job_id
            )
            
            # Update job status
            processing_time = time.time() - start_time
            articles_new = sum(1 for r in results if r.get("is_new", False))
            
            db_manager.execute_query(
                """UPDATE scraping_jobs 
                   SET status = ?, completed_at = ?, pages_scraped = ?, 
                       articles_found = ?, articles_new = ?
                   WHERE id = ?""",
                ("completed", datetime.utcnow(), max_pages, len(results), articles_new, job_id)
            )
            
            logger.info(
                "Source scraping completed",
                source_name=source_name,
                processing_time=processing_time,
                articles_found=len(results),
                articles_new=articles_new
            )
            
            return {
                "source_name": source_name,
                "job_id": job_id,
                "articles_found": len(results),
                "articles_new": articles_new,
                "processing_time": processing_time,
                "results": results
            }
            
        except Exception as e:
            # Update job with error
            db_manager.execute_query(
                """UPDATE scraping_jobs 
                   SET status = ?, completed_at = ?, error_message = ?
                   WHERE id = ?""",
                ("failed", datetime.utcnow(), str(e), job_id)
            )
            
            logger.error(
                "Source scraping failed",
                source_name=source_name,
                error=str(e),
                job_id=job_id
            )
            raise
    
    async def _scrape_listing_pages(
        self, 
        source_config: Dict, 
        max_pages: int,
        job_id: int
    ) -> List[Dict]:
        """Scrape listing pages to get article URLs"""
        
        base_url = source_config["base_url"]
        scraping_config = source_config.get("scraping_config", {})
        listing_schema = scraping_config.get("listing_schema")
        
        if not listing_schema:
            raise ValueError("No listing schema configured for source")
        
        extraction_strategy = JsonCssExtractionStrategy(listing_schema, verbose=False)
        all_articles = []
        
        async with AsyncWebCrawler() as crawler:
            for page_num in range(1, max_pages + 1):
                try:
                    page_url = self._get_page_url(source_config, page_num)
                    
                    logger.debug(
                        "Scraping listing page",
                        page_url=page_url,
                        page_num=page_num
                    )
                    
                    async with self.semaphore:
                        result = await crawler.arun(
                            url=page_url,
                            config=CrawlerRunConfig(
                                cache_mode=CacheMode.BYPASS,
                                extraction_strategy=extraction_strategy,
                                target_elements=scraping_config.get("target_elements", []),
                                excluded_tags=["form", "header", "footer"],
                                excluded_selector=",".join(scraping_config.get("excluded_selectors", [])),
                                user_agent=self.user_agent,
                                timeout=self.timeout
                            )
                        )
                    
                    if result.extracted_content:
                        page_articles = json.loads(result.extracted_content)
                        if isinstance(page_articles, list):
                            # Add page metadata to each article
                            for article in page_articles:
                                article["source_page"] = page_num
                                article["scraped_at"] = datetime.utcnow().isoformat()
                            all_articles.extend(page_articles)
                        
                        logger.debug(
                            "Listing page scraped successfully",
                            page_url=page_url,
                            articles_found=len(page_articles) if isinstance(page_articles, list) else 0
                        )
                    else:
                        logger.warning(
                            "No content extracted from listing page",
                            page_url=page_url
                        )
                    
                    # Respect rate limiting
                    if self.request_delay > 0:
                        await asyncio.sleep(self.request_delay)
                        
                except Exception as e:
                    logger.error(
                        "Failed to scrape listing page",
                        page_url=page_url,
                        error=str(e)
                    )
                    continue
        
        return all_articles
    
    async def _scrape_articles_parallel(
        self,
        article_urls: List[Dict],
        source_config: Dict,
        source_id: int,
        job_id: int
    ) -> List[Dict]:
        """Scrape article content in parallel"""
        
        # Create semaphore for article scraping
        article_semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create tasks for parallel processing
        tasks = []
        for article_data in article_urls:
            task = self._scrape_single_article(
                article_data, source_config, source_id, article_semaphore
            )
            tasks.append(task)
        
        # Execute tasks with progress tracking
        results = []
        completed = 0
        
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
                completed += 1
                
                if completed % 10 == 0:  # Log progress every 10 articles
                    logger.info(
                        "Article scraping progress",
                        completed=completed,
                        total=len(tasks),
                        job_id=job_id
                    )
                    
            except Exception as e:
                logger.error(
                    "Article scraping task failed",
                    error=str(e),
                    job_id=job_id
                )
                results.append({"error": str(e)})
        
        return results
    
    async def _scrape_single_article(
        self,
        article_data: Dict,
        source_config: Dict,
        source_id: int,
        semaphore: asyncio.Semaphore
    ) -> Dict:
        """Scrape content from a single article"""
        
        article_url = article_data.get("article_url", "")
        if not article_url:
            return {"error": "No article URL provided"}
        
        # Make URL absolute
        base_url = source_config["base_url"]
        full_url = urljoin(base_url, article_url)
        
        try:
            async with semaphore:
                # Check if article already exists
                existing = db_manager.execute_query(
                    "SELECT id, content_hash FROM articles WHERE url = ?",
                    (full_url,)
                )
                
                # Get article content
                content = await self._fetch_article_content(full_url, source_config)
                
                if not content:
                    return {"url": full_url, "error": "No content extracted"}
                
                # Calculate content hash
                content_hash = hashlib.sha256(content.encode()).hexdigest()
                
                # Check if content has changed
                if existing and existing[0]["content_hash"] == content_hash:
                    logger.debug(
                        "Article content unchanged, skipping",
                        url=full_url
                    )
                    return {"url": full_url, "status": "unchanged", "is_new": False}
                
                # Prepare article data
                article_record = {
                    "source_id": source_id,
                    "url": full_url,
                    "title": article_data.get("title", ""),
                    "summary": article_data.get("summary", ""),
                    "content": content,
                    "content_hash": content_hash,
                    "publication_date": self._parse_date(article_data.get("date", "")),
                    "analysis_status": "pending"
                }
                
                # Insert or update article
                if existing:
                    # Update existing article
                    db_manager.execute_query(
                        """UPDATE articles 
                           SET title = ?, summary = ?, content = ?, content_hash = ?,
                               publication_date = ?, analysis_status = ?, updated_at = ?
                           WHERE id = ?""",
                        (
                            article_record["title"],
                            article_record["summary"], 
                            article_record["content"],
                            article_record["content_hash"],
                            article_record["publication_date"],
                            "pending",
                            datetime.utcnow(),
                            existing[0]["id"]
                        )
                    )
                    article_id = existing[0]["id"]
                    is_new = False
                else:
                    # Insert new article
                    article_id = db_manager.execute_insert(
                        """INSERT INTO articles 
                           (source_id, url, title, summary, content, content_hash, 
                            publication_date, analysis_status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            article_record["source_id"],
                            article_record["url"],
                            article_record["title"],
                            article_record["summary"],
                            article_record["content"],
                            article_record["content_hash"],
                            article_record["publication_date"],
                            article_record["analysis_status"]
                        )
                    )
                    is_new = True
                
                logger.debug(
                    "Article scraped successfully",
                    url=full_url,
                    article_id=article_id,
                    is_new=is_new,
                    content_length=len(content)
                )
                
                return {
                    "url": full_url,
                    "article_id": article_id,
                    "status": "success",
                    "is_new": is_new,
                    "content_length": len(content)
                }
                
        except Exception as e:
            logger.error(
                "Failed to scrape article",
                url=full_url,
                error=str(e)
            )
            return {"url": full_url, "error": str(e)}
    
    async def _fetch_article_content(self, url: str, source_config: Dict) -> Optional[str]:
        """Fetch content from a single article URL"""
        
        scraping_config = source_config.get("scraping_config", {})
        article_schema = scraping_config.get("article_schema")
        
        if not article_schema:
            # Fallback to simple content extraction
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.DISABLED,
                        excluded_tags=["form", "header", "footer", "nav"],
                        user_agent=self.user_agent,
                        timeout=self.timeout
                    )
                )
                return result.markdown if result.markdown else None
        
        # Use configured schema
        extraction_strategy = JsonCssExtractionStrategy(article_schema, verbose=False)
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.DISABLED,
                    extraction_strategy=extraction_strategy,
                    excluded_selector=",".join(scraping_config.get("excluded_selectors", [])),
                    user_agent=self.user_agent,
                    timeout=self.timeout
                )
            )
            
            # Return markdown content or extracted content
            if result.markdown:
                return result.markdown
            elif result.extracted_content:
                try:
                    extracted = json.loads(result.extracted_content)
                    if isinstance(extracted, list) and extracted:
                        return extracted[0].get("post_content", "")
                    elif isinstance(extracted, dict):
                        return extracted.get("post_content", "")
                except json.JSONDecodeError:
                    pass
            
            return None
    
    def _get_page_url(self, source_config: Dict, page_num: int) -> str:
        """Generate page URL for given page number"""
        base_url = source_config["base_url"]
        scraping_config = source_config.get("scraping_config", {})
        
        if page_num == 1:
            return base_url
        
        # Use configured pattern or default
        pattern = scraping_config.get("page_url_pattern", "{base_url}/page/{page_num}/")
        return pattern.format(base_url=base_url, page_num=page_num)
    
    def _get_or_create_source(self, source_config: Dict) -> int:
        """Get or create source record in database"""
        name = source_config["name"]
        
        # Check if source exists
        existing = db_manager.execute_query(
            "SELECT id FROM sources WHERE name = ?",
            (name,)
        )
        
        if existing:
            return existing[0]["id"]
        
        # Create new source
        return db_manager.execute_insert(
            """INSERT INTO sources 
               (name, base_url, source_type, is_active, scraping_config)
               VALUES (?, ?, ?, ?, ?)""",
            (
                source_config["name"],
                source_config["base_url"],
                source_config.get("source_type", "unknown"),
                source_config.get("is_active", True),
                json.dumps(source_config.get("scraping_config", {}))
            )
        )
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        # Add date parsing logic here based on common formats
        # For now, return as-is
        return date_str

# Global scraping service instance
scraping_service = ScrapingService()