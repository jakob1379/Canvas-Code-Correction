# Testing Canvas Live Events Locally

Use the development stack when Canvas must deliver real submission events to
CCC running on your machine. Canvas requires a public HTTPS endpoint, so the
stack includes a **named, remotely managed Cloudflare Tunnel**. The hostname is
stable across restarts; unlike an ephemeral tunnel, it does not require the
Canvas subscription to be edited each time.

The request path is:

```text
Canvas Live Events
  -> https://ccc-dev.example.edu/webhooks/canvas/ccc-course-cs101
  -> Cloudflare Tunnel
  -> webhook-listener:8080
  -> Prefect deployment and worker
  -> Docker grader
  -> Canvas uploader (dry-run by default)
```

## Prerequisites

- Docker with Compose support
- a development Canvas course and API token
- Canvas account-level access to Data Services / Live Events
- a remotely managed named Cloudflare Tunnel and public hostname

Create the tunnel and hostname in Cloudflare before starting CCC. Configure
the public-hostname service to route to:

```text
http://webhook-listener:8080
```

Do not put Cloudflare Access authentication in front of this hostname: Canvas
must be able to POST events directly. CCC authenticates signed Canvas payloads.

## Configure `.env.dev`

Keep all local secrets in the ignored `.env.dev` file. Add the following names
using values for your environment; never commit or paste their values into
logs or issue reports:

```dotenv
CLOUDFLARE_TUNNEL_TOKEN=
CCC_WEBHOOK_PUBLIC_URL=
CCC_COURSE_SLUG=
CANVAS_LIVE_EVENTS_JWKS_URL=
CCC_WEBHOOK_DRY_RUN=true

CANVAS_API_URL=
CANVAS_API_TOKEN=
CANVAS_COURSE_ID=
CANVAS_TEST_ASSIGNMENT_ID=

CCC_WORKSPACE_ROOT=
CCC_WORK_POOL_NAME=local-pool
```

`CCC_WEBHOOK_PUBLIC_URL` is the HTTPS origin only, with no trailing slash.
`CCC_COURSE_SLUG` produces the block name `ccc-course-<slug>`. The Canvas JWK
URL is optional when the built-in official endpoint is appropriate.

The stack refuses live Canvas writes unless they are deliberately unlocked.
Leave `CCC_WEBHOOK_DRY_RUN=true` for tunnel and event-delivery testing. An API
token permits API reads; its presence does not itself enable grade or comment
writes.

## Start and inspect the stack

`docker-compose.yml` is the repository's local-development stack. Production
deployment is managed separately, so the optional Live Events services are
selected with the `dev-webhook` profile instead of a Compose override file or
host-side lifecycle script.

Validate configuration before creating containers:

```bash
$ poe dev-stack-config
```

Start the services and provision the local RustFS block, Prefect work pool,
course block, and deployment:

```bash
$ poe dev-stack-up
```

The profile runs a one-shot `dev-init` service before starting the worker and
listener. Initialization is idempotent, and any validation or provisioning
failure prevents the dependent services from starting. The equivalent direct
command is:

```bash
$ docker compose --env-file .env.dev \
    --profile dev-webhook \
    up --build --wait -d
```

Inspect or follow the stack with:

```bash
$ poe dev-stack-status
$ poe dev-stack-logs
```

To inspect provisioning specifically:

```bash
$ docker compose --env-file .env.dev \
    --profile dev-webhook \
    logs dev-init
```

Run the infrastructure smoke checks:

```bash
$ poe dev-stack-smoke
```

The smoke check verifies the local listener, public tunnel, Prefect API, work
pool, and deployment. Signed-payload behavior is covered by the unit and
integration suites; the real-event procedure below validates the complete
Canvas delivery path without performing Canvas writes.

## Configure Canvas Data Services

In the Canvas account that owns the development course:

1. Open **Data Services** and create a **Live Events** HTTPS stream.
2. Choose the Canvas event format.
3. Select `submission_created` and `submission_updated`.
4. Enable **Sign Payload**.
5. Use the callback assembled from `CCC_WEBHOOK_PUBLIC_URL` and
   `CCC_COURSE_SLUG`, which has this form:

   ```text
   https://<public-host>/webhooks/canvas/ccc-course-<slug>
   ```

Canvas sends a compact signed JWT as the request body. CCC verifies that body
against Canvas's rotating JWK set before it reads the event claims. A local
HMAC secret or bearer token is not the signing mechanism for Canvas Live
Events; those authentication modes remain only for compatibility and synthetic
clients.

Creating a stream requires Canvas Data Services permissions. A Canvas API key
alone cannot create or replace that account-level configuration.

## Exercise a real event safely

Submit a file to the configured development assignment, then confirm:

1. `poe dev-stack-logs` shows an accepted delivery without exposing its body.
2. The listener returns `202 Accepted`.
3. Prefect shows one flow run and an online worker picks it up.
4. The grader completes and reports uploads as dry-run actions.
5. Canvas receives no grade or comment.

Canvas retries failed HTTPS deliveries. CCC uses the event/request identity to
collapse retries so one delivery does not start several flow runs. Keep a
non-2xx response visible while troubleshooting: it tells Canvas to retry after
a transient JWK-fetch or Prefect handoff failure.

## Troubleshooting

- **Public health check fails:** confirm the Cloudflare hostname targets
  `http://webhook-listener:8080`, the tunnel reports connected, and the listener
  is healthy locally.
- **Canvas gets 401:** confirm **Sign Payload** is enabled and the configured
  JWK endpoint matches the Canvas environment. Do not add the API token as a
  webhook bearer token.
- **Canvas gets 502:** JWK retrieval or another authentication dependency is
  unavailable. Restore connectivity and let Canvas retry.
- **No Prefect run appears:** verify the deployment exists, the course slug in
  the callback matches its block, and the worker is online for
  `CCC_WORK_POOL_NAME`.
- **The grader cannot see files:** `CCC_WORKSPACE_ROOT` must be absolute and
  mounted at the same path in the worker and host Docker daemon.
- **Containers use localhost URLs:** service-to-service settings must use
  Compose names such as `prefect-server` and `rustfs`, not `localhost`.

## Tear down

Stop the stack when testing is complete:

```bash
$ poe dev-stack-down
```

Disable or delete the Canvas Live Events stream if the public endpoint will no
longer be available. This prevents repeated failed deliveries. The named tunnel
and hostname may remain configured for the next development session, but its
token must remain only in `.env.dev`.
