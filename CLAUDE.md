# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArtificialU is an AI-powered educational content platform that generates university lectures with distinct professor personalities and converts them to audio using text-to-speech. The system features:

- **Backend**: Python 3.14 with FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: SolidJS with TypeScript, TailwindCSS v4, Auth0
- **AI Integration**: Anthropic Claude, Google Gemini, OpenAI
- **TTS Services**: ElevenLabs
- **Storage**: MinIO (dev) / S3 (prod)
- **Job Processing**: Custom async worker with PostgreSQL-backed queue

## Essential Commands

### Python Backend

All Python commands use `hatch` for environment management:

```bash
# Run CLI commands
hatch run artificial_u --help
hatch run artificial_u list-courses
hatch run artificial_u create-course -d "Computer Science" -t "AI" -c "CS101"
hatch run artificial_u create-audio -c "CS101" -w 1 -n 1

# Testing
hatch run pytest                    # All tests
hatch run pytest -m unit            # Unit tests only
hatch run pytest -m integration     # Integration tests only
hatch run pytest --cov=artificial_u # Coverage report
hatch run pytest tests/path/to/test_file.py::test_function_name  # Single test

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
pnpm lint:css         # Stylelint
pnpm lint:css:fix     # Auto-fix CSS issues
pnpm format           # Format with BiomeJS

pnpm test             # Run tests
pnpm test:watch       # Watch mode
pnpm test:coverage    # Coverage report
```

### Docker Services

```bash
docker compose up -d     # Start postgres, minio
docker compose down      # Stop services
docker compose logs -f   # View logs
docker compose restart   # Restart services
```

### Makefile Shortcuts

The project includes comprehensive Makefile commands:

```bash
make help              # Show all commands
make dev-setup         # Complete setup (services + database)
make check             # Run linting + tests
make test              # Run all tests
make lint              # All linting checks
make format            # Format code
make run-api           # Start FastAPI server
make run-api-no-reload # Start FastAPI server without auto-reload
make services-up       # Start Docker services
```

## Architecture Overview

### Three-Tier Architecture

1. **API Layer** (`artificial_u/api/routers/`)
   - FastAPI routers define REST endpoints
   - Handle HTTP concerns (request/response, validation)
   - Delegate to service layer

2. **Service Layer**
   - **API Services** (`artificial_u/api/services/`): HTTP-aware, coordinate multiple core services
   - **Core Services** (`artificial_u/services/`): Domain logic, no HTTP concerns
   - **Generator Services** (`artificial_u/services/`): AI content generation workflows

3. **Repository Layer** (`artificial_u/models/`)
   - SQLAlchemy models and repository pattern
   - Repository factory for dependency injection
   - All database access goes through repositories

### Key Components

**Backend Structure:**

```
artificial_u/
├── api/              # FastAPI application
│   ├── app.py        # Application factory
│   ├── dependencies.py  # Dependency injection
│   ├── events.py     # SSE event hub
│   ├── worker.py     # Background job processor
│   ├── routers/      # API endpoints
│   ├── services/     # API-layer services
│   ├── models/       # Pydantic request/response models
│   ├── middlewares/  # CORS, logging, error handling
│   └── security/     # Auth0 JWT validation
├── models/           # SQLAlchemy models & repositories
├── services/         # Core business logic
├── audio/            # TTS processing (SpeechProcessor, VoiceMapper)
├── integrations/     # External APIs (Anthropic, ElevenLabs, etc.)
├── prompts/          # AI prompt templates
├── config/           # Configuration management
└── utils/            # Shared utilities
```

**Frontend Structure:**

```
web/src/
├── api/              # API client & service calls
├── auth/             # Auth0 integration
├── components/       # Reusable UI components
├── pages/            # Route page components
├── utils/            # Utilities (theme, SSE, etc.)
└── App.tsx           # Main app with routing
```

### Core Domain Entities

- **Department**: Academic departments
- **Professor**: Virtual faculty with personalities and voice mappings
- **Course**: Structured academic courses with topics
- **Topic**: Weekly course subjects
- **Lecture**: Generated content + audio files
- **Voice**: ElevenLabs voice configurations
- **Student**: User accounts with Auth0 integration
- **Job**: Background task queue with status tracking

### Background Job System

Jobs are PostgreSQL-backed with async processing:

- Job types: content generation, audio conversion
- Status tracking: pending → in_progress → completed/failed
- Real-time updates via Server-Sent Events (SSE)
- Rate limiting for API compliance

## Development Workflow Guidelines

When building features or making significant changes:

1. **Ideate**: Research best practices, consider multiple solutions
2. **Proliferate**: Implement chosen approach
3. **Validate**: Test thoroughly (if fails, return to ideation)
4. **Simplify**: Remove duplication, abstract common patterns
5. **Document**: Update docs, write clear commit messages
6. **Continue**: Move forward with lessons learned

Key principles:

- Balance between modern patterns and proven approaches
- Stop and revert if stuck after multiple unsuccessful attempts
- Seek clarification when lacking confidence or context

## Testing Strategy

Tests are organized by pytest markers:

- `@pytest.mark.unit`: Isolated unit tests
- `@pytest.mark.integration`: Database/external service integration
- `@pytest.mark.e2e`: End-to-end workflows
- `@pytest.mark.api`: API endpoint tests
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.demo`: Demonstration tests

Integration tests require the test database:

```bash
hatch run python scripts/setup_test_db.py
hatch run pytest -m integration
```

## Key Configuration Files

- **pyproject.toml**: Python project metadata, dependencies, tool configs (black, isort, mypy, pytest)
- **pytest.ini**: Additional pytest configuration
- **.flake8**: Flake8 linting rules
- **.pre-commit-config.yaml**: Pre-commit hooks
- **alembic.ini**: Database migration configuration
- **docker-compose.yml**: Local service orchestration (postgres, minio)
- **web/package.json**: Frontend dependencies and scripts
- **web/biome.json**: BiomeJS formatter/linter config
- **web/tsconfig.json**: TypeScript configuration

## Code Quality Standards

**Python:**

- Python 3.14 only (`requires-python`, hatch env, CI, and CDK deployment)
- Line length: 100 characters (black, isort, flake8)
- Type hints encouraged (mypy runs on `artificial_u/` directory)
- Black formatting with isort for imports
- Pre-commit hooks run black, isort, flake8

### ALWAYS run checks before opening a PR

CI (`.github/workflows/test-quick.yml` and `web-quality.yml`) will fail a PR on
formatting/linting issues, so run the equivalent checks locally first. Before
committing or opening a PR, run **one** of the following from the repo root:

```bash
# Preferred: run the same hooks CI/pre-commit enforces across all files
make pre-commit            # = hatch run pre-commit run --all-files

# Or run the linters directly (mirrors the CI "Run linting checks" step)
make lint                  # black --check + isort --check-only + flake8

# To auto-fix formatting before re-checking
make format                # black + isort over artificial_u and tests
```

If you don't have `make`, the underlying commands are:

```bash
hatch run black artificial_u tests
hatch run isort artificial_u tests
hatch run flake8 artificial_u
```

For frontend changes, also run the web checks from `web/`:

```bash
cd web && pnpm lint && pnpm lint:css && pnpm exec biome ci . && pnpm build
```

**TypeScript:**

- ESLint with TypeScript parser
- BiomeJS for formatting
- Stylelint for CSS
- Full TypeScript coverage expected

## Database Operations

### Migrations with Alembic

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

## Audio Processing Pipeline

The TTS system has specialized components:

1. **SpeechProcessor**: Enhances text for TTS (technical terms, math notation, discipline-specific)
2. **VoiceMapper**: Matches professors to voices based on attributes (gender, accent, age)
3. **ElevenLabsClient**: Direct API integration with retry/rate limiting
4. **TTSService**: Orchestrates workflow, manages storage, handles caching

## API Development Patterns

When adding new endpoints:

1. Define Pydantic models in `artificial_u/api/models/`
2. Create router in `artificial_u/api/routers/`
3. Implement API service in `artificial_u/api/services/`
4. Use core services from `artificial_u/services/` for domain logic
5. Repository methods in `artificial_u/models/` for data access
6. Queue long operations as background jobs
7. Write integration tests in `tests/integration/api/`

All API responses should:

- Use proper HTTP status codes
- Include pagination for list endpoints
- Handle errors with standardized error responses
- Validate with Pydantic models

## Frontend Development Patterns

When adding features:

1. Create TypeScript interfaces matching API types
2. Add API calls to appropriate service in `web/src/api/services/`
3. Build components using Kobalte UI primitives
4. Use SolidJS signals for reactive state
5. Style with TailwindCSS v4 utilities
6. Support all theme variants (dark-academia, vaporwave, etc.)
7. Add route protection with `RequireAuth` for authenticated pages

## Environment Variables

Required in `.env` file:

- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `ELEVENLABS_API_KEY`: ElevenLabs TTS API key
- `MISTRAL_API_KEY`: Mistral API key (TTS when using Mistral backend)
- `XAI_API_KEY`: xAI API key (TTS when using xAI/Grok backend)
- `DATABASE_URL`: PostgreSQL connection string
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`: Auth0 configuration
- `MINIO_*` or `AWS_*`: Storage configuration

Frontend requires `.env.local` in `web/` directory with Auth0 and API URL configuration.

## Common Pitfalls

- **Alembic commands**: Use `scripts/run_alembic.py` wrapper, not raw `alembic` command
- **Import organization**: Use isort profile "black" for consistent ordering
- **Type hints**: While not strictly required, mypy runs on the main codebase
- **Web directory**: Frontend commands must run from `web/` directory
- **Test database**: Integration tests fail without test database setup
- **Hatch environment**: Always use `hatch run` or activate `hatch shell` first
- **Long-running commands**: Development servers (API, frontend) don't terminate automatically
- **Python version**: Use 3.14 only; other versions fail on syntax (e.g. bracketless `except`) and can drift Black/Ruff formatting
- **Skipping pre-commit before a PR**: Run `make pre-commit` (or `make lint`/`make format`) before pushing so CI doesn't fail on black, isort, or flake8

## Additional Documentation

- `docs/ARCHITECTURE.md`: Comprehensive architecture documentation
- `docs/development.md`: Detailed development environment guide
- `docs/POSTGRES.md`: Database setup and management
- `docs/AUTHENTICATION.md`: Auth0 integration details
- `web/STYLE_GUIDE.md`: Frontend styling guidelines
