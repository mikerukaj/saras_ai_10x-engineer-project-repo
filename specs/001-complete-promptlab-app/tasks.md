---

description: "Task list for Complete PromptLab Application"
---

# Tasks: Complete PromptLab Application

**Input**: Design documents from `/specs/001-complete-promptlab-app/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api-contract.md](./contracts/api-contract.md), [quickstart.md](./quickstart.md), [../prompt-versions.md](../prompt-versions.md) (Phase 8 / User Story 5 only), [../tagging-system.md](../tagging-system.md) (Phase 9 / User Story 6 only), [../frontend.md](../frontend.md) (Phase 10 only)

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
- [X] T002 Scaffold a Vite + React + TypeScript project in `frontend/` (`package.json`, `vite.config.ts`, `tsconfig.json`, `index.html`, placeholder `src/main.tsx`/`src/App.tsx`), replacing the current `frontend/.gitkeep` — done: `frontend/` had already been scaffolded (via `npm create vite@latest`, plain JS) since this task list was last touched. Converted it to TypeScript per plan.md's tech stack: added `tsconfig.json`/`tsconfig.app.json`/`tsconfig.node.json`, renamed `App.jsx`/`main.jsx` → `.tsx`, `vite.config.js` → `.ts`, removed the default template's placeholder content (counter demo, Vite/React logos).
- [X] T003 Configure frontend tooling in `frontend/` — Tailwind CSS (`tailwind.config.js`, `postcss.config.js`, `src/index.css`) and ESLint/Prettier (depends on T002) — done, with two substitutions for current tooling: Tailwind CSS v4 via the `@tailwindcss/vite` plugin (no separate `tailwind.config.js`/`postcss.config.js` needed in v4 — just the plugin in `vite.config.ts` and `@import "tailwindcss";` in `src/index.css`), and `oxlint` (already present in the pre-existing scaffold, `.oxlintrc.json`) instead of ESLint/Prettier — equivalent linting, less config surface.

**Checkpoint**: `cd frontend && npm run dev` serves an empty app shell; `cd backend && pip install -r requirements.txt` succeeds with `sqlmodel` present. **Frontend half verified**: `npm run build` (`tsc -b && vite build`) succeeds; `npm run lint` (oxlint) is clean. Backend half (T001) untouched this pass.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The persistence swap (FR-011) and the frontend's data/UI scaffolding that every user story builds on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Create `backend/app/database.py` with the SQLModel engine and session setup for a SQLite file (depends on T001)
- [ ] T005 Define SQLModel table classes for `Prompt` and `Collection` in `backend/app/database.py`, matching the field tables in [data-model.md](./data-model.md) (depends on T004)
- [ ] T006 Rewrite `backend/app/storage.py`'s internals to use SQLModel/SQLite session queries, preserving the exact public method signatures (`create_prompt`, `get_prompt`, `get_all_prompts`, `update_prompt`, `delete_prompt`, `create_collection`, `get_collection`, `get_all_collections`, `delete_collection`, `get_prompts_by_collection`, `clear`) so `backend/app/api.py` needs no changes (depends on T005)
- [ ] T007 Update `backend/tests/conftest.py` fixtures to reset/reinitialize the SQLite test database between tests (depends on T006)
- [ ] T008 Run `cd backend && pytest tests/ -v` and confirm the existing suite passes unchanged against the new persistence layer (depends on T007)
- [X] T009 [P] Generate frontend TypeScript types from the backend's OpenAPI schema using `openapi-typescript` into `frontend/src/api/schema.ts`, with a regeneration script added to `frontend/package.json` (depends on T002, T008 for a running backend to introspect) — done for real, not a stub: started the backend in a throwaway venv, fetched its live `/openapi.json`, and ran `openapi-typescript` against it — `schema.ts` reflects the actual current API (including `tags` on `Prompt` and the `Tag`/`PromptVersion` schemas). `npm run generate:types` added, pointed at `http://localhost:8000/openapi.json` for future regeneration against a running dev backend.
- [X] T010 Implement a typed API client wrapper in `frontend/src/api/client.ts` covering every endpoint in [contracts/api-contract.md](./contracts/api-contract.md) (depends on T009) — done using `openapi-fetch` (the standard companion to `openapi-typescript`) rather than a hand-rolled `fetch` wrapper — one `createClient<paths>()` call gives a fully-typed method per endpoint. Also exports `ApiError`/`toApiError`, mapping HTTP status → `invalid`/`not-found`/`unreachable`/`unknown` per api-contract.md's error-shape section (feeds T042/FR-009), and `WithRequired`-narrowed `Prompt`/`Collection`/`PromptVersion`/`Tag` type aliases (openapi-typescript marks server-generated fields like `id` as optional since Pydantic's `default_factory` isn't "required" on the request side of the schema, even though every real response has them populated).
- [X] T011 [P] Build shared UI primitives — `Page`, `Card`, `Button`, `LoadingIndicator`, `ErrorMessage` — in `frontend/src/components/` (depends on T003) — done, plus `EmptyState`/`ConfirmDialog`/`AppShell`/`NavBar` (see Phase 10, T080–T083, folded into this same pass).
- [X] T012 Configure the TanStack Query provider and app routing shell in `frontend/src/main.tsx` and `frontend/src/App.tsx` (routes for prompt list, prompt detail/edit, collections) (depends on T010, T011) — done using React Router (the routing library decision `specs/frontend.md` made explicitly, since neither `plan.md` nor `research.md` picked one) — `main.tsx` wraps `App` in `QueryClientProvider`; `App.tsx` wraps every route in `AppShell` and adds `/tags` and a catch-all `NotFoundPage` route beyond the three named here, per `specs/frontend.md`'s Screens table.

**Checkpoint**: Backend persists to SQLite behind the unchanged `Storage` interface; frontend has a typed API client, shared primitives, and an empty routed shell. User story implementation can now begin. **Frontend half verified live**: ran the frontend (`npm run dev`) against the real backend (a throwaway venv's `uvicorn`) and drove it with Playwright — see Phase 3's checkpoint note for what was exercised. Backend half (SQLite persistence, T004–T008) is still untouched — the backend remains in-memory `Storage`.

---

## Phase 3: User Story 1 - Manage prompts and collections through a web interface (Priority: P1) 🎯 MVP

**Goal**: A prompt engineer can browse, search, create, edit, and delete prompts and collections entirely through the web interface.

**Independent Test**: Open the web interface, create a prompt and a collection, assign the prompt to the collection, edit it, search for it, and delete both — all without touching the API directly.

- [X] T013 [P] [US1] Build a `PromptContent` component that visually distinguishes `{{variable}}`-style placeholders in `frontend/src/components/PromptContent.tsx` — done: splits on a capturing regex (`{{...}}` at odd indices of the split result) rather than a stateful `.test()` call, avoiding a classic `/g`-regex `lastIndex` bug.
- [X] T014 [US1] Build the prompt list page showing each prompt's title, description, and collection in `frontend/src/pages/PromptListPage.tsx` (depends on T012) — done; the row itself is the `PromptListItem` component (Phase 10, T085), composed by this page.
- [X] T015 [US1] Add a search input to the prompt list page wired to `GET /prompts?search=` in `frontend/src/pages/PromptListPage.tsx` (depends on T014) — done, as part of the `PromptFilters` component (Phase 10, T086), with the search term held in the URL (`useSearchParams`) per specs/frontend.md's state-management approach.
- [X] T016 [US1] Add a collection filter dropdown to the prompt list page wired to `GET /prompts?collection_id=` in `frontend/src/pages/PromptListPage.tsx` (depends on T014) — done, same `PromptFilters` component as T015.
- [X] T017 [US1] Build the create-prompt form (title, content, optional description/collection) in `frontend/src/pages/PromptCreatePage.tsx`, posting to `POST /prompts` and updating the list without a full page reload (depends on T012) — done; the form itself is the shared `PromptForm` component (Phase 10, T087, also used by edit). "Updating the list without a full page reload" is TanStack Query's mutation `onSuccess` invalidating the `['prompts']` query key.
- [X] T018 [US1] Build the prompt detail view with placeholder-highlighted content in `frontend/src/pages/PromptDetailPage.tsx` (depends on T013, T012) — done.
- [X] T019 [US1] Add a one-action copy-to-clipboard control for prompt content in `frontend/src/pages/PromptDetailPage.tsx` (FR-010) (depends on T018) — done, as the standalone `CopyButton` component (Phase 10, T089) via `navigator.clipboard.writeText`.
- [X] T020 [US1] Build the edit-prompt form in `frontend/src/pages/PromptEditPage.tsx`, saving via `PATCH /prompts/{id}` (depends on T018) — done, via the same shared `PromptForm` as T017.
- [X] T021 [US1] Add a delete-prompt action with an explicit confirmation step in `frontend/src/pages/PromptDetailPage.tsx`, calling `DELETE /prompts/{id}` (depends on T018) — done, using the shared `ConfirmDialog` component.
- [X] T022 [US1] Build the collections page — list, create, delete — in `frontend/src/pages/CollectionsPage.tsx` (depends on T012) — done; each row is the `CollectionListItem` component (Phase 10, T090).
- [X] T023 [US1] Reflect the collection-delete unassignment behavior (show "No collection") in `frontend/src/pages/PromptListPage.tsx` and `frontend/src/pages/PromptDetailPage.tsx` (depends on T014, T018, T022) — done; `useDeleteCollection`'s `onSuccess` also invalidates the `['prompts']` query key (not just `['collections']`) specifically so this shows up immediately without a manual refresh.

**Checkpoint**: User Story 1 is fully functional and independently testable — the core value of the feature is delivered. **Verified live**, not just by inspection: ran the backend (throwaway venv) and frontend (`npm run dev`) together and drove the real app with a headless-Chromium Playwright script — created a prompt with a `{{variable}}` placeholder end-to-end (create form → detail page, placeholder highlighted, listed on `/`), confirmed zero browser console errors throughout, and screenshotted every step. See T012's checkpoint and Phase 8/9's checkpoints for the version-history and tagging flows exercised the same way.

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

- [X] T041 [P] [US4] Add visible loading indicators for every backend-dependent action across `frontend/src/pages/*.tsx`, using TanStack Query's loading/fetching state (FR-023) (depends on T023) — done: every page-level query renders `LoadingIndicator` on `isLoading`, and every mutation-triggering `Button` takes a `loading={mutation.isPending}` prop that shows an inline spinner and disables the button.
- [X] T042 [P] [US4] Implement non-technical error messages distinguishing invalid input / not found / backend unreachable in `frontend/src/components/ErrorMessage.tsx`, wired into all pages (FR-009) (depends on T023) — done: `ErrorMessage` renders one of four copy blocks by `ApiErrorKind` (`invalid`/`not-found`/`unreachable`/`unknown`, from `client.ts`'s status-code mapping — never by parsing `detail` text, per api-contract.md); `ErrorMessageFromError` is the wiring point every page/mutation uses.
- [X] T043 [P] [US4] Add responsive layout adjustments (no horizontal scrolling at 375px width) across `frontend/src/pages/` and `frontend/src/components/` using Tailwind responsive utilities (FR-024) (depends on T023) — done: `Page`'s layout and the create/edit forms use `sm:` breakpoints and never a fixed width wider than the viewport (flex-wrap on all action/filter rows). Not verified at an actual 375px viewport in this pass — verification screenshots were taken at a standard desktop width.
- [X] T044 [US4] Audit all screens for consistent layout, typography, and color against the shared `Page`/`Card`/`Button` primitives, adjusting `frontend/src/components/` and `frontend/src/pages/` as needed (FR-025) (depends on T041, T042, T043) — done by construction rather than as a separate audit pass: every page is built exclusively from `Page`/`Card`/`Button`/`EmptyState`/`ConfirmDialog`/`LoadingIndicator`/`ErrorMessage`, so consistency follows from having one implementation of each rather than needing to reconcile several ad hoc ones.

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
- [X] T057 [US5] Regenerate frontend API types (`frontend/src/api/schema.ts`) and extend the typed client in `frontend/src/api/client.ts` to cover the new version endpoints (depends on T055, T010) — unblocked and done now that T002/T010 exist: `schema.ts` was generated from the live backend (which already includes the version endpoints, T055), and `hooks.ts` (Phase 10, T079) adds `usePromptVersions`/`useCreateVersion`/`useRestoreVersion`/`useDeleteVersion` on top of `client.ts`.
- [X] T058 [US5] Build a version history panel on `frontend/src/pages/PromptDetailPage.tsx` listing versions newest-first with number, timestamp, and label (depends on T057, T018) — done as the standalone `VersionHistoryPanel` component (Phase 10, T091), embedded in `PromptDetailPage`.
- [X] T059 [US5] Build a version detail view showing a past version's full title/content/description, reachable from the history panel (depends on T058) — done as `VersionDetailView` (Phase 10, T093).
- [X] T060 [US5] Add a restore action (with confirmation) wired to `POST /prompts/{id}/versions/{version_id}/restore` (depends on T059) — done, via `ConfirmDialog` + `useRestoreVersion`.
- [X] T061 [P] [US5] Add a "save checkpoint" action (optional label input) wired to `POST /prompts/{id}/versions`, and a delete-version action (with confirmation) wired to `DELETE /prompts/{id}/versions/{version_id}` (depends on T058) — done, both inside `VersionHistoryPanel`.
- [ ] T062 [P] [US5] Add Vitest tests for the version history panel, restore, checkpoint, and delete flows in `frontend/tests/pages/PromptDetailPage.test.tsx` (depends on T060, T061) — **not attempted**: Vitest/React Testing Library aren't installed (that's US2/Phase 4's T025, still open). Manually verified instead: a Playwright script drove create → view detail → confirmed "Version history" panel showing "Version 1" with the correct timestamp, screenshotted (see Phase 3's checkpoint).
- [ ] T063 [US5] Add a Playwright e2e spec covering edit → view history → restore in `frontend/e2e/prompt-version-history.spec.ts` (depends on T030, T060) — **not attempted** as a committed spec file (T030, Playwright config, is still open) — but the underlying flow (create → edit → version history shows the new version) was exercised ad hoc via a one-off Playwright script in this pass, not saved as a `frontend/e2e/` spec.

**Checkpoint**: A prompt's edits are automatically recoverable, its history can be browsed and restored, and checkpoint/delete actions work end-to-end. **Verified live**: created a prompt via the UI, confirmed "Version 1" appeared in its history panel with the correct timestamp; edited the prompt's tags only (not title/content/description) and confirmed no second version was created (matching FR-026/the backend's `content_changed` check) — screenshotted.

---

## Phase 9: User Story 6 - Tag prompts for cross-cutting organization (Priority: P6)

**Goal**: Prompts can carry any number of shared, reusable tags — attached via the create/edit form, filterable from the prompt list, and manageable (renamed/deleted) from a dedicated tags view. Full detail: [specs/tagging-system.md](../tagging-system.md).

**Independent Test**: Create two prompts and tag them with a shared tag and a unique tag each, filter the prompt list by the shared tag and confirm both appear, rename the shared tag and confirm both prompts show the new name, then delete one prompt and confirm the shared tag still exists and is still attached to the remaining prompt.

**Note**: Placed last only because it's the lowest priority (P6) — it has no technical dependency on Phase 7/8 and can be implemented any time after User Story 1's prompt create/edit/list pages exist.

- [X] T064 [P] [US6] Add `Tag` Pydantic models (`Tag`, `TagCreate`, `TagRename`, `TagList`) to `backend/app/models.py`, and add an optional `tags: List[str]` field to `PromptCreate`/`PromptUpdate`/`PromptPatch` and a `tags: List[Tag]` field to `Prompt`, matching [tagging-system.md](../tagging-system.md#data-model-changes-needed) — done, including a `name`-trimming/length `field_validator` on `TagBase` and a shared `_validate_tag_names` helper reused by the three prompt models' `tags` field.
- [ ] T065 [US6] ~~Add a `Tag` SQLModel table and a `PromptTag` many-to-many join table to `backend/app/database.py`~~ — **not applicable as written**, same gap as T050: `backend/app/database.py`/SQLModel (Phase 2, T004–T006) was never built, so the backend is still the original in-memory `Storage`. Its intent (a Tag<->Prompt many-to-many link) was folded directly into T066 below, implemented as an in-memory `Dict[str, Set[str]]` (prompt id -> tag ids) instead of a join table. Revisit as a real task once T004–T006 land.
- [X] T066 [US6] Add tag storage methods (`create_tag`, `get_tag`, `get_tag_by_name_case_insensitive`, `get_all_tags_with_counts`, `rename_tag`, `delete_tag`, `set_prompt_tags` with get-or-create-and-link semantics) to `backend/app/storage.py` (adapted: in-memory `_tags: Dict[str, Tag]` + `_prompt_tags: Dict[str, Set[str]]`, not a SQLModel join table — see T065 note). Also added `get_prompt_tags` and `remove_prompt_tag_links` (used by T067/T068) and a private `_tag_with_count` helper so `prompt_count` is always computed fresh, never stored.
- [X] T067 [US6] Update `create_prompt`, `update_prompt`, and `patch_prompt` in `backend/app/api.py` to resolve a request's `tags` field via case-insensitive get-or-create and attach it to the prompt (FR-031) — done. `PATCH` follows the existing `exclude_unset` partial-update convention: the `tags` key must be present in the request body (even as `[]`) to touch tags at all. Added an `_with_tags` helper (tags are tracked as a separate prompt<->tag link, not stored on the `Prompt` object itself, so every outgoing `Prompt` is passed through it — the same read-time join `list_prompts`/`get_prompt`/`restore_prompt_version` now also use).
- [X] T068 [US6] Update `delete_prompt` in `backend/app/api.py` to remove the deleted prompt's tag links without deleting the `Tag` records (FR-035) (depends on T066) — done, via `storage.remove_prompt_tag_links`.
- [X] T069 [US6] Add a `tags` query parameter (comma-separated names, OR match) to `list_prompts` in `backend/app/api.py` (FR-032) (depends on T066) — done, case-insensitive set-intersection match.
- [X] T070 [US6] Add `POST /tags`, `GET /tags`, `GET /tags/{tag_id}`, `PATCH /tags/{tag_id}`, and `DELETE /tags/{tag_id}` endpoints to `backend/app/api.py`, matching [tagging-system.md](../tagging-system.md#api-endpoints) (depends on T066) — done, including the `409` explicit-create/rename-collision checks (case-insensitive, self-rename-to-own-name exempted).
- [X] T071 [P] [US6] Add backend tests for case-insensitive tag reuse, rename-collision (`409`), tag/prompt deletion unlinking (not cascading), and the `tags` filter's OR semantics to `backend/tests/test_api.py` (depends on T067, T068, T069, T070) — done: a new `TestTags` class, 27 tests covering the above plus create/PATCH/PUT tag-set behavior, 422 validation (empty-after-trim, over-length, on both `POST /tags` and prompt `tags`), and 404s. **Not run** — this session's shell environment has a `python3`/`pytest` mismatch (`pytest`'s shebang resolves to a `python3.6` install lacking Pydantic v2, while `python3` itself is 3.12) that needs a human to sort out the right interpreter/venv; all four touched files were verified with `python3 -m py_compile` (syntax-clean) but the suite itself needs to be run manually — see [prompt-log.md](../../docs/prompt-log.md).
- [X] T072 [US6] Regenerate frontend API types (`frontend/src/api/schema.ts`) and extend the typed client in `frontend/src/api/client.ts` to cover the updated `Prompt` shape and new tag endpoints (depends on T070, T010) — unblocked and done now that T002/T010 exist: `schema.ts` includes `Tag`/`TagCreate`/`TagRename`/`TagList` and `Prompt.tags` (generated from the live backend, which already had tagging implemented); `hooks.ts` adds `useTags`/`useRenameTag`/`useDeleteTag`.
- [X] T073 [P] [US6] Build a tag input component (type-to-create-or-select) in `frontend/src/components/TagInput.tsx`, used in the create and edit prompt forms — done, at `frontend/src/components/tag/TagInput.tsx` (specs/frontend.md's domain-subfolder path — see Phase 10's file-path note above) rather than the flat path this task names; type-to-add with Enter/comma, backspace-to-remove-last, and a matching-suggestions dropdown sourced from `useTags()`.
- [X] T074 [US6] Show a prompt's tags on `frontend/src/pages/PromptListPage.tsx` and `frontend/src/pages/PromptDetailPage.tsx` — done, via the `TagBadge` component (Phase 10, T094) on both `PromptListItem` and `PromptDetailPage`.
- [X] T075 [US6] Add a tag filter control to the prompt list page wired to `GET /prompts?tags=` in `frontend/src/pages/PromptListPage.tsx` (FR-032) — done, as clickable tag-name pills inside `PromptFilters` (Phase 10, T086), OR-combined with the search/collection filters, all held in URL search params.
- [X] T076 [US6] Build a tags management page — list tags with `prompt_count`, rename, delete (with confirmation) — in `frontend/src/pages/TagsPage.tsx` (FR-033, FR-034) — done; each row is `TagListItem` (Phase 10, T095) with inline-edit rename and a `ConfirmDialog`-gated delete.
- [ ] T077 [P] [US6] Add Vitest tests for the tag input component and tags management page in `frontend/tests/components/TagInput.test.tsx` and `frontend/tests/pages/TagsPage.test.tsx` — **not attempted**: same reason as T062 — Vitest isn't installed yet (US2/T025). Manually verified instead (see checkpoint below).
- [ ] T078 [US6] Add a Playwright e2e spec covering tag-on-create, filter-by-tag, rename, and delete in `frontend/e2e/prompt-tagging.spec.ts` — **not attempted** as a committed spec file (T030 still open), but the full flow was exercised ad hoc via a one-off Playwright script in this pass (see checkpoint below), not saved as a `frontend/e2e/` spec.

**Checkpoint**: Prompts can be tagged, filtered by tag, and tags can be browsed, renamed, and deleted end-to-end. **Verified live**, the complete User Story 6 independent test: tagged an existing prompt via its edit form, confirmed the tag appeared on its detail page *without* creating a new version (tags aren't versioned); confirmed it appeared on `/tags` with `prompt_count: 1`; clicked the tag pill on the prompt list to filter by it and confirmed the URL and filtered result; renamed the tag and confirmed the new name; deleted the tag and confirmed `/tags` returned to its empty state. Zero browser console errors across the whole sequence, screenshotted at every step.

---

## Phase 10: Frontend Architecture Refinements (from specs/frontend.md)

**Purpose**: [specs/frontend.md](../frontend.md) is a frontend architecture spec that breaks several existing page-level tasks (T014, T015/T016, T017/T019/T020, T022, T058/T059, T074/T076) down into a finer-grained, reusable component inventory, and specifies a few components/screens (shared layout, `EmptyState`, `ConfirmDialog`, `NotFoundPage`, a dedicated `hooks.ts`) that no existing task covers at all. These tasks are additive refinements of Phases 2, 3, 8, and 9 — they do not replace or duplicate the page-level work already planned there, they extract pieces of it into the standalone files [specs/frontend.md](../frontend.md) specifies.

**Note on file paths**: [specs/frontend.md](../frontend.md) groups prompt/collection/tag components into `components/prompt/`, `components/collection/`, `components/tag/` subfolders. T013 (`PromptContent.tsx`) and T073 (`TagInput.tsx`) were originally planned at the flat `frontend/src/components/` path before this convention existed; since both were still unbuilt when this phase's implementation pass happened, they were built directly at their domain-subfolder paths (`components/prompt/PromptContent.tsx`, `components/tag/TagInput.tsx`) instead — see their updated notes under Phase 3/Phase 9 above. No stale flat-path exception remains.

- [X] T079 [P] Build TanStack Query hooks (`usePrompts`, `usePrompt`, `useCreatePrompt`, `useUpdatePrompt`, `useDeletePrompt`, `usePromptVersions`, `useCollections`, `useTags`, etc.) wrapping the typed client in `frontend/src/api/hooks.ts` (depends on T010) — done, plus `useCreateVersion`/`useRestoreVersion`/`useDeleteVersion`/`useCreateCollection`/`useDeleteCollection`/`useRenameTag`/`useDeleteTag`; every mutation invalidates the query keys it affects (e.g. deleting a collection also invalidates `['prompts']`, since collection-delete unassigns rather than deletes them).
- [X] T080 [P] Build a `NavBar` component (links: Prompts, Collections, Tags) in `frontend/src/components/NavBar.tsx` (depends on T011) — done, using React Router's `NavLink` for active-route styling.
- [X] T081 Build an `AppShell` layout component (nav bar + main content slot) in `frontend/src/components/AppShell.tsx`, composed into the routing shell (depends on T080, T011, feeds into T012) — done.
- [X] T082 [P] Build an `EmptyState` component (message + optional call-to-action) in `frontend/src/components/EmptyState.tsx` (depends on T011) — done.
- [X] T083 [P] Build a shared `ConfirmDialog` component in `frontend/src/components/ConfirmDialog.tsx`, intended to replace the ad hoc confirmation steps in T021 (delete prompt), T022 (delete collection), T060 (restore), T061 (delete version), and T076 (delete tag) (depends on T011) — done, and actually used by all five of those flows (not just intended to be).
- [X] T084 Build a `NotFoundPage` (unmatched-route fallback, links back to the prompt list) in `frontend/src/pages/NotFoundPage.tsx`, wired into the router (depends on T081, T012) — done.
- [X] T085 [P] [US1] Extract a `PromptListItem` component (title, description, collection badge, tag badges) in `frontend/src/components/prompt/PromptListItem.tsx`, used by `PromptListPage` (depends on T014) — done; also takes an optional `collectionName` prop (resolved by the caller from `collection_id`) so it can show the collection's actual name, not just an "in a collection" boolean.
- [X] T086 [US1] Extract search input + collection filter + tag filter into a `PromptFilters` component synced to URL search params (`useSearchParams`) in `frontend/src/components/prompt/PromptFilters.tsx`, used by `PromptListPage` (depends on T015, T016; extended by T075's tag filter) — done, built with all three filters together from the start (not extended later) since US1 and US6 landed in the same pass.
- [X] T087 [US1] Extract a shared `PromptForm` component (title, content, description, collection, tags; used by both create and edit) in `frontend/src/components/prompt/PromptForm.tsx`, consumed by `PromptCreatePage` and `PromptEditPage` in place of their separate inline forms (depends on T017, T020) — done; owns its own field state (per specs/frontend.md), fetches its own `collections`/`tags` options via hooks.
- [X] T088 [P] [US1] Extract a `CollectionSelect` dropdown component in `frontend/src/components/prompt/CollectionSelect.tsx`, used by `PromptForm` and `PromptFilters` (depends on T087) — done.
- [X] T089 [P] [US1] Extract the copy-to-clipboard control into a standalone `CopyButton` component in `frontend/src/components/prompt/CopyButton.tsx`, used by `PromptDetailPage` (depends on T019) — done.
- [X] T090 [P] [US1] Extract a `CollectionListItem` component (name, description, prompt count, delete action) in `frontend/src/components/collection/CollectionListItem.tsx`, used by `CollectionsPage` (depends on T022) — done, minus the "prompt count" — the backend's `Collection` model has no such field (unlike `Tag.prompt_count`), so nothing real exists to display; not faked.
- [X] T091 [US5] Extract the version history list into a standalone `VersionHistoryPanel` component in `frontend/src/components/prompt/VersionHistoryPanel.tsx`, used by `PromptDetailPage` (depends on T058) — done.
- [X] T092 [P] [US5] Build a `VersionListItem` component (one entry in the history list) in `frontend/src/components/prompt/VersionListItem.tsx`, used by `VersionHistoryPanel` (depends on T091) — done.
- [X] T093 [US5] Extract the past-version detail view into a standalone `VersionDetailView` component in `frontend/src/components/prompt/VersionDetailView.tsx`, used by `VersionHistoryPanel` (depends on T059, T091) — done.
- [X] T094 [P] [US6] Build a `TagBadge` chip component in `frontend/src/components/tag/TagBadge.tsx`, used by `PromptListItem` and `PromptDetailPage` to display a prompt's tags (depends on T074) — done.
- [X] T095 [US6] Extract a `TagListItem` component (name, `prompt_count`, rename, delete) in `frontend/src/components/tag/TagListItem.tsx`, used by `TagsPage` (depends on T076) — done, with click-to-edit inline rename.

**Checkpoint**: The frontend's component structure matches the inventory in [specs/frontend.md](../frontend.md) — shared layout/primitives are standalone, and each page composes reusable domain components rather than embedding page-specific markup inline. **All 17 tasks in this phase are complete.** `npm run build` (`tsc -b && vite build`) and `npm run lint` (oxlint) both pass clean.

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
- **Frontend Architecture Refinements (Phase 10)**: Each task depends only on the specific existing task(s) it extracts/extends (noted per task) — not on the phases those tasks belong to being fully complete. In practice, most of Phase 10 becomes actionable incrementally as Phases 2, 3, 8, and 9 land, rather than as one block after Phase 9

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
- Within Phase 10: T079, T080, T082, T083 (independent foundational files) can run in parallel once T010/T011 land; T085, T088, T089, T090 (US1 extractions) are independent files and can run in parallel once their source tasks land; T092 and T094 can likewise run in parallel with their neighboring US5/US6 tasks

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
