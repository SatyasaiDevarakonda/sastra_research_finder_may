"""
SASTRA Research Finder - Publications API Routes
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.services import get_search_engine
from app.models.schemas import (
    PublicationDetail, PublicationSearchResult, PublicationFilters, FilterOptions
)

router = APIRouter(prefix="/publications", tags=["Publications"])


@router.get("/", response_model=PublicationSearchResult)
async def get_publications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    year: Optional[int] = None,
    school: Optional[str] = None,
    document_type: Optional[str] = None,
    thematic_area: Optional[str] = None,
    is_international: Optional[bool] = None,
    search: Optional[str] = None
):
    """
    Get publications with optional filters.
    """
    engine = get_search_engine()
    
    # Get filtered publications
    pubs = engine.get_publications_by_filter(
        year=year,
        school=school,
        doc_type=document_type,
        thematic_area=thematic_area,
        is_international=is_international,
        limit=1000
    )
    
    # Apply text search if provided
    if search:
        search_lower = search.lower()
        pubs = [
            p for p in pubs
            if search_lower in p.get('title', '').lower()
            or search_lower in p.get('abstract', '').lower()
            or any(search_lower in kw for kw in p.get('author_keywords', []))
        ]
    
    # Paginate
    total = len(pubs)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = pubs[start:end]
    
    return PublicationSearchResult(
        total=total,
        results=paginated,
        page=page,
        page_size=page_size
    )


@router.get("/latest", response_model=List[PublicationDetail])
async def get_latest_publications(
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get the most recent publications.
    """
    engine = get_search_engine()
    return engine.get_latest_publications(limit=limit)


@router.get("/filters", response_model=FilterOptions)
async def get_filter_options():
    """
    Get available filter options.
    """
    engine = get_search_engine()
    stats = engine.get_stats()
    
    from app.core.config import THEMATIC_AREAS
    
    return FilterOptions(
        years=stats.get('years', []),
        schools=stats.get('schools', []),
        document_types=stats.get('document_types', []),
        thematic_areas=list(THEMATIC_AREAS.keys())
    )


@router.get("/{pub_id}", response_model=PublicationDetail)
async def get_publication(pub_id: str):
    """
    Get a single publication by ID.
    """
    engine = get_search_engine()
    pub = engine.publications.get(pub_id)
    
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    return pub


@router.get("/{pub_id}/similar", response_model=List[PublicationDetail])
async def get_similar_publications(
    pub_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get publications similar to a given publication.
    """
    engine = get_search_engine()
    
    if pub_id not in engine.publications:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    similar = engine.get_similar_publications(pub_id, top_k=limit)
    return similar
