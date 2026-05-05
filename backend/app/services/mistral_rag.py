"""
SASTRA Research Finder - Mistral AI RAG Service
Provides AI-powered research analysis and skill extraction.
"""

import json
import re
from typing import List, Dict, Any, Optional

from app.core.config import get_settings

# Try to import Mistral SDK (supports multiple package layouts)
MISTRAL_AVAILABLE = False
Mistral = None
try:
    from mistralai import Mistral  # Newer SDK layout
    MISTRAL_AVAILABLE = True
except ImportError:
    try:
        from mistralai.client import Mistral  # Speakeasy-generated SDK layout
        MISTRAL_AVAILABLE = True
    except ImportError:
        Mistral = None


class MistralRAG:
    """RAG system for research analysis using Mistral AI."""

    def __init__(self):
        """Initialize Mistral API."""
        settings = get_settings()
        self.api_key = (settings.MISTRAL_API_KEY or "").strip()
        self.client = None
        self.model = None
        self._initialized = False

        if MISTRAL_AVAILABLE and self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
                self.model = (getattr(settings, "MISTRAL_MODEL", None) or "mistral-small-latest").strip()
                self.analysis_model = self.model
                self._initialized = True
                print(f"Mistral AI initialized with model: {self.model}")
            except Exception as e:
                print(f"Mistral initialization failed: {e}")
                self._initialized = False
        else:
            if not MISTRAL_AVAILABLE:
                print("Mistral SDK import failed. Install or upgrade mistralai.")
            if not self.api_key:
                print("No Mistral API key found")

    def is_available(self) -> bool:
        """Check if Mistral API is available."""
        return self._initialized and self.client is not None

    def _call_mistral(self, prompt: str, max_tokens: int = 1500,
                      temperature: float = 0.1,
                      system_prompt: Optional[str] = None) -> Optional[str]:
        """Make a call to Mistral API. Retries once on the small model if the configured model returns empty."""
        if not self.is_available():
            print("Mistral: Not available")
            return None

        system = system_prompt or (
            "You are an expert research analyst specializing in academic publication analysis. "
            "Provide accurate, detailed, and specific insights based on the provided research papers. "
            "Always include Author IDs when referencing researchers."
        )

        models_to_try = [self.model]
        if self.model != "mistral-small-latest":
            models_to_try.append("mistral-small-latest")

        last_error = None
        for model in models_to_try:
            try:
                response = self.client.chat.complete(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                if response and response.choices:
                    content = response.choices[0].message.content
                    if content and content.strip():
                        return content
                    print(f"Mistral ({model}): Empty content in response")
                else:
                    print(f"Mistral ({model}): No choices in response")
            except Exception as e:
                last_error = e
                print(f"Mistral ({model}) error: {e}")

        if last_error is not None:
            print(f"Mistral all models failed. Last error: {last_error}")
        return None

    def extract_skills(self, project_title: str,
                       context_keywords: List[str] = None) -> List[str]:
        """Extract skills from project title."""
        if not project_title:
            return []

        if self.is_available():
            try:
                return self._extract_skills_mistral(project_title, context_keywords)
            except Exception as e:
                print(f"Mistral skill extraction failed: {e}")
                return self._extract_skills_fallback(project_title)
        else:
            return self._extract_skills_fallback(project_title)

    def _extract_skills_mistral(self, project_title: str,
                              context_keywords: List[str] = None) -> List[str]:
        """Use Mistral for skill extraction."""
        context_str = ""
        if context_keywords:
            context_str = f"\n\nRelated keywords: {', '.join(context_keywords[:40])}"

        prompt = f"""Extract 10-15 highly specific technical skills from this research project title.

Project Title: "{project_title}"{context_str}

RULES:
1. Be SPECIFIC - extract exact techniques (e.g., "convolutional neural networks" not "deep learning")
2. Include domain applications (e.g., "medical image segmentation")
3. Include specific algorithms (e.g., "ResNet", "LSTM", "random forest")
4. Include frameworks/tools if implied (e.g., "TensorFlow", "PyTorch")

Return ONLY a comma-separated list of skills. No numbering, no explanations.
Skills:"""

        response = self._call_mistral(prompt, max_tokens=250, temperature=0.05)

        if response:
            skills_text = response.strip()
            skills_text = re.sub(r'^[:\s"\']+|[:\s"\']+$', '', skills_text)

            skills = []
            for skill in skills_text.split(','):
                skill = skill.strip().lower()
                skill = re.sub(r'^\d+[\.\)]\s*', '', skill)
                if skill and 3 <= len(skill) <= 60:
                    skills.append(skill)

            return skills[:15]

        return self._extract_skills_fallback(project_title)

    def _extract_skills_fallback(self, project_title: str) -> List[str]:
        """Rule-based skill extraction fallback."""
        if not project_title:
            return []

        title_lower = project_title.lower()

        # Technical patterns to match
        patterns = [
            # Deep Learning
            r'\b(deep learning|neural network|cnn|convolutional|rnn|lstm|gru|transformer|bert|gpt|resnet|vgg|u-net|gan|autoencoder)\b',
            # Machine Learning
            r'\b(machine learning|supervised|unsupervised|classification|regression|clustering|random forest|svm|decision tree|xgboost)\b',
            # NLP
            r'\b(nlp|natural language|text mining|sentiment analysis|named entity|language model|word embedding)\b',
            # Computer Vision
            r'\b(computer vision|image processing|object detection|image classification|segmentation|face recognition|ocr)\b',
            # Healthcare
            r'\b(medical imaging|mri|ct scan|x-ray|diagnosis|healthcare|clinical|disease|cancer|tumor)\b',
            # Data Science
            r'\b(data mining|big data|analytics|prediction|forecasting|time series)\b',
            # Security
            r'\b(cybersecurity|intrusion detection|malware|encryption|blockchain)\b',
            # IoT
            r'\b(iot|internet of things|sensor|smart city|smart home|embedded)\b',
        ]

        skills = set()
        for pattern in patterns:
            matches = re.findall(pattern, title_lower)
            skills.update(matches)

        # Add specific terms from title
        words = re.findall(r'\b[a-z][a-z0-9\-]+\b', title_lower)
        tech_terms = {
            'python', 'tensorflow', 'pytorch', 'keras', 'opencv', 'pandas',
            'numpy', 'scikit', 'sklearn', 'matlab', 'r', 'java', 'sql'
        }
        for word in words:
            if word in tech_terms:
                skills.add(word)

        return list(skills)[:15]

    def analyze(self, context: List[Dict[str, Any]],
                skills: List[str]) -> Dict[str, Any]:
        """Generate research analysis using RAG."""
        if not self.is_available():
            return {
                'analysis': None,
                'error': 'Mistral API not configured. Add MISTRAL_API_KEY to environment.',
                'context_count': 0
            }

        if not context:
            return {
                'analysis': None,
                'error': 'No relevant publications found.',
                'context_count': 0
            }

        try:
            return self._generate_analysis(context, skills)
        except Exception as e:
            return {
                'analysis': None,
                'error': f'Analysis failed: {str(e)}',
                'context_count': 0
            }

    def _generate_analysis(self, context: List[Dict[str, Any]],
                           skills: List[str]) -> Dict[str, Any]:
        """Generate detailed analysis."""
        # Build context from publications
        context_parts = []
        for idx, pub in enumerate(context[:20], 1):
            author_id = pub.get('author_id', 'Unknown')
            abstract = pub.get('abstract', '')[:1000]

            all_keywords = list(set(
                pub.get('author_keywords', []) +
                pub.get('index_keywords', [])
            ))[:10]
            keywords_str = ', '.join(all_keywords) if all_keywords else 'Not specified'

            link = pub.get('link', '') or (f"https://doi.org/{pub.get('doi', '')}" if pub.get('doi') else '')
            context_parts.append(f"""
[Paper {idx}]
Title: {pub.get('title', 'Untitled')}
Author ID: {author_id}
Authors: {pub.get('authors', 'N/A')}
Year: {pub.get('year', 'N/A')}
Citations: {pub.get('citations', 0)}
Keywords: {keywords_str}
Link: {link if link else 'N/A'}
Abstract: {abstract}
""")

        context_text = "\n".join(context_parts)
        skills_text = ", ".join(skills)

        prompt = f"""Analyze these SASTRA research publications and generate a comprehensive report.

SKILLS/INTERESTS: {skills_text}

PUBLICATIONS:
{context_text}

Generate analysis in this format:

## 1. KEY METHODS & TECHNIQUES
List specific methods, algorithms, and techniques found (8-12 items with details).

## 2. REPRESENTATIVE PAPERS
List most relevant papers with Author IDs (8-12 papers).
Format each paper on its own line as: "Title" [LINK: <url from paper's Link field, or N/A>] (AUTHOR_ID: XXXXX) - Brief description
Use only the exact title (no extra numbers), and use the Link from the paper data.

## 3. REQUIRED TECHNOLOGIES & TOOLS
List programming languages, frameworks, libraries, and tools mentioned.

## 4. RECOMMENDED RESEARCHERS
Top 5-8 researchers ranked by relevance with Author IDs.

## 5. RESEARCH GAPS & OPPORTUNITIES
Identify unexplored areas and potential improvements.

## 6. NEXT STEPS
Actionable recommendations for collaboration/implementation.

IMPORTANT: Always include Author IDs. Base all information on provided publications only."""

        response = self._call_mistral(prompt, max_tokens=2500, temperature=0.15)

        if response:
            return {
                'analysis': response,
                'error': None,
                'context_count': len(context)
            }
        else:
            return {
                'analysis': None,
                'error': 'Empty response from Mistral API',
                'context_count': len(context)
            }

    def summarize_author(self, profile: Dict[str, Any]) -> str:
        """Generate author research summary."""
        if not self.is_available():
            return ""

        try:
            pubs = profile.get('publications', [])[:15]
            keywords = profile.get('top_keywords', [])[:20]

            if not pubs:
                return ""

            pub_details = []
            for p in pubs:
                title = p.get('title', 'Untitled')
                year = p.get('year', 'N/A')
                cites = p.get('citations', 0)
                pub_details.append(f"- ({year}, {cites} citations) {title}")

            pub_text = "\n".join(pub_details)
            
            if isinstance(keywords, list) and keywords:
                if isinstance(keywords[0], dict):
                    kw_text = ", ".join([f"{k['keyword']} ({k['count']})" for k in keywords])
                else:
                    kw_text = ", ".join([f"{k} ({c})" for k, c in keywords])
            else:
                kw_text = "Not available"

            name_variants = profile.get('name_variants', ['Unknown'])
            name = name_variants[0] if name_variants else 'Unknown'

            prompt = f"""Summarize this researcher's expertise in 3-4 sentences.

Researcher: {name}
Total Publications: {profile.get('pub_count', 0)}
Total Citations: {profile.get('total_citations', 0)}

Top Keywords: {kw_text}

Recent Publications:
{pub_text}

Summary:"""

            response = self._call_mistral(prompt, max_tokens=200, temperature=0.2)
            return response.strip() if response else ""

        except Exception as e:
            print(f"Author summary failed: {e}")
            return ""

    def extract_from_document(self, filename: str, text: str) -> Dict[str, Any]:
        """
        Extract project metadata from an uploaded document's text.
        Returns suggested title, description, domains, keywords, complexity, impact.
        """
        fallback = {
            "suggested_title": filename,
            "suggested_description": (text or "")[:280],
            "domains": [],
            "dynamic_domains": [],
            # "complexity": 0,
            # "impact_score": 0,
            "keywords": [],
        }
        if not self.is_available() or not text or not text.strip():
            return fallback

        try:
            excerpt = text[:6000]
            prompt = f"""You are analysing a research / engineering project document.
Given the file content below, extract metadata as STRICT JSON only.

Filename: {filename}
Content (may be truncated):
\"\"\"
{excerpt}
\"\"\"

Return ONLY valid JSON with this shape:
{{
  "suggested_title": "short, human-readable project title (max 12 words)",
  "suggested_description": "2-3 sentence description of what this project does",
  "domains": ["research domains from standard taxonomy, e.g. Machine Learning, Healthcare Analytics"],
  "dynamic_domains": ["new/unusual domains not in standard taxonomy, leave empty if none"],
  "keywords": ["specific technical keywords"]
}}"""
            # Disabled (commented out): previously prompted for
            #   "complexity": 1-10,
            #   "impact_score": 1-10,

            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=600,
                temperature=0.1,
            )

            if response and response.choices:
                content = response.choices[0].message.content
                if content:
                    result = json.loads(content)
                    return {
                        "suggested_title": result.get("suggested_title") or fallback["suggested_title"],
                        "suggested_description": result.get("suggested_description") or fallback["suggested_description"],
                        "domains": result.get("domains", []) or [],
                        "dynamic_domains": result.get("dynamic_domains", []) or [],
                        # "complexity": int(result.get("complexity", 0) or 0),
                        # "impact_score": int(result.get("impact_score", 0) or 0),
                        "keywords": result.get("keywords", []) or [],
                    }
        except Exception as e:
            print(f"Document metadata extraction failed: {e}")

        return fallback

    def extract_project_metadata(self, title: str, description: str) -> Dict[str, Any]:
        """Extract metadata from project title and description using LLM."""
        if not self.is_available():
            return {
                "domains": [],
                "dynamic_domains": [],
                # "complexity": 0,
                # "impact_score": 0,
                "keywords": []
            }

        try:
            prompt = f"""Extract metadata from this research project.
Title: {title}
Description: {description}

Return ONLY valid JSON:
{{
  "domains": ["list of matching research domains from standard taxonomy (e.g., Machine Learning, Healthcare Analytics)"],
  "dynamic_domains": ["any new domain not in standard taxonomy - leave empty if none"],
  "keywords": ["specific technical keywords"]
}}"""
            # Disabled (commented out): previously prompted for
            #   "complexity": <1-10>,
            #   "impact_score": <1-10>,

            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.1
            )

            if response and response.choices:
                result = json.loads(response.choices[0].message.content)
                return {
                    "domains": result.get("domains", []),
                    "dynamic_domains": result.get("dynamic_domains", []),
                    # "complexity": result.get("complexity", 0),
                    # "impact_score": result.get("impact_score", 0),
                    "keywords": result.get("keywords", [])
                }
        except Exception as e:
            print(f"Metadata extraction failed: {e}")

        return {
            "domains": [],
            "dynamic_domains": [],
            # "complexity": 0,
            # "impact_score": 0,
            "keywords": []
        }

    def analyze_structured(self, context: List[Dict[str, Any]],
                           skills: List[str]) -> Dict[str, Any]:
        """Generate structured research analysis with SASTRA papers."""
        if not self.is_available():
            return {
                "sastra_papers": [],
                "analysis": {
                    "key_methods": [],
                    "research_gaps": [],
                    "emerging_trends": [],
                    "collaboration_insights": []
                },
                "error": "Mistral API not configured"
            }

        if not context:
            return {
                "sastra_papers": [],
                "analysis": {
                    "key_methods": [],
                    "research_gaps": [],
                    "emerging_trends": [],
                    "collaboration_insights": []
                },
                "error": "No relevant publications found"
            }

        try:
            context_pubs = []
            for pub in context[:20]:
                link = pub.get('link', '') or (f"https://doi.org/{pub.get('doi', '')}" if pub.get('doi') else '')
                context_pubs.append({
                    "title": pub.get('title', ''),
                    "authors": pub.get('authors', ''),
                    "year": pub.get('year', 0),
                    "link": link,
                    "relevance_score": 0.8,
                    "source": "SASTRA"
                })

            prompt = f"""Analyze research context and return ONLY valid JSON matching this schema:
{{
  "sastra_papers": [{{"title":"","authors":"","year":0,"link":"","relevance_score":0.0}}],
  "analysis": {{
    "key_methods": ["..."],
    "research_gaps": ["..."],
    "emerging_trends": ["..."],
    "collaboration_insights": ["..."]
  }}
}}

SASTRA papers (internal): {json.dumps(context_pubs[:10])}
Skills/Interests: {", ".join(skills)}"""

            response = self.client.chat.complete(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.15
            )

            if response and response.choices:
                result = json.loads(response.choices[0].message.content)
                return result
            error_msg = "Empty response from Mistral API"
        except Exception as e:
            print(f"Structured analysis failed: {e}")
            error_msg = str(e)

        return {
            "sastra_papers": [],
            "analysis": {
                "key_methods": [],
                "research_gaps": [],
                "emerging_trends": [],
                "collaboration_insights": []
            },
            "error": error_msg
        }

    def analyze_with_papers(self, context: List[Dict[str, Any]],
                           skills: List[str],
                           global_papers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate analysis with both SASTRA papers and (optionally) global insights."""
        if not self.is_available():
            return {
                "analysis_text": None,
                "analysis": {
                    "key_methods": [],
                    "research_gaps": [],
                    "emerging_trends": [],
                    "collaboration_insights": []
                },
                "error": "Mistral API not configured"
            }

        if not context:
            return {
                "analysis_text": None,
                "analysis": {
                    "key_methods": [],
                    "research_gaps": [],
                    "emerging_trends": [],
                    "collaboration_insights": []
                },
                "error": "No relevant publications found"
            }

        try:
            context_parts = []
            for idx, pub in enumerate(context[:10], 1):
                author_id = pub.get('author_id', 'Unknown')
                abstract = pub.get('abstract', '')[:500]
                link = pub.get('link', '') or (f"https://doi.org/{pub.get('doi', '')}" if pub.get('doi') else '')
                context_parts.append(f"""
[Paper {idx}]
Title: {pub.get('title', 'Untitled')}
Author ID: {author_id}
Authors: {pub.get('authors', 'N/A')}
Year: {pub.get('year', 'N/A')}
Citations: {pub.get('citations', 0)}
Keywords: {', '.join(pub.get('author_keywords', [])[:8])}
Link: {link}
Abstract: {abstract}
""")

            context_text = "\n".join(context_parts)
            skills_text = ", ".join(skills)

            global_block = ""
            if global_papers:
                g_lines = []
                for idx, gp in enumerate(global_papers[:8], 1):
                    title = gp.get("title", "Untitled")
                    authors = gp.get("authors", "")
                    year = gp.get("year", "")
                    link = gp.get("link", "")
                    g_lines.append(
                        f"[Global {idx}] \"{title}\" — {authors} ({year}) LINK: {link or 'N/A'}"
                    )
                global_block = (
                    "\n\nGLOBAL REFERENCE PAPERS (from web search):\n" + "\n".join(g_lines)
                )

            has_globals = bool(global_papers)
            global_section = (
                "## 2. TOP RELEVANT GLOBAL PAPERS\n"
                "For each global paper list: \"Title\" by Authors (Year) - relevance note. "
                "Format each line with [LINK: url] or [LINK: N/A].\n\n"
            ) if has_globals else ""

            prompt = f"""You are an expert research analyst. Produce a comprehensive, structured report for a researcher with the skills/interests below.

SKILLS/INTERESTS: {skills_text}

SASTRA PUBLICATIONS:
{context_text}{global_block}

Write the report with this heading style (use exactly the section headings shown, in this order). Each section must be substantive and specific — no empty sections.

# Comprehensive Analysis of SASTRA Research Papers

## 1. KEY METHODS & TECHNIQUES
8-12 specific methods, algorithms, or techniques seen across the papers with one-line explanations.

{global_section}## 3. REQUIRED TECHNOLOGIES & TOOLS
Programming languages, frameworks, libraries, cloud/infra, and lab equipment implied by the papers.

## 4. SKILLS REQUIRED
Concrete, practical skills a researcher would need to reproduce or extend this work. Group as Hard Skills (math, programming, domain) vs Soft Skills (reading papers, experimental design).

## 5. CONCEPTS TO LEARN
Prerequisite ideas and theory a newcomer should master, roughly ordered from foundational to advanced. Keep to 8-12 bullets.

## 6. OPEN-SOURCE DATASETS
List ONLY widely-known, real public datasets you are confident exist (e.g. ImageNet, CIFAR-10, MIMIC-III, MNIST, COCO, Kaggle Titanic). For each line use this exact format:
- **Dataset Name** — one-line description — https://the-official-homepage
Rules: maximum 6 items. If you are not certain of the exact URL, OMIT the URL entirely (just the name + description). NEVER invent URLs. Prefer canonical sources (kaggle.com, huggingface.co/datasets, archive.ics.uci.edu, paperswithcode.com/datasets).

## 7. REFERENCE GITHUB REPOSITORIES
List ONLY famous, widely-starred public GitHub repositories you are confident exist. For each line use this exact format:
- **owner/repo** — one-line purpose
Rules: maximum 6 items. Use the short "owner/repo" form — the UI will auto-link it to github.com. NEVER invent owner/repo names. Prefer well-known orgs (tensorflow, pytorch, huggingface, scikit-learn, microsoft, google, facebookresearch, openai).

## 8. RECOMMENDED SASTRA RESEARCHERS
Top 5-8 SASTRA researchers by relevance. Always include their AUTHOR_ID: <id>.

## 9. RESEARCH GAPS & OPPORTUNITIES
Unexplored angles worth pursuing, grounded in the provided papers.

## 10. EMERGING TRENDS
Current directions implied by recent papers / keywords.

## 11. COLLABORATION INSIGHTS
Who could collaborate with whom (SASTRA + global) and why.

## 12. NEXT STEPS
Actionable plan (3-5 bullets) for someone starting a project in this area.

Rules:
- Ground every SASTRA-specific claim in the provided papers; include AUTHOR_ID when referencing researchers.
- Datasets, GitHub repos and learning resources may draw on general public knowledge but must be real and widely known, not invented.
- Do not emit empty sections. If genuinely nothing fits, write one sentence explaining why."""

            response = self._call_mistral(prompt, max_tokens=3500, temperature=0.2)

            if response:
                return {
                    "analysis_text": response,
                    "analysis": {
                        "key_methods": self._extract_section(response, "KEY METHODS"),
                        "research_gaps": self._extract_section(response, "RESEARCH GAPS"),
                        "emerging_trends": self._extract_section(response, "EMERGING TRENDS"),
                        "collaboration_insights": self._extract_section(response, "COLLABORATION")
                    },
                    "error": None
                }
            error_msg = "Mistral returned no analysis text. The prompt may be too long or the model may be rate-limited."
        except Exception as e:
            print(f"Analysis with papers failed: {e}")
            error_msg = str(e)

        return {
            "analysis_text": None,
            "analysis": {
                "key_methods": [],
                "research_gaps": [],
                "emerging_trends": [],
                "collaboration_insights": []
            },
            "error": error_msg
        }

    def _extract_section(self, text: str, section_name: str) -> List[str]:
        """Extract items from a section in the analysis text."""
        lines = text.split('\n')
        in_section = False
        items = []
        current_items = []

        for line in lines:
            line_clean = line.strip()
            if section_name.upper() in line_clean.upper():
                in_section = True
                continue
            if in_section:
                if line_clean.startswith('## ') or (line_clean and not line_clean[0].isdigit() and 
                    not line_clean.startswith('-') and not line_clean.startswith('•')):
                    if current_items:
                        items.extend(current_items)
                        current_items = []
                    in_section = False
                    continue
                if line_clean.startswith('-') or line_clean.startswith('•'):
                    item = line_clean.lstrip('-•').strip()
                    if item and len(item) > 5:
                        current_items.append(item)

        return items[:10]


# Singleton instance
_rag_instance: Optional[MistralRAG] = None


def get_rag() -> MistralRAG:
    """Get or create RAG singleton."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = MistralRAG()
    return _rag_instance

