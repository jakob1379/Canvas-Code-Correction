# Configuring a Course

Use `ccc course setup` to create the **course block** that CCC loads at
runtime. This block stores the Canvas connection, grader image, asset storage
reference, asset prefix, and Prefect work pool for one course.

## Try It Now

If you already have a Canvas token and course ID, run:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest
```

Expected output includes:

```text
✓ Canvas access validated successfully
✓ Course ID 12345 validated
✓ Course configuration saved as block: ccc-course-12345-cs101
```

## What You Need

Before you run the command, gather:

1. A **Canvas API token**
2. The numeric **Canvas course ID**
3. A **grader Docker image**

The CLI generates the course block name, assets block name, assets prefix, and
work pool from the selected course and persists those generated values
automatically.

If you still need the assets block, start with
[RustFS Storage](07-rustfs-storage.md) for local development or your production
S3-compatible setup.

## The Command

`ccc course setup` is interactive by default. For repeatable automation, use
`--no-interactive` and pass the required values.

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --api-url https://canvas.example.edu \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --env PYTHONUNBUFFERED=1
```

### Important flags

| Flag | What it controls |
| --- | --- |
| `--token-stdin` | Reads the Canvas token from standard input. |
| `--api-url`, `-u` | Canvas base URL. |
| `--course-id`, `-c` | Canvas course to bind to the block. |
| `--docker-image`, `-d` | Grader image used for corrections. |
| `--env`, `-e` | Extra grader environment variables, repeatable. |

Generated values:

- Course block: `ccc-course-<course-id>-<slugified-course-code>`
- Assets block: `ccc-assets-<course-id>-<slugified-course-code>`
- Assets prefix: `graders/<course-id>-<slugified-course-code>/`
- Work pool: `course-work-pool-<course-id>-<slugified-course-code>`

## What CCC Saves

The resulting `ccc-course-<course-slug>` block contains:

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
$ ccc course setup --no-interactive --course-id 12345
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
