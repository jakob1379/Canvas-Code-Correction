# Contributing to Canvas Code Correction

Thank you for your interest in contributing to CCC! This project is open source and welcomes contributions.

## Development Setup

1. Fork the repository.
2. Clone your fork locally.
3. Install dependencies with `uv sync`.
4. Run tests with `uv run pytest`.
5. Make your changes and ensure tests pass.

## Code Style

- Follow [PEP 8](https://pep8.org/) for Python code.
- Use type hints where possible.
- Write docstrings for public functions.
- Use `black` for formatting (configured in `pyproject.toml`).
- Use `ruff` for linting.

## Testing

- Write unit tests for new functionality.
- Integration tests are in `tests/integration/` and require Docker and RustFS.
- Run all tests with `uv run pytest`.
- Run integration tests with `uv run pytest -m integration`.

## Documentation

- Update documentation in `docs/` as needed.
- Uses Zensical with Material theme.
- Build docs locally with `uv run poe serve-docs`.

## Pull Request Process

1. Create a branch for your feature/fix.
2. Commit changes with descriptive messages.
3. Push to your fork.
4. Open a pull request against the main branch.
5. Ensure CI passes and address any review comments.

## Code of Conduct

Be respectful and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).