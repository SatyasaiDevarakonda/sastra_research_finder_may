"""
SASTRA Research Finder - FAISS Semantic Search Engine
Provides semantic search capabilities using sentence transformers and FAISS.
"""

import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import warnings
from contextlib import contextmanager

from app.core.config import get_settings

# FAISS and sentence transformers imports
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    SentenceTransformer = None


@contextmanager
def suppress_model_warnings():
    """Suppress known benign model loading warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='.*can be ignored.*', category=UserWarning)
        warnings.filterwarnings('ignore', message='.*UNEXPECTED.*', category=UserWarning)
        yield


class FAISSEngine:
    """FAISS-based semantic search engine for publications."""

    def __init__(self):
        """Initialize the FAISS engine."""
        settings = get_settings()
        self.model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.pub_id_mapping: List[str] = []  # Maps FAISS index to pub_id
        self.publications: Dict[str, Dict] = {}
        self._initialized = False
        self.cache_dir = settings.CACHE_DIR
        self.embedding_model = settings.EMBEDDING_MODEL
        self.semantic_top_k = settings.SEMANTIC_SEARCH_TOP_K

        # Check availability
        if not FAISS_AVAILABLE:
            print("⚠️ FAISS not available. Install with: pip install faiss-cpu")
        if not ST_AVAILABLE:
            print("⚠️ Sentence Transformers not available. Install with: pip install sentence-transformers")

    def is_available(self) -> bool:
        """Check if FAISS engine is available."""
        return FAISS_AVAILABLE and ST_AVAILABLE

    def _load_model(self) -> bool:
        """Load the sentence transformer model."""
        if not self.is_available():
            return False

        if self.model is not None:
            return True

        try:
            print(f"📥 Loading embedding model: {self.embedding_model}")
            with suppress_model_warnings():
                self.model = SentenceTransformer(self.embedding_model)
            print(f"✓ Model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False

    def build_index(self, publications: Dict[str, Dict], force_rebuild: bool = False) -> bool:
        """
        Build FAISS index from publications.

        Args:
            publications: Dictionary of pub_id -> publication data
            force_rebuild: If True, rebuild even if cache exists

        Returns:
            True if successful
        """
        if not self.is_available():
            print("❌ FAISS or Sentence Transformers not available")
            return False

        self.publications = publications

        # Check for cached index
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self.cache_dir / "faiss_index"
        mapping_path = self.cache_dir / "pub_id_mapping.json"

        if not force_rebuild and cache_path.exists() and mapping_path.exists():
            return self._load_cached_index(cache_path, mapping_path)

        # Load model
        if not self._load_model():
            return False

        print(f"🔨 Building FAISS index for {len(publications)} publications...")

        # Prepare texts for embedding
        texts = []
        self.pub_id_mapping = []

        for pub_id, pub in publications.items():
            # Combine title, abstract, and keywords for embedding
            title = pub.get('title', '')
            abstract = pub.get('abstract', '')
            keywords = ' '.join(pub.get('author_keywords', [])[:10])

            text = f"{title} {abstract[:500]} {keywords}".strip()
            if text:
                texts.append(text)
                self.pub_id_mapping.append(pub_id)

        if not texts:
            print("❌ No texts to index")
            return False

        # Generate embeddings
        print(f"🧠 Generating embeddings for {len(texts)} documents...")
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Create FAISS index
        print("📊 Creating FAISS index...")
        dimension = embeddings.shape[1]

        # Use Inner Product for cosine similarity (since vectors are normalized)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings.astype(np.float32))

        print(f"✓ FAISS index built with {self.index.ntotal} vectors")

        # Cache the index
        self._save_cached_index(cache_path, mapping_path)

        self._initialized = True
        return True

    def _load_cached_index(self, cache_path: Path, mapping_path: Path) -> bool:
        """Load FAISS index from cache. Model loading is deferred to first search."""
        try:
            print("📂 Loading cached FAISS index...")
            self.index = faiss.read_index(str(cache_path))

            with open(mapping_path, 'r') as f:
                self.pub_id_mapping = json.load(f)

            print(f"✓ Loaded FAISS index with {self.index.ntotal} vectors (model deferred)")
            self._initialized = True
            return True
        except Exception as e:
            print(f"❌ Failed to load cached index: {e}")
            return False

    def _save_cached_index(self, cache_path: Path, mapping_path: Path) -> bool:
        """Save FAISS index to cache."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            faiss.write_index(self.index, str(cache_path))

            with open(mapping_path, 'w') as f:
                json.dump(self.pub_id_mapping, f)

            print(f"✓ Saved FAISS index to {cache_path}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to save index cache: {e}")
            return False

    def search(self, query: str, top_k: int = None) -> List[Tuple[str, float]]:
        """
        Semantic search for publications.

        Args:
            query: Search query string
            top_k: Number of results to return

        Returns:
            List of (pub_id, score) tuples sorted by relevance
        """
        if not self._initialized or self.index is None:
            return []

        if not query.strip():
            return []

        top_k = top_k or self.semantic_top_k
        top_k = min(top_k, self.index.ntotal)

        try:
            # Lazy-load model on first search
            if self.model is None and not self._load_model():
                return []

            # Encode query
            query_embedding = self.model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            # Search FAISS index
            scores, indices = self.index.search(
                query_embedding.astype(np.float32),
                top_k
            )

            # Map back to pub_ids
            results = []
            for idx, score in zip(indices[0], scores[0]):
                if idx >= 0 and idx < len(self.pub_id_mapping):
                    pub_id = self.pub_id_mapping[idx]
                    results.append((pub_id, float(score)))

            return results

        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

    def search_similar(self, pub_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find publications similar to a given publication.

        Args:
            pub_id: Publication ID to find similar papers for
            top_k: Number of results to return

        Returns:
            List of (pub_id, score) tuples
        """
        if not self._initialized or pub_id not in self.publications:
            return []

        pub = self.publications[pub_id]
        query = f"{pub.get('title', '')} {pub.get('abstract', '')[:300]}"

        # Search and filter out the query publication
        results = self.search(query, top_k + 1)
        return [(pid, score) for pid, score in results if pid != pub_id][:top_k]

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for a text string."""
        if not self._initialized or self.model is None:
            return None

        try:
            embedding = self.model.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding[0]
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return None

    def batch_search(self, queries: List[str], top_k: int = 10) -> List[List[Tuple[str, float]]]:
        """
        Batch semantic search for multiple queries.

        Args:
            queries: List of search query strings
            top_k: Number of results per query

        Returns:
            List of results for each query
        """
        if not self._initialized or self.index is None:
            return [[] for _ in queries]

        if not queries:
            return []

        try:
            # Encode all queries
            query_embeddings = self.model.encode(
                queries,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            # Search FAISS index
            top_k = min(top_k, self.index.ntotal)
            scores, indices = self.index.search(
                query_embeddings.astype(np.float32),
                top_k
            )

            # Map back to pub_ids
            all_results = []
            for query_scores, query_indices in zip(scores, indices):
                results = []
                for idx, score in zip(query_indices, query_scores):
                    if idx >= 0 and idx < len(self.pub_id_mapping):
                        pub_id = self.pub_id_mapping[idx]
                        results.append((pub_id, float(score)))
                all_results.append(results)

            return all_results

        except Exception as e:
            print(f"❌ Batch search error: {e}")
            return [[] for _ in queries]

    def clear_cache(self) -> bool:
        """Clear the cached FAISS index."""
        try:
            cache_path = self.cache_dir / "faiss_index"
            mapping_path = self.cache_dir / "pub_id_mapping.json"

            if cache_path.exists():
                cache_path.unlink()
            if mapping_path.exists():
                mapping_path.unlink()

            print("✓ FAISS cache cleared")
            return True
        except Exception as e:
            print(f"❌ Failed to clear cache: {e}")
            return False


# Singleton instance
_faiss_engine: Optional[FAISSEngine] = None


def get_faiss_engine() -> FAISSEngine:
    """Get or create FAISS engine singleton."""
    global _faiss_engine
    if _faiss_engine is None:
        _faiss_engine = FAISSEngine()
    return _faiss_engine
