# Contributing to ArtificialU

Thank you for considering contributing to ArtificialU! This document provides guidelines and instructions for contributing to the project.

## Development Environment

### Prerequisites

- Python 3.9+
- Anthropic API key
- ElevenLabs API key

### Setting Up Your Environment

1. Clone the repository:

```bash
git clone https://github.com/ballPointPenguin/artificial-u.git
cd artificial-u
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy the example environment file and add your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### Using GitHub Codespaces

This project is configured for GitHub Codespaces, which provides a complete development environment in the cloud:

1. Click the "Code" button on the repository
2. Select the "Codespaces" tab
3. Click "Create codespace on main"
4. Once the environment is ready, add your API keys to the `.env` file

## Project Structure

```
artificial_u/
├── __init__.py            # Package initialization
├── __main__.py            # Entry point for command-line execution
├── system.py              # Main system integration class
├── models/                # Data models and database
├── generators/            # Content generation
├── audio/                 # Audio processing
└── cli/                   # Command-line interface
```

## Development Workflow

1. Check the [Issues](https://github.com/ballPointPenguin/artificial-u/issues) for tasks to work on
2. Create a new branch for your feature or bugfix:

```bash
git checkout -b feature/your-feature-name
```

3. Make your changes
4. Write or update tests if applicable
5. Run tests before committing:

```bash
# Tests will be added in the future
```

6. Commit your changes with a descriptive message:

```bash
git commit -m "Add feature: description of your feature"
```

7. Push your branch to GitHub:

```bash
git push origin feature/your-feature-name
```

8. Create a Pull Request on GitHub

## Coding Guidelines

- Follow PEP 8 style guide for Python code
- Use docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Write clear commit messages
- Keep functions focused on a single responsibility

## Testing

- Write tests for all new functionality
- Run tests before submitting a pull request
- Ensure all tests pass before merging

## Documentation

- Update documentation when adding or changing features
- Document all public API methods with examples
- Keep README updated with current installation and usage instructions

## Working with APIs

### Anthropic Claude API

- Use the ContentGenerator class for all interactions with the Claude API
- Be mindful of token usage to manage costs
- Implement caching where appropriate

### ElevenLabs API

- Use the AudioProcessor class for all interactions with the ElevenLabs API
- Be mindful of character limits and costs
- Cache audio files to avoid regenerating the same content

## Questions?

If you have any questions or need help, feel free to:

- Open an issue
- Comment on an existing issue
- Contact the project maintainer

Thank you for contributing to ArtificialU!
