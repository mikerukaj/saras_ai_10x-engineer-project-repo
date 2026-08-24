"""Pre-implementation acceptance-test suite for the "Save Prompt Versions"
feature described in specs/prompt-versions.md.

IMPORTANT - READ BEFORE INTERPRETING RESULTS:

As of the writing of this file, the prompt-versioning feature described in
specs/prompt-versions.md is a Draft spec and has NOT been implemented
anywhere in backend/app/. There is no `PromptVersion` model, no
`/prompts/{id}/versions` routes, and no versioning side effects on the
existing `POST/PUT/PATCH/DELETE /prompts` endpoints.

This file is written FIRST, deliberately, following TDD's "red phase":
every test here codifies an acceptance scenario or API contract clause
directly from specs/prompt-versions.md, phrased as what SHOULD happen once
the feature exists - not what currently happens. Running this suite today
is expected to produce mostly FAILURES. Those failures are the correct,
expected state of an unbuilt feature - they are not regressions, not bugs
in existing code, and nobody should "fix" them by weakening assertions.
Once the feature is implemented per the spec, this suite is expected to
turn green and can then serve as its regression suite.

One nuance worth flagging explicitly: because the new routes genuinely do
not exist yet, FastAPI's routing layer itself returns a generic 404 "Not
Found" for ANY request made to them (e.g. GET /prompts/{id}/versions),
regardless of what the real implementation would eventually return for
that specific case. This means a handful of tests below that expect a 404
outcome (e.g. "prompt_id doesn't exist", "cross-prompt version id") will
PASS today, but only by accident - the route-not-found 404 happens to
numerically coincide with the spec's intended 404, even though nothing
real is being validated. Each such test is marked in its docstring with
"SPURIOUS PASS TODAY" so a future reader isn't misled by a green
checkmark that doesn't actually mean anything yet. All other tests here
(expecting 200/201/204, or a specific response body/shape/count) fail for
a real, meaningful reason today: the endpoint or side effect simply does
not exist.

No symbols from the unbuilt feature (e.g. `PromptVersion`) are imported
here - all interaction happens purely over HTTP via the existing `client`
fixture, so this file's own collection can never fail even though the
feature is unbuilt.
"""

import time

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# User Story 1 - Every edit is automatically recoverable (Priority: P1)
# Spec section: "User Story 1 - Every edit is automatically recoverable"
# ---------------------------------------------------------------------------


class TestAutomaticVersioning:
    """Covers spec User Story 1 (P1) acceptance scenarios 1-4: a version is
    captured automatically on create and on meaningful edits, no-op edits
    (collection_id only) do not create a version, and deleting a prompt
    cascades to delete its versions."""

    def test_creating_prompt_results_in_exactly_one_version(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 1, Acceptance Scenario 1: "Given a newly created
        prompt, When it is created, Then a version snapshot of its initial
        title, content, and description exists." Also "Error Conditions...":
        "POST /prompts... now also creates version 1 for the new prompt."
        GET /prompts/{id}/versions should report exactly one version
        immediately after creation.
        """
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["versions"]) == 1

    def test_initial_version_captures_creation_fields(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 1, Acceptance Scenario 1: the initial version's
        title/content/description must match what was submitted at
        creation time (data model: "snapshot of Prompt.title/content/
        description at capture time")."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        version = response.json()["versions"][0]
        assert version["title"] == sample_prompt_data["title"]
        assert version["content"] == sample_prompt_data["content"]
        assert version["description"] == sample_prompt_data["description"]
        assert version["version_number"] == 1
        assert version["prompt_id"] == created["id"]
        # Automatically-captured versions leave label null (data model table).
        assert version["label"] is None

    def test_put_edit_changing_title_creates_new_version(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 1, Acceptance Scenario 2: editing title/content/
        description via an edit and saving creates a new version snapshot
        capturing the state *before* that edit."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Changed Title", "content": created["content"]},
        )

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_put_edit_new_version_captures_pre_edit_state(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 1, Acceptance Scenario 2: the new snapshot must
        capture the state *before* the edit was applied - i.e. the newest
        version after an edit reflects the OLD title, not the new one."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        original_title = created["title"]

        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Changed Title", "content": created["content"]},
        )

        response = client.get(f"/prompts/{created['id']}/versions")
        versions = response.json()["versions"]
        # Ordered newest-first per the List endpoint contract.
        newest = versions[0]
        assert newest["version_number"] == 2
        assert newest["title"] == original_title

    def test_patch_edit_changing_content_creates_new_version(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 1, Acceptance Scenario 2 applies equally to
        PATCH edits, not just PUT - the spec says "edited... via an edit
        and saved" without distinguishing PUT vs PATCH."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        client.patch(
            f"/prompts/{created['id']}", json={"content": "New content body"}
        )

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.json()["total"] == 2

    def test_editing_only_collection_id_creates_no_new_version(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """Spec User Story 1, Acceptance Scenario 3: "Given an existing
        prompt, When it is edited but only its collection_id changes (no
        change to title, content, or description), Then no new version
        snapshot is created." Also "Error Conditions": "No-op field edits
        don't spam history"."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        collection = client.post("/collections", json=sample_collection_data).json()

        client.patch(
            f"/prompts/{created['id']}", json={"collection_id": collection["id"]}
        )

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_deleting_prompt_cascades_to_delete_all_its_versions(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 1, Acceptance Scenario 4 and "Relationship:
        Prompt -> PromptVersion" ("Deletion behavior: deleting a Prompt
        deletes all of its PromptVersions (cascade)").

        NOTE - SPURIOUS PASS TODAY: this assertion (GET .../versions ->
        404 after the parent prompt is deleted) will pass today, but only
        because the /prompts/{id}/versions route does not exist at all
        yet, so FastAPI's own routing layer 404s regardless of the prompt
        or its versions. It is not yet validating real cascade-delete
        behavior. See module docstring.
        """
        created = client.post("/prompts", json=sample_prompt_data).json()
        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Edit 1", "content": created["content"]},
        )

        client.delete(f"/prompts/{created['id']}")

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# User Story 2 - Browse and inspect version history (Priority: P2)
# Spec section: "User Story 2 - Browse and inspect version history"
# ---------------------------------------------------------------------------


class TestBrowseVersionHistory:
    """Covers spec User Story 2 (P2) acceptance scenarios 1-3 and the
    "List a prompt's version history" / "Get one specific version" API
    contracts."""

    def test_list_versions_returns_200_with_versions_and_total(
        self, client: TestClient, sample_prompt_data
    ):
        """API contract "List a prompt's version history": response 200
        with a `versions` list and a `total` count."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert "total" in data
        assert isinstance(data["versions"], list)

    def test_list_versions_ordered_newest_version_number_first(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 2, Acceptance Scenario 1 and the List endpoint
        contract: "Response 200, ordered newest (version_number) first."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Edit 1", "content": created["content"]},
        )
        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Edit 2", "content": created["content"]},
        )

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        version_numbers = [v["version_number"] for v in response.json()["versions"]]
        assert version_numbers == sorted(version_numbers, reverse=True)

    def test_list_versions_entry_contains_all_documented_fields(
        self, client: TestClient, sample_prompt_data
    ):
        """API contract sample response for GET /prompts/{id}/versions
        lists exactly: id, prompt_id, version_number, title, content,
        description, label, created_at per entry."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.get(f"/prompts/{created['id']}/versions")
        entry = response.json()["versions"][0]
        assert set(entry.keys()) == {
            "id", "prompt_id", "version_number", "title",
            "content", "description", "label", "created_at",
        }

    def test_get_one_version_returns_200_with_exact_snapshot(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 2, Acceptance Scenario 2: opening one specific
        version shows its full title/content/description exactly as they
        were at capture time. API contract "Get one specific version":
        response 200, single PromptVersion object."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        original_title = created["title"]
        original_content = created["content"]

        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Later Title", "content": "Later content"},
        )

        versions = client.get(f"/prompts/{created['id']}/versions").json()["versions"]
        original_version = [v for v in versions if v["version_number"] == 1][0]

        response = client.get(
            f"/prompts/{created['id']}/versions/{original_version['id']}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title
        assert data["content"] == original_content
        assert data["version_number"] == 1

    def test_never_edited_prompt_has_exactly_one_version(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 2, Acceptance Scenario 3: "Given a prompt that
        has never been edited since creation... exactly one version (the
        initial state) is shown."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.get(f"/prompts/{created['id']}/versions")
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_list_versions_prompt_not_found_returns_404(self, client: TestClient):
        """API contract "List a prompt's version history": "404 if
        prompt_id does not correspond to an existing prompt."

        NOTE - SPURIOUS PASS TODAY: this passes today only because the
        route itself does not exist, causing FastAPI's generic
        routing-level 404, not because any prompt-existence check ran.
        See module docstring.
        """
        response = client.get("/prompts/nonexistent-id/versions")
        assert response.status_code == 404

    def test_get_one_version_prompt_not_found_returns_404(self, client: TestClient):
        """API contract "Get one specific version": "404 if the prompt
        does not exist...".

        NOTE - SPURIOUS PASS TODAY: same routing-level reasoning as
        test_list_versions_prompt_not_found_returns_404. See module
        docstring.
        """
        response = client.get("/prompts/nonexistent-id/versions/also-nonexistent")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# User Story 3 - Restore a prompt to a previous version (Priority: P3)
# Spec section: "User Story 3 - Restore a prompt to a previous version"
# ---------------------------------------------------------------------------


class TestRestoreVersion:
    """Covers spec User Story 3 (P3) acceptance scenarios 1-3 and the
    "Restore a prompt to a previous version" API contract."""

    def test_restore_returns_200_with_updated_prompt_matching_restored_version(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 3, Acceptance Scenario 1: restoring a version
        makes the prompt's current title/content/description become that
        version's values. API contract: "Response 200: the updated Prompt
        (same shape as GET /prompts/{id})."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        original_title = created["title"]
        original_content = created["content"]
        original_description = created["description"]

        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Second wording", "content": "Second content"},
        )
        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Third wording", "content": "Third content"},
        )

        versions = client.get(f"/prompts/{created['id']}/versions").json()["versions"]
        first_version = [v for v in versions if v["version_number"] == 1][0]

        response = client.post(
            f"/prompts/{created['id']}/versions/{first_version['id']}/restore"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title
        assert data["content"] == original_content
        assert data["description"] == original_description

    def test_restore_refreshes_updated_at(
        self, client: TestClient, sample_prompt_data
    ):
        """API contract: restoring produces "the updated Prompt... with...
        updated_at refreshed" - consistent with constitution.md's rule
        that mutating a resource must refresh updated_at."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Second wording", "content": "Second content"},
        )
        versions = client.get(f"/prompts/{created['id']}/versions").json()["versions"]
        first_version = [v for v in versions if v["version_number"] == 1][0]

        time.sleep(0.1)
        response = client.post(
            f"/prompts/{created['id']}/versions/{first_version['id']}/restore"
        )
        assert response.status_code == 200
        assert response.json()["updated_at"] != created["updated_at"]

    def test_restore_leaves_collection_id_unchanged(
        self, client: TestClient, sample_collection_data
    ):
        """Spec User Story 3, Acceptance Scenario 3: "Given a prompt
        currently assigned to a collection, When the user restores an
        earlier version, Then the prompt remains assigned to its current
        collection." Also API contract: "collection_id unchanged."""
        collection = client.post("/collections", json=sample_collection_data).json()
        created = client.post(
            "/prompts",
            json={
                "title": "Title",
                "content": "Content",
                "collection_id": collection["id"],
            },
        ).json()

        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Edited", "content": "Edited content"},
        )
        versions = client.get(f"/prompts/{created['id']}/versions").json()["versions"]
        first_version = [v for v in versions if v["version_number"] == 1][0]

        response = client.post(
            f"/prompts/{created['id']}/versions/{first_version['id']}/restore"
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] == collection["id"]

    def test_restore_creates_new_version_capturing_pre_restore_state(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 3, Acceptance Scenario 2: "the prompt's state
        immediately before the restore is itself saved as a new version,
        so the restore can be undone the same way any other edit can."
        This verifies both the version-count increase AND that the
        newly-captured version reflects what was current right before the
        restore (not the restored-to content)."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        client.put(
            f"/prompts/{created['id']}",
            json={"title": "Second wording", "content": "Second content"},
        )
        # Two versions exist: v1 (original) and v2 (pre-second-edit == original,
        # since v2 captures state before the PUT). Current prompt state is
        # "Second wording"/"Second content".
        versions_before = client.get(
            f"/prompts/{created['id']}/versions"
        ).json()["versions"]
        count_before = len(versions_before)
        first_version_id = [
            v for v in versions_before if v["version_number"] == 1
        ][0]["id"]

        response = client.post(
            f"/prompts/{created['id']}/versions/{first_version_id}/restore"
        )
        assert response.status_code == 200

        versions_after = client.get(
            f"/prompts/{created['id']}/versions"
        ).json()["versions"]
        assert len(versions_after) == count_before + 1

        newest = versions_after[0]
        # The newest version must capture the pre-restore current state
        # ("Second wording"/"Second content"), not the restored-to state.
        assert newest["title"] == "Second wording"
        assert newest["content"] == "Second content"

    def test_restore_prompt_not_found_returns_404(self, client: TestClient):
        """API contract "Restore a prompt to a previous version": "404 if
        the prompt does not exist...".

        NOTE - SPURIOUS PASS TODAY: passes today only via FastAPI's
        routing-level 404 since the route doesn't exist. See module
        docstring.
        """
        response = client.post(
            "/prompts/nonexistent-id/versions/also-nonexistent/restore"
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# User Story 4 - Checkpoint and prune history on demand (Priority: P4)
# Spec section: "User Story 4 - Checkpoint and prune history on demand"
# ---------------------------------------------------------------------------


class TestCheckpointAndPrune:
    """Covers spec User Story 4 (P4) acceptance scenarios 1-2 and the
    "Manually save a checkpoint" / "Delete a version" API contracts."""

    def test_manual_checkpoint_with_label_returns_201_with_label_and_next_version_number(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 4, Acceptance Scenario 1: explicitly saving a
        checkpoint with a label creates a new version capturing current
        state with that label, even if nothing changed since the last
        version. API contract "Manually save a checkpoint": "Response
        201:... version_number set to one more than the highest existing
        version for that prompt."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.post(
            f"/prompts/{created['id']}/versions",
            json={"label": "before shortening"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "before shortening"
        # Only version 1 (from creation) existed before this checkpoint.
        assert data["version_number"] == 2
        assert data["title"] == created["title"]
        assert data["content"] == created["content"]
        assert data["description"] == created["description"]

    def test_manual_checkpoint_allows_duplicates_with_no_prior_changes(
        self, client: TestClient, sample_prompt_data
    ):
        """"Error Conditions": "Manual checkpoints allow duplicates:
        explicitly saving a checkpoint... when nothing has changed since
        the last version is allowed and still creates a new version."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        first = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "checkpoint A"}
        )
        second = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "checkpoint B"}
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert second.json()["version_number"] == first.json()["version_number"] + 1

        total = client.get(f"/prompts/{created['id']}/versions").json()["total"]
        assert total == 3  # creation version + two duplicate checkpoints

    def test_manual_checkpoint_with_no_body_is_allowed_and_unlabeled(
        self, client: TestClient, sample_prompt_data
    ):
        """API contract "Manually save a checkpoint": "Request body (all
        fields optional)." Omitting label entirely (empty JSON body) must
        still succeed and create a checkpoint whose label reflects that
        none was given (spec doesn't document a non-null default other
        than the field being optional/nullable per the data model table,
        so we assert None as the most reasonable interpretation - see
        report for this assumption)."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.post(f"/prompts/{created['id']}/versions", json={})
        assert response.status_code == 201
        data = response.json()
        assert data["label"] is None
        assert data["version_number"] == 2

    def test_manual_checkpoint_label_exceeding_max_length_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """Data model: "label... Optional, <= 100 characters." API
        contract "Manually save a checkpoint": "422 if label exceeds 100
        characters."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "x" * 101}
        )
        assert response.status_code == 422

    def test_manual_checkpoint_label_at_max_length_boundary_succeeds(
        self, client: TestClient, sample_prompt_data
    ):
        """Boundary check for the 100-character label limit: exactly 100
        characters is documented as the ceiling ("<= 100 characters"), so
        it must be accepted, not rejected."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        label = "x" * 100

        response = client.post(
            f"/prompts/{created['id']}/versions", json={"label": label}
        )
        assert response.status_code == 201
        assert response.json()["label"] == label

    def test_manual_checkpoint_prompt_not_found_returns_404(self, client: TestClient):
        """API contract "Manually save a checkpoint": "404 if the prompt
        does not exist."

        NOTE - SPURIOUS PASS TODAY: passes today only via FastAPI's
        routing-level 404 since the route doesn't exist. See module
        docstring.
        """
        response = client.post(
            "/prompts/nonexistent-id/versions", json={"label": "x"}
        )
        assert response.status_code == 404

    def test_delete_version_returns_204(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 4, Acceptance Scenario 2 and API contract
        "Delete a version": "Response 204 on success, no body."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        checkpoint = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "to be deleted"}
        ).json()

        response = client.delete(
            f"/prompts/{created['id']}/versions/{checkpoint['id']}"
        )
        assert response.status_code == 204
        assert response.content == b""

    def test_delete_version_removes_only_that_version(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 4, Acceptance Scenario 2: "that version no
        longer appears in the history, other versions are unaffected."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        checkpoint = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "to be deleted"}
        ).json()
        client.post(
            f"/prompts/{created['id']}/versions", json={"label": "survivor"}
        )

        client.delete(f"/prompts/{created['id']}/versions/{checkpoint['id']}")

        versions = client.get(f"/prompts/{created['id']}/versions").json()["versions"]
        version_ids = [v["id"] for v in versions]
        assert checkpoint["id"] not in version_ids
        assert len(versions) == 2  # creation version + "survivor" checkpoint

    def test_delete_version_leaves_prompt_current_state_unchanged(
        self, client: TestClient, sample_prompt_data
    ):
        """Spec User Story 4, Acceptance Scenario 2: "...and the prompt's
        current state is unchanged" after deleting a version."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        checkpoint = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "to be deleted"}
        ).json()

        client.delete(f"/prompts/{created['id']}/versions/{checkpoint['id']}")

        current = client.get(f"/prompts/{created['id']}").json()
        assert current["title"] == created["title"]
        assert current["content"] == created["content"]

    def test_delete_version_not_found_returns_404(self, client: TestClient):
        """API contract "Delete a version": "404 if the prompt does not
        exist, the version does not exist, or the version exists but does
        not belong to prompt_id."

        NOTE - SPURIOUS PASS TODAY: passes today only via FastAPI's
        routing-level 404 since the route doesn't exist. See module
        docstring.
        """
        response = client.delete(
            "/prompts/nonexistent-id/versions/also-nonexistent"
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Error Conditions and Edge Cases
# Spec section: "Error Conditions and Edge Cases"
# ---------------------------------------------------------------------------


class TestErrorConditionsAndEdgeCases:
    """Covers the spec's "Error Conditions and Edge Cases" section items
    not already exercised above: cross-prompt version ids, version-number
    non-reuse after deletion, restoring the current/latest version as a
    no-op, and the additive-only guarantee for existing endpoints."""

    def test_cross_prompt_version_id_get_returns_404(
        self, client: TestClient, sample_prompt_data
    ):
        """"Cross-prompt version IDs are treated as not found": a
        version_id that exists but belongs to a DIFFERENT prompt_id than
        the one in the URL returns 404, not the version from the other
        prompt.

        NOTE - NOT a spurious pass today: this test currently fails with
        a KeyError while setting up its precondition, because the
        GET /prompts/{prompt_b}/versions call used to obtain a real
        version_id itself 404s (the route doesn't exist yet at all). It
        never even reaches the cross-prompt assertion, so it is a
        genuine, meaningful failure - it is red for the right underlying
        reason (feature not built), just surfaced earlier than the final
        assert. See module docstring.
        """
        prompt_a = client.post("/prompts", json=sample_prompt_data).json()
        prompt_b = client.post(
            "/prompts", json={"title": "Other prompt", "content": "Other content"}
        ).json()

        versions_b = client.get(f"/prompts/{prompt_b['id']}/versions").json()
        version_b_id = versions_b["versions"][0]["id"]

        response = client.get(f"/prompts/{prompt_a['id']}/versions/{version_b_id}")
        assert response.status_code == 404

    def test_cross_prompt_version_id_restore_returns_404(
        self, client: TestClient, sample_prompt_data
    ):
        """Same cross-prompt-ownership rule applied to restore.

        NOTE - NOT a spurious pass today: same reasoning as
        test_cross_prompt_version_id_get_returns_404 - this fails with a
        KeyError while fetching prompt_b's version id (that GET itself
        404s), before ever reaching the restore call. A genuine failure,
        just surfaced during setup rather than at the final assert. See
        module docstring.
        """
        prompt_a = client.post("/prompts", json=sample_prompt_data).json()
        prompt_b = client.post(
            "/prompts", json={"title": "Other prompt", "content": "Other content"}
        ).json()

        versions_b = client.get(f"/prompts/{prompt_b['id']}/versions").json()
        version_b_id = versions_b["versions"][0]["id"]

        response = client.post(
            f"/prompts/{prompt_a['id']}/versions/{version_b_id}/restore"
        )
        assert response.status_code == 404

    def test_cross_prompt_version_id_delete_returns_404(
        self, client: TestClient, sample_prompt_data
    ):
        """Same cross-prompt-ownership rule applied to delete.

        NOTE - NOT a spurious pass today: same reasoning as
        test_cross_prompt_version_id_get_returns_404 - this fails with a
        KeyError while fetching prompt_b's version id (that GET itself
        404s), before ever reaching the delete call. A genuine failure,
        just surfaced during setup rather than at the final assert. See
        module docstring.
        """
        prompt_a = client.post("/prompts", json=sample_prompt_data).json()
        prompt_b = client.post(
            "/prompts", json={"title": "Other prompt", "content": "Other content"}
        ).json()

        versions_b = client.get(f"/prompts/{prompt_b['id']}/versions").json()
        version_b_id = versions_b["versions"][0]["id"]

        response = client.delete(
            f"/prompts/{prompt_a['id']}/versions/{version_b_id}"
        )
        assert response.status_code == 404

    def test_version_numbers_never_reused_after_deletion(
        self, client: TestClient, sample_prompt_data
    ):
        """"Version numbers are never reused": deleting version 2 out of
        [1, 2, 3] leaves [1, 3] - the next new version is still numbered
        4, not a reused 2.

        This is a genuinely meaningful (non-spurious) test once real,
        since it checks specific numeric behavior, not just a status
        code.
        """
        created = client.post("/prompts", json=sample_prompt_data).json()
        # Creation gives version 1. Two more checkpoints give versions 2, 3.
        v2 = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "v2"}
        ).json()
        client.post(f"/prompts/{created['id']}/versions", json={"label": "v3"})

        client.delete(f"/prompts/{created['id']}/versions/{v2['id']}")

        v4 = client.post(
            f"/prompts/{created['id']}/versions", json={"label": "v4"}
        )
        assert v4.status_code == 201
        assert v4.json()["version_number"] == 4

        remaining_numbers = {
            v["version_number"]
            for v in client.get(f"/prompts/{created['id']}/versions").json()[
                "versions"
            ]
        }
        assert 2 not in remaining_numbers
        assert remaining_numbers == {1, 3, 4}

    def test_restoring_current_latest_version_is_harmless_no_op_but_still_succeeds(
        self, client: TestClient, sample_prompt_data
    ):
        """"Restoring the current state is a harmless no-op": if a user
        restores a version that's identical to the prompt's current state
        (e.g. the latest version), the action still succeeds (200) and
        still creates a fresh snapshot of "current" beforehand - there is
        no special-cased short-circuit."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        # Latest/current version is version 1 (unedited since creation).
        versions_before = client.get(
            f"/prompts/{created['id']}/versions"
        ).json()["versions"]
        latest_version_id = versions_before[0]["id"]
        count_before = len(versions_before)

        response = client.post(
            f"/prompts/{created['id']}/versions/{latest_version_id}/restore"
        )
        assert response.status_code == 200
        assert response.json()["title"] == created["title"]
        assert response.json()["content"] == created["content"]

        versions_after = client.get(
            f"/prompts/{created['id']}/versions"
        ).json()["versions"]
        assert len(versions_after) == count_before + 1

    def test_post_prompts_response_shape_is_unchanged_by_versioning_feature(
        self, client: TestClient, sample_prompt_data
    ):
        """"This feature does not change the shape or behavior of any
        existing endpoint response; it is additive only" and "Version
        created on prompt creation:... The endpoint's response shape
        (201 Prompt) is unchanged." This is verifiable and meaningful
        RIGHT NOW against the current, pre-feature implementation, since
        it asserts what should NOT change.
        """
        response = client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201
        data = response.json()
        assert set(data.keys()) == {
            "title", "content", "description", "collection_id",
            "id", "created_at", "updated_at",
        }

    def test_delete_prompt_response_shape_is_unchanged_by_versioning_feature(
        self, client: TestClient, sample_prompt_data
    ):
        """"Cascade delete:... The endpoint's request/response shape
        (204/404) is unchanged." Verifiable and meaningful right now
        against the current, pre-feature implementation.
        """
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.delete(f"/prompts/{created['id']}")
        assert response.status_code == 204
        assert response.content == b""
