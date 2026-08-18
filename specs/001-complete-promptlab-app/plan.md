# Implementation Plan: Complete PromptLab Application

**Branch**: `001-complete-promptlab-app` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-complete-promptlab-app/spec.md`

## Summary

PromptLab currently has a working, tested-at-the-API-level FastAPI backend (`backend/app/`) with no frontend, no persistence beyond an in-memory dict, and no CI/CD or containerization. This plan covers completing the project: a React/TypeScript web interface consuming the existing REST API unchanged; swapping the backend's in-memory storage for SQLite (behind the same `Storage` interface, so `api.py` is untouched); comprehensive automated tests (backend unit/integration, frontend unit/integration, frontend↔backend contract tests, and full end-to-end browser tests); and a GitHub Actions CI/CD pipeline that gates on those tests and packages both services as Docker images brought up together with a single `docker compose up`. Per the spec's resolved clarifications, "deployment" here means a reliable local/self-hosted one-command run — not provisioning a live hosted environment.

## Technical Context

**Language/Version**: Backend: Python 3.10+ (existing, per `backend/requirements.txt` and constitution). Frontend: TypeScript, Node.js 18+.

**Primary Dependencies**: Backend: FastAPI, Pydantic v2, uvicorn (existing) + SQLModel (new, for persistence — research.md Decision 1). Frontend: React, Vite, TanStack Query, Tailwind CSS, `openapi-typescript` (research.md Decisions 2–5).

**Storage**: SQLite, accessed via SQLModel, one file persisted in a named Docker volume (research.md Decision 1). Replaces the current in-memory dict inside `backend/app/storage.py` without changing that module's public interface.

**Testing**: Backend: pytest + pytest-cov (existing). Frontend unit/integration: Vitest + React Testing Library. Contract: frontend API client run against a live backend instance. End-to-end: Playwright. (research.md Decision 6)

**Target Platform**: Any Docker-capable host (Linux/macOS/Windows via Docker Engine or Docker Desktop) — no specific server OS assumed, since the resolved deployment scope is a local/self-hosted one-command run, not a specific hosting platform.

**Project Type**: Web application (frontend + backend), matching the spec-template's Option 2 structure.

**Performance Goals**: No explicit throughput/concurrency target — the spec's Assumptions scope this as a single-user/trusted-environment tool. The only timing-bound success criteria are user-task-completion times (SC-001 locate+copy a prompt in <30s, SC-002 create a prompt in <1min), which are UX/interaction-design outcomes, not backend performance targets.

**Constraints**:
- Preserve the existing backend three-layer split (`api.py` → `utils.py` → `storage.py`) per constitution Principle II — the persistence change must live entirely inside `storage.py`'s internals.
- Preserve the existing REST contract exactly (constitution Principle III; see [contracts/api-contract.md](./contracts/api-contract.md)) — no endpoint, status code, or behavior changes as a side effect of this feature.
- No authentication (spec Assumption).
- Single command to bring up the full stack (FR-021); no live hosted environment provisioned (spec Clarifications).

**Scale/Scope**: Single-user/small-team scale; no defined concurrent-user target. Four prioritized user stories (P1–P4) covering: web UI CRUD for prompts/collections, automated test coverage, CI/CD + containerized deployment, and UX polish.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked below after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Test-Verified Changes (NON-NEGOTIABLE) | **PASS** | `pytest tests/ -v` remains the backend gate and is extended, not replaced. New frontend/contract/e2e suites are additive (research.md Decision 6). CI (FR-018/FR-019) enforces this automatically rather than relying on developer discipline alone. |
| II. Simplicity & Flat Architecture | **PASS, with one documented deviation** | The `api.py → utils.py → storage.py` split is preserved unchanged; the frontend is a new, separate project already anticipated in the constitution's own Technology Constraints section. The one real deviation — introducing a database dependency (SQLite/SQLModel) — is exactly the kind of complexity Principle II says needs justification; see Complexity Tracking below. It is justified by FR-011, which the constitution's own "until a concrete, stated requirement needs them" escape hatch anticipates. |
| III. API Contract Integrity | **PASS** | No endpoint signatures, status codes, or behaviors change. The persistence swap is designed (data-model.md, contracts/api-contract.md) to be invisible at the HTTP contract level — `Storage`'s public method signatures are preserved exactly. |
| IV. AI-Assisted Development Transparency | **PASS (procedural)** | Not a design-time gate; carried forward as a task-level requirement (prompt log and AI-verification-note updates during implementation, per existing project practice). |
| V. Incremental, Spec-Driven Change | **PASS** | This plan follows specify → plan → (next: tasks) → implement. The spec's four user stories are independently testable/deliverable slices, enabling `/speckit-tasks` to sequence work incrementally rather than as one big-bang change. |

**Result**: No unjustified violations. One documented, spec-justified complexity addition (see below). Gate passes.

## Project Structure

### Documentation (this feature)

```text
specs/001-complete-promptlab-app/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── api-contract.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api.py            # Existing — HTTP routes; unchanged by this feature
│   ├── models.py         # Existing — Pydantic models; unchanged shape, may gain SQLModel table mapping
│   ├── storage.py         # Existing — public interface unchanged; internals swap dict → SQLite/SQLModel
│   ├── utils.py           # Existing — unchanged
│   └── database.py        # New — SQLModel engine/session setup for the persistence layer
├── tests/
│   └── test_api.py        # Existing — extended with persistence-aware and edge-case coverage
├── requirements.txt        # Existing — gains sqlmodel
├── main.py                 # Existing — unchanged
└── Dockerfile               # New — backend container image

frontend/
├── src/
│   ├── api/                # New — generated types (openapi-typescript) + typed client
│   ├── components/         # New — shared UI primitives (Page, Card, Button, LoadingIndicator, ErrorMessage)
│   ├── pages/               # New — prompt list, prompt detail/edit, collection views
│   └── App.tsx, main.tsx    # New — app shell/routing
├── tests/                    # New — Vitest + React Testing Library unit/integration tests
│   └── contract/              # New — frontend API client tests run against a live backend
├── e2e/                        # New — Playwright end-to-end specs
├── package.json, vite.config.ts, tsconfig.json   # New
└── Dockerfile                                     # New — frontend container image

.github/
└── workflows/
    └── ci.yml              # New — runs all test suites; blocks packaging on failure (FR-018/FR-019)

docker-compose.yml           # New — brings up backend + frontend + persistent volume with one command
```

**Structure Decision**: Web application layout (frontend/ + backend/ as sibling top-level projects), matching what already exists in the repo (`backend/` populated, `frontend/` currently a placeholder) and the constitution's Technology Constraints section, which already anticipates this split. No new top-level directories beyond `.github/workflows/` and `docker-compose.yml` at the repo root, both required directly by the CI/CD and single-command deployment requirements (FR-018–FR-022).

## Complexity Tracking

> Constitution Principle II requires justification for complexity beyond the current flat architecture.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Introducing a database dependency (SQLite via SQLModel) where none existed before | Spec FR-011 (resolved via user clarification) requires prompt/collection data to survive an application restart or redeployment — the current in-memory dict cannot satisfy this by definition | A raw JSON file with atomic writes was considered (research.md Decision 1) but rejected: it reimplements query/filtering logic SQL already provides and adds custom atomic-write correctness risk for no simplicity gain over an embedded, zero-ops SQLite file |
