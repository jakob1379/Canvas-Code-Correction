# Prerequisites

**Goal:** Get your Canvas API token and install Docker.

Before you can create work packages for automated grading, you need two things:

1. **Canvas API token** – to authenticate with your Canvas instance
2. **Docker** – to build and test grader images (if creating custom images)

Follow the steps below. Each section includes concrete commands and expected
outputs.

---

## 1. Get your Canvas API token

You’ll generate a personal access token from your Canvas instance. **Treat this
token like a password**: keep it secret and share it only with your CCC platform
operator.

### Step‑by‑step

1. **Log in** to your Canvas instance (e.g., `canvas.your‑university.edu`).
2. Click your profile picture or initials in the global navigation bar, then
   choose **Settings**.
3. Scroll to the **Approved Integrations** section.
4. Click the **New Access Token** button.
5. Fill in the **Purpose** field (e.g., “CCC grading automation”).
6. (Optional) Set an expiry date; for long‑running work packages, choose a date
   far in the future.
7. Click **Generate Token**.
8. **Copy the token immediately** – you won’t be able to see it again. Store it
   in a secure location (password manager, encrypted note, etc.).

!!! note "Screenshot guidance" After clicking **New Access Token**, you’ll see a
form with “Purpose” and “Expires” fields. The generated token appears as a long
string of letters and numbers once you submit the form.

### What to do with the token

- Provide the token to your CCC platform operator.
- The operator will configure the CCC platform to use this token for API calls
  on your behalf.

### Troubleshooting

- **“New Access Token” button missing?** Check with your Canvas administrator;
  you may need special permissions.
- **Token not working?** Ensure you copied the entire string (no extra spaces).
  Tokens are case‑sensitive.

---

## 2. Install Docker

Docker is required if you plan to build custom grader images. If you only use
pre‑built images, you can skip this step.

### Quick installation

Visit [docker.com/get‑started](https://docker.com/get‑started) and download the
Docker Desktop installer for your operating system.

**macOS / Windows:**

- Download the `.dmg` (macOS) or `.exe` (Windows) installer.
- Run the installer and follow the on‑screen prompts.
- Accept any required system extensions.

**Docker's convenience script (for testing only)**

!!! warning "Security Note" Piping `curl` directly to `sh` is generally unsafe.
Docker's convenience script is official, but you should always inspect scripts
from the internet before running them. This method is **not recommended for
production environments**.

```bash
curl -fsSL https://get.docker.com | bash
```

### Verify Docker is installed

Open a terminal and run:

```bash
docker --version
```

**Expected output:** `Docker version 29.1.3, build xxxxxxx` (version numbers
will vary).

If you see a version string, Docker is installed correctly.

---

## 3. Verify your setup

After completing both steps, confirm everything is ready.

### Canvas token

- You have a long alphanumeric token stored securely.
- You’ve shared it with your CCC operator (or know how to provide it when
  prompted).

### Docker

Run a quick test to ensure Docker can start a container:

```bash
docker run hello-world
```

**Expected output:** A message that begins with “Hello from Docker!” and
explains that your installation appears to be working.

If the command succeeds, Docker is set up correctly.

---

## Troubleshooting tips

| Symptom                               | Likely cause                         | Fix                                                                                |
| ------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------- |
| `docker: command not found`           | Docker not installed or not in PATH. | Re‑run the installer, or add Docker to your PATH.                                  |
| `Cannot connect to the Docker daemon` | Docker service isn’t running.        | Start Docker Desktop (macOS/Windows) or run `sudo systemctl start docker` (Linux). |
| Canvas API returns “Invalid token”    | Token copied incorrectly or expired. | Generate a new token and ensure you copy the entire string.                        |
| “New Access Token” button missing     | Insufficient Canvas permissions.     | Contact your Canvas administrator to grant “Manage API tokens” permission.         |

---

## Next steps

Once you have your Canvas API token and Docker (if needed), you’re ready to:

- [Create a grader Docker image](./03-creating-grader-image.md) (optional, if
  you need custom dependencies)
- [Write grader tests](./04-writing-grader-tests.md)

If you encounter issues not covered here, reach out to your CCC platform
operator.
