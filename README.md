# ArtificialU

An AI-powered educational content platform that generates university lectures with distinct professor personalities, converting them to audio for an immersive learning experience.

## Project Overview

ArtificialU combines the Anthropic Claude API for generating educational content with the ElevenLabs API for text-to-speech conversion. The system creates virtual professors with unique personalities, teaching styles, and backgrounds who deliver engaging lectures across various academic disciplines.

## Key Features

- **Course Generation**: Create full academic courses with syllabi and lecture content
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

## Installation

1. Clone the repository:

```bash
git clone https://github.com/ballPointPenguin/artificial-u.git
cd artificial-u
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\\Scripts\\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env file to add your API keys
```

## Quick Start

Run the sample demonstration (no API keys required):

```bash
python sample_tinyllama.py
```

Or, using Anthropic API:

```bash
python sample_anthropic.py
```

This will simulate the creation of a professor, course, lecture, and audio file to demonstrate the system's capabilities.

## Usage

The CLI interface provides commands for interacting with the system:

### Enable Prompt Caching

You can enable Anthropic's prompt caching feature to reduce token usage and maintain consistent professor personalities across lectures:

```bash
./cli.py generate-lecture -c "CS4511" -w 1 -n 1 -t "What is AI?" --enable-caching
```

This feature caches professor profiles and course information, so subsequent lectures by the same professor will maintain a consistent voice and teaching style while potentially reducing API costs by 70-90% for large cached components.

### Create a course

```bash
./cli.py create-course -d "Computer Science" -t "Introduction to Artificial Intelligence" -c "CS4511"
```

### Generate a lecture

```bash
./cli.py generate-lecture -c "CS4511" -w 1 -n 1 -t "What is AI? History and Intelligent Agents"
```

### Create audio for a lecture

```bash
./cli.py create-audio -c "CS4511" -w 1 -n 1
```

### List available courses

```bash
./cli.py list-courses
```

### View course syllabus

```bash
./cli.py show-syllabus -c "CS4511"
```

### Play a lecture (if available)

```bash
./cli.py play-lecture -c "CS4511" -w 1 -n 1
```

You can also display a lecture's content:

```bash
./cli.py show-lecture -c "CS4511" -w 1 -n 1
```

For more details on any command, use the --help option:

```bash
./cli.py --help
./cli.py create-course --help
```

## Testing

The project uses pytest for testing. Tests are organized into several categories:

```bash
# Run all automated tests (excluding manual API tests)
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # End-to-end tests only

# Run with coverage report
pytest --cov=artificial_u

# Run manual API integration tests (requires API keys)
ELEVENLABS_API_KEY=<your_api_key> pytest tests/manual/test_api_integration.py -v
```

### Setting Up the Test Database

Before running integration tests, you need to set up the PostgreSQL test database:

1. Make sure PostgreSQL is running
2. Run the setup script:

```bash
# Create the test database
python scripts/setup_test_db.py

# Run integration tests
pytest tests/integration -v
```

For manual API tests, make sure to:

1. Pass any required API keys as environment variables to pytest
2. Never commit API keys to version control
3. Run manual tests separately from automated test suite

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

This repository includes a devcontainer configuration for easy development using GitHub Codespaces:

1. Click the "Code" button on the repository
2. Select the "Codespaces" tab
3. Click "Create codespace on main"
4. Once the environment is ready, add your API keys to the `.env` file
5. Start developing!

## Recent Updates

- Fixed lecture preview functionality to include `audio_path` references
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

2. Initialize the database schema:

   ```bash
   python initialize_db.py
   ```

3. For detailed database information, see [PostgreSQL Setup Guide](docs/POSTGRES.md).
