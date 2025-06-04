"""
Tool handler for PubMed MCP Server.

This module handles all tool requests and formats responses for the MCP protocol.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .citation_formatter import CitationFormatter
from .models import (
    Article,
    ArticleType,
    AuthorSearchRequest,
    CitationFormat,
    CitationRequest,
    DateRange,
    JournalSearchRequest,
    MCPResponse,
    MeSHSearchRequest,
    PMIDRequest,
    PubMedSearchRequest,
    RelatedArticlesRequest,
    SortOrder,
    TrendingRequest,
)
from .pubmed_client import PubMedClient
from .tools import TOOL_DEFINITIONS
from .utils import CacheManager, format_authors, format_date, format_mesh_terms, truncate_text

logger = logging.getLogger(__name__)


class ToolHandler:
    """Handler for all PubMed MCP tool calls."""

    def __init__(self, pubmed_client: PubMedClient, cache: CacheManager) -> None:
        """
        Initialize tool handler.

        Args:
            pubmed_client: PubMed API client instance
            cache: Cache manager instance
        """
        self.pubmed_client = pubmed_client
        self.cache = cache

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return TOOL_DEFINITIONS

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> MCPResponse:
        """
        Handle a tool call request.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            MCPResponse with formatted content
        """
        try:
            logger.info(f"Handling tool call: {name}")

            # Handle None arguments
            if arguments is None:
                return MCPResponse(
                    content=[{"type": "text", "text": "Error: Arguments cannot be None"}],
                    is_error=True,
                )

            # Route to appropriate handler
            handler_map = {
                "search_pubmed": self._handle_search_pubmed,
                "get_article_details": self._handle_get_article_details,
                "search_by_author": self._handle_search_by_author,
                "find_related_articles": self._handle_find_related_articles,
                "export_citations": self._handle_export_citations,
                "search_mesh_terms": self._handle_search_mesh_terms,
                "search_by_journal": self._handle_search_by_journal,
                "get_trending_topics": self._handle_get_trending_topics,
                "analyze_research_trends": self._handle_analyze_research_trends,
                "compare_articles": self._handle_compare_articles,
                "get_journal_metrics": self._handle_get_journal_metrics,
                "advanced_search": self._handle_advanced_search,
            }

            handler = handler_map.get(name)
            if handler:
                return await handler(arguments)
            else:
                return MCPResponse(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}], is_error=True
                )

        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error executing {name}: {str(e)}"}],
                is_error=True,
            )

    async def _handle_search_pubmed(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle PubMed search with advanced filtering."""
        try:
            # Parse arguments
            query = arguments.get("query", "")
            if not query:
                return MCPResponse(
                    content=[{"type": "text", "text": "Query parameter is required"}], is_error=True
                )

            max_results = arguments.get("max_results", 20)
            # Handle negative max_results
            if max_results < 0:
                max_results = 0

            sort_order = SortOrder(arguments.get("sort_order", "relevance"))
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")
            date_range = (
                DateRange(arguments.get("date_range")) if arguments.get("date_range") else None
            )

            # Parse article types
            article_types = None
            if arguments.get("article_types"):
                article_types = [ArticleType(at) for at in arguments["article_types"]]

            # Perform search
            search_result = await self.pubmed_client.search_articles(
                query=query,
                max_results=max_results,
                sort_order=sort_order,
                date_from=date_from,
                date_to=date_to,
                date_range=date_range,
                article_types=article_types,
                authors=arguments.get("authors"),
                journals=arguments.get("journals"),
                mesh_terms=arguments.get("mesh_terms"),
                language=arguments.get("language"),
                has_abstract=arguments.get("has_abstract"),
                has_full_text=arguments.get("has_full_text"),
                humans_only=arguments.get("humans_only"),
                cache=self.cache,
            )

            # Format response
            content = []

            # Summary
            content.append(
                {
                    "type": "text",
                    "text": f"**PubMed Search Results**\n\n"
                    f"Query: {query}\n"
                    f"Total Results: {search_result.total_results:,}\n"
                    f"Returned: {search_result.returned_results}\n"
                    f"Search Time: {search_result.search_time:.2f}s\n",
                }
            )

            # Articles
            if search_result.articles:
                for i, article_data in enumerate(search_result.articles, 1):
                    article_text = self._format_article_summary(article_data, i)
                    content.append({"type": "text", "text": article_text})
            else:
                content.append({"type": "text", "text": "No articles found for this query."})

            return MCPResponse(
                content=content,
                metadata={
                    "total_results": search_result.total_results,
                    "search_time": search_result.search_time,
                },
            )

        except Exception as e:
            logger.error(f"Error in search_pubmed: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Search error: {str(e)}"}], is_error=True
            )

    async def _handle_get_article_details(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle getting detailed article information."""
        try:
            pmids = arguments.get("pmids", [])
            if not pmids:
                return MCPResponse(
                    content=[{"type": "text", "text": "PMIDs parameter is required"}], is_error=True
                )

            include_abstracts = arguments.get("include_abstracts", True)
            include_citations = arguments.get("include_citations", False)

            articles = await self.pubmed_client.get_article_details(
                pmids=pmids,
                include_abstracts=include_abstracts,
                include_citations=include_citations,
                cache=self.cache,
            )

            content = []
            content.append(
                {"type": "text", "text": f"**Article Details for {len(articles)} Articles**\n"}
            )

            if articles:
                for i, article in enumerate(articles, 1):
                    article_text = self._format_article_details(article, i)
                    content.append({"type": "text", "text": article_text})
            else:
                content.append(
                    {"type": "text", "text": "No articles found for the provided PMIDs."}
                )

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in get_article_details: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_search_by_author(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle author-based search."""
        try:
            author_name = arguments.get("author_name", "")
            if not author_name:
                return MCPResponse(
                    content=[{"type": "text", "text": "Author name is required"}], is_error=True
                )

            max_results = arguments.get("max_results", 20)
            include_coauthors = arguments.get("include_coauthors", True)

            search_result = await self.pubmed_client.search_by_author(
                author_name=author_name,
                max_results=max_results,
                include_coauthors=include_coauthors,
                cache=self.cache,
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Publications by {author_name}**\n\n"
                    f"Total Articles: {search_result.total_results}\n"
                    f"Showing: {search_result.returned_results}\n",
                }
            )

            for i, article_data in enumerate(search_result.articles, 1):
                article_text = self._format_article_summary(article_data, i)
                content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in search_by_author: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_find_related_articles(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle finding related articles."""
        try:
            pmid = arguments.get("pmid", "")
            if not pmid:
                return MCPResponse(
                    content=[{"type": "text", "text": "PMID is required"}], is_error=True
                )

            max_results = arguments.get("max_results", 10)

            search_result = await self.pubmed_client.find_related_articles(
                pmid=pmid, max_results=max_results, cache=self.cache
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Articles Related to PMID: {pmid}**\n\n"
                    f"Found: {search_result.returned_results} related articles\n",
                }
            )

            for i, article_data in enumerate(search_result.articles, 1):
                article_text = self._format_article_summary(article_data, i)
                content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in find_related_articles: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_export_citations(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle citation export."""
        try:
            pmids = arguments.get("pmids", [])
            if not pmids:
                return MCPResponse(
                    content=[{"type": "text", "text": "PMIDs parameter is required"}], is_error=True
                )

            format_type = CitationFormat(arguments.get("format", "bibtex"))
            include_abstracts = arguments.get("include_abstracts", False)

            # Get article details
            articles = await self.pubmed_client.get_article_details(
                pmids=pmids,
                include_abstracts=True,  # Always get abstracts for citation
                cache=self.cache,
            )

            if not articles:
                return MCPResponse(
                    content=[{"type": "text", "text": "No articles found for the provided PMIDs"}],
                    is_error=True,
                )

            # Format citations
            citations = CitationFormatter.format_multiple_citations(
                articles=articles, format_type=format_type, include_abstracts=include_abstracts
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Citations in {format_type.value.upper()} format**\n\n{citations}",
                }
            )

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in export_citations: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_search_mesh_terms(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle MeSH term search."""
        try:
            term = arguments.get("term", "")
            if not term:
                return MCPResponse(
                    content=[{"type": "text", "text": "MeSH term is required"}], is_error=True
                )

            max_results = arguments.get("max_results", 20)

            # Search using the MeSH term
            search_result = await self.pubmed_client.search_articles(
                query=f'"{term}"[MeSH Terms]', max_results=max_results, cache=self.cache
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Articles with MeSH term: {term}**\n\n"
                    f"Total Results: {search_result.total_results:,}\n"
                    f"Showing: {search_result.returned_results}\n",
                }
            )

            for i, article_data in enumerate(search_result.articles, 1):
                article_text = self._format_article_summary(article_data, i, highlight_mesh=term)
                content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in search_mesh_terms: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_search_by_journal(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle journal-based search."""
        try:
            journal_name = arguments.get("journal_name", "")
            if not journal_name:
                return MCPResponse(
                    content=[{"type": "text", "text": "Journal name is required"}], is_error=True
                )

            max_results = arguments.get("max_results", 20)
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")

            search_result = await self.pubmed_client.search_articles(
                query=f'"{journal_name}"[Journal]',
                max_results=max_results,
                date_from=date_from,
                date_to=date_to,
                cache=self.cache,
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Recent Articles from {journal_name}**\n\n"
                    f"Total Results: {search_result.total_results:,}\n"
                    f"Showing: {search_result.returned_results}\n",
                }
            )

            for i, article_data in enumerate(search_result.articles, 1):
                article_text = self._format_article_summary(article_data, i)
                content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in search_by_journal: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_get_trending_topics(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle trending topics analysis."""
        try:
            category = arguments.get("category", "")
            days = arguments.get("days", 7)

            # Calculate date range for trending analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            date_from = start_date.strftime("%Y/%m/%d")
            date_to = end_date.strftime("%Y/%m/%d")

            # Build query for trending topics
            if category:
                query = f'{category} AND ("trending" OR "emerging" OR "new" OR "novel")'
            else:
                query = '("trending" OR "emerging" OR "breakthrough" OR "novel") AND (medicine OR medical)'

            search_result = await self.pubmed_client.search_articles(
                query=query,
                max_results=30,
                sort_order=SortOrder.PUBLICATION_DATE,
                date_from=date_from,
                date_to=date_to,
                cache=self.cache,
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Trending Topics in {category or 'Medicine'} (Last {days} days)**\n\n"
                    f"Found: {search_result.returned_results} recent articles\n",
                }
            )

            # Group by topics/keywords
            topics = {}
            for article_data in search_result.articles:
                for keyword in article_data.get("keywords", [])[:3]:  # Top 3 keywords
                    if keyword not in topics:
                        topics[keyword] = []
                    topics[keyword].append(article_data)

            # Show top topics
            sorted_topics = sorted(topics.items(), key=lambda x: len(x[1]), reverse=True)[:5]

            for topic, articles in sorted_topics:
                content.append(
                    {
                        "type": "text",
                        "text": f"\n**{topic}** ({len(articles)} articles)\n"
                        + "\n".join(
                            [
                                f"• {article['title']} (PMID: {article['pmid']})"
                                for article in articles[:3]
                            ]
                        ),
                    }
                )

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in get_trending_topics: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_analyze_research_trends(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle research trend analysis."""
        try:
            topic = arguments.get("topic", "")
            if not topic:
                return MCPResponse(
                    content=[{"type": "text", "text": "Topic is required"}], is_error=True
                )

            years_back = arguments.get("years_back", 5)
            include_subtopics = arguments.get("include_subtopics", False)

            # Analyze trends year by year
            current_year = datetime.now().year
            yearly_data = []

            for year in range(current_year - years_back, current_year + 1):
                search_result = await self.pubmed_client.search_articles(
                    query=topic,
                    max_results=200,  # Get more results for trend analysis
                    date_from=f"{year}/01/01",
                    date_to=f"{year}/12/31",
                    cache=self.cache,
                )
                yearly_data.append(
                    {
                        "year": year,
                        "count": search_result.total_results,
                        "articles": search_result.articles[:5],  # Top 5 articles
                    }
                )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Research Trends for: {topic}**\n\n"
                    f"Analysis Period: {current_year - years_back} - {current_year}\n",
                }
            )

            # Show yearly trends
            trend_text = "**Publication Counts by Year:**\n"
            for data in yearly_data:
                trend_text += f"{data['year']}: {data['count']:,} articles\n"

            content.append({"type": "text", "text": trend_text})

            # Calculate growth
            if len(yearly_data) >= 2:
                recent_avg = sum([d["count"] for d in yearly_data[-2:]]) / 2
                early_avg = sum([d["count"] for d in yearly_data[:2]]) / 2
                growth_rate = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0

                content.append(
                    {
                        "type": "text",
                        "text": f"\n**Growth Analysis:**\n"
                        f"Recent average: {recent_avg:.0f} articles/year\n"
                        f"Early average: {early_avg:.0f} articles/year\n"
                        f"Growth rate: {growth_rate:+.1f}%\n",
                    }
                )

            # Show recent notable articles
            recent_articles = yearly_data[-1]["articles"] if yearly_data else []
            if recent_articles:
                content.append(
                    {"type": "text", "text": f"\n**Recent Notable Articles ({current_year}):**\n"}
                )

                for i, article_data in enumerate(recent_articles[:3], 1):
                    article_text = self._format_article_summary(article_data, i)
                    content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in analyze_research_trends: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_compare_articles(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle article comparison."""
        try:
            pmids = arguments.get("pmids", [])
            if len(pmids) < 2 or len(pmids) > 5:
                return MCPResponse(
                    content=[{"type": "text", "text": "Please provide 2-5 PMIDs for comparison"}],
                    is_error=True,
                )

            comparison_fields = arguments.get(
                "comparison_fields", ["authors", "methods", "conclusions"]
            )

            # Get article details
            articles = await self.pubmed_client.get_article_details(
                pmids=pmids, include_abstracts=True, cache=self.cache
            )

            if len(articles) < 2:
                return MCPResponse(
                    content=[
                        {"type": "text", "text": "Not enough valid articles found for comparison"}
                    ],
                    is_error=True,
                )

            content = []
            content.append(
                {"type": "text", "text": f"**Comparison of {len(articles)} Articles**\n"}
            )

            # Basic comparison
            comparison_text = "**Articles:**\n"
            for i, article in enumerate(articles, 1):
                authors_str = format_authors(
                    [f"{a.first_name or a.initials} {a.last_name}" for a in article.authors[:3]]
                )
                comparison_text += f"{i}. {article.title}\n"
                comparison_text += f"   Authors: {authors_str}\n"
                comparison_text += (
                    f"   Journal: {article.journal.title} ({format_date(article.pub_date)})\n"
                )
                comparison_text += f"   PMID: {article.pmid}\n\n"

            content.append({"type": "text", "text": comparison_text})

            # Compare specific fields
            if "mesh_terms" in comparison_fields:
                mesh_comparison = "**MeSH Terms Comparison:**\n"
                for i, article in enumerate(articles, 1):
                    mesh_terms = [term.descriptor_name for term in article.mesh_terms[:5]]
                    mesh_comparison += f"{i}. {', '.join(mesh_terms)}\n"

                content.append({"type": "text", "text": mesh_comparison})

            if "abstracts" in comparison_fields:
                content.append({"type": "text", "text": "**Abstracts:**\n"})

                for i, article in enumerate(articles, 1):
                    abstract_text = truncate_text(article.abstract or "No abstract available", 200)
                    content.append({"type": "text", "text": f"{i}. {abstract_text}\n"})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in compare_articles: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_get_journal_metrics(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle journal metrics request."""
        try:
            journal_name = arguments.get("journal_name", "")
            if not journal_name:
                return MCPResponse(
                    content=[{"type": "text", "text": "Journal name is required"}], is_error=True
                )

            include_recent_articles = arguments.get("include_recent_articles", True)

            # Get recent articles from the journal
            current_year = datetime.now().year
            search_result = await self.pubmed_client.search_articles(
                query=f'"{journal_name}"[Journal]',
                max_results=50,
                date_from=f"{current_year}/01/01",
                sort_order=SortOrder.PUBLICATION_DATE,
                cache=self.cache,
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Journal Metrics: {journal_name}**\n\n"
                    f"Articles in {current_year}: {search_result.total_results:,}\n"
                    f"Sample Size: {search_result.returned_results}\n",
                }
            )

            # Analyze article types
            if search_result.articles:
                article_types = {}
                for article_data in search_result.articles:
                    for article_type in article_data.get("article_types", []):
                        article_types[article_type] = article_types.get(article_type, 0) + 1

                if article_types:
                    types_text = "**Article Types Distribution:**\n"
                    for article_type, count in sorted(
                        article_types.items(), key=lambda x: x[1], reverse=True
                    )[:5]:
                        percentage = (count / len(search_result.articles)) * 100
                        types_text += f"• {article_type}: {count} ({percentage:.1f}%)\n"

                    content.append({"type": "text", "text": types_text})

            # Show recent notable articles
            if include_recent_articles and search_result.articles:
                content.append({"type": "text", "text": f"\n**Recent Articles:**\n"})

                for i, article_data in enumerate(search_result.articles[:5], 1):
                    article_text = self._format_article_summary(article_data, i)
                    content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in get_journal_metrics: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    async def _handle_advanced_search(self, arguments: Dict[str, Any]) -> MCPResponse:
        """Handle advanced search with multiple criteria."""
        try:
            search_terms = arguments.get("search_terms", [])
            if not search_terms:
                return MCPResponse(
                    content=[{"type": "text", "text": "Search terms are required"}], is_error=True
                )

            max_results = arguments.get("max_results", 50)
            filters = arguments.get("filters", {})

            # Build complex query
            query_parts = []
            for i, term_info in enumerate(search_terms):
                term = term_info.get("term", "")
                field = term_info.get("field", "all")
                operator = term_info.get("operator", "AND") if i > 0 else ""

                if field == "title":
                    field_query = f'"{term}"[Title]'
                elif field == "abstract":
                    field_query = f'"{term}"[Abstract]'
                elif field == "author":
                    field_query = f'"{term}"[Author]'
                elif field == "journal":
                    field_query = f'"{term}"[Journal]'
                elif field == "mesh":
                    field_query = f'"{term}"[MeSH Terms]'
                else:
                    field_query = term

                if i > 0:
                    query_parts.append(f" {operator} ")
                query_parts.append(f"({field_query})")

            query = "".join(query_parts)

            # Apply filters
            filter_parts = []
            if filters.get("publication_types"):
                type_queries = [f'"{pt}"[Publication Type]' for pt in filters["publication_types"]]
                filter_parts.append(f"({' OR '.join(type_queries)})")

            if filters.get("languages"):
                lang_queries = [f'"{lang}"[Language]' for lang in filters["languages"]]
                filter_parts.append(f"({' OR '.join(lang_queries)})")

            if filters.get("species"):
                if "humans" in [s.lower() for s in filters["species"]]:
                    filter_parts.append("humans[MeSH Terms]")

            if filter_parts:
                query += " AND " + " AND ".join(filter_parts)

            # Perform search
            search_result = await self.pubmed_client.search_articles(
                query=query, max_results=max_results, cache=self.cache
            )

            content = []
            content.append(
                {
                    "type": "text",
                    "text": f"**Advanced Search Results**\n\n"
                    f"Query: {query}\n"
                    f"Total Results: {search_result.total_results:,}\n"
                    f"Returned: {search_result.returned_results}\n",
                }
            )

            for i, article_data in enumerate(search_result.articles, 1):
                article_text = self._format_article_summary(article_data, i)
                content.append({"type": "text", "text": article_text})

            return MCPResponse(content=content)

        except Exception as e:
            logger.error(f"Error in advanced_search: {e}")
            return MCPResponse(
                content=[{"type": "text", "text": f"Error: {str(e)}"}], is_error=True
            )

    def _format_article_summary(
        self, article_data: Union[Dict[str, Any], "Article"], index: int, highlight_mesh: str = None
    ) -> str:
        """Format article data for summary display."""
        # Handle both Article objects and dictionaries
        if hasattr(article_data, "model_dump"):  # Pydantic v2 Article object
            article_dict = article_data.model_dump()
        elif hasattr(article_data, "dict"):  # Pydantic v1 Article object
            article_dict = article_data.dict()
        elif isinstance(article_data, dict):
            article_dict = article_data
        else:
            # Fallback: try to access as object attributes
            article_dict = {
                "title": getattr(article_data, "title", "Unknown Title"),
                "pmid": getattr(article_data, "pmid", "Unknown"),
                "authors": getattr(article_data, "authors", []),
                "journal": getattr(article_data, "journal", {}),
                "pub_date": getattr(article_data, "pub_date", None),
                "abstract": getattr(article_data, "abstract", ""),
                "mesh_terms": getattr(article_data, "mesh_terms", []),
            }

        title = article_dict.get("title", "Unknown Title")
        pmid = article_dict.get("pmid", "Unknown")

        # Authors
        authors = article_dict.get("authors", [])
        if authors:
            author_names = []
            for author in authors[:3]:  # Show first 3 authors
                if isinstance(author, dict):
                    name = f"{author.get('first_name', author.get('initials', ''))} {author.get('last_name', '')}"
                else:
                    # Handle Author object
                    first_name = getattr(author, "first_name", None) or getattr(
                        author, "initials", ""
                    )
                    last_name = getattr(author, "last_name", "")
                    name = f"{first_name} {last_name}"
                author_names.append(name.strip())

            if len(authors) > 3:
                author_names.append("et al.")
            authors_str = ", ".join(author_names)
        else:
            authors_str = "Unknown authors"

        # Journal and date
        journal_data = article_dict.get("journal", {})
        if isinstance(journal_data, dict):
            journal_title = journal_data.get("title", "Unknown Journal")
        else:
            # Handle Journal object
            journal_title = getattr(journal_data, "title", "Unknown Journal")

        pub_date = format_date(article_dict.get("pub_date"))

        # Abstract
        abstract = article_dict.get("abstract", "")
        abstract_preview = truncate_text(abstract, 150) if abstract else "No abstract available"

        # MeSH terms
        mesh_terms = article_dict.get("mesh_terms", [])
        if mesh_terms and highlight_mesh:
            mesh_str = format_mesh_terms(mesh_terms)
            if highlight_mesh.lower() in mesh_str.lower():
                mesh_str = f"**{mesh_str}**"
        else:
            mesh_str = format_mesh_terms(mesh_terms[:5])  # Show first 5

        article_text = f"""
**{index}. {title}**
Authors: {authors_str}
Journal: {journal_title} ({pub_date})
PMID: {pmid}

{abstract_preview}

MeSH Terms: {mesh_str}
"""
        return article_text

    def _format_article_details(self, article, index: int) -> str:
        """Format detailed article information."""
        # Authors with affiliations
        authors_text = ""
        for i, author in enumerate(article.authors[:5], 1):
            authors_text += f"{i}. {author.first_name or author.initials or ''} {author.last_name}"
            if author.affiliation:
                authors_text += (
                    f" ({author.affiliation[:50]}...)"
                    if len(author.affiliation) > 50
                    else f" ({author.affiliation})"
                )
            authors_text += "\n"

        if len(article.authors) > 5:
            authors_text += f"... and {len(article.authors) - 5} more authors\n"

        # Keywords
        keywords_str = ", ".join(article.keywords[:10]) if article.keywords else "No keywords"

        # DOI and links
        links_text = ""
        if article.doi:
            links_text += f"DOI: https://doi.org/{article.doi}\n"
        if article.pmc_id:
            links_text += f"PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/{article.pmc_id}\n"
        links_text += f"PubMed: https://pubmed.ncbi.nlm.nih.gov/{article.pmid}\n"

        article_text = f"""
**{index}. {article.title}**

**Authors:**
{authors_text}

**Journal:** {article.journal.title}
**Publication Date:** {format_date(article.pub_date)}
**Volume/Issue:** {article.journal.volume or 'N/A'}/{article.journal.issue or 'N/A'}

**Abstract:**
{article.abstract or 'No abstract available'}

**Keywords:** {keywords_str}

**MeSH Terms:** {format_mesh_terms(article.mesh_terms)}

**Article Types:** {', '.join(article.article_types) if article.article_types else 'Not specified'}

**Links:**
{links_text}
"""
        return article_text
