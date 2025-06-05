"""
Extended test cases for tool handler functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models import Article, Author, Journal, MeSHTerm, SearchResult
from src.tool_handler import ToolHandler


class TestToolHandlerExtended:
    """Extended tests for tool handler to improve coverage."""

    @pytest.fixture
    def mock_pubmed_client(self):
        """Create a mock PubMed client."""
        client = Mock()
        client.search_articles = AsyncMock()
        client.get_article_details = AsyncMock()
        client.search_by_author = AsyncMock()
        client.find_related_articles = AsyncMock()
        return client

    @pytest.fixture
    def mock_cache(self):
        """Create a mock cache manager."""
        return Mock()

    @pytest.fixture
    def tool_handler(self, mock_pubmed_client, mock_cache):
        """Create a tool handler with mocked dependencies."""
        return ToolHandler(mock_pubmed_client, mock_cache)

    @pytest.fixture
    def sample_article(self):
        """Create a sample article for testing."""
        return Article(
            pmid="12345678",
            title="Sample Article Title",
            abstract="Sample abstract content.",
            authors=[
                Author(
                    last_name="Smith",
                    first_name="John",
                    initials="J",
                    affiliation="University Hospital",
                )
            ],
            journal=Journal(title="Sample Journal", volume="10", issue="1"),
            pub_date="2023/01/01",
            doi="10.1000/example",
            keywords=["keyword1", "keyword2", "keyword3"],
            mesh_terms=[MeSHTerm(descriptor_name="Sample Term", major_topic=True)],
            article_types=["Journal Article"],
        )

    @pytest.mark.asyncio
    async def test_handle_export_citations(self, tool_handler, mock_pubmed_client, sample_article):
        """Test export citations functionality."""
        mock_pubmed_client.get_article_details.return_value = [sample_article]

        result = await tool_handler._handle_export_citations(
            {"pmids": ["12345678"], "format": "bibtex", "include_abstracts": False}
        )

        assert not result.is_error
        assert len(result.content) == 1
        content_text = result.content[0]["text"]
        assert "Citations in BIBTEX format" in content_text

    @pytest.mark.asyncio
    async def test_handle_export_citations_no_pmids(self, tool_handler):
        """Test export citations with no PMIDs."""
        result = await tool_handler._handle_export_citations({})

        assert result.is_error
        assert "PMIDs parameter is required" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_export_citations_no_articles_found(
        self, tool_handler, mock_pubmed_client
    ):
        """Test export citations when no articles are found."""
        mock_pubmed_client.get_article_details.return_value = []

        result = await tool_handler._handle_export_citations(
            {"pmids": ["99999999"], "format": "apa"}
        )

        assert result.is_error
        assert "No articles found" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_search_mesh_terms(self, tool_handler, mock_pubmed_client, sample_article):
        """Test MeSH term search."""
        search_result = SearchResult(
            query="cancer[MeSH Terms]",
            total_results=100,
            returned_results=1,
            articles=[sample_article],
            search_time=0.5,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_search_mesh_terms({"term": "cancer", "max_results": 20})

        assert not result.is_error
        assert "Articles with MeSH term: cancer" in result.content[0]["text"]
        assert "Total Results: 100" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_search_mesh_terms_no_term(self, tool_handler):
        """Test MeSH term search without term."""
        result = await tool_handler._handle_search_mesh_terms({})

        assert result.is_error
        assert "MeSH term is required" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_search_by_journal(self, tool_handler, mock_pubmed_client, sample_article):
        """Test journal-based search."""
        search_result = SearchResult(
            query="Nature[Journal]",
            total_results=500,
            returned_results=1,
            articles=[sample_article],
            search_time=0.3,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_search_by_journal(
            {
                "journal_name": "Nature",
                "max_results": 20,
                "date_from": "2023/01/01",
                "date_to": "2023/12/31",
            }
        )

        assert not result.is_error
        assert "Recent Articles from Nature" in result.content[0]["text"]
        assert "Total Results: 500" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_search_by_journal_no_name(self, tool_handler):
        """Test journal search without journal name."""
        result = await tool_handler._handle_search_by_journal({})

        assert result.is_error
        assert "Journal name is required" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_get_trending_topics(self, tool_handler, mock_pubmed_client):
        """Test trending topics analysis."""
        # Create articles with keywords for testing
        article_with_keywords = Article(
            pmid="12345678",
            title="Trending Research",
            journal=Journal(title="Test Journal"),
            keywords=["AI", "machine learning", "healthcare"],
        )

        search_result = SearchResult(
            query="trending AND medicine",
            total_results=50,
            returned_results=1,
            articles=[article_with_keywords],
            search_time=0.4,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_get_trending_topics({"category": "AI", "days": 7})

        assert not result.is_error
        assert "Trending Topics in AI" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_get_trending_topics_no_category(self, tool_handler, mock_pubmed_client):
        """Test trending topics without specific category."""
        search_result = SearchResult(
            query="trending AND medicine",
            total_results=30,
            returned_results=0,
            articles=[],
            search_time=0.2,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_get_trending_topics({"days": 14})

        assert not result.is_error
        assert "Trending Topics in Medicine" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_analyze_research_trends(self, tool_handler, mock_pubmed_client):
        """Test research trends analysis."""
        search_result = SearchResult(
            query="cancer treatment",
            total_results=1000,
            returned_results=5,
            articles=[],
            search_time=0.6,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_analyze_research_trends(
            {"topic": "cancer treatment", "years_back": 3, "include_subtopics": True}
        )

        assert not result.is_error
        assert "Research Trends for: cancer treatment" in result.content[0]["text"]
        current_year = datetime.now().year
        assert f"Analysis Period: {current_year - 3} - {current_year}" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_analyze_research_trends_no_topic(self, tool_handler):
        """Test research trends analysis without topic."""
        result = await tool_handler._handle_analyze_research_trends({})

        assert result.is_error
        assert "Topic is required" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_compare_articles(self, tool_handler, mock_pubmed_client, sample_article):
        """Test article comparison."""
        mock_pubmed_client.get_article_details.return_value = [sample_article, sample_article]

        result = await tool_handler._handle_compare_articles(
            {
                "pmids": ["12345678", "87654321"],
                "comparison_fields": ["authors", "mesh_terms", "abstracts"],
            }
        )

        assert not result.is_error
        assert "Comparison of 2 Articles" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_compare_articles_insufficient_pmids(self, tool_handler):
        """Test article comparison with insufficient PMIDs."""
        result = await tool_handler._handle_compare_articles({"pmids": ["12345678"]})

        assert result.is_error
        assert "Please provide 2-5 PMIDs for comparison" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_compare_articles_too_many_pmids(self, tool_handler):
        """Test article comparison with too many PMIDs."""
        pmids = [str(i) for i in range(12345678, 12345684)]  # 6 PMIDs
        result = await tool_handler._handle_compare_articles({"pmids": pmids})

        assert result.is_error
        assert "Please provide 2-5 PMIDs for comparison" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_compare_articles_insufficient_articles(
        self, tool_handler, mock_pubmed_client
    ):
        """Test article comparison when insufficient articles found."""
        mock_pubmed_client.get_article_details.return_value = [
            Article(pmid="12345678", title="Single Article", journal=Journal(title="Test"))
        ]

        result = await tool_handler._handle_compare_articles(
            {"pmids": ["12345678", "87654321", "11111111"]}
        )

        assert result.is_error
        assert "Not enough valid articles found for comparison" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_get_journal_metrics(self, tool_handler, mock_pubmed_client):
        """Test journal metrics functionality."""
        articles_with_types = [
            Article(
                pmid="12345678",
                title="Article 1",
                journal=Journal(title="Test Journal"),
                article_types=["Journal Article", "Research Support"],
            ),
            Article(
                pmid="87654321",
                title="Article 2",
                journal=Journal(title="Test Journal"),
                article_types=["Review"],
            ),
        ]

        search_result = SearchResult(
            query="Test Journal[Journal]",
            total_results=200,
            returned_results=2,
            articles=articles_with_types,
            search_time=0.3,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_get_journal_metrics(
            {"journal_name": "Test Journal", "include_recent_articles": True}
        )

        assert not result.is_error
        assert "Journal Metrics: Test Journal" in result.content[0]["text"]
        current_year = datetime.now().year
        assert f"Articles in {current_year}: 200" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_get_journal_metrics_no_name(self, tool_handler):
        """Test journal metrics without journal name."""
        result = await tool_handler._handle_get_journal_metrics({})

        assert result.is_error
        assert "Journal name is required" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_advanced_search(self, tool_handler, mock_pubmed_client, sample_article):
        """Test advanced search functionality."""
        search_result = SearchResult(
            query="(cancer[Title]) AND (treatment[Abstract])",
            total_results=150,
            returned_results=1,
            articles=[sample_article],
            search_time=0.8,
        )
        mock_pubmed_client.search_articles.return_value = search_result

        result = await tool_handler._handle_advanced_search(
            {
                "search_terms": [
                    {"term": "cancer", "field": "title"},
                    {"term": "treatment", "field": "abstract", "operator": "AND"},
                ],
                "max_results": 50,
                "filters": {
                    "publication_types": ["Journal Article"],
                    "languages": ["eng"],
                    "species": ["humans"],
                },
            }
        )

        assert not result.is_error
        assert "Advanced Search Results" in result.content[0]["text"]
        assert "Total Results: 150" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_advanced_search_no_terms(self, tool_handler):
        """Test advanced search without search terms."""
        result = await tool_handler._handle_advanced_search({})

        assert result.is_error
        assert "Search terms are required" in result.content[0]["text"]

    def test_format_article_summary_with_dict(self, tool_handler):
        """Test article summary formatting with dictionary input."""
        article_dict = {
            "title": "Test Article",
            "pmid": "12345678",
            "authors": [{"first_name": "John", "last_name": "Smith"}],
            "journal": {"title": "Test Journal"},
            "pub_date": "2023/01/01",
            "abstract": "This is a test abstract.",
            "mesh_terms": [{"descriptor_name": "Test Term"}],
        }

        result = tool_handler._format_article_summary(article_dict, 1)

        assert "1. Test Article" in result
        assert "John Smith" in result
        assert "Test Journal" in result
        assert "PMID: 12345678" in result

    def test_format_article_summary_with_object_fallback(self, tool_handler):
        """Test article summary formatting with object fallback."""

        class MockArticle:
            title = "Mock Article"
            pmid = "99999999"
            authors = []
            journal = None
            pub_date = None
            abstract = ""
            mesh_terms = []

        mock_article = MockArticle()
        result = tool_handler._format_article_summary(mock_article, 1)

        assert "1. Mock Article" in result
        assert "PMID: 99999999" in result

    def test_format_article_summary_with_highlight_mesh(self, tool_handler):
        """Test article summary formatting with MeSH term highlighting."""
        article_dict = {
            "title": "Test Article",
            "pmid": "12345678",
            "authors": [],
            "journal": {"title": "Test Journal"},
            "pub_date": None,
            "abstract": "",
            "mesh_terms": [{"descriptor_name": "Cancer"}],
        }

        result = tool_handler._format_article_summary(article_dict, 1, highlight_mesh="cancer")

        assert "**Cancer**" in result  # Should be highlighted

    def test_format_article_details(self, tool_handler, sample_article):
        """Test detailed article formatting."""
        result = tool_handler._format_article_details(sample_article, 1)

        assert "1. Sample Article Title" in result
        assert "**Authors:**" in result
        assert "1. John Smith (University Hospital)" in result
        assert "**Journal:** Sample Journal" in result
        assert "**Publication Date:**" in result
        assert "**Abstract:**" in result
        assert "**Keywords:**" in result
        assert "**MeSH Terms:**" in result
        assert "**Article Types:**" in result
        assert "**Links:**" in result
        assert "https://doi.org/10.1000/example" in result

    def test_format_article_details_many_authors(self, tool_handler):
        """Test article details formatting with many authors."""
        authors = [
            Author(
                last_name=f"Author{i}",
                first_name=f"First{i}",
                initials=f"F{i}",
                affiliation=f"Institution {i}" if i < 3 else None,
            )
            for i in range(8)
        ]

        article = Article(
            pmid="12345678",
            title="Many Authors Article",
            authors=authors,
            journal=Journal(title="Test Journal"),
        )

        result = tool_handler._format_article_details(article, 1)

        assert "... and 3 more authors" in result  # Should show truncation message

    @pytest.mark.asyncio
    async def test_handle_tool_call_exception(self, tool_handler):
        """Test tool call exception handling."""
        # Mock a method to raise an exception
        with patch.object(
            tool_handler, "_handle_search_pubmed", side_effect=Exception("Test error")
        ):
            result = await tool_handler.handle_tool_call("search_pubmed", {"query": "test"})

            assert result.is_error
            assert "Error executing search_pubmed: Test error" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_tool_call_none_arguments(self, tool_handler):
        """Test tool call with None arguments."""
        result = await tool_handler.handle_tool_call("search_pubmed", None)

        assert result.is_error
        assert "Arguments cannot be None" in result.content[0]["text"]

    @pytest.mark.asyncio
    async def test_handle_unknown_tool(self, tool_handler):
        """Test handling of unknown tool."""
        result = await tool_handler.handle_tool_call("unknown_tool", {})

        assert result.is_error
        assert "Unknown tool: unknown_tool" in result.content[0]["text"]
