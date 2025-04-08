# Manual Tests for ArtificialU

This directory contains manual tests that require API keys, external services, or other manual intervention.

## ElevenLabs Integration Test

The ElevenLabs integration test script validates the connection and functionality of the ElevenLabs text-to-speech API.

### Prerequisites

- ElevenLabs API key (sign up at <https://elevenlabs.io/>)
- Python 3.9+
- All project dependencies installed

### Important: API Key Usage

**These tests use your real API keys from `.env`**, not the test keys from `.env.test`. This allows testing the actual API integration, but be aware that:

1. These tests will use your API quota
2. They will skip if no valid API key is found
3. They're excluded from normal test runs for this reason

### Running the Tests

You can run the tests with:

```bash
# Using pytest with manual marker - WILL USE REAL API KEYS
pytest -m manual

# Using pytest directly - WILL USE REAL API KEYS
pytest tests/manual/test_elevenlabs_integration.py
```

### Test Options

- `--play`: Play the generated audio (optional)

### What the Tests Cover

1. **API Connection Test**: Verifies basic connection to the ElevenLabs API and retrieves available voices.
2. **Voice Mapping Test**: Verifies mapping of professors to appropriate voice types.
3. **Text Processing Test**: Tests the processing of stage directions in lecture text.
4. **Speech Generation Test**: Verifies the generation of speech from a sample lecture.

### Example Output

A successful test run will output something like:

```txt
=== Starting ElevenLabs Integration Tests ===
Using REAL environment variables for manual tests
✓ Successfully connected to ElevenLabs API. Found 18 voices.
✓ Subscription tier: pro
✓ Character limit: 1000000
✓ Characters used: 123456
✓ Characters available: 876544

=== Testing Text Processing ===
...

=== All tests passed! ===
```

## Adding More Manual Tests

When adding new manual tests to this directory, please:

1. Document the test purpose and requirements
2. Include clear instructions for running the test
3. Handle API keys securely (never commit them to version control)
4. Provide clear feedback on whether tests passed or failed
