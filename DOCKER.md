# Docker deployment (API + UI + Postgres)

This repo supports running the Flask API and Next.js UI in Docker via `docker compose`.

## Quick start

From the repo root:

```bash
docker compose up --build
```

Then:
- UI: `http://localhost:3002`
- API: `http://localhost:5002/api`
- Swagger: `http://localhost:5002/api/docs`

## Use your existing Postgres (OmniDB-managed)

Docker Compose automatically loads environment variables from a repo-root `.env`.

Add (or update) in `.env`:

```bash
# Example: Postgres running on your host machine
DATABASE_URL=postgresql://USER:PASSWORD@host.docker.internal:5432/collective_memory

# Only enable if your DB has pgvector extension AND your schema uses VECTOR columns
CM_ENABLE_PGVECTOR=false
```

Then run:

```bash
docker compose up --build
```

### Notes on DB connectivity

- Do **not** use `localhost` in `DATABASE_URL` when the API runs in Docker. Inside the container, `localhost` means “the container itself”.
- For a Postgres on your **host machine**, use `host.docker.internal` (we also map it in `docker-compose.yml` for Linux compatibility).
- If the DB is on your **host machine** (macOS/Windows Docker Desktop), use `host.docker.internal`.
- If the DB is on a **remote server**, use its hostname/IP in `DATABASE_URL`.
- If your DB does **not** have pgvector enabled, keep `CM_ENABLE_PGVECTOR=false` (recommended unless you’ve set up pgvector fully).

## Use the bundled Postgres (optional)

If you want a self-contained stack (includes `pgvector` Postgres):

```bash
docker compose --profile localdb up --build
```

## Notes

### API

The API container runs via Gunicorn:
- Dockerfile: `Dockerfile.api`
- Exposes: `5001`

### UI (Next.js)

The UI uses Next’s `output: 'standalone'` build:
- Dockerfile: `Dockerfile.web`
- Container port: `3000` (mapped to host `3001`)

`NEXT_PUBLIC_API_URL` is a **build-time** variable for the browser bundle.
If you change it, you must rebuild the `web` image.

### Postgres + pgvector

If you run the bundled DB (`--profile localdb`), it uses `pgvector/pgvector:pg16` so the pgvector extension is available.

## MCP server in Docker (for Claude Code)

MCP servers communicate over **stdio**. Claude Code can run the MCP server as a Docker container by launching `docker run -i ...` so stdin/stdout are wired correctly.

### Build the MCP image

```bash
docker build -f Dockerfile.mcp -t collective-memory-mcp:local .
```

### Configure Claude Code to use Docker

Use `claude mcp add-json` (recommended). On macOS, use `host.docker.internal` so the container can reach the API running on your host (or another container you’ve exposed):

```bash
claude mcp add-json collective-memory '{
  "command": "docker",
  "args": [
    "run", "-i", "--rm",
    "-e", "CM_API_URL=http://host.docker.internal:5002",
    "-e", "CM_AGENT_ID=claude-code-collective-memory",
    "-e", "CM_PERSONA=backend-code",
    "collective-memory-mcp:local"
  ]
}'
```

### Linux notes

If `host.docker.internal` isn’t available on your Linux Docker setup, you can either:

- Use host networking (often simplest):

```bash
docker run -i --rm --network=host -e CM_API_URL=http://127.0.0.1:5002 -e CM_AGENT_ID=... -e CM_PERSONA=... collective-memory-mcp:local
```

- Or add the host gateway mapping:

```bash
docker run -i --rm --add-host=host.docker.internal:host-gateway -e CM_API_URL=http://host.docker.internal:5002 ...
```

