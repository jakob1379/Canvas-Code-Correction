# Configuring a Course

**Audience**: CCC platform operators **Prerequisites**: Grader Docker image
built, grader tests uploaded to S3 storage, Prefect blocks created

??? note "Try It Now (60 seconds)"

    If you have a Canvas API token, course ID, and an S3 bucket block ready, run
    this command to configure a course immediately:

    ```bash
    $ ccc course setup \
      --slug cs101 \
      --course-id 12345 \
      --assets-block course-assets-cs101 \
      --docker-image yourusername/canvas-grader:latest \
      --s3-prefix graders/cs101/
    ```

    To avoid leaking tokens in shell history, you can pipe the token through stdin:

    ```bash
    $ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup \

      --slug cs101 \
      --token-stdin \
      --course-id 12345 \
      --assets-block course-assets-cs101 \
      --docker-image yourusername/canvas-grader:latest \
      --s3-prefix graders/cs101/
    ```

    You’ll see output similar to:

    ```
    Created Prefect block 'ccc-course-cs101' with:
      Canvas course ID: 12345
      Assets block: course-assets-cs101
      Docker image: yourusername/canvas-grader:latest
      S3 prefix: graders/cs101/
    ```

    The course is now ready for scheduling corrections.

---

This guide walks you through configuring a course on the **Canvas Code
Correction** (CCC) platform using the CLI and Prefect blocks. By the end you’ll
have a course block that links your Canvas course to the grader image and test
assets.

## Prerequisites

Before you start, gather these three items:

1. **Canvas API token** – generate in your Canvas account under “Settings → New
   Access Token”
2. **Canvas course ID** – the numeric ID from the course URL (e.g.,
   `https://canvas.instructure.com/courses/12345`)
3. **Prefect S3 bucket block** – created via the Prefect UI or CLI (see
   [Setting up Prefect](02-setting-up-prefect.md))

If you haven’t built a grader image or uploaded tests yet, complete those steps
first (see [Deploying tests to CCC](05-deploying-tests-to-ccc.md)).

## Step 1: Configure a course with the CLI

The `ccc course setup` command creates a Prefect block that stores all
course‑specific settings. Run it from the project root.

### Basic command

```bash
$ ccc course setup \
  --slug cs101 \
  --course-id 12345 \
  --assets-block course-assets-cs101 \
  --docker-image yourusername/canvas-grader:latest \
  --s3-prefix graders/cs101/
```

**What each option does:**

| Option                 | Description                                                              |
| ---------------------- | ------------------------------------------------------------------------ |
| `cs101`                | **Course slug** – a short, URL‑safe identifier (used in block names)     |
| `--token`, `-t`        | Canvas API token (if omitted, you’ll be prompted)                        |
| `--course-id`, `-i`    | Numeric Canvas course ID                                                 |
| `--assets-block`, `-a` | Name of an existing Prefect S3 bucket block                              |
| `--docker-image`, `-d` | Docker image that runs the grader (defaults to the base image)           |
| `--s3-prefix`, `-p`    | Path prefix inside the S3 bucket where grader assets are stored          |
| `--env`, `-e`          | Environment variables for the grader container (`KEY=VALUE`, repeatable) |

### Expected output

After a successful run you’ll see:

```
Created Prefect block 'ccc-course-cs101' with:
  Canvas course ID: 12345
  Assets block: course-assets-cs101
  Docker image: yourusername/canvas-grader:latest
  S3 prefix: graders/cs101/
```

The block is now stored in your Prefect workspace and can be referenced by its
slug (`cs101`).

## Step 2: Understanding Prefect blocks

CCC uses **Prefect blocks** to store configuration securely. The command creates
a block named `ccc-course-<slug>` (e.g., `ccc-course-cs101`). The block
contains:

- Canvas token (encrypted)
- Course ID
- S3 bucket block reference
- Docker image name
- S3 prefix
- Any environment variables

**Important**: The S3 bucket block must exist before you run `course setup`.
Create it via the Prefect UI or CLI (see
[Setting up Prefect](02-setting-up-prefect.md)).

## Step 3: Verify the configuration

List all configured courses to confirm your block was created:

```bash
$ ccc course list
```

Output:

```
Slug    Canvas ID  Docker Image
cs101   12345      yourusername/canvas-grader:latest
```

If you see your course in the list, the configuration is ready.

## Next steps

With a course configured, you can:

1. **Set up Prefect deployments and workers** –
   [Setting up Prefect](02-setting-up-prefect.md)
2. **Schedule automatic corrections** –
   [Scheduling corrections](03-scheduling-corrections.md)
3. **Monitor results** – [Monitoring results](04-monitoring-results.md)
4. **Deploy updated tests** –
   [Deploying tests to CCC](05-deploying-tests-to-ccc.md)

!!! note

    The course block is now available to any Prefect flow that uses the
    `Course` block type. You can update its settings by running `course setup`
    again with the same slug.
