#!/usr/bin/env python3
"""
PubMed MCP Server

A comprehensive Model Context Protocol server for PubMed literature search
and management. Provides advanced search capabilities, citation formatting,
and research analysis tools.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from src.server import PubMedMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables and .env file."""
    # Set up logger first
    logger = logging.getLogger(__name__)

    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv()

    # Required configuration
    api_key = os.getenv("PUBMED_API_KEY")
    email = os.getenv("PUBMED_EMAIL")

    if not api_key:
        logger.error("PUBMED_API_KEY environment variable is required")
        print("Error: PUBMED_API_KEY environment variable is required")
        print("Please set PUBMED_API_KEY in your environment or .env file")
        sys.exit(1)

    if not email:
        logger.error("PUBMED_EMAIL environment variable is required")
        print("Error: PUBMED_EMAIL environment variable is required")
        print("Please set PUBMED_EMAIL in your environment or .env file")
        sys.exit(1)

    # Optional configuration with defaults
    try:
        cache_ttl = int(os.getenv("CACHE_TTL", "300"))
        cache_max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
        rate_limit = float(os.getenv("RATE_LIMIT", "3.0"))
    except ValueError as e:
        logger.error(f"Invalid configuration value: {e}")
        print(f"Error: Invalid configuration value: {e}")
        sys.exit(1)

    config = {
        "pubmed_api_key": api_key,
        "pubmed_email": email,
        "cache_ttl": cache_ttl,
        "cache_max_size": cache_max_size,
        "rate_limit": rate_limit,
        "log_level": os.getenv("LOG_LEVEL", "info"),
    }

    # Set up logging
    log_level = config.get("log_level", "info")
    try:
        level = getattr(logging, str(log_level).upper())
        logger.setLevel(level)
    except AttributeError:
        # Fallback to INFO if invalid log level
        logger.setLevel(logging.INFO)

    return config


async def main() -> None:
    """Main entry point."""
    try:
        logger.info("Initializing PubMed MCP Server...")

        # Load configuration
        config = load_config()

        logger.info("Configuration loaded successfully")
        logger.info(f"Rate limit: {config['rate_limit']} requests/second")
        logger.info(f"Cache: {config['cache_max_size']} items, " f"{config['cache_ttl']}s TTL")

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

        logger.info("PubMed MCP Server started on stdin/stdout transport")

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
