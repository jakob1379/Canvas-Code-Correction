# Prerequisites for Work Package Creation

Before creating your work package, ensure you have:

## Required for Course Responsible

- **Canvas API token**: Generate from your Canvas instance (Settings > New
  Access Token). You'll provide this to the CCC platform operator.
- **Docker**: Installed locally to build and test grader images (only if
  creating custom images).

## Optional (Operator Responsibility)

- **Prefect account**: Platform operators manage Prefect for workflow
  orchestration.
- **S3-compatible storage**: Operators provision storage for grader assets.
- **Python & uv**: Helpful for local testing but not required.

## Setting up Canvas API

1. Log into your Canvas instance.
2. Go to **Account** > **Settings**.
3. Under **Approved Integrations**, click **New Access Token**.
4. Copy the token and store it securely—you'll share it with your CCC operator.

## Installing Docker

Follow the official Docker installation guide for your operating system. You'll
use Docker to build your grader image.

Once you have a Canvas token (and Docker if creating custom images), you're
ready to proceed.
