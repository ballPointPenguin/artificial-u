# ArtificialU

An AI-powered educational content platform that generates university lectures with distinct professor personalities, converting them to audio for an immersive learning experience.

## Project Overview

ArtificialU combines the Anthropic Claude API for generating educational content with the ElevenLabs API for text-to-speech conversion. The system creates virtual professors with unique personalities, teaching styles, and backgrounds who deliver engaging lectures across various academic disciplines.

## Key Features

- Course and lecture generation with consistent professor personas
- Text-to-speech conversion with appropriate voices for each professor
- Local storage of course materials and audio files
- CLI interface for browsing and playing content
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

Run the sample demonstration:

```bash
python sample.py
```

This will simulate the creation of a professor, course, lecture, and audio file to demonstrate the system's capabilities.

## Usage

The CLI interface provides commands for interacting with the system:

### Create a course

```bash
python -m artificial_u create-course -d \"Computer Science\" -t \"Introduction to Artificial Intelligence\" -c \"CS4511\"
```

### Generate a lecture

```bash
python -m artificial_u generate-lecture -c \"CS4511\" -w 1 -n 1 -t \"What is AI? History and Intelligent Agents\"
```

### Create audio for a lecture

```bash
python -m artificial_u create-audio -c \"CS4511\" -w 1 -n 1
```

### List available courses

```bash
python -m artificial_u list-courses
```

### View course syllabus

```bash
python -m artificial_u show-syllabus -c \"CS4511\"
```

### Play a lecture (if available)

```bash
python -m artificial_u play-lecture -c \"CS4511\" -w 1 -n 1
```

## Project Structure

```
artificial_u/
├── __init__.py            # Package initialization
├── __main__.py            # Entry point for command-line execution
├── system.py              # Main system integration class
├── models/                # Data models and database
│   ├── __init__.py
│   ├── core.py            # Core data models using Pydantic
│   └── database.py        # SQLAlchemy models and repository
├── generators/            # Content generation
│   ├── __init__.py
│   └── content.py         # Claude API integration for content
├── audio/                 # Audio processing
│   ├── __init__.py
│   └── processor.py       # ElevenLabs API integration
└── cli/                   # Command-line interface
    ├── __init__.py
    └── app.py             # CLI commands using Click
```

## Development with GitHub Codespaces

This repository includes a devcontainer configuration for easy development using GitHub Codespaces:

1. Click the \"Code\" button on the repository
2. Select the \"Codespaces\" tab
3. Click \"Create codespace on main\"
4. Once the environment is ready, add your API keys to the `.env` file
5. Start developing!

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
