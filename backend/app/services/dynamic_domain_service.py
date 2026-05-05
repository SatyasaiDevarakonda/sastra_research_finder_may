"""
SASTRA Research Finder - Dynamic Domain Service
Detect and manage dynamically discovered research domains.
"""

import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.config import get_settings, THEMATIC_AREAS
from app.models.db_models import DynamicDomain

DOMAIN_SIMILARITY_THRESHOLD = 0.45


class DynamicDomainService:
    """Service for dynamic domain detection and management."""

    def __init__(self):
        self.settings = get_settings()
        self.static_domains = list(THEMATIC_AREAS.keys())
        self._centroids: Optional[Dict[str, List[float]]] = None

    def load_static_domain_centroids(self) -> Dict[str, List[float]]:
        """Load or compute static domain centroids."""
        if self._centroids is not None:
            return self._centroids

        cache_file = self.settings.CACHE_DIR / "domain_centroids.pkl"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    self._centroids = pickle.load(f)
                return self._centroids
        except Exception as e:
            print(f"Could not load domain centroids: {e}")

        self._centroids = self._compute_static_centroids()
        
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(self._centroids, f)
        except Exception as e:
            print(f"Could not save domain centroids: {e}")

        return self._centroids

    def _compute_static_centroids(self) -> Dict[str, List[float]]:
        """Compute centroid vectors for each static domain."""
        from app.services import get_search_engine
        
        centroids = {}
        
        try:
            engine = get_search_engine()
            if not hasattr(engine, 'embedding_model') or engine.embedding_model is None:
                print("Embedding model not available for centroid computation")
                return centroids
        except Exception as e:
            print(f"Could not get search engine: {e}")
            return centroids

        for domain_name, keywords in THEMATIC_AREAS.items():
            keyword_text = " ".join(keywords)
            try:
                embedding = engine.embedding_model.encode(keyword_text)
                centroids[domain_name] = embedding.tolist()
            except Exception as e:
                print(f"Could not compute centroid for {domain_name}: {e}")

        return centroids

    def detect_new_domain(self, text: str, embedding: List[float]) -> Optional[Dict[str, Any]]:
        """Detect if text represents a new domain not in static domains."""
        if not self._centroids:
            self.load_static_domain_centroids()

        max_similarity = -1.0
        closest_domain = None

        for domain, centroid in self._centroids.items():
            similarity = self._cosine_similarity(embedding, centroid)
            if similarity > max_similarity:
                max_similarity = similarity
                closest_domain = domain

        if max_similarity < DOMAIN_SIMILARITY_THRESHOLD:
            return {
                "is_new": True,
                "similarity": max_similarity,
                "closest_domain": closest_domain,
                "text": text[:200]
            }

        return {
            "is_new": False,
            "similarity": max_similarity,
            "closest_domain": closest_domain,
            "matched_domain": closest_domain
        }

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def get_all_domains(self, db: Session) -> Dict[str, List[Dict[str, Any]]]:
        """Get all static and approved dynamic domains."""
        static = [{"name": d, "type": "static"} for d in self.static_domains]

        dynamic_query = db.query(DynamicDomain).filter(
            DynamicDomain.is_approved == True
        ).all()
        
        dynamic = [{
            "name": d.name,
            "type": "dynamic",
            "parent_static_domain": d.parent_static_domain,
            "similarity_to_parent": d.similarity_to_parent,
            "paper_count": d.paper_count,
            "project_count": d.project_count
        } for d in dynamic_query]

        return {
            "static": static,
            "dynamic": dynamic,
            "all": static + dynamic
        }

    def get_dynamic_domains(self, db: Session) -> List[Dict[str, Any]]:
        """Get only dynamic domains."""
        dynamic_query = db.query(DynamicDomain).filter(
            DynamicDomain.is_approved == True
        ).all()
        
        return [{
            "id": d.id,
            "name": d.name,
            "parent_static_domain": d.parent_static_domain,
            "similarity_to_parent": d.similarity_to_parent,
            "example_titles": d.example_titles,
            "paper_count": d.paper_count,
            "project_count": d.project_count
        } for d in dynamic_query]

    def create_dynamic_domain(
        self,
        db: Session,
        name: str,
        parent_static_domain: str,
        similarity_to_parent: float,
        example_titles: List[str],
        embedding_centroid: List[float]
    ) -> DynamicDomain:
        """Create a new dynamic domain."""
        domain = DynamicDomain(
            name=name,
            parent_static_domain=parent_static_domain,
            similarity_to_parent=similarity_to_parent,
            example_titles=example_titles[:5],
            embedding_centroid=embedding_centroid,
            paper_count=0,
            project_count=0,
            is_approved=False
        )
        db.add(domain)
        db.commit()
        db.refresh(domain)
        return domain

    def approve_dynamic_domain(self, db: Session, domain_id: int) -> Optional[DynamicDomain]:
        """Approve a dynamic domain."""
        domain = db.query(DynamicDomain).filter(DynamicDomain.id == domain_id).first()
        if domain:
            domain.is_approved = True
            db.commit()
            db.refresh(domain)
        return domain

    def delete_dynamic_domain(self, db: Session, domain_id: int) -> bool:
        """Delete a dynamic domain."""
        domain = db.query(DynamicDomain).filter(DynamicDomain.id == domain_id).first()
        if domain:
            db.delete(domain)
            db.commit()
            return True
        return False


_dynamic_domain_service: Optional[DynamicDomainService] = None


def get_dynamic_domain_service() -> DynamicDomainService:
    """Get or create DynamicDomainService singleton."""
    global _dynamic_domain_service
    if _dynamic_domain_service is None:
        _dynamic_domain_service = DynamicDomainService()
    return _dynamic_domain_service