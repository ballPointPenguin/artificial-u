# Contributing to ArtificialU

Thank you for considering contributing to ArtificialU! This document provides guidelines and instructions for contributing to the project.

## Getting Started

1. **Environment Setup**: Please follow the **Installation & Setup** instructions in the main [README.md](README.md) to set up your development environment using Hatch.
2. **Project Overview**: Familiarize yourself with the project's goals and structure described in the [README.md](README.md).
3. **Development Tooling**: Review the tools and practices outlined in the [Development Environment Guide](docs/development.md).

## Development Workflow

1. **Find an Issue**: Check the [Issues](https://github.com/ballPointPenguin/artificial-u/issues) for tasks, features, or bugs to work on. If you have a new idea, consider creating an issue first to discuss it.
2. **Create a Branch**: Create a new branch from `main` for your feature or bugfix:

    ```bash
    git checkout main
    git pull origin main
    git checkout -b feature/your-feature-name  # Or fix/your-bug-name
    ```

3. **Implement Changes**: Make your code changes, adhering to the guidelines below.
4. **Test**: Write or update tests as necessary. Run all tests to ensure your changes haven't introduced regressions. See the **Testing** section in the [README.md](README.md) for instructions on running tests.
5. **Commit**: Commit your changes with a clear and descriptive message following conventional commit standards (e.g., `feat: Add professor image generation`, `fix: Correct audio file path`).

    ```bash
    git add .
    git commit -m "feat: Describe your change concisely"
    ```

6. **Push**: Push your branch to your fork on GitHub:

    ```bash
    git push origin feature/your-feature-name
    ```

7. **Create a Pull Request**: Open a Pull Request (PR) against the `main` branch of the main repository. Provide a clear description of your changes in the PR.

## Coding Guidelines

- **Style**: Follow PEP 8 style guide for Python code. Adherence is enforced by Black and Flake8 via pre-commit hooks.
- **Type Hints**: Use type hints for function signatures and variables where appropriate. Mypy is used for type checking.
- **Docstrings**: Write clear docstrings for all public modules, classes, and functions using a standard format (e.g., Google style).
- **Simplicity**: Keep functions focused and strive for clear, readable code. Apply the principles outlined in the project's [Greenfield Development Guidelines](<#greenfield-development-guidelines>).
- **Commit Messages**: Write informative commit messages.

## Testing Guidelines

- Write unit tests for new functions and logic.
- Write integration tests for interactions between components or with external services/database.
- Ensure all tests pass before submitting a pull request (CI will also check this).
- See the [README.md](README.md#testing) for how to run tests.

## Documentation Guidelines

- Update documentation (README, docstrings, files in `docs/`) when adding or changing features.
- Document public APIs clearly.
- Keep usage instructions in the README up-to-date.

## Questions?

If you have any questions or need help, feel free to:

- Open an issue on GitHub.
- Comment on an existing issue or pull request.

Thank you for contributing to ArtificialU!
