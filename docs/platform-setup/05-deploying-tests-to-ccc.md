# Deploying Grader Tests to Canvas Code Correction (CCC)

!!! note "Try It Now (5 minutes)"

    Deploy your first grader test to CCC using local RustFS storage. This quick
    start assumes you have:

    - Docker installed and running
    - `uv` installed (see [project setup](../README.md))
    - Prefect Cloud or self-hosted Orion configured
      ([Setting up Prefect](02-setting-up-prefect.md))
    - Canvas API token and course ID stored in `.env` or Prefect blocks

    **Start the local S3 server**:

    ```bash

$ poe s3 ```

    ```
    Starting RustFS server on http://localhost:9000
    Access key: rustfsadmin
    Secret key: rustfsadmin
    Storage directory: ./workspace
    Server ready.
    ```

    **In a new terminal, set up RustFS for CCC**:

    ```bash
    $ poe rustfs-setup
    ```

    ```
    ✓ RustFS server reachable at http://localhost:9000
    ✓ Bucket 'test-assets' created
    ✓ Test asset uploaded to s3://test-assets/dev/test.txt
    ✓ Prefect S3 block 'local-rustfs' registered
    Local RustFS is ready for use with CCC.
    ```

    **Build a grader image** (update `containers/grader/Dockerfile` first if
    needed):

    ```bash
    $ docker build -t my-grader:latest containers/grader
    ```

    ```
    [+] Building 2.1s (12/12) FINISHED
    => => naming to docker.io/library/my-grader:latest
    ```

    **Configure the course** (replace `cs101` with your course slug):

    ```bash
    $ ccc configure-course cs101 \
      --docker-image my-grader:latest \
      --memory-limit 2g \
      --cpu-limit 2.0 \
      --env PYTHONUNBUFFERED=1 \
      --assets-block local-rustfs
    ```

    ```
    ✓ Prefect block 'ccc-course-cs101' saved
    ✓ Work pool 'course-work-pool-cs101' created
    Course 'cs101' configured successfully.
    ```

    **Create a Prefect deployment**:

    ```bash
    $ prefect deployment build \
      canvas_code_correction.flows.correct_submission:correct_submission_flow \
      -n cs101-corrections \
      -q course-work-pool-cs101 \
      -a
    ```

    ```
    Deployment built and applied successfully!
    View deployment in UI: https://app.prefect.cloud/deployments/...
    ```

    **Start a worker**:

    ```bash
    $ prefect worker start --pool course-work-pool-cs101
    ```

    ```
    Worker started. Polling for flow runs...
    Connected to work pool 'course-work-pool-cs101'.
    ```

    **Trigger a test run**:

    ```bash
    $ prefect deployment run cs101-corrections
    ```

    ```
    Flow run submitted: cs101-corrections/alert-marmot
    ```

    Watch the worker logs to see your grader execute inside a Docker container. If
    everything is set up correctly, you will see the flow run complete
    successfully in the Prefect UI.

---

## Prerequisites

Before deploying grader tests, ensure you have:

1. **Prefect access** – either [Prefect Cloud](https://app.prefect.cloud) or a
   self‑hosted Orion instance. See
   [Setting up Prefect](02-setting-up-prefect.md) for configuration details.
2. **Docker** – installed locally for building grader images.
3. **Grader repository** – the course‑specific grader repository with instructor
   tests.
4. **Canvas credentials** – API token and course ID stored in `.env` or Prefect
   blocks.
5. **`uv`** – installed and the project dependencies resolved (`uv sync`).

!!! tip
    Export `PREFECT_API_URL`, `PREFECT_API_KEY`, and Canvas credentials before running CLI commands,
    or update your Prefect profile to include them.

## 1. Local Development with RustFS

CCC includes a lightweight S3‑compatible server (RustFS) for local development
and testing. It stores assets in the `./workspace` directory and uses fixed
credentials (`rustfsadmin`/`rustfsadmin`).

### Start RustFS

```bash
$ poe s3
```

```
Starting RustFS server on http://localhost:9000
Access key: rustfsadmin
Secret key: rustfsadmin
Storage directory: ./workspace
Server ready.
```

Keep this terminal running. The server listens on `http://localhost:9000`.

### Configure RustFS for CCC

Run the setup script to create a bucket, upload a test asset, and register a
Prefect S3 block named `local‑rustfs`:

```bash
$ poe rustfs-setup
```

```
✓ RustFS server reachable at http://localhost:9000
✓ Bucket 'test-assets' created
✓ Test asset uploaded to s3://test-assets/dev/test.txt
✓ Prefect S3 block 'local-rustfs' registered
Local RustFS is ready for use with CCC.
```

You can now use `--assets-block local-rustfs` when configuring courses for local
testing.

### Customize RustFS Settings

The setup can be tailored with environment variables:

| Variable             | Default                 | Purpose                |
| -------------------- | ----------------------- | ---------------------- |
| `RUSTFS_ENDPOINT`    | `http://localhost:9000` | S3 endpoint URL        |
| `RUSTFS_ACCESS_KEY`  | `rustfsadmin`           | Access key             |
| `RUSTFS_SECRET_KEY`  | `rustfsadmin`           | Secret key             |
| `RUSTFS_BUCKET_NAME` | `test-assets`           | Bucket name            |
| `RUSTFS_PREFIX`      | `dev`                   | Path prefix for assets |

Example for a production‑like setup:

```bash
export RUSTFS_ENDPOINT="https://rustfs.example.com"
export RUSTFS_ACCESS_KEY="your-access-key"
export RUSTFS_SECRET_KEY="your-secret-key"
export RUSTFS_BUCKET_NAME="course-assets"
export RUSTFS_PREFIX="graders/cs101"
poe rustfs-setup
```

For detailed RustFS configuration, see [RustFS Storage](07-rustfs-storage.md).

## 2. Build and Publish the Grader Image

1. Update `containers/grader/Dockerfile` (or your course‑specific Dockerfile)
   with the required dependencies and entrypoint.
2. Build the image:

```bash
$ docker build -t jakob1379/canvas-grader:latest containers/grader
```

3. If you use a remote registry, push the image:

```bash
$ docker push jakob1379/canvas-grader:latest
```

!!! note
    The image tag must be accessible from wherever the Prefect worker runs.  For private registries,
    ensure the worker environment has the necessary credentials.

## 3. Configure Prefect Blocks

Use the `ccc configure‑course` CLI to provision a Prefect work pool, record
runner settings, and associate an S3 assets block that points to the
bucket/prefix containing immutable grader tests.

```bash
$ ccc configure-course <course-slug> \
  --docker-image <image:tag> \
  --memory-limit 2g \
  --cpu-limit 2.0 \
  --env PYTHONUNBUFFERED=1 \
  --assets-block <block-name> \
  --s3-bucket <course-assets-bucket> \
  --s3-prefix graders/<course-slug>/
```

**Example with local RustFS** (block created by `rustfs‑setup`):

```bash
$ ccc configure-course cs101 \
  --docker-image my-grader:latest \
  --assets-block local-rustfs
```

**Example with production S3** (block must already exist):

```bash
$ ccc configure-course cs101 \
  --docker-image jakob1379/canvas-grader:latest \
  --assets-block course-assets-cs101 \
  --s3-bucket course-assets \
  --s3-prefix graders/cs101/
```

The command saves a Prefect course configuration block named `ccc‑course‑<course‑slug>` (by
default) and creates or reuses a work pool `course‑work‑pool‑<course‑slug>`.

For more about course configuration, see
[Configuring a Course](01-configuring-course.md).

## 4. Register a Prefect Deployment

Create a Prefect deployment so CCC flows can be triggered manually, on a
schedule, or via webhooks.

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n <course-slug>-corrections \
  -q <course-work-pool> \
  -a
```

- `-q` specifies the work pool (course‑specific) that matching workers will
  poll.
- `-a` applies the deployment immediately.

Example:

```bash
$ prefect deployment build \
  canvas_code_correction.flows.correct_submission:correct_submission_flow \
  -n cs101-corrections \
  -q course-work-pool-cs101 \
  -a
```

```
Deployment built and applied successfully!
View deployment in UI: https://app.prefect.cloud/deployments/...
```

Alternatively, create deployments through the Prefect UI. For scheduling
automated runs, see [Scheduling Corrections](03-scheduling-corrections.md).

## 5. Start a Prefect Worker

Launch a worker connected to the course work pool so queued flow runs can
execute the grader code inside the Docker container.

```bash
$ prefect worker start --pool <course-work-pool>
```

Workers can run locally, on a dedicated VM, or inside container orchestration.
Ensure Docker access is available wherever the worker runs.

Example:

```bash
$ prefect worker start --pool course-work-pool-cs101
```

```
Worker started. Polling for flow runs...
Connected to work pool 'course-work-pool-cs101'.
```

For detailed worker configuration, see
[Local Prefect Worker Guide](06-prefect-agent.md).

## 6. Trigger Test Runs

With the deployment active and a worker online, you can trigger runs in several
ways:

### Manual Run via CLI

```bash
$ prefect deployment run <course-slug>-corrections
```

### One‑Off Run Targeting a Specific Submission

```bash
$ ccc run-once <assignment-id>
```

### Automatic Runs via Canvas Webhook

Configure the Canvas webhook to call the Prefect webhook URL. When a submission
is made, CCC will automatically start a correction flow. See
[Scheduling Corrections](03-scheduling-corrections.md) for webhook setup.

### Run from the Prefect UI

Navigate to the deployment in the Prefect UI and click **Run**.

## 7. Verify and Iterate

1. **Inspect logs** in Prefect to ensure the grader command runs successfully.
2. **Review artefacts** in the submission workspace (results, points, comments).
3. **Adjust grader tests** or container configuration as required.
4. **Rebuild/push the image** when the runtime environment changes.
5. **Update grader tests** by uploading new files to the S3 bucket/prefix
   referenced by the Prefect block; the next flow run will pick up the new
   assets automatically.

For monitoring flow runs and results, see
[Monitoring Results](04-monitoring-results.md).

## Troubleshooting

| Problem                        | Likely Cause                                      | Solution                                                                                                               |
| ------------------------------ | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Worker cannot pull image**   | Missing Docker credentials or incorrect image tag | Ensure the worker environment has credentials for private registries and that the image tag is correct.                |
| **Canvas API failures**        | Invalid or missing tokens/course IDs              | Verify tokens and course IDs are present in your settings (`.env` or Prefect block).                                   |
| **Timeouts / resource issues** | Insufficient memory or CPU                        | Adjust `--memory‑limit`, `--cpu‑limit`, or `--gpu‑enabled` flags when running `configure‑course`.                      |
| **No runs start**              | Work pool mismatch or worker not connected        | Confirm the work pool name in the deployment matches the running worker and that the worker log shows it is connected. |
| **RustFS server unreachable**  | Server not running or wrong endpoint              | Check that `poe s3` is still running and that `RUSTFS_ENDPOINT` matches the server URL.                                |

Following these steps keeps grader tests aligned with CCC’s Prefect‑based
orchestration while allowing instructors to iterate rapidly on course‑specific
grading logic.
