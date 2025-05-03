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
- **CLI Interface**: Easy-to-use command line interface for generating content
- Course and lecture generation with consistent professor personas
- Direct access to audio file paths in lecture previews
- Local storage of course materials and audio files
- Faculty directory with professor information

## Prerequisites

- Python 3.13+
- Anthropic API key
- ElevenLabs API key
- [Hatch](https://hatch.pypa.io/latest/) (for environment management)

## Installation & Setup

This project uses [Hatch](https://hatch.pypa.io/latest/) for managing Python environments and dependencies.

1. **Clone the repository:**

    ```bash
    git clone https://github.com/ballPointPenguin/artificial-u.git
    cd artificial-u
    ```

2. **Install Project & Dependencies:**
    Hatch automatically manages project environments. Use `hatch run` to execute commands within the managed environment.

    ```bash
    # Installs the project in editable mode along with 'dev' dependencies
    hatch run pip install -e ".[dev]"
    ```

    To activate the environment for interactive use (e.g., running `python`, `pip`, `pytest` directly):

    ```bash
    hatch shell
    ```

3. **Configure API Keys:**
    Create a `.env` file from the example and add your API keys:

    ```bash
    cp .env.example .env
    # Edit .env and add your Anthropic and ElevenLabs keys
    ```

4. **Database Setup:**
    ArtificialU uses PostgreSQL. See the [PostgreSQL Setup Guide](docs/POSTGRES.md) for details on setting up the database container and initializing the schema.

### Optional: Lockfiles for Reproducibility

For ensuring identical environments across different machines or CI/CD, you can generate pinned `requirements.txt` files using `pip-tools`. See the [Development Environment Guide](docs/development.md#optional-generating-lockfiles-with-pip-tools) for details.

### Development Environment Details

For a comprehensive guide on the development environment, including dependency management philosophy, code quality tools (linters, formatters, pre-commit hooks), and `pyproject.toml` usage, see [docs/development.md](docs/development.md).

### GitHub Codespaces

This repository is configured for [GitHub Codespaces](https://github.com/features/codespaces). Simply open a Codespace, add your API keys to `.env`, and use `hatch run` or `hatch shell` as described above. The environment and database setup are handled automatically.

## Quick Start

Run the sample demonstrations within the hatch environment:

```bash
# Activate the environment first (if not already active)
# hatch shell

# Then run the scripts
python sample_tinyllama.py
python sample_anthropic.py
```

Or directly using `hatch run`:

```bash
hatch run python sample_tinyllama.py
hatch run python sample_anthropic.py
```

This will simulate the creation of a professor, course, lecture, and audio file.

## Usage

The CLI interface, defined as a script in `pyproject.toml`, can be run using `hatch run`:

```bash
# Example: Create a course
hatch run artificial-u create-course -d "Computer Science" -t "Introduction to Artificial Intelligence" -c "CS4511"

# Example: Create audio for a lecture
hatch run artificial-u create-audio -c "CS4511" -w 1 -n 1

# Example: List available courses
hatch run artificial-u list-courses

# Example: Play a lecture (if available)
hatch run artificial-u play-lecture -c "CS4511" -w 1 -n 1

# Example: Show lecture content
hatch run artificial-u show-lecture -c "CS4511" -w 1 -n 1
```

For more details on any command, use the `--help` option:

```bash
hatch run artificial-u --help
hatch run artificial-u create-course --help
```

## Testing

The project uses pytest for testing. Tests are organized into several categories and can be run using `hatch run`:

```bash
# Run all automated tests
hatch run pytest

# Run specific test categories
hatch run pytest -m unit          # Unit tests only
hatch run pytest -m integration   # Integration tests only
hatch run pytest -m e2e          # End-to-end tests only

# Run with coverage report
hatch run pytest --cov=artificial_u
```

### Test Database Setup

Integration tests require a PostgreSQL test database. Ensure PostgreSQL is running and then set up the test database:

```bash
# Create the test database (run once)
hatch run python scripts/setup_test_db.py

# Run integration tests
hatch run pytest tests/integration -v
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
Makefile                   # Optional: Common development tasks
pyproject.toml             # Project metadata, dependencies, tool config
README.md                  # This file
requirements.txt           # Optional: Pinned production dependencies
requirements-dev.txt       # Optional: Pinned development dependencies
```

*(This is a simplified overview. See the respective directories for more detail.)*

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) for details on the development workflow, coding standards, and how to submit changes.

## Project Status

This project is in early development as a personal learning tool.

## License

[AGPL-3.0 License](LICENSE)
