#!/usr/bin/env python3
"""
Enhanced cybersecurity intelligence crawler
This is the main script to run the enhanced crawler with all features
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings, load_config
from app.core.logging_config import setup_logging, get_logger
from app.db.database import db_manager
from app.services.scraping_service import scraping_service
from app.services.ai_analysis import ai_service
from app.workers.analysis_worker import worker_manager
from app.workers.scheduler import scheduler

# Setup logging
setup_logging(
    log_level=settings.logging.level,
    log_dir=settings.logging.log_dir,
    max_file_size_mb=settings.logging.max_file_size_mb,
    backup_count=settings.logging.backup_count
)

logger = get_logger("crawler")

async def run_single_source_scraping(source_name: str):
    """Run scraping for a single source"""
    logger.info(f"Starting single source scraping: {source_name}")
    
    # Find source configuration
    source_config = None
    for source in settings.sources:
        if source.name == source_name:
            source_config = source.dict()
            break
    
    if not source_config:
        logger.error(f"Source not found: {source_name}")
        return
    
    try:
        result = await scraping_service.scrape_source(source_config)
        logger.info(
            "Single source scraping completed",
            source_name=source_name,
            articles_found=result.get("articles_found", 0),
            articles_new=result.get("articles_new", 0),
            processing_time=result.get("processing_time", 0)
        )
    except Exception as e:
        logger.error(f"Single source scraping failed: {e}")

async def run_all_sources_scraping():
    """Run scraping for all active sources"""
    logger.info("Starting scraping for all active sources")
    
    active_sources = [source for source in settings.sources if source.is_active]
    
    if not active_sources:
        logger.warning("No active sources found")
        return
    
    # Run scraping for all sources in parallel
    tasks = []
    for source in active_sources:
        task = scraping_service.scrape_source(source.dict())
        tasks.append(task)
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_articles = 0
        total_new = 0
        
        for i, result in enumerate(results):
            source_name = active_sources[i].name
            
            if isinstance(result, Exception):
                logger.error(f"Scraping failed for {source_name}: {result}")
            else:
                articles_found = result.get("articles_found", 0)
                articles_new = result.get("articles_new", 0)
                total_articles += articles_found
                total_new += articles_new
                
                logger.info(
                    "Source scraping completed",
                    source_name=source_name,
                    articles_found=articles_found,
                    articles_new=articles_new
                )
        
        logger.info(
            "All sources scraping completed",
            total_articles=total_articles,
            total_new=total_new
        )
        
    except Exception as e:
        logger.error(f"All sources scraping failed: {e}")

async def run_analysis_only():
    """Run analysis on pending articles"""
    logger.info("Starting analysis of pending articles")
    
    # Test AI service connection
    if not await ai_service.test_connection():
        logger.error("AI service connection failed - cannot run analysis")
        return
    
    # Get pending articles count
    pending = db_manager.execute_query("""
        SELECT COUNT(*) as count 
        FROM articles 
        WHERE analysis_status = 'pending'
    """)
    
    pending_count = pending[0]["count"] if pending else 0
    logger.info(f"Found {pending_count} articles pending analysis")
    
    if pending_count == 0:
        logger.info("No articles pending analysis")
        return
    
    # Start analysis workers temporarily
    try:
        await worker_manager.start()
        
        # Wait for analysis to complete or timeout
        timeout = 3600  # 1 hour timeout
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check remaining pending articles
            remaining = db_manager.execute_query("""
                SELECT COUNT(*) as count 
                FROM articles 
                WHERE analysis_status = 'pending'
            """)
            
            remaining_count = remaining[0]["count"] if remaining else 0
            
            if remaining_count == 0:
                logger.info("All articles analyzed successfully")
                break
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.warning(f"Analysis timeout reached, {remaining_count} articles still pending")
                break
            
            # Wait before checking again
            await asyncio.sleep(30)
        
        # Get final stats
        stats = worker_manager.get_stats()
        logger.info(
            "Analysis completed",
            total_processed=stats["total_processed"],
            total_errors=stats["total_errors"]
        )
        
    finally:
        await worker_manager.stop()

async def run_full_pipeline():
    """Run the full scraping and analysis pipeline"""
    logger.info("Starting full pipeline (scraping + analysis)")
    
    # Test AI service connection
    if not await ai_service.test_connection():
        logger.error("AI service connection failed - analysis will be disabled")
    
    # Start analysis workers
    await worker_manager.start()
    
    try:
        # Run scraping for all sources
        await run_all_sources_scraping()
        
        # Wait a bit for articles to be inserted
        await asyncio.sleep(5)
        
        # Check if there are articles to analyze
        pending = db_manager.execute_query("""
            SELECT COUNT(*) as count 
            FROM articles 
            WHERE analysis_status = 'pending'
        """)
        
        pending_count = pending[0]["count"] if pending else 0
        
        if pending_count > 0:
            logger.info(f"Waiting for analysis of {pending_count} articles...")
            
            # Wait for analysis to complete (with timeout)
            timeout = 7200  # 2 hours timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                remaining = db_manager.execute_query("""
                    SELECT COUNT(*) as count 
                    FROM articles 
                    WHERE analysis_status = 'pending'
                """)
                
                remaining_count = remaining[0]["count"] if remaining else 0
                
                if remaining_count == 0:
                    logger.info("All articles analyzed successfully")
                    break
                
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Analysis timeout reached, {remaining_count} articles still pending")
                    break
                
                # Log progress every 5 minutes
                if int(elapsed) % 300 == 0:
                    stats = worker_manager.get_stats()
                    logger.info(
                        "Analysis progress",
                        remaining=remaining_count,
                        processed=stats["total_processed"],
                        errors=stats["total_errors"]
                    )
                
                await asyncio.sleep(30)
        
        # Final stats
        final_stats = worker_manager.get_stats()
        logger.info(
            "Full pipeline completed",
            total_processed=final_stats["total_processed"],
            total_errors=final_stats["total_errors"]
        )
        
    finally:
        await worker_manager.stop()

async def run_daemon_mode():
    """Run in daemon mode with scheduler"""
    logger.info("Starting daemon mode with scheduler")
    
    # Test AI service connection
    if not await ai_service.test_connection():
        logger.warning("AI service connection failed - analysis may be limited")
    
    # Start all services
    await worker_manager.start()
    await scheduler.start()
    
    try:
        logger.info("Daemon mode started - press Ctrl+C to stop")
        
        # Run indefinitely
        while True:
            await asyncio.sleep(60)
            
            # Log periodic status
            stats = worker_manager.get_stats()
            logger.info(
                "Daemon status",
                workers_running=sum(1 for w in stats["workers"] if w["is_running"]),
                total_processed=stats["total_processed"],
                total_errors=stats["total_errors"]
            )
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    
    finally:
        await scheduler.stop()
        await worker_manager.stop()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Cybersecurity Intelligence Crawler")
    parser.add_argument(
        "mode",
        choices=["scrape", "analyze", "full", "daemon", "source"],
        help="Operation mode"
    )
    parser.add_argument(
        "--source",
        help="Source name (required for 'source' mode)"
    )
    parser.add_argument(
        "--config",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    # Load configuration if provided
    if args.config:
        global settings
        settings = load_config(args.config)
    
    # Validate arguments
    if args.mode == "source" and not args.source:
        parser.error("--source is required when mode is 'source'")
    
    # Run the appropriate mode
    try:
        if args.mode == "scrape":
            asyncio.run(run_all_sources_scraping())
        elif args.mode == "analyze":
            asyncio.run(run_analysis_only())
        elif args.mode == "full":
            asyncio.run(run_full_pipeline())
        elif args.mode == "daemon":
            asyncio.run(run_daemon_mode())
        elif args.mode == "source":
            asyncio.run(run_single_source_scraping(args.source))
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()