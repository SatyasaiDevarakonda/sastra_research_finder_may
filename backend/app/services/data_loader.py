"""
SASTRA Research Finder - Data Loader Service
Handles dynamic data extraction from Excel dataset.
"""

import pandas as pd
import re
import pickle
import json
import os
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple
import math

from app.core.config import (
    get_settings,
    STOPWORDS, COUNTRY_PATTERNS, SASTRA_SCHOOLS, DOCUMENT_TYPES,
    THEMATIC_AREAS, JOURNAL_QUARTILES
)


class DataLoader:
    """Loads and processes publication data from Excel."""

    def __init__(self, excel_path: Path = None, faculty_path: Path = None):
        """Initialize the data loader."""
        settings = get_settings()
        self.excel_path = excel_path or settings.EXCEL_FILE
        self.faculty_path = faculty_path or settings.FACULTY_FILE
        self.df: Optional[pd.DataFrame] = None
        self.publications: Dict[str, Dict] = {}
        self.author_profiles: Dict[str, Dict] = {}
        self.author_id_to_names: Dict[str, Set[str]] = defaultdict(set)
        self.name_to_author_ids: Dict[str, Set[str]] = defaultdict(set)

        # Dynamic extraction results
        self.years: List[int] = []
        self.schools: List[str] = []
        self.document_types: List[str] = []
        self.all_keywords: Set[str] = set()

        # Compiled regex patterns for thematic areas
        self._compiled_patterns: Dict[str, List] = {}
        for area_name, keywords in THEMATIC_AREAS.items():
            self._compiled_patterns[area_name] = [
                re.compile(r'\b' + re.escape(kw.lower()) + r'\b')
                for kw in keywords
            ]

    def load_excel(self) -> pd.DataFrame:
        """Load Excel file into DataFrame."""
        if self.df is not None:
            return self.df

        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")

        print(f"📂 Loading data from: {self.excel_path}")
        self.df = pd.read_excel(self.excel_path, engine='openpyxl')
        print(f"✓ Loaded {len(self.df)} publications")

        return self.df

    def clean_text(self, text: Any) -> str:
        """Clean and normalize text."""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def extract_author_ids(self, author_ids_str: Any) -> List[str]:
        """Extract individual author IDs from semicolon-separated string."""
        if pd.isna(author_ids_str) or not isinstance(author_ids_str, str):
            return []

        ids = []
        for aid in author_ids_str.split(';'):
            aid = aid.strip()
            if aid and aid.replace('.', '').isdigit():
                ids.append(aid)
        return ids

    def extract_author_names(self, authors_str: Any) -> List[str]:
        """Extract individual author names from semicolon-separated string."""
        if pd.isna(authors_str) or not isinstance(authors_str, str):
            return []

        names = []
        for name in authors_str.split(';'):
            name = name.strip()
            if name:
                names.append(name)
        return names

    def parse_author_full_names(self, full_names_str: Any) -> List[Tuple[str, str]]:
        """Parse 'Author full names' column."""
        if pd.isna(full_names_str) or not isinstance(full_names_str, str):
            return []

        pattern = r'([^;]+?)\s*\((\d+)\)'
        matches = re.findall(pattern, full_names_str)
        return [(name.strip(), aid) for name, aid in matches if name.strip() and aid]

    def extract_countries(self, affiliations_str: Any) -> List[str]:
        """Extract unique countries from affiliation string."""
        if pd.isna(affiliations_str) or not isinstance(affiliations_str, str):
            return []

        countries = []
        for pattern in COUNTRY_PATTERNS:
            matches = re.findall(pattern, affiliations_str, re.IGNORECASE)
            for match in matches:
                country = match.strip()
                if country.lower() in ['usa', 'united states']:
                    country = 'United States'
                elif country.lower() in ['uk', 'united kingdom']:
                    country = 'United Kingdom'
                else:
                    country = country.title()

                if country not in countries:
                    countries.append(country)

        return countries

    def extract_school(self, affiliations_str: Any) -> str:
        """Extract SASTRA school from affiliations."""
        if pd.isna(affiliations_str) or not isinstance(affiliations_str, str):
            return "Unknown"

        affiliations_lower = affiliations_str.lower()

        for school_name, keywords in SASTRA_SCHOOLS.items():
            if any(kw in affiliations_lower for kw in keywords):
                return school_name

        if 'sastra' in affiliations_lower:
            return "SASTRA (School Not Specified)"

        return "External Institution"

    def parse_keywords(self, keywords_str: Any) -> List[str]:
        """Parse keywords from semicolon-separated string."""
        if pd.isna(keywords_str) or not isinstance(keywords_str, str):
            return []

        keywords = []
        for kw in keywords_str.split(';'):
            kw = kw.strip().lower()
            if kw and len(kw) >= 2 and kw not in STOPWORDS:
                keywords.append(kw)
                self.all_keywords.add(kw)

        return keywords

    def extract_keywords_from_text(self, text: str, max_keywords: int = 50) -> List[str]:
        """Extract keywords from text content."""
        if not text:
            return []

        text = text.lower()
        words = re.findall(r'\b[a-z][a-z0-9\-]+\b', text)

        keywords = []
        seen = set()
        for word in words:
            word = word.strip('-')
            if len(word) >= 3 and word not in STOPWORDS and word not in seen:
                keywords.append(word)
                seen.add(word)

        return keywords[:max_keywords]

    def identify_thematic_areas(self, pub: Dict[str, Any]) -> List[str]:
        """Identify thematic areas for a given publication."""
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

        # Score each thematic area
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

        return matching_areas

    def get_journal_quartile(self, source: str) -> Optional[str]:
        """Get journal quartile based on source name."""
        if not source:
            return None
        
        source_lower = source.lower()
        for journal_pattern, quartile in JOURNAL_QUARTILES.items():
            if journal_pattern in source_lower:
                return quartile
        return None

    def build_publications_index(self) -> Dict[str, Dict]:
        """Build the publications index from DataFrame."""
        if self.df is None:
            self.load_excel()

        print("📊 Building publications index...")

        for idx, row in self.df.iterrows():
            # Get publication ID
            pub_id = str(row.get('EID', f'pub_{idx}')).strip()
            if not pub_id:
                pub_id = f'pub_{idx}'

            # Extract basic fields
            title = self.clean_text(row.get('Title', ''))
            abstract = self.clean_text(row.get('Abstract', ''))
            year = int(row.get('Year', 0)) if pd.notna(row.get('Year')) else 0
            citations = int(row.get('Cited by', 0)) if pd.notna(row.get('Cited by')) else 0
            source = self.clean_text(row.get('Source title', ''))
            doc_type = str(row.get('Document Type', '')).strip() if pd.notna(row.get('Document Type')) else ''
            doi = self.clean_text(row.get('DOI', ''))
            link = self.clean_text(row.get('Link', ''))

            # Check open access
            open_access = str(row.get('Open Access', '')).lower() in ['yes', 'true', '1', 'all open access']

            # Extract author information
            authors = self.clean_text(row.get('Authors', ''))
            author_ids = self.extract_author_ids(row.get('Author(s) ID', ''))
            author_names = self.extract_author_names(authors)
            affiliations = self.clean_text(row.get('Authors with affiliations', ''))

            # Parse author full names for mapping
            full_names = self.parse_author_full_names(row.get('Author full names', ''))

            # Determine author positions
            author_positions = {}
            for i, aid in enumerate(author_ids):
                if i == 0:
                    author_positions[aid] = "1st Author"
                elif i == 1:
                    author_positions[aid] = "2nd Author"
                else:
                    author_positions[aid] = "Co-Author"

            # Extract keywords
            author_keywords = self.parse_keywords(row.get('Author Keywords', ''))
            index_keywords = self.parse_keywords(row.get('Index Keywords', ''))
            all_keywords = list(set(author_keywords + index_keywords))

            # Extract geographic information
            countries = self.extract_countries(affiliations)
            school = self.extract_school(affiliations)

            # Check if international collaboration
            is_international = len([c for c in countries if c.lower() != 'india']) > 0

            # Get journal quartile
            journal_quartile = self.get_journal_quartile(source)

            # Build publication record
            pub = {
                'pub_id': pub_id,
                'title': title,
                'abstract': abstract,
                'abstract_lower': abstract.lower(),
                'year': year,
                'citations': citations,
                'source': source,
                'document_type': DOCUMENT_TYPES.get(doc_type, doc_type),
                'doi': doi,
                'link': link if link else (f"https://doi.org/{doi}" if doi else ""),
                'open_access': open_access,
                'authors': authors,
                'author_ids': author_ids,
                'author_names': author_names,
                'author_positions': author_positions,
                'affiliations': affiliations,
                'author_keywords': author_keywords,
                'index_keywords': index_keywords,
                'all_keywords': all_keywords,
                'countries': countries,
                'school': school,
                'is_international_collab': is_international,
                'journal_quartile': journal_quartile,
            }

            # Identify thematic areas
            pub['thematic_areas'] = self.identify_thematic_areas(pub)

            self.publications[pub_id] = pub

            # Track years, schools, document types
            if year and year not in self.years:
                self.years.append(year)
            if school and school not in self.schools:
                self.schools.append(school)
            if doc_type and doc_type not in self.document_types:
                self.document_types.append(doc_type)

            # Update author name mappings
            for name, aid in full_names:
                self.author_id_to_names[aid].add(name)
                self.name_to_author_ids[name.lower()].add(aid)

        self.years = sorted(self.years, reverse=True)
        self.schools = sorted(self.schools)
        self.document_types = sorted(self.document_types)

        print(f"✓ Built index for {len(self.publications)} publications")
        return self.publications

    def build_author_name_mapping(self) -> Tuple[Dict, Dict]:
        """Build author ID to name mapping."""
        if not self.publications:
            self.build_publications_index()

        for pub_id, pub in self.publications.items():
            author_ids = pub['author_ids']
            author_names = pub.get('author_names', [])

            if len(author_names) == len(author_ids):
                for name, aid in zip(author_names, author_ids):
                    self.author_id_to_names[aid].add(name)
                    name_lower = name.lower()
                    self.name_to_author_ids[name_lower].add(aid)

                    name_parts = re.split(r'[,\s\.]+', name_lower)
                    for part in name_parts:
                        part = part.strip()
                        if len(part) >= 2:
                            self.name_to_author_ids[part].add(aid)

        return dict(self.author_id_to_names), dict(self.name_to_author_ids)

    def calculate_h_index(self, citation_list: List[int]) -> int:
        """Calculate h-index from citation list."""
        if not citation_list:
            return 0
        sorted_citations = sorted(citation_list, reverse=True)
        h = 0
        for i, citations in enumerate(sorted_citations):
            if citations >= i + 1:
                h = i + 1
            else:
                break
        return h

    def calculate_g_index(self, citation_list: List[int]) -> int:
        """Calculate g-index from citation list."""
        if not citation_list:
            return 0
        sorted_citations = sorted(citation_list, reverse=True)
        cumulative = 0
        g = 0
        for i, citations in enumerate(sorted_citations):
            cumulative += citations
            if cumulative >= (i + 1) ** 2:
                g = i + 1
        return g

    def calculate_i10_index(self, citation_list: List[int]) -> int:
        """Calculate i10-index (papers with 10+ citations)."""
        return sum(1 for c in citation_list if c >= 10)

    def build_author_profiles(self) -> Dict[str, Dict]:
        """Build comprehensive author profiles."""
        if not self.publications:
            self.build_publications_index()
        if not self.author_id_to_names:
            self.build_author_name_mapping()

        print("👤 Building author profiles...")

        # Group publications by author
        author_pubs = defaultdict(list)
        for pub_id, pub in self.publications.items():
            for aid in pub['author_ids']:
                author_pubs[aid].append(pub_id)

        author_profiles = {}

        for author_id, pub_ids in author_pubs.items():
            name_variants = list(self.author_id_to_names.get(author_id, set()))
            if not name_variants:
                name_variants = ['Unknown Author']

            author_publications = []
            total_citations = 0
            all_keywords = []
            affiliations = set()
            citation_list = []
            schools = set()
            countries_collab = defaultdict(int)
            yearly_pubs = defaultdict(int)
            yearly_cites = defaultdict(int)

            for pub_id in pub_ids:
                pub = self.publications[pub_id]

                author_publications.append({
                    'pub_id': pub_id,
                    'title': pub['title'],
                    'abstract': pub['abstract'],
                    'year': pub['year'],
                    'authors': pub['authors'],
                    'source': pub['source'],
                    'citations': pub['citations'],
                    'keywords': ', '.join(pub['author_keywords'][:10]),
                    'document_type': pub['document_type'],
                    'countries': pub['countries'],
                    'school': pub['school'],
                    'doi': pub['doi'],
                    'link': pub['link'],
                    'thematic_areas': pub.get('thematic_areas', []),
                    'author_position': pub.get('author_positions', {}).get(author_id, 'Co-Author'),
                })

                total_citations += pub['citations']
                citation_list.append(pub['citations'])
                all_keywords.extend(pub['all_keywords'])
                yearly_pubs[pub['year']] += 1
                yearly_cites[pub['year']] += pub['citations']

                if pub['affiliations']:
                    affiliations.add(pub['affiliations'])
                if pub['school']:
                    schools.add(pub['school'])

                for country in pub['countries']:
                    countries_collab[country] += 1

            # Count keyword frequencies
            keyword_counts = defaultdict(int)
            for kw in all_keywords:
                keyword_counts[kw] += 1
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:30]

            # Calculate indices
            h_index = self.calculate_h_index(citation_list)
            g_index = self.calculate_g_index(citation_list)
            i10_index = self.calculate_i10_index(citation_list)

            # National vs International collaborations
            national_count = sum(1 for p in author_publications
                                 if p['countries'] and all(c.lower() == 'india' for c in p['countries']))
            international_count = sum(1 for p in author_publications
                                      if p['countries'] and any(c.lower() != 'india' for c in p['countries']))

            author_profiles[author_id] = {
                'author_id': author_id,
                'name': name_variants[0] if name_variants else 'Unknown',
                'name_variants': name_variants,
                'pub_count': len(pub_ids),
                'total_citations': total_citations,
                'h_index': h_index,
                'g_index': g_index,
                'i10_index': i10_index,
                'publications': sorted(author_publications, key=lambda x: x['year'], reverse=True),
                'pub_ids': pub_ids,
                'top_keywords': [{'keyword': k, 'count': c} for k, c in top_keywords],
                'affiliations': list(affiliations)[:5],
                'schools': list(schools),
                'citation_list': citation_list,
                'national_collabs': national_count,
                'international_collabs': international_count,
                'country_collabs': dict(countries_collab),
                'yearly_publications': dict(yearly_pubs),
                'yearly_citations': dict(yearly_cites),
                'is_current_faculty': False,  # Will be updated by FacultyMatcher
            }

        self.author_profiles = author_profiles
        print(f"✓ Built {len(author_profiles)} author profiles")
        return author_profiles

    def build_keyword_index(self) -> Dict[str, List[Tuple[str, float]]]:
        """Build inverted index from keywords to publications."""
        if not self.publications:
            self.build_publications_index()

        print("🔑 Building keyword index...")

        keyword_index = defaultdict(list)

        for pub_id, pub in self.publications.items():
            citations = pub['citations']
            base_score = 1.0 + (citations * 0.1)

            # Index author keywords (highest weight)
            for kw in pub['author_keywords']:
                keyword_index[kw].append((pub_id, base_score * 3.0))

            # Index keywords (medium weight)
            for kw in pub['index_keywords']:
                keyword_index[kw].append((pub_id, base_score * 2.0))

            # Index abstract keywords (lower weight)
            abstract_keywords = self.extract_keywords_from_text(pub['abstract'])
            for kw in abstract_keywords[:30]:
                if kw not in pub['author_keywords'] and kw not in pub['index_keywords']:
                    keyword_index[kw].append((pub_id, base_score * 1.0))

        print(f"✓ Built keyword index with {len(keyword_index)} keywords")
        return dict(keyword_index)

    def get_stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if not self.publications:
            self.build_publications_index()
        if not self.author_profiles:
            self.build_author_profiles()

        total_citations = sum(p['citations'] for p in self.publications.values())

        return {
            'total_publications': len(self.publications),
            'total_authors': len(self.author_profiles),
            'total_citations': total_citations,
            'unique_keywords': len(self.all_keywords),
            'years': self.years,
            'year_range': f"{min(self.years)}-{max(self.years)}" if self.years else "N/A",
            'schools': self.schools,
            'document_types': self.document_types,
        }

    def _get_cache_dir(self) -> Path:
        """Get the cache directory path."""
        cache_dir = self.excel_path.parent / 'cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def _get_cache_paths(self) -> tuple:
        """Get cache file and metadata file paths."""
        cache_dir = self._get_cache_dir()
        return (
            cache_dir / 'preprocessed_data.pkl',
            cache_dir / 'cache_meta.json',
        )

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        cache_file, meta_file = self._get_cache_paths()

        if not cache_file.exists() or not meta_file.exists():
            return False

        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)

            # Check source file modification times
            excel_mtime = os.path.getmtime(self.excel_path)
            faculty_mtime = os.path.getmtime(self.faculty_path) if self.faculty_path.exists() else 0

            if meta.get('excel_mtime') != excel_mtime:
                return False
            if meta.get('faculty_mtime') != faculty_mtime:
                return False

            return True
        except Exception:
            return False

    def _save_cache(self, data: Dict[str, Any]):
        """Save processed data to cache."""
        cache_file, meta_file = self._get_cache_paths()

        try:
            start = time.time()
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            excel_mtime = os.path.getmtime(self.excel_path)
            faculty_mtime = os.path.getmtime(self.faculty_path) if self.faculty_path.exists() else 0

            meta = {
                'excel_mtime': excel_mtime,
                'faculty_mtime': faculty_mtime,
                'created_at': time.time(),
                'cache_size_mb': round(cache_file.stat().st_size / (1024 * 1024), 2),
            }

            with open(meta_file, 'w') as f:
                json.dump(meta, f, indent=2)

            elapsed = time.time() - start
            print(f"✓ Cache saved ({meta['cache_size_mb']} MB) in {elapsed:.1f}s")
        except Exception as e:
            print(f"⚠ Failed to save cache: {e}")

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load processed data from cache."""
        cache_file, _ = self._get_cache_paths()

        try:
            start = time.time()
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            elapsed = time.time() - start
            print(f"✓ Cache loaded in {elapsed:.1f}s")
            return data
        except Exception as e:
            print(f"⚠ Failed to load cache: {e}")
            return None

    def _restore_from_cache(self, data: Dict[str, Any]):
        """Restore internal state from cached data."""
        self.publications = data['publications']
        self.author_profiles = data['author_profiles']
        self.author_id_to_names = defaultdict(set, {
            k: set(v) if isinstance(v, (list, set)) else v
            for k, v in data['author_id_to_names'].items()
        })
        self.name_to_author_ids = defaultdict(set, {
            k: set(v) if isinstance(v, (list, set)) else v
            for k, v in data['name_to_author_ids'].items()
        })

        stats = data.get('stats', {})
        self.years = stats.get('years', [])
        self.schools = stats.get('schools', [])
        self.document_types = stats.get('document_types', [])

    def process_all(self) -> Dict[str, Any]:
        """Process all data and return complete data structure."""
        print("=" * 60)
        print("SASTRA Research Finder - Data Processing")
        print("=" * 60)

        # Try to load from cache first
        if self._is_cache_valid():
            print("📦 Valid cache found, loading preprocessed data...")
            cached = self._load_cache()
            if cached:
                self._restore_from_cache(cached)
                stats = cached.get('stats', {})
                print(f"✓ Publications: {stats.get('total_publications', 0):,}")
                print(f"✓ Authors: {stats.get('total_authors', 0):,}")
                print(f"✓ Total Citations: {stats.get('total_citations', 0):,}")
                print(f"✓ Keywords: {stats.get('unique_keywords', 0):,}")
                print(f"✓ Year Range: {stats.get('year_range', 'N/A')}")
                print("=" * 60)
                return cached

        print("🔄 Processing data from source files...")

        # Load and process
        self.load_excel()
        self.build_publications_index()
        self.build_author_name_mapping()
        self.build_author_profiles()
        keyword_index = self.build_keyword_index()

        # Get stats
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("Processing Complete!")
        print("=" * 60)
        print(f"✓ Publications: {stats['total_publications']:,}")
        print(f"✓ Authors: {stats['total_authors']:,}")
        print(f"✓ Total Citations: {stats['total_citations']:,}")
        print(f"✓ Keywords: {stats['unique_keywords']:,}")
        print(f"✓ Year Range: {stats['year_range']}")
        print("=" * 60)

        result = {
            'publications': self.publications,
            'author_profiles': self.author_profiles,
            'author_id_to_names': {k: list(v) for k, v in self.author_id_to_names.items()},
            'name_to_author_ids': {k: list(v) for k, v in self.name_to_author_ids.items()},
            'keyword_index': keyword_index,
            'stats': stats,
        }

        # Save to cache for next time
        self._save_cache(result)

        return result


# Singleton instance
_data_loader: Optional[DataLoader] = None


def get_data_loader() -> DataLoader:
    """Get or create data loader singleton."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
    return _data_loader


def load_all_data() -> Dict[str, Any]:
    """Load all data using the singleton loader."""
    loader = get_data_loader()
    return loader.process_all()
