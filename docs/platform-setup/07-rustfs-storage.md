# RustFS Storage

**RustFS** is the repo's local **S3-compatible storage** option for development
and testing.

## Try It Now

In one terminal:

```bash
$ poe s3
```

In a second terminal:

```bash
$ poe rustfs-setup
```

Expected setup output includes:

```text
✓ RustFS is reachable at http://localhost:9000
✓ Created bucket 'test-assets'
✓ Uploaded test asset to 'test-assets/dev/test.txt'
```

If Prefect is reachable too, the script also registers the `local-rustfs`
Prefect block.

## What the Setup Script Does

`scripts/setup_rustfs.py` performs these steps:

1. probes the RustFS endpoint
2. creates the configured bucket if needed
3. uploads a small test asset
4. registers the `local-rustfs` block when Prefect is available

## Default Configuration

These environment variables control the setup:

| Variable | Default | Purpose |
| --- | --- | --- |
| `RUSTFS_ENDPOINT` | `http://localhost:9000` | S3-compatible endpoint |
| `RUSTFS_ACCESS_KEY` | `rustfsadmin` | Access key |
| `RUSTFS_SECRET_KEY` | `rustfsadmin` | Secret key |
| `RUSTFS_BUCKET_NAME` | `test-assets` | Bucket name |
| `RUSTFS_PREFIX` | `dev` | Prefix used for the sample asset |

## Using RustFS with CCC

Point a course block at the registered local block and choose the prefix where
your grader assets live:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --course-id 12345 \
  --docker-image ghcr.io/example/cs101-grader:latest
```

CCC will download grader assets from that block and prefix into
`/workspace/assets`.

## Example Override

```bash
$ export RUSTFS_ENDPOINT="https://rustfs.example.com"
$ export RUSTFS_ACCESS_KEY="your-access-key"
$ export RUSTFS_SECRET_KEY="your-secret-key"
$ export RUSTFS_BUCKET_NAME="course-assets"
$ export RUSTFS_PREFIX="graders/cs101"
$ poe rustfs-setup
```

## Production Note

RustFS is for **development and testing**. For production use a managed or
production-ready S3-compatible service and create the corresponding Prefect
block there.

## Related Docs

- [Configuring a Course](01-configuring-course.md)
- [Deploying Grader Tests to CCC](05-deploying-tests-to-ccc.md)
- [Configuration Reference](../reference/03-configuration.md)
