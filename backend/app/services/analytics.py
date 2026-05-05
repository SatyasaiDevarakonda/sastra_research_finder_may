"""
SASTRA Research Finder - Analytics Service
Provides comprehensive analytics and SciVal-like metrics.
"""

from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import math

from app.core.config import get_settings, THEMATIC_AREAS


class AnalyticsService:
    """Service for computing research analytics and metrics."""

    def __init__(self, publications: Dict, author_profiles: Dict, faculty_matcher=None):
        """Initialize the analytics service."""
        self.publications = publications
        self.author_profiles = author_profiles
        self.faculty_matcher = faculty_matcher
        self._cache: Dict[str, Any] = {}

    def _cached(self, key: str, compute_fn):
        """Return cached result or compute and cache it."""
        if key not in self._cache:
            self._cache[key] = compute_fn()
        return self._cache[key]

    def get_publication_trends(self) -> Dict[str, Any]:
        """Get publication trends over time."""
        return self._cached('publication_trends', self._compute_publication_trends)

    def _compute_publication_trends(self) -> Dict[str, Any]:
        yearly_pubs = defaultdict(int)
        yearly_cites = defaultdict(int)

        for pub in self.publications.values():
            year = pub.get('year', 0)
            if year > 0:
                yearly_pubs[year] += 1
                yearly_cites[year] += pub.get('citations', 0)

        years = sorted(yearly_pubs.keys())
        pub_counts = [yearly_pubs[y] for y in years]
        cite_counts = [yearly_cites[y] for y in years]

        # Calculate cumulative values
        cumulative_pubs = []
        cumulative_cites = []
        running_pubs = 0
        running_cites = 0

        for i, year in enumerate(years):
            running_pubs += pub_counts[i]
            running_cites += cite_counts[i]
            cumulative_pubs.append(running_pubs)
            cumulative_cites.append(running_cites)

        return {
            'years': years,
            'publication_counts': pub_counts,
            'citation_counts': cite_counts,
            'cumulative_publications': cumulative_pubs,
            'cumulative_citations': cumulative_cites
        }

    def get_document_type_distribution(self) -> Dict[str, Any]:
        """Get document type distribution."""
        return self._cached('document_type_distribution', self._compute_document_type_distribution)

    def _compute_document_type_distribution(self) -> Dict[str, Any]:
        type_counts = defaultdict(int)

        for pub in self.publications.values():
            doc_type = pub.get('document_type', 'Unknown')
            type_counts[doc_type] += 1

        total = sum(type_counts.values())
        types = list(type_counts.keys())
        counts = [type_counts[t] for t in types]
        percentages = [c / total * 100 if total > 0 else 0 for c in counts]

        # Sort by count
        sorted_data = sorted(zip(types, counts, percentages), key=lambda x: x[1], reverse=True)
        types, counts, percentages = zip(*sorted_data) if sorted_data else ([], [], [])

        return {
            'types': list(types),
            'counts': list(counts),
            'percentages': list(percentages)
        }

    def get_school_comparison(self) -> Dict[str, Any]:
        """Get school-wise comparison data."""
        return self._cached('school_comparison', self._compute_school_comparison)

    def _compute_school_comparison(self) -> Dict[str, Any]:
        school_data = defaultdict(lambda: {
            'pub_count': 0,
            'citations': 0,
            'authors': set(),
            'faculty': set()
        })

        for pub in self.publications.values():
            school = pub.get('school', 'Unknown')
            school_data[school]['pub_count'] += 1
            school_data[school]['citations'] += pub.get('citations', 0)
            school_data[school]['authors'].update(pub.get('author_ids', []))

        # Add faculty counts
        if self.faculty_matcher:
            for staff_id, info in self.faculty_matcher.faculty_by_id.items():
                school = info.get('school', 'Unknown')
                if school:
                    school_data[school]['faculty'].add(staff_id)

        schools = sorted(school_data.keys())
        pub_counts = [school_data[s]['pub_count'] for s in schools]
        cite_counts = [school_data[s]['citations'] for s in schools]
        avg_cites = [c / p if p > 0 else 0 for c, p in zip(cite_counts, pub_counts)]
        faculty_counts = [len(school_data[s]['faculty']) for s in schools]

        return {
            'schools': schools,
            'publication_counts': pub_counts,
            'citation_counts': cite_counts,
            'avg_citations': avg_cites,
            'faculty_counts': faculty_counts
        }

    def get_geographic_collaboration(self) -> Dict[str, Any]:
        """Get geographic collaboration statistics."""
        return self._cached('geographic_collaboration', self._compute_geographic_collaboration)

    def _compute_geographic_collaboration(self) -> Dict[str, Any]:
        country_counts = defaultdict(int)
        total_pubs_with_countries = 0
        international_pubs = 0

        for pub in self.publications.values():
            countries = pub.get('countries', [])
            if countries:
                total_pubs_with_countries += 1
                has_international = any(c.lower() != 'india' for c in countries)
                if has_international:
                    international_pubs += 1

                for country in countries:
                    if country.lower() != 'india':
                        country_counts[country] += 1

        # Sort by count
        sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
        countries = [c for c, _ in sorted_countries[:30]]
        counts = [country_counts[c] for c in countries]

        international_pct = (international_pubs / total_pubs_with_countries * 100) if total_pubs_with_countries > 0 else 0

        return {
            'countries': countries,
            'collaboration_counts': counts,
            'international_percentage': international_pct,
            'total_international_publications': international_pubs,
            'total_publications_with_countries': total_pubs_with_countries
        }

    def get_collaboration_network(self, min_weight: int = 2, max_nodes: int = 100) -> Dict[str, Any]:
        """Get co-authorship network data."""
        cache_key = f'collaboration_network_{min_weight}_{max_nodes}'
        return self._cached(cache_key, lambda: self._compute_collaboration_network(min_weight, max_nodes))

    def _compute_collaboration_network(self, min_weight: int, max_nodes: int) -> Dict[str, Any]:
        # Count co-authorships
        coauthor_counts = defaultdict(int)
        author_pub_counts = defaultdict(int)

        for pub in self.publications.values():
            author_ids = pub.get('author_ids', [])

            for author_id in author_ids:
                author_pub_counts[author_id] += 1

            # Create edges for all author pairs
            for i in range(len(author_ids)):
                for j in range(i + 1, len(author_ids)):
                    pair = tuple(sorted([author_ids[i], author_ids[j]]))
                    coauthor_counts[pair] += 1

        # Filter to significant collaborations
        significant_pairs = [(pair, count) for pair, count in coauthor_counts.items() if count >= min_weight]
        significant_pairs.sort(key=lambda x: x[1], reverse=True)

        # Get unique authors from significant pairs
        significant_authors = set()
        for (a1, a2), _ in significant_pairs:
            significant_authors.add(a1)
            significant_authors.add(a2)

        # Limit nodes
        if len(significant_authors) > max_nodes:
            # Keep top authors by publication count
            sorted_authors = sorted(significant_authors, key=lambda x: author_pub_counts[x], reverse=True)
            significant_authors = set(sorted_authors[:max_nodes])

        # Build nodes
        nodes = []
        for author_id in significant_authors:
            profile = self.author_profiles.get(author_id, {})
            nodes.append({
                'id': author_id,
                'name': profile.get('name_variants', ['Unknown'])[0] if profile.get('name_variants') else 'Unknown',
                'pub_count': author_pub_counts[author_id],
                'is_faculty': profile.get('is_current_faculty', False)
            })

        # Build edges
        edges = []
        for (a1, a2), weight in significant_pairs:
            if a1 in significant_authors and a2 in significant_authors:
                edges.append({
                    'source': a1,
                    'target': a2,
                    'weight': weight
                })

        return {
            'nodes': nodes,
            'edges': edges
        }

    def get_journal_analytics(self, top_n: int = 20) -> Dict[str, Any]:
        """Get journal analytics."""
        cache_key = f'journal_analytics_{top_n}'
        return self._cached(cache_key, lambda: self._compute_journal_analytics(top_n))

    def _compute_journal_analytics(self, top_n: int) -> Dict[str, Any]:
        journal_data = defaultdict(lambda: {
            'count': 0,
            'citations': 0,
            'quartile': None
        })

        for pub in self.publications.values():
            source = pub.get('source', 'Unknown')
            if source:
                journal_data[source]['count'] += 1
                journal_data[source]['citations'] += pub.get('citations', 0)
                if pub.get('journal_quartile'):
                    journal_data[source]['quartile'] = pub['journal_quartile']

        # Sort by count
        sorted_journals = sorted(journal_data.items(), key=lambda x: x[1]['count'], reverse=True)[:top_n]

        journals = [j for j, _ in sorted_journals]
        counts = [journal_data[j]['count'] for j in journals]

        # Quartile distribution
        quartile_dist = defaultdict(int)
        for journal, data in journal_data.items():
            if data['quartile']:
                quartile_dist[data['quartile']] += data['count']

        return {
            'journals': journals,
            'counts': counts,
            'quartile_distribution': dict(quartile_dist)
        }

    def get_impact_metrics(self, entity_type: str = 'institution', entity_id: str = None) -> Dict[str, Any]:
        """Calculate impact metrics for an entity (institution, school, or author)."""
        cache_key = f'impact_metrics_{entity_type}_{entity_id}'
        return self._cached(cache_key, lambda: self._compute_impact_metrics(entity_type, entity_id))

    def _compute_impact_metrics(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        # Filter publications based on entity
        if entity_type == 'author' and entity_id:
            pubs = [p for p in self.publications.values() if entity_id in p.get('author_ids', [])]
        elif entity_type == 'school' and entity_id:
            pubs = [p for p in self.publications.values() if entity_id in p.get('school', '')]
        else:
            pubs = list(self.publications.values())

        if not pubs:
            return {
                'total_citations': 0,
                'avg_citations_per_paper': 0,
                'h_index': 0,
                'papers_in_top_1_percent': 0,
                'papers_in_top_10_percent': 0,
                'papers_in_top_25_percent': 0,
                'international_collab_percentage': 0
            }

        # Basic metrics
        total_citations = sum(p.get('citations', 0) for p in pubs)
        avg_citations = total_citations / len(pubs) if pubs else 0

        # H-index
        citations_list = sorted([p.get('citations', 0) for p in pubs], reverse=True)
        h_index = 0
        for i, c in enumerate(citations_list):
            if c >= i + 1:
                h_index = i + 1
            else:
                break

        # Citation percentiles (simplified - in real SciVal, this would be field-normalized)
        sorted_cites = sorted(citations_list, reverse=True)
        n = len(sorted_cites)

        top_1_threshold = sorted_cites[int(n * 0.01)] if n > 100 else sorted_cites[0]
        top_10_threshold = sorted_cites[int(n * 0.10)] if n > 10 else sorted_cites[0]
        top_25_threshold = sorted_cites[int(n * 0.25)] if n > 4 else sorted_cites[0]

        papers_top_1 = sum(1 for c in citations_list if c >= top_1_threshold)
        papers_top_10 = sum(1 for c in citations_list if c >= top_10_threshold)
        papers_top_25 = sum(1 for c in citations_list if c >= top_25_threshold)

        # International collaboration percentage
        international_count = sum(1 for p in pubs if p.get('is_international_collab', False))
        international_pct = (international_count / len(pubs) * 100) if pubs else 0

        return {
            'total_citations': total_citations,
            'total_publications': len(pubs),
            'avg_citations_per_paper': round(avg_citations, 2),
            'h_index': h_index,
            'papers_in_top_1_percent': papers_top_1,
            'papers_in_top_10_percent': papers_top_10,
            'papers_in_top_25_percent': papers_top_25,
            'international_collab_percentage': round(international_pct, 2)
        }

    def get_thematic_distribution(self) -> Dict[str, Any]:
        """Get publication distribution across thematic areas."""
        return self._cached('thematic_distribution', self._compute_thematic_distribution)

    def _compute_thematic_distribution(self) -> Dict[str, Any]:
        theme_counts = defaultdict(int)
        theme_citations = defaultdict(int)

        for pub in self.publications.values():
            themes = pub.get('thematic_areas', [])
            for theme in themes:
                theme_counts[theme] += 1
                theme_citations[theme] += pub.get('citations', 0)

        # Sort by count
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)

        themes = [t for t, _ in sorted_themes]
        counts = [theme_counts[t] for t in themes]
        citations = [theme_citations[t] for t in themes]

        return {
            'themes': themes,
            'publication_counts': counts,
            'citation_counts': citations
        }

    def get_open_access_statistics(self) -> Dict[str, Any]:
        """Get open access statistics."""
        return self._cached('open_access_statistics', self._compute_open_access_statistics)

    def _compute_open_access_statistics(self) -> Dict[str, Any]:
        oa_count = sum(1 for p in self.publications.values() if p.get('open_access', False))
        total = len(self.publications)

        return {
            'open_access_count': oa_count,
            'closed_access_count': total - oa_count,
            'open_access_percentage': (oa_count / total * 100) if total > 0 else 0
        }

    def get_author_productivity_distribution(self) -> Dict[str, Any]:
        """Get distribution of author productivity (publications per author)."""
        return self._cached('author_productivity', self._compute_author_productivity_distribution)

    def _compute_author_productivity_distribution(self) -> Dict[str, Any]:
        pub_counts = [p.get('pub_count', 0) for p in self.author_profiles.values()]

        # Create bins
        bins = [1, 2, 5, 10, 20, 50, float('inf')]
        bin_labels = ['1', '2-4', '5-9', '10-19', '20-49', '50+']
        bin_counts = [0] * len(bin_labels)

        for count in pub_counts:
            for i in range(len(bins) - 1):
                if bins[i] <= count < bins[i + 1]:
                    bin_counts[i] += 1
                    break

        return {
            'bins': bin_labels,
            'counts': bin_counts,
            'total_authors': len(pub_counts),
            'avg_publications_per_author': sum(pub_counts) / len(pub_counts) if pub_counts else 0
        }

    def get_citation_distribution(self) -> Dict[str, Any]:
        """Get distribution of citations across publications."""
        return self._cached('citation_distribution', self._compute_citation_distribution)

    def _compute_citation_distribution(self) -> Dict[str, Any]:
        citations = [p.get('citations', 0) for p in self.publications.values()]

        if not citations:
            return {'bins': [], 'counts': [], 'uncited_count': 0, 'highly_cited_count': 0}

        # Create bins
        bins = [0, 1, 5, 10, 25, 50, 100, 500, float('inf')]
        bin_labels = ['0', '1-4', '5-9', '10-24', '25-49', '50-99', '100-499', '500+']
        bin_counts = [0] * len(bin_labels)

        for cite in citations:
            for i in range(len(bins) - 1):
                if bins[i] <= cite < bins[i + 1]:
                    bin_counts[i] += 1
                    break

        uncited = sum(1 for c in citations if c == 0)
        highly_cited = sum(1 for c in citations if c >= 100)

        return {
            'bins': bin_labels,
            'counts': bin_counts,
            'uncited_count': uncited,
            'uncited_percentage': (uncited / len(citations) * 100) if citations else 0,
            'highly_cited_count': highly_cited,
            'highly_cited_percentage': (highly_cited / len(citations) * 100) if citations else 0
        }

    def get_yearly_growth_rate(self) -> Dict[str, Any]:
        """Calculate yearly growth rates."""
        return self._cached('yearly_growth_rate', self._compute_yearly_growth_rate)

    def _compute_yearly_growth_rate(self) -> Dict[str, Any]:
        trends = self.get_publication_trends()
        years = trends['years']
        pub_counts = trends['publication_counts']

        if len(years) < 2:
            return {'years': [], 'growth_rates': []}

        growth_rates = []
        for i in range(1, len(years)):
            if pub_counts[i - 1] > 0:
                rate = ((pub_counts[i] - pub_counts[i - 1]) / pub_counts[i - 1]) * 100
            else:
                rate = 0
            growth_rates.append(round(rate, 2))

        return {
            'years': years[1:],
            'growth_rates': growth_rates
        }

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics summary."""
        return self._cached('comprehensive_stats', self._compute_comprehensive_stats)

    def _compute_comprehensive_stats(self) -> Dict[str, Any]:
        total_pubs = len(self.publications)
        total_authors = len(self.author_profiles)
        total_citations = sum(p.get('citations', 0) for p in self.publications.values())

        # Current faculty count
        faculty_count = 0
        matched_faculty = 0
        if self.faculty_matcher:
            faculty_count = len(self.faculty_matcher.faculty_by_id)
            matched_faculty = len(self.faculty_matcher.author_to_faculty)

        # Year range
        years = [p.get('year', 0) for p in self.publications.values() if p.get('year', 0) > 0]
        year_range = f"{min(years)}-{max(years)}" if years else "N/A"

        # Get unique values
        schools = set(p.get('school', '') for p in self.publications.values() if p.get('school'))
        doc_types = set(p.get('document_type', '') for p in self.publications.values() if p.get('document_type'))

        return {
            'total_publications': total_pubs,
            'total_authors': total_authors,
            'total_citations': total_citations,
            'total_current_faculty': faculty_count,
            'matched_faculty_authors': matched_faculty,
            'unique_keywords': sum(len(p.get('author_keywords', [])) for p in self.publications.values()),
            'year_range': year_range,
            'schools': sorted(list(schools)),
            'document_types': sorted(list(doc_types)),
            'avg_citations_per_paper': round(total_citations / total_pubs, 2) if total_pubs > 0 else 0,
            'avg_papers_per_author': round(total_pubs / total_authors, 2) if total_authors > 0 else 0
        }


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service(
    publications: Dict = None,
    author_profiles: Dict = None,
    faculty_matcher=None
) -> AnalyticsService:
    """Get or create analytics service."""
    global _analytics_service
    if _analytics_service is None:
        if publications is None or author_profiles is None:
            raise ValueError("Must provide publications and author_profiles for first initialization")
        _analytics_service = AnalyticsService(publications, author_profiles, faculty_matcher)
    return _analytics_service
