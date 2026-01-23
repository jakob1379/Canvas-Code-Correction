# Contribute to Canvas Code Correction in 5 Minutes

Welcome to Canvas Code Correction (CCC). This guide walks you through the
fastest way to make your first contribution—whether you’re fixing a bug, adding
a feature, or improving documentation. Follow the steps below and you’ll have a
pull request ready in minutes.

## Quick Start: Your First Contribution

### 1. Fork and Clone

**Fork** the repository on GitHub, then **clone** your fork to your local
machine:

```bash
$ git clone https://github.com/YOUR_USERNAME/Canvas-Code-Correction.git
$ cd Canvas-Code-Correction
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Install Dependencies

CCC uses **uv** for dependency management. Install the project and its
development tools with:

```bash
$ uv sync
```

Expected output (truncated):

```
✔ Synced environment in 0.5s
✔ Installed 42 packages
✔ All dependencies are satisfied
```

### 3. Run the Tests

Verify everything works before you make changes:

```bash
$ pytest
```

You should see something like:

```
========================== test session starts ==========================
platform linux — Python 3.13.0, pytest‑8.3.4, pluggy‑1.5.0
rootdir: /home/jsg/Documents/jsg/Canvas‑Code‑Correction
collected 127 items

tests/unit/test_core.py ...................................... [ 25%]
tests/unit/test_parser.py ..................................... [ 50%]
tests/unit/test_utils.py ...................................... [ 75%]
tests/integration/test_integration.py ........................ [100%]

=========================== 127 passed in 3.2s ==========================
```

If any test fails, check the [Troubleshooting](#troubleshooting) section.

### 4. Make Your Changes

Pick one of the common workflows below.

#### Fixing a Bug

1. **Find the bug** – check the issue tracker or run the failing test.
2. **Edit the relevant file** – locate the function or module that needs fixing.
3. **Write a test** (optional but recommended) – add a minimal test that
   reproduces the bug, then verify your fix makes it pass.

Example: fixing a typo in `src/ccc/core.py`:

```python
# Before
def greet(user: str) -> str:
    return f"Helo, {user}!"

# After
def greet(user: str) -> str:
    return f"Hello, {user}!"
```

Run the tests again to ensure nothing broke:

```bash
$ pytest tests/unit/test_core.py
```

#### Adding a Feature

1. **Create a new branch** for your feature:

   ```bash
   $ git switch -c feat/your-feature-name
   ```

2. **Implement the feature** in the appropriate module. Follow the
   [code style guidelines](#code-style) below.

3. **Add unit tests** for the new functionality. Place them in the corresponding
   test file (e.g., `tests/unit/test_core.py`).

4. **Run the full test suite** to confirm everything passes:

   ```bash
   $ pytest
   ```

#### Improving Documentation

1. **Find the documentation source** – most docs live in `docs/` and are written
   in Markdown.

2. **Edit the file** – correct typos, clarify explanations, or add missing
   examples.

3. **Preview your changes** locally with the docs server:

   ```bash
   $ poe serve-docs
   ```

   Open `http://localhost:8000` in your browser to verify the updates.

### 5. Submit a Pull Request

1. **Commit your changes** with a clear, conventional commit message:

   ```bash
   $ git add .
   $ git commit -m "fix(core): correct greeting typo"
   ```

2. **Push** to your fork:

   ```bash
   $ git push origin feat/your-feature-name
   ```

3. **Open a pull request** on GitHub against the `main` branch. Fill in the PR
   template with a description of what you changed and why.

4. **Wait for CI** – the automated checks (tests, linting, formatting) will run.
   If they pass, a maintainer will review your PR. Address any feedback by
   pushing additional commits to the same branch.

## Code Style

CCC follows **PEP 8** and uses automated tools to keep the code consistent.

### Formatting with Black

Run **Black** before committing to auto‑format your Python code:

```bash
$ black .
```

Example of Black‑compliant style:

```python
from typing import Optional

def calculate_total(items: list[float], discount: Optional[float] = None) -> float:
    """Return the total price after applying an optional discount."""
    subtotal = sum(items)
    if discount is not None:
        subtotal -= subtotal * discount
    return subtotal
```

### Linting with Ruff

**Ruff** catches common mistakes and enforces style rules. Run it to see any
issues:

```bash
$ ruff check .
```

Fix any warnings or errors before submitting your PR.

### Type Hints

Use **type hints** for all function parameters and return values. They are
treated as first‑class documentation.

```python
# Good
def parse_config(path: str) -> dict[str, Any]:
    ...

# Avoid (no types)
def parse_config(path):
    ...
```

### Docstrings

Write **docstrings** for public functions, classes, and modules. Use the
triple‑quote Google style:

```python
def encode_data(data: bytes, key: str) -> bytes:
    """Encrypt the given data with the provided key.

    Args:
        data: Raw bytes to encrypt.
        key: Secret encryption key.

    Returns:
        Encrypted bytes.

    Raises:
        ValueError: If the key length is invalid.
    """
    ...
```

## Testing

### Unit Tests

Place unit tests in `tests/unit/`. Each test file should mirror the module it
tests (e.g., `test_core.py` for `core.py`). Use `pytest` fixtures and
parameterization where helpful.

Example test:

```python
def test_greet() -> None:
    from ccc.core import greet
    assert greet("world") == "Hello, world!"
```

### Integration Tests

Integration tests live in `tests/integration/` and require Docker and RustFS.
Run them separately with:

```bash
$ pytest -m integration
```

If you don’t have Docker installed, you can skip these tests; CI will run them
for your PR.

## Troubleshooting

| Problem                           | Solution                                                                                                                         |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----- |
| `uv sync` fails                   | Ensure you have **uv** installed (`curl -LsSf https://astral.sh/uv/install.sh                                                    | sh`). |
| Tests pass locally but fail in CI | Run `ruff check .` and `black --check .` to catch lint/format issues.                                                            |
| Integration tests require Docker  | Install Docker from [docker.com](https://docker.com). If you can’t run them, note in your PR that you skipped integration tests. |
| `poe serve-docs` fails            | Make sure the `docs` extra is installed: `uv sync --extra docs`.                                                                 |
| Git push rejected                 | Fetch upstream changes and rebase: `git fetch upstream main && git rebase upstream/main`.                                        |

## Code of Conduct

Be respectful and inclusive. This project follows the
[Contributor Covenant](https://www.contributor-covenant.org/). Instances of
abusive, harassing, or otherwise unacceptable behavior may be reported to the
project maintainers.

---

**Need help?** Open an issue on GitHub or join the discussion in the project’s
community channels.
