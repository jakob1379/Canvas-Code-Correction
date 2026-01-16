# Creating a Grader Image (Optional)

CCC runs your grader tests inside a Docker container. If the default
`jakob1379/canvas-grader:latest` image contains all dependencies your tests
need, you can skip this step. Only create a custom Docker image if you need
additional system packages, language runtimes, or specialized tools.

## Base Image

CCC provides a base image `jakob1379/canvas-grader:latest` based on Ubuntu with
Python pre-installed. You can extend it or use your own.

## Creating a Dockerfile

Create a `Dockerfile` in your grader repository:

```dockerfile
FROM jakob1379/canvas-grader:latest

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy grader scripts
COPY grader /grader

# Set working directory
WORKDIR /workspace

# Ensure the grader entrypoint is executable
RUN chmod +x /grader/run.sh
```

## Building and Pushing

Build the image:

```bash
docker build -t yourusername/canvas-grader:latest .
```

Push to a container registry (Docker Hub, GitHub Container Registry, etc.):

```bash
docker push yourusername/canvas-grader:latest
```

## Testing Locally

You can test the image locally by running:

```bash
docker run --rm -v $(pwd)/submission:/workspace/submission yourusername/canvas-grader:latest
```

Ensure your grader script outputs the required files (`results.json`,
`points.txt`, `comments.txt`).

Next, we'll write grader tests.
