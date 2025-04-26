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

## Settings Class

The `Settings` class from `artificial_u.config` is a Pydantic model that provides validation, typing, and helper methods:

```python
from artificial_u.config import Settings

# Create custom settings
my_settings = Settings(
    DATABASE_URL="postgresql://user:pass@host/db",
    ANTHROPIC_API_KEY="my-api-key"
)

# Use helper methods (e.g., create temporary directories)
my_settings.create_directories()
my_settings.log_configuration()
```

## Test Environment

When running tests, the configuration system automatically:

1. Detects the test environment using pytest detection
2. Loads `.env.test` instead of `.env`
3. Sets `settings.testing = True` and `settings.environment = Environment.TESTING`

## Legacy ConfigManager

For backwards compatibility, the legacy `ConfigManager` class is still available:

```python
from artificial_u.config import ConfigManager

# Create a config manager (will show deprecation warning)
config = ConfigManager(
    anthropic_api_key="my-key",
    enable_caching=True
)

# Access values through properties
db_url = config.db_url
```

The `ConfigManager` now delegates to the new `Settings` system internally.

## Storage Configuration (MinIO/S3)

ArtificialU exclusively uses remote storage for generated assets:

1. **Local MinIO**: For development environments (default)
2. **AWS S3**: For production environments

### MinIO Configuration

When using MinIO in development, the following settings are used:

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

### AWS S3 Configuration

For production environments, set these variables in your `.env` file:

```txt
STORAGE_TYPE=s3
STORAGE_ACCESS_KEY=your-aws-access-key
STORAGE_SECRET_KEY=your-aws-secret-key
STORAGE_REGION=your-aws-region
STORAGE_AUDIO_BUCKET=your-audio-bucket
STORAGE_LECTURES_BUCKET=your-lectures-bucket
STORAGE_IMAGES_BUCKET=your-images-bucket
```

### Storage Service Usage

The `StorageService` provides a unified API for both MinIO and S3:

```python
from artificial_u.services import StorageService

# Initialize the service (uses settings from config)
storage = StorageService()

# Upload a file
success, url = await storage.upload_audio_file(
    file_data=audio_bytes,
    object_name="course123/week1/lecture1.mp3",
    content_type="audio/mpeg"
)

# Download a file
audio_data, content_type = await storage.download_audio_file(
    object_name="course123/week1/lecture1.mp3"
)

# Get URL for a file
url = storage.get_file_url(
    bucket="artificial-u-audio",
    object_name="course123/week1/lecture1.mp3"
)
```

## Available Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://postgres:postgres@localhost:5432/artificial_u_dev` |
| `ANTHROPIC_API_KEY` | API key for Anthropic | None |
| `ELEVENLABS_API_KEY` | API key for ElevenLabs | None |
| `GOOGLE_API_KEY` | API key for Google | None |
| `OPENAI_API_KEY` | API key for OpenAI | None |
| `TEMP_AUDIO_PATH` | Path for *temporary* audio file processing | `temp_audio` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `content_backend` | Backend for content generation | `anthropic` |
| `content_model` | Model for chosen backend | Depends on backend |
| `enable_caching` | Whether to enable caching | `False` |
| `cache_metrics` | Whether to track cache metrics | `True` |
| `STORAGE_TYPE` | Storage type ("minio" or "s3") | `minio` |
| `STORAGE_ENDPOINT_URL` | MinIO endpoint URL | `http://localhost:9000` |
| `STORAGE_PUBLIC_URL` | Public URL for MinIO | `http://localhost:9000` |
| `STORAGE_ACCESS_KEY` | Storage access key | `minioadmin` |
| `STORAGE_SECRET_KEY` | Storage secret key | `minioadmin` |
| `STORAGE_REGION` | Storage region | `us-east-1` |
| `STORAGE_AUDIO_BUCKET` | Bucket for audio files | `artificial-u-audio` |
| `STORAGE_LECTURES_BUCKET` | Bucket for lecture files | `artificial-u-lectures` |
| `STORAGE_IMAGES_BUCKET` | Bucket for image files | `artificial-u-images` |
