"""
Utility functions and classes for the PubMed MCP Server.

This module contains common utilities including caching, rate limiting,
and data formatting functions.
"""

import asyncio
import hashlib
import logging
import re
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

# Type: ignore for cachetools since types-cachetools isn't available
from cachetools import TTLCache  # type: ignore
from dateutil import parser  # type: ignore

logger = logging.getLogger(__name__)


class CacheManager:
    """Enhanced cache manager with TTL and size limits."""

    def __init__(self, max_size: int = 1000, ttl: int = 300) -> None:
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of items to store
            ttl: Time to live in seconds
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self.stats = {"hits": 0, "misses": 0, "sets": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        try:
            value = self.cache.get(key)
            if value is not None:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss for key: {key}")
                return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache."""
        try:
            self.cache[key] = value
            self.stats["sets"] += 1
            logger.debug(f"Cached item with key: {key}")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    def generate_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key from prefix and parameters."""
        key_parts = [str(arg) for arg in args]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                if isinstance(v, (list, dict)):
                    # Convert complex types to string for consistent hashing
                    v = str(sorted(v.items()) if isinstance(v, dict) else sorted(v))
                key_parts.append(f"{k}={v}")

        key_string = ":".join(key_parts)
        # Use hash for very long keys to avoid key length issues
        if len(key_string) > 200:
            return f"{key_string}:{hashlib.md5(key_string.encode()).hexdigest()}"
        return key_string

    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()
        logger.debug("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate, 3),
            "sets": self.stats["sets"],
        }


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, rate: float = 3.0) -> None:
        """
        Initialize rate limiter.

        Args:
            rate: Maximum requests per second
        """
        self.rate = rate
        self.tokens = rate
        self.last_update = time.time()

    async def acquire(self) -> None:
        """Acquire a token (wait if necessary)."""
        current_time = time.time()
        elapsed = current_time - self.last_update

        # Add tokens based on elapsed time
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_update = current_time

        if self.tokens >= 1:
            self.tokens -= 1
        else:
            # Calculate wait time for next token
            wait_time = (1 - self.tokens) / self.rate
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            self.tokens = 0


def rate_limited(limiter: "RateLimiter") -> Callable[[Callable], Callable]:
    """Decorator to apply rate limiting to a function."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def format_authors(authors: List[str]) -> str:
    """Format author list for display."""
    if not authors:
        return "Unknown authors"

    if len(authors) == 1:
        return authors[0]
    elif len(authors) <= 3:
        return ", ".join(authors[:-1]) + f" and {authors[-1]}"
    else:
        return f"{authors[0]} et al."


def format_date(date_str: Optional[str]) -> str:
    """Format publication date for display."""
    if not date_str:
        return "Unknown date"

    # Handle various date formats from PubMed
    try:
        parsed_date = parser.parse(date_str)
        return parsed_date.strftime("%Y %b %d")
    except Exception:
        return date_str


def truncate_text(text: str, max_length: int = 300, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_mesh_terms(mesh_terms: List[Dict[str, Any]]) -> str:
    """Format MeSH terms for display."""
    if not mesh_terms:
        return "No MeSH terms"

    major_terms = []
    other_terms = []

    for term in mesh_terms:
        # Handle both dict and MeSHTerm object formats
        if hasattr(term, "major_topic"):  # MeSHTerm object
            is_major = getattr(term, "major_topic", False)
            descriptor = getattr(term, "descriptor_name", "")
        else:  # Dictionary format
            is_major = term.get("major_topic", False)
            descriptor = term.get("descriptor_name", "")

        if is_major:
            major_terms.append(descriptor)
        else:
            other_terms.append(descriptor)

    formatted = []
    if major_terms:
        formatted.append("Major: " + ", ".join(major_terms[:3]))
    if other_terms:
        formatted.append("Other: " + ", ".join(other_terms[:5]))

    return "; ".join(formatted)


def build_search_query(
    base_query: str,
    authors: Optional[List[str]] = None,
    journals: Optional[List[str]] = None,
    mesh_terms: Optional[List[str]] = None,
    article_types: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    language: Optional[str] = None,
    has_abstract: Optional[bool] = None,
    has_full_text: Optional[bool] = None,
    humans_only: Optional[bool] = None,
) -> str:
    """Build a complex PubMed search query with filters."""

    query_parts = [f"({base_query})"]

    if authors:
        author_queries = [f'"{author}"[Author]' for author in authors]
        query_parts.append(f"({' OR '.join(author_queries)})")

    if journals:
        journal_queries = [f'"{journal}"[Journal]' for journal in journals]
        query_parts.append(f"({' OR '.join(journal_queries)})")

    if mesh_terms:
        mesh_queries = [f'"{term}"[MeSH Terms]' for term in mesh_terms]
        query_parts.append(f"({' OR '.join(mesh_queries)})")

    if article_types:
        type_queries = [f'"{article_type}"[Publication Type]' for article_type in article_types]
        query_parts.append(f"({' OR '.join(type_queries)})")

    if date_from or date_to:
        date_query = ""
        if date_from and date_to:
            date_query = f'("{date_from}"[Date - Publication] : "{date_to}"[Date - Publication])'
        elif date_from:
            date_query = f'"{date_from}"[Date - Publication] : "3000"[Date - Publication]'
        elif date_to:
            date_query = f'"1800"[Date - Publication] : "{date_to}"[Date - Publication]'

        if date_query:
            query_parts.append(date_query)

    if language:
        query_parts.append(f'"{language}"[Language]')

    if has_abstract:
        query_parts.append("hasabstract[text word]")

    if has_full_text:
        query_parts.append("free full text[sb]")

    if humans_only:
        query_parts.append("humans[MeSH Terms]")

    return " AND ".join(query_parts)


def extract_pmids_from_text(text: str) -> List[str]:
    """Extract PMIDs from text using regex."""
    pmid_pattern = r"\b\d{8,9}\b"  # PMIDs are typically 8-9 digits
    pmids = re.findall(pmid_pattern, text)
    return [pmid for pmid in pmids if validate_pmid(pmid)]


def validate_pmid(pmid: str) -> bool:
    """Validate PMID format."""
    if not pmid or not pmid.isdigit():
        return False
    return 7 <= len(pmid) <= 9  # PMIDs are typically 7-9 digits


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
