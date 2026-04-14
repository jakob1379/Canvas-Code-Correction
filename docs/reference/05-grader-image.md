# Grader Image Guide

This guide describes the **current grader contract** for CCC:

- CCC pulls a **Docker image** from `grader_image`
- CCC downloads grader assets into **`/workspace/assets`**
- the default grader command is **`sh /workspace/assets/main.sh`**

## Try It Now

Build a minimal grader image:

```dockerfile
FROM jakob1379/canvas-grader:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends graphviz \
    && rm -rf /var/lib/apt/lists/*
```

Then build it:

```bash
$ docker build -t ghcr.io/example/cs101-grader:latest .
```

## What the Image Must Provide

Your image should provide the runtime required by your grader assets. CCC does
not expect the assets to be baked into the repo itself; it expects:

1. a pullable image
2. a reachable assets block and prefix
3. a runnable command inside `/workspace/assets`

By default, that command is:

```text
sh /workspace/assets/main.sh
```

If you change the command in the block, keep it compatible with the workspace
layout described in
[Authoring Grader Tests](06-authoring-grader-tests.md).

## Recommended Base Image

Start from the project base image unless you have a strong reason not to:

```dockerfile
FROM jakob1379/canvas-grader:latest
```

It already aligns with the repo's Python 3.13 runtime expectations.

## Build and Publish

Build:

```bash
$ docker build -t ghcr.io/example/cs101-grader:latest .
```

Push when workers need remote access:

```bash
$ docker push ghcr.io/example/cs101-grader:latest
```

## Local Validation

Basic smoke test:

```bash
$ docker run --rm ghcr.io/example/cs101-grader:latest python3 --version
```

If your grader depends on shell tooling, validate that too:

```bash
$ docker run --rm ghcr.io/example/cs101-grader:latest sh -lc 'command -v bash'
```

## Wiring the Image into CCC

Store the image in the course block:

```bash
$ printf "%s" "$CANVAS_API_TOKEN" | ccc course setup --no-interactive \
  --token-stdin \
  --course-id 12345 \
  --slug cs101 \
  --assets-block course-assets-cs101 \
  --assets-prefix graders/cs101/ \
  --docker-image ghcr.io/example/cs101-grader:latest \
  --work-pool course-work-pool-cs101
```

## Assets Layout

Your chosen assets prefix should contain the files the command needs. With the
default command, that normally means:

```text
graders/cs101/
  main.sh
  tests/
  fixtures/
```

CCC downloads those files into `/workspace/assets`.

## Operational Checks

Before a real run, confirm:

- the worker host can `docker pull` the image
- the assets block resolves to the correct bucket
- the assets prefix contains `main.sh`
- the worker has enough CPU and memory for the grader workload

## Related Docs

- [Deploying Grader Tests to CCC](../platform-setup/05-deploying-tests-to-ccc.md)
- [Configuring a Course](../platform-setup/01-configuring-course.md)
- [Authoring Grader Tests](06-authoring-grader-tests.md)
