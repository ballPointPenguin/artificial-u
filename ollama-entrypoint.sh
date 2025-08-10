#!/bin/sh
set -e

# Start the Ollama server in the background
ollama serve &

sleep 10 # Wait for server to start

# Pull the required model(s)
######      MODEL             SIZE   CONTEXT
ollama pull qwen3:0.6b      # 523MB, 40K
ollama pull llama3.2:1b     # 1.3GB, 128K
ollama pull smollm2:1.7b    # 1.8GB, 8K
ollama pull phi4-mini:3.8b  # 2.5GB, 128K
ollama pull qwen3:4b        # 2.5GB, 256K
ollama pull gemma3:4b       # 3.3GB, 128K
ollama pull mistral:7b      # 4.4GB, 32K

# Force model load
ollama run qwen3:0.6b "Hello"

# Bring Ollama server to foreground (if needed)
wait
