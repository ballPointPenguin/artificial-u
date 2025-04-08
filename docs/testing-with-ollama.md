# Testing with Ollama

This document explains how to use [Ollama](https://ollama.com) for local testing of the ArtificialU system without requiring an Anthropic API key.

## Overview

ArtificialU uses LLMs (Large Language Models) to generate academic content. In production, it uses Anthropic's Claude models, but for testing and development, you can use Ollama with smaller local models like TinyLlama.

Benefits of using Ollama for testing:

- No API key or costs
- Faster iteration during development
- Completely offline testing
- Smaller models are sufficient for testing logic

## Prerequisites

1. Install Ollama from [ollama.com](https://ollama.com)
2. Pull a small model like TinyLlama:

   ```bash
   ollama pull tinyllama
   ```

3. Install the required Python packages:

   ```bash
   pip install -e .[dev]
   ```

## Using Ollama in Code

### Direct Usage

You can create a ContentGenerator that uses Ollama directly:

```python
from artificial_u.generators.factory import create_ollama_generator

# Create a generator with TinyLlama
generator = create_ollama_generator(model="tinyllama")

# Use it like any other ContentGenerator
professor = generator.create_professor(
    department="Computer Science",
    specialization="AI"
)
```

### Using the Factory

You can also use the factory function to create a generator with any backend:

```python
from artificial_u.generators.factory import create_generator

# Create with Ollama
generator = create_generator(backend="ollama", model="tinyllama")

# Or with Anthropic (requires API key)
generator = create_generator(backend="anthropic", api_key="YOUR_API_KEY")
```

### Using with UniversitySystem

You can configure the UniversitySystem to use Ollama:

```python
from artificial_u.system import UniversitySystem

system = UniversitySystem(
    content_backend="ollama",
    content_model="tinyllama",
    # Other parameters...
)

# Use the system as usual
professor = system.create_professor(...)
```

## Running Tests

The integration tests are designed to automatically detect if Ollama is installed and running. If not, they will be skipped.

To run the tests:

```bash
pytest tests/test_ollama_generator.py -v
pytest tests/test_generator_factory.py -v
pytest tests/test_system_integration.py -v
```

## Available Models

Ollama supports many models. For testing, we recommend smaller models like:

- TinyLlama (1.1B parameters)
- Mistral (7B parameters)
- Phi-2 (2.7B parameters)

View available models at [ollama.com/library](https://ollama.com/library).

## Troubleshooting

### Ollama Not Running

If you see test failures with messages about Ollama not running, check if the Ollama service is running:

```bash
ollama list
```

If that fails, start the service according to your OS.

### Missing Models

If tests fail because a model is missing, download it with:

```bash
ollama pull tinyllama
```

### Performance

If the tests are slow, consider using an even smaller model. TinyLlama is already very small at 1.1B parameters.
