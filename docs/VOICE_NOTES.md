# VOICE NOTES (ElevenLabs API)

## Two Collections

- There are two endpoints for finding voices:
  - /v1/shared-voices "Shared Voices"
  - /v2/voices "Voices"
- The Voices endpoint hosts the "official" elevenlabs voices along with whatever might be in my "voice library".
  - Currently about 76 voices
- The Shared Voices omits the "official" voices, but contains a massive collection of community shared voices
  - Currently about 6,000 voices

## The JSON structure is different in the responses from each of these endpoints

### Shared top-level fields

- category (but the values may differ!)
- description
- name
- preview_url
- verified_languages (but values may differ!)
- voice_id

### Shared fields, at different (nested) levels

These fields are found at the top-level of shared-voices voice,
and within the "labels" object of Voice voice:

- accent
- age
- descriptive
- gender
- language
- use_case

The Voice response contains a "sharing" object with many fields that are also
found at the top-level of shared-voices, including:

- category (this matches the shared category)
- cloned_by_count (different value!)
- date_unix
- description (same as top-level)
- fiat_rate
- free_users_allowed
- image_url
- live_moderation_enabled
- name (same as top-level)
- notice_period
- public_owner_id
- rate

NOTE: this "sharing" object only exists on shared voices that have been added to my voice library, but not on official "premade" elevenlabs voices.

## Current database fields in my voice table

- el_voice_id (elevenlabs voice_id)
- name
- accent
- age
- category
- description
- descriptive
- gender
- language
- locale
- popularity_score (calculated by me)
- preview_url
- use_case
- verified_languages

## Fields to be wary of

These fields may be good to filter against:

- live_moderation_enabled (boolean)

This indicates if the text provided is checked for prohibited usage, which can incur extra latency.

- rate (double or null)
- fiat_rate (double or null)

Non-null values of these fields indicates additional surcharge for usage.

## Language and Accent

My list of SUPPORTED_ACCENTS is obsolete. The actual accent values in the voice library are prolific, inconsistent, often user-generated, and not canonical.

Many sub-regions are now supported, complicating filtering by simple national accents like "Greek" or "French". Instead a voice might have an accent value of "athenian", "quebec", etc.

The Voice endpoint does not even support a specific "language" or "accent" query param.
(But I can filter them myself if I pull that small collection into the database).

Helpfully, the shared-voices endpoint accepts 'language', 'accent', and 'locale' params.
Unhelpfully, if a 'language' value is invalid, it just returns unfiltered restults.
'language' must be a two-letter language code, e.g. 'el' for Greek.

If 'accent' is invalid (ie has no results), no results are returned. But 'accent' is not especially useful since it filters now on the multitudinous sub-regional accents. Unless you know you want 'athenian' or 'quebec' rather than 'greek' or 'french', it should be avoided.

Filtering on language is a useful proxy for accent.

The 'verified_languages' object is not actually very useful, except maybe for non-english tts. It seems to omit English even when english is obviously supported by the voice.

## Action Items

- Pull and store all voices from the v2/voice endpoint with category="premade"
- Give category: "premade" voices a quality score above "high_quality" and "professional"
- Ignore or discard "popularity_score" as unhelpful
- Fetch more voices from 'v1/shared-voices' more often
- Convert "accent" value to two-letter language value for voice queries; don't query on "accent"
- Limit or discourage re-use of a voice by multiple professors, eg by applying a negative 'score' modifier
- filter out shared-voices where rate is not null
- filter out shared-voices where fiat_rate is not null
- when fetching a "premade" voice from the v2/voice endpoint, use the nested "labels" values:
  labels.accent, labels.age, labels.description, labels.gender, labels.language, labels.use_case
