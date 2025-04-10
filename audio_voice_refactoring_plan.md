# Audio and Voice Components Refactoring Plan

## Current Issues

- `audio/processor.py` and `integrations/elevenlabs.py` have overlapping responsibilities
- Voice selection logic is spread across multiple files
- The audio processing concerns aren't clearly separated
- There's duplication in API calls and voice handling logic
- The current organization doesn't match the new service-based architecture

## Proposed Structure

```
artificial_u/
  services/
    audio_service.py          # Already created - high-level coordinator (remains mostly unchanged)
    voice_service.py          # NEW - Voice selection and management
    tts_service.py            # NEW - Text-to-speech conversion
  
  audio/                      # Renamed from current audio/
    speech_processor.py       # Text enhancement for better speech
    audio_utils.py            # Audio format handling and utilities
  
  integrations/
    elevenlabs/               # Restructured as a package
      __init__.py             # Package exports
      client.py               # Low-level ElevenLabs API client
      voice_mapper.py         # Match professor attributes to voices
      cache.py                # Voice data caching
```

## Component Responsibilities

### Services Layer

#### `voice_service.py`

- Professor-to-voice matching coordination
- Voice assignment and storage
- Voice metadata management
- Voice cache management

#### `tts_service.py`

- Text-to-speech conversion
- Audio chunk processing
- Audio file handling
- Text preprocessing for speech

### Audio Layer

#### `speech_processor.py`

- Text enhancement for better pronunciation
- Speech markup handling
- Technical term pronunciation
- Math notation handling

#### `audio_utils.py`

- Audio format utilities
- Audio playback utilities
- File path management

### Integrations Layer

#### `elevenlabs/client.py`

- Raw ElevenLabs API calls
- API authentication
- Response parsing

#### `elevenlabs/voice_mapper.py`

- Algorithms for matching professor attributes to voices
- Gender/accent/age extraction from professor profiles

#### `elevenlabs/cache.py`

- Voice data caching mechanisms
- Cache file handling

## Implementation Steps

1. Create directory structure
2. Extract `VoiceSelectionManager` into voice service and ElevenLabs components
3. Separate text-to-speech functionality from voice selection
4. Move speech enhancement to dedicated speech processor
5. Create minimal ElevenLabs client
6. Update `audio_service.py` to use the new components
7. Add appropriate tests
8. Update imports in other files

## Benefits

- Clear separation of concerns
- Better testability for each component
- Reduced duplication
- More maintainable code
- Better alignment with the service-based architecture
- Easier to extend or replace components (e.g., switch TTS providers)
