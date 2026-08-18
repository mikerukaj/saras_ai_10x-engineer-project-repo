# Data Model: Complete PromptLab Application

**Input**: [spec.md](./spec.md) Key Entities section, Functional Requirements, and [research.md](./research.md) decision to persist via SQLite/SQLModel.

This document describes the persisted shape of the two entities already defined (as Pydantic models, in-memory only) in `backend/app/models.py`. The API-facing shape of these entities does **not** change — only where and how they're stored — per API Contract Integrity (constitution Principle III) and spec Assumption "no new backend capabilities beyond what the UI needs."

## Entity: Prompt

Represents a single reusable, AI-facing piece of text that a user has saved.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | string (UUID) | Primary key, auto-generated | Matches existing `generate_id()` behavior in `models.py` |
| `title` | string | Required, 1–200 characters | Existing validation (`Field(..., min_length=1, max_length=200)`) |
| `content` | string | Required, min 1 character | May contain `{{variable}}`-style placeholders (spec FR-004) |
| `description` | string \| null | Optional, max 500 characters | |
| `collection_id` | string (UUID) \| null | Foreign key → `Collection.id`, nullable | Nullable because a prompt may be unassigned, and because deleting a collection unassigns (does not cascade-delete) its prompts (spec FR-008) |
| `created_at` | datetime (UTC) | Auto-set on creation, immutable after | |
| `updated_at` | datetime (UTC) | Auto-set on creation, refreshed on every update | Preserves existing behavior verified in `api.py`'s `update_prompt`/`patch_prompt` |

**Validation rules** (carried over from existing `PromptCreate`/`PromptUpdate`/`PromptPatch` models — unchanged by persistence):
- `title`: non-empty, ≤ 200 characters.
- `content`: non-empty.
- `description`: ≤ 500 characters when present.
- `collection_id`, when present and non-null, MUST reference an existing `Collection.id` at write time (already enforced in `api.py` route handlers via an explicit existence check — persistence layer does not need to duplicate this as a DB-level constraint, though a foreign key column is still used for query efficiency and documentation of intent).

**State transitions**: None beyond create → (any number of updates) → delete. No status/workflow field exists or is required by the spec.

## Entity: Collection

Represents a named grouping of prompts.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | string (UUID) | Primary key, auto-generated | |
| `name` | string | Required, 1–100 characters | |
| `description` | string \| null | Optional, max 500 characters | |
| `created_at` | datetime (UTC) | Auto-set on creation | Existing `Collection` model has no `updated_at` — carried over as-is; collections are not edited in place per the current spec (only created/listed/deleted, per FR-007) |

**Validation rules**: `name` non-empty, ≤ 100 characters; `description` ≤ 500 characters when present.

## Relationship: Prompt → Collection

- **Cardinality**: Each `Prompt` optionally belongs to at most one `Collection` (many-to-one, nullable). A `Collection` may have zero or more `Prompt`s.
- **Deletion behavior** (spec FR-008, already implemented in `api.py`'s `delete_collection`): deleting a `Collection` sets `collection_id` to `null` on every `Prompt` that referenced it, rather than deleting those prompts. The persistence layer's foreign key MUST be defined to allow this (nullable column, no `ON DELETE CASCADE`) — the application layer performs the explicit unassignment, matching current behavior exactly rather than relying on a database-level cascade rule.
- **Referential integrity at write time**: enforced in the API route handlers (existing behavior — a `collection_id` supplied on create/update must reference a real collection or the request is rejected with `400`), not as a hard DB constraint that would reject via a generic database error; this preserves the existing, already-correct error responses.

## Entity: PromptVersion

Added by the [prompt version history feature](../prompt-versions.md) — see that document for the
full field table, relationship details, and rationale. Summary: a historical snapshot of one
`Prompt`'s `title`, `content`, and `description` (not `collection_id`), with a sequential
`version_number`, an optional `label`, and a `created_at` timestamp. Many `PromptVersion`s belong
to one `Prompt`; unlike `Collection` deletion (which unassigns), deleting a `Prompt` cascades to
delete all of its `PromptVersion`s.

## Entity: Tag

Added by the [prompt tagging feature](../tagging-system.md) — see that document for the full
field table, relationship details, and rationale. Summary: a short, reusable label with a
`name` unique **case-insensitively** across all tags, linked to `Prompt` many-to-many (the data
model's first many-to-many relationship — `Collection` is many-to-one by contrast). Deleting a
`Tag` unassigns it from every `Prompt` that carried it (mirroring `Collection`'s
unassign-not-cascade philosophy); deleting a `Prompt` likewise only removes its tag links, never
the `Tag` records themselves. Tags are independent of collection assignment and are not captured
by [prompt versions](../prompt-versions.md).

## Persistence notes (from research.md Decision 1)

- Both entities map to SQLite tables via SQLModel, using the same field names/types as the existing Pydantic models so `backend/app/models.py`'s `Prompt`/`Collection` classes and their DB-table counterparts stay in lockstep (SQLModel allows a single class to serve both roles, or a thin mapping layer — the implementation phase decides which, per Principle II's "simplest implementation that satisfies the spec").
- `backend/app/storage.py`'s public method signatures (`create_prompt`, `get_prompt`, `get_all_prompts`, `update_prompt`, `delete_prompt`, `create_collection`, `get_collection`, `get_all_collections`, `delete_collection`, `get_prompts_by_collection`, `clear`) are preserved exactly; only their internals change from dict operations to SQLite queries. `clear()` continues to be used by test fixtures to reset state between test runs (existing, documented behavior).
