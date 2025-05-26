"""
Scheduler for automated scraping and analysis tasks
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from ..core.config import settings
from ..core.logging_config import get_logger
from ..services.scraping_service_simple import scraping_service
from ..db.database import db_manager

logger = get_logger("scheduler")

class TaskScheduler:
    """Scheduler for automated scraping and analysis tasks"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        
    async def start(self):
        """Start the scheduler"""
        if not settings.scheduler.enabled:
            logger.info("Scheduler is disabled in configuration")
            return
        
        logger.info("Starting task scheduler")
        
        # Add scraping jobs
        self._add_scraping_jobs()
        
        # Add maintenance jobs
        self._add_maintenance_jobs()
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info("Task scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            logger.info("Stopping task scheduler")
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")
    
    def _add_scraping_jobs(self):
        """Add scraping jobs to scheduler"""
        
        # Schedule regular scraping for each active source
        for source in settings.sources:
            if source.is_active:
                job_id = f"scrape_{source.name.lower().replace(' ', '_')}"
                
                self.scheduler.add_job(
                    func=self._scrape_source_job,
                    trigger=IntervalTrigger(hours=settings.scheduler.scraping_interval_hours),
                    args=[source.dict()],
                    id=job_id,
                    name=f"Scrape {source.name}",
                    max_instances=1,
                    coalesce=True,
                    misfire_grace_time=3600  # 1 hour grace time
                )
                
                logger.info(
                    "Scheduled scraping job",
                    source_name=source.name,
                    interval_hours=settings.scheduler.scraping_interval_hours,
                    job_id=job_id
                )
        
        # Schedule analysis status check
        self.scheduler.add_job(
            func=self._check_analysis_status,
            trigger=IntervalTrigger(minutes=settings.scheduler.analysis_interval_minutes),
            id="check_analysis_status",
            name="Check Analysis Status",
            max_instances=1,
            coalesce=True
        )
    
    def _add_maintenance_jobs(self):
        """Add maintenance jobs to scheduler"""
        
        # Daily cleanup job
        self.scheduler.add_job(
            func=self._cleanup_job,
            trigger=CronTrigger(hour=2, minute=0),  # Run at 2 AM daily
            id="daily_cleanup",
            name="Daily Cleanup",
            max_instances=1,
            coalesce=True
        )
        
        # Weekly database backup
        self.scheduler.add_job(
            func=self._backup_database,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
            id="weekly_backup",
            name="Weekly Database Backup",
            max_instances=1,
            coalesce=True
        )
        
        # Monthly statistics report
        self.scheduler.add_job(
            func=self._generate_monthly_report,
            trigger=CronTrigger(day=1, hour=4, minute=0),  # First day of month, 4 AM
            id="monthly_report",
            name="Monthly Statistics Report",
            max_instances=1,
            coalesce=True
        )
    
    async def _scrape_source_job(self, source_config: Dict):
        """Job function for scraping a source"""
        source_name = source_config.get("name", "Unknown")
        
        try:
            logger.info(
                "Starting scheduled scraping job",
                source_name=source_name
            )
            
            result = await scraping_service.scrape_source(source_config)
            
            logger.info(
                "Scheduled scraping job completed",
                source_name=source_name,
                articles_found=result.get("articles_found", 0),
                articles_new=result.get("articles_new", 0),
                processing_time=result.get("processing_time", 0)
            )
            
        except Exception as e:
            logger.error(
                "Scheduled scraping job failed",
                source_name=source_name,
                error=str(e)
            )
    
    async def _check_analysis_status(self):
        """Check analysis status and log statistics"""
        try:
            # Get analysis statistics
            stats = db_manager.execute_query("""
                SELECT 
                    analysis_status,
                    COUNT(*) as count
                FROM articles 
                GROUP BY analysis_status
            """)
            
            status_counts = {row["analysis_status"]: row["count"] for row in stats}
            
            # Get failed analysis count (attempts >= 3)
            failed_attempts = db_manager.execute_query("""
                SELECT COUNT(*) as count
                FROM articles 
                WHERE analysis_attempts >= 3 AND analysis_status != 'completed'
            """)
            
            failed_count = failed_attempts[0]["count"] if failed_attempts else 0
            
            logger.info(
                "Analysis status check",
                pending=status_counts.get("pending", 0),
                processing=status_counts.get("processing", 0),
                completed=status_counts.get("completed", 0),
                failed=status_counts.get("failed", 0),
                failed_attempts=failed_count
            )
            
            # Reset failed articles with too many attempts
            if failed_count > 0:
                db_manager.execute_query("""
                    UPDATE articles 
                    SET analysis_status = 'failed'
                    WHERE analysis_attempts >= 3 AND analysis_status != 'completed'
                """)
                
                logger.warning(
                    "Reset articles with too many failed attempts",
                    count=failed_count
                )
            
        except Exception as e:
            logger.error(
                "Analysis status check failed",
                error=str(e)
            )
    
    async def _cleanup_job(self):
        """Daily cleanup job"""
        try:
            logger.info("Starting daily cleanup job")
            
            # Clean up old scraping jobs (older than 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            deleted_jobs = db_manager.execute_query("""
                DELETE FROM scraping_jobs 
                WHERE created_at < ? AND status IN ('completed', 'failed')
            """, (cutoff_date,))
            
            # Clean up old analysis data for deleted articles
            db_manager.execute_query("""
                DELETE FROM ai_analysis 
                WHERE article_id NOT IN (SELECT id FROM articles)
            """)
            
            db_manager.execute_query("""
                DELETE FROM iocs 
                WHERE article_id NOT IN (SELECT id FROM articles)
            """)
            
            # Update source last_scraped timestamps
            db_manager.execute_query("""
                UPDATE sources 
                SET last_scraped = (
                    SELECT MAX(created_at) 
                    FROM scraping_jobs 
                    WHERE source_id = sources.id AND status = 'completed'
                )
                WHERE id IN (
                    SELECT DISTINCT source_id 
                    FROM scraping_jobs 
                    WHERE status = 'completed'
                )
            """)
            
            logger.info("Daily cleanup job completed")
            
        except Exception as e:
            logger.error(
                "Daily cleanup job failed",
                error=str(e)
            )
    
    async def _backup_database(self):
        """Weekly database backup"""
        try:
            logger.info("Starting database backup")
            
            import shutil
            from pathlib import Path
            
            # Create backup directory
            backup_dir = Path("data/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"cybersec_intel_backup_{timestamp}.db"
            
            # Copy database file
            db_path = Path(settings.database.db_path)
            if db_path.exists():
                shutil.copy2(db_path, backup_file)
                
                # Clean up old backups (keep only last N backups)
                backup_files = sorted(backup_dir.glob("cybersec_intel_backup_*.db"))
                if len(backup_files) > settings.database.max_backup_files:
                    for old_backup in backup_files[:-settings.database.max_backup_files]:
                        old_backup.unlink()
                        logger.debug(f"Deleted old backup: {old_backup}")
                
                logger.info(
                    "Database backup completed",
                    backup_file=str(backup_file),
                    file_size=backup_file.stat().st_size
                )
            else:
                logger.warning("Database file not found for backup")
            
        except Exception as e:
            logger.error(
                "Database backup failed",
                error=str(e)
            )
    
    async def _generate_monthly_report(self):
        """Generate monthly statistics report"""
        try:
            logger.info("Generating monthly statistics report")
            
            # Get current month statistics
            current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Articles scraped this month
            articles_stats = db_manager.execute_query("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as analyzed_articles,
                    COUNT(CASE WHEN analysis_status = 'failed' THEN 1 END) as failed_articles
                FROM articles 
                WHERE created_at >= ?
            """, (current_month,))
            
            # Source statistics
            source_stats = db_manager.execute_query("""
                SELECT 
                    s.name,
                    COUNT(a.id) as articles_count,
                    COUNT(CASE WHEN a.analysis_status = 'completed' THEN 1 END) as analyzed_count
                FROM sources s
                LEFT JOIN articles a ON s.id = a.source_id AND a.created_at >= ?
                GROUP BY s.id, s.name
                ORDER BY articles_count DESC
            """, (current_month,))
            
            # IOC statistics
            ioc_stats = db_manager.execute_query("""
                SELECT 
                    ioc_type,
                    COUNT(*) as count
                FROM iocs i
                JOIN articles a ON i.article_id = a.id
                WHERE a.created_at >= ?
                GROUP BY ioc_type
                ORDER BY count DESC
            """, (current_month,))
            
            # Threat actor statistics
            threat_stats = db_manager.execute_query("""
                SELECT 
                    actor_name,
                    COUNT(*) as mentions
                FROM threat_actors ta
                JOIN articles a ON ta.article_id = a.id
                WHERE a.created_at >= ?
                GROUP BY actor_name
                ORDER BY mentions DESC
                LIMIT 10
            """, (current_month,))
            
            # Log the report
            report_data = {
                "month": current_month.strftime("%Y-%m"),
                "articles": dict(articles_stats[0]) if articles_stats else {},
                "sources": [dict(row) for row in source_stats],
                "iocs": [dict(row) for row in ioc_stats],
                "top_threat_actors": [dict(row) for row in threat_stats]
            }
            
            logger.info(
                "Monthly statistics report generated",
                **report_data
            )
            
        except Exception as e:
            logger.error(
                "Monthly report generation failed",
                error=str(e)
            )
    
    def get_job_status(self) -> List[Dict]:
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    async def trigger_scraping_job(self, source_name: str) -> bool:
        """Manually trigger a scraping job"""
        try:
            # Find the source in the database
            sources = db_manager.execute_query(
                "SELECT * FROM sources WHERE name = ? AND is_active = 1",
                (source_name,)
            )
            
            if not sources:
                logger.error(f"Source not found: {source_name}")
                return False
            
            source_db = dict(sources[0])
            
            # Parse scraping_config JSON if it exists
            scraping_config = {}
            if source_db.get("scraping_config"):
                try:
                    scraping_config = json.loads(source_db["scraping_config"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in scraping_config for source {source_name}")
            
            # Convert database source to config format
            source_config = {
                "name": source_db["name"],
                "base_url": source_db["base_url"],
                "source_type": source_db["source_type"],
                "is_active": source_db["is_active"],
                "scraping_config": scraping_config
            }
            
            # Run the scraping job
            await self._scrape_source_job(source_config)
            return True
            
        except Exception as e:
            logger.error(
                "Manual scraping job failed",
                source_name=source_name,
                error=str(e)
            )
            return False

# Global scheduler instance
scheduler = TaskScheduler()