"""
Worker for processing AI analysis tasks
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

from ..core.config import settings
from ..core.logging_config import get_logger
from ..db.database import db_manager
from ..services.ai_analysis import ai_service

logger = get_logger("analysis_worker")

class AnalysisWorker:
    """Worker for processing AI analysis tasks"""
    
    def __init__(self, worker_id: int = 0):
        self.worker_id = worker_id
        self.is_running = False
        self.processed_count = 0
        self.error_count = 0
        
    async def start(self):
        """Start the analysis worker"""
        self.is_running = True
        logger.info(
            "Analysis worker started",
            worker_id=self.worker_id
        )
        
        while self.is_running:
            try:
                # Get pending articles for analysis
                articles = self._get_pending_articles()
                
                if not articles:
                    # No pending articles, wait before checking again
                    await asyncio.sleep(30)
                    continue
                
                # Process articles
                for article in articles:
                    if not self.is_running:
                        break
                    
                    await self._process_article(article)
                    
                    # Small delay between articles
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(
                    "Analysis worker error",
                    worker_id=self.worker_id,
                    error=str(e)
                )
                await asyncio.sleep(60)  # Wait longer on error
    
    async def stop(self):
        """Stop the analysis worker"""
        self.is_running = False
        logger.info(
            "Analysis worker stopped",
            worker_id=self.worker_id,
            processed_count=self.processed_count,
            error_count=self.error_count
        )
    
    def _get_pending_articles(self, limit: int = 10) -> List[Dict]:
        """Get articles pending analysis"""
        return db_manager.execute_query(
            """SELECT id, url, title, summary, content, publication_date, analysis_attempts
               FROM articles 
               WHERE analysis_status = 'pending' 
               AND analysis_attempts < 3
               ORDER BY created_at ASC 
               LIMIT ?""",
            (limit,)
        )
    
    async def _process_article(self, article: Dict):
        """Process a single article for analysis"""
        article_id = article["id"]
        url = article["url"]
        
        try:
            # Update status to processing
            db_manager.execute_query(
                """UPDATE articles 
                   SET analysis_status = 'processing', analysis_attempts = analysis_attempts + 1
                   WHERE id = ?""",
                (article_id,)
            )
            
            logger.info(
                "Starting article analysis",
                article_id=article_id,
                url=url,
                worker_id=self.worker_id
            )
            
            # Prepare metadata
            metadata = {
                "title": article.get("title"),
                "publication_date": article.get("publication_date"),
                "source_domain": self._extract_domain(url)
            }
            
            # Perform AI analysis
            analysis_result, error_message = await ai_service.analyze_content(
                content=article["content"],
                source_url=url,
                article_metadata=metadata
            )
            
            if analysis_result:
                # Save analysis result
                await self._save_analysis_result(article_id, analysis_result)
                
                # Update article status
                db_manager.execute_query(
                    "UPDATE articles SET analysis_status = 'completed' WHERE id = ?",
                    (article_id,)
                )
                
                self.processed_count += 1
                
                logger.info(
                    "Article analysis completed",
                    article_id=article_id,
                    url=url,
                    worker_id=self.worker_id
                )
                
            else:
                # Analysis failed
                db_manager.execute_query(
                    "UPDATE articles SET analysis_status = 'failed' WHERE id = ?",
                    (article_id,)
                )
                
                self.error_count += 1
                
                logger.error(
                    "Article analysis failed",
                    article_id=article_id,
                    url=url,
                    error=error_message,
                    worker_id=self.worker_id
                )
                
        except Exception as e:
            # Update status to failed
            db_manager.execute_query(
                "UPDATE articles SET analysis_status = 'failed' WHERE id = ?",
                (article_id,)
            )
            
            self.error_count += 1
            
            logger.error(
                "Article processing error",
                article_id=article_id,
                url=url,
                error=str(e),
                worker_id=self.worker_id
            )
    
    async def _save_analysis_result(self, article_id: int, analysis_result: Dict):
        """Save analysis result to database"""
        
        # Save main analysis record
        analysis_id = db_manager.execute_insert(
            """INSERT INTO ai_analysis 
               (article_id, analysis_data, confidence_score, processing_time_seconds, 
                ai_model_used, prompt_version)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                article_id,
                json.dumps(analysis_result),
                self._extract_confidence_score(analysis_result),
                analysis_result.get("ai_analysis_metadata", {}).get("processing_time_seconds"),
                analysis_result.get("ai_analysis_metadata", {}).get("ai_model_used"),
                analysis_result.get("ai_analysis_metadata", {}).get("prompt_version")
            )
        )
        
        # Extract and save IOCs
        await self._save_iocs(article_id, analysis_result.get("indicators_of_compromise", {}))
        
        # Extract and save CVEs
        await self._save_cves(article_id, analysis_result.get("vulnerabilities_and_malware", {}))
        
        # Extract and save threat actors
        await self._save_threat_actors(article_id, analysis_result.get("threat_actor_and_ttps", {}))
        
        # Extract and save malware families
        await self._save_malware_families(article_id, analysis_result.get("vulnerabilities_and_malware", {}))
        
        # Extract and save industries
        await self._save_industries(article_id, analysis_result.get("incident_event_details", {}))
        
        # Extract and save regions
        await self._save_regions(article_id, analysis_result.get("incident_event_details", {}))
    
    async def _save_iocs(self, article_id: int, iocs: Dict):
        """Save IOCs to database"""
        ioc_data = []
        
        # IP addresses
        for ip in iocs.get("ips", []):
            ioc_data.append((article_id, "ip", ip, 0.8))
        
        # Domains
        for domain in iocs.get("domains", []):
            ioc_data.append((article_id, "domain", domain, 0.8))
        
        # URLs
        for url in iocs.get("urls", []):
            ioc_data.append((article_id, "url", url, 0.8))
        
        # Hashes
        hashes = iocs.get("hashes", {})
        for hash_type in ["md5", "sha1", "sha256", "sha512"]:
            for hash_value in hashes.get(hash_type, []):
                ioc_data.append((article_id, f"hash_{hash_type}", hash_value, 0.9))
        
        # Email addresses
        for email in iocs.get("email_addresses", []):
            ioc_data.append((article_id, "email", email, 0.7))
        
        # File names
        for filename in iocs.get("file_names", []):
            ioc_data.append((article_id, "filename", filename, 0.6))
        
        # Registry keys
        for regkey in iocs.get("registry_keys", []):
            ioc_data.append((article_id, "registry_key", regkey, 0.7))
        
        # Mutexes
        for mutex in iocs.get("mutexes", []):
            ioc_data.append((article_id, "mutex", mutex, 0.8))
        
        # Batch insert IOCs
        if ioc_data:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """INSERT INTO iocs (article_id, ioc_type, ioc_value, confidence_score)
                       VALUES (?, ?, ?, ?)""",
                    ioc_data
                )
                conn.commit()
    
    async def _save_cves(self, article_id: int, vuln_data: Dict):
        """Save CVEs to database"""
        cves = vuln_data.get("cve_ids_mentioned", [])
        descriptions = vuln_data.get("vulnerabilities_exploited_desc", [])
        
        cve_data = []
        for i, cve_id in enumerate(cves):
            description = descriptions[i] if i < len(descriptions) else ""
            cve_data.append((article_id, cve_id, description, ""))
        
        if cve_data:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """INSERT INTO cves (article_id, cve_id, description, severity)
                       VALUES (?, ?, ?, ?)""",
                    cve_data
                )
                conn.commit()
    
    async def _save_threat_actors(self, article_id: int, ttp_data: Dict):
        """Save threat actors to database"""
        actors = ttp_data.get("attacker_group_suspected", [])
        motivation = ttp_data.get("attacker_motivation", "")
        confidence = ttp_data.get("attribution_confidence", "")
        
        actor_data = []
        for actor in actors:
            actor_data.append((article_id, actor, motivation, confidence))
        
        if actor_data:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """INSERT INTO threat_actors (article_id, actor_name, motivation, attribution_confidence)
                       VALUES (?, ?, ?, ?)""",
                    actor_data
                )
                conn.commit()
    
    async def _save_malware_families(self, article_id: int, vuln_data: Dict):
        """Save malware families to database"""
        families = vuln_data.get("malware_families_involved", [])
        
        family_data = []
        for family in families:
            family_data.append((article_id, family, ""))
        
        if family_data:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """INSERT INTO malware_families (article_id, family_name, malware_type)
                       VALUES (?, ?, ?)""",
                    family_data
                )
                conn.commit()
    
    async def _save_industries(self, article_id: int, incident_data: Dict):
        """Save industries to database"""
        industries = incident_data.get("industry_targeted", [])
        severity = incident_data.get("severity_assessment", "")
        
        industry_data = []
        for industry in industries:
            industry_data.append((article_id, industry, severity))
        
        if industry_data:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """INSERT INTO industries (article_id, industry_name, impact_level)
                       VALUES (?, ?, ?)""",
                    industry_data
                )
                conn.commit()
    
    async def _save_regions(self, article_id: int, incident_data: Dict):
        """Save regions to database"""
        regions = incident_data.get("regions_impacted", [])
        severity = incident_data.get("severity_assessment", "")
        
        region_data = []
        for region in regions:
            region_data.append((article_id, region, severity))
        
        if region_data:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """INSERT INTO regions (article_id, region_name, impact_level)
                       VALUES (?, ?, ?)""",
                    region_data
                )
                conn.commit()
    
    def _extract_confidence_score(self, analysis_result: Dict) -> Optional[float]:
        """Extract confidence score from analysis result"""
        confidence = analysis_result.get("ai_analysis_metadata", {}).get("confidence_in_analysis")
        if confidence == "High":
            return 0.9
        elif confidence == "Medium":
            return 0.7
        elif confidence == "Low":
            return 0.5
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc

class AnalysisWorkerManager:
    """Manager for multiple analysis workers"""
    
    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or settings.worker.max_workers
        self.workers = []
        self.tasks = []
    
    async def start(self):
        """Start all analysis workers"""
        logger.info(
            "Starting analysis worker manager",
            num_workers=self.num_workers
        )
        
        for i in range(self.num_workers):
            worker = AnalysisWorker(worker_id=i)
            self.workers.append(worker)
            
            task = asyncio.create_task(worker.start())
            self.tasks.append(task)
        
        logger.info("All analysis workers started")
    
    async def stop(self):
        """Stop all analysis workers"""
        logger.info("Stopping analysis workers")
        
        # Stop all workers
        for worker in self.workers:
            await worker.stop()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("All analysis workers stopped")
    
    def get_stats(self) -> Dict:
        """Get worker statistics"""
        total_processed = sum(worker.processed_count for worker in self.workers)
        total_errors = sum(worker.error_count for worker in self.workers)
        
        return {
            "num_workers": self.num_workers,
            "total_processed": total_processed,
            "total_errors": total_errors,
            "workers": [
                {
                    "worker_id": worker.worker_id,
                    "processed_count": worker.processed_count,
                    "error_count": worker.error_count,
                    "is_running": worker.is_running
                }
                for worker in self.workers
            ]
        }

# Global worker manager instance
worker_manager = AnalysisWorkerManager()