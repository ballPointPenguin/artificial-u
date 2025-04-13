# Code Quality Tools

## Flake8

Flake8 is a code linting tool for Python that combines PyFlakes, pycodestyle, and McCabe complexity checker. It helps enforce PEP 8 style guidelines and detect programming errors.

### Installation

Flake8 is included in the development dependencies. To install it, run:

```bash
pip install -e ".[dev]"
```

### Usage

To run Flake8 on the entire codebase:

```bash
flake8
```

To run Flake8 on a specific file or directory:

```bash
flake8 path/to/file.py
flake8 path/to/directory/
```

### Configuration

Flake8 is configured in the `.flake8` file at the root of the project. The configuration includes:

- Maximum line length of 88 characters (compatible with Black)
- Ignoring E203 and W503 (recommended when using Black)
- Maximum complexity limit of 10
- Special handling for `__init__.py` files (allowing unused imports)
- Excluded directories (e.g., `.git`, `__pycache__`, `build`, etc.)

### Common Error Codes

- E### / W###: PEP 8 style violations
  - E501: Line too long
  - E402: Module level import not at top of file
  - W293: Blank line contains whitespace
- F###: PyFlakes errors
  - F401: Import not used
  - F811: Redefinition of unused name
  - F841: Local variable is assigned to but never used
- C###: McCabe complexity errors
  - C901: Function is too complex

### Fixing Issues

To automatically fix some common issues:

1. Consider using [autopep8](https://github.com/hhatto/autopep8) or [black](https://github.com/psf/black) for formatting
2. Review and remove unused imports
3. Refactor complex functions (those with C901 errors) into smaller, more manageable functions

### Integration with VS Code

To integrate Flake8 with VS Code, install the Python extension and add these settings to your `.vscode/settings.json`:

```json
{
    "python.linting.flake8Enabled": true,
    "python.linting.enabled": true
}
```

## Black

Black is an uncompromising Python code formatter. It automatically formats your code to follow a consistent style, eliminating debates about code formatting during code reviews.

### Installation

Black is included in the development dependencies. To install it, run:

```bash
pip install -e ".[dev]"
```

### Usage

To format all Python files in the project:

```bash
black .
```

To check if files are formatted without modifying them:

```bash
black --check .
```

To format specific files:

```bash
black path/to/file.py
```

### Configuration

Black is configured in the `pyproject.toml` file. The configuration includes:

- Line length of 88 characters (the Black default)
- Target Python version of 3.9
- Exclusion patterns for directories that should not be formatted

### Integration with VS Code

To integrate Black with VS Code, install the Python extension and add these settings to your `.vscode/settings.json`:

```json
{
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

## isort

isort is a utility that automatically sorts Python imports alphabetically, and automatically separates them into sections and by type. It ensures consistent import organization across the codebase.

### Installation

isort is included in the development dependencies. To install it, run:

```bash
pip install -e ".[dev]"
```

### Usage

To sort imports in all Python files:

```bash
isort .
```

To check if imports are properly sorted without modifying files:

```bash
isort --check-only .
```

To apply isort to a specific file:

```bash
isort path/to/file.py
```

To show what changes would be made without modifying files:

```bash
isort --diff .
```

### Configuration

isort is configured in the `pyproject.toml` file. The configuration includes:

- Black compatibility profile
- Line length matching Black's configuration (88 characters)
- Appropriate import sections and ordering
- Exclusion patterns for directories that should not be processed

### Integration with VS Code

VS Code integration is handled through the `.vscode/settings.json` file with the following setting:

```json
{
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

## Pre-commit Hooks

We've set up pre-commit hooks to run Flake8, Black, and isort before committing changes. This ensures that code quality and formatting are maintained throughout the development process.

To use the pre-commit hooks:

1. Install pre-commit:

   ```bash
   pip install pre-commit
   ```

2. Install the git hooks:

   ```bash
   pre-commit install
   ```

Now, when you commit changes, all tools will run automatically.

## Implementation Status

The following tasks have been completed:

- [x] Choose Flake8 as the linting tool (issue #45)
- [x] Create configuration file (.flake8) with appropriate rules
- [x] Configure to work with our existing code structure
- [x] Add to development dependencies in pyproject.toml
- [x] Create basic documentation
- [x] Configure VSCode integration
- [x] Set up pre-commit hooks
- [x] Add Black for code formatting (issue #46)
- [x] Add isort for import organization (issue #47)

The codebase currently has numerous style issues that need to be addressed. The tooling is now in place to help enforce consistent style going forward.
