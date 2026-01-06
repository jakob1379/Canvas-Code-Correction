# RustFS Storage

CCC can use RustFS, a lightweight S3-compatible storage server, for local development and testing.

## Running RustFS Locally

Start the RustFS server:

```bash
uv run poe s3
```

This starts a server at `http://localhost:9000` with default credentials `rustfsadmin`/`rustfsadmin`. Data is stored in `./workspace`.

## Setting Up for Testing

Run the setup script to create a bucket and upload test assets:

```bash
uv run poe rustfs-setup
```

This script:

1. Verifies RustFS is running
2. Creates a `test-assets` bucket
3. Uploads a test asset file
4. Registers a Prefect S3 block named `local-rustfs`

## Configuration

Customize via environment variables:

- `RUSTFS_ENDPOINT`: S3 endpoint URL (default: `http://localhost:9000`)
- `RUSTFS_ACCESS_KEY`: Access key (default: `rustfsadmin`)
- `RUSTFS_SECRET_KEY`: Secret key (default: `rustfsadmin`)
- `RUSTFS_BUCKET_NAME`: Bucket name (default: `test-assets`)
- `RUSTFS_PREFIX`: Path prefix for assets (default: `dev`)

Example production setup:

```bash
export RUSTFS_ENDPOINT="https://rustfs.example.com"
export RUSTFS_ACCESS_KEY="your-access-key"
export RUSTFS_SECRET_KEY="your-secret-key"
export RUSTFS_BUCKET_NAME="course-assets"
export RUSTFS_PREFIX="graders/cs101"
uv run poe rustfs-setup
```

## Using RustFS with CCC

When configuring a course, use the `--assets-block` flag with the block name created by the setup script (e.g., `local-rustfs`).

```bash
uv run ccc configure-course cs101 \
  --assets-block local-rustfs \
  --s3-prefix dev/
```

## Production Considerations

For production, consider using a dedicated S3 service (AWS S3, MinIO, etc.) with proper backups and access controls. RustFS is suitable for development and small-scale deployments.