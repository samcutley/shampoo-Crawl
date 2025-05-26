#!/usr/bin/env python3
"""
Script to trigger manual crawling for a specific source
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Change to backend directory to ensure correct database path
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.scraping_service_simple import scraping_service
from app.db.database import db_manager
from app.core.logging_config import get_logger

logger = get_logger("manual_crawl")

async def trigger_crawl_for_source(source_id: int):
    """Trigger crawling for a specific source"""
    try:
        # Get source from database
        sources = db_manager.execute_query("""
            SELECT * FROM sources WHERE id = ? AND is_active = 1
        """, (source_id,))
        
        if not sources:
            logger.error(f"Source with ID {source_id} not found or inactive")
            return False
        
        source = dict(sources[0])
        logger.info(f"Starting crawl for source: {source['name']}")
        print(f"DEBUG: Source data: {source}")
        
        # Parse scraping config
        scraping_config = json.loads(source['scraping_config']) if source['scraping_config'] else {}
        
        # Create source config for scraping service
        source_config = {
            'name': source['name'],
            'base_url': source['base_url'],
            'source_type': source['source_type'],
            'scraping_config': scraping_config
        }
        print(f"DEBUG: Source config: {source_config}")
        
        # Trigger scraping
        result = await scraping_service.scrape_source(source_id, source_config)
        print(f"DEBUG: Scraping result: {result}")
        
        if result and result.get('status') == 'completed':
            articles_found = result.get('articles_found', 0)
            articles_new = result.get('articles_new', 0)
            logger.info(f"Successfully scraped {articles_found} articles ({articles_new} new) from {source['name']}")
            
            # Update last_scraped timestamp
            db_manager.execute_query("""
                UPDATE sources SET last_scraped = ? WHERE id = ?
            """, (datetime.utcnow().isoformat(), source_id))
            
            return True
        else:
            logger.warning(f"Scraping failed or no articles found for source: {source['name']}")
            logger.warning(f"Result: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to crawl source {source_id}: {e}")
        return False

async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python trigger_crawl.py <source_id>")
        sys.exit(1)
    
    try:
        source_id = int(sys.argv[1])
    except ValueError:
        print("Error: source_id must be an integer")
        sys.exit(1)
    
    # Database is already initialized when db_manager is imported
    
    # Trigger crawl
    success = await trigger_crawl_for_source(source_id)
    
    if success:
        print(f"✅ Successfully triggered crawl for source {source_id}")
    else:
        print(f"❌ Failed to trigger crawl for source {source_id}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())