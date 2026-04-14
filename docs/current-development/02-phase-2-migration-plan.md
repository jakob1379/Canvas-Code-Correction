# Phase 2 Migration Plan

This document is now a **historical alignment note** for the v1 to v2
migration. The migration work is complete; the value of this page is to explain
how the legacy bash-based pipeline maps to the code that exists today.

## Current Outcome

The migration landed on a Python 3.13 codebase built around:

- `canvas_code_correction.clients.canvas_resources`
- `canvas_code_correction.flows.correction`
- `canvas_code_correction.flows.workspace`
- `canvas_code_correction.flows.runner`
- `canvas_code_correction.flows.collector`
- `canvas_code_correction.flows.uploader`
- `canvas_code_correction.webhooks.*`

The live operator workflow is described in:

- [Configuring a Course](../platform-setup/01-configuring-course.md)
- [Setting Up Prefect](../platform-setup/02-setting-up-prefect.md)
- [Monitoring Results](../platform-setup/04-monitoring-results.md)

## Legacy-to-Current Mapping

| Legacy concern | Current implementation |
| --- | --- |
| Canvas API access | `clients/canvas_resources.py` and course settings |
| Workspace preparation | `flows/workspace.py` |
| Docker grader execution | `flows/runner.py` |
| Result collection | `flows/collector.py` |
| Canvas uploads | `flows/uploader.py` |
| End-to-end orchestration | `flows/correction.py` |
| Webhook intake | `webhooks/server.py`, `webhooks/handler.py`, `webhooks/auth.py` |
| Deployment management | `webhooks/deployments.py` and `ccc system deploy create` |

## What Replaced the Old Manual Steps

### Course configuration

Old migration notes often referred to ad hoc environment files or shell
wrappers. The supported path is now:

```bash
$ ccc course setup
```

### Deployment creation

Old migration notes referred to hand-written Prefect deployment build commands.
The supported path is now:

```bash
$ ccc system deploy create ccc-course-cs101
```

### Local storage for testing

Use the repository helpers:

```bash
$ poe s3
$ poe rustfs-setup
```

### Local validation

Use the repo tasks:

```bash
$ poe all
$ uv run zensical build --strict --clean
```

## Verification Commands

These commands match the current repository layout:

```bash
$ uv run pytest tests/unit -v --strict-markers
$ uv run pytest tests/integration -v --strict-markers -m integration --no-cov
$ poe test-e2e
```

## Remaining Historical Notes

The original migration goals around container isolation, typed settings,
webhooks, and RustFS-backed local storage are all reflected in the current
codebase. What changed most since the early migration notes is the operator
surface:

- course setup is CLI-first through `ccc`
- deployment creation is CLI-first through `ccc`
- the built-in deployment is webhook-oriented, not a generic cron batch runner

## Related Docs

- [Roadmap](01-roadmap.md)
- [Architecture Overview](../reference/01-architecture.md)
- [CLI Reference](../reference/02-cli.md)
