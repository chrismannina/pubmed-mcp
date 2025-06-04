# PubMed MCP Server Test Suite

This directory contains comprehensive unit tests for the PubMed MCP Server.

## Test Structure

```
tests/
├── __init__.py           # Test package marker
├── conftest.py          # Pytest fixtures and configuration
├── test_utils.py        # Tests for utility functions and rate limiting
├── test_models.py       # Tests for data models (Pydantic models)
├── test_pubmed_client.py # Tests for PubMed API client
├── test_tool_handler.py # Tests for MCP tool handling
└── README.md           # This file
```

## Running Tests

### Prerequisites

Install the test dependencies:

```bash
pip install -r requirements.txt
```

This will install pytest and related testing packages.

### Basic Test Execution

Run all tests:
```bash
python run_tests.py
```

Or use pytest directly:
```bash
pytest tests/
```

### Advanced Test Options

Run specific test files:
```bash
python run_tests.py test_utils.py
python run_tests.py test_pubmed_client.py
```

Run with coverage reporting:
```bash
python run_tests.py --coverage
```

Run only fast tests (skip slow integration tests):
```bash
python run_tests.py --markers "not slow"
```

Run in verbose mode:
```bash
pytest tests/ -v
```

Run specific test methods:
```bash
pytest tests/test_utils.py::TestRateLimiter::test_rate_limiter_initialization
```

### Test Categories

Tests are organized into several categories:

1. **Unit Tests** (`test_*.py`): Test individual components in isolation
2. **Integration Tests**: Test component interactions (marked with `@pytest.mark.integration`)
3. **Slow Tests**: Tests that take longer to run (marked with `@pytest.mark.slow`)

## Test Coverage

The test suite aims to cover:

- ✅ **Rate Limiting**: Ensures the rate limiting decorator works correctly
- ✅ **Caching**: Tests cache functionality and TTL behavior
- ✅ **PubMed API Client**: Tests API interactions with mocked responses
- ✅ **Data Models**: Tests Pydantic model validation and serialization
- ✅ **Tool Handling**: Tests MCP tool request handling
- ✅ **Error Handling**: Tests exception handling and error responses
- ✅ **Edge Cases**: Tests with invalid inputs, empty results, etc.

## Key Test Fixes

This test suite addresses several issues found in the original code:

### 1. Rate Limiting Decorator Issue

**Problem**: The `@rate_limited` decorator was being used incorrectly, causing the error:
```
rate_limited.<locals>.decorator() takes 1 positional argument but 3 were given
```

**Solution**: The tests verify that rate limiting is now applied correctly using direct calls to `await self.rate_limiter.acquire()` instead of the problematic decorator usage.

### 2. Comprehensive Mocking

The test suite uses comprehensive mocking to:
- Avoid actual API calls during testing
- Test error scenarios safely
- Ensure predictable test results

### 3. Async Testing

All async functions are properly tested using `pytest-asyncio` with the `@pytest.mark.asyncio` decorator.

## Test Fixtures

Key fixtures provided in `conftest.py`:

- `mock_config`: Test configuration
- `mock_rate_limiter`: Mocked rate limiter
- `mock_cache_manager`: Mocked cache
- `mock_pubmed_client`: Mocked PubMed client
- `sample_article`: Sample article data
- `sample_search_result`: Sample search results
- `mock_httpx_response`: Mocked HTTP responses

## Writing New Tests

When adding new tests:

1. **Use appropriate fixtures**: Leverage existing fixtures for consistency
2. **Mock external dependencies**: Don't make real API calls
3. **Test both success and error cases**: Include negative test scenarios
4. **Use descriptive test names**: Test names should explain what they test
5. **Add markers for slow tests**: Use `@pytest.mark.slow` for time-consuming tests

Example test structure:
```python
@pytest.mark.asyncio
async def test_new_feature(mock_client, sample_data):
    """Test description of what this test verifies."""
    # Arrange
    mock_client.some_method.return_value = sample_data

    # Act
    result = await function_under_test()

    # Assert
    assert result.success is True
    mock_client.some_method.assert_called_once()
```

## Continuous Integration

These tests are designed to run in CI/CD environments. The `run_tests.py` script provides:

- Exit codes for CI systems
- Parallel test execution (with `--parallel`)
- Coverage reporting
- Dependency installation

## Debugging Tests

For debugging failing tests:

1. **Run with verbose output**: `pytest -v -s`
2. **Run specific failing test**: `pytest tests/test_file.py::test_function`
3. **Use pytest debugger**: `pytest --pdb`
4. **Check logs**: Tests include logging output for debugging

## Performance Testing

Some tests include performance checks:
- Rate limiting timing tests
- Cache performance tests
- API response time validation

Run only performance tests:
```bash
pytest tests/ -m "performance"
```

## Common Issues

### Import Errors
If you see import errors, ensure you're running tests from the project root:
```bash
cd pubmed-mcp
python run_tests.py
```

### Async Event Loop Issues
If you encounter event loop issues, ensure `pytest-asyncio` is installed and `asyncio_mode = auto` is set in `pytest.ini`.

### Mock Object Issues
If mocks aren't working as expected, check that you're using the correct mock specifications and return values in the test fixtures.
