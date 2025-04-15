#!/bin/sh
set -e

# Start the Ollama server in the background
ollama serve &

sleep 10 # Wait for server to start

# Pull the required model(s)
ollama pull tinyllama
ollama pull phi4-mini

# Force model load
ollama run phi4-mini "Hello"

# Bring Ollama server to foreground (if needed)
wait
