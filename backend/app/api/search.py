"""
SASTRA Research Finder - Search API Routes
"""

from fastapi import APIRouter, Query, Body
from typing import Optional, List

from app.services import get_search_engine, get_rag, extract_keywords
from app.models.schemas import (
    KeywordSearchRequest, KeywordSearchResponse,
    SemanticSearchRequest, SemanticSearchResponse,
    SkillSearchRequest, SkillSearchResponse,
    AuthorSearchResult
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/keywords", response_model=KeywordSearchResponse)
async def search_by_keywords(request: KeywordSearchRequest):
    """
    Search publications and authors by keywords.
    Combines keyword and semantic search for best results.
    """
    engine = get_search_engine()
    
    results = engine.search_by_keywords(
        keywords_input=request.keywords,
        max_results=request.max_results,
        use_semantic=request.use_semantic
    )
    
    # Convert to response format
    author_results = []
    for r in results.get('results', []):
        author_results.append(AuthorSearchResult(
            author_id=r.get('author_id', ''),
            name=r.get('name_variants', ['Unknown'])[0] if r.get('name_variants') else 'Unknown',
            name_variants=r.get('name_variants', []),
            matching_papers=r.get('matching_papers', 0),
            total_score=r.get('total_score', 0.0),
            total_citations=r.get('total_citations', 0),
            top_keywords=r.get('top_keywords', []),
            pub_ids=r.get('pub_ids', []),
            is_current_faculty=r.get('is_current_faculty', False),
            photo_url=r.get('photo_url', '')
        ))

    return KeywordSearchResponse(
        total=results.get('total', 0),
        keywords_used=results.get('keywords_used', []),
        total_matching_pubs=results.get('total_matching_pubs', 0),
        document_type_dist=results.get('document_type_dist', {}),
        results=author_results
    )


@router.get("/keywords")
async def search_keywords_get(
    keywords: str = Query(..., description="Comma-separated keywords"),
    use_semantic: bool = Query(True),
    max_results: int = Query(100, ge=1, le=500)
):
    """
    Search by keywords (GET endpoint).
    """
    engine = get_search_engine()
    return engine.search_by_keywords(
        keywords_input=keywords,
        max_results=max_results,
        use_semantic=use_semantic
    )


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    Perform semantic search using FAISS.
    """
    engine = get_search_engine()
    results = engine.semantic_search(query=request.query, top_k=request.top_k)
    
    return SemanticSearchResponse(
        total=len(results),
        results=results
    )


@router.get("/semantic")
async def semantic_search_get(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(50, ge=1, le=200)
):
    """
    Perform semantic search (GET endpoint).
    """
    engine = get_search_engine()
    return engine.semantic_search(query=query, top_k=top_k)


@router.post("/skills", response_model=SkillSearchResponse)
async def search_by_skills(request: SkillSearchRequest):
    """
    Find experts based on project title.
    Extracts skills from the title and finds matching researchers.
    """
    engine = get_search_engine()
    rag = get_rag()
    
    # Extract skills from project title
    skills = rag.extract_skills(request.project_title)
    
    if not skills:
        # Fallback to basic keyword extraction
        skills = extract_keywords(request.project_title, max_keywords=10)
    
    # Search for experts
    search_results = engine.search_by_keywords(
        keywords_input=', '.join(skills),
        max_results=request.max_results,
        use_semantic=True
    )
    
    # Get context publications
    context = engine.get_rag_context(skills, max_abstracts=20)
    
    # Convert results
    experts = []
    for r in search_results.get('results', []):
        experts.append(AuthorSearchResult(
            author_id=r.get('author_id', ''),
            name=r.get('name_variants', ['Unknown'])[0] if r.get('name_variants') else 'Unknown',
            name_variants=r.get('name_variants', []),
            matching_papers=r.get('matching_papers', 0),
            total_score=r.get('total_score', 0.0),
            total_citations=r.get('total_citations', 0),
            top_keywords=r.get('top_keywords', []),
            pub_ids=r.get('pub_ids', []),
            is_current_faculty=r.get('is_current_faculty', False),
            photo_url=r.get('photo_url', '')
        ))
    
    return SkillSearchResponse(
        extracted_skills=skills,
        experts=experts,
        context_publications=context
    )


@router.get("/skills")
async def search_skills_get(
    project_title: str = Query(..., description="Project title to extract skills from"),
    max_results: int = Query(20, ge=1, le=100)
):
    """
    Search by skills (GET endpoint).
    """
    engine = get_search_engine()
    rag = get_rag()
    
    skills = rag.extract_skills(project_title)
    if not skills:
        skills = extract_keywords(project_title, max_keywords=10)
    
    results = engine.search_by_keywords(
        keywords_input=', '.join(skills),
        max_results=max_results,
        use_semantic=True
    )
    
    return {
        "extracted_skills": skills,
        "results": results
    }


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get autocomplete suggestions for search.
    """
    engine = get_search_engine()
    q_lower = q.lower()
    
    # Get matching keywords
    matching_keywords = [
        kw for kw in engine.keyword_index.keys()
        if kw.startswith(q_lower)
    ]
    
    # Sort by frequency
    matching_keywords.sort(key=lambda x: len(engine.keyword_index.get(x, [])), reverse=True)
    
    return {
        "suggestions": matching_keywords[:limit]
    }
