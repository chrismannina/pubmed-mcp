"""
Pydantic models for PubMed MCP server.

This module contains all the data models used throughout the application,
including request models, response models, and data structure definitions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class SortOrder(str, Enum):
    """PubMed search sort orders."""

    RELEVANCE = "relevance"
    PUBLICATION_DATE = "pub_date"
    AUTHOR = "author"
    JOURNAL = "journal"
    TITLE = "title"


class DateRange(str, Enum):
    """Predefined date ranges for search."""

    LAST_YEAR = "1y"
    LAST_5_YEARS = "5y"
    LAST_10_YEARS = "10y"
    ALL_TIME = "all"


class ArticleType(str, Enum):
    """PubMed article types."""

    JOURNAL_ARTICLE = "Journal Article"
    REVIEW = "Review"
    SYSTEMATIC_REVIEW = "Systematic Review"
    META_ANALYSIS = "Meta-Analysis"
    CLINICAL_TRIAL = "Clinical Trial"
    RANDOMIZED_CONTROLLED_TRIAL = "Randomized Controlled Trial"
    CASE_REPORT = "Case Reports"
    LETTER = "Letter"
    EDITORIAL = "Editorial"
    COMMENT = "Comment"


class CitationFormat(str, Enum):
    """Citation export formats."""

    BIBTEX = "bibtex"
    ENDNOTE = "endnote"
    RIS = "ris"
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    VANCOUVER = "vancouver"


# Request Models
class PubMedSearchRequest(BaseModel):
    """Request model for PubMed search."""

    query: str = Field(..., description="Search query")
    max_results: Optional[int] = Field(20, ge=1, le=200, description="Maximum number of results")
    sort_order: Optional[SortOrder] = Field(
        SortOrder.RELEVANCE, description="Sort order for results"
    )
    date_from: Optional[str] = Field(None, description="Start date (YYYY/MM/DD or YYYY/MM or YYYY)")
    date_to: Optional[str] = Field(None, description="End date (YYYY/MM/DD or YYYY/MM or YYYY)")
    date_range: Optional[DateRange] = Field(None, description="Predefined date range")
    article_types: Optional[List[ArticleType]] = Field(None, description="Filter by article types")
    authors: Optional[List[str]] = Field(None, description="Filter by authors")
    journals: Optional[List[str]] = Field(None, description="Filter by journals")
    mesh_terms: Optional[List[str]] = Field(None, description="Filter by MeSH terms")
    language: Optional[str] = Field(None, description="Language filter (e.g., 'eng', 'fre')")
    has_abstract: Optional[bool] = Field(None, description="Only include articles with abstracts")
    has_full_text: Optional[bool] = Field(None, description="Only include articles with full text")
    humans_only: Optional[bool] = Field(None, description="Only include human studies")


class AuthorSearchRequest(BaseModel):
    """Request model for author-based search."""

    author_name: str = Field(..., description="Author name to search for")
    max_results: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")
    include_coauthors: Optional[bool] = Field(True, description="Include co-author information")


class PMIDRequest(BaseModel):
    """Request model for PMID-based operations."""

    pmids: List[str] = Field(..., description="List of PubMed IDs")
    include_abstracts: Optional[bool] = Field(True, description="Include abstracts in response")
    include_citations: Optional[bool] = Field(False, description="Include citation information")


class RelatedArticlesRequest(BaseModel):
    """Request model for finding related articles."""

    pmid: str = Field(..., description="PMID of the reference article")
    max_results: Optional[int] = Field(
        10, ge=1, le=50, description="Maximum number of related articles"
    )


class CitationRequest(BaseModel):
    """Request model for citation export."""

    pmids: List[str] = Field(..., description="List of PubMed IDs to export")
    format: CitationFormat = Field(CitationFormat.BIBTEX, description="Citation format")
    include_abstracts: Optional[bool] = Field(False, description="Include abstracts in citations")


class MeSHSearchRequest(BaseModel):
    """Request model for MeSH term search."""

    term: str = Field(..., description="MeSH term to search for")
    max_results: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")


class JournalSearchRequest(BaseModel):
    """Request model for journal-based search."""

    journal_name: str = Field(..., description="Journal name or abbreviation")
    max_results: Optional[int] = Field(20, ge=1, le=100, description="Maximum number of results")
    date_from: Optional[str] = Field(None, description="Start date (YYYY/MM/DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY/MM/DD)")


class TrendingRequest(BaseModel):
    """Request model for trending topics."""

    category: Optional[str] = Field(
        None, description="Medical category (e.g., 'cardiology', 'oncology')"
    )
    days: Optional[int] = Field(7, ge=1, le=30, description="Number of days to look back")


# Data Models
class Author(BaseModel):
    """Author information model."""

    last_name: str
    first_name: Optional[str] = None
    initials: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


class Journal(BaseModel):
    """Journal information model."""

    title: str
    iso_abbreviation: Optional[str] = None
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pub_date: Optional[str] = None


class MeSHTerm(BaseModel):
    """MeSH term information model."""

    descriptor_name: str
    qualifier_name: Optional[str] = None
    major_topic: bool = False
    ui: Optional[str] = None


class Article(BaseModel):
    """Complete article information model."""

    pmid: str
    title: str
    abstract: Optional[str] = None
    authors: List[Author] = []
    journal: Journal
    pub_date: Optional[str] = None
    doi: Optional[str] = None
    pmc_id: Optional[str] = None
    article_types: List[str] = []
    mesh_terms: List[MeSHTerm] = []
    keywords: List[str] = []
    languages: List[str] = []
    citation_count: Optional[int] = None
    full_text_urls: List[str] = []
    pdf_urls: List[str] = []
    grant_info: List[Dict[str, str]] = []
    conflict_of_interest: Optional[str] = None


class SearchResult(BaseModel):
    """Search result container model."""

    query: str
    total_results: int
    returned_results: int
    articles: List[Article]
    search_time: float
    suggestions: List[str] = []


class TrendingTopic(BaseModel):
    """Trending topic information model."""

    topic: str
    article_count: int
    growth_rate: float
    representative_articles: List[str]  # PMIDs


# Response Models
class MCPResponse(BaseModel):
    """MCP response format model."""

    content: List[Dict[str, Any]]
    is_error: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None
