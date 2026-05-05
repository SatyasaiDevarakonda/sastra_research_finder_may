"""
SASTRA Research Finder - Thematic Areas API Routes
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.services import get_search_engine, get_faculty_matcher
from app.services.thematic_areas import ThematicAreasEngine, get_theme_names, get_theme_keywords
from app.core.config import POPULAR_THEME_COMBINATIONS
from app.models.schemas import (
    ThematicAreaRanking, ThematicAuthor, InterdisciplinaryTeam,
    TeamFormationRequest, TeamFormationResponse, ThematicStatistics
)

router = APIRouter(prefix="/thematic", tags=["Thematic Areas"])

# Global thematic engine reference
_thematic_engine: Optional[ThematicAreasEngine] = None


def get_thematic_engine_instance() -> ThematicAreasEngine:
    """Get or create thematic engine instance."""
    global _thematic_engine
    if _thematic_engine is None:
        engine = get_search_engine()
        faculty_matcher = get_faculty_matcher()
        _thematic_engine = ThematicAreasEngine(
            engine.publications,
            engine.author_profiles,
            faculty_matcher.current_faculty_author_ids
        )
    return _thematic_engine


@router.get("/themes")
async def get_available_themes(
    only_with_faculty: bool = Query(True, description="Only return themes with current faculty")
):
    """
    Get list of all available thematic areas.
    """
    thematic_engine = get_thematic_engine_instance()
    themes = thematic_engine.get_available_themes(only_with_faculty=only_with_faculty)
    
    return {
        "themes": themes,
        "total": len(themes)
    }


@router.get("/themes/{theme_name}")
async def get_theme_details(theme_name: str):
    """
    Get details and keywords for a specific theme.
    """
    keywords = get_theme_keywords(theme_name)
    if not keywords:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    return {
        "theme_name": theme_name,
        "keywords": keywords
    }


@router.get("/rankings")
async def get_theme_rankings(
    theme: str = Query(..., description="Theme name"),
    only_faculty: bool = Query(True, description="Only include current faculty"),
    limit: int = Query(15, ge=1, le=50)
):
    """
    Get ranked authors for a specific theme.
    Faculty-only rankings are used for team formation.
    """
    thematic_engine = get_thematic_engine_instance()
    
    rankings = thematic_engine.get_single_theme_rankings(only_current_faculty=only_faculty)
    
    if theme not in rankings:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    authors = rankings[theme][:limit]
    
    # Add faculty info
    faculty_matcher = get_faculty_matcher()
    for author in authors:
        faculty_info = faculty_matcher.get_faculty_info(author_id=author['author_id'])
        author['faculty_info'] = faculty_info
    
    return ThematicAreaRanking(
        theme_name=theme,
        authors=[ThematicAuthor(**a) for a in authors],
        total_papers=sum(a['paper_count'] for a in authors),
        total_citations=sum(a['total_cite_score'] for a in authors),
        current_faculty_count=len([a for a in authors if a.get('is_current_faculty', False)])
    )


@router.get("/rankings/all")
async def get_all_theme_rankings(
    only_faculty: bool = Query(True, description="Only include current faculty")
):
    """
    Get rankings for all themes.
    """
    thematic_engine = get_thematic_engine_instance()
    rankings = thematic_engine.get_single_theme_rankings(only_current_faculty=only_faculty)
    
    result = {}
    for theme, authors in rankings.items():
        if authors:  # Only include themes with authors
            result[theme] = {
                "theme_name": theme,
                "top_author": authors[0]['primary_name'] if authors else None,
                "author_count": len(authors),
                "total_citations": sum(a['total_cite_score'] for a in authors)
            }
    
    return result


@router.post("/teams", response_model=TeamFormationResponse)
async def generate_teams(request: TeamFormationRequest):
    """
    Generate interdisciplinary teams from selected themes.
    Teams are formed ONLY from current SASTRA faculty members.
    """
    if len(request.themes) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 themes are required for team formation"
        )
    
    thematic_engine = get_thematic_engine_instance()
    
    teams = thematic_engine.generate_team_for_themes(
        themes=tuple(request.themes),
        max_teams=request.max_teams
    )
    
    return TeamFormationResponse(
        themes=request.themes,
        teams=[InterdisciplinaryTeam(**t) for t in teams],
        total_teams=len(teams)
    )


@router.get("/teams/popular")
async def get_popular_combinations():
    """
    Get popular interdisciplinary theme combinations.
    """
    return {
        "combinations": POPULAR_THEME_COMBINATIONS
    }


@router.get("/teams/generate")
async def generate_teams_get(
    themes: str = Query(..., description="Comma-separated theme names"),
    max_teams: int = Query(5, ge=1, le=20)
):
    """
    Generate teams (GET endpoint).
    """
    theme_list = [t.strip() for t in themes.split(',') if t.strip()]
    
    if len(theme_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 themes are required"
        )
    
    thematic_engine = get_thematic_engine_instance()
    teams = thematic_engine.generate_team_for_themes(
        themes=tuple(theme_list),
        max_teams=max_teams
    )
    
    return {
        "themes": theme_list,
        "teams": teams,
        "total_teams": len(teams)
    }


@router.get("/statistics")
async def get_theme_statistics():
    """
    Get statistics for all thematic areas.
    """
    thematic_engine = get_thematic_engine_instance()
    stats = thematic_engine.get_theme_statistics()
    
    result = []
    for theme_name, data in stats.items():
        result.append(ThematicStatistics(
            theme_name=theme_name,
            paper_count=data['paper_count'],
            total_citations=data['total_citations'],
            author_count=data['author_count'],
            current_faculty_count=data['current_faculty_count'],
            avg_citations=data['avg_citations'],
            year_range=data['year_range']
        ))
    
    # Sort by paper count
    result.sort(key=lambda x: x.paper_count, reverse=True)
    
    return result
