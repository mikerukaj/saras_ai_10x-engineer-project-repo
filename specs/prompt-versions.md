# Feature Specification: Save Prompt Versions

**Extends**: [001-complete-promptlab-app](./001-complete-promptlab-app/spec.md)

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "please add a feature to save prompt versions"

## Overview and Goals

Today, editing a prompt (`PUT`/`PATCH /prompts/{id}`) permanently overwrites its `title`,
`content`, and `description` — the prior wording is gone the moment a save succeeds. A prompt
engineer who iterates on a prompt (tightening wording, trying a different instruction style,
then wanting the old version back) currently has no way to recover what was there before, short
of remembering it themselves.

This feature adds **version history** to prompts: every meaningful edit is automatically
preserved as a recoverable snapshot, the history can be browsed and inspected, and a prompt can
be restored to any earlier snapshot. It also lets a user explicitly checkpoint a state they want
to label and come back to, and prune history entries they no longer need.

### Goals

- No edit to a prompt's wording is ever unrecoverable — every saved change is captured as a
  version automatically, with no extra action required from the user.
- A user can see, at a glance, how a prompt's wording evolved over time and inspect any past
  state in full.
- A user can revert a prompt to an earlier state in one action, without retyping or
  copy-pasting old content.
- A user can mark a specific state as worth returning to (a labeled checkpoint) and remove
  history entries that are just noise.
- This feature does not change the shape or behavior of any existing endpoint response; it is
  additive only (see [Error Conditions and Edge Cases](#error-conditions-and-edge-cases) for the
  two existing endpoints that gain new, non-breaking side effects).

### Out of Scope

- Comparing two versions side-by-side (diffing) — this spec covers saving and restoring, not
  visual diffs.
- Limiting or paginating version history (e.g., "keep only the last 50") — left as a future
  concern; see [Assumptions](#assumptions).
- Access control over who may view/restore/delete versions — unchanged from the rest of the
  application (no authentication, single-user/trusted-environment tool).
- Versioning collection assignment — only a prompt's `title`, `content`, and `description` are
  versioned (see [Data Model Changes Needed](#data-model-changes-needed) for rationale).

## User Stories with Acceptance Criteria

### User Story 1 - Every edit is automatically recoverable (Priority: P1)

A prompt engineer refines a prompt's wording over several edits. They want to know that if a
later edit turns out worse than an earlier one, nothing is permanently lost — without having to
remember to do anything extra when saving.

**Why this priority**: This is the core promise of the feature. Every other capability
(browsing, restoring, checkpointing) is only useful if history is actually being captured in the
first place.

**Independent Test**: Create a prompt, edit its content three times with different wording each
time, then confirm (via the version history endpoint) that four distinct snapshots exist — the
original and each edited state — without having taken any action beyond the normal create/edit
flow.

**Acceptance Scenarios**:

1. **Given** a newly created prompt, **When** it is created, **Then** a version snapshot of its
   initial `title`, `content`, and `description` exists.
2. **Given** an existing prompt, **When** its `title`, `content`, or `description` is changed via
   an edit and saved, **Then** a new version snapshot is created capturing the state *before*
   that edit was applied.
3. **Given** an existing prompt, **When** it is edited but only its `collection_id` changes (no
   change to `title`, `content`, or `description`), **Then** no new version snapshot is created.
4. **Given** an existing prompt with several edits behind it, **When** the prompt is deleted,
   **Then** all of its version snapshots are removed along with it.

---

### User Story 2 - Browse and inspect version history (Priority: P2)

A prompt engineer wants to see how a prompt's wording has changed over time and read the full
text of any earlier version, so they can decide whether it's worth reverting to.

**Why this priority**: Captured history has no value if it can't be seen. This is the second
step after User Story 1 makes the data exist.

**Independent Test**: Open a prompt with several edits behind it, view its version history list,
confirm it's ordered newest-first with one entry per meaningful edit, then open one specific past
version and confirm its full `title`/`content`/`description` are shown exactly as they were at
that point in time.

**Acceptance Scenarios**:

1. **Given** a prompt with multiple saved versions, **When** the user views its version history,
   **Then** they see each version's number, a timestamp, and (if present) its label, ordered
   newest first.
2. **Given** a prompt's version history, **When** the user opens one specific version, **Then**
   they see that version's full `title`, `content`, and `description` as they were at the time
   that version was captured.
3. **Given** a prompt that has never been edited since creation, **When** the user views its
   version history, **Then** exactly one version (the initial state) is shown.

---

### User Story 3 - Restore a prompt to a previous version (Priority: P3)

A prompt engineer realizes an earlier version of a prompt was better than the current one. They
want to bring that earlier wording back as the prompt's current state in one action.

**Why this priority**: This is the payoff of capturing and browsing history — turning "I can see
the old version" into "I can have it back." It depends on User Stories 1 and 2 already existing.

**Independent Test**: Edit a prompt twice (so three versions exist), restore it to the first
version, and confirm the prompt's current `title`/`content`/`description` now match that first
version — and that the state right before the restore was itself captured as a new version (so
the restore itself is undoable).

**Acceptance Scenarios**:

1. **Given** a prompt with an earlier version available, **When** the user chooses to restore
   that version, **Then** the prompt's current `title`, `content`, and `description` become that
   version's values, and its `collection_id` assignment is left unchanged.
2. **Given** a restore action, **When** it completes, **Then** the prompt's state immediately
   before the restore is itself saved as a new version, so the restore can be undone the same way
   any other edit can.
3. **Given** a prompt currently assigned to a collection, **When** the user restores an earlier
   version, **Then** the prompt remains assigned to its current collection (collection
   assignment is not part of what gets restored).

---

### User Story 4 - Checkpoint and prune history on demand (Priority: P4)

A prompt engineer is about to try a risky rewrite of a prompt that's currently working well. They
want to explicitly mark the current state with a note before experimenting, and later clean up
old checkpoints they no longer need.

**Why this priority**: This rounds out the feature with user-initiated control over history,
building on User Stories 1–3 but not required for the core "nothing is lost, and I can go back"
value.

**Independent Test**: On a prompt with no pending edits, explicitly save a labeled checkpoint,
confirm it appears in the version history with its label, then delete an unrelated older version
and confirm it disappears from the history while the rest of the history and the prompt's current
state are unaffected.

**Acceptance Scenarios**:

1. **Given** an existing prompt, **When** the user explicitly saves a checkpoint with a label
   (e.g., "before rewrite"), **Then** a new version is created capturing the prompt's current
   state with that label attached, even if nothing has changed since the last version.
2. **Given** a prompt's version history, **When** the user deletes one specific past version,
   **Then** that version no longer appears in the history, other versions are unaffected, and the
   prompt's current state is unchanged.
3. **Given** a version the user is viewing, **When** they choose to delete it, **Then** they are
   asked to confirm before it is permanently removed (consistent with the existing prompt-delete
   confirmation pattern).

## Data Model Changes Needed

### New Entity: PromptVersion

Represents one historical snapshot of a prompt's wording.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | string (UUID) | Primary key, auto-generated | |
| `prompt_id` | string (UUID) | Required, foreign key → `Prompt.id` | |
| `version_number` | integer | Required, ≥ 1, sequential per `prompt_id`, immutable | Not reused or renumbered after a deletion — gaps in the sequence are expected and normal |
| `title` | string | Required, snapshot of `Prompt.title` at capture time | |
| `content` | string | Required, snapshot of `Prompt.content` at capture time | |
| `description` | string \| null | Snapshot of `Prompt.description` at capture time | |
| `label` | string \| null | Optional, ≤ 100 characters | User-supplied note; only set on manually-checkpointed versions (User Story 4) — automatically-captured versions leave this `null` |
| `created_at` | datetime (UTC) | Auto-set on creation, immutable | |

**Design decision — `collection_id` is not versioned**: a prompt's collection assignment is an
organizational property of its current state, not part of its wording. Restoring a version never
changes `collection_id` (User Story 3, Acceptance Scenario 3), so there is nothing meaningful to
capture or restore for that field.

**Validation rules**: `label`, when present, ≤ 100 characters (same convention as `Collection`'s
`name` field).

### Relationship: Prompt → PromptVersion

- **Cardinality**: Each `Prompt` has one or more `PromptVersion`s (one is guaranteed to exist
  from creation onward). Each `PromptVersion` belongs to exactly one `Prompt`.
- **Deletion behavior**: deleting a `Prompt` deletes all of its `PromptVersion`s (cascade). This
  is a deliberate difference from the existing `Collection` → `Prompt` relationship, which
  *unassigns* rather than cascades — a version has no meaning independent of the prompt it
  captures, whereas a prompt has independent meaning after its collection is gone.

### No changes to the existing `Prompt` or `Collection` entities

Their fields, constraints, and the `Collection`-deletion unassignment behavior described in
[001's data-model.md](./001-complete-promptlab-app/data-model.md) are unchanged by this feature.

## API Endpoints

All new endpoints are nested under a prompt's existing resource path. None of the request/response
shapes of already-existing endpoints change (see
[Error Conditions and Edge Cases](#error-conditions-and-edge-cases) for the new, non-breaking
*side effects* two existing endpoints gain).

### List a prompt's version history

`GET /prompts/{prompt_id}/versions`

Response `200`, ordered newest (`version_number`) first:

```json
{
  "versions": [
    {
      "id": "3b1c...",
      "prompt_id": "a9f0...",
      "version_number": 3,
      "title": "Customer follow-up email",
      "content": "Write a warm, concise follow-up to {{customer_name}}...",
      "description": "For post-purchase check-ins",
      "label": "before shortening",
      "created_at": "2026-08-17T14:22:00Z"
    }
  ],
  "total": 3
}
```

`404` if `prompt_id` does not correspond to an existing prompt.

### Get one specific version

`GET /prompts/{prompt_id}/versions/{version_id}`

Response `200`: a single `PromptVersion` object, same shape as an entry above.

`404` if the prompt does not exist, the version does not exist, or the version exists but does
not belong to `prompt_id`.

### Manually save a checkpoint

`POST /prompts/{prompt_id}/versions`

Request body (all fields optional):

```json
{ "label": "before shortening" }
```

Response `201`: the newly created `PromptVersion`, with `title`/`content`/`description` copied
from the prompt's current state at the moment of the call and `version_number` set to one more
than the highest existing version for that prompt.

`404` if the prompt does not exist. `422` if `label` exceeds 100 characters.

### Restore a prompt to a previous version

`POST /prompts/{prompt_id}/versions/{version_id}/restore`

No request body.

Response `200`: the updated `Prompt` (same shape as `GET /prompts/{id}`), with `title`,
`content`, and `description` now matching the restored version, `updated_at` refreshed, and
`collection_id` unchanged. As a side effect, the prompt's state immediately before the restore is
saved as a new, unlabeled version (User Story 3, Acceptance Scenario 2).

`404` if the prompt does not exist, the version does not exist, or the version exists but does
not belong to `prompt_id`.

### Delete a version

`DELETE /prompts/{prompt_id}/versions/{version_id}`

Response `204` on success, no body.

`404` if the prompt does not exist, the version does not exist, or the version exists but does
not belong to `prompt_id`.

## Error Conditions and Edge Cases

- **No-op field edits don't spam history**: a `PUT`/`PATCH` to `/prompts/{id}` that changes only
  `collection_id` (not `title`, `content`, or `description`) does not create a new version — see
  User Story 1, Acceptance Scenario 3.
- **Cascade delete**: `DELETE /prompts/{id}` (existing endpoint) gains a new side effect — it now
  also deletes every `PromptVersion` belonging to that prompt. The endpoint's request/response
  shape (`204`/`404`) is unchanged.
- **Version created on prompt creation**: `POST /prompts` (existing endpoint) gains a new side
  effect — it now also creates version `1` for the new prompt. The endpoint's response shape
  (`201 Prompt`) is unchanged.
- **Cross-prompt version IDs are treated as not found**: requesting, restoring, or deleting a
  `version_id` that exists but belongs to a *different* `prompt_id` than the one in the URL
  returns `404`, not the version from the other prompt. This prevents one prompt's history from
  leaking into another's URL space.
- **Restoring the current state is a harmless no-op**: if a user restores a version that's
  identical to the prompt's current state (e.g., the latest version), the action still succeeds
  and still creates a fresh snapshot of "current" beforehand, exactly as any other restore would
  — there is no special-cased short-circuit, keeping the behavior simple and predictable.
- **Restore does not touch collection assignment**: restoring never changes `collection_id`,
  even if the version being restored was originally captured while the prompt belonged to a
  different (or no) collection — see the data model's design decision above.
- **Version numbers are never reused**: deleting version 2 out of [1, 2, 3] leaves [1, 3] — the
  next new version is still numbered 4, not a reused 2. This keeps `version_number` a reliable
  indicator of creation order even after deletions.
- **Manual checkpoints allow duplicates**: explicitly saving a checkpoint (User Story 4) when
  nothing has changed since the last version is allowed and still creates a new version — the
  user is intentionally marking a point in time, which is different from an automatic,
  change-triggered snapshot.
- **Concurrent edits**: if two clients edit the same prompt at nearly the same time, the existing
  last-write-wins behavior for the prompt's current state is unchanged — but both edits still
  each produce their own version snapshot, so neither client's intermediate wording is lost even
  though only the later write becomes "current."
- **Deleting a prompt's only version is not possible through this API**: because `POST /prompts`
  always creates version 1, and version deletion only targets a `version_id` a caller already
  knows about, there is no user-facing action that leaves a prompt with zero versions during its
  lifetime (only prompt deletion removes the last one, atomically with the prompt itself).

## Assumptions

- No limit is placed on the number of versions retained per prompt for this feature; unbounded
  history growth for very frequently-edited prompts is an accepted tradeoff, not a defect —
  revisit if it becomes a real-world storage concern.
- Only `title`, `content`, and `description` are versioned, matching the fields a user actually
  edits when refining a prompt's wording; `collection_id` is deliberately excluded (see Data
  Model Changes Needed).
- No authentication or per-user ownership applies to versions, consistent with the rest of the
  application's single-user/trusted-environment design (per
  [001's spec.md Assumptions](./001-complete-promptlab-app/spec.md#assumptions)).
- This feature depends on 001's persistent storage (FR-011) already being in place — version
  history stored only in memory would defeat its own purpose of surviving restarts.
