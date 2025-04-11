#!/bin/bash
# Script to update dependency lockfiles

set -e # Exit on error

echo "Updating lockfiles for ArtificialU..."

# Make sure pip-tools is installed
pip install pip-tools

# Update production dependencies lockfile
echo "Generating requirements.lock..."
pip-compile --output-file=requirements.lock pyproject.toml

# Update development dependencies lockfile
echo "Generating requirements-dev.lock..."
pip-compile --extra=dev --output-file=requirements-dev.lock pyproject.toml

echo "Lockfiles updated successfully!"
echo ""
echo "To install dependencies using the updated lockfiles:"
echo "  - Production: pip install -r requirements.lock"
echo "  - Development: pip install -r requirements-dev.lock"
