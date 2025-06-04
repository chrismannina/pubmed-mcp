# PubMed MCP Server

[![CI](https://github.com/chrismannina/pubmed-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/chrismannina/pubmed-mcp/actions/workflows/ci.yml)

A comprehensive Model Context Protocol (MCP) server for PubMed literature search and management. This server provides advanced search capabilities, citation formatting, and research analysis tools through the MCP protocol.

## Features

- **Advanced PubMed Search**: Search with complex filters including date ranges, article types, authors, journals, and MeSH terms
- **Article Details**: Retrieve detailed information for specific PMIDs including abstracts, authors, and metadata
- **Citation Export**: Export citations in multiple formats (BibTeX, APA, MLA, Chicago, Vancouver, EndNote, RIS)
- **Author Search**: Find articles by specific authors with co-author information
- **Related Articles**: Discover articles related to a specific PMID
- **MeSH Term Search**: Search and explore Medical Subject Headings
- **Journal Analysis**: Get metrics and recent articles from specific journals
- **Research Trends**: Analyze publication trends over time
- **Article Comparison**: Compare multiple articles side by side
- **Caching**: Built-in caching for improved performance
- **Rate Limiting**: Respectful API usage with configurable rate limits

## Installation

### Prerequisites

- Python 3.8 or higher
- NCBI API key (free registration required)
- Valid email address for NCBI API identification

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/pubmed-mcp.git
   cd pubmed-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your NCBI API key and email
   ```

4. **Run the server:**
   ```bash
   python -m src.main
   ```

### Development Installation

For development with additional tools:

```bash
make install-dev
```

Or manually:

```bash
pip install -r requirements.txt
pip install -e .
pip install black isort mypy flake8
```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Required
PUBMED_API_KEY=your_ncbi_api_key_here
PUBMED_EMAIL=your.email@example.com

# Optional
CACHE_TTL=300
CACHE_MAX_SIZE=1000
RATE_LIMIT=3.0
LOG_LEVEL=info
```

### Getting an NCBI API Key

1. Visit [NCBI Account Settings](https://www.ncbi.nlm.nih.gov/account/settings/)
2. Sign in or create an account
3. Navigate to "API Key Management"
4. Create a new API key
5. Copy the key to your `.env` file

## Usage

### Available Tools

The server provides the following MCP tools:

#### 1. `search_pubmed`
Search PubMed with advanced filtering options.

```json
{
  "query": "machine learning healthcare",
  "max_results": 20,
  "date_range": "5y",
  "article_types": ["Journal Article", "Review"],
  "has_abstract": true
}
```

#### 2. `get_article_details`
Get detailed information for specific PMIDs.

```json
{
  "pmids": ["12345678", "87654321"],
  "include_abstracts": true,
  "include_citations": false
}
```

#### 3. `search_by_author`
Search for articles by a specific author.

```json
{
  "author_name": "Smith J",
  "max_results": 10,
  "include_coauthors": true
}
```

#### 4. `export_citations`
Export citations in various formats.

```json
{
  "pmids": ["12345678"],
  "format": "bibtex",
  "include_abstracts": false
}
```

#### 5. `find_related_articles`
Find articles related to a specific PMID.

```json
{
  "pmid": "12345678",
  "max_results": 10
}
```

#### 6. `search_mesh_terms`
Search using MeSH terms.

```json
{
  "term": "Machine Learning",
  "max_results": 20
}
```

#### 7. `analyze_research_trends`
Analyze publication trends over time.

```json
{
  "topic": "artificial intelligence",
  "years_back": 5,
  "include_subtopics": false
}
```

### Example Usage with MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.main"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Search PubMed
            result = await session.call_tool(
                "search_pubmed",
                {
                    "query": "COVID-19 vaccines",
                    "max_results": 5,
                    "date_range": "1y"
                }
            )
            
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test types
python run_tests.py unit
python run_tests.py integration
python run_tests.py coverage
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
mypy src/
```

### Project Structure

```
pubmed-mcp/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── server.py            # MCP server implementation
│   ├── models.py            # Pydantic models
│   ├── pubmed_client.py     # PubMed API client
│   ├── tool_handler.py      # Tool request handlers
│   ├── citation_formatter.py # Citation formatting
│   ├── tools.py             # Tool definitions
│   └── utils.py             # Utility functions
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
├── setup.py                 # Package setup
├── pyproject.toml          # Modern Python config
├── Makefile                # Development commands
├── Dockerfile              # Container setup
└── README.md               # This file
```

## Docker

### Build and Run

```bash
# Build Docker image
make docker-build

# Run with environment variables
make docker-run PUBMED_API_KEY=your_key PUBMED_EMAIL=your_email
```

### Docker Compose

```yaml
version: '3.8'
services:
  pubmed-mcp:
    build: .
    environment:
      - PUBMED_API_KEY=your_key
      - PUBMED_EMAIL=your_email
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data
```

## API Reference

### Search Parameters

- `query`: Search query using PubMed syntax
- `max_results`: Maximum number of results (1-200)
- `sort_order`: Sort order (relevance, pub_date, author, journal, title)
- `date_from`/`date_to`: Date range filters
- `date_range`: Predefined ranges (1y, 5y, 10y, all)
- `article_types`: Filter by publication types
- `authors`: Filter by author names
- `journals`: Filter by journal names
- `mesh_terms`: Filter by MeSH terms
- `language`: Language filter (e.g., 'eng', 'fre')
- `has_abstract`: Only articles with abstracts
- `has_full_text`: Only articles with full text
- `humans_only`: Only human studies

### Citation Formats

- `bibtex`: BibTeX format
- `apa`: APA style
- `mla`: MLA style
- `chicago`: Chicago style
- `vancouver`: Vancouver style
- `endnote`: EndNote format
- `ris`: RIS format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests
- Update documentation for new features
- Use conventional commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/pubmed-mcp/issues)
- **Documentation**: [Project Wiki](https://github.com/your-org/pubmed-mcp/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/pubmed-mcp/discussions)

## Acknowledgments

- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/) for PubMed API access
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [Anthropic](https://www.anthropic.com/) for MCP development and support

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

---

**Note**: This server requires a valid NCBI API key and follows NCBI's usage guidelines. Please be respectful of API rate limits and terms of service. 