# Configuration System

ArtificialU provides a comprehensive configuration system that supports different environments, environment variables, and validation.

## Required API Keys

ArtificialU requires the following API keys to function properly:

- **ANTHROPIC_API_KEY**: Required for content generation using Claude models
- **ELEVENLABS_API_KEY**: Required for text-to-speech conversion

These keys must be set in your `.env` file or as environment variables before running the application.

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
# Backend: 'anthropic' or 'ollama'
content_backend=anthropic

# Model to use with the chosen backend
content_model=claude-3-7-sonnet-latest

# If using Ollama, specify the host URL
OLLAMA_HOST=http://localhost:11434
```

## Storage Configuration

ArtificialU provides a unified storage interface for both local development (MinIO) and production (AWS S3):

### MinIO Configuration (Development)

```python
STORAGE_TYPE = "minio"
STORAGE_ENDPOINT_URL = "http://localhost:9000"
STORAGE_PUBLIC_URL = "http://localhost:9000"
STORAGE_ACCESS_KEY = "minioadmin"
STORAGE_SECRET_KEY = "minioadmin"
STORAGE_REGION = "us-east-1"
STORAGE_AUDIO_BUCKET = "artificial-u-audio"
STORAGE_LECTURES_BUCKET = "artificial-u-lectures"
STORAGE_IMAGES_BUCKET = "artificial-u-images"
```

### AWS S3 Configuration (Production)

```python
STORAGE_TYPE = "s3"
STORAGE_ACCESS_KEY = "your-aws-access-key"
STORAGE_SECRET_KEY = "your-aws-secret-key"
STORAGE_REGION = "your-aws-region"
STORAGE_AUDIO_BUCKET = "your-audio-bucket"
STORAGE_LECTURES_BUCKET = "your-lectures-bucket"
STORAGE_IMAGES_BUCKET = "your-images-bucket"
```

## Model Selection

ArtificialU allows configuration of different AI models for various services:

```python
# Course generation model
COURSE_GENERATION_MODEL=claude-3-7-sonnet-latest

# Department generation model
DEPARTMENT_GENERATION_MODEL=gpt-4.1-nano

# Professor generation model
PROFESSOR_GENERATION_MODEL=claude-3-5-haiku-latest

# Image generation model
IMAGE_GENERATION_MODEL=imagen-3.0-generate-002
```

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
| `ANTHROPIC_API_KEY` | API key for Anthropic | None | Yes |
| `ELEVENLABS_API_KEY` | API key for ElevenLabs | None | Yes |
| `GOOGLE_API_KEY` | API key for Google | None | No |
| `OPENAI_API_KEY` | API key for OpenAI | None | No |
| `TEMP_AUDIO_PATH` | Path for *temporary* audio file processing | `temp_audio` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `content_backend` | Backend for content generation | `anthropic` | No |
| `content_model` | Model for chosen backend | Depends on backend | No |
| `COURSE_GENERATION_MODEL` | Model for course generation | `claude-3-7-sonnet-latest` | No |
| `DEPARTMENT_GENERATION_MODEL` | Model for department generation | `gpt-4.1-nano` | No |
| `PROFESSOR_GENERATION_MODEL` | Model for professor generation | `claude-3-5-haiku-latest` | No |
| `IMAGE_GENERATION_MODEL` | Model for image generation | `imagen-3.0-generate-002` | No |
| `STORAGE_TYPE` | Storage type ("minio" or "s3") | `minio` | No |
| `STORAGE_ENDPOINT_URL` | MinIO endpoint URL | `http://localhost:9000` | No |
| `STORAGE_PUBLIC_URL` | Public URL for MinIO | `http://localhost:9000` | No |
| `STORAGE_ACCESS_KEY` | Storage access key | `minioadmin` | No |
| `STORAGE_SECRET_KEY` | Storage secret key | `minioadmin` | No |
| `STORAGE_REGION` | Storage region | `us-east-1` | No |
| `STORAGE_AUDIO_BUCKET` | Bucket for audio files | `artificial-u-audio` | No |
| `STORAGE_LECTURES_BUCKET` | Bucket for lecture files | `artificial-u-lectures` | No |
| `STORAGE_IMAGES_BUCKET` | Bucket for image files | `artificial-u-images` | No |
