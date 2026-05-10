"""
SASTRA Research Finder - Main FastAPI Application
Professional, AI-powered research publication discovery platform.
Version 4.0 - React + FastAPI Architecture
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.api import api_router
from app.models.schemas import HealthCheck, ErrorResponse


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("=" * 60)
    print("SASTRA Research Finder v4.0 - Starting...")
    print("=" * 60)
    
    # Initialize database
    try:
        from app.core.database import init_db
        init_db()
        print("✓ Database initialized")
        
        # Seed domains and themes
        try:
            from app.core.database import SessionLocal
            from app.services.theme_service import seed_domains_and_themes
            db = SessionLocal()
            seed_domains_and_themes(db)
            db.close()
            print("✓ Domains and themes seeded")
        except Exception as e:
            print(f"⚠️ Warning: Could not seed domains/themes: {e}")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize database: {e}")
    
    # Initialize search engine (loads data, builds indexes)
    try:
        from app.services import get_search_engine
        engine = get_search_engine()
        print("✓ Search engine initialized")
        print(f"  - Publications: {len(engine.publications):,}")
        print(f"  - Authors: {len(engine.author_profiles):,}")
        
        # Initialize unified scorer with search engine
        from app.services.unified_scorer import init_unified_scorer
        init_unified_scorer(search_engine=engine)
        print("✓ Unified scorer initialized")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize search engine: {e}")

    # Pre-compute analytics and thematic caches so first page visits are instant
    try:
        from app.services.analytics import AnalyticsService
        from app.services.thematic_areas import ThematicAreasEngine
        from app.services import get_search_engine, get_faculty_matcher

        eng = get_search_engine()
        fm = get_faculty_matcher()

        # Warm up analytics cache
        analytics = AnalyticsService(eng.publications, eng.author_profiles, fm)
        analytics.get_comprehensive_stats()
        analytics.get_publication_trends()
        analytics.get_document_type_distribution()
        analytics.get_school_comparison()
        analytics.get_geographic_collaboration()
        analytics.get_journal_analytics()
        analytics.get_impact_metrics()
        analytics.get_citation_distribution()
        print("✓ Analytics cache warmed up")

        # Store the pre-warmed instance for the API to use
        from app.api.analytics import _analytics_service
        import app.api.analytics as analytics_module
        analytics_module._analytics_service = analytics

        # Warm up thematic cache
        import time as _time
        thematic = ThematicAreasEngine(
            eng.publications, eng.author_profiles, fm.current_faculty_author_ids
        )
        _t0 = _time.time()
        thematic.get_available_themes(only_with_faculty=True)
        print(f"  ✓ get_available_themes: {_time.time()-_t0:.1f}s")
        _t0 = _time.time()
        thematic.get_theme_statistics()
        print(f"  ✓ get_theme_statistics: {_time.time()-_t0:.1f}s")
        print("✓ Thematic areas cache warmed up")

        import app.api.thematic as thematic_module
        thematic_module._thematic_engine = thematic

    except Exception as e:
        print(f"⚠️ Warning: Could not warm up caches: {e}")

    print("=" * 60)
    print("Application ready!")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("Shutting down SASTRA Research Finder...")


# Create FastAPI application
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="""
## SASTRA Research Finder API

A professional, AI-powered research publication discovery platform for SASTRA Deemed University.

### Features

- **Advanced Search**: Keyword, semantic (FAISS), and hybrid search
- **Author Discovery**: Comprehensive author profiles with metrics
- **Faculty Integration**: Current faculty identification and team formation
- **Thematic Areas**: 100 research domains with expert rankings
- **Analytics**: SciVal-like metrics and visualizations
- **RAG Analysis**: AI-powered research insights (Mistral AI)

### Key Endpoints

- `/api/publications` - Publication management
- `/api/authors` - Author profiles and faculty
- `/api/search` - Search capabilities
- `/api/thematic` - Thematic areas and teams
- `/api/analytics` - Research analytics
- `/api/rag` - AI-powered analysis
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Serve faculty staff photos as static files. Frontend renders <img src=...>
# pointing to <BACKEND_PUBLIC_URL>/staff-photos/<staff_id>.jpg.
_staff_photos_dir = settings.DATA_DIR / "staff-photos"
if _staff_photos_dir.exists():
    app.mount(
        "/staff-photos",
        StaticFiles(directory=str(_staff_photos_dir)),
        name="staff-photos",
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-powered research publication discovery platform",
        "docs_url": "/docs",
        "api_prefix": "/api",
        "endpoints": {
            "publications": "/api/publications",
            "authors": "/api/authors",
            "search": "/api/search",
            "thematic": "/api/thematic",
            "analytics": "/api/analytics",
            "rag": "/api/rag"
        }
    }


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    components = {
        "api": "healthy"
    }
    
    # Check database
    try:
        from app.core.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        components["database"] = "connected"
    except Exception as e:
        components["database"] = f"error: {str(e)}"
    
    # Check search engine
    try:
        from app.services import get_search_engine
        engine = get_search_engine()
        if engine._initialized:
            components["search_engine"] = "healthy"
            components["publications"] = f"{len(engine.publications)} loaded"
            components["authors"] = f"{len(engine.author_profiles)} loaded"
        else:
            components["search_engine"] = "not initialized"
    except Exception as e:
        components["search_engine"] = f"error: {str(e)}"
    
    # Check FAISS
    try:
        from app.services import get_faiss_engine
        faiss_engine = get_faiss_engine()
        components["faiss"] = "available" if faiss_engine.is_available() else "not available"
    except Exception as e:
        components["faiss"] = f"error: {str(e)}"
    
    # Check RAG
    try:
        from app.services import get_rag
        rag = get_rag()
        components["mistral_rag"] = "available" if rag.is_available() else "not configured"
    except Exception as e:
        components["mistral_rag"] = f"error: {str(e)}"
    
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        components=components
    )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# 404 handler
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 Not Found handler."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Not found",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Resource not found"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG
    )
