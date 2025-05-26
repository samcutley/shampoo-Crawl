"""
API routes for the cybersecurity intelligence platform
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel

from ..core.config import settings
from ..core.logging_config import get_logger
from ..db.database import db_manager
from ..services.scraping_service import scraping_service
from ..workers.scheduler import scheduler
from ..workers.analysis_worker import worker_manager

logger = get_logger("api")
router = APIRouter()

# Pydantic models for API
class SourceCreate(BaseModel):
    name: str
    base_url: str
    source_type: str
    is_active: bool = True
    scraping_config: Dict = {}

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    source_type: Optional[str] = None
    is_active: Optional[bool] = None
    scraping_config: Optional[Dict] = None

class ScrapingJobTrigger(BaseModel):
    source_name: str
    job_type: str = "manual"

# Sources endpoints
@router.get("/sources")
async def get_sources():
    """Get all sources"""
    try:
        sources = db_manager.execute_query("""
            SELECT s.*, 
                   COUNT(a.id) as article_count,
                   MAX(a.created_at) as last_article_date
            FROM sources s
            LEFT JOIN articles a ON s.id = a.source_id
            GROUP BY s.id
            ORDER BY s.name
        """)
        
        return {"sources": [dict(source) for source in sources]}
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sources")
async def create_source(source: SourceCreate):
    """Create a new source"""
    try:
        source_id = db_manager.execute_insert("""
            INSERT INTO sources (name, base_url, source_type, is_active, scraping_config)
            VALUES (?, ?, ?, ?, ?)
        """, (
            source.name,
            source.base_url,
            source.source_type,
            source.is_active,
            json.dumps(source.scraping_config)
        ))
        
        logger.info(f"Created new source: {source.name}")
        return {"source_id": source_id, "message": "Source created successfully"}
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sources/{source_id}")
async def update_source(source_id: int, source: SourceUpdate):
    """Update a source"""
    try:
        # Build update query dynamically
        updates = []
        params = []
        
        if source.name is not None:
            updates.append("name = ?")
            params.append(source.name)
        if source.base_url is not None:
            updates.append("base_url = ?")
            params.append(source.base_url)
        if source.source_type is not None:
            updates.append("source_type = ?")
            params.append(source.source_type)
        if source.is_active is not None:
            updates.append("is_active = ?")
            params.append(source.is_active)
        if source.scraping_config is not None:
            updates.append("scraping_config = ?")
            params.append(json.dumps(source.scraping_config))
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.append(source_id)
        
        query = f"UPDATE sources SET {', '.join(updates)} WHERE id = ?"
        db_manager.execute_query(query, tuple(params))
        
        logger.info(f"Updated source: {source_id}")
        return {"message": "Source updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sources/{source_id}")
async def delete_source(source_id: int):
    """Delete a source"""
    try:
        db_manager.execute_query("DELETE FROM sources WHERE id = ?", (source_id,))
        logger.info(f"Deleted source: {source_id}")
        return {"message": "Source deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Articles endpoints
@router.get("/articles")
async def get_articles(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    source_id: Optional[int] = Query(None),
    analysis_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get articles with pagination and filtering"""
    try:
        offset = (page - 1) * limit
        
        # Build query
        where_conditions = []
        params = []
        
        if source_id:
            where_conditions.append("a.source_id = ?")
            params.append(source_id)
        
        if analysis_status:
            where_conditions.append("a.analysis_status = ?")
            params.append(analysis_status)
        
        if search:
            where_conditions.append("(a.title LIKE ? OR a.summary LIKE ? OR a.content LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get articles
        articles = db_manager.execute_query(f"""
            SELECT a.*, s.name as source_name
            FROM articles a
            JOIN sources s ON a.source_id = s.id
            {where_clause}
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
        """, tuple(params + [limit, offset]))
        
        # Get total count
        count_result = db_manager.execute_query(f"""
            SELECT COUNT(*) as total
            FROM articles a
            JOIN sources s ON a.source_id = s.id
            {where_clause}
        """, tuple(params))
        
        total = count_result[0]["total"] if count_result else 0
        
        return {
            "articles": [dict(article) for article in articles],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    except Exception as e:
        logger.error(f"Failed to get articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/{article_id}")
async def get_article(article_id: int):
    """Get a specific article with analysis data"""
    try:
        # Get article
        article = db_manager.execute_query("""
            SELECT a.*, s.name as source_name
            FROM articles a
            JOIN sources s ON a.source_id = s.id
            WHERE a.id = ?
        """, (article_id,))
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        article_data = dict(article[0])
        
        # Get analysis data
        analysis = db_manager.execute_query("""
            SELECT analysis_data, confidence_score, processing_time_seconds, 
                   ai_model_used, prompt_version, created_at
            FROM ai_analysis
            WHERE article_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (article_id,))
        
        if analysis:
            analysis_data = dict(analysis[0])
            analysis_data["analysis_data"] = json.loads(analysis_data["analysis_data"])
            article_data["analysis"] = analysis_data
        
        # Get IOCs
        iocs = db_manager.execute_query("""
            SELECT ioc_type, ioc_value, confidence_score
            FROM iocs
            WHERE article_id = ?
            ORDER BY ioc_type, confidence_score DESC
        """, (article_id,))
        
        article_data["iocs"] = [dict(ioc) for ioc in iocs]
        
        # Get CVEs
        cves = db_manager.execute_query("""
            SELECT cve_id, description, severity
            FROM cves
            WHERE article_id = ?
        """, (article_id,))
        
        article_data["cves"] = [dict(cve) for cve in cves]
        
        return article_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis endpoints
@router.get("/analysis/stats")
async def get_analysis_stats():
    """Get analysis statistics"""
    try:
        # Overall stats
        overall = db_manager.execute_query("""
            SELECT 
                analysis_status,
                COUNT(*) as count
            FROM articles
            GROUP BY analysis_status
        """)
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent = db_manager.execute_query("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as articles_scraped,
                COUNT(CASE WHEN analysis_status = 'completed' THEN 1 END) as articles_analyzed
            FROM articles
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (week_ago,))
        
        # Top IOC types
        ioc_types = db_manager.execute_query("""
            SELECT 
                ioc_type,
                COUNT(*) as count
            FROM iocs
            GROUP BY ioc_type
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # Top threat actors
        threat_actors = db_manager.execute_query("""
            SELECT 
                actor_name,
                COUNT(*) as mentions
            FROM threat_actors
            GROUP BY actor_name
            ORDER BY mentions DESC
            LIMIT 10
        """)
        
        return {
            "overall_stats": {row["analysis_status"]: row["count"] for row in overall},
            "recent_activity": [dict(row) for row in recent],
            "top_ioc_types": [dict(row) for row in ioc_types],
            "top_threat_actors": [dict(row) for row in threat_actors]
        }
    except Exception as e:
        logger.error(f"Failed to get analysis stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# IOCs endpoints
@router.get("/iocs")
async def get_iocs(
    ioc_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get IOCs with filtering"""
    try:
        where_conditions = []
        params = []
        
        if ioc_type:
            where_conditions.append("i.ioc_type = ?")
            params.append(ioc_type)
        
        if search:
            where_conditions.append("i.ioc_value LIKE ?")
            params.append(f"%{search}%")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        iocs = db_manager.execute_query(f"""
            SELECT i.*, a.title as article_title, a.url as article_url, s.name as source_name
            FROM iocs i
            JOIN articles a ON i.article_id = a.id
            JOIN sources s ON a.source_id = s.id
            {where_clause}
            ORDER BY i.confidence_score DESC, i.created_at DESC
            LIMIT ?
        """, tuple(params + [limit]))
        
        return {"iocs": [dict(ioc) for ioc in iocs]}
    except Exception as e:
        logger.error(f"Failed to get IOCs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scraping endpoints
@router.post("/scraping/trigger")
async def trigger_scraping(job: ScrapingJobTrigger):
    """Manually trigger scraping for a source"""
    try:
        success = await scheduler.trigger_scraping_job(job.source_name)
        if success:
            return {"message": f"Scraping job triggered for {job.source_name}"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to trigger scraping for {job.source_name}")
    except Exception as e:
        logger.error(f"Failed to trigger scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scraping/jobs")
async def get_scraping_jobs(
    limit: int = Query(50, ge=1, le=1000),
    source_id: Optional[int] = Query(None)
):
    """Get scraping job history"""
    try:
        where_clause = "WHERE sj.source_id = ?" if source_id else ""
        params = [source_id] if source_id else []
        
        jobs = db_manager.execute_query(f"""
            SELECT sj.*, s.name as source_name
            FROM scraping_jobs sj
            JOIN sources s ON sj.source_id = s.id
            {where_clause}
            ORDER BY sj.created_at DESC
            LIMIT ?
        """, tuple(params + [limit]))
        
        return {"jobs": [dict(job) for job in jobs]}
    except Exception as e:
        logger.error(f"Failed to get scraping jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System endpoints
@router.get("/system/status")
async def get_system_status():
    """Get system status"""
    try:
        # Worker stats
        worker_stats = worker_manager.get_stats()
        
        # Scheduler status
        scheduler_jobs = scheduler.get_job_status()
        
        # Database stats
        db_stats = db_manager.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM sources WHERE is_active = 1) as active_sources,
                (SELECT COUNT(*) FROM articles) as total_articles,
                (SELECT COUNT(*) FROM articles WHERE analysis_status = 'pending') as pending_analysis,
                (SELECT COUNT(*) FROM iocs) as total_iocs,
                (SELECT COUNT(*) FROM cves) as total_cves
        """)
        
        return {
            "workers": worker_stats,
            "scheduler": {
                "is_running": scheduler.is_running,
                "jobs": scheduler_jobs
            },
            "database": dict(db_stats[0]) if db_stats else {}
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoints
@router.get("/search")
async def search_content(
    q: str = Query(..., min_length=3),
    content_type: str = Query("all", regex="^(all|articles|iocs|cves|actors)$"),
    limit: int = Query(50, ge=1, le=200)
):
    """Search across different content types"""
    try:
        results = {}
        search_term = f"%{q}%"
        
        if content_type in ["all", "articles"]:
            articles = db_manager.execute_query("""
                SELECT a.id, a.title, a.summary, a.url, s.name as source_name, a.created_at
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                WHERE a.title LIKE ? OR a.summary LIKE ? OR a.content LIKE ?
                ORDER BY a.created_at DESC
                LIMIT ?
            """, (search_term, search_term, search_term, limit))
            results["articles"] = [dict(article) for article in articles]
        
        if content_type in ["all", "iocs"]:
            iocs = db_manager.execute_query("""
                SELECT i.*, a.title as article_title, a.url as article_url
                FROM iocs i
                JOIN articles a ON i.article_id = a.id
                WHERE i.ioc_value LIKE ?
                ORDER BY i.confidence_score DESC
                LIMIT ?
            """, (search_term, limit))
            results["iocs"] = [dict(ioc) for ioc in iocs]
        
        if content_type in ["all", "cves"]:
            cves = db_manager.execute_query("""
                SELECT c.*, a.title as article_title, a.url as article_url
                FROM cves c
                JOIN articles a ON c.article_id = a.id
                WHERE c.cve_id LIKE ? OR c.description LIKE ?
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (search_term, search_term, limit))
            results["cves"] = [dict(cve) for cve in cves]
        
        if content_type in ["all", "actors"]:
            actors = db_manager.execute_query("""
                SELECT ta.*, a.title as article_title, a.url as article_url
                FROM threat_actors ta
                JOIN articles a ON ta.article_id = a.id
                WHERE ta.actor_name LIKE ?
                ORDER BY ta.created_at DESC
                LIMIT ?
            """, (search_term, limit))
            results["threat_actors"] = [dict(actor) for actor in actors]
        
        return {"query": q, "results": results}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))