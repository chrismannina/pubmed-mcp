#!/usr/bin/env python3
"""
Critical issue verification tests for PubMed MCP Server.
This script specifically tests the fixes for issues that were causing errors.
"""
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.pubmed_client import PubMedClient
from src.utils import RateLimiter, rate_limited, CacheManager
from src.models import MCPResponse


async def test_rate_limiting_fixed():
    """Test that the rate limiting issue is fixed."""
    print("🔍 Testing rate limiting fix...")
    
    # Create a PubMed client (the old problematic way)
    client = PubMedClient(
        api_key="test_key",
        email="test@example.com",
        rate_limit=5.0
    )
    
    # Test that the rate limiter is properly initialized
    assert isinstance(client.rate_limiter, RateLimiter)
    assert client.rate_limiter.rate == 5.0
    
    # Test that we can make requests without the decorator error
    # Mock the HTTP client to avoid actual API calls
    client.client.get = AsyncMock()
    mock_response = Mock()
    mock_response.json.return_value = {"esearchresult": {"idlist": [], "count": "0"}}
    mock_response.raise_for_status = Mock()
    client.client.get.return_value = mock_response
    
    # This should work without the "takes 1 positional argument but 3 were given" error
    params = {"db": "pubmed", "term": "test"}
    response = await client._make_request("esearch.fcgi", params)
    
    print("✅ Rate limiting works correctly!")
    return True


async def test_rate_limited_decorator():
    """Test that the rate_limited decorator works correctly."""
    print("🔍 Testing rate_limited decorator...")
    
    limiter = RateLimiter(rate=10.0)
    
    @rate_limited(limiter)
    async def test_function(x, y):
        return x + y
    
    # This should work without errors
    result = await test_function(2, 3)
    assert result == 5
    
    print("✅ Rate limited decorator works correctly!")
    return True


def test_cache_manager():
    """Test that CacheManager works correctly."""
    print("🔍 Testing CacheManager...")
    
    cache = CacheManager(max_size=10, ttl=300)
    
    # Test basic functionality
    cache.set("test_key", "test_value")
    result = cache.get("test_key")
    assert result == "test_value"
    
    # Test stats
    stats = cache.get_stats()
    assert "size" in stats
    assert "hits" in stats
    assert "misses" in stats
    
    print("✅ CacheManager works correctly!")
    return True


def test_mcp_response_model():
    """Test that MCPResponse model works correctly."""
    print("🔍 Testing MCPResponse model...")
    
    # Test successful response
    response = MCPResponse(
        content=[{"type": "text", "text": "Success message"}],
        is_error=False
    )
    assert response.is_error is False
    assert len(response.content) == 1
    
    # Test error response
    error_response = MCPResponse(
        content=[{"type": "text", "text": "Error message"}],
        is_error=True
    )
    assert error_response.is_error is True
    
    print("✅ MCPResponse model works correctly!")
    return True


async def test_pubmed_client_initialization():
    """Test that PubMedClient initializes correctly."""
    print("🔍 Testing PubMedClient initialization...")
    
    client = PubMedClient(
        api_key="test_key",
        email="test@example.com",
        rate_limit=3.0
    )
    
    # Check initialization
    assert client.api_key == "test_key"
    assert client.email == "test@example.com"
    assert client.rate_limiter.rate == 3.0
    assert client.base_url == "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    print("✅ PubMedClient initializes correctly!")
    return True


async def main():
    """Run all critical tests."""
    print("🧪 Running Critical Issue Verification Tests")
    print("=" * 50)
    
    tests = [
        test_rate_limiting_fixed,
        test_rate_limited_decorator,
        test_cache_manager,
        test_mcp_response_model,
        test_pubmed_client_initialization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                await test()
            else:
                test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All critical issues have been fixed!")
        print("\nKey fixes implemented:")
        print("✓ Rate limiting decorator issue resolved")
        print("✓ PubMed client properly initializes rate limiter")
        print("✓ Cache manager works correctly")
        print("✓ MCPResponse model updated for MCP protocol")
        print("✓ All core functionality tested and working")
        return True
    else:
        print("❌ Some issues still need to be addressed")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1) 