"""
SASTRA Research Finder - Database Models
SQLAlchemy ORM models for new database features.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class PaperSource(str, enum.Enum):
    SASTRA = "SASTRA"
    GLOBAL = "GLOBAL"


class ResearchDomain(Base):
    """Research domain/category - top level grouping"""
    __tablename__ = "research_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    color = Column(String, nullable=True)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_dynamic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    themes = relationship("ResearchTheme", back_populates="domain", cascade="all, delete-orphan")


class ResearchTheme(Base):
    """Research theme - individual topics within domains"""
    __tablename__ = "research_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("research_domains.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    keywords = Column(JSON, default=list)
    description = Column(Text, nullable=True)
    embedding_centroid = Column(JSON, nullable=True)
    paper_count = Column(Integer, default=0)
    faculty_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_dynamic = Column(Boolean, default=False)
    source = Column(String, default="static")  # "static" or "dynamic"
    similarity_to_parent = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    domain = relationship("ResearchDomain", back_populates="themes")


class PocProject(Base):
    __tablename__ = "poc_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_author_id = Column(String, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    source = Column(String, default="manual")  # "manual" or "github"
    github_repo_id = Column(String, nullable=True)
    github_repo_name = Column(String, nullable=True)
    linked_account = Column(String, nullable=True)  # "github", etc.
    auto_synced = Column(Boolean, default=False)
    github_link = Column(String, nullable=True)
    document_url = Column(String, nullable=True)
    year = Column(Integer, default=datetime.now().year)
    extracted_domains = Column(JSON, default=list)
    # complexity_score = Column(Integer, default=0)
    # impact_score = Column(Integer, default=0)
    keywords = Column(JSON, default=list)
    tech_stack = Column(JSON, default=list)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    last_synced = Column(DateTime, nullable=True)
    github_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class FundedProject(Base):
    __tablename__ = "funded_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_author_id = Column(String, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    funding_agency = Column(String)
    amount = Column(Float, nullable=True)
    currency = Column(String, default="INR")
    start_year = Column(Integer)
    end_year = Column(Integer, nullable=True)
    document_url = Column(String, nullable=True)
    extracted_domains = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class IndexScore(Base):
    __tablename__ = "index_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_author_id = Column(String, unique=True, index=True)
    scopus_h_index = Column(Integer, default=0)
    sci_paper_count = Column(Integer, default=0)
    q1_paper_count = Column(Integer, default=0)
    q2_paper_count = Column(Integer, default=0)
    web_of_science_count = Column(Integer, default=0)
    composite_index_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)


class DynamicDomain(Base):
    __tablename__ = "dynamic_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    parent_static_domain = Column(String, nullable=True)
    similarity_to_parent = Column(Float)
    example_titles = Column(JSON, default=list)
    embedding_centroid = Column(JSON, default=list)
    paper_count = Column(Integer, default=0)
    project_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=False)


class GithubAccount(Base):
    """GitHub account connection for faculty"""
    __tablename__ = "github_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_author_id = Column(String, index=True)
    github_username = Column(String, nullable=True)
    access_token_encrypted = Column(Text, nullable=True)  # Encrypted token storage
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_synced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)