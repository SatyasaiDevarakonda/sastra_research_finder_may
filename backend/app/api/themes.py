"""
SASTRA Research Finder - Themes API Routes
Manage research domains and themes.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.theme_service import (
    get_all_themes, get_theme_by_name, create_dynamic_theme,
    get_themes_for_team_builder
)

router = APIRouter(prefix="/themes", tags=["Themes"])


class ThemeResponse(BaseModel):
    """Theme response."""
    id: int
    name: str
    keywords: List[str]
    paper_count: int = 0
    faculty_count: int = 0
    is_dynamic: bool = False


class DomainResponse(BaseModel):
    """Domain response."""
    id: int
    name: str
    color: str
    themes: List[ThemeResponse]


class CreateThemeRequest(BaseModel):
    """Create dynamic theme request."""
    name: str
    domain_name: str
    keywords: List[str]
    description: Optional[str] = None


@router.get("/all", response_model=List[DomainResponse])
async def get_all_domains_and_themes(db: Session = Depends(get_db)):
    """Get all domains with their themes."""
    domains = get_all_themes(db, include_dynamic=True)
    
    result = []
    for domain in domains:
        themes = []
        for t in domain.get('themes', []):
            themes.append(ThemeResponse(
                id=t['id'],
                name=t['name'],
                keywords=t.get('keywords', []),
                paper_count=t.get('paper_count', 0),
                faculty_count=t.get('faculty_count', 0),
                is_dynamic=t.get('is_dynamic', False)
            ))
        result.append(DomainResponse(
            id=domain.get('id', 0),
            name=domain['name'],
            color=domain.get('color', '#6B7280'),
            themes=themes
        ))
    
    return result


@router.get("/team-builder")
async def get_themes_for_teams(db: Session = Depends(get_db)):
    """Get themes available for team building."""
    themes = get_themes_for_team_builder(db)
    return {"themes": themes}


@router.get("/{theme_name}")
async def get_theme_details(theme_name: str, db: Session = Depends(get_db)):
    """Get details of a specific theme."""
    theme = get_theme_by_name(db, theme_name)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    
    return {
        "id": theme.id,
        "name": theme.name,
        "domain": theme.domain.name if theme.domain else None,
        "keywords": theme.keywords,
        "description": theme.description,
        "paper_count": theme.paper_count,
        "faculty_count": theme.faculty_count,
        "is_dynamic": theme.is_dynamic
    }


@router.post("/dynamic")
async def create_theme(request: CreateThemeRequest, db: Session = Depends(get_db)):
    """Create a new dynamic theme."""
    theme = create_dynamic_theme(
        db=db,
        name=request.name,
        domain_name=request.domain_name,
        keywords=request.keywords,
        description=request.description
    )
    
    return {
        "id": theme.id,
        "name": theme.name,
        "message": "Dynamic theme created successfully"
    }


@router.get("/")
async def get_themes_legacy(db: Session = Depends(get_db)):
    """Legacy endpoint - returns theme names for backward compatibility."""
    from app.core.config import THEMATIC_AREAS
    return {"themes": list(THEMATIC_AREAS.keys())}