# Configuration Reference

The project reads configuration from environment variables or a TOML file parsed
into `Settings`:

| Key                       | Environment Variable          | Description                                                |
| ------------------------- | ----------------------------- | ---------------------------------------------------------- |
| `canvas.api_url`          | `CANVAS_API_URL`              | Base URL for the Canvas instance.                          |
| `canvas.token`            | `CANVAS_API_TOKEN`            | API token with rights to read submissions and post grades. |
| `canvas.course_id`        | `CANVAS_COURSE_ID`            | Numeric identifier of the Canvas course.                   |
| `runner.docker_image`     | `CCC_RUNNER_IMAGE` (planned)  | Docker image used to run grading jobs.                     |
| `runner.network_disabled` | `CCC_RUNNER_NETWORK_DISABLED` | Disable network inside grading container.                  |
| `runner.memory_limit`     | `CCC_RUNNER_MEMORY_LIMIT`     | Container memory limit (e.g., `1g`).                       |
| `runner.cpu_limit`        | `CCC_RUNNER_CPU_LIMIT`        | CPU quota for the container.                               |
| `working_dir`             | `CCC_WORKING_DIR`             | Root directory for temporary run workspaces.               |

Configuration files can be supplied via `ccc --config path/to/settings.toml` and
must follow the same structure as the `Settings` model defined in
`canvas_code_correction.config`.
