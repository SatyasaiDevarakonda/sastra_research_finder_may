"""
SASTRA Research Finder - GitHub Integration API Routes
Connect GitHub, fetch repositories, create/update projects.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.github_service import GithubService
from app.services.project_service import ProjectService
from app.services import get_search_engine
from app.services.faculty_matcher import get_faculty_matcher
from app.models.schemas import (
    GithubConnectionRequest,
    GithubConnectionResponse,
    GithubRepoListResponse,
    GithubProjectCreate,
    GithubSyncResponse,
    GithubRepoInfo,
    GithubUsernameConnectionRequest,
    GithubSuggestionResponse,
    PocProjectResponse,
    SuccessResponse,
)

router = APIRouter(prefix="/github", tags=["GitHub Integration"])


@router.post("/connect", response_model=GithubConnectionResponse)
async def connect_github(
    request: GithubConnectionRequest,
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """Connect GitHub account with access token."""
    try:
        return GithubService.connect_github(db, faculty_author_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect GitHub: {str(e)}")


@router.post("/disconnect", response_model=SuccessResponse)
async def disconnect_github(
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """Disconnect GitHub account."""
    success = GithubService.disconnect_github(db, faculty_author_id)
    return SuccessResponse(
        success=success,
        message="GitHub disconnected successfully" if success else "No GitHub account found"
    )


@router.get("/status")
async def get_github_status(
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """Check GitHub connection status."""
    is_connected = GithubService.is_github_connected(db, faculty_author_id)
    username = GithubService.get_github_username(db, faculty_author_id) if is_connected else None
    
    return {
        "connected": is_connected,
        "github_username": username
    }


@router.get("/repositories", response_model=GithubRepoListResponse)
async def get_github_repositories(
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """Get all repositories for connected GitHub account."""
    if not GithubService.is_github_connected(db, faculty_author_id):
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    repos = GithubService.get_user_repositories(db, faculty_author_id)
    
    return GithubRepoListResponse(
        repositories=repos,
        total=len(repos)
    )


@router.post("/projects", response_model=PocProjectResponse)
async def create_project_from_github(
    request: GithubProjectCreate,
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """Create POC project from GitHub repository. Works for both token-auth and public-username connections."""
    if not GithubService.is_github_connected(db, faculty_author_id):
        raise HTTPException(status_code=400, detail="GitHub not connected")

    repos = GithubService.get_user_repositories(db, faculty_author_id)
    repo_info = next((r for r in repos if r.repo_id == request.repo_id), None)

    if not repo_info:
        raise HTTPException(status_code=404, detail="Repository not found")

    project = GithubService.create_project_from_github(db, faculty_author_id, repo_info)

    return PocProjectResponse(
        id=project.id,
        faculty_author_id=project.faculty_author_id,
        title=project.title or "",
        description=project.description or "",
        source=project.source or "github",
        github_repo_id=project.github_repo_id,
        github_repo_name=project.github_repo_name,
        linked_account=project.linked_account,
        auto_synced=bool(project.auto_synced),
        github_link=project.github_link,
        document_url=project.document_url,
        year=project.year or 0,
        extracted_domains=project.extracted_domains or [],
        # complexity_score=project.complexity_score or 0,
        # impact_score=project.impact_score or 0,
        keywords=project.keywords or [],
        tech_stack=project.tech_stack or [],
        stars=project.stars or 0,
        forks=project.forks or 0,
        last_synced=project.last_synced,
        github_metadata=project.github_metadata or {},
        created_at=project.created_at
    )


@router.post("/projects/{project_id}/sync", response_model=GithubSyncResponse)
async def sync_github_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Sync GitHub-based POC project with latest data."""
    project = ProjectService.get_poc_project(db, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.source != "github":
        raise HTTPException(status_code=400, detail="Project is not from GitHub")
    
    try:
        return GithubService.sync_github_project(db, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/repos/{repo_id}", response_model=GithubRepoInfo)
async def get_repo_details(
    repo_id: str,
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific repository."""
    if not GithubService.is_github_connected(db, faculty_author_id):
        raise HTTPException(status_code=400, detail="GitHub not connected")

    repos = GithubService.get_user_repositories(db, faculty_author_id)
    for repo in repos:
        if repo.repo_id == repo_id:
            return repo

    raise HTTPException(status_code=404, detail="Repository not found")


@router.post("/connect-public", response_model=GithubConnectionResponse)
async def connect_github_by_username(
    request: GithubUsernameConnectionRequest,
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """
    Connect a GitHub profile by public username alone (no access token).
    Only public repos will be accessible. Ideal for faculty who don't want to
    generate a personal access token.
    """
    try:
        return GithubService.connect_by_username(db, faculty_author_id, request.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect GitHub: {str(e)}")


@router.get("/suggest", response_model=GithubSuggestionResponse)
async def suggest_github_username(
    faculty_author_id: str,
    db: Session = Depends(get_db)
):
    """
    Suggest a GitHub username for the given faculty by searching GitHub using
    their SASTRA email and full name (public profile data only).
    """
    faculty_matcher = get_faculty_matcher()
    info = faculty_matcher.get_faculty_info(author_id=faculty_author_id) or {}

    engine = get_search_engine()
    profile = engine.search_by_author_id(faculty_author_id) or {}
    name = info.get("name") or profile.get("name") or (profile.get("name_variants") or [""])[0]
    email = info.get("email")

    suggestions = GithubService.suggest_usernames(name=name, email=email, limit=5)
    return GithubSuggestionResponse(
        suggestions=suggestions,
        source=email or name or ""
    )