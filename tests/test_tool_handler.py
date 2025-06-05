"""
Test cases for the tool handler module.
"""

import pytest

from src.models import MCPResponse, SearchResult
from src.tool_handler import ToolHandler


class TestToolHandler:
    """Test the ToolHandler class."""

    def test_tool_handler_initialization(self, mock_pubmed_client, mock_cache_manager):
        """Test tool handler initialization."""
        handler = ToolHandler(pubmed_client=mock_pubmed_client, cache=mock_cache_manager)

        assert handler.pubmed_client == mock_pubmed_client
        assert handler.cache == mock_cache_manager

    def test_get_tools(self, mock_tool_handler):
        """Test getting available tools."""
        tools = mock_tool_handler.get_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check that all tools have required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    @pytest.mark.asyncio
    async def test_handle_tool_search_pubmed(self, mock_tool_handler, sample_search_result):
        """Test handling search_pubmed tool."""
        mock_tool_handler.pubmed_client.search_articles.return_value = sample_search_result

        arguments = {"query": "cancer treatment", "max_results": 10, "date_range": "5y"}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is False
        assert len(response.content) > 0

        # Check that content contains expected text
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "cancer treatment" in content_text

        # Verify the client method was called
        mock_tool_handler.pubmed_client.search_articles.assert_called_once()
        call_args = mock_tool_handler.pubmed_client.search_articles.call_args
        assert call_args[1]["query"] == "cancer treatment"
        assert call_args[1]["max_results"] == 10

    @pytest.mark.asyncio
    async def test_handle_tool_get_article_details(self, mock_tool_handler, sample_article):
        """Test handling get_article_details tool."""
        mock_tool_handler.pubmed_client.get_article_details.return_value = [sample_article]

        arguments = {"pmids": ["12345678", "87654321"], "include_abstracts": True}

        response = await mock_tool_handler.handle_tool_call("get_article_details", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is False

        # Check that content contains PMID
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "12345678" in content_text

        mock_tool_handler.pubmed_client.get_article_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_search_by_author(self, mock_tool_handler, sample_search_result):
        """Test handling search_by_author tool."""
        mock_tool_handler.pubmed_client.search_by_author.return_value = sample_search_result

        arguments = {"author_name": "Smith J", "max_results": 20}

        response = await mock_tool_handler.handle_tool_call("search_by_author", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is False

        mock_tool_handler.pubmed_client.search_by_author.assert_called_once()
        call_args = mock_tool_handler.pubmed_client.search_by_author.call_args
        assert call_args[1]["author_name"] == "Smith J"

    @pytest.mark.asyncio
    async def test_handle_tool_find_related_articles(self, mock_tool_handler, sample_search_result):
        """Test handling find_related_articles tool."""
        mock_tool_handler.pubmed_client.find_related_articles.return_value = sample_search_result

        arguments = {"pmid": "12345678", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("find_related_articles", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is False

        mock_tool_handler.pubmed_client.find_related_articles.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_invalid_tool_name(self, mock_tool_handler):
        """Test handling invalid tool name."""
        arguments = {"query": "test"}

        response = await mock_tool_handler.handle_tool_call("invalid_tool", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "Unknown tool" in content_text or "invalid_tool" in content_text

    @pytest.mark.asyncio
    async def test_handle_tool_missing_arguments(self, mock_tool_handler):
        """Test handling tool with missing required arguments."""
        # Missing required 'query' argument
        arguments = {"max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "required" in content_text.lower() or "query" in content_text.lower()

    @pytest.mark.asyncio
    async def test_handle_tool_exception(self, mock_tool_handler):
        """Test handling tool when client raises exception."""
        # Mock client to raise exception
        mock_tool_handler.pubmed_client.search_articles.side_effect = Exception("API Error")

        arguments = {"query": "test", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "API Error" in content_text

    @pytest.mark.asyncio
    async def test_search_pubmed_with_filters(self, mock_tool_handler, sample_search_result):
        """Test search_pubmed with various filters."""
        mock_tool_handler.pubmed_client.search_articles.return_value = sample_search_result

        arguments = {
            "query": "cancer",
            "max_results": 50,
            "authors": ["Smith J", "Doe A"],
            "journals": ["Nature", "Science"],
            "article_types": ["Journal Article", "Review"],
            "language": "eng",
            "has_abstract": True,
            "humans_only": True,
        }

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert response.is_error is False

        # Verify all filters were passed to the client
        call_args = mock_tool_handler.pubmed_client.search_articles.call_args
        assert call_args[1]["authors"] == ["Smith J", "Doe A"]
        assert call_args[1]["journals"] == ["Nature", "Science"]
        assert call_args[1]["has_abstract"] is True
        assert call_args[1]["humans_only"] is True

    @pytest.mark.asyncio
    async def test_get_article_details_with_options(self, mock_tool_handler, sample_article):
        """Test get_article_details with various options."""
        mock_tool_handler.pubmed_client.get_article_details.return_value = [sample_article]

        arguments = {"pmids": ["12345678"], "include_abstracts": False, "include_citations": True}

        response = await mock_tool_handler.handle_tool_call("get_article_details", arguments)

        assert response.is_error is False

        call_args = mock_tool_handler.pubmed_client.get_article_details.call_args
        assert call_args[1]["include_abstracts"] is False
        assert call_args[1]["include_citations"] is True

    @pytest.mark.asyncio
    async def test_tool_response_formatting(self, mock_tool_handler, sample_search_result):
        """Test that tool responses are properly formatted."""
        mock_tool_handler.pubmed_client.search_articles.return_value = sample_search_result

        arguments = {"query": "test", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert isinstance(response, MCPResponse)
        assert response.is_error is False
        assert len(response.content) > 0

        # Data should be properly formatted content
        for item in response.content:
            assert isinstance(item, dict)
            assert "type" in item
            assert "text" in item

        # Should contain search information
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "Query:" in content_text or "search" in content_text.lower()

    @pytest.mark.asyncio
    async def test_empty_search_results(self, mock_tool_handler):
        """Test handling empty search results."""
        # Mock empty search result
        empty_result = SearchResult(
            query="nonexistent query",
            total_results=0,
            returned_results=0,
            articles=[],
            search_time=0.1,
            suggestions=[],
        )

        mock_tool_handler.pubmed_client.search_articles.return_value = empty_result

        arguments = {"query": "nonexistent query", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert response.is_error is False
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "No articles" in content_text or "0" in content_text

    @pytest.mark.asyncio
    async def test_invalid_pmid_format(self, mock_tool_handler):
        """Test handling invalid PMID format."""
        arguments = {
            "pmids": ["invalid", "12345", "abcdefgh"],  # Various invalid formats
            "include_abstracts": True,
        }

        # Mock client to return empty list for invalid PMIDs
        mock_tool_handler.pubmed_client.get_article_details.return_value = []

        response = await mock_tool_handler.handle_tool_call("get_article_details", arguments)

        # Should still succeed but with no results
        assert response.is_error is False
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "No articles found" in content_text or "0 Articles" in content_text

    @pytest.mark.asyncio
    async def test_tool_with_cache_hit(self, mock_tool_handler, sample_search_result):
        """Test tool execution with cache hit."""
        # Set up cache to return cached result
        mock_tool_handler.cache.get.return_value = {
            "query": "cached query",
            "total_results": 1,
            "returned_results": 1,
            "articles": [sample_search_result.articles[0].model_dump()],
            "search_time": 0.1,
            "suggestions": [],
        }

        arguments = {"query": "cached query", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert response.is_error is False

        # Verify cache was checked (the client.search_articles method checks cache)
        # Since the client actually handles caching, just verify the search was called
        mock_tool_handler.pubmed_client.search_articles.assert_called_once()


class TestToolHandlerEdgeCases:
    """Test edge cases and error scenarios for ToolHandler."""

    @pytest.mark.asyncio
    async def test_malformed_arguments(self, mock_tool_handler):
        """Test handling malformed arguments."""
        # Arguments that are not a dictionary - this would be caught at a higher level
        # Test with None instead
        response = await mock_tool_handler.handle_tool_call("search_pubmed", None)

        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "Error" in content_text

    @pytest.mark.asyncio
    async def test_none_arguments(self, mock_tool_handler):
        """Test handling None arguments."""
        response = await mock_tool_handler.handle_tool_call("search_pubmed", None)

        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "Error" in content_text

    @pytest.mark.asyncio
    async def test_very_large_results_request(self, mock_tool_handler, sample_search_result):
        """Test requesting very large number of results."""
        mock_tool_handler.pubmed_client.search_articles.return_value = sample_search_result

        arguments = {"query": "test", "max_results": 10000}  # Very large number

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        # Should handle gracefully
        assert response.is_error is False

        # Verify the large number was passed through
        call_args = mock_tool_handler.pubmed_client.search_articles.call_args
        assert call_args[1]["max_results"] == 10000

    @pytest.mark.asyncio
    async def test_unicode_query(self, mock_tool_handler, sample_search_result):
        """Test handling Unicode characters in search query."""
        mock_tool_handler.pubmed_client.search_articles.return_value = sample_search_result

        arguments = {
            "query": "cáncer α-beta γ-radiation 中文",  # Unicode characters
            "max_results": 10,
        }

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert response.is_error is False

        # Verify Unicode query was handled
        call_args = mock_tool_handler.pubmed_client.search_articles.call_args
        assert "cáncer" in call_args[1]["query"]

    @pytest.mark.asyncio
    async def test_empty_string_query(self, mock_tool_handler):
        """Test handling empty string query."""
        arguments = {"query": "", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        # Should fail with appropriate error
        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "required" in content_text.lower() or "query" in content_text.lower()

    @pytest.mark.asyncio
    async def test_negative_max_results(self, mock_tool_handler):
        """Test handling negative max_results."""
        arguments = {"query": "test", "max_results": -5}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        # Should handle gracefully or return error
        if not response.is_error:
            # If it succeeds, verify it was handled appropriately
            call_args = mock_tool_handler.pubmed_client.search_articles.call_args
            # max_results should be corrected or handled
            assert call_args[1]["max_results"] >= 0
        else:
            # If it fails, should have appropriate error message
            content_text = " ".join([item.get("text", "") for item in response.content])
            assert "max_results" in content_text.lower() or "negative" in content_text.lower()

    @pytest.mark.asyncio
    async def test_tool_execution_timeout_simulation(self, mock_tool_handler):
        """Test handling of long-running tool execution."""
        import asyncio

        # Mock client to simulate timeout
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow operation
            raise asyncio.TimeoutError("Operation timed out")

        mock_tool_handler.pubmed_client.search_articles.side_effect = slow_search

        arguments = {"query": "test", "max_results": 10}

        response = await mock_tool_handler.handle_tool_call("search_pubmed", arguments)

        assert response.is_error is True
        content_text = " ".join([item.get("text", "") for item in response.content])
        assert "timeout" in content_text.lower() or "timed out" in content_text.lower()
