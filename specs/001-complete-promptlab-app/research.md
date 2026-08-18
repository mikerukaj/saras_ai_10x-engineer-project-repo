# Research: Complete PromptLab Application

**Input**: [spec.md](./spec.md) — see especially the Clarifications and Assumptions sections, which already resolved the three scope-defining questions (deployment target, persistence, test depth). This document resolves the remaining *technical* choices needed to satisfy those decisions.

## 1. Persistence technology (FR-011, FR-012)

**Decision**: SQLite, accessed via SQLModel (built on SQLAlchemy + Pydantic v2).

**Rationale**:
- The spec requires only that data *survive restarts* (FR-012 explicitly defers the mechanism to planning) — it does not require multi-user write concurrency, a separate DB server, or network access to the data store.
- SQLite is an embedded, file-based engine: no separate service/container to run, start, or fail independently — a direct fit for FR-021's "single command, no separate live environment" deployment target and the constitution's Simplicity & Flat Architecture principle (Principle II).
- SQLModel is built on Pydantic v2, which the backend already uses for `Prompt`/`Collection` (`backend/app/models.py`). This keeps one validation/serialization model system instead of introducing a second (e.g., a separate ORM's declarative models), minimizing new concepts.
- The existing `Storage` class (`backend/app/storage.py`) already exposes the exact method surface (`create_prompt`, `get_prompt`, `get_all_prompts`, `update_prompt`, `delete_prompt`, equivalents for collections, `get_prompts_by_collection`) that `api.py` depends on. Swapping the internals of that class from dict-backed to SQLite-backed — without changing its public interface — means `api.py` requires no changes, preserving API Contract Integrity (Principle III) by construction.

**Alternatives considered**:
- **Raw JSON file with atomic writes**: Simpler dependency footprint (no ORM), but reimplements query/filter logic that SQL already provides, and risks partial-write corruption without careful atomic-replace handling. Rejected: more custom code to get right for equivalent behavior.
- **PostgreSQL in a separate container**: Standard for production multi-user apps, but requires an additional service, network wiring, and credentials management — directly conflicts with the clarified "single command, no separate live environment" deployment scope. Rejected as disproportionate to a single-user/trusted-environment tool.
- **Raw SQLAlchemy (no SQLModel)**: Viable, but means maintaining separate ORM model classes alongside the existing Pydantic models, duplicating field definitions. Rejected in favor of SQLModel's unification.

## 2. Frontend framework and language (spec Assumptions: React/Vite, Node.js 18+)

**Decision**: React + TypeScript, built with Vite.

**Rationale**:
- React/Vite is already the project's documented direction (README "phased plan", constitution Technology Constraints section) — not a new choice, just confirming it.
- TypeScript adds compile-time checking against the backend's data shapes (see contract typing below), which directly supports FR-013–FR-016's testing requirements: a class of bugs (wrong field name, wrong type sent to the API) is caught before tests even run.

**Alternatives considered**:
- **Plain JavaScript**: Less setup, but forgoes compile-time contract checking, which matters more here because the frontend is being built fresh against an existing, already-stable API — type-checking the integration is cheap insurance. Rejected.

## 3. Server-state / data-fetching (supports FR-023 loading indicators, FR-009 error states)

**Decision**: TanStack Query (React Query) for backend data fetching, caching, and request lifecycle state.

**Rationale**: Gives loading/error/success states for every backend call out of the box, which is exactly what FR-009 (distinguish invalid input / not found / unreachable) and FR-023 (visible loading indicator) need, without hand-rolling request state per component.

**Alternatives considered**:
- **Plain `fetch` + component-local `useState`**: Works, but re-implements loading/error/retry bookkeeping in every component; higher risk of an inconsistent UX across screens, which FR-025 (consistent design) explicitly guards against. Rejected in favor of a single, consistent request-state pattern.

## 4. Styling approach (FR-024 responsive, FR-025 consistent design)

**Decision**: Tailwind CSS utility classes plus a small set of shared layout/typography primitives (e.g., a `Page`, `Card`, `Button` wrapper).

**Rationale**: Utility-first CSS keeps styling co-located with markup (easy to audit for consistency) and has first-class responsive breakpoint utilities, directly supporting FR-024's desktop/mobile requirement, without adding a large component-library runtime dependency.

**Alternatives considered**:
- **Full component library (e.g., MUI)**: Faster initial scaffolding, but a heavier dependency and harder to keep visually distinct/lightweight for a small internal tool. Rejected as more than this feature needs.
- **Hand-written CSS/CSS Modules only**: No new dependency, but higher risk of drifting, inconsistent spacing/typography across screens (the exact failure mode FR-025 exists to prevent). Rejected.

## 5. Frontend/backend contract typing

**Decision**: Generate TypeScript types from the backend's existing OpenAPI schema (FastAPI serves this automatically at `/openapi.json`) using `openapi-typescript`, checked in and regenerated as part of the build.

**Rationale**: The backend already defines the contract (see `contracts/api-contract.md`); generating types from it instead of hand-writing a parallel TypeScript interface means the frontend cannot silently drift from what the backend actually returns — a schema change becomes a type error at build time, directly supporting FR-015 (frontend/backend interaction verified).

**Alternatives considered**:
- **Hand-written TypeScript interfaces**: No extra build step, but two independent sources of truth (Pydantic models and hand-written types) that can silently diverge. Rejected.

## 6. Automated test tooling

**Decision**:
- Backend: `pytest` + `pytest-cov` (already in `requirements.txt`), extended with tests for the new persistence layer and the existing endpoints.
- Frontend unit/integration: Vitest + React Testing Library (Vite-native, fast, no separate test runner config).
- Contract tests: integration tests that run the frontend's generated API client against a real running instance of the backend (not a mock), verifying request/response shapes match at runtime — directly satisfies FR-015.
- End-to-end: Playwright, driving a real browser through full user journeys (FR-016) against the fully composed stack (frontend + backend + persistent store).

**Rationale**: Each tool is the standard, actively maintained choice for its layer in the chosen stack (Vite project → Vitest; need real-browser automation → Playwright, which has stronger CI/headless support and built-in multi-browser coverage compared to alternatives). Reusing `pytest` on the backend avoids replacing an already-working, constitution-mandated toolchain (Principle I references `pytest tests/ -v` by name).

**Alternatives considered**:
- **Cypress for E2E**: Popular alternative to Playwright; Playwright was chosen for native multi-browser support and typically faster CI runs. Either would satisfy FR-016; Playwright is the more actively-recommended default as of 2026.
- **Jest for frontend unit tests**: Works with Vite via extra config, but Vitest is Vite-native and requires none of that extra config. Rejected in favor of less setup surface.

## 7. CI/CD platform

**Decision**: GitHub Actions.

**Rationale**: The repository is already hosted and worked with via `git`/`gh` tooling with a `main` branch convention; GitHub Actions requires no new hosting account or credential setup beyond what already exists for the repo, and integrates directly with pull requests to satisfy FR-018/FR-019 (tests run automatically, failing tests block packaging).

**Alternatives considered**:
- **GitLab CI, CircleCI, Jenkins**: All viable, but each requires either a different git host or additional external account/infrastructure setup not implied by anything already in this repo. Rejected as unnecessary given GitHub is already in use.

## 8. Container orchestration for the "single command" run (FR-020, FR-021, FR-022)

**Decision**: A `docker-compose.yml` at the repo root defining two services (`backend`, `frontend`) plus a named volume for the SQLite database file, brought up with `docker compose up`.

**Rationale**: Directly satisfies the clarified deployment scope — one command, no external hosting target — while keeping backend and frontend as separately buildable, separately testable images (each gets its own `Dockerfile`), which matches the existing flat, separated architecture rather than merging them into one container.

**Alternatives considered**:
- **Single combined Dockerfile/image serving both frontend and backend**: Fewer moving parts to start, but couples frontend and backend build/release cycles together and complicates independently testing each in CI. Rejected in favor of two images composed together.

## Summary of resolved unknowns

| Technical Context field | Resolution |
|---|---|
| Storage | SQLite via SQLModel |
| Frontend language/framework | TypeScript + React, built with Vite |
| Server-state management | TanStack Query |
| Styling | Tailwind CSS |
| Contract typing | Generated from OpenAPI schema via `openapi-typescript` |
| Backend testing | pytest + pytest-cov (existing) |
| Frontend unit/integration testing | Vitest + React Testing Library |
| Contract testing | Frontend API client run against a live backend instance |
| End-to-end testing | Playwright |
| CI/CD platform | GitHub Actions |
| Container orchestration | `docker-compose.yml`, two services + one named volume |

No `NEEDS CLARIFICATION` markers remain in the Technical Context.
