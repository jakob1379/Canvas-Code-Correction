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
- [ ] **Phase 2 – Canvas Client Migration**: Port download/upload helpers, add
      retries and observability.
- [ ] **Phase 3 – Container Runner**: Harden Docker execution, add resource
      limits, smoke tests.
- [ ] **Phase 4 – Webhooks & Queueing**: FastAPI webhook receiver, Prefect
      deployments, optional external queue.
- [ ] **Phase 5 – Reporting & Docs**: Automated run summaries, expanded MkDocs
      content, CI integration.

## Contributing

Contributions should target the `v2` branch via focused pull requests and be
accompanied by appropriate documentation updates in this site.
