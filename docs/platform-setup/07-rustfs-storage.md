# RustFS Storage

**Audience**: CCC platform operators **Prerequisites**: Docker installed, Python
environment with `uv` (see [Project Setup](../project-setup.md))

**RustFS** is a lightweight S3‑compatible storage server that CCC can use for
local development and testing. With RustFS you can emulate cloud storage on your
laptop, upload grader assets, and run the entire correction pipeline without
connecting to a real S3 service.

!!! note "Try It Now (2 minutes)"

    If you have Docker running, execute these three commands to start RustFS,
    create a test bucket, and register a Prefect block:

    ```bash
    $ poe s3
    ```

    Expected output (first line):

    ```
     INFO  rustfs > Starting server on http://localhost:9000
    ```

    In a **second terminal**, run:

    ```bash
    $ poe rustfs-setup
    ```

    Expected output:

    ```
    ✅ RustFS is reachable at http://localhost:9000
    ✅ Created bucket 'test-assets'
    ✅ Uploaded test asset 'greeting.txt'
    ✅ Registered Prefect S3 block 'local-rustfs'
    ```

    Now you can use the block `local-rustfs` when you
    [configure a course](01-configuring-course.md).

---

## What is RustFS?

RustFS is a minimal S3‑compatible object‑storage server written in Rust. It runs
in a Docker container, stores data in a local directory (`./workspace`), and
uses the same API as AWS S3. CCC uses RustFS for **local development** and
**integration testing**: you can upload grader assets, run corrections, and
verify the whole storage layer without leaving your machine.

## Running RustFS Locally

Start the RustFS server with the project’s Poe task:

```bash
$ poe s3
```

You’ll see output similar to:

```
 INFO  rustfs > Starting server on http://localhost:9000
 INFO  rustfs > Default credentials: rustfsadmin / rustfsadmin
 INFO  rustfs > Data directory: ./workspace
 INFO  rustfs > Press Ctrl+C to stop
```

The server is now listening at `http://localhost:9000`. Keep this terminal open
while you work with RustFS.

## Setting Up for Testing

Once RustFS is running, open another terminal and run the setup script:

```bash
$ poe rustfs-setup
```

This script performs four actions:

1. **Verifies** RustFS is reachable.
2. **Creates** a bucket named `test‑assets`.
3. **Uploads** a test asset file (`greeting.txt`).
4. **Registers** a Prefect S3 block named `local‑rustfs`.

You’ll see the success messages shown in the “Try It Now” section. The Prefect
block is now ready to be used by CCC.

## Configuration

You can customize RustFS behavior with environment variables. The defaults are:

| Variable             | Default                 | Purpose                       |
| -------------------- | ----------------------- | ----------------------------- |
| `RUSTFS_ENDPOINT`    | `http://localhost:9000` | S3 endpoint URL               |
| `RUSTFS_ACCESS_KEY`  | `rustfsadmin`           | Access key                    |
| `RUSTFS_SECRET_KEY`  | `rustfsadmin`           | Secret key                    |
| `RUSTFS_BUCKET_NAME` | `test‑assets`           | Bucket for grader assets      |
| `RUSTFS_PREFIX`      | `dev`                   | Path prefix inside the bucket |

For example, to point the setup script at a production‑like RustFS instance:

```bash
export RUSTFS_ENDPOINT="https://rustfs.example.com"
export RUSTFS_ACCESS_KEY="your-access-key"
export RUSTFS_SECRET_KEY="your-secret-key"
export RUSTFS_BUCKET_NAME="course-assets"
export RUSTFS_PREFIX="graders/cs101"
poe rustfs-setup
```

The script will create the bucket `course‑assets` and register a Prefect block
with the supplied credentials.

## Using RustFS with CCC

When you [configure a course](01-configuring-course.md), pass the block name
created by the setup script (by default `local‑rustfs`) to the `--assets‑block`
flag:

```bash
$ ccc configure-course cs101 \
  --assets-block local-rustfs \
  --s3-prefix dev/
```

CCC will store and retrieve grader assets from your RustFS bucket. If you need
to change the bucket or prefix later, update the Prefect block with
`prefect block edit` and reconfigure the course.

## Production Considerations

RustFS is designed for **development and testing**. It does not provide
durability, backups, or fine‑grained access controls. For production workloads,
use a dedicated S3‑compatible service:

- **AWS S3** (with appropriate IAM policies)
- **MinIO** (self‑hosted, production‑ready)
- **Google Cloud Storage** (S3 interoperability mode)
- **Azure Blob Storage** (S3 compatibility layer)

When you switch to a production storage service, update the environment
variables and re‑run `rustfs‑setup` (or create the Prefect block manually). The
rest of CCC (course configuration, scheduling, and correction flows) remains
unchanged.

!!! note "Next Step" After setting up storage,
[configure a course](01-configuring-course.md) to start scheduling corrections.
