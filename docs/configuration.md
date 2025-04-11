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

# Use helper methods
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

## Available Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://postgres:postgres@localhost:5432/artificial_u_dev` |
| `ANTHROPIC_API_KEY` | API key for Anthropic | None |
| `ELEVENLABS_API_KEY` | API key for ElevenLabs | None |
| `OPENAI_API_KEY` | API key for OpenAI | None |
| `AUDIO_STORAGE_PATH` | Path to store audio files | `./audio_files` |
| `AUDIO_PATH` | Path for audio resources | `audio` |
| `TEXT_EXPORT_PATH` | Path for text exports | `exports` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `content_backend` | Backend for content generation | `anthropic` |
| `content_model` | Model for chosen backend | Depends on backend |
| `enable_caching` | Whether to enable caching | `False` |
| `cache_metrics` | Whether to track cache metrics | `True` |
