"""
SASTRA Research Finder - Domains API Routes
Static and dynamic domain management.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.dynamic_domain_service import get_dynamic_domain_service
from app.services import get_search_engine

router = APIRouter(prefix="/domains", tags=["Domains"])


class DomainDetectionRequest(BaseModel):
    """Request for domain detection."""
    text: str


class DomainDetectionResponse(BaseModel):
    """Response for domain detection."""
    is_new: bool
    similarity: float
    closest_domain: Optional[str] = None
    matched_domain: Optional[str] = None


class DynamicDomainCreate(BaseModel):
    """Create dynamic domain request."""
    name: str
    parent_static_domain: str
    similarity_to_parent: float
    example_titles: List[str]
    embedding_centroid: List[float]


@router.get("/all")
async def get_all_domains(db: Session = Depends(get_db)):
    """Get all static and approved dynamic domains."""
    service = get_dynamic_domain_service()
    return service.get_all_domains(db)


@router.get("/dynamic")
async def get_dynamic_domains(db: Session = Depends(get_db)):
    """Get only dynamic domains."""
    service = get_dynamic_domain_service()
    return service.get_dynamic_domains(db)


@router.post("/detect", response_model=DomainDetectionResponse)
async def detect_domain(request: DomainDetectionRequest):
    """Detect if given text represents a new domain."""
    engine = get_search_engine()
    service = get_dynamic_domain_service()

    if not hasattr(engine, 'embedding_model') or engine.embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not available")

    try:
        embedding = engine.embedding_model.encode(request.text)
        result = service.detect_new_domain(request.text, embedding.tolist())
        
        return DomainDetectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dynamic")
async def create_dynamic_domain(
    domain: DynamicDomainCreate,
    db: Session = Depends(get_db)
):
    """Create a new dynamic domain (requires approval)."""
    service = get_dynamic_domain_service()
    
    new_domain = service.create_dynamic_domain(
        db=db,
        name=domain.name,
        parent_static_domain=domain.parent_static_domain,
        similarity_to_parent=domain.similarity_to_parent,
        example_titles=domain.example_titles,
        embedding_centroid=domain.embedding_centroid
    )
    
    return {
        "id": new_domain.id,
        "name": new_domain.name,
        "message": "Dynamic domain created, pending approval"
    }


@router.post("/dynamic/{domain_id}/approve")
async def approve_dynamic_domain(
    domain_id: int,
    db: Session = Depends(get_db)
):
    """Approve a dynamic domain."""
    service = get_dynamic_domain_service()
    domain = service.approve_dynamic_domain(db, domain_id)
    
    if not domain:
        raise HTTPException(status_code=404, detail="Dynamic domain not found")
    
    return {"success": True, "name": domain.name, "message": "Domain approved"}


@router.delete("/dynamic/{domain_id}")
async def delete_dynamic_domain(
    domain_id: int,
    db: Session = Depends(get_db)
):
    """Delete a dynamic domain."""
    service = get_dynamic_domain_service()
    
    if not service.delete_dynamic_domain(db, domain_id):
        raise HTTPException(status_code=404, detail="Dynamic domain not found")
    
    return {"success": True, "message": "Domain deleted"}