"""
SASTRA Research Finder - Project Service
CRUD operations for POC and Funded projects.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db_models import PocProject, FundedProject, IndexScore
from datetime import datetime


class ProjectService:
    """Service for managing POC and Funded projects."""
    
    @staticmethod
    def create_poc_project(
        db: Session,
        faculty_author_id: str,
        title: str,
        description: str = "",
        source: str = "manual",
        github_repo_id: str = None,
        github_repo_name: str = None,
        linked_account: str = None,
        github_link: Optional[str] = None,
        document_url: Optional[str] = None,
        year: Optional[int] = None,
        extracted_domains: List[str] = None,
        # complexity_score: int = 0,
        # impact_score: int = 0,
        keywords: List[str] = None,
        tech_stack: List[str] = None,
        stars: int = 0,
        forks: int = 0,
        metadata: dict = None
    ) -> PocProject:
        """Create a new POC project."""
        project = PocProject(
            faculty_author_id=faculty_author_id,
            title=title,
            description=description,
            source=source,
            github_repo_id=github_repo_id,
            github_repo_name=github_repo_name,
            linked_account=linked_account,
            auto_synced=True if source == "github" else False,
            github_link=github_link,
            document_url=document_url,
            year=year or datetime.now().year,
            extracted_domains=extracted_domains or [],
            # complexity_score=complexity_score,
            # impact_score=impact_score,
            keywords=keywords or [],
            tech_stack=tech_stack or [],
            stars=stars,
            forks=forks,
            github_metadata=metadata or {},
            last_synced=datetime.utcnow() if source == "github" else None
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def get_poc_projects(db: Session, faculty_author_id: str) -> List[PocProject]:
        """Get all POC projects for a faculty."""
        return db.query(PocProject).filter(
            PocProject.faculty_author_id == faculty_author_id
        ).all()
    
    @staticmethod
    def get_poc_project(db: Session, project_id: int) -> Optional[PocProject]:
        """Get a specific POC project."""
        return db.query(PocProject).filter(PocProject.id == project_id).first()
    
    @staticmethod
    def update_poc_project(
        db: Session,
        project_id: int,
        **kwargs
    ) -> Optional[PocProject]:
        """Update a POC project."""
        project = ProjectService.get_poc_project(db, project_id)
        if not project:
            return None
        
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def delete_poc_project(db: Session, project_id: int) -> bool:
        """Delete a POC project."""
        project = ProjectService.get_poc_project(db, project_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True
    
    @staticmethod
    def create_funded_project(
        db: Session,
        faculty_author_id: str,
        title: str,
        description: str = "",
        funding_agency: str = "",
        amount: Optional[float] = None,
        currency: str = "INR",
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        document_url: Optional[str] = None,
        extracted_domains: List[str] = None,
        keywords: List[str] = None
    ) -> FundedProject:
        """Create a new funded project."""
        project = FundedProject(
            faculty_author_id=faculty_author_id,
            title=title,
            description=description,
            funding_agency=funding_agency,
            amount=amount,
            currency=currency,
            start_year=start_year or datetime.now().year,
            end_year=end_year,
            document_url=document_url,
            extracted_domains=extracted_domains or [],
            keywords=keywords or []
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def get_funded_projects(db: Session, faculty_author_id: str) -> List[FundedProject]:
        """Get all funded projects for a faculty."""
        return db.query(FundedProject).filter(
            FundedProject.faculty_author_id == faculty_author_id
        ).all()
    
    @staticmethod
    def get_funded_project(db: Session, project_id: int) -> Optional[FundedProject]:
        """Get a specific funded project."""
        return db.query(FundedProject).filter(FundedProject.id == project_id).first()
    
    @staticmethod
    def update_funded_project(
        db: Session,
        project_id: int,
        **kwargs
    ) -> Optional[FundedProject]:
        """Update a funded project."""
        project = ProjectService.get_funded_project(db, project_id)
        if not project:
            return None
        
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def delete_funded_project(db: Session, project_id: int) -> bool:
        """Delete a funded project."""
        project = ProjectService.get_funded_project(db, project_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True


class IndexScoreService:
    """Service for managing index scores."""
    
    @staticmethod
    def get_or_create_index_score(
        db: Session,
        faculty_author_id: str
    ) -> IndexScore:
        """Get or create an index score entry."""
        index_score = db.query(IndexScore).filter(
            IndexScore.faculty_author_id == faculty_author_id
        ).first()
        
        if not index_score:
            index_score = IndexScore(faculty_author_id=faculty_author_id)
            db.add(index_score)
            db.commit()
            db.refresh(index_score)
        
        return index_score
    
    @staticmethod
    def get_index_score(db: Session, faculty_author_id: str) -> Optional[IndexScore]:
        """Get index score for a faculty."""
        return db.query(IndexScore).filter(
            IndexScore.faculty_author_id == faculty_author_id
        ).first()
    
    @staticmethod
    def update_index_score(
        db: Session,
        faculty_author_id: str,
        scopus_h_index: Optional[int] = None,
        sci_paper_count: Optional[int] = None,
        q1_paper_count: Optional[int] = None,
        q2_paper_count: Optional[int] = None,
        web_of_science_count: Optional[int] = None
    ) -> IndexScore:
        """Update index score for a faculty."""
        index_score = IndexScoreService.get_or_create_index_score(db, faculty_author_id)
        
        if scopus_h_index is not None:
            index_score.scopus_h_index = scopus_h_index
        if sci_paper_count is not None:
            index_score.sci_paper_count = sci_paper_count
        if q1_paper_count is not None:
            index_score.q1_paper_count = q1_paper_count
        if q2_paper_count is not None:
            index_score.q2_paper_count = q2_paper_count
        if web_of_science_count is not None:
            index_score.web_of_science_count = web_of_science_count
        
        # Compute composite score
        index_score.composite_index_score = (
            (index_score.scopus_h_index * 3) +
            (index_score.sci_paper_count * 2) +
            (index_score.q1_paper_count * 5) +
            (index_score.q2_paper_count * 2) +
            (index_score.web_of_science_count * 1)
        )
        
        index_score.last_updated = datetime.utcnow()
        
        db.commit()
        db.refresh(index_score)
        return index_score