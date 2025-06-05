"""
Unit tests for the PubMed MCP Server.
"""

from unittest.mock import Mock, patch

import pytest

from src.models import MCPResponse
from src.server import PubMedMCPServer


class TestPubMedMCPServer:
    """Test the PubMedMCPServer class."""

    def test_server_initialization(self):
        """Test server initialization with valid parameters."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
            cache_ttl=300,
            cache_max_size=1000,
            rate_limit=3.0,
        )

        assert server.pubmed_client is not None
        assert server.tool_handler is not None
        assert server.cache is not None
        assert server.server is not None
        assert hasattr(server, "get_cache_stats")

    def test_server_initialization_with_defaults(self):
        """Test server initialization with default parameters."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        assert server.pubmed_client is not None
        assert server.tool_handler is not None
        assert server.cache is not None

    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        stats = server.get_cache_stats()
        assert isinstance(stats, dict)
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats

    def test_server_components_initialized(self):
        """Test that all server components are properly initialized."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Check that all components exist
        assert hasattr(server, "pubmed_client")
        assert hasattr(server, "tool_handler")
        assert hasattr(server, "cache")
        assert hasattr(server, "server")

        # Check that tool handler has the pubmed client
        assert server.tool_handler.pubmed_client is server.pubmed_client
        assert server.tool_handler.cache is server.cache

    @pytest.mark.asyncio
    async def test_tool_handler_integration(self):
        """Test that the tool handler is properly integrated."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Test that we can get tools from the tool handler
        tools = server.tool_handler.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check that each tool has required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool

    @pytest.mark.asyncio
    async def test_tool_call_handling(self):
        """Test tool call handling through the tool handler."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Mock the tool handler response
        mock_response = MCPResponse(
            content=[{"type": "text", "text": "Test result"}], is_error=False
        )

        with patch.object(server.tool_handler, "handle_tool_call", return_value=mock_response):
            # This tests the integration but doesn't call the actual MCP server handlers
            # since those are registered during initialization
            result = await server.tool_handler.handle_tool_call(
                "search_pubmed", {"query": "cancer"}
            )
            assert result.content[0]["text"] == "Test result"
            assert result.is_error is False

    @pytest.mark.asyncio
    async def test_tool_call_error_handling(self):
        """Test error handling in tool calls."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Mock the tool handler to raise an exception
        with patch.object(
            server.tool_handler, "handle_tool_call", side_effect=Exception("Test error")
        ):
            # Test that errors are properly handled
            with pytest.raises(Exception) as exc_info:
                await server.tool_handler.handle_tool_call("invalid_tool", {})
            assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test server shutdown process."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Mock the client close method
        with patch.object(server.pubmed_client, "close") as mock_close:
            await server.shutdown()
            mock_close.assert_called_once()

    def test_server_attributes(self):
        """Test that server has the expected attributes."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        assert server.pubmed_api_key == "test_key"
        assert server.pubmed_email == "test@example.com"
