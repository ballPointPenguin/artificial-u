# Dependency Management for ArtificialU

This document explains the dependency management approach used in the ArtificialU project.

## Overview

The project uses a hybrid approach for managing dependencies:

1. **pyproject.toml** - Central configuration file for project metadata and dependencies
2. **pip-tools** - Used to generate lockfiles for reproducible environments
3. **hatchling** - Build backend for the project

This approach provides a balance between modern Python packaging standards and reproducible builds.

## Key Components

### 1. pyproject.toml

The `pyproject.toml` file is the central configuration file that:

- Defines project metadata and dependencies
- Configures the build system (hatchling)
- Separates production dependencies from development dependencies
- Contains tool-specific configurations (pytest, black, isort, etc.)

### 2. Lockfiles

Two lockfiles are generated from the pyproject.toml file:

- `requirements.lock` - Contains pinned versions of all production dependencies
- `requirements-dev.lock` - Contains pinned versions of all development dependencies (including production dependencies)

These lockfiles ensure reproducible environments across different systems.

## Installation Workflows

For development:

```bash
# Install with exact versions (recommended for reproducibility)
pip install -r requirements-dev.lock

# Or install using pyproject.toml (latest compatible versions)
pip install -e ".[dev]"
```

For production:

```bash
# Install with exact versions (recommended for reproducibility)
pip install -r requirements.lock

# Or install using pyproject.toml (latest compatible versions)
pip install -e .
```

## Updating Dependencies

When you need to add or update dependencies:

1. Update the dependencies in `pyproject.toml`
2. Regenerate the lockfiles:

   ```bash
   # Regenerate production lockfile
   pip-compile --output-file=requirements.lock pyproject.toml
   
   # Regenerate development lockfile
   pip-compile --extra=dev --output-file=requirements-dev.lock pyproject.toml
   ```

3. Commit both the updated `pyproject.toml` and lockfiles

## Benefits of This Approach

- **Standards-compliant**: Uses the standard pyproject.toml format
- **Reproducible**: Lockfiles ensure consistent environments
- **Minimal workflow changes**: Easy to integrate with existing tools
- **Clear separation**: Development vs. production dependencies are clearly separated
- **Flexible**: Supports both exact pinned versions and compatible version ranges

## Future Considerations

- Integration with CI/CD pipelines for dependency validation
- Automating dependency updates with tools like Dependabot
- Potential migration to Poetry if more advanced capabilities are needed
