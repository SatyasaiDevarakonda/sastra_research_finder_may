"""
SASTRA Research Finder - Search Engine Service
Combines keyword-based and FAISS semantic search for accurate results.
"""

import re
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple

from app.core.config import (
    get_settings, STOPWORDS, CITATION_BINS, CITATION_BIN_LABELS
)
from app.services.data_loader import DataLoader, get_data_loader
from app.services.faiss_engine import FAISSEngine, get_faiss_engine
from app.services.faculty_matcher import FacultyMatcher, get_faculty_matcher


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
    """Extract keywords from text for search."""
    if not text:
        return []

    text = text.lower()
    words = re.findall(r'\b[a-z][a-z0-9\-]+\b', text)

    keywords = []
    seen = set()
    for word in words:
        word = word.strip('-')
        if len(word) >= min_length and word not in STOPWORDS and word not in seen:
            keywords.append(word)
            seen.add(word)

    return keywords[:max_keywords]


class SearchEngine:
    """Main search engine combining keyword and semantic search."""

    def __init__(self):
        """Initialize the search engine."""
        self.settings = get_settings()
        self.publications: Dict[str, Dict] = {}
        self.author_profiles: Dict[str, Dict] = {}
        self.keyword_index: Dict[str, List[Tuple[str, float]]] = {}
        self.author_id_to_names: Dict[str, Set[str]] = {}
        self.name_to_author_ids: Dict[str, Set[str]] = {}
        self.stats: Dict[str, Any] = {}

        self._data_loader: Optional[DataLoader] = None
        self._faiss_engine: Optional[FAISSEngine] = None
        self._faculty_matcher: Optional[FacultyMatcher] = None
        self._initialized = False

    def initialize(self, force_reload: bool = False) -> bool:
        """Initialize the search engine with data."""
        if self._initialized and not force_reload:
            return True

        try:
            # Load data
            print("🚀 Initializing Search Engine...")
            self._data_loader = get_data_loader()
            data = self._data_loader.process_all()

            self.publications = data['publications']
            self.author_profiles = data['author_profiles']
            self.keyword_index = data['keyword_index']
            self.author_id_to_names = data['author_id_to_names']
            self.name_to_author_ids = data['name_to_author_ids']
            self.stats = data['stats']

            # Initialize Faculty Matcher and match authors
            self._faculty_matcher = get_faculty_matcher()
            self._faculty_matcher.match_all_authors(self.author_profiles)

            # Initialize FAISS engine
            self._faiss_engine = get_faiss_engine()
            if self._faiss_engine.is_available():
                self._faiss_engine.build_index(self.publications)

            self._initialized = True
            print("✓ Search engine initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize search engine: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self._initialized:
            self.initialize()

        faculty_stats = self._faculty_matcher.get_current_faculty_stats() if self._faculty_matcher else {}

        return {
            'total_publications': len(self.publications),
            'total_authors': len(self.author_profiles),
            'total_current_faculty': faculty_stats.get('total_faculty', 0),
            'matched_faculty_authors': faculty_stats.get('matched_authors', 0),
            'total_citations': sum(p['citations'] for p in self.publications.values()),
            'unique_keywords': len(self.keyword_index),
            'years': self.stats.get('years', []),
            'schools': self.stats.get('schools', []),
            'document_types': self.stats.get('document_types', []),
        }

    def _normalize_keywords(self, keywords_input: str) -> List[str]:
        """Normalize and split keyword input."""
        if not keywords_input:
            return []

        keywords = []
        for kw in keywords_input.split(','):
            kw = kw.strip().lower()
            if kw:
                keywords.append(kw)

        return keywords

    def _search_keyword_exact(self, keyword: str) -> List[Tuple[str, float]]:
        """Exact match search in keyword index."""
        return self.keyword_index.get(keyword, [])

    def _search_keyword_partial(self, keyword: str) -> List[Tuple[str, float]]:
        """Partial/substring match in keyword index."""
        results = []
        keyword_lower = keyword.lower()

        for indexed_kw, pub_list in self.keyword_index.items():
            if keyword_lower in indexed_kw or indexed_kw in keyword_lower:
                for pub_id, score in pub_list:
                    results.append((pub_id, score * 0.7))

        return results

    def _search_fulltext(self, keyword: str) -> List[Tuple[str, float]]:
        """Full-text search in abstracts and titles."""
        results = []
        keyword_lower = keyword.lower()

        for pub_id, pub in self.publications.items():
            abstract_lower = pub.get('abstract_lower', '')
            title_lower = pub.get('title', '').lower()

            abstract_count = abstract_lower.count(keyword_lower)
            title_count = title_lower.count(keyword_lower)

            if abstract_count > 0 or title_count > 0:
                score = (abstract_count * 0.5) + (title_count * 1.5)
                results.append((pub_id, score))

        return results

    def search_by_keywords(self, keywords_input: str, max_results: int = None,
                           use_semantic: bool = True) -> Dict[str, Any]:
        """
        Search publications by keywords with accurate matching.
        Combines keyword and semantic search for best results.
        """
        if not self._initialized:
            self.initialize()

        keywords = self._normalize_keywords(keywords_input)
        max_results = max_results or self.settings.MAX_SEARCH_RESULTS

        if not keywords:
            return {
                'total': 0,
                'results': [],
                'keywords_used': [],
                'total_matching_pubs': 0,
                'document_type_dist': {}
            }

        # Collect publication scores from keyword search
        pub_scores = defaultdict(float)
        pub_matched_keywords = defaultdict(set)

        for keyword in keywords:
            # Exact match (highest priority)
            for pub_id, score in self._search_keyword_exact(keyword):
                pub_scores[pub_id] += score * 2.0
                pub_matched_keywords[pub_id].add(keyword)

            # Partial match
            for pub_id, score in self._search_keyword_partial(keyword):
                if keyword not in pub_matched_keywords[pub_id]:
                    pub_scores[pub_id] += score
                    pub_matched_keywords[pub_id].add(keyword)

            # Full-text search
            for pub_id, score in self._search_fulltext(keyword):
                if keyword not in pub_matched_keywords[pub_id]:
                    pub_scores[pub_id] += score * 0.5
                    pub_matched_keywords[pub_id].add(keyword)

        # Add semantic search results
        if use_semantic and self._faiss_engine and self._faiss_engine._initialized:
            query = ' '.join(keywords)
            semantic_results = self._faiss_engine.search(query, top_k=50)

            for pub_id, score in semantic_results:
                pub_scores[pub_id] += score * 3.0

        # Aggregate by author
        author_results = defaultdict(lambda: {
            'author_id': '',
            'name_variants': [],
            'matching_papers': 0,
            'total_score': 0.0,
            'total_citations': 0,
            'pub_ids': [],
            'top_keywords': [],
            'is_current_faculty': False
        })

        for pub_id, score in pub_scores.items():
            pub = self.publications.get(pub_id)
            if not pub:
                continue

            for author_id in pub.get('author_ids', []):
                profile = self.author_profiles.get(author_id, {})
                author_results[author_id]['author_id'] = author_id
                author_results[author_id]['name_variants'] = profile.get('name_variants', [])
                author_results[author_id]['matching_papers'] += 1
                author_results[author_id]['total_score'] += score
                author_results[author_id]['total_citations'] += pub.get('citations', 0)
                author_results[author_id]['pub_ids'].append(pub_id)
                author_results[author_id]['is_current_faculty'] = profile.get('is_current_faculty', False)

        # Add top keywords and photo_url to each author
        for author_id, result in author_results.items():
            profile = self.author_profiles.get(author_id, {})
            top_kw = profile.get('top_keywords', [])
            result['top_keywords'] = [k['keyword'] for k in top_kw[:5]] if isinstance(top_kw, list) else []
            # Add photo_url from faculty matcher
            if self._faculty_matcher:
                faculty_info = self._faculty_matcher.get_faculty_info(author_id=author_id)
                result['photo_url'] = faculty_info.get('photo_url', '') if faculty_info else ''
            else:
                result['photo_url'] = ''

        # Sort results
        sorted_results = sorted(
            author_results.values(),
            key=lambda x: (x['total_score'], x['total_citations']),
            reverse=True
        )[:max_results]

        # Calculate document type distribution
        doc_type_dist = defaultdict(int)
        for pub_id in pub_scores.keys():
            pub = self.publications.get(pub_id)
            if pub:
                doc_type_dist[pub.get('document_type', 'Unknown')] += 1

        return {
            'total': len(sorted_results),
            'results': sorted_results,
            'keywords_used': keywords,
            'total_matching_pubs': len(pub_scores),
            'document_type_dist': dict(doc_type_dist)
        }

    def search_by_author_id(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Search for an author by their ID."""
        if not self._initialized:
            self.initialize()

        return self.author_profiles.get(author_id)

    def search_by_author_name(self, name: str) -> List[Dict[str, Any]]:
        """Search for authors by name."""
        if not self._initialized:
            self.initialize()

        name_lower = name.lower()
        matching_ids = set()

        # Check exact matches
        if name_lower in self.name_to_author_ids:
            matching_ids.update(self.name_to_author_ids[name_lower])

        # Check partial matches
        for indexed_name, author_ids in self.name_to_author_ids.items():
            if name_lower in indexed_name or indexed_name in name_lower:
                matching_ids.update(author_ids)

        results = []
        for author_id in matching_ids:
            profile = self.author_profiles.get(author_id)
            if profile:
                results.append(profile)

        results.sort(key=lambda x: x.get('pub_count', 0), reverse=True)
        return results

    def semantic_search(self, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
        """Perform semantic search."""
        if not self._initialized:
            self.initialize()

        if not self._faiss_engine or not self._faiss_engine._initialized:
            return []

        results = self._faiss_engine.search(query, top_k)

        search_results = []
        for pub_id, score in results:
            pub = self.publications.get(pub_id)
            if pub:
                search_results.append({
                    **pub,
                    'relevance_score': score
                })

        return search_results

    def get_similar_publications(self, pub_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Find similar publications."""
        if not self._initialized:
            self.initialize()

        if not self._faiss_engine or not self._faiss_engine._initialized:
            return []

        results = self._faiss_engine.search_similar(pub_id, top_k)

        similar_pubs = []
        for similar_id, score in results:
            pub = self.publications.get(similar_id)
            if pub:
                similar_pubs.append({
                    **pub,
                    'similarity_score': score
                })

        return similar_pubs

    def get_rag_context(self, skills: List[str], max_abstracts: int = None) -> List[Dict[str, Any]]:
        """Get relevant publications for RAG analysis."""
        if not self._initialized:
            self.initialize()

        max_abstracts = max_abstracts or self.settings.MAX_RAG_CONTEXT

        if self._faiss_engine and self._faiss_engine._initialized:
            query = ' '.join(skills)
            semantic_results = self._faiss_engine.search(query, top_k=max_abstracts * 2)

            context = []
            for pub_id, score in semantic_results:
                pub = self.publications.get(pub_id)
                if pub and pub.get('abstract'):
                    first_author_id = pub['author_ids'][0] if pub['author_ids'] else 'Unknown'
                    context.append({
                        'pub_id': pub_id,
                        'title': pub['title'],
                        'abstract': pub['abstract'],
                        'authors': pub['authors'],
                        'author_id': first_author_id,
                        'year': pub['year'],
                        'keywords': pub['author_keywords'][:10],
                        'citations': pub['citations'],
                        'relevance_score': score,
                        'link': pub.get('link', ''),
                        'doi': pub.get('doi', ''),
                    })

                if len(context) >= max_abstracts:
                    break

            return context

        # Fallback to keyword search
        search_results = self.search_by_keywords(', '.join(skills), max_results=50)
        context = []
        seen_pubs = set()

        for author_result in search_results.get('results', [])[:20]:
            for pub_id in author_result.get('pub_ids', [])[:5]:
                if pub_id in seen_pubs:
                    continue
                seen_pubs.add(pub_id)

                pub = self.publications.get(pub_id)
                if pub and pub.get('abstract'):
                    context.append({
                        'pub_id': pub_id,
                        'title': pub['title'],
                        'abstract': pub['abstract'],
                        'authors': pub['authors'],
                        'year': pub['year'],
                        'citations': pub['citations'],
                        'link': pub.get('link', ''),
                        'doi': pub.get('doi', ''),
                    })

                if len(context) >= max_abstracts:
                    break

        context.sort(key=lambda x: (x['citations'], x.get('year', 0)), reverse=True)
        return context[:max_abstracts]

    def get_citation_histogram_data(self, author_id: str) -> Dict[str, Any]:
        """Get citation histogram data for an author."""
        profile = self.search_by_author_id(author_id)
        if not profile:
            return {'citation_list': [], 'bins': [], 'counts': []}

        citation_list = profile.get('citation_list', [])
        if not citation_list:
            return {'citation_list': [], 'bins': [], 'counts': []}

        max_cite = max(citation_list) if citation_list else 0
        counts = [0] * len(CITATION_BIN_LABELS)

        for cite in citation_list:
            for i, (low, high) in enumerate(CITATION_BINS):
                if low <= cite < high:
                    counts[i] += 1
                    break

        return {
            'citation_list': citation_list,
            'bins': CITATION_BIN_LABELS,
            'counts': counts,
            'total_pubs': len(citation_list),
            'avg_citations': sum(citation_list) / len(citation_list) if citation_list else 0,
            'max_citations': max_cite
        }

    def get_publications_by_filter(self, year: int = None, school: str = None,
                                   doc_type: str = None, thematic_area: str = None,
                                   is_international: bool = None, limit: int = 100) -> List[Dict]:
        """Get publications filtered by various criteria."""
        if not self._initialized:
            self.initialize()

        results = []

        for pub in self.publications.values():
            if year and pub['year'] != year:
                continue
            if school and school not in pub.get('school', ''):
                continue
            if doc_type and pub.get('document_type', '') != doc_type:
                continue
            if thematic_area and thematic_area not in pub.get('thematic_areas', []):
                continue
            if is_international is not None and pub.get('is_international_collab') != is_international:
                continue

            results.append(pub)

        results.sort(key=lambda x: (x['year'], x['citations']), reverse=True)
        return results[:limit]

    def get_latest_publications(self, limit: int = 50) -> List[Dict]:
        """Get the most recent publications."""
        if not self._initialized:
            self.initialize()

        all_pubs = list(self.publications.values())
        all_pubs.sort(key=lambda x: (x['year'], x['citations']), reverse=True)
        return all_pubs[:limit]

    def get_top_keywords(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top keywords across all publications."""
        keyword_counts = defaultdict(int)

        for pub in self.publications.values():
            for kw in pub.get('author_keywords', []):
                keyword_counts[kw] += 3
            for kw in pub.get('index_keywords', []):
                keyword_counts[kw] += 2

        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{'keyword': k, 'count': c} for k, c in sorted_keywords]

    def get_top_authors(self, limit: int = 20, only_current_faculty: bool = False) -> List[Dict[str, Any]]:
        """Get top authors by publication count."""
        author_data = []

        for author_id, profile in self.author_profiles.items():
            if only_current_faculty and not profile.get('is_current_faculty', False):
                continue

            author_data.append({
                'author_id': author_id,
                'name': ', '.join(profile.get('name_variants', ['Unknown'])[:2]),
                'pub_count': profile.get('pub_count', 0),
                'total_citations': profile.get('total_citations', 0),
                'h_index': profile.get('h_index', 0),
                'is_current_faculty': profile.get('is_current_faculty', False),
                'top_keywords': [k['keyword'] for k in profile.get('top_keywords', [])[:3]]
            })

        author_data.sort(key=lambda x: x['pub_count'], reverse=True)
        return author_data[:limit]


# Singleton instance
_engine_instance: Optional[SearchEngine] = None


def get_search_engine() -> SearchEngine:
    """Get or create SearchEngine singleton."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SearchEngine()
        _engine_instance.initialize()
    return _engine_instance
