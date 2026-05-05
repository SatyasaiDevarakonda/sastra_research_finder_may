"""
File extraction utilities for POC / Funded project uploads.
Supports PDF, DOCX, TXT, MD, common code files, and ZIP archives (folders).
"""

from __future__ import annotations

import io
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Tuple, List, Optional

TEXT_EXTS = {
    ".txt", ".md", ".rst", ".log",
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs",
    ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini",
    ".html", ".css", ".scss",
}
PDF_EXTS = {".pdf"}
DOCX_EXTS = {".docx"}
IPYNB_EXTS = {".ipynb"}
ZIP_EXTS = {".zip"}

MAX_TEXT_CHARS = 20000  # Hard cap on combined extracted text


def extract_from_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        out = []
        for page in reader.pages:
            try:
                out.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(out)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def extract_from_docx(data: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text)
    except Exception as e:
        return f"[DOCX extraction failed: {e}]"


def extract_from_text(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc, errors="ignore")
        except Exception:
            continue
    return ""


def extract_from_ipynb(data: bytes) -> str:
    """Extract the readable text from a Jupyter notebook (markdown + code cells)."""
    try:
        text = data.decode("utf-8", errors="ignore")
        nb = json.loads(text)
    except Exception as e:
        return f"[IPYNB parse failed: {e}]"

    out: List[str] = []
    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type", "")
        src = cell.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        src = (src or "").strip()
        if not src:
            continue
        if cell_type == "markdown":
            out.append(src)
        elif cell_type == "code":
            out.append(f"```python\n{src}\n```")
        elif cell_type == "raw":
            out.append(src)
    return "\n\n".join(out)


def extract_single(filename: str, data: bytes) -> str:
    """Extract text from a single file's bytes based on extension."""
    ext = Path(filename).suffix.lower()
    if ext in PDF_EXTS:
        return extract_from_pdf(data)
    if ext in DOCX_EXTS:
        return extract_from_docx(data)
    if ext in IPYNB_EXTS:
        return extract_from_ipynb(data)
    if ext in TEXT_EXTS:
        return extract_from_text(data)
    return ""


def extract_from_zip(data: bytes) -> Tuple[str, List[str]]:
    """Extract concatenated text from all supported files in a zip. Returns (text, file_list)."""
    text_chunks: List[str] = []
    files_listed: List[str] = []
    total_chars = 0

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                # skip hidden / system dirs and huge blobs
                if any(part.startswith(".") or part in {"node_modules", "__pycache__", ".git", "venv", ".venv", "dist", "build"}
                       for part in Path(name).parts):
                    continue
                if info.file_size > 2_000_000:  # 2MB per file cap
                    continue
                ext = Path(name).suffix.lower()
                if (ext not in TEXT_EXTS and ext not in PDF_EXTS
                        and ext not in DOCX_EXTS and ext not in IPYNB_EXTS):
                    # still list it but don't extract
                    files_listed.append(name)
                    continue

                files_listed.append(name)
                try:
                    with zf.open(info) as f:
                        chunk = extract_single(name, f.read())
                except Exception:
                    continue

                if not chunk:
                    continue
                header = f"\n\n===== {name} =====\n"
                remaining = MAX_TEXT_CHARS - total_chars
                if remaining <= 0:
                    break
                piece = (header + chunk)[:remaining]
                text_chunks.append(piece)
                total_chars += len(piece)
    except Exception as e:
        return f"[ZIP extraction failed: {e}]", files_listed

    return "".join(text_chunks), files_listed


def extract_text_and_files(filename: str, data: bytes) -> Tuple[str, List[str]]:
    """Main entry — returns (extracted_text, listed_files)."""
    ext = Path(filename).suffix.lower()
    if ext in ZIP_EXTS:
        text, files = extract_from_zip(data)
    else:
        text = extract_single(filename, data)
        files = [filename]
    # Truncate
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS]
    return text, files


def sanitize_filename(name: str) -> str:
    """Prevent path traversal and weird characters in saved filenames."""
    name = os.path.basename(name)
    name = re.sub(r"[^A-Za-z0-9._\- ]+", "_", name)
    return name.strip() or "upload"
