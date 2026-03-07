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
COURSE_GENERATION_MODEL=gpt-5-nano

# Department generation model
DEPARTMENT_GENERATION_MODEL=gpt-5-nano

# Lecture generation model
LECTURE_GENERATION_MODEL=claude-opus-4-6

# Professor generation model
PROFESSOR_GENERATION_MODEL=gpt-5-nano

# Topics generation model
TOPICS_GENERATION_MODEL=gemini-3.1-flash-lite-preview

# Image generation model
IMAGE_GENERATION_MODEL=gemini-3.1-flash-image-preview

# Text-to-speech voice model (ElevenLabs)
# Must be supported by the selected voice's verified languages
# Common values: eleven_flash_v2_5, eleven_multilingual_v2
TTS_VOICE_MODEL=eleven_flash_v2_5
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
| `GOOGLE_API_KEY` | API key for Google | None | No |
| `OPENAI_API_KEY` | API key for OpenAI | None | No |
| `CONTENT_LOGS_PATH` | (Deprecated) Path for content generation logs | `content_logs` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `content_backend` | Backend for content generation | `anthropic` | No |
| `content_model` | Model for chosen backend | Depends on backend | No |
| `COURSE_GENERATION_MODEL` | Model for course generation | `gpt-5-nano` | No |
| `DEPARTMENT_GENERATION_MODEL` | Model for department generation | `gpt-5-nano` | No |
| `LECTURE_GENERATION_MODEL` | Model for lecture generation | `claude-opus-4-6` | No |
| `LECTURE_SUMMARY_MODEL` | Model for lecture summary generation | `gpt-5-nano` | No |
| `TOPICS_GENERATION_MODEL` | Model for topics generation | `gemini-3.1-flash-lite-preview` | No |
| `PROFESSOR_GENERATION_MODEL` | Model for professor generation | `gpt-5-nano` | No |
| `IMAGE_GENERATION_MODEL` | Model for image generation | `gemini-3.1-flash-image-preview` | No |
| `TTS_VOICE_MODEL` | Model for text-to-speech voice | `eleven_flash_v2_5` | No |
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
