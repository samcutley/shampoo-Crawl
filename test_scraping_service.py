#!/usr/bin/env python3

import asyncio
import sys
import os
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.scraping_service_simple import ScrapingService

async def test_scraping_service():
    """Test the scraping service directly"""
    
    service = ScrapingService()
    
    source_config = {
        'name': 'BleepingComputer Security News',
        'base_url': 'https://www.bleepingcomputer.com/news/security/',
        'source_type': 'website',
        'scraping_config': {
            'selectors': {
                'title': 'h1, .article-title, .post-title',
                'content': '.article-content, .post-content, .entry-content',
                'summary': '.article-summary, .excerpt, .post-excerpt',
                'author': '.author, .byline',
                'publication_date': '.date, .published, time'
            },
            'link_selectors': [
                'a[href*="/news/security/"]',
                'a[href*="/news/"]',
                '.nmic'
            ],
            'max_articles': 50,
            'follow_links': True
        }
    }
    
    print("Testing scraping service...")
    print(f"Config: {json.dumps(source_config, indent=2)}")
    
    try:
        result = await service.scrape_source(1, source_config)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scraping_service())