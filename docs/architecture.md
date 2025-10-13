---
title: Architecture Overview
---

# Architecture Overview

The v2 rewrite replaces the original bash pipeline with a Prefect-first
architecture that keeps the system modular, testable, and secure by default.

## Component Responsibilities

- **Prefect Flow** – coordinates the download, execution, upload, and reporting
  tasks. Runs entirely locally via Prefect Orion/agent.
- **CanvasClient** – encapsulates Canvas API access (download submissions,
  upload comments, post grades) with retries and structured logging.
- **Runner** – executes student submissions inside a Docker container derived
  from the provided template using a non-root UID/GID, memory/CPU limits, and
  optionally network isolation.
- **Submission Store** – temporary workspace on the host (or object storage)
  used to exchange artefacts with the runner.
- **Prefect Webhook** – Canvas events call Prefect's native webhook endpoint,
  which queues a flow run without additional services. Optional custom shims can
  be added later only if advanced preprocessing is required.

## Prefect Flow (UML Sequence)

```mermaid
sequenceDiagram
    autonumber
    participant Webhook as Canvas Webhook
    participant WebhookEndpoint as Prefect Webhook Endpoint
    participant Prefect as Prefect Orion
    participant Agent as Prefect Agent
    participant Runner as Docker Runner
    participant Canvas as Canvas API

    Webhook->>WebhookEndpoint: submission_created payload
    WebhookEndpoint->>Prefect: create flow run (assignment_id, submission_id)
    Prefect->>Agent: dispatch run
    Agent->>Runner: start grader container (non-root UID/GID)
    Runner->>Canvas: fetch submission artefacts
    Runner->>Runner: execute instructor tests, create feedback zip & points
    Runner->>Canvas: upload feedback & grade
    Runner->>Prefect: report artefacts & logs
    Prefect->>WebhookEndpoint: completion callback (optional)
```

## Component Diagram

```mermaid
graph TD
  subgraph Prefect
    F1[Prefect Flow]
    T1[Download Task]
    T2[Run Container Task]
    T3[Upload Task]
    F1 --> T1
    F1 --> T2
    F1 --> T3
  end

  subgraph Application
    C1[CanvasClient]
    R1[RunnerService]
    S1[SubmissionStore]
    W1[Prefect Webhook]
  end

  Canvas[(Canvas API)]
  Registry[(Container Registry)]

  W1 -->|schedule| F1
  T1 --> C1
  T1 --> S1
  T2 --> R1
  R1 --> Registry
  R1 --> S1
  T3 --> C1
  C1 --> Canvas
```

## Data Flow Stages

1. **Schedule** – Canvas webhook or CLI call triggers a Prefect flow run with
   assignment/submission identifiers.
2. **Download** – CanvasClient fetches the submission attachment(s) into an
   isolated workspace (or object storage). Metadata persists alongside artefacts
   for traceability.
3. **Execute** – Runner launches the grader Docker image using a non-root user,
   network isolation, and resource quotas. Feedback artefacts are generated
   in-place.
4. **Collect** – Prefect captures stdout/stderr, collects the feedback zip,
   points, and logs, and stores them for inspection.
5. **Upload** – Feedback and grades are pushed back to Canvas idempotently (md5
   and filename checks). Failures trigger Prefect retries.

## Security Considerations

- Every container run uses an unprivileged UID/GID configurable in settings; the
  Dockerfile ensures ownership alignment for mounted volumes.
- Network is disabled by default unless explicitly required for dependencies.
- Canvas API tokens are stored using Prefect blocks or environment
  variables—never committed to the repository.
- Project defaults target reproducibility: `uv` manages dependencies, Prefect
  logs provide run transparency, and MkDocs records design updates.
