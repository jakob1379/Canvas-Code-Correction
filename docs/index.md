# Canvas Code Correction

**Canvas Code Correction (CCC)** automates Canvas grading with **Prefect**,
**Docker**, and **S3-compatible asset storage**.

## Try It Now

Verify a fresh checkout in under a minute:

```bash
$ uv sync
$ source .venv/bin/activate
$ ccc --help
```

Expected output begins with:

```text
Usage: ccc [OPTIONS] COMMAND [ARGS]...
```

If that command works, your local environment is ready.

## What CCC Does

CCC gives you one codebase for the full grading loop:

1. **Configure a course** with Canvas credentials, grader image, asset block,
   and work pool.
2. **Download submissions** from Canvas.
3. **Run the grader** in Docker against a prepared workspace.
4. **Collect results** such as points, comments, and feedback artifacts.
5. **Upload grades and feedback** back to Canvas.
6. **Trigger runs** manually or from Canvas webhooks through Prefect.

## Choose Your Path

| If you are... | Start here | Why |
| --- | --- | --- |
| A **course owner** writing grader logic | [Tutorial](./tutorial/index.md) | Build the grader image and grader assets. |
| A **platform operator** running CCC | [Configuring a Course](./platform-setup/01-configuring-course.md) | Set up blocks, workers, deployments, and local services. |
| A **developer** changing CCC itself | [Architecture Overview](./reference/01-architecture.md) | Understand the flows, services, and runtime boundaries. |
| Tracking active work | [Roadmap](./current-development/01-roadmap.md) | See what is current, historical, or still changing. |

## Documentation Map

### Tutorial

Use this path when you are authoring grader assets:

1. [Prerequisites](./tutorial/02-prerequisites.md)
2. [Creating a Grader Docker Image](./tutorial/03-creating-grader-image.md)
3. [Writing Grader Tests](./tutorial/04-writing-grader-tests.md)

### Platform Setup

Use this path when you are operating CCC:

1. [Configuring a Course](./platform-setup/01-configuring-course.md)
2. [Setting Up Prefect](./platform-setup/02-setting-up-prefect.md)
3. [Scheduling Corrections](./platform-setup/03-scheduling-corrections.md)
4. [Monitoring Results](./platform-setup/04-monitoring-results.md)
5. [Deploying Grader Tests to CCC](./platform-setup/05-deploying-tests-to-ccc.md)
6. [Running Prefect Locally](./platform-setup/06-prefect-agent.md)
7. [RustFS Storage](./platform-setup/07-rustfs-storage.md)

### Reference

Use this section when you need exact behavior or field names:

1. [Architecture Overview](./reference/01-architecture.md)
2. [CLI Reference](./reference/02-cli.md)
3. [Configuration Reference](./reference/03-configuration.md)
4. [API Clients](./reference/04-api-clients.md)
5. [Grader Image Guide](./reference/05-grader-image.md)
6. [Authoring Grader Tests](./reference/06-authoring-grader-tests.md)

## Local Operator Workflow

These commands cover the common local stack:

```bash
$ poe prefect
$ poe s3
$ poe rustfs-setup
$ ccc system status
```

Useful development commands:

```bash
$ poe all
$ uv run zensical build --strict --clean
```

## Notes for Contributors

If you edit docs, apply [.docs-style-checklist.md](../.docs-style-checklist.md)
to the pages you touch. Prefer runnable commands, real outputs, direct language,
and clear links to the next page a reader should open.
