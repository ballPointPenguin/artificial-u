# Manual Tests for ArtificialU

This directory contains manual tests that require API keys, external services, or other manual intervention.

## ElevenLabs Integration Test

The ElevenLabs integration test script validates the connection and functionality of the ElevenLabs text-to-speech API.

### Prerequisites

- ElevenLabs API key (sign up at <https://elevenlabs.io/>)
- Python 3.9+
- All project dependencies installed

### Running the Tests

You can run the tests with:

```bash
# Using environment variable
ELEVENLABS_API_KEY=your_api_key python tests/manual/test_elevenlabs_integration.py

# Using command-line argument
python tests/manual/test_elevenlabs_integration.py --api-key your_api_key
```

### Test Options

- `--api-key`, `-k`: ElevenLabs API key
- `--skip-audio`, `-s`: Skip the audio generation test (useful for quick validation without using too many API credits)

### What the Tests Cover

1. **API Connection Test**: Verifies basic connection to the ElevenLabs API and retrieves available voices.
2. **Voice Creation and Mapping Test**: Verifies the creation and mapping of voices for different professor personas.
3. **Text Processing Test**: Tests the processing of stage directions in lecture text.
4. **Speech Generation Test**: Verifies the generation of speech from a sample lecture.

### Example Output

A successful test run will output something like:

```txt
=== Starting ElevenLabs Integration Tests ===
? Successfully connected to ElevenLabs API. Found 18 voices.
? Subscription tier: pro
? Character limit: 1000000
? Characters used: 123456
? Characters available: 876544

=== Testing Professor Voice Creation and Mapping ===

Creating voice for Dr. Alan Turing in Computer Science...
? Created voice 21m00Tcm4TlvDq8ikWAM for Dr. Alan Turing
? Voice settings correctly stored: {'voice_id': '21m00Tcm4TlvDq8ikWAM', 'stability': 0.5, 'similarity_boost': 0.75, 'style': 0.5, 'use_speaker_boost': True}
? Retrieved voice: 21m00Tcm4TlvDq8ikWAM

...

=== Test Summary ===
API Connection: ?
Voice Creation: ?
Text Processing: ?
Speech Generation: ?

? All tests passed!
```

## Adding More Manual Tests

When adding new manual tests to this directory, please:

1. Document the test purpose and requirements
2. Include clear instructions for running the test
3. Handle API keys securely (never commit them to version control)
4. Provide clear feedback on whether tests passed or failed
