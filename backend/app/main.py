"""
Main application entry point
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.logging_config import setup_logging, get_logger
from .db.database import db_manager
from .workers.analysis_worker import worker_manager
from .workers.scheduler import scheduler
from .services.ai_analysis import ai_service
from .api import routes

# Setup logging
setup_logging(
    log_level=settings.logging.level,
    log_dir=settings.logging.log_dir,
    max_file_size_mb=settings.logging.max_file_size_mb,
    backup_count=settings.logging.backup_count
)

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Cybersecurity Intelligence Platform")
    
    try:
        # Test AI service connection
        logger.info("Testing AI service connection...")
        ai_connected = await ai_service.test_connection()
        if not ai_connected:
            logger.warning("AI service connection failed - analysis will be disabled")
        else:
            logger.info("AI service connection successful")
        
        # Start workers (temporarily disabled due to errors)
        logger.info("Analysis workers disabled temporarily...")
        # await worker_manager.start()
        
        # Start scheduler
        logger.info("Starting task scheduler...")
        await scheduler.start()
        
        logger.info("Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down application...")
        
        try:
            await scheduler.stop()
            # await worker_manager.stop()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="Cybersecurity Intelligence Platform",
    description="AI-powered cybersecurity intelligence scraping and analysis platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cybersecurity Intelligence Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            db_manager.execute_query("SELECT 1")
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Check AI service
        ai_status = "healthy" if await ai_service.test_connection() else "error"
        
        # Get worker stats
        worker_stats = worker_manager.get_stats()
        
        # Get scheduler status
        scheduler_status = "running" if scheduler.is_running else "stopped"
        
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {
                "database": db_status,
                "ai_service": ai_status,
                "workers": worker_stats,
                "scheduler": scheduler_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    import uvicorn
    
    setup_signal_handlers()
    
    logger.info(
        "Starting server",
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.logging.level.lower()
    )