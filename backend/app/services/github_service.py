"""
SASTRA Research Finder - GitHub Integration Service
Handles GitHub OAuth, repository fetching, and project auto-creation.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import requests

from app.models.db_models import GithubAccount, PocProject
from app.models.schemas import (
    GithubRepoInfo,
    GithubConnectionRequest,
    GithubConnectionResponse,
    GithubRepoListResponse,
    GithubProjectCreate,
    GithubSyncResponse,
    ActivityScore,
    PocProjectResponse,
    GithubUsernameSuggestion,
)


GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN_ENCRYPTION_KEY = os.environ.get("GITHUB_TOKEN_ENCRYPTION_KEY", "default-dev-key-change-in-prod")


def encrypt_token(token: str) -> str:
    """Simple token encryption for storage (use proper encryption in prod)."""
    import base64
    return base64.b64encode(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Simple token decryption."""
    import base64
    return base64.b64decode(encrypted_token.encode()).decode()


class GithubService:
    """Service for GitHub integration."""

    @staticmethod
    def connect_github(
        db: Session,
        faculty_author_id: str,
        request: GithubConnectionRequest
    ) -> GithubConnectionResponse:
        """Connect a GitHub account using access token."""
        user_info = GithubService.verify_token(request.access_token)
        
        if not user_info:
            raise ValueError("Invalid GitHub access token")
        
        existing = db.query(GithubAccount).filter(
            GithubAccount.faculty_author_id == faculty_author_id,
            GithubAccount.is_active == True
        ).first()
        
        if existing:
            existing.access_token_encrypted = encrypt_token(request.access_token)
            existing.github_username = user_info.get("login")
            existing.updated_at = datetime.utcnow()
        else:
            account = GithubAccount(
                faculty_author_id=faculty_author_id,
                github_username=user_info.get("login"),
                access_token_encrypted=encrypt_token(request.access_token),
                is_active=True
            )
            db.add(account)
        
        db.commit()
        
        repos = GithubService.fetch_repositories(request.access_token)
        
        return GithubConnectionResponse(
            github_username=user_info.get("login"),
            connected=True,
            repositories_count=len(repos)
        )

    @staticmethod
    def verify_token(access_token: str) -> Optional[Dict[str, Any]]:
        """Verify GitHub token and get user info."""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        try:
            response = requests.get(f"{GITHUB_API_BASE}/user", headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    @staticmethod
    def get_account(db: Session, faculty_author_id: str) -> Optional[GithubAccount]:
        """Get active GitHub account for faculty."""
        return db.query(GithubAccount).filter(
            GithubAccount.faculty_author_id == faculty_author_id,
            GithubAccount.is_active == True
        ).first()

    @staticmethod
    def get_access_token(db: Session, faculty_author_id: str) -> Optional[str]:
        """Get decrypted access token for faculty. Returns None for public-only accounts."""
        account = GithubService.get_account(db, faculty_author_id)
        if account and account.access_token_encrypted:
            return decrypt_token(account.access_token_encrypted)
        return None

    @staticmethod
    def connect_by_username(
        db: Session,
        faculty_author_id: str,
        username: str
    ) -> GithubConnectionResponse:
        """Connect a GitHub profile by public username only (no token, public repos)."""
        username = (username or "").strip().lstrip("@")
        if not username:
            raise ValueError("GitHub username is required")

        user_info = GithubService._fetch_public_user(username)
        if not user_info:
            raise ValueError(f"GitHub user '{username}' not found")

        canonical_username = user_info.get("login", username)

        existing = db.query(GithubAccount).filter(
            GithubAccount.faculty_author_id == faculty_author_id,
            GithubAccount.is_active == True
        ).first()

        if existing:
            existing.github_username = canonical_username
            existing.access_token_encrypted = None
            existing.updated_at = datetime.utcnow()
        else:
            account = GithubAccount(
                faculty_author_id=faculty_author_id,
                github_username=canonical_username,
                access_token_encrypted=None,
                is_active=True
            )
            db.add(account)

        db.commit()

        repos = GithubService.fetch_public_repositories(canonical_username)

        return GithubConnectionResponse(
            github_username=canonical_username,
            connected=True,
            repositories_count=len(repos),
            mode="public"
        )

    @staticmethod
    def _fetch_public_user(username: str) -> Optional[Dict[str, Any]]:
        """Fetch a GitHub user profile without authentication."""
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    @staticmethod
    def fetch_public_repositories(username: str) -> List[GithubRepoInfo]:
        """Fetch public repositories for a username without authentication."""
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/users/{username}/repos",
                headers={"Accept": "application/vnd.github.v3+json"},
                params={"sort": "updated", "per_page": 100, "direction": "desc", "type": "owner"},
                timeout=15
            )
            if response.status_code != 200:
                return []

            result = []
            for repo in response.json():
                if repo.get("private", False):
                    continue
                result.append(GithubRepoInfo(
                    repo_id=str(repo.get("id")),
                    name=repo.get("name"),
                    full_name=repo.get("full_name"),
                    description=repo.get("description") or "",
                    html_url=repo.get("html_url", ""),
                    language=repo.get("language"),
                    stargazers_count=repo.get("stargazers_count", 0),
                    forks_count=repo.get("forks_count", 0),
                    open_issues_count=repo.get("open_issues_count", 0),
                    watchers_count=repo.get("watchers_count", 0),
                    default_branch=repo.get("default_branch", "main"),
                    created_at=repo.get("created_at"),
                    updated_at=repo.get("updated_at"),
                    pushed_at=repo.get("pushed_at"),
                    topics=repo.get("topics", []),
                    license=repo.get("license", {}).get("name") if repo.get("license") else None,
                    is_private=repo.get("private", False),
                    is_fork=repo.get("fork", False),
                    forks=repo.get("forks_count", 0),
                    open_issues=repo.get("open_issues_count", 0)
                ))
            return result
        except Exception as e:
            print(f"Error fetching public repositories: {e}")
            return []

    @staticmethod
    def suggest_usernames(
        name: Optional[str] = None,
        email: Optional[str] = None,
        limit: int = 5
    ) -> List[GithubUsernameSuggestion]:
        """Suggest GitHub usernames from name and/or email via GitHub user search."""
        queries = []
        if email:
            queries.append((f"{email} in:email", "email"))
        if name:
            cleaned = name.strip()
            if cleaned:
                queries.append((f"{cleaned} in:fullname", "name"))

        suggestions: List[GithubUsernameSuggestion] = []
        seen = set()

        for query, reason in queries:
            try:
                response = requests.get(
                    f"{GITHUB_API_BASE}/search/users",
                    headers={"Accept": "application/vnd.github.v3+json"},
                    params={"q": query, "per_page": limit},
                    timeout=10
                )
                if response.status_code != 200:
                    continue
                for item in response.json().get("items", []):
                    login = item.get("login")
                    if not login or login in seen:
                        continue
                    seen.add(login)
                    profile = GithubService._fetch_public_user(login) or {}
                    suggestions.append(GithubUsernameSuggestion(
                        username=login,
                        name=profile.get("name"),
                        avatar_url=item.get("avatar_url"),
                        profile_url=item.get("html_url", f"https://github.com/{login}"),
                        match_reason=reason
                    ))
                    if len(suggestions) >= limit:
                        return suggestions
            except Exception as e:
                print(f"GitHub user search failed for '{query}': {e}")

        return suggestions

    @staticmethod
    def fetch_repositories(access_token: str, sort: str = "updated") -> List[GithubRepoInfo]:
        """Fetch repositories from GitHub."""
        headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/user/repos",
                headers=headers,
                params={"sort": sort, "per_page": 100, "direction": "desc"},
                timeout=15
            )
            
            if response.status_code != 200:
                return []
            
            repos = response.json()
            result = []
            
            for repo in repos:
                if repo.get("private", False):
                    continue
                    
                result.append(GithubRepoInfo(
                    repo_id=str(repo.get("id")),
                    name=repo.get("name"),
                    full_name=repo.get("full_name"),
                    description=repo.get("description") or "",
                    html_url=repo.get("html_url", ""),
                    language=repo.get("language"),
                    stargazers_count=repo.get("stargazers_count", 0),
                    forks_count=repo.get("forks_count", 0),
                    open_issues_count=repo.get("open_issues_count", 0),
                    watchers_count=repo.get("watchers_count", 0),
                    default_branch=repo.get("default_branch", "main"),
                    created_at=repo.get("created_at"),
                    updated_at=repo.get("updated_at"),
                    pushed_at=repo.get("pushed_at"),
                    topics=repo.get("topics", []),
                    license=repo.get("license", {}).get("name") if repo.get("license") else None,
                    is_private=repo.get("private", False),
                    is_fork=repo.get("fork", False),
                    forks=repo.get("forks_count", 0),
                    open_issues=repo.get("open_issues_count", 0)
                ))
            
            return result
            
        except Exception as e:
            print(f"Error fetching repositories: {e}")
            return []

    @staticmethod
    def get_user_repositories(db: Session, faculty_author_id: str) -> List[GithubRepoInfo]:
        """Get repositories for connected faculty (uses token if available, else public API)."""
        account = GithubService.get_account(db, faculty_author_id)
        if not account:
            return []
        access_token = GithubService.get_access_token(db, faculty_author_id)
        if access_token:
            return GithubService.fetch_repositories(access_token)
        if account.github_username:
            return GithubService.fetch_public_repositories(account.github_username)
        return []

    @staticmethod
    def fetch_single_repo(access_token: str, repo_full_name: str) -> Optional[GithubRepoInfo]:
        """Fetch a single repository by full name (owner/repo). Works without token for public repos."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if access_token:
            headers["Authorization"] = f"token {access_token}"
        
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo_full_name}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            repo = response.json()
            
            return GithubRepoInfo(
                repo_id=str(repo.get("id")),
                name=repo.get("name"),
                full_name=repo.get("full_name"),
                description=repo.get("description") or "",
                html_url=repo.get("html_url", ""),
                language=repo.get("language"),
                stargazers_count=repo.get("stargazers_count", 0),
                forks_count=repo.get("forks_count", 0),
                open_issues_count=repo.get("open_issues_count", 0),
                watchers_count=repo.get("watchers_count", 0),
                default_branch=repo.get("default_branch", "main"),
                created_at=repo.get("created_at"),
                updated_at=repo.get("updated_at"),
                pushed_at=repo.get("pushed_at"),
                topics=repo.get("topics", []),
                license=repo.get("license", {}).get("name") if repo.get("license") else None,
                is_private=repo.get("private", False),
                is_fork=repo.get("fork", False),
                forks=repo.get("forks_count", 0),
                open_issues=repo.get("open_issues_count", 0)
            )
            
        except Exception:
            return None

    @staticmethod
    def get_repo_readme(access_token: str, repo_full_name: str) -> str:
        """Fetch the README content for a repo (public or private).

        GitHub returns a JSON object with base64-encoded content; decode and
        truncate to a reasonable size so we can feed it to the LLM.
        """
        headers = {"Accept": "application/vnd.github.v3+json"}
        if access_token:
            headers["Authorization"] = f"token {access_token}"
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo_full_name}/readme",
                headers=headers,
                timeout=10,
            )
            if response.status_code != 200:
                return ""
            data = response.json()
            content_b64 = data.get("content") or ""
            if not content_b64:
                return ""
            import base64
            try:
                decoded = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                return decoded[:6000]
            except Exception:
                return ""
        except Exception as e:
            print(f"README fetch failed for {repo_full_name}: {e}")
            return ""

    @staticmethod
    def get_repo_languages(access_token: str, repo_full_name: str) -> Dict[str, int]:
        """Get language breakdown for a repository (works without token for public repos)."""
        headers = {"Accept": "application/vnd.github.v3+json"}
        if access_token:
            headers["Authorization"] = f"token {access_token}"

        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo_full_name}/languages",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {}

    @staticmethod
    def _enrich_github_metadata(
        repo_info: GithubRepoInfo,
        access_token: Optional[str],
        tech_stack: List[str],
    ) -> Dict[str, Any]:
        """Run Mistral metadata extraction against a GitHub repo's description + topics + README.

        Returns a dict with 'domains', 'keywords', 'complexity_10', 'impact_10',
        plus 'readme_used' flag and the raw activity score fallback.
        """
        activity_score = GithubService.calculate_activity_score(repo_info)
        raw_activity = float(activity_score.github_activity_score or 0)
        # fallback_impact = max(0, min(10, int(round(raw_activity / 50.0))))
        # fallback_complexity = max(0, min(10, int(activity_score.complexity_level or 0)))

        readme = GithubService.get_repo_readme(access_token or "", repo_info.full_name)
        topics_line = ", ".join(repo_info.topics or [])
        lang_line = ", ".join(tech_stack)
        llm_text_parts = []
        if repo_info.description:
            llm_text_parts.append(repo_info.description)
        if topics_line:
            llm_text_parts.append(f"Topics: {topics_line}")
        if lang_line:
            llm_text_parts.append(f"Languages: {lang_line}")
        if readme:
            llm_text_parts.append(f"README:\n{readme}")
        llm_description = "\n\n".join(llm_text_parts).strip()

        domains: List[str] = list(repo_info.topics or [])
        keywords: List[str] = list(repo_info.topics or [])
        # impact_10 = fallback_impact
        # complexity_10 = fallback_complexity

        try:
            from app.services.mistral_rag import get_rag
            rag = get_rag()
            if rag.is_available() and llm_description:
                meta = rag.extract_project_metadata(
                    title=repo_info.name or "",
                    description=llm_description,
                )
                llm_domains = meta.get("domains") or []
                llm_keywords = meta.get("keywords") or []
                # llm_impact = int(meta.get("impact_score") or 0)
                # llm_complexity = int(meta.get("complexity") or 0)

                if llm_domains:
                    merged = list(llm_domains)
                    for t in (repo_info.topics or []):
                        if t not in merged:
                            merged.append(t)
                    domains = merged[:8]
                if llm_keywords:
                    merged_kw = list(llm_keywords)
                    for t in (repo_info.topics or []):
                        if t not in merged_kw:
                            merged_kw.append(t)
                    keywords = merged_kw[:12]
                # if llm_impact > 0:
                #     impact_10 = max(1, min(10, llm_impact))
                # if llm_complexity > 0:
                #     complexity_10 = max(1, min(10, llm_complexity))
        except Exception as e:
            print(f"LLM metadata enrichment failed for {repo_info.full_name}: {e}")

        return {
            "domains": domains,
            "keywords": keywords,
            # "complexity_10": complexity_10,
            # "impact_10": impact_10,
            "raw_activity_score": round(raw_activity, 2),
            "readme_used": bool(readme),
        }

    @staticmethod
    def create_project_from_github(
        db: Session,
        faculty_author_id: str,
        repo_info: GithubRepoInfo
    ) -> PocProject:
        """Create a POC project from a GitHub repository."""
        access_token = GithubService.get_access_token(db, faculty_author_id)

        tech_stack = []
        languages = GithubService.get_repo_languages(access_token or "", repo_info.full_name)
        if languages:
            tech_stack = list(languages.keys())
        elif repo_info.language:
            tech_stack = [repo_info.language]
        
        existing = db.query(PocProject).filter(
            PocProject.github_repo_id == repo_info.repo_id,
            PocProject.faculty_author_id == faculty_author_id
        ).first()
        
        if existing:
            return existing
        
        enrichment = GithubService._enrich_github_metadata(repo_info, access_token, tech_stack)

        project = PocProject(
            faculty_author_id=faculty_author_id,
            title=repo_info.name,
            description=repo_info.description or "",
            source="github",
            github_repo_id=repo_info.repo_id,
            github_repo_name=repo_info.name,
            linked_account="github",
            auto_synced=True,
            github_link=repo_info.html_url,
            year=datetime.now().year,
            extracted_domains=enrichment["domains"],
            # complexity_score=enrichment["complexity_10"],
            # impact_score=enrichment["impact_10"],
            keywords=enrichment["keywords"],
            tech_stack=tech_stack,
            stars=repo_info.stargazers_count,
            forks=repo_info.forks_count,
            last_synced=datetime.utcnow(),
            github_metadata={
                "full_name": repo_info.full_name,
                "language": repo_info.language,
                "default_branch": repo_info.default_branch,
                "license": repo_info.license,
                "created_at": repo_info.created_at,
                "updated_at": repo_info.updated_at,
                "pushed_at": repo_info.pushed_at,
                "raw_activity_score": enrichment["raw_activity_score"],
                "readme_used": enrichment["readme_used"],
            }
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return project

    @staticmethod
    def calculate_activity_score(repo: GithubRepoInfo) -> ActivityScore:
        """Calculate GitHub activity score for a repository."""
        stars = repo.stargazers_count
        forks = repo.forks_count
        
        days_since_update = 0
        if repo.updated_at:
            try:
                updated = datetime.fromisoformat(repo.updated_at.replace("Z", "+00:00"))
                days_since_update = (datetime.utcnow() - updated.replace(tzinfo=None)).days
            except Exception:
                days_since_update = 30
        
        recency_weight_value = max(0, 1 - (days_since_update / 365))
        
        github_activity_score = (
            (stars * 0.5) +
            (forks * 0.3) +
            (recency_weight_value * 100)
        )
        
        stars_weight = stars * 0.5
        commit_weight = 0
        recency_weight = recency_weight_value * 100
        
        complexity_level = min(10, max(1, int((stars / 50) + (forks / 20) + (recency_weight_value * 5))))
        
        return ActivityScore(
            github_activity_score=round(github_activity_score, 2),
            stars_weight=stars_weight,
            commit_weight=commit_weight,
            recency_weight=round(recency_weight, 2),
            stars=stars,
            total_commits=0,
            days_since_update=days_since_update,
            complexity_level=complexity_level
        )

    @staticmethod
    def sync_github_project(
        db: Session,
        project: PocProject
    ) -> GithubSyncResponse:
        """Sync a GitHub-based POC project with latest repository data."""
        if project.source != "github" or not project.github_repo_id:
            raise ValueError("Project is not linked to GitHub")

        account = GithubService.get_account(db, project.faculty_author_id)
        if not account:
            raise ValueError("GitHub account not found")

        access_token = GithubService.get_access_token(db, project.faculty_author_id)

        repo_full_name = f"{account.github_username}/{project.github_repo_name}"
        repo_info = GithubService.fetch_single_repo(access_token or "", repo_full_name)

        if not repo_info:
            raise ValueError("Repository not found or access denied")

        languages = GithubService.get_repo_languages(access_token or "", repo_full_name)
        tech_stack = list(languages.keys()) if languages else ([repo_info.language] if repo_info.language else [])

        enrichment = GithubService._enrich_github_metadata(repo_info, access_token, tech_stack)

        project.title = repo_info.name
        project.description = repo_info.description or ""
        project.stars = repo_info.stargazers_count
        project.forks = repo_info.forks_count
        project.keywords = enrichment["keywords"]
        project.extracted_domains = enrichment["domains"]
        project.tech_stack = tech_stack
        # project.complexity_score = enrichment["complexity_10"]
        # project.impact_score = enrichment["impact_10"]
        project.last_synced = datetime.utcnow()

        project.github_metadata = {
            **(project.github_metadata or {}),
            "full_name": repo_info.full_name,
            "language": repo_info.language,
            "updated_at": repo_info.updated_at,
            "synced_at": datetime.utcnow().isoformat(),
            "raw_activity_score": enrichment["raw_activity_score"],
            "readme_used": enrichment["readme_used"],
        }

        db.commit()
        db.refresh(project)

        return GithubSyncResponse(
            project_id=project.id,
            title=project.title,
            synced=True,
            github_metadata=project.github_metadata or {},
        )

    @staticmethod
    def disconnect_github(db: Session, faculty_author_id: str) -> bool:
        """Disconnect GitHub account."""
        account = GithubService.get_account(db, faculty_author_id)
        if account:
            account.is_active = False
            account.access_token_encrypted = None
            db.commit()
            return True
        return False

    @staticmethod
    def is_github_connected(db: Session, faculty_author_id: str) -> bool:
        """Check if GitHub is connected for faculty."""
        account = GithubService.get_account(db, faculty_author_id)
        return account is not None and account.is_active

    @staticmethod
    def get_github_username(db: Session, faculty_author_id: str) -> Optional[str]:
        """Get GitHub username for faculty."""
        account = GithubService.get_account(db, faculty_author_id)
        return account.github_username if account else None