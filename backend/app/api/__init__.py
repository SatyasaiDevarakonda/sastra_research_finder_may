"""
SASTRA Research Finder - API Package
"""

from fastapi import APIRouter

from app.api.publications import router as publications_router
from app.api.authors import router as authors_router
from app.api.search import router as search_router
from app.api.thematic import router as thematic_router
from app.api.analytics import router as analytics_router
from app.api.rag import router as rag_router
from app.api.evaluation import router as evaluation_router
from app.api.domains import router as domains_router
from app.api.themes import router as themes_router
from app.api.github import router as github_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(publications_router)
api_router.include_router(authors_router)
api_router.include_router(search_router)
api_router.include_router(thematic_router)
api_router.include_router(analytics_router)
api_router.include_router(rag_router)
api_router.include_router(evaluation_router)
api_router.include_router(domains_router)
api_router.include_router(themes_router)
api_router.include_router(github_router)

__all__ = ['api_router']
