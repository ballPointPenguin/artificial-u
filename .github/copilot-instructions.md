# GitHub Copilot Instructions for ArtificialU

This file provides instructions for GitHub Copilot when working with the ArtificialU codebase.

## Project Overview

ArtificialU is an AI-powered educational content platform that generates university lectures with distinct professor personalities and converts them to audio using text-to-speech.

### Technology Stack

**Backend:**

- Python 3.14 with FastAPI
- PostgreSQL with SQLAlchemy ORM
- Hatch for environment management
- AI: Anthropic Claude, Google Gemini, OpenAI
- TTS: ElevenLabs
- Storage: MinIO (dev) / S3 (prod)
- Background jobs: Custom async worker with PostgreSQL-backed queue

**Frontend:**

- SolidJS with TypeScript
- TailwindCSS v4
- Auth0 for authentication
- Kobalte UI for components
- Vite for build tooling

## Architecture

### Three-Tier Backend Architecture

1. **API Layer** (`artificial_u/api/routers/`)
   - FastAPI routers define REST endpoints
   - Handle HTTP concerns (request/response, validation)
   - Delegate business logic to service layer

2. **Service Layer**
   - **API Services** (`artificial_u/api/services/`): HTTP-aware, coordinate multiple core services
   - **Core Services** (`artificial_u/services/`): Pure domain logic, no HTTP dependencies
   - **Generator Services**: AI content generation workflows

3. **Repository Layer** (`artificial_u/models/`)
   - SQLAlchemy models and repository pattern
   - Repository factory for dependency injection
   - All database access goes through repositories

### Key Directory Structure

```
artificial_u/
├── api/                 # FastAPI application
│   ├── app.py          # Application factory
│   ├── dependencies.py # Dependency injection
│   ├── routers/        # API endpoints
│   ├── services/       # API-layer services
│   ├── models/         # Pydantic request/response models
│   ├── middlewares/    # CORS, logging, error handling
│   └── security/       # Auth0 JWT validation
├── models/             # SQLAlchemy models & repositories
├── services/           # Core business logic
├── audio/              # TTS processing
├── integrations/       # External API clients
├── prompts/            # AI prompt templates
└── config/             # Configuration management

web/src/
├── api/                # API client & service calls
├── auth/               # Auth0 integration
├── components/         # Reusable UI components
├── pages/              # Route page components
└── utils/              # Utilities (theme, SSE, etc.)
```

## Development Commands

### Python Backend

All Python commands use `hatch` for environment management:

```bash
# Run CLI commands
hatch run artificial_u --help
hatch run artificial_u list-courses

# Testing
hatch run pytest                    # All tests
hatch run pytest -m unit            # Unit tests only
hatch run pytest -m integration     # Integration tests only
hatch run pytest --cov=artificial_u # Coverage report

# Code quality
hatch run black artificial_u        # Format code
hatch run isort artificial_u        # Sort imports
hatch run flake8 artificial_u       # Lint
hatch run mypy artificial_u         # Type check

# Database
hatch run python scripts/initialize_db.py       # Setup dev database
hatch run python scripts/setup_test_db.py      # Setup test database
hatch run python scripts/run_alembic.py upgrade head  # Run migrations

# API server
hatch run uvicorn artificial_u.api.app:app --reload --host 0.0.0.0 --port 8000

# Background worker
hatch run python -m artificial_u.api.worker
```

### Frontend (SolidJS)

All frontend commands run from the `web/` directory using `pnpm`:

```bash
cd web

pnpm dev              # Start dev server (http://localhost:5173)
pnpm build            # Production build
pnpm preview          # Preview production build

pnpm lint             # ESLint
pnpm lint:fix         # Auto-fix ESLint issues
pnpm format           # Format with BiomeJS

pnpm test             # Run tests
pnpm test:watch       # Watch mode
pnpm test:coverage    # Coverage report
```

### Docker & Services

```bash
docker compose up -d     # Start postgres, minio
docker compose down      # Stop services
docker compose logs -f   # View logs

# Makefile shortcuts
make dev-setup          # Complete setup (services + database)
make check              # Run linting + tests
make test               # Run all tests
make lint               # All linting checks
make format             # Format code
make run-api            # Start FastAPI server
```

## Code Quality Standards

### Python

- **Line length**: 100 characters (enforced by black, isort, flake8)
- **Formatting**: Use Black formatter with isort for imports
- **Type hints**: Encouraged and checked with mypy on `artificial_u/` directory
- **Import order**: Use isort profile "black" for consistency
- **Linting**: Must pass flake8 checks
- **Pre-commit hooks**: Run black, isort, flake8 automatically

### TypeScript

- **Linting**: ESLint with TypeScript parser
- **Formatting**: BiomeJS for code formatting
- **Styling**: Stylelint for CSS
- **Type coverage**: Full TypeScript coverage expected
- **Components**: Use Kobalte UI primitives
- **State**: SolidJS signals for reactivity
- **Styling**: TailwindCSS v4 utilities

## Testing Guidelines

Tests are organized by pytest markers:

- `@pytest.mark.unit`: Isolated unit tests
- `@pytest.mark.integration`: Database/external service integration
- `@pytest.mark.e2e`: End-to-end workflows
- `@pytest.mark.api`: API endpoint tests
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.demo`: Demonstration tests

**Integration tests require test database setup:**

```bash
hatch run python scripts/setup_test_db.py
hatch run pytest -m integration
```

## API Development Patterns

When adding new API endpoints:

1. Define Pydantic request/response models in `artificial_u/api/models/`
2. Create router in `artificial_u/api/routers/`
3. Implement API service in `artificial_u/api/services/`
4. Use core services from `artificial_u/services/` for domain logic
5. Database access via repository methods in `artificial_u/models/`
6. Queue long operations as background jobs
7. Write integration tests in `tests/integration/api/`

**API Response Standards:**

- Use proper HTTP status codes
- Include pagination for list endpoints
- Handle errors with standardized error responses
- Validate all inputs with Pydantic models

## Database Operations

### Alembic Migrations

**IMPORTANT**: Always use the wrapper script, not raw `alembic` commands:

```bash
# Create new migration
hatch run python scripts/run_alembic.py revision --autogenerate -m "description"

# Apply migrations
hatch run python scripts/run_alembic.py upgrade head

# Rollback one version
hatch run python scripts/run_alembic.py downgrade -1
```

### Database Management Scripts

- `scripts/initialize_db.py`: Setup development database
- `scripts/setup_test_db.py`: Setup test database
- `scripts/rebuild_dev_db.py`: Rebuild dev database from scratch
- `scripts/run_alembic.py`: Wrapper for alembic commands with proper environment

## Domain Entities

Core domain models:

- **Department**: Academic departments
- **Professor**: Virtual faculty with personalities and voice mappings
- **Course**: Structured academic courses with topics
- **Topic**: Weekly course subjects
- **Lecture**: Generated content + audio files
- **Voice**: ElevenLabs voice configurations
- **Student**: User accounts with Auth0 integration
- **Job**: Background task queue with status tracking

## Background Job System

PostgreSQL-backed async job processing:

- Job types: content generation, audio conversion
- Status tracking: pending → in_progress → completed/failed
- Real-time updates via Server-Sent Events (SSE)
- Rate limiting for API compliance

## Audio Processing Pipeline

1. **SpeechProcessor**: Enhances text for TTS (technical terms, math notation, discipline-specific)
2. **VoiceMapper**: Matches professors to voices based on attributes (gender, accent, age)
3. **ElevenLabsClient**: Direct API integration with retry/rate limiting
4. **TTSService**: Orchestrates workflow, manages storage, handles caching

## Frontend Development Patterns

When adding frontend features:

1. Create TypeScript interfaces matching API types
2. Add API calls to appropriate service in `web/src/api/services/`
3. Build components using Kobalte UI primitives
4. Use SolidJS signals for reactive state
5. Style with TailwindCSS v4 utilities
6. Support all theme variants (dark-academia, vaporwave, etc.)
7. Add route protection with `RequireAuth` for authenticated pages

## Environment Variables

**Backend** (`.env` file):

- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `ELEVENLABS_API_KEY`: ElevenLabs TTS API key
- `MISTRAL_API_KEY`: Mistral API key (TTS when using Mistral backend)
- `XAI_API_KEY`: xAI API key (TTS when using xAI/Grok backend)
- `DATABASE_URL`: PostgreSQL connection string
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`: Auth0 configuration
- `MINIO_*` or `AWS_*`: Storage configuration

**Frontend** (`.env.local` in `web/` directory):

- Auth0 configuration
- API URL configuration

## Common Pitfalls to Avoid

1. **Alembic commands**: Never use raw `alembic` command - always use `scripts/run_alembic.py` wrapper
2. **Import organization**: Always use isort profile "black" for consistent import ordering
3. **Type hints**: While not strictly required, mypy runs on the main codebase
4. **Web directory**: Frontend commands MUST run from `web/` directory
5. **Test database**: Integration tests fail without proper test database setup
6. **Hatch environment**: Always use `hatch run` or activate `hatch shell` first
7. **Long-running commands**: Development servers (API, frontend) don't terminate automatically

## Configuration Files Reference

- `pyproject.toml`: Python project metadata, dependencies, tool configs (black, isort, mypy, pytest)
- `pytest.ini`: Additional pytest configuration
- `.flake8`: Flake8 linting rules
- `.pre-commit-config.yaml`: Pre-commit hooks
- `alembic.ini`: Database migration configuration
- `docker-compose.yml`: Local service orchestration (postgres, minio)
- `web/package.json`: Frontend dependencies and scripts
- `web/biome.json`: BiomeJS formatter/linter config
- `web/tsconfig.json`: TypeScript configuration

## Additional Documentation

For more detailed information, refer to:

- `docs/ARCHITECTURE.md`: Comprehensive architecture documentation
- `docs/development.md`: Detailed development environment guide
- `docs/POSTGRES.md`: Database setup and management
- `docs/AUTHENTICATION.md`: Auth0 integration details
- `web/STYLE_GUIDE.md`: Frontend styling guidelines
- `CLAUDE.md`: Instructions for Claude AI assistant
- `README.md`: Project overview and quick start guide
