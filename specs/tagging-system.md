# Feature Specification: Prompt Tagging System

**Extends**: [001-complete-promptlab-app](./001-complete-promptlab-app/spec.md)

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "please add a feature to that allows the user to add tags to their prompts"

## Overview and Goals

A prompt can currently only be organized one way: assignment to a single, optional collection.
In practice, prompts are often cross-cutting — a prompt might be both "for customer support" and
"needs review" and "uses GPT-4-specific formatting" at once, which a single collection can't
express. This feature adds **tags**: short, reusable labels a user can freely attach to any
prompt, any number at a time, independent of (and in addition to) its collection.

Tags are first-class, shared records — not free text repeated on each prompt — so that renaming
a mistyped or evolving tag updates every prompt that uses it at once, the full set of tags in use
can be browsed, and typing a tag that already exists (regardless of capitalization) reuses it
instead of quietly creating a near-duplicate.

### Goals

- A user can attach any number of existing or brand-new tags to a prompt as easily as typing a
  word — no separate "create the tag first" step is required.
- A user never ends up with accidental near-duplicate tags (e.g., "Marketing" and "marketing")
  cluttering their tag list; typing an existing tag name (in any capitalization) reuses it.
- A user can rename a tag once and have that change reflected on every prompt that uses it.
- A user can browse the full set of tags they've used, see how many prompts each is applied to,
  and filter the prompt list down to prompts carrying a given tag.
- Removing a tag (or removing it from one prompt) never deletes the prompt itself, and deleting a
  prompt never deletes tags that other prompts still use.
- This feature is additive to the existing `Prompt` API shape (a new `tags` field) and does not
  change the request/response shape or behavior of collection- or version-related endpoints.

### Out of Scope

- Tag hierarchies, categories, or colors — tags are flat, unstructured labels.
- Merging two existing tags into one — a rename only changes a tag's name, it does not combine
  two separate tag records (a user who wants that today deletes one and re-tags manually).
- A dedicated "add one tag" / "remove one tag" endpoint — tags are set via the same
  create/update/patch calls a prompt's other fields already use (see
  [API Endpoints](#api-endpoints)), consistent with how `collection_id` is already assigned.
- A limit on the number of tags per prompt or the total number of tags in the system — left
  unbounded for this feature; see [Assumptions](#assumptions).

## User Stories with Acceptance Criteria

### User Story 1 - Tag a prompt while creating or editing it (Priority: P1)

A prompt engineer wants to label a prompt with one or more short tags — some already in use,
some brand new — while creating or editing it, without leaving the create/edit form or
performing any separate setup step.

**Why this priority**: This is the entire value of the feature — attaching tags to prompts. Every
other capability (browsing, filtering, renaming) only matters once prompts actually carry tags.

**Independent Test**: Create a prompt supplying two tag names, one of which doesn't exist yet.
Confirm both tags now appear on the prompt, the new one now exists as a reusable tag, and typing
the same existing tag name with different capitalization on a second prompt reuses the same tag
rather than creating a second one.

**Acceptance Scenarios**:

1. **Given** the create-prompt form, **When** the user supplies one or more tag names along with
   the prompt's other fields and submits, **Then** the created prompt carries exactly those tags.
2. **Given** a tag name that does not yet exist, **When** it is supplied on a prompt create or
   edit, **Then** a new tag is created automatically and attached — no separate "create tag"
   action is required.
3. **Given** a tag name that already exists (in any capitalization), **When** it is supplied on a
   prompt create or edit, **Then** the existing tag is reused and attached — a new, near-duplicate
   tag is not created.
4. **Given** an existing prompt with tags, **When** the user edits it and changes its set of
   tags, **Then** the prompt's tags afterward exactly match what was submitted (tags left off the
   new list are detached; the prompt's collection assignment is unaffected).

---

### User Story 2 - Browse and filter prompts by tag (Priority: P2)

A prompt engineer wants to see every prompt carrying a specific tag, and separately wants to
browse the full list of tags they've used so far, so they can find prompts by label rather than
only by keyword search or collection.

**Why this priority**: Tags only pay off once they can be used to find things. This builds
directly on User Story 1's data existing.

**Independent Test**: Tag three prompts with a mix of shared and unique tags, then filter the
prompt list by one shared tag and confirm exactly the prompts carrying it are shown; separately,
open the tag list and confirm every tag in use is listed with how many prompts carry it.

**Acceptance Scenarios**:

1. **Given** prompts tagged with various tags, **When** the user filters the prompt list by one
   tag, **Then** only prompts carrying that tag are shown.
2. **Given** prompts tagged with more than one tag each, **When** the user filters by more than
   one tag at once, **Then** prompts carrying *any* of the selected tags are shown (not only
   prompts carrying all of them).
3. **Given** the tag list view, **When** the user opens it, **Then** they see every tag currently
   in use, each showing how many prompts it's attached to.
4. **Given** a tag filter selected, **When** no prompts carry that tag, **Then** the prompt list
   shows a clear "no results" state rather than an error.

---

### User Story 3 - Rename or remove a tag (Priority: P3)

A prompt engineer notices a tag was misspelled, or has become redundant, and wants to fix or
remove it once, everywhere, rather than editing every prompt that carries it one by one.

**Why this priority**: This is tag *management* rather than tag *use* — valuable for keeping a
growing tag list clean, but not required for the core tagging value delivered by User Stories 1
and 2.

**Independent Test**: Rename a tag applied to two different prompts, then confirm both prompts
now show the new name; separately, delete a tag applied to a prompt and confirm the prompt still
exists with its other tags and fields intact, just without the deleted one.

**Acceptance Scenarios**:

1. **Given** a tag applied to multiple prompts, **When** the user renames it, **Then** every
   prompt that carried it now shows the new name, with no other prompt data affected.
2. **Given** a tag name the user wants to change to another name that's already used by a
   *different* existing tag, **When** they attempt the rename, **Then** the system rejects it
   with a clear "name already in use" message rather than silently merging the two tags.
3. **Given** a tag applied to one or more prompts, **When** the user deletes the tag, **Then** it
   is removed from every prompt that carried it, those prompts and their other fields are
   otherwise unchanged, and the tag no longer appears in the tag list.
4. **Given** a prompt with several tags, **When** the prompt itself is deleted, **Then** its tags
   are detached from it, but the tags themselves continue to exist for any other prompt still
   using them.

## Data Model Changes Needed

### New Entity: Tag

Represents one reusable label a user has created, independent of any single prompt.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `id` | string (UUID) | Primary key, auto-generated | |
| `name` | string | Required, 1–50 characters after trimming surrounding whitespace, unique **case-insensitively** across all tags | "Marketing" and "marketing" are the same tag; the first casing used wins and is preserved on display |
| `created_at` | datetime (UTC) | Auto-set on creation, immutable | |

`prompt_count` (an integer count of prompts currently carrying the tag) is returned alongside
these fields wherever tags are **listed**, but is a computed value, not a stored field — see
[API Endpoints](#api-endpoints).

**Validation rules**: `name` non-empty after trimming, ≤ 50 characters, unique case-insensitively.

### New Relationship: Prompt ↔ Tag (many-to-many)

- **Cardinality**: A `Prompt` may carry zero or more `Tag`s; a `Tag` may be attached to zero or
  more `Prompt`s. This is the first many-to-many relationship in the data model (`Collection` is
  many-to-one by contrast).
- **Deletion behavior**:
  - Deleting a `Prompt` removes its links to any `Tag`s it carried; the `Tag` records themselves
    are **not** deleted, since other prompts may still use them.
  - Deleting a `Tag` removes its links from every `Prompt` that carried it; those prompts are
    **not** deleted and their other fields are unaffected — only that one label is gone.
  - This mirrors the existing `Collection`-deletion philosophy (unassign, don't cascade-delete
    the other side) applied to a many-to-many relationship instead of a many-to-one one.
- **No changes to `Collection` or `PromptVersion`**: tags are independent of, and do not interact
  with, collection assignment or [prompt version history](./prompt-versions.md). A prompt's tags
  are **not** captured by version snapshots — a version is a snapshot of wording (`title`,
  `content`, `description`), not organization, matching the existing decision to exclude
  `collection_id` from versions.

### Changed: `Prompt` gains a `tags` field

The existing `Prompt` entity gains one new field:

| Field | Type | Constraints | Notes |
|---|---|---|---|
| `tags` | array of `Tag` | Defaults to empty list | The prompt's currently-attached tags, embedded in full (not just IDs) so a prompt's tags are visible without a second request |

`PromptCreate`, `PromptUpdate`, and `PromptPatch` each gain an optional `tags` field of **tag
name strings** (not IDs) — see [API Endpoints](#api-endpoints) for exactly how names resolve to
tag records.

## API Endpoints

### Tags

#### List all tags

`GET /tags`

Response `200`:

```json
{
  "tags": [
    { "id": "9c2a...", "name": "marketing", "created_at": "2026-08-10T09:00:00Z", "prompt_count": 4 },
    { "id": "1d7e...", "name": "needs-review", "created_at": "2026-08-15T11:30:00Z", "prompt_count": 1 }
  ],
  "total": 2
}
```

#### Get one tag

`GET /tags/{tag_id}`

Response `200`: a single `Tag` object (with `prompt_count`), same shape as above. `404` if
`tag_id` does not exist.

#### Create a tag explicitly

`POST /tags`

Request body:

```json
{ "name": "needs-review" }
```

Response `201`: the created `Tag`. If a tag with this name already exists (case-insensitively),
the request is rejected with `409` rather than silently returning or duplicating it — explicit
creation is intentional and should surface the collision, unlike the automatic get-or-create that
happens when tagging a prompt (see below). `422` if `name` is empty after trimming or exceeds 50
characters.

#### Rename a tag

`PATCH /tags/{tag_id}`

Request body:

```json
{ "name": "needs-final-review" }
```

Response `200`: the updated `Tag`, unchanged `id`, new `name`. `404` if `tag_id` does not exist.
`409` if the new name collides (case-insensitively) with a *different* existing tag. `422` if
`name` is empty after trimming or exceeds 50 characters.

#### Delete a tag

`DELETE /tags/{tag_id}`

Response `204` on success, no body. Removes the tag from every prompt that carried it. `404` if
`tag_id` does not exist.

### Prompts (changes to existing endpoints)

All shapes below show only what's new; every other existing field, status code, and behavior
documented in [001's api-contract.md](./001-complete-promptlab-app/contracts/api-contract.md)
is unchanged.

#### List prompts — new `tags` filter, tags in the response

`GET /prompts?tags=marketing,needs-review` (in addition to the existing `collection_id` and
`search` query parameters, which continue to work exactly as before and can be combined with
`tags`)

- `tags` is a comma-separated list of tag **names**. A prompt matches if it carries **any** of
  the listed tags (OR semantics, not AND) — see
  [Error Conditions and Edge Cases](#error-conditions-and-edge-cases).
- Every `Prompt` in the response now includes its `tags: Tag[]` array.

#### Get / create / update a prompt — `tags` accepted and returned

`GET /prompts/{id}`, `POST /prompts`, `PUT /prompts/{id}`, `PATCH /prompts/{id}` — request bodies
for the latter three may now include:

```json
{ "tags": ["marketing", "needs-review"] }
```

- Each name is resolved case-insensitively against existing tags: a match reuses that tag: no
  match creates a new tag with the name as submitted (trimmed).
- On `POST` and `PUT`, `tags` is a **full replacement** list (omit it, or a prior create call, to
  mean "no tags"). On `PATCH`, `tags` follows the same partial-update convention as the rest of
  the patch body: omit the key entirely to leave tags unchanged; include it (even as `[]`) to
  fully replace the prompt's tag set with what's provided.
- Every response `Prompt` object includes its resolved `tags: Tag[]` array.
- `400` if `collection_id` is invalid (existing behavior, unchanged). `404` if the prompt doesn't
  exist (existing behavior, unchanged). `422` if any tag name is empty after trimming or exceeds
  50 characters.

#### Delete a prompt — unchanged shape, new side effect

`DELETE /prompts/{id}` — response shape (`204`/`404`) is unchanged. As a new side effect, the
prompt's links to its tags are removed; the `Tag` records themselves are untouched.

## Error Conditions and Edge Cases

- **Case-insensitive reuse on tagging, strict collision on explicit create**: supplying a tag
  name that matches an existing tag (any capitalization) while tagging a prompt *reuses* that
  tag silently — this is the point of the feature (User Story 1, Scenario 3). Explicitly calling
  `POST /tags` with a name that already exists is instead rejected with `409`, since that call is
  a deliberate "create a new tag" request, not an implicit "tag a prompt" request.
- **Duplicate names within one request are deduplicated**: submitting
  `{"tags": ["Marketing", "marketing"]}` on a single prompt create/update resolves both entries
  to the same tag; the prompt ends up with one link to it, not an error and not two links.
- **Rename collision is explicit, not a silent merge**: renaming tag A to a name already held by
  tag B returns `409` rather than merging every prompt that had A onto B — merging is out of
  scope (see [Out of Scope](#out-of-scope)); the user must resolve the collision by choosing a
  different name.
- **Renaming a tag to its own current name (a case-only change) succeeds**: e.g. "marketing" →
  "Marketing" on the same tag is not treated as a collision with itself.
- **Tag filter with no matches returns an empty list, not an error**: `GET /prompts?tags=` with a
  name that matches no tag returns `200` with zero prompts and `total: 0`, consistent with the
  existing `search` parameter's behavior for no matches.
- **Tag filter is OR, not AND**: filtering by multiple tags returns prompts carrying *any* of
  them, not only prompts carrying *all* of them — called out explicitly since both
  interpretations are common in tagging UIs elsewhere.
- **Deleting a tag does not delete prompts, and deleting a prompt does not delete tags**: only
  the link between them is removed in either direction — the `Tag` record persists for other
  prompts; the `Prompt` record persists with its remaining tags and other fields intact.
- **Tags are independent of collections**: a prompt's `collection_id` and its `tags` do not
  interact, validate against each other, or share any deletion behavior — a prompt can belong to
  a collection, carry tags, both, or neither, with no combination being invalid.
- **Tags are not versioned**: restoring an earlier [prompt version](./prompt-versions.md) does
  not change the prompt's current tags, exactly as it does not change `collection_id` — tags are
  organizational, not part of a prompt's wording.
- **No cap on tags per prompt or total tags for this feature**: left unbounded, matching the
  same unbounded-history tradeoff already accepted for prompt versions; revisit only if it
  becomes a real-world usability or storage concern.
- **Empty or whitespace-only tag names are rejected**: `""`, `"   "`, or a name that trims down
  to empty returns `422`, both when explicitly creating a tag and when supplying tag names on a
  prompt create/update/patch.

## Assumptions

- No authentication or per-user ownership applies to tags, consistent with the rest of the
  application's single-user/trusted-environment design (per
  [001's spec.md Assumptions](./001-complete-promptlab-app/spec.md#assumptions)).
- Tag names are meant to be short labels (≤ 50 characters) rather than descriptions; a user
  wanting to explain a tag's purpose would do so elsewhere (e.g., in a prompt's own
  `description`), not on the tag itself.
- This feature depends on 001's persistent storage (FR-011) already being in place — tags and
  their prompt links are stored in the same persistent store as prompts and collections.
- Tag list ordering (e.g., alphabetical vs. by usage count) is a display-layer decision left to
  implementation time; this spec only requires that every tag in use is listed with its
  `prompt_count`.
