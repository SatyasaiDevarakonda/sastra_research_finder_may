"""
SASTRA Research Finder - Web Search Service
Uses Mistral and Exa search to find global research papers.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import get_settings

MISTRAL_AVAILABLE = False
try:
    from mistralai import Mistral
    from mistralai.models import ChatMessage
    MISTRAL_AVAILABLE = True
except ImportError:
    Mistral = None


class WebSearchService:
    """Service for searching global research papers online."""

    def __init__(self):
        """Initialize the web search service."""
        settings = get_settings()
        self.api_key = (settings.MISTRAL_API_KEY or "").strip()
        self.client = None
        self._initialized = False
        self.exa_key = settings.EXA_API_KEY if hasattr(settings, 'EXA_API_KEY') else None

        if MISTRAL_AVAILABLE and self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
                self._initialized = True
                print("Web search service initialized with Mistral")
            except Exception as e:
                print(f"Web search service init failed: {e}")

    def is_available(self) -> bool:
        """Check if service is available."""
        return self._initialized and self.client is not None

    def search_research_papers(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for global research papers using Mistral's web search."""
        if not self.is_available():
            return self._search_fallback(query, max_results)

        try:
            return self._search_with_mistral(query, max_results)
        except Exception as e:
            print(f"Web search error: {e}")
            return self._search_fallback(query, max_results)

    def _search_with_mistral(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Mistral's web search tool."""
        from mistralai.models import (
            WebSearchTool,
            ChatMessage,
            ToolChoice,
            ResponseFormatJsonObject
        )

        search_query = f"research papers {query} site:arxiv.org OR site:semanticscholar.org OR site:doi.org"
        
        response = self.client.chat.stream(
            model="mistral-large-latest",
            messages=[
                ChatMessage(
                    role="user",
                    content=f"Find {max_results} recent research papers about: {query}. Return ONLY valid JSON array with this exact schema:\n[{{\"title\":\"\",\"authors\":\"\",\"year\":0,\"link\":\"\",\"pdf_link\":\"\",\"abstract\":\"\",\"venue\":\"\",\"citations\":0}}]"
                )
            ],
            tools=[WebSearchTool()],
            tool_choice=ToolChoice(type="web_search"),
            response_format=ResponseFormatJsonObject(type="json_object"),
            max_tokens=3000
        )

        papers = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                try:
                    papers = json.loads(chunk.choices[0].delta.content)
                    if isinstance(papers, list):
                        for p in papers:
                            p['source'] = 'GLOBAL'
                        return papers
                except:
                    pass
        return []

    def _search_fallback(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback search using basic approach when Mistral tool unavailable."""
        return []

    def search_papers_with_llm(self, skills: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for papers using LLM to find relevant research."""
        if not self.is_available():
            return []

        query = " AND ".join(skills[:5])
        return self.search_research_papers(query, max_results)


class ExaSearchService:
    """Service for searching using Exa AI for better results."""

    def __init__(self):
        """Initialize Exa search service."""
        settings = get_settings()
        self.api_key = getattr(settings, 'EXA_API_KEY', None) or getattr(settings, 'EXA_KEY', None)
        self.base_url = "https://api.exa.ai"

    def is_available(self) -> bool:
        """Check if Exa is available."""
        return bool(self.api_key)

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search using Exa API."""
        if not self.is_available():
            return []

        try:
            import requests
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            data = {
                "query": query,
                "num_results": num_results,
                "filters": {
                    "type": "any",
                    "condition": [{"texts": {"query": "paper OR research OR preprint"}},
                                   {"texts": {"query": "arxiv OR doi OR semantic scholar"}}]
                }
            }
            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json=data,
                timeout=30
            )
            if response.status_code == 200:
                results = response.json().get("results", [])
                papers = []
                for r in results:
                    published = r.get("published_date") or ""
                    year = 0
                    if isinstance(published, str) and len(published) >= 4 and published[:4].isdigit():
                        year = int(published[:4])
                    url = r.get("url", "") or ""
                    # Only treat as a PDF link when the URL actually ends with .pdf
                    pdf_link = url if url.lower().endswith(".pdf") else ""
                    authors_val = r.get("authors", [])
                    if isinstance(authors_val, list):
                        authors_str = ", ".join([a for a in authors_val if a])
                    else:
                        authors_str = str(authors_val or "")
                    source_field = r.get("source", {})
                    venue = source_field.get("name", "") if isinstance(source_field, dict) else str(source_field or "")
                    paper = {
                        "title": r.get("title", "") or "",
                        "authors": authors_str,
                        "year": year,
                        "link": url,
                        "pdf_link": pdf_link,
                        "abstract": (r.get("text", "") or "")[:500],
                        "venue": venue,
                        "citations": int(r.get("citation_count", 0) or 0),
                        "source": "GLOBAL",
                    }
                    papers.append(paper)
                return papers
        except Exception as e:
            print(f"Exa search error: {e}")
        return []

    def search_by_skills(self, skills: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """Search by skills/interests."""
        query = " ".join(skills[:5])
        return self.search(query, max_results)


class OpenAlexSearchService:
    """
    Free global research paper search via the OpenAlex API.
    No API key required; shares a soft rate limit by optionally sending an
    email via the `mailto` query param (best-practice per OpenAlex docs).
    """

    def __init__(self):
        self.base_url = "https://api.openalex.org/works"
        # OpenAlex asks users to identify themselves for higher rate limits.
        self.mailto = "sastra-research-finder@sastra.edu"

    def is_available(self) -> bool:
        return True

    @staticmethod
    def _reconstruct_abstract(inverted_index: Dict[str, List[int]]) -> str:
        if not inverted_index:
            return ""
        position_map: Dict[int, str] = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                position_map[pos] = word
        if not position_map:
            return ""
        ordered = [position_map[k] for k in sorted(position_map.keys())]
        return " ".join(ordered)

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        if not query.strip():
            return []

        import requests
        params = {
            "search": query,
            "per-page": min(max(num_results, 1), 25),
            "mailto": self.mailto,
            # Rank by relevance (default) but filter to works with a DOI or OA link.
            "filter": "has_abstract:true",
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=20)
            if response.status_code != 200:
                print(f"OpenAlex error: {response.status_code} {response.text[:200]}")
                return []
            data = response.json()
        except Exception as e:
            print(f"OpenAlex request failed: {e}")
            return []

        papers: List[Dict[str, Any]] = []
        for r in data.get("results", [])[:num_results]:
            title = (r.get("title") or r.get("display_name") or "").strip()
            if not title:
                continue

            year = int(r.get("publication_year") or 0)

            authorships = r.get("authorships") or []
            author_names = []
            for a in authorships[:6]:
                name = (a.get("author") or {}).get("display_name")
                if name:
                    author_names.append(name)
            authors_str = ", ".join(author_names)
            if len(authorships) > 6:
                authors_str += f" et al."

            citations = int(r.get("cited_by_count") or 0)

            primary = r.get("primary_location") or {}
            source = (primary.get("source") or {})
            venue = source.get("display_name") or ""

            # Canonical page: prefer DOI, else landing page, else the OpenAlex record.
            doi = r.get("doi") or ""
            landing = primary.get("landing_page_url") or ""
            oa = (r.get("open_access") or {}).get("oa_url") or ""
            link = doi or landing or r.get("id") or ""

            # Prefer an open-access PDF if available.
            pdf_link = ""
            if oa and oa.lower().endswith(".pdf"):
                pdf_link = oa
            elif primary.get("pdf_url"):
                pdf_link = primary.get("pdf_url")

            abstract = self._reconstruct_abstract(r.get("abstract_inverted_index") or {})[:500]

            papers.append({
                "title": title,
                "authors": authors_str,
                "year": year,
                "link": link,
                "pdf_link": pdf_link,
                "abstract": abstract,
                "venue": venue,
                "citations": citations,
                "relevance_score": 0.7,
                "source": "GLOBAL",
            })
        return papers

    def search_by_skills(self, skills: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        query = " ".join(skills[:5])
        return self.search(query, max_results)


_web_search_instance: Optional[WebSearchService] = None
_exa_search_instance: Optional[ExaSearchService] = None
_openalex_instance: Optional[OpenAlexSearchService] = None


def get_web_search() -> WebSearchService:
    """Get web search singleton."""
    global _web_search_instance
    if _web_search_instance is None:
        _web_search_instance = WebSearchService()
    return _web_search_instance


def get_exa_search() -> ExaSearchService:
    """Get Exa search singleton."""
    global _exa_search_instance
    if _exa_search_instance is None:
        _exa_search_instance = ExaSearchService()
    return _exa_search_instance


def get_openalex_search() -> OpenAlexSearchService:
    """Get OpenAlex search singleton (free, no API key required)."""
    global _openalex_instance
    if _openalex_instance is None:
        _openalex_instance = OpenAlexSearchService()
    return _openalex_instance