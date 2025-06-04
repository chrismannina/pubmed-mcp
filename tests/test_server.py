#!/usr/bin/env python3
"""
Simple test script for the PubMed MCP Server
"""
import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.main import load_config
from src.server import PubMedMCPServer


async def test_server():
    """Test basic server functionality"""
    print("🧪 Testing PubMed MCP Server...")

    try:
        # Load configuration
        config = load_config()
        print(f"✅ Configuration loaded")
        print(f"   - API Key: {config['pubmed_api_key'][:10]}...")
        print(f"   - Email: {config['pubmed_email']}")

        # Initialize server with individual parameters (fixed)
        server = PubMedMCPServer(
            pubmed_api_key=config["pubmed_api_key"],
            pubmed_email=config["pubmed_email"],
            cache_ttl=config["cache_ttl"],
            cache_max_size=config["cache_max_size"],
            rate_limit=config["rate_limit"],
        )
        print("✅ Server initialized")

        # Get tools from tool handler directly
        tools_data = server.tool_handler.get_tools()
        print(f"✅ Found {len(tools_data)} tools:")

        for i, tool in enumerate(tools_data, 1):
            print(f"   {i:2d}. {tool['name']:25} - {tool['description']}")

        print(f"\n✅ Cache initialized: {server.get_cache_stats()}")
        print(
            f"✅ PubMed client ready with rate limit: {server.pubmed_client.rate_limiter.rate} req/sec"
        )

        print("\n🎉 Server test completed successfully!")
        print("\nYour PubMed MCP server is ready! Next steps:")
        print("1. Run: PYTHONPATH=. mcp-inspector python src/main.py")
        print("2. Open http://127.0.0.1:6274 in your browser")
        print("3. Test tools with real PubMed searches!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_server())
    sys.exit(0 if success else 1)
