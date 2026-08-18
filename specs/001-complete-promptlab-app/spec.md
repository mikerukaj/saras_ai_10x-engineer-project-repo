# Feature Specification: Complete PromptLab Application

**Feature Branch**: `[001-complete-promptlab-app]`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "We already have the backend of a web app that will store, organize, and manage AI prompt templates. We would like to complete this project by writing comprehensive tests, setting up CI/CD and Docker for the deployment of this app, creating a React frontend for the existing backend, connecting the frontend to the backend, and polishing the user experience"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage prompts and collections through a web interface (Priority: P1)

A prompt engineer wants to browse, search, create, edit, and delete their AI prompt templates and the collections that organize them, without needing to call the API directly (e.g., with a script or API testing tool).

**Why this priority**: This is the core value the project has been missing — a usable web interface over the existing backend. Every other workstream (tests, CI/CD, polish) exists to support this being reliable and deployable. Without it, the backend remains unusable by a non-technical audience.

**Independent Test**: Can be fully tested by opening the web interface, creating a prompt and a collection, assigning the prompt to the collection, editing it, searching for it, and deleting both — all without touching the API directly. Delivers standalone value even before CI/CD, Docker, or visual polish exist.

**Acceptance Scenarios**:

1. **Given** the web interface is open and prompts already exist, **When** the user views the prompt list, **Then** they see each prompt's title, description, and collection (if any).
2. **Given** the user is viewing the prompt list, **When** they enter a search term, **Then** only prompts whose title or description match the term are shown.
3. **Given** the user is viewing the prompt list, **When** they select a collection filter, **Then** only prompts belonging to that collection are shown.
4. **Given** the user opens the "create prompt" form and fills in a title and content, **When** they submit the form, **Then** the new prompt appears in the prompt list without a page reload losing their place.
5. **Given** an existing prompt, **When** the user edits its title, content, description, or collection and saves, **Then** the updated values are reflected immediately in the prompt list and detail view.
6. **Given** an existing prompt, **When** the user chooses to delete it and confirms, **Then** the prompt no longer appears in the list.
7. **Given** an existing collection with prompts assigned to it, **When** the user deletes the collection, **Then** those prompts remain in the system but show as having no collection.
8. **Given** a prompt whose content contains `{{variable}}`-style placeholders, **When** the user views its details, **Then** the placeholders are visually distinguishable from the surrounding text.

---

### User Story 2 - Trust the application through automated test coverage (Priority: P2)

A project maintainer wants automated tests covering both the existing backend behavior and the new web interface, so that a change (by a human or an AI assistant) that breaks existing functionality is caught before it ships rather than discovered by a user.

**Why this priority**: The project's own constitution treats a passing test suite as the source of truth for correctness. Extending the application (new frontend, new deployment pipeline) without extending test coverage would leave the riskiest, newest parts of the system unverified.

**Independent Test**: Can be fully tested by intentionally introducing a regression (e.g., breaking a create-prompt flow or an API endpoint) and confirming the automated test suite fails and clearly identifies the broken behavior, then confirming it passes again once the regression is fixed.

**Acceptance Scenarios**:

1. **Given** the full automated test suite, **When** it is run with a single documented command, **Then** it exercises the primary create/read/update/delete flows for both prompts and collections.
2. **Given** a code change that breaks an existing, previously-passing behavior, **When** the test suite is run, **Then** at least one test fails and its failure message identifies which behavior broke.
3. **Given** the web interface's core user flows (search, create, edit, delete, collection filtering), **When** the test suite is run, **Then** each of those flows has at least one automated test exercising it end-to-end from the interface down to the stored data.
4. **Given** a known edge case (e.g., deleting a prompt that doesn't exist, deleting a collection with prompts assigned to it), **When** the test suite is run, **Then** the expected (not-a-crash) behavior for that case is explicitly verified.

---

### User Story 3 - Reliable, repeatable deployment via CI/CD and containerization (Priority: P3)

A project maintainer wants every proposed change to be automatically built, tested, and packaged the same way every time, so that "it works on my machine" never becomes a blocker to shipping, and a broken change cannot reach a deployable state.

**Why this priority**: This turns the project from something that only runs in a single developer's local setup into something that can be reliably handed off and run by someone else with one command — but it depends on User Story 2's test coverage existing first to have something meaningful to gate on.

**Independent Test**: Can be fully tested by proposing a change that fails the test suite and confirming the pipeline blocks it from reaching a packaged state, then proposing a passing change and confirming it is automatically built, tested, packaged, and can be brought up with a single command on a clean machine.

**Acceptance Scenarios**:

1. **Given** a proposed change, **When** it is submitted, **Then** the automated test suite runs against it without manual triggering.
2. **Given** a proposed change whose tests fail, **When** the pipeline evaluates it, **Then** the change is prevented from reaching a packaged state.
3. **Given** a proposed change whose tests pass, **When** the pipeline evaluates it, **Then** the application is packaged into a self-contained, runnable form.
4. **Given** the packaged application, **When** a single documented command is run on a clean machine that only has the documented prerequisites installed, **Then** the backend, web interface, and persistent data store all start successfully and the application is ready to use.

---

### User Story 4 - Polished, cohesive user experience (Priority: P4)

A prompt engineer using the web interface day-to-day wants it to feel consistent, responsive, and forgiving of mistakes — clear feedback while something is loading, readable layouts on different screen sizes, and understandable messages when something goes wrong — rather than a bare-functionality prototype.

**Why this priority**: This builds on User Story 1's functionality; the interface must work before it can be polished. It's the difference between "technically usable" and "pleasant to use daily," which matters for adoption but doesn't block the interface from delivering value on its own.

**Independent Test**: Can be fully tested by walking through every flow from User Story 1 while watching for loading feedback, checking layouts at both a desktop and a mobile-width window size, and triggering error conditions (e.g., disconnecting the backend, submitting invalid input) to confirm messages are clear and non-technical.

**Acceptance Scenarios**:

1. **Given** any action that waits on a backend response, **When** the response is pending, **Then** the interface shows a visible loading indicator rather than appearing frozen or unresponsive.
2. **Given** an action fails (invalid input, resource not found, backend unreachable), **When** the failure occurs, **Then** the interface shows a clear, non-technical message describing what happened.
3. **Given** the same set of screens, **When** viewed on a standard desktop-width window versus a mobile-width window, **Then** all core actions remain reachable and readable without horizontal scrolling.
4. **Given** any two screens in the application, **When** compared, **Then** they share consistent layout, typography, and color conventions.

---

### User Story 5 - Save and restore prompt versions (Priority: P5)

A prompt engineer iterating on a prompt's wording wants every save to be automatically
recoverable, wants to browse how a prompt's content changed over time, and wants to restore an
earlier version in one action — so refining a prompt never risks losing wording that turned out
to be better than a later edit.

**Why this priority**: This adds safety and confidence to the editing workflow User Story 1
already delivers, but is not required for the interface to be usable end-to-end — it builds on
US1's edit flow rather than blocking it.

**Independent Test**: Edit a prompt's content twice via the web interface, open its version
history, confirm three versions exist (original plus two edits), restore the first version, and
confirm the prompt's current content matches it. Full detail in
[specs/prompt-versions.md](../prompt-versions.md).

**Acceptance Scenarios**:

1. **Given** a prompt is created or its title, content, or description is edited and saved,
   **When** the save succeeds, **Then** the prior state is automatically captured as a
   recoverable version, with no extra action from the user.
2. **Given** a prompt with multiple saved versions, **When** the user views its version history
   from the web interface, **Then** they see each version listed newest-first and can open any
   one to see its full content.
3. **Given** an earlier version of a prompt, **When** the user chooses to restore it, **Then**
   the prompt's current title, content, and description become that version's values (its
   collection assignment is unaffected), and the state just before the restore is itself saved
   as a new version.
4. **Given** an existing prompt, **When** the user deletes it, **Then** all of its saved versions
   are removed along with it.

---

### User Story 6 - Tag prompts for cross-cutting organization (Priority: P6)

A prompt engineer wants to label prompts with short, reusable tags (e.g., "needs-review",
"gpt4-formatting") that cut across collections, so prompts can be organized and found by more
than one dimension at once, and can rename or remove a tag once and have it apply everywhere the
tag is used.

**Why this priority**: This adds a second, complementary organization axis to the collection
system User Story 1 already delivers; it's independently useful but not required for the
interface's core CRUD flows to work, so it's scoped after the higher-priority stories.

**Independent Test**: Create two prompts and tag them with a shared tag and a unique tag each,
filter the prompt list by the shared tag and confirm both appear, rename the shared tag and
confirm both prompts show the new name, then delete one prompt and confirm the shared tag still
exists and is still attached to the remaining prompt. Full detail in
[specs/tagging-system.md](../tagging-system.md).

**Acceptance Scenarios**:

1. **Given** the create or edit prompt form, **When** the user supplies one or more tag names
   (existing or new) and saves, **Then** the prompt carries exactly those tags, with any
   not-yet-existing tag created automatically and any existing tag (matched regardless of
   capitalization) reused rather than duplicated.
2. **Given** prompts carrying various tags, **When** the user filters the prompt list by one or
   more tags, **Then** only prompts carrying at least one of the selected tags are shown.
3. **Given** a tag applied to multiple prompts, **When** the user renames it, **Then** every
   prompt carrying it shows the new name.
4. **Given** a tag applied to one or more prompts, **When** the user deletes the tag or deletes
   one of the prompts carrying it, **Then** only that link is removed — the tag continues to
   exist for any other prompt still using it, and the prompt continues to exist with its
   remaining tags and other fields intact.

---

### Edge Cases

- What happens when the web interface tries to load data but the backend is unreachable or returns an error?
- What happens when a user attempts to edit or delete a prompt or collection that was already deleted by another client since the page was loaded?
- What happens when a user submits a create/edit form with invalid data (empty required field, over the maximum length)?
- How does the search/filter experience behave when no prompts match, or when the collection filter refers to a collection that no longer exists?
- What happens to in-progress work (e.g., a partially filled create-prompt form) if the interface loses its connection to the backend while the form is open?
- How does the deployment pipeline behave when a change passes tests but the packaging/build step itself fails?
- What happens when the same prompt is edited from two different browser tabs/sessions at nearly the same time?
- What happens when the persistent data store is unavailable or fails to start when the application starts up?
- What happens when a prompt is edited but only its collection assignment changes (no wording change)? See [specs/prompt-versions.md](../prompt-versions.md) for the full answer (no redundant version is created).
- What happens to a prompt's saved versions when the prompt itself is deleted? See [specs/prompt-versions.md](../prompt-versions.md) (versions are deleted along with it, unlike collection-unassignment on collection delete).
- What happens when a user tags a prompt with a tag name that already exists under different capitalization, or renames a tag to a name already used by another tag? See [specs/tagging-system.md](../tagging-system.md) (case-insensitive reuse when tagging; an explicit, non-silent collision error when renaming).
- What happens to a tag's other prompts when one prompt carrying it is deleted, or to a prompt's other tags when one tag is deleted? See [specs/tagging-system.md](../tagging-system.md) (only the specific link is removed; the tag and the prompt otherwise persist independently).

## Requirements *(mandatory)*

### Functional Requirements

**Web interface**

- **FR-001**: System MUST provide a web-based interface that lists all stored prompts, showing each prompt's title, description, and collection (if assigned).
- **FR-002**: Users MUST be able to search the prompt list by keyword and filter it by collection from the web interface.
- **FR-003**: Users MUST be able to create a new prompt from the web interface by supplying a title and content, with optional description and collection assignment.
- **FR-004**: Users MUST be able to view a single prompt's full details, including its content with any `{{variable}}`-style placeholders visually distinguished.
- **FR-005**: Users MUST be able to edit an existing prompt's title, content, description, and collection assignment from the web interface.
- **FR-006**: Users MUST be able to delete a prompt from the web interface, with an explicit confirmation step before the deletion is applied.
- **FR-007**: Users MUST be able to create, list, and delete collections from the web interface.
- **FR-008**: The web interface MUST reflect that deleting a collection unassigns rather than deletes the prompts that belonged to it.
- **FR-009**: The web interface MUST show a clear, non-technical error message whenever an action fails, distinguishing at minimum between "invalid input," "not found," and "backend unreachable" cases.
- **FR-010**: The web interface MUST provide a one-action way to copy a prompt's content for reuse elsewhere.

**Data persistence**

- **FR-011**: The system MUST persist prompt and collection data so that it survives an application restart or redeployment, replacing the current in-memory-only storage.
- **FR-012**: The specific persistence technology is an implementation decision made during planning; this requirement only constrains the observable behavior (data survives restarts), not the mechanism.

**Automated testing**

- **FR-013**: The system MUST have automated tests covering the documented backend behaviors for prompts and collections, including their create/read/update/delete operations and known edge cases (e.g., deleting a collection with assigned prompts).
- **FR-014**: The system MUST have automated tests covering the web interface's core user flows: listing, searching, filtering, creating, editing, and deleting both prompts and collections.
- **FR-015**: The system MUST have automated tests verifying that the web interface and backend interact correctly for at least the primary create/edit/delete flows (i.e., an action taken in the interface is confirmed to have taken effect in the underlying stored data).
- **FR-016**: The system MUST have end-to-end automated tests that drive a real browser through complete user journeys (e.g., creating a prompt via the web interface and confirming it persists and is retrievable afterward).
- **FR-017**: The full automated test suite MUST be runnable via a single documented command, without manual setup beyond the project's documented installation steps.

**CI/CD and deployment**

- **FR-018**: The system MUST automatically run the full automated test suite against every proposed change, without a person needing to trigger it manually.
- **FR-019**: A proposed change whose automated tests fail MUST be prevented from reaching a packaged state.
- **FR-020**: The system MUST be packaged into a self-contained, runnable form that starts the same way regardless of which machine builds or runs it.
- **FR-021**: The packaged application MUST be startable with a single command on any machine that has the documented container prerequisites installed; this feature does not provision or maintain any separate live/hosted environment beyond that local, one-command run.
- **FR-022**: Running the deployment process with the same inputs MUST produce the same running result each time (no manual, undocumented setup steps required).

**User experience polish**

- **FR-023**: The web interface MUST show a visible loading indicator for any action that waits on a backend response.
- **FR-024**: The web interface MUST remain usable — all core actions reachable and readable without horizontal scrolling — on both standard desktop-width and mobile-width screens.
- **FR-025**: The web interface MUST apply a consistent layout, typography, and color scheme across all of its screens.

**Prompt version history**

Full detail (data model, API endpoints, error conditions) is specified in
[specs/prompt-versions.md](../prompt-versions.md); the requirements below are the summary that
belongs to this feature's scope.

- **FR-026**: The system MUST automatically capture a recoverable version of a prompt's title, content, and description whenever a prompt is created or one of those fields changes on an edit.
- **FR-027**: Users MUST be able to view a prompt's version history (ordered newest first) and inspect the full title, content, and description of any past version, from the web interface.
- **FR-028**: Users MUST be able to restore a prompt to a previous version, which updates its current title, content, and description to that version's values without changing its collection assignment.
- **FR-029**: The system MUST delete a prompt's saved versions when the prompt itself is deleted.
- **FR-030**: Users MUST be able to explicitly save a labeled checkpoint version of a prompt's current state, and delete an individual past version, from the web interface.

**Prompt tagging**

Full detail (data model, API endpoints, error conditions) is specified in
[specs/tagging-system.md](../tagging-system.md); the requirements below are the summary that
belongs to this feature's scope.

- **FR-031**: Users MUST be able to attach any number of tags to a prompt from the create/edit form, with a not-yet-existing tag name creating a new tag automatically and an existing tag name (matched case-insensitively) being reused rather than duplicated.
- **FR-032**: Users MUST be able to filter the prompt list by one or more tags from the web interface, showing prompts carrying at least one of the selected tags.
- **FR-033**: Users MUST be able to browse the full list of tags in use, each showing how many prompts carry it, from the web interface.
- **FR-034**: Users MUST be able to rename a tag, with the new name reflected on every prompt that carries it, and delete a tag, which removes it from every prompt that carried it without deleting those prompts.
- **FR-035**: Deleting a prompt MUST remove its tag links without deleting the tags themselves, and deleting a tag MUST remove its links without deleting the prompts that carried it.

### Key Entities

- **Prompt**: A reusable piece of AI-facing text with a title, content (which may contain `{{variable}}`-style placeholders), an optional description, an optional collection assignment, and zero or more tags. Tracks when it was created and last updated. Persists across application restarts.
- **Collection**: A named grouping of prompts (e.g., "Marketing", "Development") with an optional description. Deleting a collection unassigns, rather than deletes, the prompts that belonged to it. Persists across application restarts.
- **PromptVersion**: A historical snapshot of one prompt's title, content, and description at a point in time, with a sequential version number, an optional user-supplied label, and a creation timestamp. Belongs to exactly one prompt; deleted along with it. See [specs/prompt-versions.md](../prompt-versions.md).
- **Tag**: A short, reusable label (unique case-insensitively) that can be attached to any number of prompts, independent of collection assignment. Deleting a tag unassigns it from every prompt that carried it, rather than deleting those prompts. See [specs/tagging-system.md](../tagging-system.md).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user can locate an existing prompt and copy its content within 30 seconds of opening the web interface, without prior training.
- **SC-002**: A user can create a new prompt from the web interface, from opening the create form to seeing it appear in the list, in under 1 minute.
- **SC-003**: 100% of the documented backend behaviors (prompt and collection create/read/update/delete, search, filtering, and the collection-deletion unassignment behavior) are covered by an automated test that can be run without manual steps.
- **SC-004**: 100% of proposed changes that fail the automated test suite are blocked from reaching a packaged/deployable state, with zero manual override in the standard flow.
- **SC-005**: The packaged application starts successfully and serves the backend, web interface, and persistent data store with a single command on a clean machine with only the documented prerequisites installed, on the first attempt.
- **SC-006**: All core actions (search, create, edit, delete, for both prompts and collections) remain fully completable on a mobile-width (375px) screen as well as a standard desktop window.
- **SC-007**: In a moderated usability check, 90% of participants can create, find, edit, and delete a prompt using only the web interface, without external help.
- **SC-008**: Data created or edited through the web interface remains available and unchanged after the application is restarted or redeployed.
- **SC-009**: A user can restore a prompt to any version shown in its history in under 15 seconds from opening that prompt's version history.
- **SC-010**: 100% of prompt edits that change title, content, or description produce a recoverable version, verified by an automated test that can be run without manual steps.
- **SC-011**: A user can tag a prompt with a new or existing tag and see it filterable from the prompt list in under 30 seconds, without leaving the create/edit form to set up the tag first.
- **SC-012**: Renaming a tag used by multiple prompts updates 100% of those prompts' displayed tag name with no additional per-prompt action, verified by an automated test.

## Assumptions

- The web frontend will be built as a browser-based single-page application, consistent with the project's already-documented technology direction (React/Vite, Node.js 18+) rather than a server-rendered or native application.
- No user authentication, accounts, or multi-tenant access control are required; the application continues to operate as a single-user/trusted-environment tool, consistent with the current backend's design.
- The existing backend REST API (prompt and collection endpoints already implemented) is the system of record the web interface integrates with; this feature does not assume new backend capabilities beyond what the acceptance scenarios above require.
- "Comprehensive tests" refers to automated, repeatable tests runnable in a development or CI environment — not manual test scripts or manual QA checklists.
- Visual/branding decisions (exact color palette, font choices, logo) are left to implementation-time design judgment as long as FR-025's consistency requirement is met; this spec does not mandate a specific visual identity.
- "Deployment" for this feature means a reliable, single-command local/self-hosted run (e.g., on a developer's or self-hoster's own machine); provisioning or maintaining a live, publicly reachable hosted environment is out of scope and would be a separate, future feature.
- The specific persistent storage technology (e.g., an embedded file-based database vs. a separate database server) is an implementation decision made during planning, not this specification.
- Prompt version history (User Story 5) only versions `title`, `content`, and `description` — not collection assignment — and places no limit on the number of versions retained per prompt for this feature; see [specs/prompt-versions.md](../prompt-versions.md) Assumptions for the full rationale.
- Tags (User Story 6) are first-class, shared records (not free text repeated per prompt), matched case-insensitively, with no limit on tags per prompt or total tags for this feature; see [specs/tagging-system.md](../tagging-system.md) Assumptions for the full rationale.

## Clarifications

### Session 2026-08-17

- Q: What should "CI/CD and Docker for deployment" actually produce? → A: A reliable, single-command local/self-hosted run on any machine with the documented container prerequisites installed. No live hosted environment is provisioned or maintained as part of this feature.
- Q: Should this feature add persistent data storage, or keep the current in-memory storage? → A: Add persistent storage — prompt and collection data must survive an application restart or redeployment.
- Q: What test coverage counts as "comprehensive" for this feature? → A: Unit, integration, and contract tests for both backend and frontend, plus full end-to-end tests that drive a real browser through complete user journeys.

### Session 2026-08-17 (Prompt version history added)

- Q: Should editing a prompt overwrite its prior wording permanently, or should past wording be recoverable? → A: Recoverable — add automatic, per-edit version history plus manual checkpoint/restore/delete actions, detailed in [specs/prompt-versions.md](../prompt-versions.md).

### Session 2026-08-17 (Prompt tagging added)

- Q: Should tags be free-text strings stored per prompt, or first-class shared records? → A: First-class `Tag` entities, many-to-many with prompts, matched case-insensitively so near-duplicate tags aren't created and a rename applies everywhere at once — detailed in [specs/tagging-system.md](../tagging-system.md).
