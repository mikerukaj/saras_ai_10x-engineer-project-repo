<!--
Sync Impact Report
Version change: [TEMPLATE] → 1.0.0 (initial ratification)
Modified principles: n/a (first concrete adoption; all placeholders replaced)
Added sections:
  - Core Principles: I. Test-Verified Changes (NON-NEGOTIABLE), II. Simplicity & Flat
    Architecture, III. API Contract Integrity, IV. AI-Assisted Development Transparency,
    V. Incremental, Spec-Driven Change
  - Technology Constraints
  - Development Workflow
  - Governance
Removed sections: none (scaffold placeholders only)
Templates checked for alignment:
  - .specify/templates/ (plan/spec/tasks templates are read at runtime; no edits made here per
    scope guard — no changes needed, they reference the constitution generically)
Deferred / TODO items: none
-->

# PromptLab Constitution

## Core Principles

### I. Test-Verified Changes (NON-NEGOTIABLE)
No change is complete until `pytest tests/ -v` passes. A passing test suite overrides any
visual or logical impression of correctness — including AI-generated code that "looks right."
When fixing a bug: first confirm a test exists (or write one) that fails against the current
buggy behavior, then implement the fix, then confirm the test passes. Tests are the source of
truth for correctness, not inspection alone.

Rationale: documented directly in `docs/ai-verification-note.md` — AI-generated code that
appeared correct still broke tests written against prior buggy behavior; only running the test
suite caught it.

### II. Simplicity & Flat Architecture
Preserve the existing three-layer split: HTTP routes (`app/api.py`) → business logic/helpers
(`app/utils.py`) → storage (`app/storage.py`). Do not introduce a database, authentication,
async I/O, or additional service layers until a concrete, stated requirement needs them. New
code MUST be the simplest implementation that satisfies the current spec — no speculative
abstractions, unused feature flags, or dead code paths.

Rationale: matches `docs/SYSTEM_MODEL.md`'s explicit "deliberately simple flat architecture,"
which keeps a small in-memory prototype easy to reason about and safe to hand off between
contributors.

### III. API Contract Integrity
Every endpoint MUST use correct HTTP status codes and behavior: 404 (not 500) for missing
resources, 422 for invalid payloads, 2xx only on success. Mutating a resource MUST refresh its
`updated_at` timestamp. Deleting a parent resource (e.g., a Collection) MUST NOT silently orphan
its children — the relationship must be explicitly resolved (cascade, reassign, or block). New
endpoints MUST support the same CRUD symmetry as existing ones rather than leaving
noted-but-unimplemented gaps (e.g., a documented but missing PATCH).

Rationale: derived directly from the known, documented bugs in `docs/SYSTEM_MODEL.md` (500 vs
404 on missing prompt, stale `updated_at`, missing PATCH, orphaned prompts on collection
delete). Turning these into standing rules keeps them from being reintroduced.

### IV. AI-Assisted Development Transparency
When AI assistance materially shapes a change (a generated function, an architectural
suggestion, a bug fix), the prompt and its verification step MUST be logged (e.g.,
`docs/prompt-log.md`), and any discovered AI mistake MUST be recorded (e.g.,
`docs/ai-verification-note.md`). AI output is a draft, not a merge-ready artifact, until a human
has run it against the test suite and confirmed the diff matches intent.

Rationale: this repo's own workflow already practices this. Making it a principle keeps the
practice from lapsing as the project grows past its current scale.

### V. Incremental, Spec-Driven Change
Work proceeds in small, reviewable increments scoped to a single spec/task at a time (via the
Spec Kit specify → plan → tasks → implement flow). A change MUST NOT silently expand beyond its
stated task's boundary; new needs surfaced mid-implementation are captured as a new spec/task
rather than folded in unannounced.

Rationale: keeps a partially-built, actively-changing prototype (no CI/CD yet, small
contributor base) auditable and reviewable one step at a time.

## Technology Constraints

- Backend: Python 3.10+, FastAPI, Pydantic v2, uvicorn, as pinned in
  `backend/requirements.txt`. New runtime dependencies require updating that file and stating
  the reason in the commit/PR.
- Frontend (when built): Node.js 18+, introduced no earlier than the point the backend contract
  it depends on is stable, per the README's phased plan.
- No secrets (API keys, credentials) are committed to the repository. Placeholder values in
  `config.yaml` MUST remain placeholders in version control.

## Development Workflow

- Before merging: `pytest tests/ -v` MUST pass locally.
- Bug fixes MUST reference the specific bug being fixed (endpoint/behavior) and add or update a
  test that would have caught it.
- Documentation (`docs/SYSTEM_MODEL.md`, `docs/prompt-log.md`, `README.md`) is updated in the
  same change when architecture, routes, or setup steps shift — not deferred to a later cleanup
  pass.

## Governance

This constitution supersedes ad hoc practice whenever the two conflict. Amendments are made via
the `/speckit-constitution` command, MUST state the version bump rationale (MAJOR/MINOR/PATCH),
and MUST update the Last Amended date below. Specs, plans, and PRs are checked against these
principles before implementation is considered complete; unresolved conflicts are flagged
rather than silently overridden. Complexity that violates Principle II (Simplicity & Flat
Architecture) MUST be justified in the plan's Complexity Tracking section.

Versioning policy: MAJOR for backward-incompatible principle removals or redefinitions, MINOR
for new principles or materially expanded guidance, PATCH for clarifications and wording fixes.

**Version**: 1.0.0 | **Ratified**: 2026-08-15 | **Last Amended**: 2026-08-15
