"""
SASTRA Research Finder - RAG Analysis API Routes
AI-powered research analysis using Mistral with global paper search.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.services import get_search_engine, get_rag
from app.services.web_search_service import get_web_search, get_exa_search, get_openalex_search
from app.models.schemas import (
    RAGAnalysisRequest, RAGAnalysisResponse,
    AuthorSummaryRequest, AuthorSummaryResponse,
    RAGPaper, RAGAnalysisContent
)

router = APIRouter(prefix="/rag", tags=["RAG Analysis"])


@router.post("/analyze", response_model=RAGAnalysisResponse)
async def analyze_research(request: RAGAnalysisRequest):
    """
    Generate comprehensive research analysis using RAG.
    Optionally searches online for global papers and returns both SASTRA and global papers.
    """
    try:
        return await _analyze_research_impl(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return RAGAnalysisResponse(
            analysis=None,
            error=f"Analysis failed: {type(e).__name__}: {e}",
            context_count=0,
            sastra_papers=[],
            global_papers=[],
            structured_analysis=None,
        )


async def _analyze_research_impl(request: RAGAnalysisRequest):
    engine = get_search_engine()
    rag = get_rag()
    web_search = get_web_search()
    exa_search = get_exa_search()
    openalex_search = get_openalex_search()

    context = engine.get_rag_context(
        skills=request.skills,
        max_abstracts=request.max_context
    )
    
    sastra_papers = []
    global_papers = []
    context_count = len(context) if context else 0
    
    if not context and not request.search_online:
        return RAGAnalysisResponse(
            analysis=None,
            error="No relevant publications found for the given skills.",
            context_count=0
        )
    
    if request.structured:
        sastra_papers_data = []
        if context:
            for p in context[:15]:
                link = p.get('link', '') or (f"https://doi.org/{p.get('doi', '')}" if p.get('doi') else '')
                pdf_link = p.get('document_url', link) if p.get('document_url') else (link if link else '')
                sastra_papers_data.append({
                    "title": p.get('title', ''),
                    "authors": p.get('authors', ''),
                    "year": p.get('year', 0),
                    "link": link,
                    "pdf_link": pdf_link,
                    "abstract": p.get('abstract', '')[:500],
                    "citations": p.get('citations', 0),
                    "venue": p.get('source', ''),
                    "relevance_score": 0.8,
                    "source": "SASTRA"
                })
                sastra_papers.append(RAGPaper(
                    title=p.get('title', ''),
                    authors=p.get('authors', ''),
                    year=p.get('year', 0),
                    link=link,
                    pdf_link=pdf_link,
                    abstract=p.get('abstract', '')[:300],
                    citations=p.get('citations', 0),
                    venue=p.get('source', ''),
                    relevance_score=0.8,
                    source="SASTRA"
                ))
        
        # Fetch globals FIRST so we can feed them into the analysis prompt.
        # Priority: Exa (paid, best quality) → OpenAlex (free, no key). Users always
        # get global papers when they toggle the checkbox.
        online_papers_raw = []
        if request.search_online:
            max_globals = request.max_global_papers or 10
            if exa_search.is_available():
                online_papers_raw = exa_search.search_by_skills(request.skills, max_globals)
            if not online_papers_raw:
                online_papers_raw = openalex_search.search_by_skills(request.skills, max_globals)
            for p in online_papers_raw[:max_globals]:
                global_papers.append(RAGPaper(
                    title=p.get('title', ''),
                    authors=p.get('authors', ''),
                    year=p.get('year', 0),
                    link=p.get('link', ''),
                    pdf_link=p.get('pdf_link', ''),
                    abstract=p.get('abstract', '')[:300],
                    citations=p.get('citations', 0),
                    venue=p.get('venue', ''),
                    relevance_score=p.get('relevance_score', 0.7),
                    source="GLOBAL"
                ))

        analysis_result = {}
        if context and rag.is_available():
            analysis_result = rag.analyze_with_papers(
                context=context,
                skills=request.skills,
                global_papers=online_papers_raw or None,
            )

        error_msg = None
        if not rag.is_available():
            error_msg = "Mistral AI not configured"
        elif context and analysis_result.get("error"):
            error_msg = analysis_result.get("error")
        elif request.search_online and not global_papers:
            error_msg = "Global paper search returned no results for these skills."
        
        analysis_content = analysis_result.get("analysis", {})
        structured = RAGAnalysisContent(
            key_methods=analysis_content.get("key_methods", []),
            research_gaps=analysis_content.get("research_gaps", []),
            emerging_trends=analysis_content.get("emerging_trends", []),
            collaboration_insights=analysis_content.get("collaboration_insights", [])
        ) if analysis_content else None
        
        return RAGAnalysisResponse(
            analysis=analysis_result.get("analysis_text"),
            sastra_papers=sastra_papers,
            global_papers=global_papers,
            structured_analysis=structured,
            error=error_msg,
            context_count=context_count
        )
    
    # Non-structured request
    if not rag.is_available():
        return RAGAnalysisResponse(
            analysis=None,
            error="Mistral AI not configured. Add MISTRAL_API_KEY to environment.",
            context_count=0
        )
    
    if not context:
        return RAGAnalysisResponse(
            analysis=None,
            error="No relevant publications found for the given skills.",
            context_count=0
        )
    
    result = rag.analyze(context=context, skills=request.skills)
    
    return RAGAnalysisResponse(
        analysis=result.get('analysis'),
        error=result.get('error'),
        context_count=result.get('context_count', context_count)
    )


@router.get("/analyze")
async def analyze_research_get(
    skills: str,
    max_context: int = 20
):
    """
    Generate research analysis (GET endpoint).
    """
    skill_list = [s.strip() for s in skills.split(',') if s.strip()]
    
    if not skill_list:
        raise HTTPException(status_code=400, detail="Skills parameter is required")
    
    engine = get_search_engine()
    rag = get_rag()
    
    context = engine.get_rag_context(skills=skill_list, max_abstracts=max_context)
    result = rag.analyze(context=context, skills=skill_list)
    
    return result


@router.post("/summarize-author", response_model=AuthorSummaryResponse)
async def summarize_author(request: AuthorSummaryRequest):
    """
    Generate AI summary for an author.
    """
    engine = get_search_engine()
    rag = get_rag()
    
    profile = engine.search_by_author_id(request.author_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Author not found")
    
    summary = rag.summarize_author(profile)
    
    return AuthorSummaryResponse(
        author_id=request.author_id,
        summary=summary
    )


@router.post("/extract-skills")
async def extract_skills(project_title: str):
    """
    Extract skills from a project title.
    """
    rag = get_rag()
    
    if not project_title:
        raise HTTPException(status_code=400, detail="Project title is required")
    
    skills = rag.extract_skills(project_title)
    
    return {
        "project_title": project_title,
        "skills": skills
    }


@router.get("/status")
async def get_rag_status():
    """
    Check if RAG (Mistral AI) is available.
    """
    rag = get_rag()
    
    return {
        "available": rag.is_available(),
        "model": rag.model if rag.is_available() else None,
        "message": "Mistral AI is configured and ready" if rag.is_available() else "Mistral API key not configured"
    }
