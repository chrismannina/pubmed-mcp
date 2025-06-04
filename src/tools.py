"""
Tool definitions for PubMed MCP Server.

This module contains the MCP tool schema definitions for all available tools
in the PubMed server.
"""

from typing import Any, Dict, List

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "search_pubmed",
        "description": "Search PubMed for articles with advanced filtering options",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query using PubMed syntax"},
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 20,
                    "description": "Maximum number of results to return",
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["relevance", "pub_date", "author", "journal", "title"],
                    "default": "relevance",
                    "description": "Sort order for results",
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date (YYYY/MM/DD, YYYY/MM, or YYYY)",
                },
                "date_to": {
                    "type": "string",
                    "description": "End date (YYYY/MM/DD, YYYY/MM, or YYYY)",
                },
                "date_range": {
                    "type": "string",
                    "enum": ["1y", "5y", "10y", "all"],
                    "description": "Predefined date range",
                },
                "article_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "Journal Article",
                            "Review",
                            "Systematic Review",
                            "Meta-Analysis",
                            "Clinical Trial",
                            "Randomized Controlled Trial",
                            "Case Reports",
                            "Letter",
                            "Editorial",
                            "Comment",
                        ],
                    },
                    "description": "Filter by article types",
                },
                "authors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by author names",
                },
                "journals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by journal names",
                },
                "mesh_terms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by MeSH terms",
                },
                "language": {
                    "type": "string",
                    "description": "Language filter (e.g., 'eng', 'fre', 'ger')",
                },
                "has_abstract": {
                    "type": "boolean",
                    "description": "Only include articles with abstracts",
                },
                "has_full_text": {
                    "type": "boolean",
                    "description": "Only include articles with full text available",
                },
                "humans_only": {"type": "boolean", "description": "Only include human studies"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_article_details",
        "description": "Get detailed information for specific articles by PMID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pmids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PubMed IDs",
                },
                "include_abstracts": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include abstracts in response",
                },
                "include_citations": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include citation count and metrics",
                },
            },
            "required": ["pmids"],
        },
    },
    {
        "name": "search_by_author",
        "description": "Search for articles by a specific author",
        "inputSchema": {
            "type": "object",
            "properties": {
                "author_name": {"type": "string", "description": "Author name to search for"},
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Maximum number of results",
                },
                "include_coauthors": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include co-author information",
                },
            },
            "required": ["author_name"],
        },
    },
    {
        "name": "find_related_articles",
        "description": "Find articles related to a specific PMID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pmid": {"type": "string", "description": "PMID of the reference article"},
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 10,
                    "description": "Maximum number of related articles",
                },
            },
            "required": ["pmid"],
        },
    },
    {
        "name": "export_citations",
        "description": "Export article citations in various formats",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pmids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of PubMed IDs to export",
                },
                "format": {
                    "type": "string",
                    "enum": ["bibtex", "endnote", "ris", "apa", "mla", "chicago", "vancouver"],
                    "default": "bibtex",
                    "description": "Citation format",
                },
                "include_abstracts": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include abstracts in citations",
                },
            },
            "required": ["pmids"],
        },
    },
    {
        "name": "search_mesh_terms",
        "description": "Search and explore MeSH (Medical Subject Headings) terms",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "MeSH term to search for"},
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Maximum number of results",
                },
            },
            "required": ["term"],
        },
    },
    {
        "name": "search_by_journal",
        "description": "Search articles from a specific journal",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journal_name": {"type": "string", "description": "Journal name or abbreviation"},
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20,
                    "description": "Maximum number of results",
                },
                "date_from": {"type": "string", "description": "Start date (YYYY/MM/DD)"},
                "date_to": {"type": "string", "description": "End date (YYYY/MM/DD)"},
            },
            "required": ["journal_name"],
        },
    },
    {
        "name": "get_trending_topics",
        "description": "Get trending medical topics and research areas",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Medical category (e.g., 'cardiology', 'oncology', 'neurology')",
                },
                "days": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 30,
                    "default": 7,
                    "description": "Number of days to analyze for trends",
                },
            },
        },
    },
    {
        "name": "analyze_research_trends",
        "description": "Analyze publication trends for a research topic over time",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic to analyze"},
                "years_back": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5,
                    "description": "Number of years to analyze",
                },
                "include_subtopics": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include analysis of related subtopics",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "compare_articles",
        "description": "Compare multiple articles side by side",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pmids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 5,
                    "description": "List of PMIDs to compare (2-5 articles)",
                },
                "comparison_fields": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "authors",
                            "methods",
                            "results",
                            "conclusions",
                            "mesh_terms",
                            "citations",
                        ],
                    },
                    "default": ["authors", "methods", "conclusions"],
                    "description": "Fields to compare",
                },
            },
            "required": ["pmids"],
        },
    },
    {
        "name": "get_journal_metrics",
        "description": "Get metrics and information about a specific journal",
        "inputSchema": {
            "type": "object",
            "properties": {
                "journal_name": {"type": "string", "description": "Journal name or abbreviation"},
                "include_recent_articles": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include recent notable articles",
                },
            },
            "required": ["journal_name"],
        },
    },
    {
        "name": "advanced_search",
        "description": "Perform complex PubMed searches with multiple criteria",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_terms": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "term": {"type": "string"},
                            "field": {
                                "type": "string",
                                "enum": ["title", "abstract", "author", "journal", "mesh", "all"],
                            },
                            "operator": {"type": "string", "enum": ["AND", "OR", "NOT"]},
                        },
                        "required": ["term", "field"],
                    },
                    "description": "Complex search criteria with fields and operators",
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "publication_types": {"type": "array", "items": {"type": "string"}},
                        "species": {"type": "array", "items": {"type": "string"}},
                        "languages": {"type": "array", "items": {"type": "string"}},
                        "age_groups": {"type": "array", "items": {"type": "string"}},
                        "sex": {"type": "string", "enum": ["male", "female", "both"]},
                    },
                    "description": "Additional filters",
                },
                "max_results": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
            },
            "required": ["search_terms"],
        },
    },
]
