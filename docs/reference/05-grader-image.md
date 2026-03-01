# Grader Image Guide

Create a **grader Docker image** for Canvas Code Correction (CCC) to execute
student submissions in an isolated environment. This guide walks you through
building, hardening, packaging, and configuring a grader image, from a minimal
example to production-ready deployment.

## Quick Start: Create and Test a Minimal Grader Image

Start with the CCC base image `jakob1379/canvas-grader:latest` (Ubuntu with
Python 3.13 pre‑installed). Create a **Dockerfile** in your grader repository:

```dockerfile
FROM jakob1379/canvas-grader:latest

# Install any extra system packages your grader needs
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*
```

Build the image:

```bash
$ docker build -t my-course/grader:latest .
```

```output
Sending build context to Docker daemon  4.096kB
Step 1/2 : FROM jakob1379/canvas-grader:latest
latest: Pulling from jakob1379/canvas-grader
Digest: sha256:...
Status: Downloaded newer image for jakob1379/canvas-grader:latest
 ---> a1b2c3d4e5f6
Step 2/2 : RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*
 ---> Running in 1234567890ab
Get:1 http://archive.ubuntu.com/ubuntu jammy InRelease [270 kB]
...
Setting up graphviz (2.42.2-6) ...
 ---> 7890abcdef12
Successfully built 7890abcdef12
Successfully tagged my-course/grader:latest
```

Test that the image works and includes the added dependency:

```bash
$ docker run --rm my-course/grader:latest dot -V
```

```output
dot - graphviz version 2.42.2 (20200629.0806)
```

Your minimal grader image is ready. Now add hardening, package your grader code,
and configure CCC to use it.

## 1. Hardening Steps

The CCC base image already follows security best practices. When you extend it,
keep these hardening principles in mind.

### Run as a Non‑Root User

The base image creates a non‑root user `app` (UID/GID configurable via build
arguments). Your container will automatically run as this user, reducing the
impact of potential container escapes.

Verify the user inside the container:

```bash
$ docker run --rm my-course/grader:latest whoami
app
```

### Dependency Management

Install system dependencies with `apt-get` in a single `RUN` layer and clean up
afterward to keep the image small:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        graphviz \
        clang \
    && rm -rf /var/lib/apt/lists/*
```

For Python dependencies, use `pip` inside your grader test scripts. No need to
bake them into the image unless they are large or rarely change.

### Frozen Dependencies

If your grader uses `uv` or `pip-tools`, you can mirror the project’s tooling
inside the image. Add a `requirements.txt` or `pyproject.toml` and install with
`--frozen`:

```dockerfile
COPY requirements.txt .
RUN uv pip install --frozen -r requirements.txt
```

This ensures the same versions are used in the container as in your development
environment.

## 2. Packaging Course‑Specific Graders

Course configuration should **not** require modifying the CCC source tree.
Instead, ship grader code and test assets with your Docker image (or mount them
read‑only at runtime) while keeping CCC itself immutable.

Two common approaches:

### Approach 1: General‑Purpose Base Image

Start from a lightweight Ubuntu image, install the language runtimes and
dependencies required by your grader, and copy your test harness into the image
under `/opt/grader`.

Example Dockerfile:

```dockerfile
FROM ubuntu:22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create non‑root user
RUN useradd -m -u 1000 app
USER app

# Copy grader scripts
COPY --chown=app:app grader /opt/grader
WORKDIR /opt/grader

# Set entrypoint to the grader harness
ENTRYPOINT ["python3", "/opt/grader/run.py"]
```

### Approach 2: Course‑Specialized Image

Fork the CCC base image and bake in course‑specific tooling or third‑party
binaries. When sensitive test assets should **not** be bundled into the image,
mount them read/executable‑only via Prefect worker volume configuration.

Example Dockerfile:

```dockerfile
FROM jakob1379/canvas-grader:latest

# Add course‑specific binaries
COPY --chown=app:app binaries/ /usr/local/bin/

# Install extra system packages
RUN apt-get update && apt-get install -y \
    java-17-openjdk \
    && rm -rf /var/lib/apt/lists/*

# Grader entrypoint is already set by the base image
```

In both cases the container should expose the grader entry script via
`ENTRYPOINT` (or `CMD`) so Prefect can invoke it directly. The script is
responsible for reading submission files from `/workspace/submission` and
writing results (`results.json`, `points.txt`, `comments.txt`) back to the
workspace.

## 3. Building and Publishing

Once your Dockerfile packages the grader harness and any required test assets,
build and optionally push the image to a container registry.

### Build the Image

```bash
$ docker build -t <registry>/grader:latest .
```

Replace `<registry>` with your Docker Hub username, GitHub Container Registry
address, or private registry URL.

### Push to a Registry (Recommended)

Tag the image with the full registry path, then push:

```bash
$ docker tag <registry>/grader:latest ghcr.io/your‑org/your‑course‑grader:latest
$ docker push ghcr.io/your‑org/your‑course‑grader:latest
```

```output
The push refers to repository [ghcr.io/your‑org/your‑course‑grader]
latest: digest: sha256:... size: 1234
```

Publishing the image allows CCC workers to pull it from a central location.

## 4. Configuring CCC to Use the Image

Provision the course through the Prefect flow/deployment instead of the former
CLI. The provisioning flow will:

1. Create (or overwrite) the course work pool.
2. Upload the grader asset folder to S3 via the configured Prefect S3 block.
3. Persist a `ccc-course-<course_slug>` block referencing the Docker image and
   latest asset materialization.

### Using the Provisioning Flow Directly

Example Python snippet:

```python
from pathlib import Path
from canvas_code_correction.flows.provision import provision_course_flow

provision_course_flow(
    course_name="my-course",
    course_id=42,
    docker_image="ghcr.io/your‑org/your‑course‑grader:latest",
    assets_path=str(Path("grader-assets")),
    bucket_block="course-assets-my-course",
)
```

Alternatively, build and apply the provided deployment script under
`canvas_code_correction/deployments/provision.py` so operators can trigger
provisioning from Prefect Cloud/UI.

### Local Testing with RustFS

For local development and testing, use the RustFS S3‑compatible server:

```bash
# Start RustFS server
$ poe s3
```

```output
Starting RustFS S3 server on http://localhost:9000
Credentials: rustfsadmin / rustfsadmin
```

Set up RustFS for testing:

```bash
$ poe rustfs-setup
```

```output
Verifying RustFS is running...
Creating bucket 'test-assets'...
Uploading test asset...
Registered Prefect S3 block 'local-rustfs'.
```

Configure the course to use the local RustFS block:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup \
  --slug my-course \
  --token-stdin \
  --course-id 42 \
  --docker-image my-course/grader:latest \
  --assets-block local-rustfs \
  --s3-prefix dev
```

```output
Course configuration saved as block: ccc-course-my-course
```

See the [Deploying Tests to CCC](../platform-setup/05-deploying-tests-to-ccc.md)
guide for details.

## 5. Validating the Setup

Once provisioning completes and the correction deployment is active, trigger a
test run via Prefect (UI, CLI, or API).

### Trigger a Test Run Manually

```bash
$ prefect deployment run my-course-corrections
```

### Verify Execution

Inspect the Prefect flow run logs to confirm:

1. The correct Docker image was pulled.
2. Grader assets were downloaded into the container.
3. The grader command executed successfully.
4. Results (`results.json`, `points.txt`, `comments.txt`) were written back to
   the workspace.

### Common Validation Steps

- **Image accessibility**: Ensure the worker environment has credentials for
  private registries (if used).
- **Worker sizing**: Ensure the worker host has enough CPU and memory for your
  grader workload.
- **Asset synchronization**: Verify the S3 bucket/prefix contains the latest
  grader test files.

## Next Steps

Your grader image is now ready for production. Continue with:

- [Writing Grader Tests](../tutorial/04-writing-grader-tests.md) – develop the
  actual test logic.
- [Deploying Tests to CCC](../platform-setup/05-deploying-tests-to-ccc.md) –
  publish tests and configure the CCC platform.
- [CLI Reference](02-cli.md) – trigger grading flows and monitor results.

**Remember:** Keep your Dockerfile simple. Only add dependencies that are truly
required for grading. The smaller the image, the faster it starts and the less
storage it consumes.
