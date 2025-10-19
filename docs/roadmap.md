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
- [x] **Phase 2 – Canvas Client Migration** - Canvas client, workspace store,
      Docker runner, result collector, uploader tasks, and end-to-end Prefect
      flow implemented with unit-test coverage; Phase 2 migration plan docs
      updated and PR #13 marked ready for review.
- [ ] **Phase 3 – Container Runner**: Harden Docker execution, add resource
      limits, smoke tests.
- [ ] **Phase 4 – Webhooks & Queueing**: FastAPI webhook receiver, Prefect
      deployments, optional external queue.
- [ ] **Phase 5 – Reporting & Docs**: Automated run summaries, expanded MkDocs
      content, CI integration.

## Contributing

Contributions should target the `v2` branch via focused pull requests and be
accompanied by appropriate documentation updates in this site.
