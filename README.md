# ArtificialU

An AI-powered educational content platform that generates university lectures with distinct professor personalities, converting them to audio for an immersive learning experience.

## Project Overview

ArtificialU combines the Anthropic Claude API for generating educational content with the ElevenLabs API for text-to-speech conversion. The system creates virtual professors with unique personalities, teaching styles, and backgrounds who deliver engaging lectures across various academic disciplines.

## Key Features

- **Course Generation**: Create full academic courses with topics and lecture content
- **Professor Profiles**: Generate diverse, detailed professor personas
- **Text-to-Speech**: Convert lecture content to audio using ElevenLabs voices
- **Smart Voice Selection**: Automatically match professors to appropriate ElevenLabs voices based on gender, nationality, accent, and age
- **CLI Interface**: Easy-to-use command line interface for generating content
- Course and lecture generation with consistent professor personas
- Text-to-speech conversion with appropriate voices for each professor
- Prompt caching for more efficient API usage and consistent personalities
- Direct access to audio file paths in lecture previews
- Local storage of course materials and audio files
- Faculty directory with professor information

## Prerequisites

- Python 3.9+
- Anthropic API key
- ElevenLabs API key
- [Hatch](https://hatch.pypa.io/latest/) (for environment management)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ballPointPenguin/artificial-u.git
cd artificial-u
```

2. Install dependencies using Hatch:

   Hatch automatically manages project environments. To install the project and its dependencies, use the `hatch run` command:

   ```bash
   # Installs the project in editable mode along with 'dev' dependencies
   hatch run pip install -e ".[dev]"
   ```

   To activate the project's managed environment for interactive use (e.g., running commands directly):

   ```bash
   hatch shell
   ```

   *(Within the hatch shell, you can run commands like `pip`, `python`, etc., without `hatch run`)*

3. Generate pinned requirements files (optional but recommended for reproducible environments):

   ```bash
   # Generate requirements.txt for base dependencies
   hatch run pip-compile pyproject.toml --resolver=backtracking -o requirements.txt

   # Generate requirements-dev.txt for development dependencies
   hatch run pip-compile pyproject.toml --resolver=backtracking --extra dev -o requirements-dev.txt
   ```

4. Sync your environment using the generated files:

   If you generated the requirements files, you can ensure your environment matches them exactly using `pip-sync` via `hatch run`:

   ```bash
   # Sync using the development requirements file
   hatch run pip-sync requirements-dev.txt

   # Or, sync using only the base requirements file
   # hatch run pip-sync requirements.txt
   ```

   *Note: Anytime you add/remove dependencies in `pyproject.toml`, regenerate the requirements files (step 3) and re-sync your environment (step 4). Commit the changes to `pyproject.toml` and the generated `requirements*.txt` files.*

5. Create a `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env file to add your API keys
```

## Project Configuration

The project uses a modern `pyproject.toml` file for configuration, following PEP 518 and PEP 621 standards. This file centralizes build settings, project metadata, and tool configurations. See [docs/pyproject_usage.md](docs/pyproject_usage.md) for details.

## Dependency Management

The project uses `pyproject.toml` for defining dependencies and [Hatch](https://hatch.pypa.io/latest/) for environment management. Optionally, `pip-tools` can be used to generate lockfiles (`requirements*.txt`) for pinning dependencies and ensuring reproducible environments. See [docs/dependency_management.md](docs/dependency_management.md) for more details on the approach and workflows.

## Quick Start

Run the sample demonstrations within the hatch environment:

```bash
# Activate the environment (if not already active)
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

This will simulate the creation of a professor, course, lecture, and audio file to demonstrate the system's capabilities.

## Usage

The CLI interface, defined as a script in `pyproject.toml`, can be run using `hatch run`:

```bash
# Example: Create a course
hatch run artificial-u create-course -d "Computer Science" -t "Introduction to Artificial Intelligence" -c "CS4511"

# Example: Generate a lecture with caching
hatch run artificial-u generate-lecture -c "CS4511" -w 1 -n 1 -t "What is AI?" --enable-caching

# Example: Create audio for a lecture
hatch run artificial-u create-audio -c "CS4511" -w 1 -n 1

# Example: List available courses
hatch run artificial-u list-courses

# Example: Play a lecture (if available)
hatch run artificial-u play-lecture -c "CS4511" -w 1 -n 1

# Example: Show lecture content
hatch run artificial-u show-lecture -c "CS4511" -w 1 -n 1
```

For more details on any command, use the --help option:

```bash
hatch run artificial-u --help
hatch run artificial-u create-course --help
```

## Testing

The project uses pytest for testing. Tests are organized into several categories:

```bash
# Run all automated tests (uses the hatch environment)
pytest

# Or explicitly using hatch run
hatch run pytest

# Run specific test categories
hatch run pytest -m unit          # Unit tests only
hatch run pytest -m integration   # Integration tests only
hatch run pytest -m e2e          # End-to-end tests only

# Run with coverage report
hatch run pytest --cov=artificial_u
```

### Setting Up the Test Database

Before running integration tests, you need to set up the PostgreSQL test database:

1. Make sure PostgreSQL is running
2. Run the setup script:

```bash
# Create the test database
hatch run python scripts/setup_test_db.py

# Run integration tests
hatch run pytest tests/integration -v
```

## Project Structure

```txt
artificial_u/
├── __init__.py            # Package initialization
├── __main__.py            # Entry point for command-line execution
├── cli.py                 # CLI interface using Click
├── system.py              # Main system integration class - includes lecture preview functionality
├── models/                # Data models and database
│   ├── __init__.py
│   ├── core.py            # Core data models using Pydantic
│   └── database.py        # SQLAlchemy models and repository
├── generators/            # Content generation
│   ├── __init__.py
│   └── content.py         # Claude API integration for content
└── audio/                 # Audio processing
    ├── __init__.py
    └── processor.py       # ElevenLabs API integration
```

## Development with GitHub Codespaces

This repository includes a devcontainer configuration for easy development using GitHub Codespaces. Hatch is typically pre-installed or easily installable in these environments.

1. Click the "Code" button on the repository
2. Select the "Codespaces" tab
3. Click "Create codespace on main"
4. Once the environment is ready, add your API keys to the `.env` file
5. Use `hatch shell` or `hatch run` as described in the Installation/Usage sections.

## Recent Updates

- Streamlined CLI interface for audio playback
- Improved error handling for missing audio files

## Future Enhancements

- Web interface with Flask/FastAPI
- Faculty visualization using AI-generated images
- Interactive Q&A with professors
- Homework generation and assessment
- Improved voice customization for professors

## Project Status

This project is in early development as a personal learning tool.

## License

[AGPL-3.0 License](LICENSE)

## Database Setup

ArtificialU uses PostgreSQL for data storage:

1. Start the PostgreSQL container:

   ```bash
   docker-compose up -d
   ```

2. Initialize the database schema using Hatch:

   ```bash
   hatch run python initialize_db.py
   ```

3. For detailed database information, see [PostgreSQL Setup Guide](docs/POSTGRES.md).
