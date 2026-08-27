# Deployment

This doc explains how to deploy PromptLab (backend + frontend) using Docker. It's the fastest,
most reproducible way to run the app, and is the recommended path for anyone pulling this repo
for the first time. For local, non-Docker development instead (hot-reload, etc.), see the
[README](../README.md#development-setup).

---

## Prerequisites

- **Docker** (24+) and **Docker Compose** (v2, i.e. the `docker compose` subcommand — not the
  legacy standalone `docker-compose`)
- **Git**

That's it — you do not need Python, Node, or any dependencies installed on your host machine.
Everything runs inside the containers.

---

## Quick start (recommended)

From the repo root:

```bash
git clone <your-repo-url>
cd 10x-engineer-project-repo

docker compose up --build
```

This builds both images and starts them together:

| Service                        | URL                          |
|---------------------------------|-------------------------------|
| Frontend (app UI)                | http://localhost:5173         |
| Backend API base URL             | http://localhost:8000         |
| Interactive API docs (Swagger UI)| http://localhost:8000/docs    |
| Health check                     | http://localhost:8000/health  |

Open http://localhost:5173 in a browser — the app is ready to use immediately, no further setup
required.

Stop it with:

```bash
docker compose down
```

Add `-d` to `docker compose up --build -d` to run in the background (detached mode).

---

## Running the containers individually (without Compose)

If you only need one service, or want more control over how each is run:

```bash
# Backend
docker build -t promptlab-backend ./backend
docker run -p 8000:8000 promptlab-backend

# Frontend
docker build -t promptlab-frontend ./frontend
docker run -p 5173:80 promptlab-frontend
```

The frontend image is a static production build served by nginx (built via `docker compose`'s
`frontend/Dockerfile`, a Node 22 multi-stage build). It talks to the backend at
`http://localhost:8000` by default — see [Environment variables](#environment-variables-and-secrets)
below if you need to point it elsewhere.

---

## Environment variables and secrets

**There are no secrets, API keys, or credentials required to run this app.** It has no
authentication, no external service integrations, and no database — so there's nothing to
configure or keep out of source control.

There is exactly one environment variable in the whole app:

| Variable              | Where it's used                  | Default                 | Purpose                                                                 |
|------------------------|-----------------------------------|--------------------------|--------------------------------------------------------------------------|
| `VITE_API_BASE_URL`    | `frontend/src/api/client.ts`      | `http://localhost:8000` | The backend URL the frontend's browser-side code calls.                 |

Notes on this variable:

- It's a **Vite build-time variable**, not a runtime one — it gets baked into the static JS
  bundle when the frontend image is built, and can't be changed by setting it on a running
  container. To override it, pass it as a Docker **build arg**:

  ```bash
  docker build -t promptlab-frontend --build-arg VITE_API_BASE_URL=https://api.example.com ./frontend
  ```

  (Compose users: add a `build.args` entry for the `frontend` service in `docker-compose.yml` if
  you need this for a non-default deployment.)
- For the default `docker compose up --build` setup, you don't need to set this at all — the
  browser calls `http://localhost:8000` directly (resolved by your browser, not the container
  network), which works because the backend's port is published on the host.
- Only override it if you're deploying the backend and frontend to different hosts/domains (e.g.
  a real production deployment behind separate URLs).

The **backend** reads no environment variables at all and has no `.env` file or `.env.example` —
there is nothing to configure there.

---

## What "deployment" means for this project

Worth being explicit about, since this affects how you'd deploy it anywhere beyond a laptop:

- **No persistence.** The backend stores all data (prompts, collections) in memory. Restarting
  the backend container — or redeploying, or an orchestrator rescheduling the pod — wipes all
  data. There is currently no database or volume to configure.
- **No authentication.** Every API endpoint is open to anyone who can reach it. Don't expose this
  deployment on the open internet without putting something in front of it (auth proxy,
  network restrictions, etc.) if that matters for your use case.
- **CORS is wide open** (`allow_origins=["*"]`) on the backend — fine for local/demo use, not
  something to carry as-is into a real production deployment.
- **No concurrency safety.** The in-memory storage has no locking, so a multi-worker/multi-replica
  deployment of the backend could race. Stick to a single backend instance.

In short: this Docker setup is meant for local use, demos, and grading/review — not as a
hardened production deployment. See [Known limitations](../README.md#known-limitations) in the
README for the full list and reasoning.

---

## Troubleshooting

- **Port already in use** (`5173` or `8000`): stop whatever else is using that port, or change the
  host-side port mapping in `docker-compose.yml` (e.g. `"5174:80"`).
- **Frontend loads but API calls fail**: confirm the backend container is running and reachable at
  http://localhost:8000/health. If you rebuilt the frontend with a custom `VITE_API_BASE_URL`,
  make sure that URL is actually reachable from your browser.
- **Stale build after code changes**: Compose caches image layers. Force a clean rebuild with
  `docker compose up --build --force-recreate`, or `docker compose build --no-cache` for a fully
  clean image build.
