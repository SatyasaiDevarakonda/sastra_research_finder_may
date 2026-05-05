"""
SASTRA Research Finder - Unified Scoring Engine
Computes unified faculty scores based on publications, citations, index scores, etc.
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict

DEFAULT_WEIGHTS = {
    "w1": 0.20,  # Publications
    "w2": 0.30,  # Citations (most impactful)
    "w3": 0.25,  # H-index
    "w4": 0.10,  # POC Projects
    "w5": 0.15,  # Funded Projects
}


class UnifiedScorer:
    """Unified scoring engine for faculty evaluation."""

    def __init__(self, search_engine=None, db_session=None):
        self.search_engine = search_engine
        self.db_session = db_session
        self._component_cache: Dict[str, Dict[str, float]] = {}

    def set_db_session(self, db_session):
        """Set database session for fetching project data."""
        self.db_session = db_session

    def _fetch_project_counts(self, author_id: str) -> Dict[str, float]:
        """Fetch POC and Funded project counts from database."""
        components = {
            "poc_count": 0.0,
            "funded_count": 0.0,
        }

        db = None
        close_db = False
        if self.db_session:
            db = self.db_session
        else:
            try:
                from app.core.database import SessionLocal
                db = SessionLocal()
                close_db = True
            except Exception as e:
                print(f"Error creating DB session: {e}")
                return components

        try:
            from app.models.db_models import PocProject, FundedProject

            poc_count = db.query(PocProject).filter(
                PocProject.faculty_author_id == author_id
            ).count()
            components["poc_count"] = float(poc_count)

            funded_count = db.query(FundedProject).filter(
                FundedProject.faculty_author_id == author_id
            ).count()
            components["funded_count"] = float(funded_count)

        except Exception as e:
            print(f"Error fetching project counts: {e}")
        finally:
            if close_db and db is not None and hasattr(db, 'close'):
                db.close()

        return components

    def compute_faculty_score(
        self,
        author_id: str,
        domain: Optional[str] = None,
        weights: Dict[str, float] = None,
    ) -> float:
        """Compute unified score for a faculty member."""
        if weights is None:
            weights = DEFAULT_WEIGHTS

        components = self._get_all_components(author_id, domain)

        # Fetch project counts from DB
        project_counts = self._fetch_project_counts(author_id)
        components.update(project_counts)

        normalized = self._normalize_components(components)

        score = (
            weights["w1"] * normalized.get("pub_count", 0) +
            weights["w2"] * normalized.get("citations", 0) +
            weights["w3"] * normalized.get("h_index", 0) +
            weights["w4"] * normalized.get("poc_count", 0) +
            weights["w5"] * normalized.get("funded_count", 0)
        )

        return round(score, 4)

    def _get_all_components(self, author_id: str, domain: Optional[str] = None) -> Dict[str, float]:
        """Get all score components for a faculty member."""
        components = {
            "pub_count": 0.0,
            "citations": 0.0,
            "h_index": 0.0,
            "poc_count": 0.0,
            "funded_count": 0.0,
        }

        if self.search_engine:
            profile = self.search_engine.search_by_author_id(author_id)
            if profile:
                components["pub_count"] = float(profile.get("pub_count", 0))
                components["citations"] = float(profile.get("total_citations", 0))
                components["h_index"] = float(profile.get("h_index", 0))

        return components

    def _normalize_components(self, components: Dict[str, float]) -> Dict[str, float]:
        """Min-max normalize components."""
        normalized = {}

        for key, value in components.items():
            if key == "pub_count":
                min_val, max_val = 0, 500
            elif key == "citations":
                min_val, max_val = 0, 5000
            elif key == "h_index":
                min_val, max_val = 0, 100
            elif key == "poc_count":
                min_val, max_val = 0, 20
            elif key == "funded_count":
                min_val, max_val = 0, 10
            else:
                min_val, max_val = 0, 1

            if max_val > min_val:
                raw = (value - min_val) / (max_val - min_val)
                normalized[key] = max(0.0, min(1.0, raw))
            else:
                normalized[key] = 0.0

        return normalized

    def rank_faculty(
        self,
        domain: Optional[str] = None,
        top_k: int = 50,
        weights: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """Rank all faculty by unified score."""
        if not self.search_engine:
            return []

        faculty_scores = []

        for author_id, profile in self.search_engine.author_profiles.items():
            if not profile.get("is_current_faculty", False):
                continue

            score = self.compute_faculty_score(
                author_id=author_id,
                domain=domain,
                weights=weights
            )

            faculty_scores.append({
                "author_id": author_id,
                "name": profile.get("name_variants", [""])[0] if profile.get("name_variants") else "",
                "unified_score": score,
                "pub_count": profile.get("pub_count", 0),
                "total_citations": profile.get("total_citations", 0),
                "h_index": profile.get("h_index", 0)
            })

        faculty_scores.sort(key=lambda x: x["unified_score"], reverse=True)
        return faculty_scores[:top_k]


_unified_scorer_instance: Optional[UnifiedScorer] = None


def get_unified_scorer() -> UnifiedScorer:
    """Get or create UnifiedScorer singleton."""
    global _unified_scorer_instance
    if _unified_scorer_instance is None:
        _unified_scorer_instance = UnifiedScorer()
    return _unified_scorer_instance


def init_unified_scorer(search_engine=None) -> UnifiedScorer:
    """Initialize unified scorer with search engine."""
    global _unified_scorer_instance
    _unified_scorer_instance = UnifiedScorer(search_engine=search_engine)
    return _unified_scorer_instance