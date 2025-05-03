# Development Environment & Tooling

This document details the development environment setup, dependency management strategy, code quality tools, and configuration files used in the ArtificialU project.

## Environment Setup & Dependency Management

This project uses [Hatch](https://hatch.pypa.io/latest/) for managing Python environments and project dependencies defined in `pyproject.toml`. Optionally, `pip-tools` can be used to generate lockfiles for pinning dependencies to ensure reproducible environments.

### Using Hatch (Recommended)

1. **Install Hatch:** Follow the instructions on the [Hatch website](https://hatch.pypa.io/latest/install/).
2. **Install Project & Dependencies:** Navigate to the project root directory and run:

    ```bash
    # Installs the project in editable mode along with 'dev' dependencies
    hatch run pip install -e ".[dev]"
    ```

3. **Activate Environment:** To work within the managed environment directly:

    ```bash
    hatch shell
    ```

    *(Within the hatch shell, you can run Python, pip, pytest, etc., directly)*

### Optional: Generating Lockfiles with pip-tools

For highly reproducible environments, especially for CI or specific deployment scenarios, you can generate pinned dependency lockfiles using `pip-tools` (which is included in the dev dependencies).

1. **Generate Lockfiles:**

    ```bash
    # Ensure you are in the hatch environment or use 'hatch run'
    # Generate requirements.txt for base dependencies
    pip-compile pyproject.toml --resolver=backtracking -o requirements.txt

    # Generate requirements-dev.txt for development dependencies
    pip-compile pyproject.toml --resolver=backtracking --extra dev -o requirements-dev.txt
    ```

2. **Sync Environment from Lockfiles:** If you have generated the lockfiles, you can synchronize your environment to match them exactly:

    ```bash
    # Sync using the development requirements file
    pip-sync requirements-dev.txt

    # Or, sync using only the base requirements file
    # pip-sync requirements.txt
    ```

    *Note: If using lockfiles, remember to regenerate them (step 1) and re-sync (step 2) whenever you modify dependencies in `pyproject.toml`. Commit the updated `pyproject.toml` and `requirements*.txt` files.*

### GitHub Codespaces

This repository includes a devcontainer configuration. GitHub Codespaces automatically sets up the environment using Hatch. Simply open the Codespace, add your API keys to `.env`, and use `hatch shell` or `hatch run`.

## pyproject.toml Configuration

The `pyproject.toml` file ([PEP 518](https://peps.python.org/pep-518/), [PEP 621](https://peps.python.org/pep-621/)) is the central configuration hub for:

- **Build System:** Defines `hatchling` as the build backend.
- **Project Metadata:** Contains name, version, description, dependencies, etc.
- **Tool Configurations:** Settings for `pytest`, `black`, `isort`, `mypy`, etc.

This standard approach simplifies configuration management and integrates well with modern Python tooling. Standard commands like `pip install -e .[dev]`, `pytest`, `black .`, `isort .`, `mypy artificial_u` work seamlessly, picking up their configuration from this file.

## Code Quality Tools

We use several tools to maintain code quality and consistency, configured in `pyproject.toml` and run via pre-commit hooks.

### 1. Black (Code Formatter)

Black ensures uncompromisingly consistent code formatting.

- **Usage:** `black .` (to format), `black --check .` (to check)
- **Configuration:** `[tool.black]` section in `pyproject.toml`.
- **VS Code:** Set `"python.formatting.provider": "black"` and `"editor.formatOnSave": true`.

### 2. isort (Import Sorter)

isort organizes imports alphabetically and into sections.

- **Usage:** `isort .` (to sort), `isort --check-only .` (to check)
- **Configuration:** `[tool.isort]` section in `pyproject.toml` (uses `black` profile).
- **VS Code:** Enable `"editor.codeActionsOnSave": { "source.organizeImports": true }`.

### 3. Flake8 (Linter)

Flake8 checks for PEP 8 style violations, logical errors (via PyFlakes), and complexity.

- **Usage:** `flake8` or `flake8 path/to/file.py`
- **Configuration:** `.flake8` file (compatible with Black formatting).
- **VS Code:** Set `"python.linting.flake8Enabled": true`.

### 4. Mypy (Type Checker)

Mypy checks static type hints to find potential type errors.

- **Usage:** `mypy artificial_u`
- **Configuration:** `[tool.mypy]` section in `pyproject.toml`.

### Pre-commit Hooks

Pre-commit hooks are configured in `.pre-commit-config.yaml` to automatically run Black, isort, Flake8, and Mypy before each commit.

1. **Install pre-commit:** `pip install pre-commit` (or `hatch run pip install pre-commit`)
2. **Install hooks:** `pre-commit install`

This ensures that code pushed to the repository adheres to the defined quality standards.
