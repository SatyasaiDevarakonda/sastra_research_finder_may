"""
SASTRA Research Finder - Analytics API Routes
SciVal-like analytics and metrics.
"""

from fastapi import APIRouter, Query
from typing import Optional

from app.services import get_search_engine, get_faculty_matcher
from app.services.analytics import AnalyticsService
from app.models.schemas import (
    AnalyticsStats, PublicationTrends, DocumentTypeDistribution,
    TopKeywords, CollaborationNetwork, GeographicCollaboration,
    SchoolComparison, JournalAnalytics, ImpactMetrics
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Global analytics service reference
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service_instance() -> AnalyticsService:
    """Get or create analytics service instance."""
    global _analytics_service
    if _analytics_service is None:
        engine = get_search_engine()
        faculty_matcher = get_faculty_matcher()
        _analytics_service = AnalyticsService(
            engine.publications,
            engine.author_profiles,
            faculty_matcher
        )
    return _analytics_service


@router.get("/stats", response_model=AnalyticsStats)
async def get_stats():
    """
    Get comprehensive statistics summary.
    """
    analytics = get_analytics_service_instance()
    stats = analytics.get_comprehensive_stats()
    
    return AnalyticsStats(
        total_publications=stats['total_publications'],
        total_authors=stats['total_authors'],
        total_citations=stats['total_citations'],
        total_current_faculty=stats['total_current_faculty'],
        unique_keywords=stats['unique_keywords'],
        year_range=stats['year_range'],
        schools=stats['schools'],
        document_types=stats['document_types']
    )


@router.get("/trends", response_model=PublicationTrends)
async def get_publication_trends():
    """
    Get publication and citation trends over time.
    """
    analytics = get_analytics_service_instance()
    trends = analytics.get_publication_trends()
    
    return PublicationTrends(**trends)


@router.get("/document-types", response_model=DocumentTypeDistribution)
async def get_document_type_distribution():
    """
    Get document type distribution.
    """
    analytics = get_analytics_service_instance()
    dist = analytics.get_document_type_distribution()
    
    return DocumentTypeDistribution(**dist)


@router.get("/keywords")
async def get_top_keywords(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get top keywords across all publications.
    """
    engine = get_search_engine()
    return engine.get_top_keywords(limit=limit)


@router.get("/collaboration/network", response_model=CollaborationNetwork)
async def get_collaboration_network(
    min_weight: int = Query(2, ge=1, description="Minimum collaboration count"),
    max_nodes: int = Query(100, ge=10, le=500, description="Maximum number of nodes")
):
    """
    Get co-authorship network data for visualization.
    """
    analytics = get_analytics_service_instance()
    network = analytics.get_collaboration_network(min_weight=min_weight, max_nodes=max_nodes)
    
    return CollaborationNetwork(**network)


@router.get("/collaboration/geographic", response_model=GeographicCollaboration)
async def get_geographic_collaboration():
    """
    Get geographic collaboration statistics.
    """
    analytics = get_analytics_service_instance()
    geo = analytics.get_geographic_collaboration()
    
    return GeographicCollaboration(
        countries=geo['countries'],
        collaboration_counts=geo['collaboration_counts'],
        international_percentage=geo['international_percentage']
    )


@router.get("/schools", response_model=SchoolComparison)
async def get_school_comparison():
    """
    Get school-wise comparison data (SciVal-like benchmarking).
    """
    analytics = get_analytics_service_instance()
    comparison = analytics.get_school_comparison()
    
    return SchoolComparison(**comparison)


@router.get("/journals", response_model=JournalAnalytics)
async def get_journal_analytics(
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get journal analytics including quartile distribution.
    """
    analytics = get_analytics_service_instance()
    journals = analytics.get_journal_analytics(top_n=limit)
    
    return JournalAnalytics(**journals)


@router.get("/impact", response_model=ImpactMetrics)
async def get_impact_metrics(
    entity_type: str = Query("institution", description="Entity type: institution, school, or author"),
    entity_id: Optional[str] = Query(None, description="Entity ID (required for school/author)")
):
    """
    Get impact metrics (SciVal-like FWCI, percentiles).
    """
    analytics = get_analytics_service_instance()
    metrics = analytics.get_impact_metrics(entity_type=entity_type, entity_id=entity_id)
    
    return ImpactMetrics(**metrics)


@router.get("/thematic-distribution")
async def get_thematic_distribution():
    """
    Get publication distribution across thematic areas.
    """
    analytics = get_analytics_service_instance()
    return analytics.get_thematic_distribution()


@router.get("/open-access")
async def get_open_access_statistics():
    """
    Get open access statistics.
    """
    analytics = get_analytics_service_instance()
    return analytics.get_open_access_statistics()


@router.get("/productivity")
async def get_author_productivity():
    """
    Get author productivity distribution.
    """
    analytics = get_analytics_service_instance()
    return analytics.get_author_productivity_distribution()


@router.get("/citation-distribution")
async def get_citation_distribution():
    """
    Get citation distribution across publications.
    """
    analytics = get_analytics_service_instance()
    return analytics.get_citation_distribution()


@router.get("/growth-rate")
async def get_yearly_growth_rate():
    """
    Get yearly publication growth rates.
    """
    analytics = get_analytics_service_instance()
    return analytics.get_yearly_growth_rate()


@router.get("/benchmark")
async def get_benchmark_data(
    schools: str = Query(None, description="Comma-separated school names to compare")
):
    """
    Get benchmarking data for comparing schools.
    """
    analytics = get_analytics_service_instance()
    comparison = analytics.get_school_comparison()
    
    # Filter if specific schools requested
    if schools:
        school_list = [s.strip() for s in schools.split(',')]
        indices = [
            i for i, s in enumerate(comparison['schools'])
            if any(requested in s for requested in school_list)
        ]
        
        if indices:
            return {
                'schools': [comparison['schools'][i] for i in indices],
                'publication_counts': [comparison['publication_counts'][i] for i in indices],
                'citation_counts': [comparison['citation_counts'][i] for i in indices],
                'avg_citations': [comparison['avg_citations'][i] for i in indices],
                'faculty_counts': [comparison['faculty_counts'][i] for i in indices]
            }
    
    return comparison
