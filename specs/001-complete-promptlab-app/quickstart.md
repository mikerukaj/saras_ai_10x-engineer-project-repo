# Quickstart: Validating the Complete PromptLab Application

This guide proves the feature works end-to-end once implemented. It exercises the deployment path (User Story 3), the persisted data path (FR-011), and the core web interface (User Story 1). Full implementation-level detail belongs in `tasks.md`, not here.

## Prerequisites

- Docker and Docker Compose installed (the only documented prerequisite, per FR-021/SC-005).
- No other local setup (no manually-installed Python/Node versions required to *run* the packaged app — those are only needed for local development, listed separately below).

## 1. Start the full stack with one command

```bash
docker compose up
```

**Expected outcome**: the backend, frontend, and persistent data store (SQLite, via a named volume — see [research.md](./research.md) Decision 1) all start, with no manual follow-up steps. This validates FR-020, FR-021, FR-022, and SC-005.

## 2. Confirm the backend is healthy

```bash
curl http://localhost:8000/health
```

**Expected outcome**: `200 { "status": "healthy", ... }` (see [contracts/api-contract.md](./contracts/api-contract.md)).

## 3. Confirm the frontend loads

Open the frontend's served URL (printed by `docker compose up`) in a browser. **Expected outcome**: the prompt list view loads and shows either existing prompts or an empty state — no error screen.

## 4. Create a prompt and verify it persists across a restart

1. In the web interface, create a new prompt (title + content required). **Expected**: it appears in the list without a full page reload (User Story 1, Acceptance Scenario 4).
2. Stop the stack: `docker compose down` (not `-v`, so the named volume is kept).
3. Restart it: `docker compose up`.
4. Reload the web interface. **Expected**: the prompt created in step 1 is still present. This validates FR-011 and SC-008 (the behavior this feature added beyond the original in-memory-only backend).

## 5. Exercise the core user flows

Walk through User Story 1's acceptance scenarios directly in the browser: search, filter by collection, edit a prompt, delete a prompt, create a collection, delete a collection with prompts assigned to it (confirm those prompts remain, now unassigned — FR-008).

## 6. Run the automated test suites

From the repo root (local development prerequisites: Python 3.10+, Node.js 18+ — only needed to run these, not to run the packaged app):

```bash
# Backend unit/integration tests
cd backend && pytest tests/ -v

# Frontend unit/integration tests
cd frontend && npm test

# Contract tests (frontend API client against a live backend)
cd frontend && npm run test:contract

# End-to-end tests (full stack, real browser)
cd frontend && npm run test:e2e
```

**Expected outcome**: all four suites pass. This validates FR-013–FR-017 and SC-003.

## 7. Confirm the CI/CD gate

Push a change that intentionally breaks a test (e.g., an assertion in `backend/tests/test_api.py`) to a branch and open a pull request. **Expected outcome**: the GitHub Actions pipeline (see [research.md](./research.md) Decision 7) runs automatically and reports failure; the change is visibly blocked from being merged. This validates FR-018 and FR-019/SC-004. Revert the intentional break to confirm the pipeline goes green and the change becomes packageable.

## 8. Spot-check UX polish

While repeating step 5, watch for: a loading indicator during each backend request (FR-023), no horizontal scrolling at a 375px-wide browser window (FR-024, SC-006), and a plain-language (not stack-trace) error message when you temporarily stop the backend container and retry an action (FR-009).
