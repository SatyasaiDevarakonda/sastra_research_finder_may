"""
SASTRA Research Finder - Pydantic Models
Data models for API requests and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _coerce_int(v):
    """Coerce None/floats/strings into int safely. Used to rescue legacy DB rows."""
    if v is None:
        return 0
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return 0


# =============================================================================
# PUBLICATION MODELS
# =============================================================================

class PublicationBase(BaseModel):
    """Base publication model."""
    pub_id: str
    title: str
    abstract: Optional[str] = ""
    year: int
    citations: int = 0
    document_type: str = ""
    source: str = ""
    doi: str = ""
    link: str = ""
    open_access: bool = False


class PublicationDetail(PublicationBase):
    """Detailed publication model."""
    authors: str = ""
    author_ids: List[str] = []
    author_names: List[str] = []
    author_positions: Dict[str, str] = {}  # author_id -> position (1st, 2nd, co-author)
    affiliations: str = ""
    author_keywords: List[str] = []
    index_keywords: List[str] = []
    all_keywords: List[str] = []
    countries: List[str] = []
    school: str = ""
    thematic_areas: List[str] = []
    is_international_collab: bool = False
    journal_quartile: Optional[str] = None


class PublicationSearchResult(BaseModel):
    """Publication search result."""
    total: int
    results: List[PublicationDetail]
    page: int = 1
    page_size: int = 20


# =============================================================================
# AUTHOR MODELS
# =============================================================================

class AuthorBase(BaseModel):
    """Base author model."""
    author_id: str
    name: str
    name_variants: List[str] = []
    is_current_faculty: bool = False


class AuthorProfile(AuthorBase):
    """Detailed author profile."""
    pub_count: int = 0
    total_citations: int = 0
    h_index: int = 0
    g_index: int = 0
    i10_index: int = 0
    publications: List[PublicationDetail] = []
    top_keywords: List[Dict[str, Any]] = []  # [{"keyword": str, "count": int}]
    affiliations: List[str] = []
    schools: List[str] = []
    citation_list: List[int] = []
    national_collabs: int = 0
    international_collabs: int = 0
    country_collabs: Dict[str, int] = {}
    yearly_publications: Dict[int, int] = {}
    yearly_citations: Dict[int, int] = {}
    faculty_info: Optional[Dict[str, Any]] = None


class AuthorSearchResult(BaseModel):
    """Author search result."""
    author_id: str
    name: str
    name_variants: List[str] = []
    matching_papers: int = 0
    total_score: float = 0.0
    total_citations: int = 0
    top_keywords: List[str] = []
    pub_ids: List[str] = []
    is_current_faculty: bool = False
    photo_url: str = ""


# =============================================================================
# FACULTY MODELS
# =============================================================================

class FacultyInfo(BaseModel):
    """Faculty member information."""
    staff_id: str
    name: str
    normalized_name: str = ""
    email: str = ""
    school: str = ""
    department: str = ""
    designation: str = ""
    campus: str = ""
    orcid: str = ""
    photo_url: str = ""
    is_current: bool = True
    author_ids: List[str] = []


class FacultyStats(BaseModel):
    """Faculty statistics."""
    total_faculty: int
    matched_authors: int
    schools: Dict[str, int]
    departments: Dict[str, int]
    designations: Dict[str, int]


# =============================================================================
# THEMATIC AREA MODELS
# =============================================================================

class ThematicAuthor(BaseModel):
    """Author in a thematic area."""
    author_id: str
    primary_name: str
    name_variants: List[str] = []
    total_cite_score: int = 0
    paper_count: int = 0
    papers: List[Dict[str, Any]] = []
    is_current_faculty: bool = False
    faculty_info: Optional[FacultyInfo] = None
    unified_score: Optional[float] = None
    poc_count: Optional[int] = None
    funded_count: Optional[int] = None
    composite_index_score: Optional[float] = None


class ThematicAreaRanking(BaseModel):
    """Thematic area with ranked authors."""
    theme_name: str
    authors: List[ThematicAuthor]
    total_papers: int = 0
    total_citations: int = 0
    current_faculty_count: int = 0


class TeamMember(BaseModel):
    """Member of an interdisciplinary team."""
    author_id: str
    name: str
    theme: str
    cite_score: int = 0
    paper_count: int = 0
    papers: List[Dict[str, Any]] = []
    is_current_faculty: bool = True
    faculty_info: Optional[FacultyInfo] = None
    unified_score: Optional[float] = None
    poc_count: Optional[int] = None
    funded_count: Optional[int] = None
    composite_index_score: Optional[float] = None


class InterdisciplinaryTeam(BaseModel):
    """Interdisciplinary team."""
    team_number: int
    members: List[TeamMember]
    total_cite_score: int = 0
    average_cite_score: float = 0.0
    themes: List[str] = []


# =============================================================================
# SEARCH MODELS
# =============================================================================

class KeywordSearchRequest(BaseModel):
    """Keyword search request."""
    keywords: str
    use_semantic: bool = True
    max_results: int = 100
    page: int = 1
    page_size: int = 20


class KeywordSearchResponse(BaseModel):
    """Keyword search response."""
    total: int
    keywords_used: List[str]
    total_matching_pubs: int
    document_type_dist: Dict[str, int]
    results: List[AuthorSearchResult]


class SemanticSearchRequest(BaseModel):
    """Semantic search request."""
    query: str
    top_k: int = 50


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    total: int
    results: List[Dict[str, Any]]  # [{pub_id, score, ...}]


class SkillSearchRequest(BaseModel):
    """Skill-based search request."""
    project_title: str
    max_results: int = 20


class SkillSearchResponse(BaseModel):
    """Skill-based search response."""
    extracted_skills: List[str]
    experts: List[AuthorSearchResult]
    context_publications: List[Dict[str, Any]]


# =============================================================================
# ANALYTICS MODELS
# =============================================================================

class AnalyticsStats(BaseModel):
    """Overall analytics statistics."""
    total_publications: int
    total_authors: int
    total_citations: int
    total_current_faculty: int
    unique_keywords: int
    year_range: str
    schools: List[str]
    document_types: List[str]


class PublicationTrends(BaseModel):
    """Publication trends over time."""
    years: List[int]
    publication_counts: List[int]
    citation_counts: List[int]
    cumulative_publications: List[int]
    cumulative_citations: List[int]


class DocumentTypeDistribution(BaseModel):
    """Document type distribution."""
    types: List[str]
    counts: List[int]
    percentages: List[float]


class TopKeywords(BaseModel):
    """Top keywords."""
    keywords: List[str]
    counts: List[int]


class TopAuthors(BaseModel):
    """Top authors by publication count."""
    authors: List[Dict[str, Any]]


class CollaborationNetwork(BaseModel):
    """Collaboration network data."""
    nodes: List[Dict[str, Any]]  # [{id, name, pub_count, is_faculty}]
    edges: List[Dict[str, Any]]  # [{source, target, weight}]


class GeographicCollaboration(BaseModel):
    """Geographic collaboration data."""
    countries: List[str]
    collaboration_counts: List[int]
    international_percentage: float


class SchoolComparison(BaseModel):
    """School comparison data."""
    schools: List[str]
    publication_counts: List[int]
    citation_counts: List[int]
    avg_citations: List[float]
    faculty_counts: List[int]


class JournalAnalytics(BaseModel):
    """Journal analytics data."""
    journals: List[str]
    counts: List[int]
    quartile_distribution: Dict[str, int]


class ImpactMetrics(BaseModel):
    """Research impact metrics."""
    total_citations: int
    avg_citations_per_paper: float
    h_index: int
    papers_in_top_1_percent: int
    papers_in_top_10_percent: int
    papers_in_top_25_percent: int
    international_collab_percentage: float


class ThematicStatistics(BaseModel):
    """Thematic area statistics."""
    theme_name: str
    paper_count: int
    total_citations: int
    author_count: int
    current_faculty_count: int
    avg_citations: float
    year_range: str


# =============================================================================
# RAG MODELS
# =============================================================================

class RAGAnalysisRequest(BaseModel):
    """RAG analysis request."""
    skills: List[str]
    max_context: int = 20
    structured: bool = False
    search_online: bool = True  # Search for global papers
    max_global_papers: int = 10  # Max global papers to fetch from web


class RAGPaper(BaseModel):
    """Paper in RAG analysis."""
    title: str
    authors: str = ""
    year: int = 0
    link: str = ""
    pdf_link: str = ""  # Direct PDF link
    abstract: str = ""  # Paper abstract
    citations: int = 0  # Citation count
    venue: str = ""  # Journal/Conference name
    relevance_score: float = 0.0
    source: str = "SASTRA"  # "SASTRA" or "GLOBAL"


class RAGAnalysisContent(BaseModel):
    """RAG analysis content."""
    key_methods: List[str] = []
    research_gaps: List[str] = []
    emerging_trends: List[str] = []
    collaboration_insights: List[str] = []


class RAGAnalysisResponse(BaseModel):
    """RAG analysis response."""
    analysis: Optional[str] = None
    error: Optional[str] = None
    context_count: int = 0
    sastra_papers: Optional[List[RAGPaper]] = None
    global_papers: Optional[List[RAGPaper]] = None
    structured_analysis: Optional[RAGAnalysisContent] = None


class AuthorSummaryRequest(BaseModel):
    """Author summary request."""
    author_id: str


class AuthorSummaryResponse(BaseModel):
    """Author summary response."""
    summary: str
    author_id: str


# =============================================================================
# FILTER MODELS
# =============================================================================

class PublicationFilters(BaseModel):
    """Publication filters."""
    year: Optional[int] = None
    school: Optional[str] = None
    document_type: Optional[str] = None
    has_doi: Optional[bool] = None
    is_open_access: Optional[bool] = None
    min_citations: Optional[int] = None
    thematic_area: Optional[str] = None
    is_international: Optional[bool] = None


class FilterOptions(BaseModel):
    """Available filter options."""
    years: List[int]
    schools: List[str]
    document_types: List[str]
    thematic_areas: List[str]


# =============================================================================
# BENCHMARKING MODELS
# =============================================================================

class BenchmarkComparison(BaseModel):
    """Benchmark comparison data."""
    entity_type: str  # "school", "department", "author"
    entities: List[str]
    metrics: Dict[str, List[float]]  # metric_name -> values for each entity


class FieldWeightedCitationImpact(BaseModel):
    """FWCI calculation."""
    entity_name: str
    fwci: float
    world_average: float
    percentile: float


# =============================================================================
# TEAM FORMATION MODELS
# =============================================================================

class TeamFormationRequest(BaseModel):
    """Team formation request."""
    themes: List[str]
    max_teams: int = 5


class TeamFormationResponse(BaseModel):
    """Team formation response."""
    themes: List[str]
    teams: List[InterdisciplinaryTeam]
    total_teams: int


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    timestamp: datetime
    components: Dict[str, str]  # component -> status


# =============================================================================
# EVALUATION MODELS
# =============================================================================

class PocProjectCreate(BaseModel):
    """POC project creation request."""
    faculty_author_id: str
    title: str
    description: str = ""
    source: str = "manual"  # "manual" or "github"
    github_repo_id: Optional[str] = None
    github_repo_name: Optional[str] = None
    linked_account: Optional[str] = None
    github_link: Optional[str] = None
    document_url: Optional[str] = None
    year: Optional[int] = None
    extracted_domains: List[str] = []
    # complexity_score: int = 0
    # impact_score: int = 0
    keywords: List[str] = []
    tech_stack: List[str] = []


class PocProjectResponse(BaseModel):
    """POC project response."""
    model_config = ConfigDict(from_attributes=True)

    @field_validator("year", "stars", "forks", mode="before")
    @classmethod
    def _as_int(cls, v):
        return _coerce_int(v)

    @field_validator("description", "title", mode="before")
    @classmethod
    def _as_str(cls, v):
        return "" if v is None else str(v)

    @field_validator("extracted_domains", "keywords", "tech_stack", mode="before")
    @classmethod
    def _as_list(cls, v):
        return [] if v is None else v

    @field_validator("github_metadata", mode="before")
    @classmethod
    def _as_dict(cls, v):
        return {} if v is None else v

    id: int
    faculty_author_id: str
    title: str
    description: str
    source: str = "manual"
    github_repo_id: Optional[str] = None
    github_repo_name: Optional[str] = None
    linked_account: Optional[str] = None
    auto_synced: bool = False
    github_link: Optional[str] = None
    document_url: Optional[str] = None
    year: int
    extracted_domains: List[str]
    # complexity_score: int
    # impact_score: int
    keywords: List[str]
    tech_stack: List[str] = []
    stars: int = 0
    forks: int = 0
    last_synced: Optional[datetime] = None
    github_metadata: Dict[str, Any] = {}
    created_at: datetime


class FundedProjectCreate(BaseModel):
    """Funded project creation request."""
    faculty_author_id: str
    title: str
    description: str = ""
    funding_agency: str = ""
    amount: Optional[float] = None
    currency: str = "INR"
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    document_url: Optional[str] = None
    extracted_domains: List[str] = []
    keywords: List[str] = []


class FundedProjectResponse(BaseModel):
    """Funded project response."""
    model_config = ConfigDict(from_attributes=True)

    @field_validator("start_year", mode="before")
    @classmethod
    def _start_year_as_int(cls, v):
        return _coerce_int(v)

    @field_validator("end_year", mode="before")
    @classmethod
    def _end_year_as_int_optional(cls, v):
        if v is None or v == "":
            return None
        try:
            return int(round(float(v)))
        except (TypeError, ValueError):
            return None

    @field_validator("description", "title", "funding_agency", "currency", mode="before")
    @classmethod
    def _as_str(cls, v):
        return "" if v is None else str(v)

    @field_validator("extracted_domains", "keywords", mode="before")
    @classmethod
    def _as_list(cls, v):
        return [] if v is None else v

    id: int
    faculty_author_id: str
    title: str
    description: str
    funding_agency: str
    amount: Optional[float]
    currency: str
    start_year: int
    end_year: Optional[int]
    document_url: Optional[str]
    extracted_domains: List[str]
    keywords: List[str]
    created_at: datetime


class IndexScoreCreate(BaseModel):
    """Index score creation request."""
    faculty_author_id: str
    scopus_h_index: int = 0
    sci_paper_count: int = 0
    q1_paper_count: int = 0
    q2_paper_count: int = 0
    web_of_science_count: int = 0


class IndexScoreResponse(BaseModel):
    """Index score response."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    faculty_author_id: str
    scopus_h_index: int
    sci_paper_count: int
    q1_paper_count: int
    q2_paper_count: int
    web_of_science_count: int
    composite_index_score: float
    last_updated: datetime


class EvaluationSummary(BaseModel):
    """Full evaluation summary for a faculty."""
    author_id: str
    poc_projects: List[PocProjectResponse] = []
    funded_projects: List[FundedProjectResponse] = []
    index_score: Optional[IndexScoreResponse] = None


class MetadataExtractionRequest(BaseModel):
    """Request for LLM metadata extraction."""
    title: str
    description: str


class MetadataExtractionResponse(BaseModel):
    """Response for LLM metadata extraction."""
    domains: List[str] = []
    dynamic_domains: List[str] = []
    # complexity: int = 0
    # impact_score: int = 0
    keywords: List[str] = []


# =============================================================================
# GITHUB INTEGRATION MODELS
# =============================================================================

class GithubRepoInfo(BaseModel):
    """GitHub repository information."""
    repo_id: str
    name: str
    full_name: str
    description: Optional[str] = ""
    html_url: str
    language: Optional[str] = ""
    stargazers_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    watchers_count: int = 0
    default_branch: str = "main"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pushed_at: Optional[str] = None
    topics: List[str] = []
    license: Optional[str] = None
    is_private: bool = False
    is_fork: bool = False
    forks: int = 0
    open_issues: int = 0


class GithubConnectionRequest(BaseModel):
    """Request to connect GitHub account."""
    access_token: str
    refresh_token: Optional[str] = None


class GithubUsernameConnectionRequest(BaseModel):
    """Request to connect GitHub account by public username (no token)."""
    username: str


class GithubConnectionResponse(BaseModel):
    """Response for GitHub connection."""
    github_username: str
    connected: bool = True
    repositories_count: int = 0
    mode: str = "token"  # "token" (private repos possible) or "public" (public only)


class GithubUsernameSuggestion(BaseModel):
    """A suggested GitHub username with context."""
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_url: str
    match_reason: str  # "email", "name", etc.


class GithubSuggestionResponse(BaseModel):
    """Response for GitHub username auto-suggest."""
    suggestions: List[GithubUsernameSuggestion] = []
    source: str = ""  # What we searched by


class GithubRepoListResponse(BaseModel):
    """Response listing GitHub repositories."""
    repositories: List[GithubRepoInfo]
    total: int


class GithubProjectCreate(BaseModel):
    """Create POC project from GitHub repo. faculty_author_id is supplied via query string."""
    repo_id: str
    faculty_author_id: Optional[str] = None


class GithubSyncResponse(BaseModel):
    """Response for GitHub sync operation."""
    project_id: int
    title: str
    synced: bool = True
    github_metadata: Dict[str, Any] = {}


class ActivityScore(BaseModel):
    """GitHub activity score calculation."""
    github_activity_score: float = 0.0
    stars_weight: float = 0.0
    commit_weight: float = 0.0
    recency_weight: float = 0.0
    stars: int = 0
    total_commits: int = 0
    days_since_update: int = 0
    complexity_level: int = 1
