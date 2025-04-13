# Unit Tests for ArtificialU

This directory contains unit tests that can be run without external API calls or database connections. These tests focus on individual components in isolation, using mocks to substitute dependencies.

## Running Unit Tests

To run only unit tests:

```bash
cd /path/to/artificial-u
python -m pytest -m unit
```

This will run only tests marked with `@pytest.mark.unit`.

## Testing Philosophy

1. **Isolation**: Tests are isolated from external systems like databases and APIs.
2. **Mocking**: Dependencies are mocked rather than modified with test-specific code.
3. **Test Credentials**: Environment variables are set to standard test values (via `.env.test`) during test runs.

## Environment Variables

Unit tests use dummy API keys from `.env.test`:

- `ELEVENLABS_API_KEY=test_elevenlabs_key`
- `ANTHROPIC_API_KEY=test_anthropic_key`
- `OPENAI_API_KEY=test_openai_key`

## Test Organization

- **Unit Tests**: Located in `tests/unit/`, these don't need real API keys or database connections
- **Integration Tests**: Located in parent directories, these test interactions between components

## Test Collection Optimization

When running with the `-m unit` flag, the test collector will:

1. Avoid loading database connections when running unit tests
2. Provide dummy implementations of certain classes to prevent import errors

This approach keeps the testing concerns out of the production code while still allowing seamless test execution.

## Adding New Unit Tests

When adding new unit tests:

1. Place the test in the `tests/unit/` directory
2. Add the `@pytest.mark.unit` decorator to test classes/functions
3. Mock external dependencies rather than modifying production code
4. Verify the test works without any real API keys or database connections
