# Integration Tests

This directory contains integration tests that require real environment variables and may make actual API calls to PubMed.

## Setup

Before running integration tests, you need to:

1. **Create a `.env` file** in the project root with:
   ```bash
   PUBMED_API_KEY=your_ncbi_api_key_here
   PUBMED_EMAIL=your_email@example.com
   ```

2. **Get a PubMed API key** (optional but recommended):
   - Visit: https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
   - Sign up for an NCBI account and generate an API key

## Running Integration Tests

```bash
# Run all integration tests
python -m pytest integration_tests/ -v

# Run specific integration test
python -m pytest integration_tests/test_server_integration.py -v

# Run with coverage
python -m coverage run -m pytest integration_tests/ -v
python -m coverage report
```

## Test Files

- `test_server_integration.py` - Tests the complete server startup and functionality with real configuration

## Notes

- Integration tests are **not run in CI/CD** to avoid requiring API keys in the pipeline
- These tests may make real API calls to PubMed (rate limited)
- Run these locally to verify everything works end-to-end
- Some tests may be slower due to network calls

## Environment Variables

The integration tests expect these environment variables:

- `PUBMED_API_KEY` - Your NCBI API key (optional)
- `PUBMED_EMAIL` - Your email address (required by NCBI)
- `CACHE_TTL` - Cache timeout in seconds (optional, default: 300)
- `CACHE_MAX_SIZE` - Maximum cache size (optional, default: 1000)
- `RATE_LIMIT` - Rate limit in requests per second (optional, default: 3.0)
