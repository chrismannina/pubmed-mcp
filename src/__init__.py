"""
PubMed MCP Server Package.

A comprehensive Model Context Protocol (MCP) server for PubMed literature search and management.
"""

from .models import (
    Article,
    ArticleType,
    Author,
    CitationFormat,
    DateRange,
    Journal,
    MCPResponse,
    MeSHTerm,
    SearchResult,
    SortOrder,
)
from .pubmed_client import PubMedClient
from .server import PubMedMCPServer
from .tool_handler import ToolHandler

__version__ = "1.0.0"
__author__ = "Agent Care Team"

__all__ = [
    "PubMedMCPServer",
    "PubMedClient",
    "ToolHandler",
    "Article",
    "Author",
    "Journal",
    "MeSHTerm",
    "SearchResult",
    "MCPResponse",
    "SortOrder",
    "DateRange",
    "ArticleType",
    "CitationFormat",
]
