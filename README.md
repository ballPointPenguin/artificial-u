# ArtificialU

An AI-powered educational content platform that generates university lectures with distinct professor personalities, converting them to audio for an immersive learning experience.

## Project Overview

ArtificialU combines the Anthropic Claude API for generating educational content with the ElevenLabs API for text-to-speech conversion. The system creates virtual professors with unique personalities, teaching styles, and backgrounds who deliver engaging lectures across various academic disciplines.

## Key Features

- **Course Generation**: Create full academic courses with topics and lecture content
- **Professor Profiles**: Generate diverse, detailed professor personas
- **Text-to-Speech**: Convert lecture content to audio using ElevenLabs voices
- **Modular Audio Architecture**: Clean separation between text processing, voice selection, and TTS conversion
- **Smart Voice Selection**: Automatically match professors to appropriate ElevenLabs voices based on gender, accent, and age
- **Speech Enhancement**: Intelligently process academic text for optimal TTS quality, including handling of technical terms and mathematical notation
- **AI Response Prefilling**: Guide Claude's responses with assistant message prefills for consistent formatting and structure (Anthropic models only)
- **CLI Interface**: Easy-to-use command line interface for generating content
- **Course and lecture generation** with consistent professor personas
- **Faculty directory** with professor information

## Prerequisites

- Python 3.14+
- Anthropic API key
- ElevenLabs API key
- [uv](https://docs.astral.sh/uv/) (for environment and dependency management)

## Installation & Setup

This project uses [uv](https://docs.astral.sh/uv/) for managing the Python toolchain, virtual environment, and dependencies.

### Installing uv (Recommended)

```bash
brew install uv
# or: curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. **Clone the repository:**

    ```bash
    git clone https://github.com/ballPointPenguin/artificial-u.git
    cd artificial_u
    ```

2. **Install Project & Dependencies:**
    uv creates and manages the project virtualenv (`.venv/`) automatically. Use `uv run` to execute commands within the environment — it installs the correct Python and dependencies on first use.

    ```bash
    # Installs the project in editable mode along with the 'dev' dependency group
    uv sync
    ```

    To activate the environment for interactive use (e.g., running `python`, `pytest` directly):

    ```bash
    source .venv/bin/activate
    ```

3. **Configure API Keys:**
    Create a `.env` file from the example and add your API keys:

    ```bash
    cp .env.example .env
    # Edit .env and add your Anthropic and ElevenLabs keys
    ```

4. **Database Setup:**
    ArtificialU uses PostgreSQL. See the [PostgreSQL Setup Guide](docs/POSTGRES.md) for details on setting up the database container and initializing the schema.

### Lockfile & Reproducibility

Dependencies are pinned in `uv.lock` (committed to the repo), so every machine, CI run, and Docker build resolves identical versions. `uv sync` always installs from the lockfile; run `uv lock` after changing dependencies in `pyproject.toml`. See the [Development Environment Guide](docs/development.md#dependency-management-with-uv) for details.

### Development Environment Details

For a comprehensive guide on the development environment, including dependency management philosophy, code quality tools (linters, formatters, pre-commit hooks), and `pyproject.toml` usage, see [docs/development.md](docs/development.md).

### GitHub Codespaces

This repository is configured for [GitHub Codespaces](https://github.com/features/codespaces). Simply open a Codespace, add your API keys to `.env`, and use `uv run` as described above. The environment and database setup are handled automatically.

## Usage

The CLI interface, defined as a script in `pyproject.toml`, can be run using `uv run`:

```bash
# Example: Create a course
uv run artificial_u create-course -d "Computer Science" -t "Introduction to Artificial Intelligence" -c "CS4511"

# Example: Create audio for a lecture
uv run artificial_u create-audio -c "CS4511" -w 1 -n 1

# Example: List available courses
uv run artificial_u list-courses

# Example: Play a lecture (if available)
uv run artificial_u play-lecture -c "CS4511" -w 1 -n 1

# Example: Show lecture content
uv run artificial_u show-lecture -c "CS4511" -w 1 -n 1
```

For more details on any command, use the `--help` option:

```bash
uv run artificial_u --help
uv run artificial_u create-course --help
```

## Testing

The project uses pytest for testing. Tests are organized into several categories and can be run using `uv run`:

```bash
# Run all automated tests
uv run pytest

# Run specific test categories
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m e2e          # End-to-end tests only

# Run with coverage report
uv run pytest --cov=artificial_u
```

### Test Database Setup

Integration tests require a PostgreSQL test database. Ensure PostgreSQL is running and then set up the test database:

```bash
# Create the test database (run once)
uv run python scripts/setup_test_db.py

# Run integration tests
uv run pytest tests/integration -v
```

See the [PostgreSQL Setup Guide](docs/POSTGRES.md) for more database details.

## Project Structure

```txt
artificial_u/
├── __init__.py            # Package initialization
├── __main__.py            # Entry point for command-line execution
├── cli.py                 # CLI interface using Click
├── system.py              # Main system integration class
├── models/                # Data models and database (SQLAlchemy, Pydantic)
├── audio/                 # Audio processing (TTS, speech enhancement)
├── integrations/          # External API integrations (Anthropic, ElevenLabs)
├── services/              # Business logic layer
└── ... (other components)

docs/
├── development.md         # Development environment, tooling, dependencies
├── CONTRIBUTING.md        # Contribution guidelines and workflow
├── POSTGRES.md            # PostgreSQL setup details
└── ... (other docs)

tests/
├── unit/
├── integration/
└── e2e/

scripts/                   # Utility scripts (DB setup, etc.)

.env.example               # Example environment variables
.flake8                    # Flake8 configuration
.gitignore                 # Git ignore patterns
.pre-commit-config.yaml    # Pre-commit hook configuration
LICENSE                    # Project license
Makefile                   # Common development tasks and shortcuts
pyproject.toml             # Project metadata, dependencies, tool config
README.md                  # This file
uv.lock                    # Pinned dependency lockfile (managed by uv)
```

*(This is a simplified overview. See the respective directories for more detail.)*

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) for details on the development workflow, coding standards, and how to submit changes.

## Project Status

This project is in early development as a personal learning tool.

## License

[AGPL-3.0 License](LICENSE)
