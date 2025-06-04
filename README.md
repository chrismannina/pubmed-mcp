# PubMed MCP Server

A comprehensive **Model Context Protocol (MCP) server** for PubMed literature search and management. This server provides advanced search capabilities, citation formatting, research analysis tools, and seamless integration with Claude Desktop and other MCP clients.

## 🚀 Features

### Advanced Search Capabilities
- **Complex Query Building**: Support for boolean operators, field-specific searches, and filters
- **Advanced Filtering**: Filter by publication date, article types, authors, journals, languages, and more
- **MeSH Terms Integration**: Search and filter using Medical Subject Headings
- **Author & Journal Search**: Dedicated search functions for specific authors and journals
- **Related Articles**: Find articles related to any PMID using PubMed's algorithm

### Citation Management
- **Multiple Formats**: Export citations in BibTeX, APA, MLA, Chicago, Vancouver, EndNote, and RIS formats
- **Bulk Export**: Export multiple articles at once with consistent formatting
- **Custom Fields**: Include or exclude abstracts, DOIs, and other metadata

### Research Analysis Tools
- **Trending Topics**: Analyze current research trends and emerging topics
- **Publication Trends**: Track publication patterns over time for any research topic
- **Article Comparison**: Side-by-side comparison of multiple research papers
- **Journal Metrics**: Get insights into journal publication patterns and article types

### Performance & Reliability
- **Intelligent Caching**: Reduce API calls with configurable TTL cache
- **Rate Limiting**: Respect PubMed API limits with built-in rate limiting
- **Error Handling**: Comprehensive error handling and logging
- **Async Architecture**: Built with modern Python async/await patterns

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- NCBI API key (free from [NCBI](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/))

### Install Dependencies

```bash
cd pubmed-mcp
pip install -r requirements.txt
```

Or install in development mode:

```bash
cd pubmed-mcp
pip install -e .
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `pubmed-mcp` directory:

```env
# Required Configuration
PUBMED_API_KEY=your_ncbi_api_key_here
PUBMED_EMAIL=your_email@example.com

# Optional Configuration
CACHE_TTL=300
CACHE_MAX_SIZE=1000
RATE_LIMIT=3
LOG_LEVEL=info
```

### Getting an NCBI API Key

1. Visit the [NCBI API Key page](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/)
2. Sign in to your NCBI account or create one
3. Go to your [account settings](https://www.ncbi.nlm.nih.gov/account/settings/)
4. Generate an API key
5. Copy the key to your `.env` file

## 🖥️ Usage

### Running the Server

```bash
cd pubmed-mcp
python -m src.main
```

Or if installed via setuptools:

```bash
pubmed-mcp
```

### Using with Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pubmed-mcp": {
      "command": "python",
      "args": [
        "/path/to/pubmed-mcp/src/main.py"
      ],
      "env": {
        "PUBMED_API_KEY": "your_api_key_here",
        "PUBMED_EMAIL": "your_email@example.com"
      }
    }
  }
}
```

## 🛠️ Available Tools

### Search Tools

#### `search_pubmed`
Advanced PubMed search with comprehensive filtering options.

**Parameters:**
- `query` (required): Search query using PubMed syntax
- `max_results`: Maximum number of results (1-200, default: 20)
- `sort_order`: Sort by relevance, publication date, author, journal, or title
- `date_from/date_to`: Date range filters (YYYY/MM/DD format)
- `date_range`: Predefined ranges (1y, 5y, 10y, all)
- `article_types`: Filter by publication types (Review, Clinical Trial, etc.)
- `authors`: Filter by specific authors
- `journals`: Filter by journal names
- `mesh_terms`: Filter by MeSH terms
- `language`: Language filter (eng, fre, ger, etc.)
- `has_abstract`: Only articles with abstracts
- `has_full_text`: Only articles with full text
- `humans_only`: Only human studies

**Example:**
```json
{
  "query": "machine learning healthcare",
  "max_results": 50,
  "date_range": "5y",
  "article_types": ["Review", "Systematic Review"],
  "has_abstract": true,
  "humans_only": true
}
```

#### `search_by_author`
Search for publications by a specific author.

**Parameters:**
- `author_name` (required): Author name to search
- `max_results`: Maximum results (default: 20)
- `include_coauthors`: Include co-author information

#### `search_by_journal`
Find recent articles from a specific journal.

**Parameters:**
- `journal_name` (required): Journal name or abbreviation
- `max_results`: Maximum results (default: 20)
- `date_from/date_to`: Date range filters

#### `search_mesh_terms`
Search articles by MeSH (Medical Subject Headings) terms.

**Parameters:**
- `term` (required): MeSH term to search
- `max_results`: Maximum results (default: 20)

#### `advanced_search`
Perform complex searches with multiple criteria and boolean operators.

**Parameters:**
- `search_terms` (required): Array of search criteria with fields and operators
- `filters`: Additional filters (publication types, languages, species, etc.)
- `max_results`: Maximum results (default: 50)

### Article Management Tools

#### `get_article_details`
Get comprehensive information for specific articles.

**Parameters:**
- `pmids` (required): Array of PubMed IDs
- `include_abstracts`: Include abstracts (default: true)
- `include_citations`: Include citation metrics (default: false)

#### `find_related_articles`
Find articles related to a specific PMID using PubMed's algorithm.

**Parameters:**
- `pmid` (required): Reference article PMID
- `max_results`: Maximum related articles (default: 10)

#### `compare_articles`
Compare multiple articles side by side.

**Parameters:**
- `pmids` (required): Array of 2-5 PMIDs to compare
- `comparison_fields`: Fields to compare (authors, methods, conclusions, mesh_terms, citations)

### Citation Tools

#### `export_citations`
Export article citations in various academic formats.

**Parameters:**
- `pmids` (required): Array of PMIDs to export
- `format`: Citation format (bibtex, apa, mla, chicago, vancouver, endnote, ris)
- `include_abstracts`: Include abstracts in citations (default: false)

**Supported Formats:**
- **BibTeX**: Standard LaTeX bibliography format
- **APA**: American Psychological Association style
- **MLA**: Modern Language Association style
- **Chicago**: Chicago Manual of Style
- **Vancouver**: Medical/scientific citation style
- **EndNote**: EndNote reference manager format
- **RIS**: Research Information Systems format

### Analysis Tools

#### `get_trending_topics`
Analyze trending topics and emerging research areas.

**Parameters:**
- `category`: Medical category filter (cardiology, oncology, etc.)
- `days`: Analysis period in days (default: 7)

#### `analyze_research_trends`
Track publication trends for research topics over time.

**Parameters:**
- `topic` (required): Research topic to analyze
- `years_back`: Years to analyze (default: 5)
- `include_subtopics`: Include related subtopic analysis

#### `get_journal_metrics`
Get metrics and publication patterns for journals.

**Parameters:**
- `journal_name` (required): Journal name
- `include_recent_articles`: Include recent notable articles

## 🎯 Example Use Cases

### Academic Research
```
"Search for systematic reviews on artificial intelligence in radiology published in the last 2 years, then export the top 10 results in APA format."
```

### Literature Review
```
"Find articles related to PMID 12345678, compare them with the original article, and analyze publication trends for 'deep learning medical imaging' over the last 5 years."
```

### Journal Analysis
```
"Get metrics for 'Nature Medicine' journal and show me trending topics in oncology research from the past month."
```

### Citation Management
```
"Search for articles by 'Smith J' on 'cancer immunotherapy', then export all results in BibTeX format with abstracts included."
```

## 📊 Performance Features

### Caching
- **Intelligent Caching**: Automatic caching of API responses
- **Configurable TTL**: Set cache expiration times
- **Cache Statistics**: Monitor hit rates and performance
- **Memory Management**: Automatic cache size management

### Rate Limiting
- **API Compliance**: Respects NCBI rate limits
- **Token Bucket**: Smooth request distribution
- **Configurable Rates**: Adjust for your API key tier

### Error Handling
- **Graceful Degradation**: Continue operation on partial failures
- **Detailed Logging**: Comprehensive error tracking
- **Input Validation**: Validate PMIDs and parameters
- **Network Resilience**: Retry logic for transient failures

## 🔧 Development

### Project Structure

```
pubmed-mcp/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── server.py              # Main MCP server
│   ├── types.py               # Pydantic models
│   ├── tools.py               # Tool definitions
│   ├── utils.py               # Utilities and helpers
│   ├── pubmed_client.py       # PubMed API client
│   ├── citation_formatter.py  # Citation formatting
│   └── tool_handler.py        # Tool request router
├── requirements.txt
├── setup.py
├── env.example
└── README.md
```

### Testing

Test the server using the MCP Inspector:

```bash
npm install -g @modelcontextprotocol/inspector
mcp-inspector python -m src.main
```

Then open http://localhost:5173 in your browser.

### Custom Development

The server is built with extensibility in mind:

1. **Add New Tools**: Extend `tool_handler.py` with new tool methods
2. **Custom Formatters**: Add new citation formats in `citation_formatter.py`
3. **Enhanced Analysis**: Add new research analysis features
4. **Additional APIs**: Integrate other biomedical databases

## 🐛 Troubleshooting

### Common Issues

**"Missing API Key" Error:**
- Ensure `PUBMED_API_KEY` is set in your `.env` file
- Verify the API key is valid and active

**Rate Limit Errors:**
- Check your API key tier limits
- Adjust `RATE_LIMIT` in configuration
- Consider getting a higher-tier API key

**Connection Issues:**
- Verify internet connectivity
- Check NCBI service status
- Ensure firewall allows HTTPS connections

**Memory Issues:**
- Reduce `CACHE_MAX_SIZE` if using limited memory
- Lower `max_results` in searches
- Monitor cache statistics

### Debug Mode

Run with debug logging:

```bash
LOG_LEVEL=debug python -m src.main
```

### Cache Management

Clear cache and view statistics:

```python
# The server provides cache statistics in logs
# Cache automatically expires based on TTL
# Restart server to clear all cache
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Check this README and code comments
- **PubMed API**: See [NCBI E-utilities documentation](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- **MCP Protocol**: See [Model Context Protocol documentation](https://modelcontextprotocol.io)

## 🙏 Acknowledgments

- **NCBI/PubMed**: For providing comprehensive biomedical literature data
- **Model Context Protocol**: For the standardized integration framework
- **Claude**: For MCP client support and integration
- **Open Source Community**: For the excellent Python libraries used

---

**Happy Researching! 🔬📚** 