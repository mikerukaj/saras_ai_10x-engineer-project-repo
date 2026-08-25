---

description: "Task list for Complete PromptLab Application"
---

# Tasks: Complete PromptLab Application

**Input**: Design documents from `/specs/001-complete-promptlab-app/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api-contract.md](./contracts/api-contract.md), [quickstart.md](./quickstart.md), [../prompt-versions.md](../prompt-versions.md) (Phase 8 / User Story 5 only), [../tagging-system.md](../tagging-system.md) (Phase 9 / User Story 6 only)

**Tests**: The spec's User Story 2 (P2) makes comprehensive automated test coverage a first-class deliverable (FR-013–FR-017), so test-writing tasks are included as that story's implementation, not as optional TDD scaffolding for the other stories.

**Organization**: Tasks are grouped by user story (per spec.md priorities P1–P4) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- File paths are exact and repo-relative

## Path Conventions

Matches [plan.md](./plan.md)'s Project Structure: `backend/app/`, `backend/tests/` for the existing FastAPI service; `frontend/src/`, `frontend/tests/`, `frontend/e2e/` for the new React/Vite app; `.github/workflows/` and `docker-compose.yml` at the repo root for CI/CD and containerization.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the one new backend dependency and scaffold the (currently empty) frontend project.

- [ ] T001 [P] Add `sqlmodel` to `backend/requirements.txt` and run `cd backend && pip install -r requirements.txt` to verify it installs cleanly
- [ ] T002 Scaffold a Vite + React + TypeScript project in `frontend/` (`package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, placeholder `src/main.tsx`/`src/App.tsx`), replacing the current `frontend/.gitkeep`
- [ ] T003 Configure frontend tooling in `frontend/` — Tailwind CSS (`tailwind.config.js`, `postcss.config.js`, `src/index.css`) and ESLint/Prettier (depends on T002)

**Checkpoint**: `cd frontend && npm run dev` serves an empty app shell; `cd backend && pip install -r requirements.txt` succeeds with `sqlmodel` present.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The persistence swap (FR-011) and the frontend's data/UI scaffolding that every user story builds on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create `backend/app/database.py` with the SQLModel engine and session setup for a SQLite file (depends on T001)
- [ ] T005 Define SQLModel table classes for `Prompt` and `Collection` in `backend/app/database.py`, matching the field tables in [data-model.md](./data-model.md) (depends on T004)
- [ ] T006 Rewrite `backend/app/storage.py`'s internals to use SQLModel/SQLite session queries, preserving the exact public method signatures (`create_prompt`, `get_prompt`, `get_all_prompts`, `update_prompt`, `delete_prompt`, `create_collection`, `get_collection`, `get_all_collections`, `delete_collection`, `get_prompts_by_collection`, `clear`) so `backend/app/api.py` needs no changes (depends on T005)
- [ ] T007 Update `backend/tests/conftest.py` fixtures to reset/reinitialize the SQLite test database between tests (depends on T006)
- [ ] T008 Run `cd backend && pytest tests/ -v` and confirm the existing suite passes unchanged against the new persistence layer (depends on T007)
- [ ] T009 [P] Generate frontend TypeScript types from the backend's OpenAPI schema using `openapi-typescript` into `frontend/src/api/schema.ts`, with a regeneration script added to `frontend/package.json` (depends on T002, T008 for a running backend to introspect)
- [ ] T010 Implement a typed API client wrapper in `frontend/src/api/client.ts` covering every endpoint in [contracts/api-contract.md](./contracts/api-contract.md) (depends on T009)
- [ ] T011 [P] Build shared UI primitives — `Page`, `Card`, `Button`, `LoadingIndicator`, `ErrorMessage` — in `frontend/src/components/` (depends on T003)
- [ ] T012 Configure the TanStack Query provider and app routing shell in `frontend/src/main.tsx` and `frontend/src/App.tsx` (routes for prompt list, prompt detail/edit, collections) (depends on T010, T011)

**Checkpoint**: Backend persists to SQLite behind the unchanged `Storage` interface; frontend has a typed API client, shared primitives, and an empty routed shell. User story implementation can now begin.

---

## Phase 3: User Story 1 - Manage prompts and collections through a web interface (Priority: P1) 🎯 MVP

**Goal**: A prompt engineer can browse, search, create, edit, and delete prompts and collections entirely through the web interface.

**Independent Test**: Open the web interface, create a prompt and a collection, assign the prompt to the collection, edit it, search for it, and delete both — all without touching the API directly.

- [ ] T013 [P] [US1] Build a `PromptContent` component that visually distinguishes `{{variable}}`-style placeholders in `frontend/src/components/PromptContent.tsx`
- [ ] T014 [US1] Build the prompt list page showing each prompt's title, description, and collection in `frontend/src/pages/PromptListPage.tsx` (depends on T012)
- [ ] T015 [US1] Add a search input to the prompt list page wired to `GET /prompts?search=` in `frontend/src/pages/PromptListPage.tsx` (depends on T014)
- [ ] T016 [US1] Add a collection filter dropdown to the prompt list page wired to `GET /prompts?collection_id=` in `frontend/src/pages/PromptListPage.tsx` (depends on T014)
- [ ] T017 [US1] Build the create-prompt form (title, content, optional description/collection) in `frontend/src/pages/PromptCreatePage.tsx`, posting to `POST /prompts` and updating the list without a full page reload (depends on T012)
- [ ] T018 [US1] Build the prompt detail view with placeholder-highlighted content in `frontend/src/pages/PromptDetailPage.tsx` (depends on T013, T012)
- [ ] T019 [US1] Add a one-action copy-to-clipboard control for prompt content in `frontend/src/pages/PromptDetailPage.tsx` (FR-010) (depends on T018)
- [ ] T020 [US1] Build the edit-prompt form in `frontend/src/pages/PromptEditPage.tsx`, saving via `PATCH /prompts/{id}` (depends on T018)
- [ ] T021 [US1] Add a delete-prompt action with an explicit confirmation step in `frontend/src/pages/PromptDetailPage.tsx`, calling `DELETE /prompts/{id}` (depends on T018)
- [ ] T022 [US1] Build the collections page — list, create, delete — in `frontend/src/pages/CollectionsPage.tsx` (depends on T012)
- [ ] T023 [US1] Reflect the collection-delete unassignment behavior (show "No collection") in `frontend/src/pages/PromptListPage.tsx` and `frontend/src/pages/PromptDetailPage.tsx` (depends on T014, T018, T022)

**Checkpoint**: User Story 1 is fully functional and independently testable — the core value of the feature is delivered.

---

## Phase 4: User Story 2 - Trust the application through automated test coverage (Priority: P2)

**Goal**: Automated tests cover backend behavior and every web interface flow, so regressions are caught before shipping.

**Independent Test**: Intentionally break a create-prompt flow or endpoint, confirm the suite fails and identifies the broken behavior, then confirm it passes again once fixed.

- [ ] T024 [P] [US2] Add backend edge-case tests (delete a nonexistent prompt, delete a collection with assigned prompts, data surviving a storage re-init) to `backend/tests/test_api.py`
- [ ] T025 [P] [US2] Add Vitest + React Testing Library unit tests for shared components in `frontend/tests/components/`
- [ ] T026 [P] [US2] Add Vitest integration tests for the search/filter flow in `frontend/tests/pages/PromptListPage.test.tsx` (depends on T015, T016)
- [ ] T027 [P] [US2] Add Vitest integration tests for the create/edit/delete prompt flows in `frontend/tests/pages/PromptCreatePage.test.tsx` and `frontend/tests/pages/PromptEditPage.test.tsx` (depends on T017, T020, T021)
- [ ] T028 [P] [US2] Add Vitest integration tests for the collection create/delete flow in `frontend/tests/pages/CollectionsPage.test.tsx` (depends on T022)
- [ ] T029 [US2] Configure and write contract tests that run the generated API client against a live backend instance in `frontend/tests/contract/api-client.contract.test.ts`, covering create/edit/delete for prompts and collections (depends on T010, T008)
- [ ] T030 [P] [US2] Configure Playwright in `frontend/` (`playwright.config.ts`, `webServer` config to start backend + frontend)
- [ ] T031 [US2] Write a Playwright e2e spec that creates a prompt via the UI and confirms it persists across a reload in `frontend/e2e/create-prompt.spec.ts` (depends on T030, T017)
- [ ] T032 [P] [US2] Write a Playwright e2e spec covering the search/filter/edit/delete prompt journey in `frontend/e2e/prompt-lifecycle.spec.ts` (depends on T030)
- [ ] T033 [P] [US2] Write a Playwright e2e spec covering collection create/delete and prompt unassignment in `frontend/e2e/collection-lifecycle.spec.ts` (depends on T030)
- [ ] T034 [US2] Add `test`, `test:contract`, and `test:e2e` npm scripts to `frontend/package.json` so the full suite runs via documented single commands (FR-017) (depends on T025–T033)

**Checkpoint**: Backend, frontend unit/integration, contract, and end-to-end suites all pass and are each runnable with one documented command.

---

## Phase 5: User Story 3 - Reliable, repeatable deployment via CI/CD and containerization (Priority: P3)

**Goal**: Every proposed change is automatically tested and, if it passes, packaged into a form startable with one command.

**Independent Test**: Propose a change that fails tests and confirm the pipeline blocks packaging; propose a passing change and confirm it's built, tested, packaged, and startable with one command on a clean machine.

- [X] T035 [P] [US3] Write `backend/Dockerfile` (Python 3.10+ base image, install `requirements.txt`, run via `uvicorn`) — done: `python:3.12-slim` base, installs `requirements.txt`, runs `uvicorn app.api:app --host 0.0.0.0 --port 8000`. Verified with a local `docker build`.
- [ ] T036 [P] [US3] ~~Write `frontend/Dockerfile`~~ — **blocked, not attempted**: `frontend/` still only contains a placeholder `.gitkeep` (Phases 1–4, which scaffold the React/Vite app, were never implemented — same gap already noted at T057). There is no `package.json`, build tooling, or source to containerize yet. Revisit once Phase 1–3 land.
- [X] T037 [US3] ~~Write `docker-compose.yml` at the repo root defining `backend` and `frontend` services plus a named volume for the SQLite database file~~ — **implemented with reduced scope**: `docker-compose.yml` defines only a `backend` service (build context `./backend`, port `8000:8000`); no `frontend` service (blocked, see T036) and no named volume (the SQLModel/SQLite persistence swap, Phase 2 T004–T006, was never implemented either — the backend is still in-memory `Storage`, so there's no database file to persist). Both gaps are called out in comments in `docker-compose.yml` itself. Verified with `docker compose build backend` and `docker compose up -d backend` (`/health` returned `200`).
- [X] T038 [US3] ~~Write `.github/workflows/ci.yml` that runs the backend pytest suite, frontend Vitest suite, contract tests, and Playwright e2e suite~~ — **partially pre-existing, partially blocked**: `.github/workflows/ci.yml` already ran `ruff` lint + `pytest --cov` for the backend on every push/PR before this task (unrelated prior work, not part of this feature branch). Frontend Vitest/contract/Playwright jobs are blocked — those suites don't exist because Phases 1–4 (frontend scaffold, US1, US2) were never implemented (same gap as T036). No changes made to the existing lint/test jobs.
- [X] T039 [US3] Add a docker build/package job to `.github/workflows/ci.yml`, gated to run only after the test jobs succeed, building the backend and frontend images — **implemented for backend only**: added a `build` job (`needs: [lint, test]`) using `docker/build-push-action@v6` to build (not push) the backend image, tagged `promptlab-backend:${{ github.sha }}`. No frontend image build (blocked, see T036) — noted in a comment in the workflow.
- [X] T040 [US3] Validate `docker compose up` brings up backend, frontend, and the persistent volume successfully on a clean checkout, per [quickstart.md](./quickstart.md) steps 1–4 — **validated for backend only**: `docker compose up -d backend` starts successfully and `curl http://localhost:8000/health` returns `{"status":"healthy",...}`. No frontend or persistent volume to validate yet (see T036, T037).

**Checkpoint**: A failing change is blocked from packaging; a passing change is built, tested, packaged, and startable with `docker compose up`.

---

## Phase 6: User Story 4 - Polished, cohesive user experience (Priority: P4)

**Goal**: The interface feels consistent, responsive, and forgiving — loading feedback, readable layouts on any screen size, and clear error messages.

**Independent Test**: Walk through every User Story 1 flow while watching for loading feedback, checking desktop and mobile-width (375px) layouts, and triggering error conditions (invalid input, backend unreachable) to confirm messages are clear.

- [ ] T041 [P] [US4] Add visible loading indicators for every backend-dependent action across `frontend/src/pages/*.tsx`, using TanStack Query's loading/fetching state (FR-023) (depends on T023)
- [ ] T042 [P] [US4] Implement non-technical error messages distinguishing invalid input / not found / backend unreachable in `frontend/src/components/ErrorMessage.tsx`, wired into all pages (FR-009) (depends on T023)
- [ ] T043 [P] [US4] Add responsive layout adjustments (no horizontal scrolling at 375px width) across `frontend/src/pages/` and `frontend/src/components/` using Tailwind responsive utilities (FR-024) (depends on T023)
- [ ] T044 [US4] Audit all screens for consistent layout, typography, and color against the shared `Page`/`Card`/`Button` primitives, adjusting `frontend/src/components/` and `frontend/src/pages/` as needed (FR-025) (depends on T041, T042, T043)

**Checkpoint**: All four user stories are complete and independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation across the whole feature.

- [ ] T045 [P] Update `docs/SYSTEM_MODEL.md` to reflect the new frontend, persistence layer, and deployment architecture
- [ ] T046 [P] Update `README.md` with frontend setup, `docker compose` usage, and test commands
- [ ] T047 [P] Log AI-assisted changes in `docs/prompt-log.md` and any discovered mistakes in `docs/ai-verification-note.md` per constitution Principle IV
- [ ] T048 Run the full [quickstart.md](./quickstart.md) validation (steps 1–8) end-to-end on a clean checkout (depends on T040, T044)

---

## Phase 8: User Story 5 - Save and restore prompt versions (Priority: P5)

**Goal**: Every prompt edit is automatically captured as a recoverable version, with browsing, restore, manual checkpoint, and delete actions. Full detail: [specs/prompt-versions.md](../prompt-versions.md).

**Independent Test**: Edit a prompt's content twice via the web interface, open its version history, confirm three versions exist (original plus two edits), restore the first version, and confirm the prompt's current content matches it.

**Note**: Placed last only because it's the lowest priority (P5) — it has no technical dependency on Phase 7 (Polish) and can be implemented any time after User Story 1's prompt detail/edit pages exist.

- [X] T049 [P] [US5] Add `PromptVersion` Pydantic models (`PromptVersion`, `PromptVersionCreate`, `PromptVersionList`) to `backend/app/models.py`, matching the field table in [prompt-versions.md](../prompt-versions.md#data-model-changes-needed)
- [ ] T050 [US5] ~~Add a `PromptVersion` SQLModel table to `backend/app/database.py`~~ — **not applicable as written**: `backend/app/database.py`/SQLModel (Phase 2, T004–T006) was never built, so the backend is still the original in-memory `Storage`. Its intent (versions persisted per-prompt with cascade-delete) was folded directly into T051 below, implemented against `Storage`'s existing `Dict[str, X]`-per-entity pattern instead of a DB table. Revisit as a real task once T004–T006 land.
- [X] T051 [US5] Add version storage methods (`create_version`, `get_version`, `get_versions_by_prompt`, `delete_version`, plus `delete_versions_by_prompt` for cascade delete) to `backend/app/storage.py` (adapted: in-memory `_versions: Dict[str, PromptVersion]`, not a SQLModel table — see T050 note)
- [X] T052 [US5] Update `create_prompt` in `backend/app/api.py` to also create version 1 for the new prompt (depends on T051)
- [X] T053 [US5] Update `update_prompt`/`patch_prompt` in `backend/app/api.py` to snapshot the prompt's pre-update state as a new version whenever `title`, `content`, or `description` changes (FR-026) (depends on T051)
- [X] T054 [US5] Update `delete_prompt` in `backend/app/api.py` to cascade-delete the prompt's versions (FR-029) (depends on T051)
- [X] T055 [US5] Add `GET /prompts/{id}/versions`, `GET /prompts/{id}/versions/{version_id}`, `POST /prompts/{id}/versions`, `POST /prompts/{id}/versions/{version_id}/restore`, and `DELETE /prompts/{id}/versions/{version_id}` endpoints to `backend/app/api.py`, matching [prompt-versions.md](../prompt-versions.md#api-endpoints) (depends on T051)
- [X] T056 [P] [US5] Turn the pre-implementation acceptance suite in `backend/tests/test_prompt_version.py` green (depends on T052, T053, T054, T055) — **done: 36/36 passing.** One test (`test_restore_leaves_collection_id_unchanged`) had a setup bug, not an implementation bug: it used `PUT` for its intervening "edit" step, and `PUT`'s already-verified full-replace semantics (clears an omitted `collection_id`) wiped the collection assignment *before* restore ever ran, breaking the test's own "currently assigned to a collection" precondition for a reason unrelated to restore. Fixed by switching that one call to `PATCH` (partial-update, leaves `collection_id` untouched when omitted) — no assertion was weakened. Full regression: `pytest tests/ --cov=app` → 471 passed, 0 failed; `app/api.py`/`app/models.py` 100%, `app/storage.py` 98% (one defensive branch — `delete_version`'s not-found path — only reachable by calling it directly at the storage layer, since the API always checks existence first; harmless, not a bug).
- [ ] T057 [US5] Regenerate frontend API types (`frontend/src/api/schema.ts`) and extend the typed client in `frontend/src/api/client.ts` to cover the new version endpoints (depends on T055, T010) — **blocked, not attempted**: T010 (typed API client) and everything upstream of it in Phase 1–2 (frontend scaffold) don't exist yet, so T057–T063 remain undone. The backend (T049, T051–T056) is complete and independently usable via HTTP in the meantime.
- [ ] T058 [US5] Build a version history panel on `frontend/src/pages/PromptDetailPage.tsx` listing versions newest-first with number, timestamp, and label (depends on T057, T018)
- [ ] T059 [US5] Build a version detail view showing a past version's full title/content/description, reachable from the history panel (depends on T058)
- [ ] T060 [US5] Add a restore action (with confirmation) wired to `POST /prompts/{id}/versions/{version_id}/restore` (depends on T059)
- [ ] T061 [P] [US5] Add a "save checkpoint" action (optional label input) wired to `POST /prompts/{id}/versions`, and a delete-version action (with confirmation) wired to `DELETE /prompts/{id}/versions/{version_id}` (depends on T058)
- [ ] T062 [P] [US5] Add Vitest tests for the version history panel, restore, checkpoint, and delete flows in `frontend/tests/pages/PromptDetailPage.test.tsx` (depends on T060, T061)
- [ ] T063 [US5] Add a Playwright e2e spec covering edit → view history → restore in `frontend/e2e/prompt-version-history.spec.ts` (depends on T030, T060)

**Checkpoint**: A prompt's edits are automatically recoverable, its history can be browsed and restored, and checkpoint/delete actions work end-to-end.

---

## Phase 9: User Story 6 - Tag prompts for cross-cutting organization (Priority: P6)

**Goal**: Prompts can carry any number of shared, reusable tags — attached via the create/edit form, filterable from the prompt list, and manageable (renamed/deleted) from a dedicated tags view. Full detail: [specs/tagging-system.md](../tagging-system.md).

**Independent Test**: Create two prompts and tag them with a shared tag and a unique tag each, filter the prompt list by the shared tag and confirm both appear, rename the shared tag and confirm both prompts show the new name, then delete one prompt and confirm the shared tag still exists and is still attached to the remaining prompt.

**Note**: Placed last only because it's the lowest priority (P6) — it has no technical dependency on Phase 7/8 and can be implemented any time after User Story 1's prompt create/edit/list pages exist.

- [ ] T064 [P] [US6] Add `Tag` Pydantic models (`Tag`, `TagCreate`, `TagRename`, `TagList`) to `backend/app/models.py`, and add an optional `tags: List[str]` field to `PromptCreate`/`PromptUpdate`/`PromptPatch` and a `tags: List[Tag]` field to `Prompt`, matching [tagging-system.md](../tagging-system.md#data-model-changes-needed)
- [ ] T065 [US6] Add a `Tag` SQLModel table and a `PromptTag` many-to-many join table to `backend/app/database.py` (depends on T064, T005)
- [ ] T066 [US6] Add tag storage methods (`create_tag`, `get_tag`, `get_tag_by_name_case_insensitive`, `get_all_tags_with_counts`, `rename_tag`, `delete_tag`, `set_prompt_tags` with get-or-create-and-link semantics) to `backend/app/storage.py` (depends on T065)
- [ ] T067 [US6] Update `create_prompt`, `update_prompt`, and `patch_prompt` in `backend/app/api.py` to resolve a request's `tags` field via case-insensitive get-or-create and attach it to the prompt (FR-031) (depends on T066)
- [ ] T068 [US6] Update `delete_prompt` in `backend/app/api.py` to remove the deleted prompt's tag links without deleting the `Tag` records (FR-035) (depends on T066)
- [ ] T069 [US6] Add a `tags` query parameter (comma-separated names, OR match) to `list_prompts` in `backend/app/api.py` (FR-032) (depends on T066)
- [ ] T070 [US6] Add `POST /tags`, `GET /tags`, `GET /tags/{tag_id}`, `PATCH /tags/{tag_id}`, and `DELETE /tags/{tag_id}` endpoints to `backend/app/api.py`, matching [tagging-system.md](../tagging-system.md#api-endpoints) (depends on T066)
- [ ] T071 [P] [US6] Add backend tests for case-insensitive tag reuse, rename-collision (`409`), tag/prompt deletion unlinking (not cascading), and the `tags` filter's OR semantics to `backend/tests/test_api.py` (depends on T067, T068, T069, T070)
- [ ] T072 [US6] Regenerate frontend API types (`frontend/src/api/schema.ts`) and extend the typed client in `frontend/src/api/client.ts` to cover the updated `Prompt` shape and new tag endpoints (depends on T070, T010)
- [ ] T073 [P] [US6] Build a tag input component (type-to-create-or-select) in `frontend/src/components/TagInput.tsx`, used in the create and edit prompt forms (depends on T072)
- [ ] T074 [US6] Show a prompt's tags on `frontend/src/pages/PromptListPage.tsx` and `frontend/src/pages/PromptDetailPage.tsx` (depends on T072, T014, T018)
- [ ] T075 [US6] Add a tag filter control to the prompt list page wired to `GET /prompts?tags=` in `frontend/src/pages/PromptListPage.tsx` (FR-032) (depends on T074)
- [ ] T076 [US6] Build a tags management page — list tags with `prompt_count`, rename, delete (with confirmation) — in `frontend/src/pages/TagsPage.tsx` (FR-033, FR-034) (depends on T072, T012)
- [ ] T077 [P] [US6] Add Vitest tests for the tag input component and tags management page in `frontend/tests/components/TagInput.test.tsx` and `frontend/tests/pages/TagsPage.test.tsx` (depends on T073, T076)
- [ ] T078 [US6] Add a Playwright e2e spec covering tag-on-create, filter-by-tag, rename, and delete in `frontend/e2e/prompt-tagging.spec.ts` (depends on T030, T075, T076)

**Checkpoint**: Prompts can be tagged, filtered by tag, and tags can be browsed, renamed, and deleted end-to-end.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational; most tasks also depend on the specific US1 pages/flows they test, so in practice follows US1
- **User Story 3 (Phase 5)**: Depends on Foundational; its CI test-running steps assume US2's test suites exist, so in practice follows US2
- **User Story 4 (Phase 6)**: Depends on US1's pages existing to polish (in practice follows US1; can proceed in parallel with US2/US3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete
- **User Story 5 (Phase 8)**: Depends on Foundational and US1's prompt detail/edit pages (T018, T020); independent of Phases 4–7 otherwise, so it can proceed in parallel with US2/US3/US4/Polish once US1 is done
- **User Story 6 (Phase 9)**: Depends on Foundational and US1's prompt create/edit/list pages (T014, T017, T018, T020); independent of Phases 4–8 otherwise, so it can proceed in parallel with US2/US3/US4/US5/Polish once US1 is done

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — delivers standalone value
- **User Story 2 (P2)**: Tests the flows US1 builds; independently valuable (a red/green suite) but exercises US1's UI, so implement after US1
- **User Story 3 (P3)**: Gates CI on US2's suites; implement after US2
- **User Story 4 (P4)**: Polishes US1's screens; can be implemented in parallel with US2/US3 once US1 is done
- **User Story 5 (P5)**: Adds version history to US1's prompt detail/edit flow; can be implemented in parallel with US2/US3/US4 once US1 is done
- **User Story 6 (P6)**: Adds tagging to US1's prompt create/edit/list flow; can be implemented in parallel with US2/US3/US4/US5 once US1 is done

### Within Each User Story

- Foundational pieces (API client, shared primitives, routing) before page-level work
- List/detail pages before edit/delete actions that depend on them
- Story complete and checkpointed before moving to the next priority

### Parallel Opportunities

- T001 (backend dependency) can run in parallel with T002/T003 (frontend scaffold)
- T009 (type generation) and T011 (shared primitives) can run in parallel once their prerequisites land
- T013 (PromptContent component) can be built in parallel with T014 (list page) before they're wired together
- Within US2: T024–T028 and T030 are independent files and can run in parallel; T032/T033 (e2e specs) can run in parallel once T030 (Playwright config) exists
- Within US3: T035 and T036 (the two Dockerfiles) can run in parallel
- Within US4: T041, T042, T043 touch different concerns and can run in parallel before the consistency audit (T044)
- Phase 7 documentation tasks (T045–T047) can all run in parallel
- Within US5: T049 (models) can start alongside other Phase 4–7 work once Foundational is done; T056 (backend tests) and T061 (checkpoint/delete actions) are independent files and can run in parallel once their prerequisites land
- Within US6: T064 (models) can start alongside other Phase 4–8 work once Foundational is done; T071 (backend tests), T073 (tag input component), and T077 (frontend tests) are independent files and can run in parallel once their prerequisites land

---

## Parallel Example: User Story 1 Kickoff

```bash
# Once Foundational (Phase 2) is complete, launch these together:
Task: "Build PromptContent component in frontend/src/components/PromptContent.tsx"
Task: "Build prompt list page in frontend/src/pages/PromptListPage.tsx"
```

## Parallel Example: User Story 2 Test Suites

```bash
# Once US1 is complete, launch these together:
Task: "Add backend edge-case tests in backend/tests/test_api.py"
Task: "Add Vitest unit tests for shared components in frontend/tests/components/"
Task: "Add Vitest integration tests for search/filter flow in frontend/tests/pages/PromptListPage.test.tsx"
Task: "Configure Playwright in frontend/ (playwright.config.ts)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (persistence swap + frontend scaffold — blocks everything)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Manually run through US1's independent test (create/edit/search/delete prompts and collections via the UI)
5. Demo if ready — this is the first point the project has a usable web interface

### Incremental Delivery

1. Setup + Foundational → SQLite-backed backend, typed API client, routed empty shell
2. Add User Story 1 → validate manually → demo the core web interface (MVP)
3. Add User Story 2 → validate by intentionally breaking and fixing a flow → the suite becomes the safety net
4. Add User Story 3 → validate by pushing a failing then a passing change → CI/CD and `docker compose up` work
5. Add User Story 4 → validate with the desktop/mobile/error-condition walkthrough → polished daily-use experience
6. Phase 7 → documentation and a full quickstart.md pass close out the feature
7. Add User Story 5 → validate by editing a prompt twice, restoring an earlier version, and confirming the pre-restore state is itself recoverable → version history hardens the editing workflow
8. Add User Story 6 → validate by tagging prompts, filtering by tag, renaming a shared tag, and confirming deletes only unlink rather than cascade → cross-cutting organization on top of collections

### Suggested MVP Scope

**User Story 1** alone (Phases 1–3, tasks T001–T023) is the MVP: a working web interface over the existing backend, with data now surviving restarts. Everything after that (tests, CI/CD, polish) hardens and packages that MVP rather than adding new user-facing capability.
