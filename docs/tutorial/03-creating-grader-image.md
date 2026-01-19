# Creating a Custom Grader Docker Image

CCC runs your grader tests inside a Docker container. By default, CCC provides
the **base image** `jakob1379/canvas-grader:latest` (Ubuntu with Python
pre‑installed). This tutorial shows you how to build a custom Docker image when
you need extra dependencies.

## 1. Decide If You Need a Custom Image

**Use the base image unless you need extra packages.** The base image already
contains Python 3.13, a minimal Ubuntu environment, and the grader entrypoint.
You only need a custom image if your grader requires:

- Additional system packages (e.g., `graphviz`, `clang`, `java`)
- Language runtimes not present in the base image (e.g., Node.js, Ruby)
- Specialized tools (e.g., `pandoc`, `ffmpeg`)

If your grader only needs Python packages, install them via `pip` in your test
script. No custom image required.

## 2. Create a Dockerfile

Create a file named **Dockerfile** in your work‑package directory. Start from
the CCC base image and add the dependencies you need.

Here’s a minimal example that installs a single system package (`graphviz`):

```dockerfile
FROM jakob1379/canvas-grader:latest

# Install one additional package
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*
```

That’s it. The Dockerfile inherits the grader entrypoint and working directory
from the base image. You can add more `RUN`, `COPY`, or `ENV` instructions as
needed, but keep the image small and focused.

## 3. Build the Image

Open a terminal in the directory containing your Dockerfile and run:

```bash
docker build -t my-course/grader:latest .
```

You’ll see output similar to:

```
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

The image is now stored locally with the tag you provided
(`my-course/grader:latest`).

## 4. Test the Image Locally

Verify that your custom image works and includes the added dependency. Run a
quick test:

```bash
docker run --rm my-course/grader:latest dot -V
```

Expected output:

```
dot - graphviz version 2.42.2 (20200629.0806)
```

If you see the version string, the package was installed correctly. You can also
run a full grader test by mounting a sample submission:

```bash
mkdir -p sample/submission
echo "print('Hello')" > sample/submission/hello.py
docker run --rm -v "$(pwd)/sample/submission:/workspace/submission" my-course/grader:latest
```

The container will execute the default grader entrypoint (which expects your
test scripts). If you haven’t added test scripts yet, the container will exit
with an error. This is fine; the purpose is to confirm the image starts and can
access the submission directory.

## 5. Push to a Container Registry (Optional)

If you want to share the image with your CCC platform operator or deploy it to a
cloud environment, push it to a **container registry** (Docker Hub, GitHub
Container Registry, etc.).

First, tag the image with your registry URL:

```bash
docker tag my-course/grader:latest ghcr.io/your‑org/your‑course‑grader:latest
```

Then push it:

```bash
docker push ghcr.io/your‑org/your‑course‑grader:latest
```

The platform operator can later pull the image from that registry.

## Next Steps

Your custom grader image is ready. Now you can write the grader test scripts
that will run inside it. Proceed to
[Writing Grader Tests](./04-writing-grader-tests.md).

**Remember:** Keep your Dockerfile simple. Only add dependencies that are truly
required for grading. The smaller the image, the faster it starts and the less
storage it consumes.
