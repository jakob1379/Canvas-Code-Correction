# Contributing

This guide describes the current contributor workflow for **Canvas Code
Correction (CCC)**. It is intentionally practical: install the dev environment,
run the repo commands, make focused changes, and verify them before opening a
pull request.

## Try It Now

Set up the full development environment from the repository root:

```bash
$ uv sync --all-groups
$ source .venv/bin/activate
$ poe all
```

If the environment is healthy, you will finish with passing format, lint, type,
and unit-test checks.

## Development Setup

### Prerequisites

- **Python 3.13**
- **uv**
- **Docker** if you need integration or e2e coverage

### Install the project

```bash
$ uv sync --all-groups
$ source .venv/bin/activate
```

If you do not want to activate the environment, use `uv run <command>` instead.

### Verify the CLI

```bash
$ ccc --version
```

Expected output:

```text
Canvas Code Correction 2.0.0a0
```

## Daily Workflow

### Create a branch

```bash
$ git switch -c <type>/<short-description>
```

Examples:

- `fix/webhook-auth-timeout`
- `docs/update-course-setup-guide`
- `feat/course-block-validation`

### Run the standard checks

Use the task aliases in `pyproject.toml`:

```bash
$ poe fmt
$ poe lint
$ poe check
$ poe test
```

Or run the full local gate:

```bash
$ poe all
```

### Test scopes

Default `pytest` excludes integration and e2e markers. Run the larger suites
explicitly when your changes touch those paths.

Unit tests:

```bash
$ uv run pytest tests/unit -v --strict-markers
```

Integration tests:

```bash
$ uv run pytest tests/integration -v --strict-markers -m integration --no-cov
```

End-to-end tests:

```bash
$ poe test-e2e
```

## Code Style

### Formatting and linting

CCC uses **Ruff** for formatting and linting.

```bash
$ ruff format
$ ruff check --fix
```

CI-friendly variants:

```bash
$ ruff check
$ pyrefly check
```

### Python requirements

- Target **Python 3.13** only.
- Use **type hints** throughout.
- Keep public interfaces explicit and small.
- Prefer updating the existing flow/CLI/service modules over adding parallel
  abstractions.

### Tests

- Put unit tests in `tests/unit/`.
- Put integration tests in `tests/integration/`.
- Put e2e tests in `tests/e2e/`.
- Do not use `autouse=True` fixtures. `tests/AGENTS.md` repeats this rule.

## Documentation Changes

If you change docs, use [.docs-style-checklist.md](.docs-style-checklist.md).
At minimum, each affected page should:

- start with a clear goal or quick-start section
- use the current command names and flags from the codebase
- show expected output when it adds clarity
- link to the adjacent docs that readers need next

Preview or rebuild docs with:

```bash
$ poe serve-docs
$ uv run zensical build --strict --clean
```

## Common Change Patterns

### Bug fixes

1. Reproduce the problem with a focused test or command.
2. Patch the implementation.
3. Add or update a regression test.
4. Re-run the narrow test first, then `poe all`.

### CLI changes

If you change `src/canvas_code_correction/cli*.py`, update:

- `README.md`
- `docs/reference/02-cli.md`
- any platform setup page that shows the changed command

### Docs-only changes

Run at least:

```bash
$ uv run zensical build --strict --clean
```

## Pull Requests

Before you open a PR:

1. Keep the branch focused.
2. Use a conventional commit message, for example `docs(reference): align cli flags`.
3. Summarize the user-visible change and any verification you ran.
4. Note any checks you could not run.

Typical commit flow:

```bash
$ git add <files>
$ git commit -m "docs(reference): align course setup flags"
$ git push origin <branch>
```

## Troubleshooting

| Problem | What to check |
| --- | --- |
| `uv sync` fails | Confirm your Python toolchain supports 3.13 and that `uv` is installed correctly. |
| `ccc` is not found | Activate `.venv` or prefix the command with `uv run`. |
| Integration tests fail immediately | Ensure RustFS and any required Canvas credentials are configured. |
| e2e tests fail before running assertions | Start the docker-compose stack through `poe test-e2e` or bring the services up manually. |
| Docs build fails | Fix the broken link, malformed Markdown, or bad admonition syntax and rerun `uv run zensical build --strict --clean`. |

## Need Help

Open an issue or draft PR with the failing command, the exact output, and the
files you were changing.
