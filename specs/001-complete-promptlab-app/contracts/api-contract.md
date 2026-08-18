# Contract: Backend REST API (consumed by the frontend)

**Source of truth**: `backend/app/api.py` and `backend/app/models.py` — this document summarizes the *existing, already-implemented* contract the frontend integrates against. Per spec Assumption ("this feature does not assume new backend capabilities beyond what the acceptance scenarios above require"), no endpoints are added or changed by this feature; the persistence-layer change (see [data-model.md](../data-model.md)) is required to be invisible at this contract level (API Contract Integrity, constitution Principle III).

The backend also serves a live, authoritative machine-readable version of this contract at `GET /openapi.json` (FastAPI auto-generated) — this is what `openapi-typescript` (see research.md Decision 5) generates frontend types from. This document is the human-readable index into that same contract, annotated with which spec user story / FR each endpoint supports.

## Health

| Method | Path | Response | Supports |
|---|---|---|---|
| GET | `/health` | `200 { status, version }` | Operational check (not directly user-facing; useful for e2e/CI smoke checks, FR-016 style) |

## Prompts

| Method | Path | Request | Response | Supports |
|---|---|---|---|---|
| GET | `/prompts` | Query: `collection_id?`, `search?` | `200 { prompts: Prompt[], total }` | FR-001, FR-002 (list, search, collection filter) |
| GET | `/prompts/{prompt_id}` | — | `200 Prompt` \| `404` | FR-004 (prompt detail view) |
| POST | `/prompts` | `PromptCreate` body | `201 Prompt` \| `400` (bad `collection_id`) \| `422` (invalid body) | FR-003 (create) |
| PUT | `/prompts/{prompt_id}` | `PromptUpdate` body (full replace) | `200 Prompt` \| `404` \| `400` \| `422` | FR-005 (edit — full replace) |
| PATCH | `/prompts/{prompt_id}` | `PromptPatch` body (partial) | `200 Prompt` \| `404` \| `400` \| `422` | FR-005 (edit — partial; frontend should prefer this for single-field edits) |
| DELETE | `/prompts/{prompt_id}` | — | `204` \| `404` | FR-006 (delete, with frontend-side confirmation step) |

## Collections

| Method | Path | Request | Response | Supports |
|---|---|---|---|---|
| GET | `/collections` | — | `200 { collections: Collection[], total }` | FR-007 (list, and populate collection filter/assignment UI) |
| GET | `/collections/{collection_id}` | — | `200 Collection` \| `404` | Supporting detail lookups if needed |
| POST | `/collections` | `CollectionCreate` body | `201 Collection` \| `422` | FR-007 (create) |
| DELETE | `/collections/{collection_id}` | — | `204` \| `404` | FR-007 (delete); backend already unassigns affected prompts before deleting, satisfying FR-008 without frontend-side special-casing |

## Prompt Versions

Added by the [prompt version history feature](../../prompt-versions.md) — see that document for
full request/response shapes and error conditions. Summary:

| Method | Path | Request | Response | Supports |
|---|---|---|---|---|
| GET | `/prompts/{prompt_id}/versions` | — | `200 { versions: PromptVersion[], total }` \| `404` | FR-027 (browse history) |
| GET | `/prompts/{prompt_id}/versions/{version_id}` | — | `200 PromptVersion` \| `404` | FR-027 (inspect a past version) |
| POST | `/prompts/{prompt_id}/versions` | `{ label? }` | `201 PromptVersion` \| `404` \| `422` | FR-030 (manual checkpoint) |
| POST | `/prompts/{prompt_id}/versions/{version_id}/restore` | — | `200 Prompt` \| `404` | FR-028 (restore) |
| DELETE | `/prompts/{prompt_id}/versions/{version_id}` | — | `204` \| `404` | FR-030 (prune history) |

`POST /prompts` and `DELETE /prompts/{id}` (above) gain non-breaking side effects — creating
version 1 on prompt creation, and cascade-deleting versions on prompt deletion, respectively —
with no change to their existing request/response shapes.

## Tags

Added by the [prompt tagging feature](../../tagging-system.md) — see that document for full
request/response shapes and error conditions. Summary:

| Method | Path | Request | Response | Supports |
|---|---|---|---|---|
| GET | `/tags` | — | `200 { tags: Tag[], total } ` | FR-033 (browse tags with usage counts) |
| GET | `/tags/{tag_id}` | — | `200 Tag` \| `404` | Supporting detail lookups if needed |
| POST | `/tags` | `{ name }` | `201 Tag` \| `409` (name collision) \| `422` | CRUD symmetry (explicit tag creation) |
| PATCH | `/tags/{tag_id}` | `{ name }` | `200 Tag` \| `404` \| `409` \| `422` | FR-034 (rename, applies everywhere) |
| DELETE | `/tags/{tag_id}` | — | `204` \| `404` | FR-034 (delete, unassigns rather than cascades) |

`GET /prompts` gains an optional `tags` query parameter (comma-separated names, OR match,
combinable with the existing `collection_id`/`search` params) — FR-032. `POST /prompts`,
`PUT /prompts/{id}`, and `PATCH /prompts/{id}` gain an optional `tags` request field (tag name
strings, resolved via case-insensitive get-or-create) — FR-031. Every `Prompt` response object
(list and detail) now includes a `tags: Tag[]` field. `DELETE /prompts/{id}` gains a non-breaking
side effect — removing the deleted prompt's tag links without deleting the `Tag` records — with
no change to its existing `204`/`404` shape.

## Data shapes referenced above

Defined in `backend/app/models.py` (already documented there with Google-style docstrings):

- `Prompt` / `PromptCreate` / `PromptUpdate` / `PromptPatch` — see [data-model.md](../data-model.md) for the field table.
- `Collection` / `CollectionCreate` — see [data-model.md](../data-model.md).
- `PromptList { prompts, total }`, `CollectionList { collections, total }`, `HealthResponse { status, version }` — thin response wrappers, unchanged.

## Error shape

All error responses use FastAPI's default `HTTPException` JSON shape: `{ "detail": "<message>" }`, with status codes `400` (bad `collection_id` reference), `404` (resource not found), or `422` (request body fails Pydantic validation — FastAPI's default behavior, not custom-coded). The frontend's error-handling (spec FR-009) MUST distinguish these three cases by status code, not by parsing `detail` text.

## Frontend consumption notes

- **Search** (`GET /prompts?search=`) matches only `title` and `description`, not `content` — the frontend should not imply full-text search over prompt bodies (matches documented backend behavior, not a defect to work around).
- **`collection_id` on prompts is a soft reference** — the frontend does not need to handle a "collection not found" error when merely *displaying* a prompt's collection (the backend never returns a dangling reference after the FR-008 unassignment behavior); the `400` "Collection not found" case only applies when the frontend itself submits an invalid `collection_id` on create/update.
- **No authentication headers are required or supported** — per spec Assumption, requests are unauthenticated.
