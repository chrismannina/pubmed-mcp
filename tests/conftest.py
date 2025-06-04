"""
Pytest configuration and fixtures for PubMed MCP Server tests.
"""
import os
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.models import Article, Author, Journal, MCPResponse, SearchResult
from src.pubmed_client import PubMedClient
from src.server import PubMedMCPServer
from src.tool_handler import ToolHandler
from src.utils import CacheManager, RateLimiter


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "pubmed_api_key": "test_api_key_123",
        "pubmed_email": "test@example.com",
        "cache_ttl": 300,
        "cache_max_size": 100,
        "rate_limit": 5.0,
    }


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    limiter = Mock(spec=RateLimiter)
    limiter.acquire = AsyncMock()
    return limiter


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing."""
    cache = Mock(spec=CacheManager)
    cache.get.return_value = None
    cache.set = Mock()
    cache.generate_key.return_value = "test_cache_key"
    cache.get_stats.return_value = {
        "size": 0,
        "max_size": 100,
        "hits": 0,
        "misses": 0,
        "hit_rate": 0.0,
        "sets": 0,
    }
    return cache


@pytest.fixture
def sample_article():
    """Sample article for testing."""
    return Article(
        pmid="12345678",
        title="Test Article Title",
        abstract="This is a test abstract for the article.",
        authors=[
            Author(
                last_name="Smith", first_name="John", initials="J", affiliation="Test University"
            )
        ],
        journal=Journal(
            title="Test Journal",
            iso_abbreviation="Test J",
            issn="1234-5678",
            volume="1",
            issue="1",
            pub_date="2023/01/01",
        ),
        pub_date="2023/01/01",
        doi="10.1234/test.doi",
        article_types=["Journal Article"],
        keywords=["test", "example"],
        languages=["eng"],
    )


@pytest.fixture
def sample_search_result(sample_article):
    """Sample search result for testing."""
    return SearchResult(
        query="test query",
        total_results=1,
        returned_results=1,
        articles=[sample_article],
        search_time=0.5,
        suggestions=[],
    )


@pytest.fixture
def mock_pubmed_client(mock_rate_limiter, sample_search_result):
    """Mock PubMed client for testing."""
    client = Mock(spec=PubMedClient)
    client.rate_limiter = mock_rate_limiter
    client.search_articles = AsyncMock(return_value=sample_search_result)
    client.get_article_details = AsyncMock(return_value=[sample_search_result.articles[0]])
    client.search_by_author = AsyncMock(return_value=sample_search_result)
    client.find_related_articles = AsyncMock(return_value=sample_search_result)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_tool_handler(mock_pubmed_client, mock_cache_manager):
    """Mock tool handler for testing."""
    handler = ToolHandler(
        pubmed_client=mock_pubmed_client,
        cache=mock_cache_manager,  # Fixed: use 'cache' parameter as per actual constructor
    )
    return handler


@pytest.fixture
def mock_server(mock_config, mock_pubmed_client, mock_cache_manager, mock_tool_handler):
    """Mock server for testing."""
    server = Mock(spec=PubMedMCPServer)
    server.pubmed_client = mock_pubmed_client
    server.cache_manager = mock_cache_manager
    server.tool_handler = mock_tool_handler
    server.get_cache_stats.return_value = mock_cache_manager.get_stats()
    return server


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response for testing."""
    response = Mock()
    response.status_code = 200
    response.raise_for_status = Mock()
    response.json.return_value = {
        "esearchresult": {"idlist": ["12345678", "87654321"], "count": "2"}
    }
    response.text = """<?xml version="1.0" ?>
    <PubmedArticleSet>
        <PubmedArticle>
            <MedlineCitation>
                <PMID>12345678</PMID>
                <Article>
                    <ArticleTitle>Test Article</ArticleTitle>
                    <Abstract>
                        <AbstractText>Test abstract</AbstractText>
                    </Abstract>
                    <AuthorList>
                        <Author>
                            <LastName>Smith</LastName>
                            <ForeName>John</ForeName>
                            <Initials>J</Initials>
                        </Author>
                    </AuthorList>
                    <Journal>
                        <Title>Test Journal</Title>
                        <JournalIssue>
                            <Volume>1</Volume>
                            <Issue>1</Issue>
                            <PubDate>
                                <Year>2023</Year>
                                <Month>Jan</Month>
                            </PubDate>
                        </JournalIssue>
                    </Journal>
                </Article>
            </MedlineCitation>
        </PubmedArticle>
    </PubmedArticleSet>"""
    return response
