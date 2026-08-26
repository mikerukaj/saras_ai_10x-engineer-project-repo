# Frontend Architecture Specification: PromptLab Web Interface

**Extends**: [001-complete-promptlab-app](./001-complete-promptlab-app/spec.md), and its child specs
[prompt-versions.md](./prompt-versions.md) (User Story 5) and [tagging-system.md](./tagging-system.md)
(User Story 6)

**Created**: 2026-08-25

**Status**: Draft

**Input**: User request to document, in one place: the frontend's screens and their purpose, a
full component inventory (responsibility + props per component), the state management approach,
loading/error/empty state behavior, and the folder structure's organizing principle.

## Purpose and scope

[001's plan.md](./001-complete-promptlab-app/plan.md) and [research.md](./001-complete-promptlab-app/research.md)
already decided *what* the frontend is built with (React + TypeScript + Vite, TanStack Query,
Tailwind CSS, generated API types) and [tasks.md](./001-complete-promptlab-app/tasks.md) already
breaks the work into file-level tasks. This document sits between those two: it is the frontend's
internal architecture — every screen, every component's responsibility and props, how state is
managed, and how loading/error/empty conditions are handled consistently — so that implementation
(and any future frontend work) has one authoritative reference instead of re-deriving these
decisions per task. It does not repeat the backend API contract; see
[contracts/api-contract.md](./001-complete-promptlab-app/contracts/api-contract.md) for that.

**Current backend readiness** (as of this writing, relevant to scope below):
- Prompts, Collections, and Prompt Versions ([prompt-versions.md](./prompt-versions.md)) are
  implemented and live in the backend today.
- Tags ([tagging-system.md](./tagging-system.md)) are **not yet implemented in the backend**
  (`tasks.md` Phase 9, T064–T078, are all still open). The tag-related screens and components
  below are fully specified so frontend work isn't blocked on re-deriving design later, but they
  cannot be wired to a real backend until Phase 9 lands — see the note on each affected item.
- The frontend project itself does not exist yet (`frontend/` is still a placeholder) — this
  document specifies what Phases 1–4, 6, 8, and 9 of `tasks.md` build, not something already
  running.

## Routing

**Decision**: [React Router](https://reactrouter.com/) (v6+), the de facto standard SPA router
for React/Vite projects — not decided in `research.md`, decided here since the screens below
depend on it. Its `useSearchParams` hook is used to hold list-filter state (search term,
collection filter, tag filter) in the URL, which is what makes filtered/searched views shareable
and survivable across navigation without a separate state store (see [State Management](#state-management-approach)).

## Screens

| Route | Page component | Purpose | Backing spec |
|---|---|---|---|
| `/` | `PromptListPage` | Browse all prompts: title, description, collection, tags. Search by keyword, filter by collection and/or tags. Entry point to create/view a prompt. | FR-001, FR-002, US1 AS1–3; FR-032, US6 AS2 |
| `/prompts/new` | `PromptCreatePage` | Create a prompt: title, content, optional description, optional collection, optional tags. | FR-003, US1 AS4; FR-031, US6 AS1 |
| `/prompts/:id` | `PromptDetailPage` | View one prompt's full details (content with `{{variable}}` placeholders highlighted), copy its content, delete it (with confirmation), and — inline on this same screen — browse/restore/checkpoint/delete its version history. | FR-004, FR-006, FR-010, US1 AS6, AS8; FR-027–FR-030, US5 |
| `/prompts/:id/edit` | `PromptEditPage` | Edit an existing prompt's title, content, description, collection, and tags. | FR-005, US1 AS5; FR-031, US6 AS4 |
| `/collections` | `CollectionsPage` | List, create, and delete collections. | FR-007, FR-008, US1 AS7 |
| `/tags` | `TagsPage` | Browse every tag in use with its `prompt_count`, rename a tag, delete a tag. **Blocked on backend Phase 9.** | FR-033, FR-034, US6 AS3 |
| `*` (unmatched) | `NotFoundPage` | Generic "page not found" with a link back to the prompt list — not itself an FR, but the standard fallback every router-based SPA needs so an invalid/stale URL doesn't render blank. | — |

Version history is a **panel within `PromptDetailPage`**, not a separate route — this matches
`tasks.md` T058–T061, which all target `PromptDetailPage.tsx`, and keeps the restore/checkpoint
actions next to the prompt they act on rather than forcing a navigation round-trip.

## Component inventory

Props are given as TypeScript-shaped signatures. Types like `Prompt`, `Collection`,
`PromptVersion`, and `Tag` refer to the generated types in `frontend/src/api/schema.ts` (per
[research.md](./001-complete-promptlab-app/research.md) Decision 5) — not redefined here.

### Shared primitives (`frontend/src/components/`)

| Component | Responsibility | Props |
|---|---|---|
| `AppShell` | Top-level layout: nav bar + main content slot. Every page renders inside it via the router's layout route. | `{ children: ReactNode }` |
| `NavBar` | Top navigation links: Prompts, Collections, Tags. | *(none — reads current route for active-link styling)* |
| `Page` | Per-screen wrapper: page title, consistent padding/max-width. The one place page-level spacing/typography is defined, so every screen looks consistent (FR-025). | `{ title: string; actions?: ReactNode; children: ReactNode }` |
| `Card` | Bordered/padded container used for list rows, form sections, and panels. | `{ children: ReactNode; className?: string }` |
| `Button` | Styled button with consistent variants. | `{ variant?: 'primary' \| 'secondary' \| 'danger'; loading?: boolean; disabled?: boolean; onClick?: () => void; type?: 'button' \| 'submit'; children: ReactNode }` |
| `LoadingIndicator` | Visible loading spinner/state (FR-023). | `{ label?: string }` |
| `ErrorMessage` | Renders one of the three non-technical error kinds the contract distinguishes (FR-009): invalid input, not found, backend unreachable. | `{ kind: 'invalid' \| 'not-found' \| 'unreachable' \| 'unknown'; detail?: string }` |
| `EmptyState` | Generic "nothing here yet" placeholder with an optional call-to-action, used for empty lists (distinct from an error). | `{ message: string; action?: { label: string; onClick: () => void } }` |
| `ConfirmDialog` | Reusable confirmation modal for every destructive action (delete prompt, delete collection, delete version, delete tag) — one implementation instead of four ad hoc confirms, per FR-006's "explicit confirmation step" and the same pattern `tasks.md` calls for on every other delete action. | `{ open: boolean; title: string; message: string; confirmLabel?: string; onConfirm: () => void; onCancel: () => void }` |

### Prompt domain (`frontend/src/components/prompt/`)

| Component | Responsibility | Props |
|---|---|---|
| `PromptContent` | Renders prompt content with `{{variable}}`-style placeholders visually distinguished from surrounding text (FR-004). | `{ content: string }` |
| `PromptListItem` | One row in the prompt list: title, description, collection badge, tag badges, link to detail. | `{ prompt: Prompt }` |
| `PromptFilters` | Search input + collection filter dropdown + tag filter, synced to URL search params. | `{ collections: Collection[]; tags: Tag[]; value: { search: string; collectionId?: string; tagNames: string[] }; onChange: (next: PromptFilterState) => void }` |
| `PromptForm` | The shared create/edit form (title, content, description, collection select, tag input, submit/cancel) used by both `PromptCreatePage` and `PromptEditPage` — one implementation so the two flows can't drift in validation or layout. | `{ initialValue?: Partial<PromptCreate>; submitLabel: string; onSubmit: (value: PromptCreate) => void; submitting: boolean }` |
| `CollectionSelect` | Dropdown for choosing a prompt's collection (including "No collection"). Used inside `PromptForm` and `PromptFilters`. | `{ collections: Collection[]; value: string \| null; onChange: (id: string \| null) => void }` |
| `CopyButton` | One-action copy-to-clipboard control for prompt content (FR-010). | `{ text: string }` |

### Version history (`frontend/src/components/prompt/`) — depends on US5, backend already implemented

| Component | Responsibility | Props |
|---|---|---|
| `VersionHistoryPanel` | Lists a prompt's versions newest-first (number, timestamp, label); hosts the "save checkpoint" action; opens `VersionDetailView` for a selected version. | `{ promptId: string }` |
| `VersionListItem` | One entry in the history list. | `{ version: PromptVersion; onView: () => void }` |
| `VersionDetailView` | Shows one past version's full title/content/description; hosts restore (with `ConfirmDialog`) and delete (with `ConfirmDialog`) actions. | `{ version: PromptVersion; onRestore: () => void; onDelete: () => void; onClose: () => void }` |

### Collection domain (`frontend/src/components/collection/`)

| Component | Responsibility | Props |
|---|---|---|
| `CollectionListItem` | One row on `CollectionsPage`: name, description, prompt count, delete action. | `{ collection: Collection; onDelete: () => void }` |

### Tag domain (`frontend/src/components/tag/`) — **blocked on backend Phase 9**

| Component | Responsibility | Props |
|---|---|---|
| `TagInput` | Type-to-create-or-select multi-tag input used in `PromptForm`. | `{ value: string[]; onChange: (tags: string[]) => void; suggestions: Tag[] }` |
| `TagBadge` | Small chip rendering one tag's name, used on `PromptListItem` and `PromptDetailPage`. | `{ tag: Tag; onRemove?: () => void }` |
| `TagListItem` | One row on `TagsPage`: name, `prompt_count`, rename (inline edit) and delete actions. | `{ tag: Tag; onRename: (name: string) => void; onDelete: () => void }` |

### Pages (`frontend/src/pages/`)

| Page | Composes |
|---|---|
| `PromptListPage` | `Page`, `PromptFilters`, `PromptListItem[]`, `EmptyState` (no prompts / no results), `LoadingIndicator`, `ErrorMessage` |
| `PromptCreatePage` | `Page`, `PromptForm` |
| `PromptDetailPage` | `Page`, `PromptContent`, `CopyButton`, `ConfirmDialog` (delete prompt), `VersionHistoryPanel`, `TagBadge[]` |
| `PromptEditPage` | `Page`, `PromptForm` (pre-filled) |
| `CollectionsPage` | `Page`, `CollectionListItem[]`, create form, `ConfirmDialog` (delete collection), `EmptyState` |
| `TagsPage` | `Page`, `TagListItem[]`, `ConfirmDialog` (delete tag), `EmptyState` |
| `NotFoundPage` | `Page` |

## State management approach

Three kinds of state, deliberately kept separate rather than funneled into one global store:

1. **Server state — TanStack Query** (per [research.md](./001-complete-promptlab-app/research.md) Decision 3).
   All data that lives on the backend (prompts, collections, versions, tags) is read and written
   exclusively through TanStack Query, via custom hooks in `frontend/src/api/hooks.ts` (e.g.
   `usePrompts(filters)`, `usePrompt(id)`, `useCreatePrompt()`, `usePromptVersions(id)`,
   `useCollections()`, `useTags()`) that wrap the typed client from `frontend/src/api/client.ts`.
   Query keys are structured for targeted invalidation, e.g. `['prompts', filters]`,
   `['prompt', id]`, `['prompt', id, 'versions']`, `['collections']`, `['tags']`. A mutation
   (create/edit/delete) invalidates the query keys it affects (e.g. creating a prompt invalidates
   `['prompts', *]`) so the list updates without a full page reload — the behavior US1 Acceptance
   Scenario 4 requires.

2. **URL state — route params and search params.** The prompt list's search term, collection
   filter, and tag filter live in the URL (`useSearchParams`), not component state. This makes
   filtered views bookmarkable/shareable and means navigating away and back (e.g. list → detail →
   back) doesn't silently reset the user's filters. The `:id` route params for detail/edit pages
   are the single source of truth for which prompt is being viewed/edited — no prompt ID is ever
   duplicated into component state.

3. **Local UI state — `useState`/`useReducer` inside components.** Form field values (before
   submit), modal/dialog open state, and any other state with no meaning outside one component
   tree stay local. `PromptForm` owns its own field state, initialized from `initialValue` when
   editing.

**No global client-state library** (Redux, Zustand, Context-based stores) is introduced. The only
state that's genuinely shared across the app is server data, and TanStack Query already owns that
with its own cache — adding a second state layer on top would duplicate it for no benefit, which
constitution Principle II (Simplicity & Flat Architecture) weighs against.

## Loading, error, and empty state behavior

**Loading** (FR-023): every backend-dependent action shows a visible `LoadingIndicator` (initial
page loads) driven by TanStack Query's `isLoading`, or a disabled/spinning `Button`
(`loading` prop, driven by a mutation's `isPending`) for in-flight creates/edits/deletes/restores.
No screen is ever left looking frozen during a request.

**Errors** (FR-009): every failure is routed through `ErrorMessage`, which maps the failure to
exactly one of the three non-technical categories the API contract's
[Error shape](./001-complete-promptlab-app/contracts/api-contract.md#error-shape) section defines
by HTTP status — **never** by parsing the `detail` string:

| Condition | `ErrorMessage` kind | Example screen |
|---|---|---|
| `422` (validation) or a `400` from submitting a bad `collection_id` | `invalid` | Create/edit form shows inline field errors plus a summary |
| `404` | `not-found` | Detail/edit page for a prompt deleted by another client mid-session (spec Edge Cases) |
| Network failure / no response | `unreachable` | Any page, e.g. backend down |
| Anything else (unexpected `5xx`, etc.) | `unknown` | Fallback — a generic "something went wrong" rather than a raw stack trace |

**Empty states** are distinct from errors and from each other — collapsing them into one
generic "no data" message would blur two different situations the spec calls out separately
(Edge Cases: "no prompts match" vs. a genuinely empty system):

- `PromptListPage` with zero prompts *in the system*: `EmptyState` — "No prompts yet" + a
  "Create your first prompt" action.
- `PromptListPage` with prompts but zero matching the current search/collection/tag filter:
  `EmptyState` — "No prompts match your filters," no creation CTA (US6 AS4 for the tag case
  specifically).
- `CollectionsPage` / `TagsPage` with zero collections/tags: same `EmptyState` pattern.
- Version history has no empty state — every prompt has at least one version from the moment it's
  created ([prompt-versions.md](./prompt-versions.md) Assumptions), so `VersionHistoryPanel`
  always renders at least one entry.

## Folder structure

**Organizing principle**: code is grouped by architectural role first (`api/`, `components/`,
`pages/`), and only *within* `components/` by domain (`prompt/`, `collection/`, `tag/`), so a
change to one entity's UI touches one predictable subtree without hunting across role-based and
domain-based folders at the same time.

```text
frontend/src/
├── api/
│   ├── schema.ts        # Generated from the backend's OpenAPI schema (research.md Decision 5)
│   ├── client.ts         # Typed fetch wrapper covering every endpoint (contracts/api-contract.md)
│   └── hooks.ts           # TanStack Query hooks built on client.ts (usePrompts, useTags, etc.)
├── components/
│   ├── AppShell.tsx, NavBar.tsx, Page.tsx, Card.tsx, Button.tsx,
│   │   LoadingIndicator.tsx, ErrorMessage.tsx, EmptyState.tsx, ConfirmDialog.tsx
│   ├── prompt/
│   │   ├── PromptContent.tsx, PromptListItem.tsx, PromptFilters.tsx,
│   │   │   PromptForm.tsx, CollectionSelect.tsx, CopyButton.tsx
│   │   └── VersionHistoryPanel.tsx, VersionListItem.tsx, VersionDetailView.tsx
│   ├── collection/
│   │   └── CollectionListItem.tsx
│   └── tag/
│       └── TagInput.tsx, TagBadge.tsx, TagListItem.tsx
├── pages/
│   ├── PromptListPage.tsx, PromptCreatePage.tsx, PromptDetailPage.tsx,
│   │   PromptEditPage.tsx, CollectionsPage.tsx, TagsPage.tsx, NotFoundPage.tsx
├── App.tsx                # Router + AppShell wiring
└── main.tsx                # Entry point, TanStack Query provider
```

This matches the source tree already laid out in
[001's plan.md](./001-complete-promptlab-app/plan.md#source-code-repository-root) and the file
paths already assigned per-task in
[001's tasks.md](./001-complete-promptlab-app/tasks.md) Phases 3, 4, 6, 8, and 9 — this document
adds the component-level breakdown those tasks operate on, it does not redefine their file
locations.
