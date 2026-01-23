# Development Roadmap

## Current Status

The Canvas Code Correction project is undergoing a v2 rewrite from a legacy
bash‑based system to a modern Prefect‑based architecture. **All planned
milestones are now complete**: the core platform is fully functional and ready
for production use.

You can:

- **Deploy the system** using the
  [platform setup guide](../platform-setup/01-configuring-course.md)
- **Explore the architecture** in the
  [architecture reference](../reference/01-architecture.md)
- **Follow the migration plan** for legacy users in
  [Phase 2 migration](./02-phase-2-migration-plan.md)

The table below shows the completed milestones and their current state.

## Milestones

| Milestone                             | Status      | Key Deliverables                                                                                          | Notes                                                                                                       |
| ------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Phase 1 – Bootstrap**               | ✅ Complete | Core scaffolding, uv‑managed dependencies, Prefect flow skeleton                                          | Establishes the modern Python foundation                                                                    |
| **Phase 1.5 – Test/Dev Environment**  | ✅ Complete | Shared Canvas cloud course (`https://canvas.instructure.com/courses/13121974`) for validation             | Enables rapid iteration without affecting production courses                                                |
| **Phase 2 – Canvas Client Migration** | ✅ Complete | Canvas client, workspace store, Docker runner, result collector, uploader tasks, end‑to‑end Prefect flow  | All components implemented and tested; see the [migration plan](./02-phase-2-migration-plan.md) for details |
| **Phase 3 – Container Runner**        | ✅ Complete | Docker execution with resource limits, smoke tests                                                        | Runner hardened for security and resource isolation                                                         |
| **Phase 4 – Webhooks & Queueing**     | ✅ Complete | FastAPI webhook receiver with JWT validation, rate limiting, Prefect deployments, optional external queue | Production‑ready webhook handling                                                                           |
| **Phase 5 – Reporting & Docs**        | ✅ Complete | Automated run summaries, expanded MkDocs content, GitHub Actions CI                                       | Documentation and reporting fully integrated into the CI/CD pipeline                                        |

## What’s Next

With the v2 rewrite complete, the project now enters a **maintenance and
enhancement phase**. Future work will focus on:

- **Performance optimizations** – profiling and improving execution latency
- **Extended grader language support** – adding runtimes for additional
  programming languages
- **Enhanced monitoring** – deeper integration with Prefect Cloud and custom
  dashboards
- **Community contributions** – streamlining the contributor workflow and
  expanding the example gallery

If you have ideas or need a specific feature, please open an issue on the
project repository.

## Contributing

Contributions target the `dev` branch via focused pull requests. **Every change
must be accompanied by updated documentation** in this site.

Before you start:

1. **Read the [contributing guidelines](../../CONTRIBUTING.md)** (if present)
   and the [architecture overview](../reference/01-architecture.md).
2. **Discuss larger changes** by opening an issue first.
3. **Follow the [Conventional Commits](https://www.conventionalcommits.org/)
   standard** for commit messages.
4. **Run the test suite** with `pytest` and ensure all checks pass.
5. **Update the relevant documentation** (tutorials, references, or this
   roadmap) to reflect your changes.

For small fixes (typos, broken links) you can submit a PR directly.

!!! note The project uses `git flow`. Start a new feature with
`git flow feat start <feature-name>` and finish it with
`git flow feat finish <feature-name>`.
