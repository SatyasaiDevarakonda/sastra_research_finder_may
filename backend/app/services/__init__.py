"""
SASTRA Research Finder - Services Package
"""

from app.services.data_loader import DataLoader, get_data_loader, load_all_data
from app.services.faculty_matcher import FacultyMatcher, get_faculty_matcher, is_current_faculty, get_faculty_info
from app.services.faiss_engine import FAISSEngine, get_faiss_engine
from app.services.search_engine import SearchEngine, get_search_engine, extract_keywords
from app.services.thematic_areas import ThematicAreasEngine, get_thematic_engine, get_theme_names, get_theme_keywords
from app.services.analytics import AnalyticsService, get_analytics_service
from app.services.mistral_rag import MistralRAG, get_rag

__all__ = [
    'DataLoader', 'get_data_loader', 'load_all_data',
    'FacultyMatcher', 'get_faculty_matcher', 'is_current_faculty', 'get_faculty_info',
    'FAISSEngine', 'get_faiss_engine',
    'SearchEngine', 'get_search_engine', 'extract_keywords',
    'ThematicAreasEngine', 'get_thematic_engine', 'get_theme_names', 'get_theme_keywords',
    'AnalyticsService', 'get_analytics_service',
    'MistralRAG', 'get_rag',
]
