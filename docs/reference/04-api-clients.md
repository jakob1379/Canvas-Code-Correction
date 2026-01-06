# API Clients Reference

Canvas interactions are consolidated in a forthcoming `CanvasClient` module.
Planned capabilities include:

- Download submission attachments with retry/backoff.
- Upload feedback artefacts (zip files) while avoiding duplicates via checksum
  checks.
- Post grades and comments idempotently.

Integration points:

- Prefect tasks will instantiate `CanvasClient` with credentials from
  `Settings`.
- Unit tests will mock Canvas endpoints using pytest fixtures and
  `pytest-datadir` sample payloads.

Future enhancements may include rate-limit handling and caching of course
metadata to reduce Canvas API traffic.
