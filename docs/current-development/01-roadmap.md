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
- [x] **Phase 2 – Canvas Client Migration** - Canvas client and workspace store
      implemented; Docker runner, result collector, uploader tasks, and
      end-to-end Prefect flow completed. All Phase 2 components are now
      implemented and tested.
- [x] **Phase 3 – Container Runner**: Harden Docker execution, add resource
      limits, smoke tests. _(Complete - Docker runner with resource limits
      implemented)_
- [x] **Phase 4 – Webhooks & Queueing**: FastAPI webhook receiver, Prefect
      deployments, optional external queue. _(Complete - Webhook server with JWT
      validation, rate limiting, deployment management)_
- [x] **Phase 5 – Reporting & Docs**: Automated run summaries, expanded MkDocs
      content, CI integration. _(In progress - GitHub Actions CI added, docs
      updated)_

## Contributing

Contributions should target the `v2` branch via focused pull requests and be
accompanied by appropriate documentation updates in this site.
