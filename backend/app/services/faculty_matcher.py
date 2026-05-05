"""
SASTRA Research Finder - Faculty Matcher Service
Matches authors with current SASTRA faculty from Faculty-List.xlsx
Only current faculty are eligible for team formation in Thematic Areas.
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from app.core.config import get_settings


class FacultyMatcher:
    """Matches publication authors with current SASTRA faculty."""

    def __init__(self, faculty_file: Path = None):
        """Initialize the faculty matcher."""
        settings = get_settings()
        self.faculty_file = faculty_file or settings.FACULTY_FILE
        self.faculty_df: Optional[pd.DataFrame] = None

        # Faculty data structures
        self.faculty_by_id: Dict[str, Dict] = {}  # Staff_ID -> faculty info
        self.faculty_by_name: Dict[str, List[str]] = defaultdict(list)  # normalized name -> [Staff_IDs]
        self.faculty_by_email: Dict[str, str] = {}  # email -> Staff_ID
        self.faculty_name_variants: Dict[str, Set[str]] = defaultdict(set)  # Staff_ID -> set of name variants

        # Author ID to Faculty mapping
        self.author_to_faculty: Dict[str, str] = {}  # Author ID -> Staff_ID
        self.faculty_to_authors: Dict[str, Set[str]] = defaultdict(set)  # Staff_ID -> set of Author IDs

        # Current faculty set for quick lookup
        self.current_faculty_ids: Set[str] = set()
        self.current_faculty_author_ids: Set[str] = set()  # Author IDs that belong to current faculty

    def load_faculty_data(self) -> pd.DataFrame:
        """Load faculty data from Excel file."""
        if self.faculty_df is not None:
            return self.faculty_df

        if not self.faculty_file.exists():
            print(f"⚠️ Faculty file not found: {self.faculty_file}")
            return pd.DataFrame()

        print(f"📂 Loading faculty data from: {self.faculty_file}")
        self.faculty_df = pd.read_excel(self.faculty_file, engine='openpyxl')
        print(f"✓ Loaded {len(self.faculty_df)} current faculty members")

        return self.faculty_df

    def normalize_name(self, name: str) -> str:
        """Normalize a name for matching."""
        if not name or pd.isna(name):
            return ""

        # Remove titles
        name = re.sub(r'^(Dr\.?|Prof\.?|Mr\.?|Ms\.?|Mrs\.?)\s*', '', name, flags=re.IGNORECASE)

        # Remove extra characters and normalize
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip().upper()

        return name

    def get_name_parts(self, name: str) -> List[str]:
        """Get all meaningful parts of a name for matching."""
        normalized = self.normalize_name(name)
        if not normalized:
            return []

        parts = normalized.split()
        result = [normalized]  # Full name
        result.extend(parts)  # Individual parts

        # Add reversed order
        if len(parts) >= 2:
            result.append(f"{parts[-1]} {' '.join(parts[:-1])}")
            result.append(f"{parts[0]} {parts[-1]}")

        return result

    def build_faculty_index(self) -> None:
        """Build faculty lookup indices."""
        if self.faculty_df is None:
            self.load_faculty_data()

        if self.faculty_df is None or len(self.faculty_df) == 0:
            return

        print("🔨 Building faculty index...")

        settings = get_settings()
        photo_base_url = settings.BACKEND_PUBLIC_URL

        for _, row in self.faculty_df.iterrows():
            staff_id = str(row.get('Staff_ID', '')).strip()
            if not staff_id:
                continue

            # Get all name columns
            name1 = str(row.get('Name', '')).strip() if pd.notna(row.get('Name')) else ''
            name2 = str(row.get('Name.1', '')).strip() if pd.notna(row.get('Name.1')) else ''
            email = str(row.get('Email', '')).strip().lower() if pd.notna(row.get('Email')) else ''
            school = str(row.get('School', '')).strip() if pd.notna(row.get('School')) else ''
            department = str(row.get('Department', '')).strip() if pd.notna(row.get('Department')) else ''
            designation = str(row.get('Designation', '')).strip() if pd.notna(row.get('Designation')) else ''
            campus = str(row.get('Campus', '')).strip() if pd.notna(row.get('Campus')) else ''

            # Extract photo filename
            photo = str(row.get('Photo', '')).strip() if pd.notna(row.get('Photo')) else ''
            # Photos are served by the backend at /staff-photos/<staff_id>.jpg.
            # If BACKEND_PUBLIC_URL is set (production), emit an absolute URL so
            # the frontend on a different origin can load it directly.
            # Otherwise emit a relative path (works in dev via Vite proxy).
            if photo:
                photo_url = f"{photo_base_url}/staff-photos/{staff_id}.jpg" if photo_base_url else f"/staff-photos/{staff_id}.jpg"
            else:
                photo_url = ''

            # Extract ORCID if available
            orcid_url = str(row.get('QRCODE URL', '')).strip() if pd.notna(row.get('QRCODE URL')) else ''
            orcid = ''
            if 'orcid.org' in orcid_url:
                orcid_match = re.search(r'(\d{4}-\d{4}-\d{4}-\d{4})', orcid_url)
                if orcid_match:
                    orcid = orcid_match.group(1)

            # Build faculty record
            faculty_info = {
                'staff_id': staff_id,
                'name': name1,
                'normalized_name': name2,
                'email': email,
                'school': school,
                'department': department,
                'designation': designation,
                'campus': campus,
                'orcid': orcid,
                'photo_url': photo_url,
                'is_current': True,
                'author_ids': []
            }

            self.faculty_by_id[staff_id] = faculty_info
            self.current_faculty_ids.add(staff_id)

            # Index by email
            if email:
                self.faculty_by_email[email] = staff_id

            # Index by name variants
            for name in [name1, name2]:
                if name:
                    self.faculty_name_variants[staff_id].add(name)
                    normalized = self.normalize_name(name)
                    if normalized:
                        self.faculty_by_name[normalized].append(staff_id)

                        # Also index parts
                        for part in self.get_name_parts(name):
                            if len(part) >= 3:
                                self.faculty_by_name[part].append(staff_id)

        print(f"✓ Built index for {len(self.faculty_by_id)} faculty members")

    def match_author_to_faculty(self, author_name: str, author_id: str = None) -> Optional[str]:
        """
        Try to match an author to a current faculty member.
        Returns Staff_ID if matched, None otherwise.
        """
        if not self.faculty_by_id:
            self.build_faculty_index()

        # Check cache first
        if author_id and author_id in self.author_to_faculty:
            return self.author_to_faculty[author_id]

        matched_staff_id = None

        # Try name matching
        if author_name:
            name_parts = self.get_name_parts(author_name)

            for part in name_parts:
                if part in self.faculty_by_name:
                    candidates = self.faculty_by_name[part]
                    if len(candidates) == 1:
                        matched_staff_id = candidates[0]
                        break
                    elif len(candidates) > 1:
                        # Try to disambiguate with more specific match
                        for candidate in candidates:
                            faculty = self.faculty_by_id[candidate]
                            faculty_normalized = self.normalize_name(faculty['name'])
                            if faculty_normalized == self.normalize_name(author_name):
                                matched_staff_id = candidate
                                break

        # Cache the result
        if matched_staff_id and author_id:
            self.author_to_faculty[author_id] = matched_staff_id
            self.faculty_to_authors[matched_staff_id].add(author_id)
            self.current_faculty_author_ids.add(author_id)
            
            # Update faculty record with author ID
            if matched_staff_id in self.faculty_by_id:
                if author_id not in self.faculty_by_id[matched_staff_id]['author_ids']:
                    self.faculty_by_id[matched_staff_id]['author_ids'].append(author_id)

        return matched_staff_id

    def is_current_faculty(self, author_id: str = None, author_name: str = None) -> bool:
        """Check if an author is a current SASTRA faculty member."""
        if author_id and author_id in self.current_faculty_author_ids:
            return True

        if author_id and author_id in self.author_to_faculty:
            return True

        # Try to match
        matched = self.match_author_to_faculty(author_name or '', author_id)
        return matched is not None

    def get_faculty_info(self, staff_id: str = None, author_id: str = None) -> Optional[Dict]:
        """Get faculty information by Staff ID or Author ID."""
        if staff_id and staff_id in self.faculty_by_id:
            return self.faculty_by_id[staff_id]

        if author_id and author_id in self.author_to_faculty:
            staff_id = self.author_to_faculty[author_id]
            return self.faculty_by_id.get(staff_id)

        return None

    def match_all_authors(self, author_profiles: Dict) -> Dict[str, str]:
        """
        Match all authors from publications to faculty.
        Returns mapping of Author ID -> Staff ID for matched authors.
        """
        if not self.faculty_by_id:
            self.build_faculty_index()

        print("🔗 Matching authors to faculty...")

        matched = 0
        total = len(author_profiles)

        for author_id, profile in author_profiles.items():
            name_variants = profile.get('name_variants', [])

            for name in name_variants:
                staff_id = self.match_author_to_faculty(name, author_id)
                if staff_id:
                    matched += 1
                    # Update the profile
                    profile['is_current_faculty'] = True
                    profile['faculty_info'] = self.get_faculty_info(staff_id=staff_id)
                    break

        print(f"✓ Matched {matched}/{total} authors to current faculty")
        return dict(self.author_to_faculty)

    def get_current_faculty_stats(self) -> Dict:
        """Get statistics about current faculty."""
        if not self.faculty_by_id:
            self.build_faculty_index()

        schools = defaultdict(int)
        departments = defaultdict(int)
        designations = defaultdict(int)

        for staff_id, info in self.faculty_by_id.items():
            if info['school']:
                schools[info['school']] += 1
            if info['department']:
                departments[info['department']] += 1
            if info['designation']:
                designations[info['designation']] += 1

        return {
            'total_faculty': len(self.faculty_by_id),
            'matched_authors': len(self.author_to_faculty),
            'schools': dict(schools),
            'departments': dict(departments),
            'designations': dict(designations)
        }

    def get_all_current_faculty(self) -> List[Dict]:
        """Get list of all current faculty members."""
        if not self.faculty_by_id:
            self.build_faculty_index()

        return list(self.faculty_by_id.values())

    def get_faculty_by_school(self, school: str) -> List[Dict]:
        """Get faculty members by school."""
        if not self.faculty_by_id:
            self.build_faculty_index()

        return [
            faculty for faculty in self.faculty_by_id.values()
            if school.lower() in faculty.get('school', '').lower()
        ]

    def get_faculty_by_department(self, department: str) -> List[Dict]:
        """Get faculty members by department."""
        if not self.faculty_by_id:
            self.build_faculty_index()

        return [
            faculty for faculty in self.faculty_by_id.values()
            if department.lower() in faculty.get('department', '').lower()
        ]


# Singleton instance
_faculty_matcher: Optional[FacultyMatcher] = None


def get_faculty_matcher() -> FacultyMatcher:
    """Get or create FacultyMatcher singleton."""
    global _faculty_matcher
    if _faculty_matcher is None:
        _faculty_matcher = FacultyMatcher()
        _faculty_matcher.build_faculty_index()
    return _faculty_matcher


def is_current_faculty(author_id: str = None, author_name: str = None) -> bool:
    """Check if author is current faculty."""
    matcher = get_faculty_matcher()
    return matcher.is_current_faculty(author_id, author_name)


def get_faculty_info(staff_id: str = None, author_id: str = None) -> Optional[Dict]:
    """Get faculty info."""
    matcher = get_faculty_matcher()
    return matcher.get_faculty_info(staff_id, author_id)
