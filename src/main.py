#!/usr/bin/env python3
"""
PubMed MCP Server

A comprehensive Model Context Protocol server for PubMed literature search and management.
Provides advanced search capabilities, citation formatting, and research analysis tools.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from .server import PubMedMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""

    # Load .env file if it exists
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded configuration from {env_path}")

    # Required configuration
    config = {
        "pubmed_api_key": os.getenv("PUBMED_API_KEY", ""),
        "pubmed_email": os.getenv("PUBMED_EMAIL", ""),
        "cache_ttl": int(os.getenv("CACHE_TTL", "300")),
        "cache_max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
        "rate_limit": float(os.getenv("RATE_LIMIT", "3.0")),
        "log_level": os.getenv("LOG_LEVEL", "info"),
    }

    # Validate required configuration
    required_vars = ["pubmed_api_key", "pubmed_email"]
    missing_vars = [var for var in required_vars if not config[var]]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment variables")
        logger.error("Required variables:")
        logger.error("  PUBMED_API_KEY - Your NCBI API key")
        logger.error("  PUBMED_EMAIL - Your email address for NCBI")
        sys.exit(1)

    # Set log level
    log_level = getattr(logging, config["log_level"].upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)

    return config


async def main() -> None:
    """Main entry point."""
    try:
        logger.info("Initializing PubMed MCP Server...")

        # Load configuration
        config = load_config()

        logger.info("Configuration loaded successfully")
        logger.info(f"Rate limit: {config['rate_limit']} requests/second")
        logger.info(f"Cache: {config['cache_max_size']} items, {config['cache_ttl']}s TTL")

        # Initialize and start server
        server = PubMedMCPServer(
            pubmed_api_key=config["pubmed_api_key"],
            pubmed_email=config["pubmed_email"],
            cache_ttl=config["cache_ttl"],
            cache_max_size=config["cache_max_size"],
            rate_limit=config["rate_limit"],
        )

        logger.info("Starting server...")
        await server.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def cli_main() -> None:
    """CLI entry point for setuptools."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
