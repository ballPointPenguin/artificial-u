# ElevenLabs API Notes

## Shared Voices ie the "Voice Library"

base URL: `https://api.elevenlabs.io/v1/shared-voices`

## Query Parameters

- `featured`: boolean (default: `false`)
- `reader_app_enabled`: boolean (default: `false`)
- `page_size`: integer (default: 30, max: 100)
- `category`: enum (default: nil)
  - `famous`
  - `high_quality`
  - `professional`
  - nil ("any")
- `gender`: string (default: nil)
  - `male`
  - `female`
  - `neutral`
  - nil ("any")
- `age`: string (default: nil)
  - `young`
  - `middle_aged`
  - `old`
  - nil ("any")
- `language`: string (default: nil); e.g. "en"
- `locale`: string (default: nil)
- `search`: string (default: nil)
- `use_cases`: string (default: nil)
  - `narrative_story`
  - `conversational`
  - `characters_animation`
  - `social_media`
  - `entertainment_tv`
  - `advertisement`
  - `informative_educational`
- `descriptives`: string (default: nil)
- `min_notice_period_days`: integer (default: 0); 0 means "any"
- `owner_id`: string (default nil)
- `sort`: string (default nil)
  - `trending`
  - `created_date`
  - `cloned_by_count`
  - `usage_character_count_1yr`
- `page`: integer (default 0) "infinite" pagination
- `accent`: string (default: nil); language must be specified

accents listed, for English-capable voices (not all accents have > 0 voices):
  american, australian, british, canadian, indian, irish, jamaican,
  new+zealand, nigerian, scottish, south+african, african+american,
  singaporean, boston, chicago, new+york, us+southern, us+midwest,
  us+northeast, cockney, geordie, received+pronunciation, scouse,
  welsh, yorkshire, arabic, bulgarian, chinese, croatian, czech,
  danish, dutch, filipino, finnish, frenh, german, greek, hindi,
  indonesian, italian, japanese, korean, malay, polish,
  portuguese, romanian, russian, slovak, spanish, swedish, tamil,
  turkish, ukrainian

## Example Request

```txt
https://api.elevenlabs.io/v1/shared-voices?page_size=5&lang=en&sort=cloned_by_count&use_cases=informative_educational
```

## Example Response

See [response.json](./voices-response.json)
