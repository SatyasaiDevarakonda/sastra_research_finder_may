"""
SASTRA Research Finder - Authors API Routes
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

from app.services import get_search_engine, get_faculty_matcher, get_rag
from app.models.schemas import (
    AuthorProfile, AuthorSearchResult, FacultyInfo, FacultyStats
)

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.get("/", response_model=List[AuthorSearchResult])
async def search_authors(
    name: Optional[str] = None,
    author_id: Optional[str] = None,
    only_faculty: bool = False,
    limit: int = Query(50, ge=1, le=2000)
):
    """
    Search authors by name, author ID, or list all authors.
    Also includes current SASTRA faculty who have no indexed publications —
    so the full 735 faculty from Faculty-List.xlsx are always visible in the
    "Current Faculty" tab and in name searches.
    """
    engine = get_search_engine()
    faculty_matcher = get_faculty_matcher()

    if author_id:
        profile = engine.search_by_author_id(author_id)
        if profile:
            results = [profile]
        else:
            results = [
                p for aid, p in engine.author_profiles.items()
                if author_id in aid
            ]
    elif name:
        results = engine.search_by_author_name(name)
    else:
        results = list(engine.author_profiles.values())

    if only_faculty:
        # Collapse to one row per faculty: keep the author profile with the highest
        # pub_count for each staff_id, then add faculty-only entries for unmatched
        # faculty so all 735 faculty appear exactly once.
        best_by_staff: dict = {}
        for r in results:
            if not r.get('is_current_faculty'):
                continue
            fi = faculty_matcher.get_faculty_info(author_id=r.get('author_id', ''))
            staff_id = fi.get('staff_id') if fi else None
            if not staff_id:
                continue
            existing = best_by_staff.get(staff_id)
            if not existing or (r.get('pub_count', 0) > existing.get('pub_count', 0)):
                best_by_staff[staff_id] = r

        needle = (name or '').strip().lower()
        needle_id = (author_id or '').strip().lower()

        def _faculty_matches_query(faculty: dict) -> bool:
            if not name and not author_id:
                return True
            if needle:
                hay = ' '.join([
                    faculty.get('name') or '',
                    faculty.get('normalized_name') or '',
                    faculty.get('email') or '',
                    faculty.get('department') or '',
                    faculty.get('designation') or '',
                ]).lower()
                if needle in hay:
                    return True
            if needle_id and needle_id in (faculty.get('staff_id') or '').lower():
                return True
            return False

        results = list(best_by_staff.values())

        # Add faculty-only entries (those with no matched author profile yet)
        represented = set(best_by_staff.keys())
        for staff_id, faculty in faculty_matcher.faculty_by_id.items():
            if staff_id in represented:
                continue
            if not _faculty_matches_query(faculty):
                continue
            display_name = faculty.get('name') or faculty.get('normalized_name') or staff_id
            results.append({
                'author_id': staff_id,
                'name': display_name,
                'name_variants': [n for n in [faculty.get('name'), faculty.get('normalized_name')] if n],
                'pub_count': 0,
                'total_citations': 0,
                'top_keywords': [],
                'pub_ids': [],
                'is_current_faculty': True,
                '_faculty_only': True,
            })
    else:
        # Non-faculty-only searches: merge faculty-only matches so hidden faculty are findable.
        needle = (name or '').strip().lower()
        needle_id = (author_id or '').strip().lower()

        def _faculty_matches_query(faculty: dict) -> bool:
            if needle:
                hay = ' '.join([
                    faculty.get('name') or '',
                    faculty.get('normalized_name') or '',
                    faculty.get('email') or '',
                    faculty.get('department') or '',
                    faculty.get('designation') or '',
                ]).lower()
                if needle in hay:
                    return True
            if needle_id and needle_id in (faculty.get('staff_id') or '').lower():
                return True
            return False

        if name or author_id:
            already = {(faculty_matcher.get_faculty_info(author_id=r.get('author_id', '')) or {}).get('staff_id')
                       for r in results}
            already.discard(None)
            for staff_id, faculty in faculty_matcher.faculty_by_id.items():
                if staff_id in already:
                    continue
                if faculty.get('author_ids'):
                    continue
                if not _faculty_matches_query(faculty):
                    continue
                display_name = faculty.get('name') or faculty.get('normalized_name') or staff_id
                results.append({
                    'author_id': staff_id,
                    'name': display_name,
                    'name_variants': [n for n in [faculty.get('name'), faculty.get('normalized_name')] if n],
                    'pub_count': 0,
                    'total_citations': 0,
                    'top_keywords': [],
                    'pub_ids': [],
                    'is_current_faculty': True,
                    '_faculty_only': True,
                })

    # Sort: entries with publications first (desc), then alphabetically.
    results.sort(key=lambda x: (
        0 if x.get('pub_count', 0) > 0 else 1,
        -x.get('pub_count', 0),
        (x.get('name') or '').lower(),
    ))

    search_results = []
    for r in results[:limit]:
        photo_url = ""
        if r.get('is_current_faculty'):
            fi = faculty_matcher.get_faculty_info(author_id=r.get('author_id', ''))
            if not fi and r.get('_faculty_only'):
                fi = faculty_matcher.get_faculty_info(staff_id=r.get('author_id', ''))
            if fi:
                photo_url = fi.get('photo_url', '')
        top_keywords_raw = r.get('top_keywords') or []
        if top_keywords_raw and isinstance(top_keywords_raw[0], dict):
            top_keywords = [k['keyword'] for k in top_keywords_raw[:5]]
        else:
            top_keywords = list(top_keywords_raw[:5])
        search_results.append(AuthorSearchResult(
            author_id=r.get('author_id', ''),
            name=r.get('name', ''),
            name_variants=r.get('name_variants', []),
            matching_papers=r.get('pub_count', 0),
            total_citations=r.get('total_citations', 0),
            top_keywords=top_keywords,
            pub_ids=r.get('pub_ids', []),
            is_current_faculty=r.get('is_current_faculty', False),
            photo_url=photo_url,
        ))

    return search_results


@router.get("/top", response_model=List[dict])
async def get_top_authors(
    limit: int = Query(20, ge=1, le=100),
    only_faculty: bool = False
):
    """
    Get top authors by publication count.
    """
    engine = get_search_engine()
    return engine.get_top_authors(limit=limit, only_current_faculty=only_faculty)


@router.get("/{author_id}", response_model=AuthorProfile)
async def get_author(author_id: str):
    """
    Get author profile by ID. The ID may be a Scopus author id or a faculty
    staff_id (for faculty without indexed publications).
    """
    engine = get_search_engine()
    profile = engine.search_by_author_id(author_id)
    faculty_matcher = get_faculty_matcher()

    if not profile:
        # Fallback: treat id as a faculty staff_id so the 735 faculty remain reachable.
        faculty_info = faculty_matcher.get_faculty_info(staff_id=author_id)
        if not faculty_info:
            raise HTTPException(status_code=404, detail="Author not found")
        display_name = faculty_info.get('name') or faculty_info.get('normalized_name') or author_id
        return AuthorProfile(
            author_id=author_id,
            name=display_name,
            name_variants=[n for n in [faculty_info.get('name'), faculty_info.get('normalized_name')] if n],
            is_current_faculty=True,
            pub_count=0,
            total_citations=0,
            h_index=0,
            g_index=0,
            i10_index=0,
            publications=[],
            top_keywords=[],
            affiliations=[],
            schools=[faculty_info.get('school')] if faculty_info.get('school') else [],
            citation_list=[],
            national_collabs=0,
            international_collabs=0,
            country_collabs={},
            yearly_publications={},
            yearly_citations={},
            faculty_info=faculty_info,
        )

    # Add faculty info if available
    faculty_info = faculty_matcher.get_faculty_info(author_id=author_id)

    return AuthorProfile(
        author_id=profile.get('author_id', ''),
        name=profile.get('name', ''),
        name_variants=profile.get('name_variants', []),
        is_current_faculty=profile.get('is_current_faculty', False),
        pub_count=profile.get('pub_count', 0),
        total_citations=profile.get('total_citations', 0),
        h_index=profile.get('h_index', 0),
        g_index=profile.get('g_index', 0),
        i10_index=profile.get('i10_index', 0),
        publications=profile.get('publications', []),
        top_keywords=profile.get('top_keywords', []),
        affiliations=profile.get('affiliations', []),
        schools=profile.get('schools', []),
        citation_list=profile.get('citation_list', []),
        national_collabs=profile.get('national_collabs', 0),
        international_collabs=profile.get('international_collabs', 0),
        country_collabs=profile.get('country_collabs', {}),
        yearly_publications=profile.get('yearly_publications', {}),
        yearly_citations=profile.get('yearly_citations', {}),
        faculty_info=faculty_info
    )


@router.get("/{author_id}/citations")
async def get_author_citations(author_id: str):
    """
    Get citation histogram data for an author.
    """
    engine = get_search_engine()
    
    if author_id not in engine.author_profiles:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return engine.get_citation_histogram_data(author_id)


@router.get("/{author_id}/summary")
async def get_author_summary(author_id: str):
    """
    Get AI-generated summary for an author.
    """
    engine = get_search_engine()
    profile = engine.search_by_author_id(author_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Author not found")
    
    rag = get_rag()
    summary = rag.summarize_author(profile)
    
    return {
        "author_id": author_id,
        "summary": summary
    }


# Faculty-specific endpoints
@router.get("/faculty/all", response_model=List[FacultyInfo])
async def get_all_faculty():
    """
    Get all current SASTRA faculty members.
    """
    faculty_matcher = get_faculty_matcher()
    return faculty_matcher.get_all_current_faculty()


@router.get("/faculty/stats", response_model=FacultyStats)
async def get_faculty_stats():
    """
    Get faculty statistics.
    """
    faculty_matcher = get_faculty_matcher()
    stats = faculty_matcher.get_current_faculty_stats()
    return FacultyStats(**stats)


@router.get("/faculty/by-school/{school}")
async def get_faculty_by_school(school: str):
    """
    Get faculty members by school.
    """
    faculty_matcher = get_faculty_matcher()
    return faculty_matcher.get_faculty_by_school(school)


@router.get("/faculty/by-department/{department}")
async def get_faculty_by_department(department: str):
    """
    Get faculty members by department.
    """
    faculty_matcher = get_faculty_matcher()
    return faculty_matcher.get_faculty_by_department(department)
