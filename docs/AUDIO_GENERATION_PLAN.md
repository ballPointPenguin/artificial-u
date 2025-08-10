# Lecture Audio Generation Plan

## Goals

- Convert `lecture.content` to speech using the professor’s assigned ElevenLabs voice
- Store generated audio in MinIO (dev/test) or AWS S3 (prod) via `StorageService`
- Update `lecture.audio_url` and expose it via existing API (`GET /v1/lectures/{id}/audio`)
- Provide a synchronous trigger endpoint (`POST /v1/lectures/{id}/generate-audio`) with extended timeout for now

## References

- ElevenLabs Create speech API: <https://elevenlabs.io/docs/api-reference/text-to-speech/convert>
- ElevenLabs TTS capabilities and formats: <https://elevenlabs.io/docs/capabilities/text-to-speech>
- ElevenLabs Python SDK: <https://github.com/elevenlabs/elevenlabs-python/blob/main/README.md>

## Current State (repo overview)

- API
  - `POST /v1/lectures/{id}/generate-audio` added; returns updated `Lecture`
  - `GET /v1/lectures/{id}/audio` returns a 307 JSON redirect to storage URL
- Services
  - `artificial_u/services/tts_service.py`: Orchestrates TTS using ElevenLabs client, chunking, enhancement
  - `artificial_u/services/audio_service.py`: Generates and stores audio keyed by `(course_code, week, number)`; updates `lecture.audio_url`
  - `artificial_u/services/voice_service.py`: Voice selection and DB sync with ElevenLabs
  - `artificial_u/services/storage_service.py`: Uploads to MinIO/S3; constructs public URLs
  - `artificial_u/services/lecture_service.py`: Core lecture service implements `generate_lecture_audio(lecture_id)` with helpers for entity fetching, voice resolution, TTS, and storage upload
  - `artificial_u/api/services/lecture_service.py`: API layer calls core and returns `Lecture`

## Status / Progress

- Completed
  - Added frontend trigger and API route `POST /v1/lectures/{id}/generate-audio`
  - Implemented core orchestration by `lecture_id` with helper methods:
    - Fetch entities (lecture, course, topic, professor)
    - Auto-select/assign professor voice if missing
    - Generate audio via `TTSService` (mp3 default)
    - Upload to storage via `StorageService` and update `lecture.audio_url`
  - Frontend shows “Generate Audio” button and refreshes lecture
- Remaining
  - Unit tests for `generate_lecture_audio` with mocks (TTS, storage, voice selection)
  - Configurability for model and output format (optional)
  - Optional background processing and progress endpoints (later)
  - Optional audio join smoothing (crossfade) for long lectures (later)

## Proposed End-to-End Flow (synchronous MVP)

1. Client triggers `POST /v1/lectures/{id}/generate-audio`
2. API service verifies lecture exists, delegates to core: `LectureService.generate_lecture_audio(lecture_id)`
3. Core service orchestrates:
   - Fetch `Lecture`, `Topic` (to get `week`/`order`), `Course` (to get `code`), and `Professor`
   - Ensure professor has an assigned voice: if missing, select one via `VoiceService.select_voice_for_professor`
   - Call `TTSService.generate_lecture_audio(lecture, professor, el_voice_id)` to get audio bytes (mp3)
   - Create storage key via `StorageService.generate_audio_key(course_code, week, order)`
   - `StorageService.upload_audio_file(bytes, key)` → returns public `audio_url`
   - Update `lecture.audio_url` in repository; return updated `Lecture`
4. API returns updated `Lecture` JSON
5. Client refetches lecture; “Listen”/“Get Audio” becomes available

## ElevenLabs usage notes

- Default model: `eleven_flash_v2_5` (fast, low-latency); configurable
- Default format: mp3; other `output_format` variants available (see capabilities doc)
- Python SDK call path in our client: `client.text_to_speech.convert(text, voice_id, model_id, voice_settings)` (Create speech API)
- Chunking: Implemented in `TTSService` via `SpeechProcessor.split_into_chunks`, with concatenation of segments

## Incremental Implementation Steps

1. Core orchestration by lecture_id (COMPLETED)
   - Implement `LectureService.generate_lecture_audio(lecture_id)` to:
     - Fetch `Lecture`, `Topic`, `Course`, `Professor`
     - Ensure/resolve `el_voice_id` (select voice if missing)
     - Call `TTSService.generate_lecture_audio`
     - Compute storage key from `(course.code, topic.week, topic.order)`; upload; update `lecture.audio_url`
   - Implemented directly in `LectureService` with small helpers; no reuse of legacy `AudioService` path

2. Storage key convention
   - Use `StorageService.generate_audio_key(course_id: str, week_number: int, lecture_order: int)`
   - Prefer `course.code` for the path segment (matches `AudioService` usage)

3. Voice resolution
   - If `professor.voice_id` exists, map to ElevenLabs `el_voice_id` via `VoiceRepository.get`
   - If missing, call `VoiceService.select_voice_for_professor(professor)` to auto-assign and persist, then extract `el_voice_id`

4. Error handling and timeouts
   - 404 if lecture not found
   - 400/500 if content missing or TTS/storage fails; include logging
   - Keep synchronous MVP with extended timeout; background processing later

5. API response
   - Return updated `Lecture` (with `audio_url` set) on success
   - Frontend will refetch or use returned body to show audio actions

6. Tests
   - Unit tests for `LectureService.generate_lecture_audio(lecture_id)` with mocks:
     - TTS client → returns bytes
     - Storage service → returns URL
     - Repository interactions → updates lecture
   - Integration test: exercise TTS layer in test mode (mock ElevenLabs client) and storage upload

## Configuration

- Requires `ELEVENLABS_API_KEY` and storage config (MinIO defaults for dev/test)
- Optional: model/format overrides in settings (`TTSService.DEFAULT_MODEL`)

## Future Enhancements (post-MVP)

- Background task queue and progress endpoints
- Regeneration with `seed` and caching of segments
- Transcript generation and `transcript_url` support
- Streaming TTS path for real-time playback
- Parameterizing `output_format`, `voice_settings`, and language enforcement

## Decisions

- Voice assignment: Auto-select and assign a voice if `professor.voice_id` is missing
- Audio format: Use `mp3_44100_128` for now; make configurable later if needed
- Long content handling: Current chunking via `SpeechProcessor` is sufficient; crossfade/join smoothing can be explored later
- Regeneration semantics: New generation overwrites `lecture.audio_url` if it already exists; old files remain in storage
