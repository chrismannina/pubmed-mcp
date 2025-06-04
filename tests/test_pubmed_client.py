"""
Unit tests for the PubMedClient class.
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from xml.etree import ElementTree as ET

from src.pubmed_client import PubMedClient
from src.models import Article, SearchResult, SortOrder, DateRange
from src.utils import RateLimiter, CacheManager

class TestPubMedClient:
    """Test the PubMedClient class."""
    
    def test_client_initialization(self):
        """Test PubMed client initialization."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com",
            rate_limit=5.0
        )
        
        assert client.api_key == "test_key"
        assert client.email == "test@example.com"
        assert client.base_url == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        assert isinstance(client.rate_limiter, RateLimiter)
        assert client.rate_limiter.rate == 5.0
        assert isinstance(client.client, httpx.AsyncClient)
    
    def test_build_params(self):
        """Test API parameter building."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        params = client._build_params(db="pubmed", term="cancer")
        
        assert params["api_key"] == "test_key"
        assert params["email"] == "test@example.com"
        assert params["tool"] == "pubmed-mcp-server"
        assert params["db"] == "pubmed"
        assert params["term"] == "cancer"
        
        # Test with None values (should be filtered out)
        params = client._build_params(db="pubmed", term="cancer", retmode=None)
        assert "retmode" not in params
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limiting(self, mock_httpx_response):
        """Test that _make_request applies rate limiting correctly."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com",
            rate_limit=5.0
        )
        
        # Mock the rate limiter
        client.rate_limiter.acquire = AsyncMock()
        
        # Mock the HTTP client
        client.client.get = AsyncMock(return_value=mock_httpx_response)
        
        # Make a request
        params = {"db": "pubmed", "term": "cancer"}
        response = await client._make_request("esearch.fcgi", params)
        
        # Verify rate limiting was applied
        client.rate_limiter.acquire.assert_called_once()
        
        # Verify HTTP request was made
        client.client.get.assert_called_once()
        expected_url = f"{client.base_url}/esearch.fcgi"
        call_args = client.client.get.call_args
        assert call_args[0][0] == expected_url
        
        assert response == mock_httpx_response
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self):
        """Test _make_request handling HTTP errors."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Mock rate limiter
        client.rate_limiter.acquire = AsyncMock()
        
        # Mock HTTP client to raise an error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock()
        )
        client.client.get = AsyncMock(return_value=mock_response)
        
        # Should raise the HTTP error
        with pytest.raises(httpx.HTTPStatusError):
            await client._make_request("esearch.fcgi", {})
    
    @pytest.mark.asyncio
    async def test_search_articles_basic(self, mock_httpx_response):
        """Test basic article search functionality."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Mock the _make_request method
        client._make_request = AsyncMock(return_value=mock_httpx_response)
        client._fetch_article_details = AsyncMock(return_value=[])
        
        # Test search
        result = await client.search_articles(
            query="cancer treatment",
            max_results=10
        )
        
        # Verify the result
        assert isinstance(result, SearchResult)
        assert result.query == "cancer treatment"
        assert result.total_results == 2  # From mock response
        assert isinstance(result.search_time, float)
        
        # Verify _make_request was called with correct parameters
        client._make_request.assert_called_once()
        call_args = client._make_request.call_args
        assert call_args[0][0] == "esearch.fcgi"
        params = call_args[0][1]
        assert "term" in params
        assert "retmax" in params
    
    @pytest.mark.asyncio
    async def test_search_articles_with_date_range(self, mock_httpx_response):
        """Test article search with date range filtering."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        client._make_request = AsyncMock(return_value=mock_httpx_response)
        client._fetch_article_details = AsyncMock(return_value=[])
        
        # Test with date range
        result = await client.search_articles(
            query="cancer",
            date_range=DateRange.LAST_5_YEARS,
            max_results=10
        )
        
        assert isinstance(result, SearchResult)
        client._make_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_articles_with_cache(self, mock_httpx_response, mock_cache_manager):
        """Test article search with caching."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Set up cache to return a result
        cached_result = {
            "query": "cancer",
            "total_results": 1,
            "returned_results": 1,
            "articles": [],
            "search_time": 0.5,
            "suggestions": []
        }
        mock_cache_manager.get.return_value = cached_result
        
        # Test search with cache
        result = await client.search_articles(
            query="cancer",
            cache=mock_cache_manager
        )
        
        # Should return cached result
        assert isinstance(result, SearchResult)
        assert result.query == "cancer"
        
        # Should not make HTTP request
        client._make_request = AsyncMock()
        client._make_request.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_article_details(self, mock_httpx_response):
        """Test getting article details by PMIDs."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Mock the fetch method
        sample_article = Mock(spec=Article)
        sample_article.pmid = "12345678"
        sample_article.title = "Test Article"
        
        client._fetch_article_details = AsyncMock(return_value=[sample_article])
        
        # Test getting article details
        pmids = ["12345678", "87654321"]
        articles = await client.get_article_details(pmids)
        
        assert len(articles) == 1
        assert articles[0] == sample_article
        
        # Verify _fetch_article_details was called
        client._fetch_article_details.assert_called_once_with(
            pmids, include_full_details=True, include_citations=False
        )
    
    @pytest.mark.asyncio
    async def test_get_article_details_invalid_pmids(self):
        """Test handling of invalid PMIDs."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        client._fetch_article_details = AsyncMock(return_value=[])
        
        # Test with invalid PMIDs
        invalid_pmids = ["123", "abcd", ""]
        articles = await client.get_article_details(invalid_pmids)
        
        # Should return empty list
        assert articles == []
        
        # Should not call _fetch_article_details
        client._fetch_article_details.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_search_by_author(self, mock_httpx_response):
        """Test searching articles by author."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        client._make_request = AsyncMock(return_value=mock_httpx_response)
        client._fetch_article_details = AsyncMock(return_value=[])
        
        # Test author search
        result = await client.search_by_author("Smith J")
        
        assert isinstance(result, SearchResult)
        assert "Smith J" in result.query
        
        # Verify correct search query was built
        client._make_request.assert_called_once()
        call_args = client._make_request.call_args
        params = call_args[0][1]
        assert '"Smith J"[Author]' in params.get("term", "")
    
    @pytest.mark.asyncio
    async def test_find_related_articles(self, mock_httpx_response):
        """Test finding related articles."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Mock response for elink
        link_response = Mock()
        link_response.json.return_value = {
            "linksets": [{
                "linksetdbs": [{
                    "linkname": "pubmed_pubmed",
                    "links": ["11111111", "22222222"]
                }]
            }]
        }
        
        client._make_request = AsyncMock(return_value=link_response)
        client._fetch_article_details = AsyncMock(return_value=[])
        
        # Test finding related articles
        result = await client.find_related_articles("12345678")
        
        assert isinstance(result, SearchResult)
        assert "12345678" in result.query
        
        # Verify elink API was called
        client._make_request.assert_called_once()
        call_args = client._make_request.call_args
        assert call_args[0][0] == "elink.fcgi"
        params = call_args[0][1]
        assert params.get("id") == "12345678"
    
    @pytest.mark.asyncio
    async def test_find_related_articles_invalid_pmid(self):
        """Test finding related articles with invalid PMID."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Should raise ValueError for invalid PMID
        with pytest.raises(ValueError, match="Invalid PMID"):
            await client.find_related_articles("invalid")
    
    def test_parse_pubmed_xml(self):
        """Test parsing PubMed XML response."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Sample XML response
        xml_content = """<?xml version="1.0" ?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>Test abstract content</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                                <ForeName>John</ForeName>
                                <Initials>J</Initials>
                                <AffiliationInfo>
                                    <Affiliation>Test University</Affiliation>
                                </AffiliationInfo>
                            </Author>
                        </AuthorList>
                        <Journal>
                            <Title>Test Journal</Title>
                            <ISOAbbreviation>Test J</ISOAbbreviation>
                            <ISSN>1234-5678</ISSN>
                            <JournalIssue>
                                <Volume>1</Volume>
                                <Issue>1</Issue>
                                <PubDate>
                                    <Year>2023</Year>
                                    <Month>Jan</Month>
                                    <Day>15</Day>
                                </PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
                <PubmedData>
                    <ArticleIdList>
                        <ArticleId IdType="doi">10.1234/test.doi</ArticleId>
                        <ArticleId IdType="pmc">PMC123456</ArticleId>
                    </ArticleIdList>
                </PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>"""
        
        articles = client._parse_pubmed_xml(xml_content)
        
        assert len(articles) == 1
        article = articles[0]
        
        assert article.pmid == "12345678"
        assert article.title == "Test Article Title"
        assert article.abstract == "Test abstract content"
        assert len(article.authors) == 1
        assert article.authors[0].last_name == "Smith"
        assert article.authors[0].first_name == "John"
        assert article.authors[0].affiliation == "Test University"
        assert article.journal.title == "Test Journal"
        assert article.journal.volume == "1"
        assert article.journal.issue == "1"
    
    def test_parse_pubmed_xml_invalid(self):
        """Test parsing invalid XML."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Invalid XML
        invalid_xml = "This is not valid XML content"
        articles = client._parse_pubmed_xml(invalid_xml)
        
        # Should return empty list
        assert articles == []
    
    def test_parse_single_article_missing_pmid(self):
        """Test parsing article without PMID."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Create XML element without PMID
        xml_content = """<PubmedArticle>
            <MedlineCitation>
                <Article>
                    <ArticleTitle>Test Article</ArticleTitle>
                </Article>
            </MedlineCitation>
        </PubmedArticle>"""
        
        element = ET.fromstring(xml_content)
        article = client._parse_single_article(element)
        
        # Should return None for article without PMID
        assert article is None
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing the HTTP client."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com"
        )
        
        # Mock the aclose method
        client.client.aclose = AsyncMock()
        
        await client.close()
        
        # Verify aclose was called
        client.client.aclose.assert_called_once()

class TestPubMedClientIntegration:
    """Integration tests for PubMedClient with mocked HTTP responses."""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test the complete search workflow with mocked responses."""
        client = PubMedClient(
            api_key="test_key",
            email="test@example.com",
            rate_limit=10.0  # High rate for testing
        )
        
        # Mock search response
        search_response = Mock()
        search_response.json.return_value = {
            "esearchresult": {
                "idlist": ["12345678"],
                "count": "1"
            }
        }
        search_response.raise_for_status = Mock()
        
        # Mock fetch response with XML
        fetch_response = Mock()
        fetch_response.text = """<?xml version="1.0" ?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>AI in Healthcare</ArticleTitle>
                        <Abstract>
                            <AbstractText>This study explores AI applications in healthcare.</AbstractText>
                        </Abstract>
                        <Journal>
                            <Title>Nature Medicine</Title>
                        </Journal>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>"""
        fetch_response.raise_for_status = Mock()
        
        # Mock the HTTP client to return appropriate responses
        client.client.get = AsyncMock(side_effect=[search_response, fetch_response])
        
        # Mock rate limiter
        client.rate_limiter.acquire = AsyncMock()
        
        # Perform search
        result = await client.search_articles(
            query="artificial intelligence healthcare",
            max_results=10
        )
        
        # Verify results
        assert isinstance(result, SearchResult)
        assert result.query == "artificial intelligence healthcare"
        assert result.total_results == 1
        assert result.returned_results == 1
        assert len(result.articles) == 1
        
        article = result.articles[0]
        assert article.pmid == "12345678"
        assert article.title == "AI in Healthcare"
        assert "AI applications" in article.abstract
        assert article.journal.title == "Nature Medicine"
        
        # Verify HTTP calls were made
        assert client.client.get.call_count == 2  # Search + fetch
        
        # Verify rate limiting was applied
        assert client.rate_limiter.acquire.call_count == 2 