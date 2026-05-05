"""
SASTRA Research Finder - Faculty Evaluation API Routes
POC projects, funded projects, and index scores.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from app.core.database import get_db
from app.core.config import get_settings
from app.services.project_service import ProjectService, IndexScoreService
from app.utils.file_extractor import extract_text_and_files, sanitize_filename
from app.models.schemas import (
    PocProjectCreate, PocProjectResponse,
    FundedProjectCreate, FundedProjectResponse,
    IndexScoreCreate, IndexScoreResponse,
    EvaluationSummary, MetadataExtractionRequest,
    MetadataExtractionResponse
)

router = APIRouter(prefix="/evaluation", tags=["Faculty Evaluation"])


@router.post("/poc", response_model=PocProjectResponse)
async def create_poc_project(
    project: PocProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new POC project."""
    return ProjectService.create_poc_project(
        db=db,
        faculty_author_id=project.faculty_author_id,
        title=project.title,
        description=project.description,
        github_link=project.github_link,
        document_url=project.document_url,
        year=project.year,
        extracted_domains=project.extracted_domains,
        # complexity_score=project.complexity_score,
        # impact_score=project.impact_score,
        keywords=project.keywords
    )


@router.get("/poc/{author_id}", response_model=List[PocProjectResponse])
async def get_poc_projects(
    author_id: str,
    db: Session = Depends(get_db)
):
    """Get all POC projects for a faculty member."""
    return ProjectService.get_poc_projects(db, author_id)


@router.put("/poc/{project_id}", response_model=PocProjectResponse)
async def update_poc_project(
    project_id: int,
    project: PocProjectCreate,
    db: Session = Depends(get_db)
):
    """Update a POC project."""
    updated = ProjectService.update_poc_project(
        db=db,
        project_id=project_id,
        title=project.title,
        description=project.description,
        github_link=project.github_link,
        document_url=project.document_url,
        year=project.year,
        extracted_domains=project.extracted_domains,
        # complexity_score=project.complexity_score,
        # impact_score=project.impact_score,
        keywords=project.keywords
    )
    if not updated:
        raise HTTPException(status_code=404, detail="POC project not found")
    return updated


@router.delete("/poc/{project_id}")
async def delete_poc_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Delete a POC project."""
    if not ProjectService.delete_poc_project(db, project_id):
        raise HTTPException(status_code=404, detail="POC project not found")
    return {"success": True, "message": "POC project deleted"}


@router.post("/funded", response_model=FundedProjectResponse)
async def create_funded_project(
    project: FundedProjectCreate,
    db: Session = Depends(get_db)
):
    """Create a new funded project."""
    return ProjectService.create_funded_project(
        db=db,
        faculty_author_id=project.faculty_author_id,
        title=project.title,
        description=project.description,
        funding_agency=project.funding_agency,
        amount=project.amount,
        currency=project.currency,
        start_year=project.start_year,
        end_year=project.end_year,
        document_url=project.document_url,
        extracted_domains=project.extracted_domains,
        keywords=project.keywords
    )


@router.get("/funded/{author_id}", response_model=List[FundedProjectResponse])
async def get_funded_projects(
    author_id: str,
    db: Session = Depends(get_db)
):
    """Get all funded projects for a faculty member."""
    return ProjectService.get_funded_projects(db, author_id)


@router.put("/funded/{project_id}", response_model=FundedProjectResponse)
async def update_funded_project(
    project_id: int,
    project: FundedProjectCreate,
    db: Session = Depends(get_db)
):
    """Update a funded project."""
    updated = ProjectService.update_funded_project(
        db=db,
        project_id=project_id,
        title=project.title,
        description=project.description,
        funding_agency=project.funding_agency,
        amount=project.amount,
        currency=project.currency,
        start_year=project.start_year,
        end_year=project.end_year,
        document_url=project.document_url,
        extracted_domains=project.extracted_domains,
        keywords=project.keywords
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Funded project not found")
    return updated


@router.delete("/funded/{project_id}")
async def delete_funded_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Delete a funded project."""
    if not ProjectService.delete_funded_project(db, project_id):
        raise HTTPException(status_code=404, detail="Funded project not found")
    return {"success": True, "message": "Funded project deleted"}


@router.post("/index-score/{author_id}", response_model=IndexScoreResponse)
async def update_index_score(
    author_id: str,
    score_data: IndexScoreCreate,
    db: Session = Depends(get_db)
):
    """Update index scores for a faculty member."""
    return IndexScoreService.update_index_score(
        db=db,
        faculty_author_id=author_id,
        scopus_h_index=score_data.scopus_h_index,
        sci_paper_count=score_data.sci_paper_count,
        q1_paper_count=score_data.q1_paper_count,
        q2_paper_count=score_data.q2_paper_count,
        web_of_science_count=score_data.web_of_science_count
    )


@router.get("/index-score/{author_id}", response_model=IndexScoreResponse)
async def get_index_score(
    author_id: str,
    db: Session = Depends(get_db)
):
    """Get index scores for a faculty member."""
    score = IndexScoreService.get_index_score(db, author_id)
    if not score:
        raise HTTPException(status_code=404, detail="Index score not found")
    return score


@router.post("/extract-metadata", response_model=MetadataExtractionResponse)
async def extract_metadata(
    request: MetadataExtractionRequest
):
    """Extract metadata from project using LLM."""
    from app.services import get_rag
    rag = get_rag()
    
    if not rag.is_available():
        raise HTTPException(status_code=503, detail="RAG service not available")
    
    result = rag.extract_project_metadata(request.title, request.description)
    
    return MetadataExtractionResponse(
        domains=result.get("domains", []),
        dynamic_domains=result.get("dynamic_domains", []),
        # complexity=result.get("complexity", 0),
        # impact_score=result.get("impact_score", 0),
        keywords=result.get("keywords", [])
    )


@router.post("/upload")
async def upload_project_document(
    faculty_author_id: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a project document (PDF / DOCX / TXT / code / ZIP folder).
    Extracts text, runs Mistral metadata extraction, saves the file under
    data/uploads/{author_id}/, and returns suggested metadata plus a public URL.
    """
    settings = get_settings()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    # Size guard (reject > 20 MB)
    max_bytes = 20 * 1024 * 1024
    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    filename = sanitize_filename(file.filename)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_author = sanitize_filename(faculty_author_id)
    upload_dir = settings.DATA_DIR / "uploads" / safe_author
    upload_dir.mkdir(parents=True, exist_ok=True)
    final_name = f"{ts}_{filename}"
    final_path = upload_dir / final_name

    try:
        final_path.write_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    text, files_listed = extract_text_and_files(filename, data)

    from app.services import get_rag
    rag = get_rag()
    metadata = rag.extract_from_document(filename, text) if rag.is_available() else {
        "suggested_title": Path(filename).stem.replace("_", " ").replace("-", " ").title(),
        "suggested_description": (text or "")[:280],
        "domains": [],
        "dynamic_domains": [],
        # "complexity": 0,
        # "impact_score": 0,
        "keywords": [],
    }

    public_url = f"/api/evaluation/uploads/{safe_author}/{final_name}"

    return {
        "filename": filename,
        "stored_filename": final_name,
        "file_url": public_url,
        "size_bytes": len(data),
        "files_listed": files_listed[:50],
        "text_preview": (text or "")[:500],
        "metadata": metadata,
    }


@router.get("/uploads/{author_id}/{filename}")
async def get_uploaded_file(author_id: str, filename: str):
    """Serve a previously uploaded project document."""
    settings = get_settings()
    safe_author = sanitize_filename(author_id)
    safe_name = sanitize_filename(filename)
    path = settings.DATA_DIR / "uploads" / safe_author / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=safe_name)


@router.get("/summary/{author_id}", response_model=EvaluationSummary)
async def get_evaluation_summary(
    author_id: str,
    db: Session = Depends(get_db)
):
    """Get full evaluation summary for a faculty member."""
    poc_projects = ProjectService.get_poc_projects(db, author_id)
    funded_projects = ProjectService.get_funded_projects(db, author_id)
    index_score = IndexScoreService.get_index_score(db, author_id)
    
    # Validate each row individually so a single bad legacy row can't
    # 500 the whole list. Bad rows are logged and skipped.
    def _safe_validate(model_cls, row):
        try:
            return model_cls.model_validate(row)
        except Exception as e:
            print(f"⚠️ skipping row id={getattr(row, 'id', '?')} "
                  f"for {model_cls.__name__}: {e}")
            return None

    poc_items = [m for m in (_safe_validate(PocProjectResponse, p) for p in poc_projects) if m]
    funded_items = [m for m in (_safe_validate(FundedProjectResponse, p) for p in funded_projects) if m]
    index_item = _safe_validate(IndexScoreResponse, index_score) if index_score else None

    return EvaluationSummary(
        author_id=author_id,
        poc_projects=poc_items,
        funded_projects=funded_items,
        index_score=index_item,
    )