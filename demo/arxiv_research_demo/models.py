"""Data models for the ArXiv research demo."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class Paper(BaseModel):
    """Represents an ArXiv paper with extracted information."""
    title: str
    authors: List[str]
    summary: str
    pdf_url: str
    paper_id: str
    published: str
    categories: List[str]
    doi: Optional[str] = None


class ExtractedInfo(BaseModel):
    """Key information extracted from a paper."""
    title: str
    authors: List[str]
    key_findings: List[str]
    methodology: str
    datasets_used: List[str]
    limitations: List[str]
    future_work: List[str]
    paper_id: str
    arxiv_url: str


class GistInfo(BaseModel):
    """Information about a created GitHub gist."""
    gist_id: str
    gist_url: str
    filename: str
    title: str
    created_at: datetime
