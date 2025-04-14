import logging

import ollama

from artificial_u.config import get_settings

# Get settings for Ollama configuration
settings = get_settings()
ollama_host = getattr(settings, "OLLAMA_HOST", "http://localhost:11434")

# Set up logger
logger = logging.getLogger(__name__)
logger.info(f"Initializing Ollama client with host: {ollama_host}")

# Initialize the client with the configured host
client = ollama.AsyncClient(host=ollama_host)
