# Configuration System

ArtificialU provides a comprehensive configuration system that supports different environments, environment variables, and validation.

## Basic Usage

The simplest way to access configuration values is through the `get_settings()` function:

```python
from artificial_u.config import get_settings

# Get the settings singleton
settings = get_settings()

# Access configuration values
db_url = settings.DATABASE_URL
api_key = settings.ANTHROPIC_API_KEY
```

## Environment Detection

The configuration system automatically detects the current environment:

- **Development**: The default environment when no specific environment is detected
- **Testing**: Automatically detected when running under pytest or when `TESTING=true` is set
- **Production**: Set when `ENV=production` is in environment variables

## Environment Variables and Files

Configuration values are loaded from the following sources in order:

1. Default values defined in code
2. Environment variables file (`.env`, `.env.test`, etc.)
3. System environment variables
4. Explicitly provided values

### Environment Files

- `.env`: Default environment file for development
- `.env.test`: Used automatically when running tests
- `.env.example`: Template showing required variables (not loaded)

You can specify a custom environment file using the `ENV_FILE` environment variable:

```bash
ENV_FILE=.env.staging python app.py
```

## Content Generation Configuration

ArtificialU supports multiple backends for content generation:

```python
# Backend: 'anthropic' or 'openai' or 'gemini'
content_backend=anthropic

# Model to use with the chosen backend
content_model=claude-3-7-sonnet-latest
```

## Storage Configuration

ArtificialU provides a unified storage interface for both local development (MinIO) and production (AWS S3):

### MinIO Configuration (Development)

For local development with MinIO, you **must** set the following environment variables in your `.env` file:

```bash
STORAGE_TYPE=minio
STORAGE_ENDPOINT_URL=http://localhost:9000
STORAGE_PUBLIC_URL=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_REGION=us-east-1
STORAGE_AUDIO_BUCKET=artificial-u-audio
STORAGE_LECTURES_BUCKET=artificial-u-lectures
STORAGE_IMAGES_BUCKET=artificial-u-images
STORAGE_EXPORTS_BUCKET=artificial-u-exports
STORAGE_CONTENT_LOGS_BUCKET=artificial-u-content-logs
```

**Important:** The `STORAGE_ACCESS_KEY` and `STORAGE_SECRET_KEY` have no default values and must be explicitly set for MinIO to work.

### AWS S3 Configuration (Production)

For production deployments on ECS/Fargate, the application uses IAM role-based authentication instead of explicit credentials. The IAM role is automatically attached to the ECS task by the CDK stack.

**Required Environment Variables:**

```python
STORAGE_TYPE = "s3"
STORAGE_REGION = "us-east-1"  # or your AWS region
STORAGE_AUDIO_BUCKET = "your-audio-bucket"
STORAGE_LECTURES_BUCKET = "your-lectures-bucket"
STORAGE_IMAGES_BUCKET = "your-images-bucket"
STORAGE_EXPORTS_BUCKET = "your-exports-bucket"
```

**Optional (for non-ECS deployments):**

If you're running outside of ECS and don't have IAM role access, you can provide explicit credentials:

```python
STORAGE_ACCESS_KEY = "your-aws-access-key"  # Optional, uses IAM role if not provided
STORAGE_SECRET_KEY = "your-aws-secret-key"  # Optional, uses IAM role if not provided
```

**Note:** The CDK stack automatically configures the bucket names and IAM permissions. When deploying via CDK, you only need to ensure `STORAGE_TYPE="s3"` is set, and the bucket names will be injected from the stack outputs.

### Content Logs

ArtificialU automatically logs all LLM generation requests and responses for debugging and analysis purposes. These logs are stored as JSON files in a dedicated bucket:

**Development (MinIO):**

```python
STORAGE_CONTENT_LOGS_BUCKET = "artificial-u-content-logs"
```

**Production (S3):**
The CDK stack automatically creates and configures the content logs bucket with the appropriate IAM permissions.

Each log file contains:

- **Metadata**: timestamp, backend, model, temperature, max_tokens
- **Content**: system_prompt, prompt, prefill (if applicable), response

Log files are named with the format: `{timestamp}_{backend}_{model}.json`

This allows you to browse and download logs from your MinIO console (dev) or S3 console (prod) for inspection, analysis, or debugging of generation issues.

## Model Selection

ArtificialU allows configuration of different AI models for various services:

```python
# Course generation model
COURSE_GENERATION_MODEL=gpt-5.4-nano

# Department generation model
DEPARTMENT_GENERATION_MODEL=gpt-5.4-nano

# Lecture generation model
LECTURE_GENERATION_MODEL=claude-sonnet-4-6

# Professor generation model
PROFESSOR_GENERATION_MODEL=gpt-5.4-nano

# Topics generation model
TOPICS_GENERATION_MODEL=gemini-3.5-flash

# Image generation model (gemini-3.1-flash-lite-image, gemini-3.1-flash-image, or gemini-3-pro-image)
IMAGE_GENERATION_MODEL=gemini-3.1-flash-lite-image

# Text-to-speech voice model (ElevenLabs)
# Must be supported by the selected voice's verified languages
# Common values: eleven_flash_v2_5, eleven_multilingual_v2
TTS_VOICE_MODEL=eleven_flash_v2_5
```

### Anthropic (Claude) Model Version Compatibility

`ContentService` inspects the Claude model name (e.g. `claude-sonnet-4-6`,
`claude-opus-4-8`, `claude-sonnet-5`) to automatically adjust request parameters
for API differences across model generations, so callers can swap
`LECTURE_GENERATION_MODEL` (or the equivalent preference) without code changes:

- **Prefill**: Claude 4.6+ models (including Sonnet 5) reject assistant-message
  prefill with a 400 error; it's automatically skipped for these models.
- **Sampling params**: Claude 4.7+ models (including Opus 4.8 and Sonnet 5) reject
  non-default `temperature`/`top_p`/`top_k`; these are omitted for supported models
  instead of causing a request failure.
- **Effort**: Claude Opus 4.5+ and Sonnet 4.6+ (including Sonnet 5) support the
  `output_config.effort` parameter, which controls overall token spend. Defaults to
  `"medium"` for content generation.
- **Adaptive thinking**: Claude Sonnet 5 is the first model that runs adaptive
  thinking by default (no `thinking` field required), and thinking tokens count
  against `max_tokens`. To keep output budgets predictable and behavior consistent
  with Sonnet 4.6/Opus 4.5-4.8 (which don't think unless explicitly configured),
  `ContentService` explicitly sends `thinking: {"type": "disabled"}` for Sonnet 5+
  models.

Model names are parsed with `ContentService._parse_claude_version()`, which
understands both the `claude-{tier}-{major}-{minor}[-date]` naming scheme (e.g.
`claude-sonnet-4-6`) and the bare-major naming scheme introduced with Sonnet 5
(e.g. `claude-sonnet-5`, with no explicit minor version).

## Lecture Defaults

Lecture generation and lecture image planning have hard-coded defaults that can be overridden with primary environment variables:

```python
# Target word count for generated lectures (default: 3000)
LECTURE_WORD_COUNT=3000

# Approximate seconds between generated lecture images (default: 45)
LECTURE_IMAGE_INTERVAL_SEC=45
```

## Coin Costs for Generation Operations

ArtificialU uses a virtual currency system ("coins") to control access to expensive AI generation operations. These costs can be configured via environment variables:

```python
# Cost for course generation (default: 1)
COIN_COST_COURSE_GENERATION=1

# Cost for lecture generation (default: 5)
COIN_COST_LECTURE_GENERATION=5

# Cost for lecture audio generation (default: 10)
COIN_COST_LECTURE_AUDIO=10

# Cost for lecture summary generation (default: 0)
COIN_COST_LECTURE_SUMMARY=0

# Cost for topic generation (default: 3)
COIN_COST_TOPIC_GENERATION=3

# Cost for professor generation (default: 0)
COIN_COST_PROFESSOR_GENERATION=0

# Cost for professor image generation (default: 2)
COIN_COST_PROFESSOR_IMAGE=2

# Cost for department generation (default: 0)
COIN_COST_DEPARTMENT_GENERATION=0
```

These costs are deducted from a user's coin balance when they trigger generation operations. Administrators bypass coin checks entirely.

## Logging Configuration

Configure logging level:

```python
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

### Process diagnostics (optional)

The API can emit periodic structured JSON logs for process-level metrics (memory, GC, open FDs, threads, and related counters) to help correlate behavior across Gunicorn workers. This is controlled by plain environment variables read in the FastAPI lifespan (not Pydantic settings).

- **`DIAG_PROCESS_METRICS`**: Set to `1` to enable; **`0` or unset turns telemetry off** (default).
- **`DIAG_PROCESS_METRICS_INTERVAL_SEC`**: Sampling interval in seconds when enabled (default `30`).

### CloudWatch custom metrics (optional)

The API can also emit CloudWatch custom metrics (queue health, SSE health, worker utilization) using the ECS task role. This is **off by default** and must be explicitly enabled.

Important: because the API may run multiple Gunicorn workers per task, enable metrics emission only on a single “leader” process/task.

- **`DIAG_CLOUDWATCH_METRICS`**: Set to `1` to enable metrics emission (default off).
- **`DIAG_CLOUDWATCH_METRICS_LEADER`**: Set to `1` on exactly one task/process to avoid duplicate metric submissions.
- **`DIAG_CLOUDWATCH_METRICS_INTERVAL_SEC`**: Emission interval in seconds when enabled (default `60`).
- **`CLOUDWATCH_NAMESPACE`**: CloudWatch namespace to publish metrics under (default `ArtificialU`).

### One-off memory drift tracing (optional)

For one-off investigations of suspected memory growth, you can enable `tracemalloc` and capture allocation diffs vs a baseline snapshot. When enabled, the API takes a baseline snapshot on startup and logs a diff on `SIGUSR1` (top 25 deltas).

- **`DIAG_TRACEMALLOC`**: Set to `1` to enable (default off).
- Send `SIGUSR1` to the process (e.g. `kill -USR1 <pid>`) to log the diff.

## Database Configuration

Configure the PostgreSQL database connection:

```python
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/artificial_u_dev
```

## Testing Configuration

When running tests, the system automatically:

1. Detects the test environment using pytest detection
2. Loads `.env.test` instead of `.env`
3. Sets `settings.testing = True` and `settings.environment = Environment.TESTING`

You can manually set the testing environment with:

```python
TESTING=true
```

## Available Configuration Options

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `postgresql://postgres:postgres@localhost:5432/artificial_u_dev` | Yes |
| `ANTHROPIC_API_KEY` | API key for Anthropic | None | No |
| `ELEVENLABS_API_KEY` | API key for ElevenLabs | None | No |
| `MISTRAL_API_KEY` | API key for Mistral (TTS when using Mistral backend) | None | No |
| `XAI_API_KEY` | API key for xAI (TTS when using xAI/Grok backend) | None | No |
| `GOOGLE_API_KEY` | API key for Google | None | No |
| `OPENAI_API_KEY` | API key for OpenAI | None | No |
| `CONTENT_LOGS_PATH` | (Deprecated) Path for content generation logs | `content_logs` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `DIAG_PROCESS_METRICS` | Enable process-level diagnostic telemetry (`1` on; `0` or unset off) | `0` (off) | No |
| `DIAG_PROCESS_METRICS_INTERVAL_SEC` | Telemetry interval in seconds when `DIAG_PROCESS_METRICS=1` | `30` | No |
| `DIAG_CLOUDWATCH_METRICS` | Enable CloudWatch custom metrics emission (`1` on; `0` or unset off) | `0` (off) | No |
| `DIAG_CLOUDWATCH_METRICS_LEADER` | Emit metrics only when set to `1` (avoid duplicates) | `0` (off) | No |
| `DIAG_CLOUDWATCH_METRICS_INTERVAL_SEC` | Emission interval in seconds when enabled | `60` | No |
| `CLOUDWATCH_NAMESPACE` | CloudWatch metrics namespace | `ArtificialU` | No |
| `DIAG_TRACEMALLOC` | Enable one-off tracemalloc baseline + SIGUSR1 diffs (`1` on; `0` or unset off) | `0` (off) | No |
| `content_backend` | Backend for content generation | `anthropic` | No |
| `content_model` | Model for chosen backend | Depends on backend | No |
| `COURSE_GENERATION_MODEL` | Model for course generation | `gpt-5.4-nano` | No |
| `DEPARTMENT_GENERATION_MODEL` | Model for department generation | `gpt-5.4-nano` | No |
| `LECTURE_GENERATION_MODEL` | Model for lecture generation | `claude-sonnet-4-6` | No |
| `LECTURE_SUMMARY_MODEL` | Model for lecture summary generation | `gpt-5.4-nano` | No |
| `TOPICS_GENERATION_MODEL` | Model for topics generation | `gemini-3.5-flash` | No |
| `PROFESSOR_GENERATION_MODEL` | Model for professor generation | `gpt-5.4-nano` | No |
| `IMAGE_GENERATION_MODEL` | Model for image generation (`gemini-3.1-flash-lite-image`, `gemini-3.1-flash-image`, `gemini-3-pro-image`) | `gemini-3.1-flash-lite-image` | No |
| `TTS_VOICE_MODEL` | Model for text-to-speech voice | `eleven_flash_v2_5` | No |
| `XAI_TTS_BASE_URL` | Base URL for the xAI TTS API | `https://api.x.ai/v1` | No |
| `XAI_TTS_LANGUAGE` | Default output language (BCP-47) for the xAI backend | `en` | No |
| `LECTURE_WORD_COUNT` | Target word count for generated lectures | `3000` | No |
| `LECTURE_IMAGE_INTERVAL_SEC` | Approximate seconds between generated lecture images | `45` | No |
| `STORAGE_TYPE` | Storage type ("minio" or "s3") | `minio` | No |
| `STORAGE_ENDPOINT_URL` | MinIO endpoint URL | `http://localhost:9000` | No |
| `STORAGE_PUBLIC_URL` | Public URL for MinIO | `http://localhost:9000` | No |
| `STORAGE_ACCESS_KEY` | Storage access key | `minioadmin` | No |
| `STORAGE_SECRET_KEY` | Storage secret key | `minioadmin` | No |
| `STORAGE_REGION` | Storage region | `us-east-1` | No |
| `STORAGE_AUDIO_BUCKET` | Bucket for audio files | `artificial-u-audio` | No |
| `STORAGE_LECTURES_BUCKET` | Bucket for lecture files | `artificial-u-lectures` | No |
| `STORAGE_IMAGES_BUCKET` | Bucket for image files | `artificial-u-images` | No |
| `STORAGE_EXPORTS_BUCKET` | Bucket for course export files | `artificial-u-exports` | No |
| `COIN_COST_COURSE_GENERATION` | Coin cost for course generation | `10` | No |
| `COIN_COST_LECTURE_GENERATION` | Coin cost for lecture generation | `5` | No |
| `COIN_COST_LECTURE_AUDIO` | Coin cost for lecture audio | `3` | No |
| `COIN_COST_LECTURE_SUMMARY` | Coin cost for lecture summary | `2` | No |
| `COIN_COST_TOPIC_GENERATION` | Coin cost for topic generation | `8` | No |
| `COIN_COST_PROFESSOR_GENERATION` | Coin cost for professor generation | `5` | No |
| `COIN_COST_PROFESSOR_IMAGE` | Coin cost for professor image | `2` | No |
| `COIN_COST_DEPARTMENT_GENERATION` | Coin cost for department generation | `5` | No |
