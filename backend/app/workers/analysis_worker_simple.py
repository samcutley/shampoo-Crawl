"""
Simplified worker for processing AI analysis tasks
"""

import asyncio
import time
from typing import Dict, List
from datetime import datetime

from ..core.config import settings
from ..core.logging_config import get_logger
from ..db.database import db_manager
from ..services.ai_analysis_simple import ai_analysis_service

logger = get_logger("analysis_worker")

class AnalysisWorker:
    """Simplified worker for processing AI analysis tasks"""
    
    def __init__(self, worker_id: str = "worker-1"):
        self.worker_id = worker_id
        self.is_running = False
        self.processed_count = 0
        self.error_count = 0
        self.batch_size = getattr(settings, 'ANALYSIS_BATCH_SIZE', 5)
        self.check_interval = getattr(settings, 'ANALYSIS_CHECK_INTERVAL', 30)
    
    async def start(self):
        """Start the analysis worker"""
        self.is_running = True
        logger.info(f"Analysis worker {self.worker_id} started")
        
        while self.is_running:
            try:
                # Get pending articles
                articles = self._get_pending_articles(self.batch_size)
                
                if articles:
                    logger.info(f"Processing {len(articles)} articles")
                    
                    for article in articles:
                        if not self.is_running:
                            break
                        
                        await self._process_article(article)
                        await asyncio.sleep(1)  # Small delay between articles
                else:
                    # No articles to process, wait
                    await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Analysis worker error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def stop(self):
        """Stop the analysis worker"""
        self.is_running = False
        logger.info(f"Analysis worker {self.worker_id} stopped. Processed: {self.processed_count}, Errors: {self.error_count}")
    
    def _get_pending_articles(self, limit: int = 10) -> List[Dict]:
        """Get articles pending analysis"""
        try:
            return db_manager.execute_query(
                """SELECT id, url, title, summary, content, publication_date
                   FROM articles 
                   WHERE analysis_status = 'pending'
                   ORDER BY created_at ASC 
                   LIMIT ?""",
                (limit,)
            )
        except Exception as e:
            logger.error(f"Error getting pending articles: {e}")
            return []
    
    async def _process_article(self, article: Dict):
        """Process a single article for analysis"""
        article_id = article["id"]
        url = article["url"]
        
        try:
            logger.info(f"Starting analysis for article {article_id}")
            
            # Perform AI analysis
            analysis_result = await ai_analysis_service.analyze_article(article_id)
            
            if analysis_result.get('status') == 'completed':
                self.processed_count += 1
                logger.info(f"Article {article_id} analysis completed")
            else:
                self.error_count += 1
                logger.error(f"Article {article_id} analysis failed: {analysis_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing article {article_id}: {e}")
            
            # Update article status to failed
            try:
                db_manager.execute_insert(
                    "UPDATE articles SET analysis_status = 'failed' WHERE id = ?",
                    (article_id,)
                )
            except Exception as update_error:
                logger.error(f"Error updating article status: {update_error}")

# Global worker instance
analysis_worker = AnalysisWorker()