# PromptLab

**An AI Prompt Engineering Platform — "Postman for Prompts"**

PromptLab is a learning project built around a small backend REST API for storing, organizing,
and managing AI prompt templates. It doubles as a teaching sandbox for practicing AI-assisted
software engineering: finding and fixing bugs, writing documentation, adding tests, and using
structured spec-driven workflows (via [GitHub Spec Kit](https://github.com/github/spec-kit) and
Claude Code) rather than being a finished, production product.

If you are exploring this repo for the first time, read the [What this repo actually is](#what-this-repo-actually-is)
section below — it is not a typical single-purpose app.

---

## Table of Contents

- [What this repo actually is](#what-this-repo-actually-is)
- [Project overview and purpose](#project-overview-and-purpose)
- [Features](#features)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API endpoint summary](#api-endpoint-summary)
- [Development setup](#development-setup)
- [The `.claude/` and `.specify/` tooling](#the-claude-and-specify-tooling)
- [Known limitations](#known-limitations)
- [Contributing guidelines](#contributing-guidelines)
- [Summary](#summary)

---

## What this repo actually is

This repository is **two things layered together**, and it is worth separating them clearly:

1. **A real, runnable backend application** — `backend/`, a Python [FastAPI](https://fastapi.tiangolo.com/)
   service (`PromptLab`) that exposes a REST API for prompts and collections. This is the
   "product" part of the repo.
2. **An AI-assisted engineering workflow scaffold** — the `.claude/` and `.specify/` directories.
   These are **not application code**. They configure
   [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (Anthropic's CLI coding
   assistant) with:
   - **Agents** (`.claude/agents/`) — reusable AI personas with a specific job. Currently there
     is one: `docs-teacher`, a documentation/teaching agent that explains code to beginners
     without modifying it.
   - **Skills** (`.claude/skills/`) — reusable prompt templates/instructions Claude Code can
     invoke, including a `docstring` skill (writes Google-style docstrings) and a full set of
     **Spec Kit** skills (`speckit-specify`, `speckit-plan`, `speckit-tasks`,
     `speckit-implement`, `speckit-clarify`, `speckit-checklist`, `speckit-analyze`,
     `speckit-constitution`, `speckit-converge`, `speckit-taskstoissues`) that implement a
     structured "specify → plan → tasks → implement" development workflow.
   - **Spec Kit project state** (`.specify/`) — templates, scripts, an integration manifest, and
     a project **constitution** (`.specify/memory/constitution.md`) that encodes this project's
     engineering rules (see [Contributing guidelines](#contributing-guidelines)).

In short: if you just want to run an API, you only need `backend/`. If you're curious how the AI
tooling in this repo works, look at `.claude/` and `.specify/`.

There is currently no code in `frontend/` or `specs/` — both only contain placeholder
`.gitkeep` files with comments describing what is planned to go there later (a React/Vite
frontend and feature spec documents, respectively). This project was originally scoped as a
4-week, week-by-week assignment (fix backend bugs → document → add tests/CI → build a
frontend); this README describes what exists **today**, not the full original plan.

---

## Project overview and purpose

The problem PromptLab's backend solves: teams that work with AI prompts (for example, prompts
sent to an LLM like GPT-4 or Claude) tend to lose track of them — they get pasted into Slack
messages, buried in notebooks, or overwritten with no history. PromptLab gives prompts a proper
home:

- Each **prompt** is a stored piece of text (with a title, content, and optional description)
  that can include `{{variable}}`-style placeholders (e.g. `{{code}}`, `{{context}}`) for later
  substitution.
- Prompts can be grouped into **collections** (e.g. "Development", "Marketing").
- Everything is exposed over HTTP as a JSON REST API, so it could be used by a CLI, a script, or
  (eventually) a web frontend.

The storage layer is deliberately simple: an **in-memory Python dictionary**, not a database.
That means all data is lost when the server restarts. This is intentional for the current stage
of the project (see [Known limitations](#known-limitations)) — the architecture (`routes → business
logic/helpers → storage`) is structured so a real database could be swapped in later without
touching the API layer.

---

## Features

Based on what is actually implemented in `backend/app/`:

- **Prompt management** — create, read (single or list), update (full replace via `PUT` or
  partial via `PATCH`), and delete prompts.
- **Prompt templating support** — `extract_variables()` in `backend/app/utils.py` can pull
  `{{variable_name}}` placeholders out of prompt content (used for future template-filling
  features).
- **Prompt content validation** — `validate_prompt_content()` checks that content isn't empty,
  isn't just whitespace, and is at least 10 characters.
- **Collections** — create, read (single or list), and delete groups of prompts.
- **Safe collection deletion** — deleting a collection unlinks (`collection_id = None`) any
  prompts that belonged to it instead of leaving them silently pointing at a deleted collection.
- **Filtering and search** — `GET /prompts` supports filtering by `collection_id` and free-text
  `search` against title/description.
- **Sorting** — prompts are returned newest-first (sorted by `created_at`, descending).
- **Auto-generated interactive API docs** — FastAPI serves Swagger UI at `/docs` automatically
  from the route/model definitions, no extra work needed.
- **Health check endpoint** — `GET /health` for basic liveness checking.
- **CORS enabled for all origins** — convenient for local development with a separate frontend,
  but see the security note in [Known limitations](#known-limitations).
- **Test suite** — `pytest`-based tests in `backend/tests/` covering prompts, collections, and
  their interaction (e.g. what happens to a prompt when its collection is deleted).
- **AI-assisted engineering workflow tooling** — Claude Code agent/skill definitions and a Spec
  Kit setup for spec-driven development (see [The `.claude/` and `.specify/` tooling](#the-claude-and-specify-tooling)).

---

## Repository structure

```
10x-engineer-project-repo/
├── backend/                  # The actual application (Python/FastAPI)
│   ├── main.py                # Entry point — runs the uvicorn server
│   ├── requirements.txt       # Python dependencies
│   ├── ruff.toml               # Lint config
│   ├── Dockerfile              # Backend container image (see Docker section)
│   ├── .dockerignore           # Excludes tests/caches/etc. from the image build context
│   ├── app/
│   │   ├── __init__.py        # Package init, defines __version__
│   │   ├── api.py             # FastAPI route definitions (the HTTP layer)
│   │   ├── models.py          # Pydantic data models (validation/serialization)
│   │   ├── storage.py         # In-memory storage layer (stands in for a DB)
│   │   └── utils.py           # Pure helper functions (sort/filter/search/etc.)
│   └── tests/
│       ├── conftest.py        # pytest fixtures (test client, sample data)
│       └── test_api.py        # API endpoint tests
├── frontend/                  # Empty — reserved for a future React/Vite UI
├── specs/                     # Spec Kit feature specs (in progress)
├── docs/
│   ├── SYSTEM_MODEL.md        # Architecture write-up (routes, data flow, models, storage)
│   ├── prompt-log.md          # Log of prompts used with AI tools while building this repo
│   └── ai-verification-note.md# Notes on mistakes AI made and how they were caught
├── docker-compose.yml           # Backend-only container orchestration (see Docker section)
├── .gitignore
├── config.yaml                 # Editor/model config for an AI course tool (NOT read by the backend)
├── .claude/
│   ├── agents/docs-teacher.md  # Claude Code agent for beginner-friendly code explanations
│   └── skills/                 # Claude Code skills: docstring writer + full Spec Kit skill set
├── .specify/                   # Spec Kit scaffolding: templates, scripts, project constitution
├── .github/workflows/ci.yml    # CI: lint, test, build (backend only, see CI/CD section)
├── README.md                   # This file
```

---

## Prerequisites


- **Python 3.10+**
- **pip** (for installing Python dependencies)
- **Git**
- **Node.js 18+** — only needed if/when the (currently empty) `frontend/` project is built; not
  required to run the backend today.

There is no `.env` file or `.env.example` in this repo, and the backend does not read any
environment variables — no environment configuration is required to run it.

## Installation

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd 10x-engineer-project-repo

# 2. Move into the backend project
cd backend

# 3. (Recommended) create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

The pinned dependencies (`backend/requirements.txt`) are:

| Package      | Version | Purpose                                             |
|--------------|---------|------------------------------------------------------|
| fastapi      | 0.109.0 | Web framework, routing, auto-generated OpenAPI docs  |
| uvicorn      | 0.27.0  | ASGI server that actually runs the FastAPI app       |
| pydantic     | 2.5.3   | Request/response data validation and serialization   |
| pytest       | 7.4.4   | Test runner                                           |
| pytest-cov   | 4.1.0   | Test coverage reporting                              |
| httpx        | 0.26.0  | HTTP client used by FastAPI's `TestClient` in tests  |

---

## Quick Start

From inside `backend/` (with dependencies installed as above):

```bash
python main.py
```

This starts the server with `uvicorn` on `0.0.0.0:8000` with auto-reload enabled
(`backend/main.py` calls `uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)`).

Once running:

- **API base URL:** http://localhost:8000
- **Interactive API docs (Swagger UI):** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

Try it with `curl`:

```bash
# Check the server is alive
curl http://localhost:8000/health

# Create a prompt
curl -X POST http://localhost:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{"title": "Code Review", "content": "Review this code:\n\n{{code}}", "description": "Prompt for AI code review"}'

# List all prompts
curl http://localhost:8000/prompts
```

---

## API endpoint summary

Yes — this project does expose a real HTTP API. It is defined entirely in `backend/app/api.py`
using FastAPI, and interactive documentation (Swagger UI, generated automatically from the
Pydantic models) is available at `/docs` whenever the server is running.

There is no authentication on any endpoint. All requests currently succeed or fail purely based
on payload validity and whether the referenced resource exists.

### Health

| Method | Path      | Description                     |
|--------|-----------|----------------------------------|
| GET    | `/health` | Returns `{"status": "healthy", "version": "..."}` |

### Prompts

| Method | Path                | Description                                                                 |
|--------|---------------------|-------------------------------------------------------------------------------|
| GET    | `/prompts`          | List prompts, newest first. Supports `?collection_id=` and `?search=` query params. |
| GET    | `/prompts/{id}`     | Get a single prompt by ID. Returns `404` if not found.                       |
| POST   | `/prompts`          | Create a prompt. Returns `201`. Validates `collection_id` exists if provided (`400` if not). |
| PUT    | `/prompts/{id}`     | Full update — all fields must be supplied. Refreshes `updated_at`. Returns `404` if the prompt doesn't exist. |
| PATCH  | `/prompts/{id}`     | Partial update — only supplied fields change. Refreshes `updated_at`. Returns `404` if not found. |
| DELETE | `/prompts/{id}`     | Delete a prompt. Returns `204` on success, `404` if not found.               |

Example request body for `POST /prompts` (matches `PromptCreate` in `backend/app/models.py`):

```json
{
  "title": "Code Review Prompt",
  "content": "Review the following code and provide feedback:\n\n{{code}}",
  "description": "A prompt for AI code review",
  "collection_id": null
}
```

Example response for a created prompt (matches `Prompt` in `backend/app/models.py`):

```json
{
  "id": "3fbd6c1a-1e2a-4c9d-9d3e-1a2b3c4d5e6f",
  "title": "Code Review Prompt",
  "content": "Review the following code and provide feedback:\n\n{{code}}",
  "description": "A prompt for AI code review",
  "collection_id": null,
  "created_at": "2026-08-15T12:00:00.000000",
  "updated_at": "2026-08-15T12:00:00.000000"
}
```

### Collections

| Method | Path                   | Description                                                                          |
|--------|------------------------|----------------------------------------------------------------------------------------|
| GET    | `/collections`         | List all collections.                                                                  |
| GET    | `/collections/{id}`    | Get a single collection by ID. Returns `404` if not found.                             |
| POST   | `/collections`         | Create a collection. Returns `201`.                                                    |
| DELETE | `/collections/{id}`    | Delete a collection. Any prompts referencing it have their `collection_id` set to `null` (not silently orphaned, and not cascade-deleted). Returns `204`, or `404` if not found. |

Example request body for `POST /collections` (matches `CollectionCreate`):

```json
{
  "name": "Development",
  "description": "Prompts for development tasks"
}
```

---

## Development setup

### Running locally

See [Quick Start](#quick-start) above — `python main.py` from inside `backend/`, with `--reload`
already enabled for you by `main.py` itself, so code changes are picked up automatically.

### Running tests

```bash
cd backend
pytest tests/ -v
```

Tests live in `backend/tests/` and use FastAPI's `TestClient` (via `httpx`) against the app
directly, with an autouse fixture (`clear_storage` in `backend/tests/conftest.py`) that resets
the in-memory storage before and after every test so tests don't leak state into each other.

For a coverage report (the `pytest-cov` package is included in `requirements.txt` for this):

```bash
pytest tests/ --cov=app -v
```

### Linting / formatting

The backend is linted with [ruff](https://docs.astral-sh/ruff/) (configured in `backend/ruff.toml`,
scoped to `E`/`F`/`I` — pycodestyle errors, Pyflakes, isort). Run it with:

```bash
cd backend
ruff check app tests
```

No formatter or static type checker (e.g. `black`, `mypy`) is configured. Frontend
linting/formatting isn't set up yet since `frontend/` has no code.

### CI/CD

`.github/workflows/ci.yml` runs automatically on every push/PR and currently covers the backend
only:

- **`lint`** — runs `ruff check app tests` in `backend/`
- **`test`** — runs `pytest tests/ --cov=app --cov-fail-under=80` in `backend/`
- **`build`** — runs after `lint` and `test` succeed; builds the `backend/Dockerfile` image (not
  pushed anywhere) to confirm it stays buildable

Frontend test/build jobs aren't configured yet since `frontend/` has no code (see
[What this repo actually is](#what-this-repo-actually-is)).

### Docker

The backend can be built and run as a container. There is a `backend/Dockerfile` (Python
3.12-slim base, installs `backend/requirements.txt`, runs the API via `uvicorn`) and a
`docker-compose.yml` at the repo root that wires it up.

```bash
# From the repo root
docker compose up --build
```

This builds the backend image and starts it, publishing the API on the same port as running it
locally:

- **API base URL:** http://localhost:8000
- **Interactive API docs (Swagger UI):** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

Stop it with:

```bash
docker compose down
```

To build the backend image directly without Compose:

```bash
docker build -t promptlab-backend ./backend
docker run -p 8000:8000 promptlab-backend
```

**Current limitations of the Docker setup** (see [Known limitations](#known-limitations) for the
underlying reasons):

- **Backend only.** `docker-compose.yml` defines just the `backend` service. There is no
  `frontend` service or `frontend/Dockerfile` yet, because `frontend/` has no code to
  containerize — it's still a placeholder (see [What this repo actually is](#what-this-repo-actually-is)).
- **No persistent volume.** The backend still uses in-memory storage (no SQLite/database swap
  has landed yet), so there's nothing to mount a volume for — data does not survive a container
  restart, same as running it directly with `python main.py`.
- **CI builds the image but doesn't push it.** `.github/workflows/ci.yml` has a `build` job that
  runs after linting and tests pass and builds the backend image (to confirm the Dockerfile stays
  buildable), but it doesn't push to a registry — there's nowhere configured to push it to yet.

---

## Known limitations

Documented directly in `docs/SYSTEM_MODEL.md` and `.specify/memory/constitution.md` — worth
being explicit about rather than glossing over:

- **No persistence.** Storage is two plain Python dictionaries (`backend/app/storage.py`).
  Restarting the server deletes all prompts and collections.
- **No authentication or authorization.** Every endpoint is open to anyone who can reach the
  server.
- **CORS is wide open** (`allow_origins=["*"]` in `backend/app/api.py`) — fine for local
  development, not appropriate as-is for a real deployment.
- **No concurrency safety.** There are no locks around the in-memory dictionaries, so concurrent
  requests under a multi-worker/threaded deployment could race.
- **No referential integrity.** A prompt's `collection_id` is a "soft" foreign key with no
  database-level enforcement; the API code (not a database constraint) is what keeps it
  consistent on collection deletion.
- **`get_prompts_by_collection()` in `storage.py` is currently dead code** outside of its use in
  the collection-delete path — flagged here rather than silently left unexplained.
- **No frontend** exists yet (see [Repository structure](#repository-structure)). CI/CD
  (`.github/workflows/ci.yml`: lint, test, build) and a backend-only Docker setup
  (`backend/Dockerfile`, `docker-compose.yml`) do exist — see [Docker](#docker) — but both are
  backend-only until the frontend is built.

---

## Contributing guidelines

There is no `CONTRIBUTING.md` in this repo, but there is a project constitution at
`.specify/memory/constitution.md` that functions as one. Its core, testable rules:

1. **Tests are the source of truth.** `pytest tests/ -v` must pass before a change is considered
   complete — including AI-generated code that merely *looks* correct.
2. **Keep the flat architecture.** Preserve the `routes (api.py) → helpers (utils.py) → storage
   (storage.py)` split. Don't add a database, auth, async I/O, or extra service layers without a
   concrete stated need.
3. **API contract integrity.** Use correct status codes (404 for missing resources, 422 for
   invalid payloads, 2xx for success), always refresh `updated_at` on mutation, and never
   silently orphan child resources on delete.
4. **AI-assisted-development transparency.** If AI materially shaped a change, log the prompt
   and how it was verified in `docs/prompt-log.md`, and record any AI mistake found in
   `docs/ai-verification-note.md`. Treat AI output as a draft until a human has run it against
   the tests and confirmed it matches intent.
5. **Small, spec-driven increments.** Prefer the Spec Kit `specify → plan → tasks → implement`
   flow (via the `.claude/skills/speckit-*` skills) for non-trivial changes, scoped to one
   spec/task at a time.

Practical conventions observed in the actual commit history (`git log`) worth following:

- Commit messages are short, plain-English, present/past-tense descriptions of what changed
  (e.g. `Fixing syntax issues in docs/prompt-log.md`, `Implemented PATCH ednpoint`,
  `Bugs #1 and #2 addressed. SYSYEM_MODEL.md and prompt-logs.md updated`) rather than following a
  strict format like Conventional Commits.
- Documentation (`docs/SYSTEM_MODEL.md`, `docs/prompt-log.md`, `README.md`) is expected to be
  updated in the *same* change as any architecture, route, or setup change — not deferred.
- Bug fixes are expected to reference the specific bug/endpoint and add or update a test that
  would have caught it (see `backend/tests/test_api.py`, which has comments noting exactly which
  bug each assertion guards against).

If you're contributing with Claude Code, note that the `docs-teacher` agent (`.claude/agents/docs-teacher.md`)
explicitly will not modify code — use it for explanations, and a separate coding-focused
workflow (e.g. the Spec Kit skills) for actual implementation.

---

## Summary

- **PromptLab** (`backend/`) is a working Python/FastAPI REST API for storing and organizing AI
  prompt templates and collections, backed by simple in-memory storage (no database yet).
- It exposes a real HTTP API — 11 endpoints across health, prompts, and collections — documented
  above and browsable live at `/docs` once the server is running.
- Run it with `pip install -r requirements.txt` then `python main.py` from `backend/`; test it
  with `pytest tests/ -v`. It can also be run in Docker with `docker compose up --build` (see
  [Docker](#docker)), and `.github/workflows/ci.yml` lints, tests, and builds it on every push/PR.
- The rest of the repo (`.claude/`, `.specify/`, `docs/`, `config.yaml`) is AI-assisted
  engineering tooling and process documentation, not part of the running application — it
  configures Claude Code agents/skills and a Spec Kit spec-driven workflow, and records the
  prompts/decisions used to build this project.
- `frontend/` and `specs/` are placeholders for future work and currently contain no code.
- The project constitution (`.specify/memory/constitution.md`) is the closest thing this repo
  has to formal contributing rules — read it before making non-trivial changes.
