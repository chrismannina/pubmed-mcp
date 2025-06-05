"""
MCP server for PubMed literature search and management.

This module implements the Model Context Protocol server that handles
communication with MCP clients and delegates requests to appropriate handlers.
"""

import asyncio
import logging
import signal
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .pubmed_client import PubMedClient
from .tool_handler import ToolHandler
from .utils import CacheManager

logger = logging.getLogger(__name__)


class PubMedMCPServer:
    """Main PubMed MCP server."""

    def __init__(
        self,
        pubmed_api_key: str,
        pubmed_email: str,
        cache_ttl: int = 300,
        cache_max_size: int = 1000,
        rate_limit: float = 3.0,
    ) -> None:
        """
        Initialize PubMed MCP server.

        Args:
            pubmed_api_key: NCBI API key
            pubmed_email: Email for NCBI API
            cache_ttl: Cache time to live in seconds
            cache_max_size: Maximum cache size
            rate_limit: API rate limit (requests per second)
        """
        self.pubmed_api_key = pubmed_api_key
        self.pubmed_email = pubmed_email

        # Initialize components
        self.cache = CacheManager(max_size=cache_max_size, ttl=cache_ttl)
        self.pubmed_client = PubMedClient(
            api_key=pubmed_api_key, email=pubmed_email, rate_limit=rate_limit
        )
        self.tool_handler = ToolHandler(pubmed_client=self.pubmed_client, cache=self.cache)

        # Initialize MCP server
        self.server = Server("pubmed-mcp-server")
        self._setup_handlers()
        self._setup_error_handling()

    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            tools_data = self.tool_handler.get_tools()
            return [Tool(**tool) for tool in tools_data]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Handle tool calls."""
            try:
                result = await self.tool_handler.handle_tool_call(name, arguments)
                return result.content
            except Exception as e:
                logger.error(f"Error in tool call {name}: {e}")
                return [
                    {
                        "type": "text",
                        "text": f"Error executing tool {name}: {str(e)}",
                    }
                ]

    def _setup_error_handling(self) -> None:
        """Set up error handling and signal handlers."""

        def signal_handler(signum: int, frame) -> None:
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self) -> None:
        """Run the MCP server."""
        try:
            logger.info("Starting PubMed MCP server...")
            cache_config = (
                f"Cache configuration: TTL={self.cache.cache.ttl}s, "
                f"Max Size={self.cache.cache.maxsize}"
            )
            logger.info(cache_config)

            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )

        except Exception as e:
            logger.error(f"Error running server: {e}")
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shutdown the server."""
        try:
            logger.info("Shutting down PubMed MCP server...")

            # Close PubMed client
            if self.pubmed_client:
                await self.pubmed_client.close()

            # Clear cache and show final stats
            if self.cache:
                cache_stats = self.cache.get_stats()
                logger.info(f"Final cache stats: {cache_stats}")
                self.cache.clear()

            logger.info("Server shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics."""
        return self.cache.get_stats()
