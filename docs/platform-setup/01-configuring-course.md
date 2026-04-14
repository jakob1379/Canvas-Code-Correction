# Configuring a Course

Use `ccc course setup` to create the **course block** that CCC loads at
runtime. This block stores the Canvas connection, grader image, asset storage
reference, asset prefix, and Prefect work pool for one course.

## Try It Now

If you already have a Canvas token, a course ID, and an assets block, run:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --slug cs101 \
  --assets-block course-assets-cs101 \
  --assets-prefix graders/cs101/ \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-pool course-work-pool-cs101
```

Expected output includes:

```text
✓ Canvas access validated successfully
✓ Course ID 12345 validated
✓ Course configuration saved as block: ccc-course-cs101
```

## What You Need

Before you run the command, gather:

1. A **Canvas API token**
2. The numeric **Canvas course ID**
3. An **assets block** that points at S3-compatible storage
4. A **grader Docker image**
5. A **work pool name** for Prefect workers

If you still need the assets block, start with
[RustFS Storage](07-rustfs-storage.md) for local development or your production
S3-compatible setup.

## The Command

`ccc course setup` is interactive by default. For repeatable automation, use
`--no-interactive` and pass every required value.

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --slug cs101 \
  --assets-block course-assets-cs101 \
  --assets-prefix graders/cs101/ \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-pool course-work-pool-cs101 \
  --env PYTHONUNBUFFERED=1
```

### Important flags

| Flag | What it controls |
| --- | --- |
| `--token-stdin` | Reads the Canvas token from standard input. |
| `--api-url`, `-u` | Canvas base URL. |
| `--course-id`, `-c` | Canvas course to bind to the block. |
| `--slug` | Suffix used in the block name `ccc-course-<slug>`. |
| `--assets-block` | Prefect block name for S3-compatible storage. |
| `--assets-prefix` | Prefix inside the assets bucket, for example `graders/cs101/`. |
| `--docker-image`, `-d` | Grader image used for corrections. |
| `--work-pool` | Prefect work pool that should execute this course. |
| `--env`, `-e` | Extra grader environment variables, repeatable. |

## What CCC Saves

The resulting `ccc-course-<slug>` block contains:

- **Canvas** URL, token, and course ID
- **Assets** block name and prefix
- **Grader** image, work pool, and extra environment variables
- **Webhook** defaults such as deployment name and rate limit

For the exact runtime model, see
[Configuration Reference](../reference/03-configuration.md).

## Verify the Block

List the configured courses:

```bash
$ ccc course list
```

Expected result: a table that includes the block name, Canvas course ID, grader
image, and assets block.

## Common Errors

Missing token in non-interactive mode:

```bash
$ ccc course setup --no-interactive --course-id 12345 --assets-block course-assets-cs101
```

Expected output:

```text
--token or --token-stdin is required in non-interactive mode
```

If Canvas validation fails, re-check the base URL and token. The CLI will print
the attempted URL and common causes.

## Next Steps

After the course block exists:

1. [Set up Prefect](02-setting-up-prefect.md)
2. [Deploy grader assets to CCC](05-deploying-tests-to-ccc.md)
3. [Run or monitor corrections](04-monitoring-results.md)
