# pyproject.toml Configuration

This document explains the purpose and usage of the `pyproject.toml` file in the ArtificialU project.

## Overview

The `pyproject.toml` file is a standardized configuration file for Python projects defined by [PEP 518](https://peps.python.org/pep-518/) and [PEP 621](https://peps.python.org/pep-621/). It centralizes project metadata, build configuration, and tool-specific settings in a single file, replacing multiple configuration files like `setup.py`, `setup.cfg`, `.pylintrc`, etc.

## Key Benefits

- **Centralized Configuration**: Single file for project metadata and tool configurations
- **Modern Standard**: Aligns with current Python packaging best practices
- **Tool Integration**: Better integration with modern Python tooling
- **Simpler Maintenance**: Easier to manage than multiple configuration files

## File Structure

Our `pyproject.toml` is organized into these main sections:

### 1. Build System Configuration

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

This section defines how the package is built and what dependencies are needed for building. We use `hatchling`, a modern, extensible build backend.

### 2. Project Metadata

```toml
[project]
name = "artificial-u"
version = "0.1.0"
description = "AI-powered educational content platform"
# ... additional metadata
```

This section contains basic information about the project, including its name, version, dependencies, and other metadata used when the package is published.

### 3. Tool-specific Configurations

Various sections like `[tool.pytest.ini_options]`, `[tool.black]`, `[tool.isort]`, etc., configure specific development tools.

## Using with Standard Python Tooling

### Installing the Project in Development Mode

```bash
pip install -e .
```

This installs the project in development mode, allowing you to make changes without reinstalling.

### Installing Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs both the project and its development dependencies.

### Running Tests

```bash
pytest
```

The test configuration is automatically picked up from the `[tool.pytest.ini_options]` section.

### Formatting Code

```bash
black .
isort .
```

These tools will use the configurations in the respective sections.

### Type Checking

```bash
mypy artificial_u
```

## Compatibility with Existing Workflows

The `pyproject.toml` file works alongside existing configuration files in the repository (like `pytest.ini` and `.pylintrc`). Over time, these can be migrated fully to `pyproject.toml`.

## Future Considerations

- Eventually, this file can replace `setup.py` for packaging
- Additional linters and code quality tools can be configured here
- As the project grows, dependencies can be better organized in this structure

## References

- [PEP 518 – Specifying Minimum Build System Requirements for Python Projects](https://peps.python.org/pep-518/)
- [PEP 621 – Storing project metadata in pyproject.toml](https://peps.python.org/pep-621/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
