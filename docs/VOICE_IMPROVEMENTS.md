# Voice System Improvements

## Overview

This document details the improvements made to the ElevenLabs voice integration based on the analysis in VOICE_NOTES.md.

## Key Improvements

### 1. Added Support for v2/voices Endpoint

- Created `get_premade_voices()` method in `ElevenLabsClient` to fetch from the v2/voices endpoint
- This endpoint provides access to official ElevenLabs "premade" voices with higher quality
- Handles the different JSON structure where attributes are nested in the "labels" object

### 2. Enhanced Quality Scoring

Updated the quality scoring system to prioritize voices:

- **Premade voices**: +0.4 points (highest priority)
- **High quality voices**: +0.3 points
- **Professional voices**: +0.25 points

This ensures official ElevenLabs voices are preferred over community voices when available.

### 3. Replaced SUPPORTED_ACCENTS with Language-Based System

- Removed the obsolete `SUPPORTED_ACCENTS` list
- Added `ACCENT_TO_LANGUAGE_MAP` for converting accent names to two-letter language codes
- Created `accent_to_language_code()` method for conversion
- The system now uses language codes (e.g., "en", "fr", "de") for API queries instead of accent strings

### 4. Filtering of Paid Voices

Added filtering to exclude voices that require additional payment:

- Voices with `rate` != null and rate != 1.0 are filtered out
- Voices with `fiat_rate` != null are filtered out
- This filtering is applied in both `get_shared_voices()` and `get_premade_voices()` methods

### 5. Voice Usage Tracking

Implemented a system to prevent voice reuse across multiple professors:

- Added `_get_used_voice_ids()` method to track which voices are already assigned
- Modified `rank_voices()` to accept a list of used voice IDs
- Applied a -0.3 penalty to the match score for voices already in use
- This encourages diversity in voice selection across professors

### 6. Improved API Usage

- The system now fetches premade voices in addition to shared voices
- Removed accent parameter from shared voices API calls (it's not effective)
- Uses language parameter instead for better filtering

## Usage

### Initialize Premade Voices

Run the initialization script to populate the database with premade voices:

```bash
python scripts/initialize_voices.py
```

### Voice Selection Process

The improved voice selection process:

1. Extracts professor attributes (gender, accent, age)
2. Converts accent to language code
3. Searches database for matching voices
4. If none found, fetches from APIs (both premade and shared)
5. Gets list of already-used voices
6. Ranks voices based on:
   - Quality score (premade > high_quality > professional)
   - Attribute matching (gender, age, language)
   - Penalty for already-used voices
7. Selects voice using configured strategy (top, top_random, or weighted)

### API Filtering

The system automatically filters out:

- Voices that require additional payment (rate/fiat_rate)
- Voices with live moderation enabled (when possible)

## Configuration

No additional configuration is required. The system will automatically:

- Fetch premade voices when needed
- Apply the new scoring and filtering rules
- Track voice usage across professors

## Benefits

1. **Higher Quality**: Premade voices are professional-grade and preferred
2. **Better Matching**: Language-based filtering is more reliable than accent strings
3. **Cost Control**: Automatic filtering of paid voices prevents unexpected charges
4. **Voice Diversity**: Usage tracking ensures variety across professors
5. **Improved Performance**: Better caching and smarter API usage

## Future Considerations

1. Implement periodic refresh of voice library
2. Add support for voice preview/testing before assignment
3. Create admin interface for manual voice management
4. Add metrics tracking for voice usage patterns
