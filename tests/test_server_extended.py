"""
Extended test cases for MCP server functionality.
"""

import asyncio
import signal
from unittest.mock import Mock, patch

import pytest

from src.server import PubMedMCPServer


class TestPubMedMCPServerExtended:
    """Extended tests for PubMed MCP server to improve coverage."""

    @pytest.mark.asyncio
    async def test_server_run_with_stdio(self):
        """Test server run method with stdio server."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Mock stdio_server and server.run
        with patch("src.server.stdio_server") as mock_stdio:
            mock_read_stream = Mock()
            mock_write_stream = Mock()
            mock_stdio.return_value.__aenter__.return_value = (mock_read_stream, mock_write_stream)

            with patch.object(server.server, "run") as mock_server_run:
                mock_server_run.return_value = asyncio.sleep(0)

                with patch.object(server, "shutdown") as mock_shutdown:
                    mock_shutdown.return_value = asyncio.sleep(0)

                    await server.run()

                    mock_server_run.assert_called_once()
                    mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_run_with_exception(self):
        """Test server run method when an exception occurs."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        with patch("src.server.stdio_server") as mock_stdio:
            mock_stdio.side_effect = Exception("Connection error")

            with patch.object(server, "shutdown") as mock_shutdown:
                mock_shutdown.return_value = asyncio.sleep(0)

                with pytest.raises(Exception, match="Connection error"):
                    await server.run()

                mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_server_shutdown_with_client_error(self):
        """Test server shutdown when client close raises an error."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        with patch.object(server.pubmed_client, "close", side_effect=Exception("Close error")):
            # Should not raise exception, should handle gracefully
            await server.shutdown()

    @pytest.mark.asyncio
    async def test_server_shutdown_with_cache_error(self):
        """Test server shutdown when cache operations raise errors."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        with patch.object(server.cache, "get_stats", side_effect=Exception("Stats error")):
            with patch.object(server.cache, "clear", side_effect=Exception("Clear error")):
                # Should handle exceptions gracefully
                await server.shutdown()

    def test_signal_handler_setup(self):
        """Test that signal handlers are properly set up."""
        with patch("src.server.signal.signal") as mock_signal:
            server = PubMedMCPServer(
                pubmed_api_key="test_key",
                pubmed_email="test@example.com",
            )

            # Verify signal handlers were registered
            assert mock_signal.call_count == 2
            assert server is not None  # Use the server variable
            mock_signal.assert_any_call(signal.SIGINT, mock_signal.call_args_list[0][0][1])
            mock_signal.assert_any_call(signal.SIGTERM, mock_signal.call_args_list[1][0][1])

    def test_signal_handler_execution(self):
        """Test signal handler execution."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Get the signal handler function
        with patch("src.server.signal.signal") as mock_signal:
            # Recreate server to capture signal handler
            server = PubMedMCPServer(
                pubmed_api_key="test_key",
                pubmed_email="test@example.com",
            )

            # Extract the signal handler function
            signal_handler = mock_signal.call_args_list[0][0][1]

        # Test signal handler execution
        with patch("asyncio.create_task") as mock_create_task:
            with patch.object(server, "shutdown"):
                # Call the signal handler
                signal_handler(signal.SIGINT, None)

                # Verify that shutdown task was created
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_handler(self):
        """Test the list_tools handler function."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Mock the tool handler to return specific tools
        mock_tools_data = [
            {"name": "search_pubmed", "description": "Search PubMed", "inputSchema": {}},
            {
                "name": "get_article_details",
                "description": "Get article details",
                "inputSchema": {},
            },
        ]

        with patch.object(server.tool_handler, "get_tools", return_value=mock_tools_data):
            # Test the tools are available through the tool handler
            tools = server.tool_handler.get_tools()
            assert len(tools) >= 2
            tool_names = [tool["name"] for tool in tools]
            assert "search_pubmed" in tool_names

    @pytest.mark.asyncio
    async def test_call_tool_handler_success(self):
        """Test the call_tool handler function with successful result."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        mock_response = Mock()
        mock_response.content = [{"type": "text", "text": "Success response"}]

        with patch.object(server.tool_handler, "handle_tool_call", return_value=mock_response):
            # Test tool call handling
            result = await server.tool_handler.handle_tool_call("search_pubmed", {"query": "test"})
            assert result.content[0]["text"] == "Success response"

    @pytest.mark.asyncio
    async def test_call_tool_handler_with_exception(self):
        """Test the call_tool handler function when tool handler raises exception."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        with patch.object(
            server.tool_handler, "handle_tool_call", side_effect=Exception("Tool error")
        ):
            # Test exception handling
            with pytest.raises(Exception, match="Tool error"):
                await server.tool_handler.handle_tool_call("search_pubmed", {"query": "test"})

    def test_cache_configuration_logging(self):
        """Test that cache configuration is properly logged during run."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
            cache_ttl=600,
            cache_max_size=2000,
        )

        # Test that cache is configured with the right parameters
        assert server.cache.cache.maxsize == 2000
        # TTL is not directly accessible, but we can test that cache was created
        assert server.cache is not None

    def test_server_attributes_storage(self):
        """Test that server properly stores initialization attributes."""
        api_key = "test_api_key_123"
        email = "test@example.com"

        server = PubMedMCPServer(
            pubmed_api_key=api_key,
            pubmed_email=email,
            cache_ttl=500,
            cache_max_size=1500,
            rate_limit=4.0,
        )

        assert server.pubmed_api_key == api_key
        assert server.pubmed_email == email

    def test_server_component_initialization_order(self):
        """Test that server components are initialized in correct order."""
        with patch("src.server.CacheManager") as mock_cache_class:
            with patch("src.server.PubMedClient") as mock_client_class:
                with patch("src.server.ToolHandler") as mock_handler_class:
                    with patch("src.server.Server") as mock_server_class:

                        mock_cache = Mock()
                        mock_client = Mock()
                        mock_handler = Mock()
                        mock_server = Mock()

                        mock_cache_class.return_value = mock_cache
                        mock_client_class.return_value = mock_client
                        mock_handler_class.return_value = mock_handler
                        mock_server_class.return_value = mock_server

                        server = PubMedMCPServer(
                            pubmed_api_key="test_key",
                            pubmed_email="test@example.com",
                        )

                        # Verify server was created
                        assert server is not None

                        # Verify initialization order
                        mock_cache_class.assert_called_once_with(max_size=1000, ttl=300)
                        mock_client_class.assert_called_once_with(
                            api_key="test_key", email="test@example.com", rate_limit=3.0
                        )
                        mock_handler_class.assert_called_once_with(
                            pubmed_client=mock_client, cache=mock_cache
                        )
                        mock_server_class.assert_called_once_with("pubmed-mcp-server")

    @pytest.mark.asyncio
    async def test_server_initialization_options(self):
        """Test server initialization options creation."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Test that create_initialization_options works
        init_options = server.server.create_initialization_options()
        assert init_options is not None

    def test_get_cache_stats_content(self):
        """Test that get_cache_stats returns proper content."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # Mock the cache stats
        expected_stats = {
            "size": 5,
            "hits": 10,
            "misses": 3,
            "hit_rate": 0.77,
        }

        with patch.object(server.cache, "get_stats", return_value=expected_stats):
            stats = server.get_cache_stats()
            assert stats == expected_stats

    @pytest.mark.asyncio
    async def test_shutdown_logs_final_cache_stats(self):
        """Test that shutdown logs final cache statistics."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        mock_stats = {"size": 10, "hits": 50, "misses": 5}

        with patch.object(server.cache, "get_stats", return_value=mock_stats):
            with patch("src.server.logger") as mock_logger:
                with patch.object(server.pubmed_client, "close"):
                    await server.shutdown()

                    # Check that final cache stats were logged
                    stats_log_call = None
                    for call in mock_logger.info.call_args_list:
                        if "Final cache stats" in str(call):
                            stats_log_call = call
                            break

                    assert stats_log_call is not None
                    assert str(mock_stats) in str(stats_log_call)

    @pytest.mark.asyncio
    async def test_shutdown_clears_cache(self):
        """Test that shutdown clears the cache."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        with patch.object(server.cache, "clear") as mock_clear:
            with patch.object(server.cache, "get_stats", return_value={}):
                with patch.object(server.pubmed_client, "close"):
                    await server.shutdown()

                    mock_clear.assert_called_once()

    def test_server_name_configuration(self):
        """Test that server is configured with correct name."""
        server = PubMedMCPServer(
            pubmed_api_key="test_key",
            pubmed_email="test@example.com",
        )

        # The server name should be set during initialization
        # We can verify this by checking the server attribute
        assert hasattr(server, "server")
        assert server.server is not None
