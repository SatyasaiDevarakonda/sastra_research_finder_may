"""
SASTRA Research Finder - Thematic Areas Service
Research domain classification and interdisciplinary team analysis.
IMPORTANT: Teams are formed ONLY from current SASTRA faculty members.
"""

import re
import pickle
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set

from app.core.config import (
    get_settings, THEMATIC_AREAS, INTERDISCIPLINARY_COMBINATIONS, POPULAR_THEME_COMBINATIONS
)
from app.services.faculty_matcher import get_faculty_matcher


class ThematicAreasEngine:
    """Engine for thematic area analysis with 100 research domains."""

    THEMATIC_AREAS = THEMATIC_AREAS

    def __init__(self, publications: Dict, author_profiles: Dict, current_faculty_author_ids: Set[str] = None):
        """
        Initialize the Thematic Areas Engine.

        Args:
            publications: Dictionary of publications
            author_profiles: Dictionary of author profiles
            current_faculty_author_ids: Set of Author IDs that belong to current SASTRA faculty
                                       Only these will be included in team formation
        """
        self.publications = publications
        self.author_profiles = author_profiles
        self.current_faculty_author_ids = current_faculty_author_ids or set()
        self.thematic_cache: Dict[str, List[str]] = {}
        self._single_rankings_cache: Optional[Dict] = None
        self._all_rankings_cache: Optional[Dict] = None
        self._interdisciplinary_cache: Optional[Dict] = None
        self._statistics_cache: Optional[Dict] = None
        self._available_themes_cache: Dict[bool, List[str]] = {}

        settings = get_settings()
        self.data_dir = settings.DATA_DIR

        # Pre-compile all regex patterns at initialization for performance
        self._compiled_patterns = {}
        for area_name, keywords in self.THEMATIC_AREAS.items():
            self._compiled_patterns[area_name] = [
                re.compile(r'\b' + re.escape(kw.lower()) + r'\b')
                for kw in keywords
            ]

    def identify_thematic_areas(self, pub: Dict[str, Any]) -> List[str]:
        """Identify thematic areas for a given publication."""
        pub_id = pub.get('pub_id', '')
        if pub_id in self.thematic_cache:
            return self.thematic_cache[pub_id]

        # Combine all text for matching
        text_parts = [
            pub.get('title', ''),
            pub.get('abstract', '')
        ]

        author_kw = pub.get('author_keywords', [])
        if isinstance(author_kw, list):
            text_parts.extend(author_kw)

        index_kw = pub.get('index_keywords', [])
        if isinstance(index_kw, list):
            text_parts.extend(index_kw)

        combined_text = ' '.join(str(t) for t in text_parts).lower()

        # Score each thematic area using pre-compiled patterns
        area_scores = defaultdict(float)
        for area_name, patterns in self._compiled_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(combined_text):
                    score += 2.0

            if score > 0:
                area_scores[area_name] = score

        # Sort by score and filter
        sorted_areas = sorted(area_scores.items(), key=lambda x: x[1], reverse=True)
        matching_areas = [area for area, score in sorted_areas if score >= 1.5]

        self.thematic_cache[pub_id] = matching_areas
        return matching_areas

    def get_single_theme_rankings(self, only_current_faculty: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Compute rankings of authors for each single thematic area.

        Args:
            only_current_faculty: If True, only include current SASTRA faculty (for team formation)
        """
        # Check in-memory cache first
        if only_current_faculty and self._single_rankings_cache:
            return self._single_rankings_cache
        elif not only_current_faculty and self._all_rankings_cache:
            return self._all_rankings_cache

        # Try loading from pickle file (includes rankings + thematic_cache + statistics)
        try:
            pickle_file = "thematic_single_rankings_faculty.pkl" if only_current_faculty else "thematic_single_rankings_all.pkl"
            cache_path = self.data_dir / pickle_file
            if cache_path.exists():
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)

                # Support both old format (dict of rankings) and new format (dict with 'rankings' key)
                if isinstance(cached_data, dict) and 'rankings' in cached_data:
                    rankings = cached_data['rankings']
                    cached_thematic = cached_data.get('thematic_cache', {})
                    cached_statistics = cached_data.get('statistics', None)
                else:
                    # Old format: just the rankings dict
                    rankings = cached_data
                    cached_thematic = {}
                    cached_statistics = None

                # Validate cache has correct number of themes
                if len(rankings) == len(self.THEMATIC_AREAS):
                    print(f"✓ Loaded {len(rankings)} theme rankings from cache ({pickle_file})")
                    if only_current_faculty:
                        self._single_rankings_cache = rankings
                    else:
                        self._all_rankings_cache = rankings
                    # Restore thematic_cache and statistics so get_theme_statistics() is instant
                    if cached_thematic:
                        self.thematic_cache.update(cached_thematic)
                        print(f"  ✓ Restored {len(cached_thematic):,} publication-theme mappings from cache")
                    if cached_statistics:
                        self._statistics_cache = cached_statistics
                        print(f"  ✓ Restored theme statistics from cache")
                    return rankings
                else:
                    print(f"⚠️ Cache has {len(rankings)} themes but config has {len(self.THEMATIC_AREAS)}, recomputing...")
        except Exception as e:
            print(f"Warning: Could not load from pickle cache: {e}")

        # Compute from scratch
        print(f"🔄 Computing theme rankings (only_current_faculty={only_current_faculty})...")

        # Track author data per theme
        author_theme_data = defaultdict(lambda: {
            'author_id': '',
            'name_variants': [],
            'total_cite_score': 0,
            'paper_count': 0,
            'papers': [],
            'themes': set(),
            'is_current_faculty': False
        })

        # Process each publication
        for pub_id, pub in self.publications.items():
            themes = self.identify_thematic_areas(pub)
            if not themes:
                continue

            cite_score = pub.get('citations', 0)

            author_ids = pub.get('author_ids', [])
            if isinstance(author_ids, str):
                author_ids = [aid.strip() for aid in author_ids.split(';') if aid.strip()]
            elif not isinstance(author_ids, list):
                author_ids = []

            for author_id in author_ids:
                if author_id not in self.author_profiles:
                    continue

                # Check if this author is current faculty
                is_current = author_id in self.current_faculty_author_ids

                # If we only want current faculty and this isn't one, skip
                if only_current_faculty and not is_current:
                    continue

                profile = self.author_profiles[author_id]
                author_data = author_theme_data[author_id]

                if not author_data['author_id']:
                    author_data['author_id'] = author_id
                    author_data['name_variants'] = profile.get('name_variants', [author_id])
                    author_data['is_current_faculty'] = is_current

                author_data['total_cite_score'] += cite_score
                author_data['paper_count'] += 1
                author_data['papers'].append({
                    'title': pub.get('title', ''),
                    'year': pub.get('year', ''),
                    'citations': cite_score,
                    'abstract': pub.get('abstract', '')[:500] if pub.get('abstract') else ''
                })
                author_data['themes'].update(themes)

        # Build rankings per theme
        theme_rankings = {}
        for theme_name in self.THEMATIC_AREAS.keys():
            theme_authors = []

            for author_id, data in author_theme_data.items():
                if theme_name in data['themes']:
                    theme_authors.append({
                        'author_id': data['author_id'],
                        'name_variants': data['name_variants'],
                        'total_cite_score': data['total_cite_score'],
                        'paper_count': data['paper_count'],
                        'papers': sorted(data['papers'], key=lambda x: x['citations'], reverse=True)[:10],
                        'primary_name': data['name_variants'][0] if data['name_variants'] else 'Unknown',
                        'is_current_faculty': data['is_current_faculty']
                    })

            # Sort by citation score
            theme_authors.sort(key=lambda x: x['total_cite_score'], reverse=True)
            theme_rankings[theme_name] = theme_authors[:15]  # Top 15 per theme

        # Store in memory cache
        if only_current_faculty:
            self._single_rankings_cache = theme_rankings
        else:
            self._all_rankings_cache = theme_rankings

        # Also compute statistics now (thematic_cache is fully populated)
        statistics = self._compute_theme_statistics()
        self._statistics_cache = statistics

        # Save rankings + thematic_cache + statistics to pickle for future fast loading
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            pickle_file = "thematic_single_rankings_faculty.pkl" if only_current_faculty else "thematic_single_rankings_all.pkl"
            cache_path = self.data_dir / pickle_file
            cache_data = {
                'rankings': theme_rankings,
                'thematic_cache': dict(self.thematic_cache),
                'statistics': statistics,
            }
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"✓ Saved theme rankings + statistics to {cache_path}")
        except Exception as e:
            print(f"Warning: Could not save to pickle cache: {e}")

        return theme_rankings

    def generate_team_for_themes(self, themes: tuple, max_teams: int = 5) -> List[Dict[str, Any]]:
        """
        Generate interdisciplinary teams for given themes.
        ONLY includes current SASTRA faculty members.

        Args:
            themes: Tuple of theme names to combine
            max_teams: Maximum number of teams to generate

        Returns:
            List of team dictionaries with members from each theme
        """
        if len(themes) < 2:
            return []

        # Get faculty-only rankings
        single_rankings = self.get_single_theme_rankings(only_current_faculty=True)

        # Check if all themes have faculty
        for theme in themes:
            if theme not in single_rankings or not single_rankings[theme]:
                return []

        teams = []
        seen_team_ids = set()

        # Generate teams by combining top faculty from each theme
        max_iterations = max(len(single_rankings[t]) for t in themes) * 2

        for rank in range(max_iterations):
            team = self._build_single_team(themes, rank, single_rankings)

            if team:
                # O(1) duplicate check using frozenset hash
                team_id = frozenset(m['author_id'] for m in team['members'])

                if team_id not in seen_team_ids:
                    teams.append(team)
                    seen_team_ids.add(team_id)

                    if len(teams) >= max_teams:
                        break

        return teams

    def _build_single_team(self, themes: tuple, rank: int, single_rankings: Dict) -> Optional[Dict]:
        """Build a single team for given themes at specific rank."""
        members = []
        total_cites = 0
        used_author_ids = set()

        faculty_matcher = get_faculty_matcher()

        from app.services.unified_scorer import get_unified_scorer
        unified_scorer = get_unified_scorer()

        if unified_scorer.search_engine is None:
            from app.services import get_search_engine
            unified_scorer.search_engine = get_search_engine()

        for theme in themes:
            faculty_list = single_rankings[theme]
            found = False

            for offset in range(len(faculty_list)):
                idx = (rank + offset) % len(faculty_list)
                candidate = faculty_list[idx]

                if candidate['author_id'] not in used_author_ids:
                    author_id = candidate['author_id']
                    faculty_info = faculty_matcher.get_faculty_info(author_id=author_id)

                    unified_score = unified_scorer.compute_faculty_score(author_id)

                    members.append({
                        'author_id': author_id,
                        'name': candidate['primary_name'],
                        'theme': theme,
                        'cite_score': candidate['total_cite_score'],
                        'paper_count': candidate['paper_count'],
                        'papers': candidate['papers'][:3],
                        'is_current_faculty': True,
                        'faculty_info': faculty_info,
                        'unified_score': unified_score
                    })
                    used_author_ids.add(author_id)
                    total_cites += candidate['total_cite_score']
                    found = True
                    break

            if not found:
                return None

        if len(members) == len(themes):
            return {
                'team_number': rank + 1,
                'members': members,
                'total_cite_score': total_cites,
                'average_cite_score': total_cites / len(members),
                'themes': list(themes)
            }
        return None

    def get_all_authors_theme_rankings(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get theme rankings including ALL authors (not just current faculty).
        Use this for general browsing, not for team formation.
        """
        return self.get_single_theme_rankings(only_current_faculty=False)

    def get_theme_statistics(self) -> Dict[str, Dict]:
        """Get statistics for each thematic area (returns from cache if available)."""
        if self._statistics_cache is not None:
            return self._statistics_cache

        result = self._compute_theme_statistics()
        self._statistics_cache = result
        return result

    def _compute_theme_statistics(self) -> Dict[str, Dict]:
        """Compute statistics for each thematic area from scratch."""
        theme_stats = defaultdict(lambda: {
            'paper_count': 0,
            'total_citations': 0,
            'author_count': set(),
            'current_faculty_count': set(),
            'years': []
        })

        for pub_id, pub in self.publications.items():
            themes = self.identify_thematic_areas(pub)

            author_ids = pub.get('author_ids', [])
            if isinstance(author_ids, str):
                author_ids = [aid.strip() for aid in author_ids.split(';') if aid.strip()]

            for theme in themes:
                theme_stats[theme]['paper_count'] += 1
                theme_stats[theme]['total_citations'] += pub.get('citations', 0)
                theme_stats[theme]['author_count'].update(author_ids)

                # Track current faculty
                for aid in author_ids:
                    if aid in self.current_faculty_author_ids:
                        theme_stats[theme]['current_faculty_count'].add(aid)

                if pub.get('year'):
                    theme_stats[theme]['years'].append(pub['year'])

        # Convert sets to counts
        result = {}
        for theme, stats in theme_stats.items():
            result[theme] = {
                'paper_count': stats['paper_count'],
                'total_citations': stats['total_citations'],
                'author_count': len(stats['author_count']),
                'current_faculty_count': len(stats['current_faculty_count']),
                'avg_citations': stats['total_citations'] / stats['paper_count'] if stats['paper_count'] > 0 else 0,
                'year_range': f"{min(stats['years'])}-{max(stats['years'])}" if stats['years'] else "N/A"
            }

        return result

    def get_popular_combinations(self) -> List[Dict]:
        """Get list of popular interdisciplinary combinations."""
        return POPULAR_THEME_COMBINATIONS

    def get_available_themes(self, only_with_faculty: bool = True) -> List[str]:
        """Get list of available theme names."""
        if only_with_faculty in self._available_themes_cache:
            return self._available_themes_cache[only_with_faculty]

        if only_with_faculty:
            rankings = self.get_single_theme_rankings(only_current_faculty=True)
            result = sorted([theme for theme, authors in rankings.items() if authors])
        else:
            result = sorted(list(self.THEMATIC_AREAS.keys()))

        self._available_themes_cache[only_with_faculty] = result
        return result


# Module-level functions
_thematic_engine: Optional[ThematicAreasEngine] = None


def get_thematic_engine(
    publications: Dict = None,
    author_profiles: Dict = None,
    current_faculty_author_ids: Set[str] = None
) -> ThematicAreasEngine:
    """Get or create thematic engine."""
    global _thematic_engine
    if _thematic_engine is None:
        if publications is None or author_profiles is None:
            raise ValueError("Must provide publications and author_profiles for first initialization")
        _thematic_engine = ThematicAreasEngine(publications, author_profiles, current_faculty_author_ids)
    return _thematic_engine


def get_theme_names() -> List[str]:
    """Get list of all available thematic area names."""
    return list(THEMATIC_AREAS.keys())


def get_theme_keywords(theme_name: str) -> List[str]:
    """Get keywords for a specific theme."""
    return THEMATIC_AREAS.get(theme_name, [])
