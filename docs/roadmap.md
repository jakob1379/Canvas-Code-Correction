# Roadmap

This roadmap tracks planned milestones for the v2 rewrite. It will be updated as
features migrate from the legacy bash implementation to the Prefect-based
architecture.

## Milestones

- [x] **Phase 1 – Bootstrap**: Core scaffolding, uv-managed dependencies,
      Prefect flow skeleton. _(Complete)_
- [x] Phase 1.5 - **Setup a test/dev environment**: use the shared Canvas cloud
      course at https://canvas.instructure.com/courses/13121974 for development
      validation
- [ ] **Phase 2 – Canvas Client Migration** - Inventory legacy Canvas scripts
      and the Prefect stubs to capture required endpoints and auth needs (tokens
      live in the repo `.env`). - Stand up a reusable IMSCC-based course fixture
      (`ccc-testing-course-export.imscc`) for reference; re-importing/cloning
      remains a manual step for now. - Design and implement a shared Python
      Canvas client with auth/session management, pagination, and retry/backoff
      support. - Port high-value workflows (submissions download, grade upload,
      file sync, etc.) into Prefect tasks/flows with accompanying unit and
      optional integration tests. - Document manual validation steps against the
      hosted sandbox course and record troubleshooting guidance.
- [ ] **Phase 3 – Container Runner**: Harden Docker execution, add resource
      limits, smoke tests.
- [ ] **Phase 4 – Webhooks & Queueing**: FastAPI webhook receiver, Prefect
      deployments, optional external queue.
- [ ] **Phase 5 – Reporting & Docs**: Automated run summaries, expanded MkDocs
      content, CI integration.

## Contributing

Contributions should target the `v2` branch via focused pull requests and be
accompanied by appropriate documentation updates in this site.
