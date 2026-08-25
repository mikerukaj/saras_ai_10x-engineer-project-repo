"""API tests for PromptLab

These tests verify the API endpoints work correctly.
Students should expand these tests significantly in Week 3.
"""

from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app import __version__
from app.models import Prompt
from app.storage import storage as backend_storage


class TestHealth:
    """Tests for health endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """GET /health must respond 200 OK per the documented contract
        (docs/API_REFERENCE.md, specs/.../contracts/api-contract.md)."""
        response = client.get("/health")
        assert response.status_code == 300

    def test_health_check_status_is_healthy(self, client: TestClient):
        """status must always be the literal string "healthy" per the
        health_check docstring and API_REFERENCE.md sample response."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_version_matches_running_app_version(self, client: TestClient):
        """version must equal the running application's __version__, not a
        hardcoded/stale literal, per the health_check docstring."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == __version__

    def test_health_check_response_body_shape(self, client: TestClient):
        """Response body must contain exactly the fields declared on
        HealthResponse (status: str, version: str) - app/models.py."""
        response = client.get("/health")
        data = response.json()
        assert set(data.keys()) == {"status", "version"}
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)

    def test_health_check_content_type_is_json(self, client: TestClient):
        response = client.get("/health")
        assert response.headers["content-type"].startswith("application/json")


class TestPrompts:
    """Tests for prompt endpoints."""
    
    def test_create_prompt(self, client: TestClient, sample_prompt_data):
        """POST /prompts happy path must return 201 and the full Prompt
        shape (app/models.py Prompt; response_model=Prompt on the route),
        echoing back every submitted field plus server-generated id and
        timestamps - not just a subset. Source: create_prompt docstring
        ("Returns: The newly created prompt, with a generated id and
        creation/update timestamps"), docs/API_REFERENCE.md's POST
        /prompts sample response (id, title, content, description,
        collection_id, created_at, updated_at)."""
        response = client.post("/prompts", json=sample_prompt_data)
        assert response.status_code == 201
        data = response.json()

        assert set(data.keys()) == {
            "title", "content", "description", "collection_id",
            "id", "created_at", "updated_at",
        }
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert data["description"] == sample_prompt_data["description"]
        # No collection_id was submitted, so it must default to None per
        # PromptBase.collection_id's Optional[str] = None default.
        assert data["collection_id"] is None
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_prompt_persists_and_is_retrievable(
        self, client: TestClient, sample_prompt_data
    ):
        """The created prompt must actually be stored, not merely echoed
        back - storage.create_prompt docstring ("Store a new prompt") and
        the create_prompt route calling storage.create_prompt(prompt)
        before returning it."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.get(f"/prompts/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_create_prompt_without_description_defaults_to_none(
        self, client: TestClient
    ):
        """description is optional (PromptBase.description docstring: "An
        optional description") - omitting it entirely must succeed and
        yield None, not a validation error or an empty string."""
        response = client.post(
            "/prompts", json={"title": "No description", "content": "Some content"}
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_prompt_with_description_is_preserved(
        self, client: TestClient
    ):
        """When description is provided, it must be stored and returned
        verbatim, not dropped or truncated below its max_length=500."""
        response = client.post(
            "/prompts",
            json={
                "title": "Has description",
                "content": "Some content",
                "description": "A helpful description",
            },
        )
        assert response.status_code == 201
        assert response.json()["description"] == "A helpful description"

    def test_create_prompt_generates_unique_ids_across_multiple_creates(
        self, client: TestClient
    ):
        """Each call must generate a fresh unique id (models.generate_id
        docstring: "Generate a unique identifier string" via uuid4) -
        creating two otherwise-identical prompts must not collide or reuse
        an id."""
        first = client.post(
            "/prompts", json={"title": "Same title", "content": "Same content"}
        ).json()
        second = client.post(
            "/prompts", json={"title": "Same title", "content": "Same content"}
        ).json()

        assert first["id"] != second["id"]

    def test_create_prompt_sets_created_at_and_updated_at_close_together(
        self, client: TestClient, sample_prompt_data
    ):
        """On creation, created_at and updated_at both represent "now" -
        Prompt.created_at/updated_at docstrings both describe them as set
        "automatically" at creation, and docs/API_REFERENCE.md's sample
        response shows identical created_at/updated_at values for a newly
        created prompt. The model uses two independent default_factory
        calls (app/models.py Prompt.created_at / updated_at), so exact
        equality is not guaranteed at microsecond resolution; this test
        asserts they are within the same instant (a small delta) rather
        than assuming exact string equality, to avoid asserting on
        implementation-accidental precision."""
        response = client.post("/prompts", json=sample_prompt_data)
        data = response.json()

        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        assert abs((updated_at - created_at).total_seconds()) < 1.0

    def test_create_prompt_with_valid_collection_id_succeeds(
        self, client: TestClient, sample_collection_data
    ):
        """Providing a collection_id that references an existing
        collection must succeed and be echoed back on the created prompt -
        create_prompt docstring's Raises clause only fires when the
        collection does NOT exist; a valid reference is the documented
        non-error branch."""
        collection = client.post("/collections", json=sample_collection_data).json()

        response = client.post(
            "/prompts",
            json={
                "title": "In a collection",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        )
        assert response.status_code == 201
        assert response.json()["collection_id"] == collection["id"]

    def test_create_prompt_with_unknown_collection_id_returns_400(
        self, client: TestClient
    ):
        """A collection_id that does not correspond to any stored
        collection must return 400 with detail "Collection not found" -
        create_prompt docstring ("Raises: HTTPException: With status 400
        if prompt_data.collection_id is provided but does not correspond
        to an existing collection"), matching docs/API_REFERENCE.md's
        sample 400 response and api-contract.md's error shape
        ({"detail": "<message>"})."""
        response = client.post(
            "/prompts",
            json={
                "title": "Bad collection",
                "content": "Some content",
                "collection_id": "does-not-exist",
            },
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection not found"}

    def test_create_prompt_with_unknown_collection_id_does_not_persist_prompt(
        self, client: TestClient
    ):
        """When creation is rejected for an invalid collection_id, no
        prompt should be created as a side effect - the validation check
        (app/api.py lines 129-132) happens before storage.create_prompt is
        ever called, so a failed create must leave storage unchanged."""
        response = client.post(
            "/prompts",
            json={
                "title": "Should not be created",
                "content": "Some content",
                "collection_id": "does-not-exist",
            },
        )
        assert response.status_code == 400

        listed = client.get("/prompts").json()
        assert listed["total"] == 0
        assert listed["prompts"] == []

    def test_create_prompt_with_deleted_collection_id_returns_400(
        self, client: TestClient, sample_collection_data
    ):
        """A collection_id that referenced a real collection which has
        since been deleted must be treated the same as any other unknown
        collection_id - storage.get_collection is a plain dict lookup that
        returns None once the key is removed (storage.delete_collection),
        so create_prompt's `if not collection` check must reject it."""
        collection = client.post("/collections", json=sample_collection_data).json()
        client.delete(f"/collections/{collection['id']}")

        response = client.post(
            "/prompts",
            json={
                "title": "Stale collection ref",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection not found"}

    def test_create_prompt_missing_title_returns_422(self, client: TestClient):
        """title is a required field (PromptBase.title: Field(...,
        min_length=1, max_length=200) - the `...` marks it required in
        Pydantic). Omitting it must fail FastAPI's request validation with
        422, per api-contract.md's error shape section ("422 (request body
        fails Pydantic validation")."""
        response = client.post("/prompts", json={"content": "Some content"})
        assert response.status_code == 422

    def test_create_prompt_missing_content_returns_422(self, client: TestClient):
        """content is a required field (PromptBase.content: Field(...,
        min_length=1)). Omitting it must fail validation with 422."""
        response = client.post("/prompts", json={"title": "Some title"})
        assert response.status_code == 422

    def test_create_prompt_empty_title_returns_422(self, client: TestClient):
        """title has min_length=1 (PromptBase.title Field constraint) - an
        empty string must be rejected with 422, not silently accepted as a
        title-less prompt."""
        response = client.post(
            "/prompts", json={"title": "", "content": "Some content"}
        )
        assert response.status_code == 422

    def test_create_prompt_title_exceeding_max_length_returns_422(
        self, client: TestClient
    ):
        """title has max_length=200 (PromptBase.title Field constraint) -
        a 201-character title must be rejected with 422."""
        response = client.post(
            "/prompts", json={"title": "x" * 201, "content": "Some content"}
        )
        assert response.status_code == 422

    def test_create_prompt_title_at_max_length_boundary_succeeds(
        self, client: TestClient
    ):
        """A title of exactly 200 characters is within the documented
        boundary (max_length=200 is inclusive in Pydantic) and must be
        accepted."""
        title = "x" * 200
        response = client.post(
            "/prompts", json={"title": title, "content": "Some content"}
        )
        assert response.status_code == 201
        assert response.json()["title"] == title

    def test_create_prompt_empty_content_returns_422(self, client: TestClient):
        """content has min_length=1 (PromptBase.content Field constraint) -
        an empty string must be rejected with 422."""
        response = client.post(
            "/prompts", json={"title": "Some title", "content": ""}
        )
        assert response.status_code == 422

    def test_create_prompt_description_exceeding_max_length_returns_422(
        self, client: TestClient
    ):
        """description has max_length=500 (PromptBase.description Field
        constraint) - a 501-character description must be rejected with
        422."""
        response = client.post(
            "/prompts",
            json={
                "title": "Some title",
                "content": "Some content",
                "description": "x" * 501,
            },
        )
        assert response.status_code == 422

    def test_create_prompt_null_description_is_accepted(self, client: TestClient):
        """description is Optional[str] with default None - an explicit
        JSON null must be accepted the same as omitting the field
        entirely, not rejected as a type mismatch."""
        response = client.post(
            "/prompts",
            json={
                "title": "Null description",
                "content": "Some content",
                "description": None,
            },
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_prompt_null_collection_id_is_accepted(self, client: TestClient):
        """collection_id is Optional[str] = None - an explicit JSON null
        must be accepted and must not trigger the "Collection not found"
        validation branch (the route's `if prompt_data.collection_id:`
        check is falsy for None, so it must be skipped)."""
        response = client.post(
            "/prompts",
            json={
                "title": "Null collection",
                "content": "Some content",
                "collection_id": None,
            },
        )
        assert response.status_code == 201
        assert response.json()["collection_id"] is None

    def test_create_prompt_wrong_type_for_title_returns_422(self, client: TestClient):
        """title is typed as str; submitting a non-string, non-coercible
        value (a list) must fail Pydantic validation with 422 - FastAPI's
        default behavior per api-contract.md's error shape section."""
        response = client.post(
            "/prompts", json={"title": ["not", "a", "string"], "content": "Some content"}
        )
        assert response.status_code == 422

    def test_list_prompts_empty(self, client: TestClient):
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0
    
    def test_list_prompts_with_data(self, client: TestClient, sample_prompt_data):
        # Create a prompt first
        client.post("/prompts", json=sample_prompt_data)
        
        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 1
        assert data["total"] == 1
    
    def test_get_prompt_success(self, client: TestClient, sample_prompt_data):
        """GET /prompts/{id} for an existing id must return 200 and the
        full Prompt shape (app/models.py Prompt), not merely a matching id.

        Intended behavior source: get_prompt docstring ("Returns: The
        prompt if found"), response_model=Prompt on the route, and
        docs/API_REFERENCE.md's GET /prompts/{prompt_id} sample response,
        which lists exactly these seven fields.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        created = create_response.json()

        response = client.get(f"/prompts/{created['id']}")
        assert response.status_code == 200
        data = response.json()

        # Full response shape matches the Prompt model - not just "has an id".
        assert set(data.keys()) == {
            "title", "content", "description", "collection_id",
            "id", "created_at", "updated_at",
        }
        assert data["id"] == created["id"]
        assert data["title"] == sample_prompt_data["title"]
        assert data["content"] == sample_prompt_data["content"]
        assert data["description"] == sample_prompt_data["description"]
        assert data["collection_id"] is None
        assert data["created_at"] == created["created_at"]
        assert data["updated_at"] == created["updated_at"]

    def test_get_prompt_not_found_returns_404_with_documented_detail(self, client: TestClient):
        """GET /prompts/{id} for a missing id must return exactly 404 with
        the documented error detail shape.

        Intended behavior source: get_prompt docstring ("Raises:
        HTTPException: If prompt_id is not found."), api-contract.md's
        "Error shape" section (`{"detail": "<message>"}`), and
        .specify/memory/constitution.md line 46 ("404 (not 500) for
        missing"). The exact message "Prompt not found" comes from the
        HTTPException raised at app/api.py:104.
        """
        response = client.get("/prompts/nonexistent-id")
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_get_prompt_not_found_does_not_partially_match_existing_id(
        self, client: TestClient, sample_prompt_data
    ):
        """A lookup id that is a prefix/substring of a real prompt's id
        must still 404 - storage.get_prompt does an exact dict-key lookup
        (app/storage.py get_prompt docstring: "the matching prompt, or
        None if no prompt with prompt_id exists"), not a partial match."""
        create_response = client.post("/prompts", json=sample_prompt_data)
        real_id = create_response.json()["id"]

        response = client.get(f"/prompts/{real_id[:-1]}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_get_prompt_success_with_collection_id_populated(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """When a prompt belongs to a collection, GET /prompts/{id} must
        echo back that collection_id (PromptBase.collection_id docstring:
        "The identifier of the collection this prompt belongs to, if
        any."), not silently drop it."""
        collection = client.post("/collections", json=sample_collection_data).json()
        prompt_data = {**sample_prompt_data, "collection_id": collection["id"]}
        created = client.post("/prompts", json=prompt_data).json()

        response = client.get(f"/prompts/{created['id']}")
        assert response.status_code == 200
        assert response.json()["collection_id"] == collection["id"]

    def test_get_prompt_after_deletion_returns_404(
        self, client: TestClient, sample_prompt_data
    ):
        """A prompt that existed but was deleted must subsequently 404 on
        GET, not continue to be retrievable and not 500 - storage.get_prompt
        is a plain dict lookup keyed by id, and delete_prompt removes the
        key entirely (app/storage.py)."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        prompt_id = created["id"]

        client.delete(f"/prompts/{prompt_id}")

        response = client.get(f"/prompts/{prompt_id}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_delete_prompt(self, client: TestClient, sample_prompt_data):
        """DELETE /prompts/{id} for an existing prompt must return 204 and
        the prompt must no longer be retrievable afterwards.

        Intended behavior source: delete_prompt docstring ("Returns: None:
        No content is returned on successful deletion."), route decorator
        `status_code=204`, and docs/API_REFERENCE.md's DELETE
        /prompts/{prompt_id} sample response ("204 No Content (empty
        body)")."""
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        prompt_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/prompts/{prompt_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 404

    def test_delete_prompt_response_body_is_empty(
        self, client: TestClient, sample_prompt_data
    ):
        """A successful 204 response must carry no body content, per REST
        convention for 204 No Content and docs/API_REFERENCE.md's DELETE
        /prompts/{prompt_id} sample response ("204 No Content (empty
        body)"). The route also declares no response_model, reinforcing
        that no JSON body is intended."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.delete(f"/prompts/{created['id']}")
        assert response.status_code == 204
        assert response.content == b""

    def test_delete_prompt_not_found_returns_404_with_documented_detail(
        self, client: TestClient
    ):
        """DELETE /prompts/{id} for an id that never existed must return
        404 with the documented detail, not 500 or any 2xx status.

        Intended behavior source: delete_prompt docstring ("Raises:
        HTTPException: With status 404 if no prompt with prompt_id
        exists."), api-contract.md's Prompts table ("DELETE
        /prompts/{prompt_id} ... 204 | 404"), docs/API_REFERENCE.md's
        sample 404 response ({"detail": "Prompt not found"}), and
        constitution.md Principle III ("404 (not 500) for missing
        resources")."""
        response = client.delete("/prompts/nonexistent-id")
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_delete_prompt_twice_returns_404_on_second_delete(
        self, client: TestClient, sample_prompt_data
    ):
        """Deleting the same prompt a second time (double-delete) must
        404, not succeed again or 500 - storage.delete_prompt returns
        False once the id is no longer a key in its dict (app/storage.py
        delete_prompt docstring: "False if no prompt with prompt_id
        exists"), and delete_prompt in api.py raises 404 whenever
        storage.delete_prompt returns a falsy value."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        prompt_id = created["id"]

        first_response = client.delete(f"/prompts/{prompt_id}")
        assert first_response.status_code == 204

        second_response = client.delete(f"/prompts/{prompt_id}")
        assert second_response.status_code == 404
        assert second_response.json() == {"detail": "Prompt not found"}

    def test_delete_prompt_without_collection_id_succeeds(
        self, client: TestClient, sample_prompt_data
    ):
        """Deleting a prompt that has no collection_id (the common case,
        collection_id defaults to None per PromptBase) must succeed with
        204, the same as any other prompt - deleting a prompt has no
        documented dependency on whether it is assigned to a collection.
        Source: delete_prompt docstring/route, and storage.delete_prompt's
        implementation, which only ever inspects self._prompts, never
        collection_id or self._collections (app/storage.py)."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        assert created["collection_id"] is None

        response = client.delete(f"/prompts/{created['id']}")
        assert response.status_code == 204

    def test_delete_prompt_with_collection_id_succeeds_identically(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """Deleting a prompt that IS assigned to a collection must behave
        identically to deleting one that isn't - a plain 204, and no
        assertion is made anywhere that this depends on collection_id.
        Source: delete_prompt docstring/route (no mention of collections),
        and storage.delete_prompt's implementation, which never reads or
        writes self._collections (app/storage.py delete_prompt, lines
        115-134) - unlike delete_collection, which explicitly unassigns
        its prompts (app/storage.py delete_collection / api.py
        delete_collection; docs/API_REFERENCE.md: "Deletes a collection.
        Any prompts assigned to it are unassigned")."""
        collection = client.post("/collections", json=sample_collection_data).json()
        prompt_data = {**sample_prompt_data, "collection_id": collection["id"]}
        created = client.post("/prompts", json=prompt_data).json()
        assert created["collection_id"] == collection["id"]

        response = client.delete(f"/prompts/{created['id']}")
        assert response.status_code == 204

        get_response = client.get(f"/prompts/{created['id']}")
        assert get_response.status_code == 404

    def test_delete_prompt_does_not_delete_its_collection(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """Deleting a prompt must never delete or otherwise remove the
        collection it belonged to - only delete_collection is documented
        to have any cross-resource side effect, and that side effect runs
        in the opposite direction (collection -> prompts, not
        prompt -> collection). Source: docs/API_REFERENCE.md's DELETE
        /prompts/{prompt_id} entry describes only "Deletes a prompt by
        id." with no mention of collections; storage.delete_prompt only
        ever touches self._prompts (app/storage.py, lines 115-134)."""
        collection = client.post("/collections", json=sample_collection_data).json()
        prompt_data = {**sample_prompt_data, "collection_id": collection["id"]}
        created = client.post("/prompts", json=prompt_data).json()

        client.delete(f"/prompts/{created['id']}")

        get_collection_response = client.get(f"/collections/{collection['id']}")
        assert get_collection_response.status_code == 200
        assert get_collection_response.json()["id"] == collection["id"]

    def test_delete_prompt_does_not_affect_other_prompts(
        self, client: TestClient, sample_prompt_data
    ):
        """Deleting one prompt must not remove or alter any other prompt
        in storage - storage.delete_prompt only deletes the single key
        matching the given prompt_id from self._prompts (app/storage.py,
        lines 131-133), leaving every other entry untouched."""
        deleted = client.post("/prompts", json=sample_prompt_data).json()
        survivor_data = {**sample_prompt_data, "title": "Untouched Prompt"}
        survivor = client.post("/prompts", json=survivor_data).json()

        response = client.delete(f"/prompts/{deleted['id']}")
        assert response.status_code == 204

        get_survivor_response = client.get(f"/prompts/{survivor['id']}")
        assert get_survivor_response.status_code == 200
        assert get_survivor_response.json()["title"] == "Untouched Prompt"

    def test_update_prompt(self, client: TestClient, sample_prompt_data):
        """PUT /prompts/{id} happy path must return 200, echo back every
        replaced field, and refresh updated_at.

        Intended behavior source: update_prompt docstring ("Preserves the
        original prompt's ID and creation timestamp. The updated_at
        timestamp is set to the current time"), docs/API_REFERENCE.md's
        PUT /prompts/{prompt_id} section ("Preserves id and created_at;
        refreshes updated_at"), and constitution.md Principle III (API
        Contract Integrity): "Mutating a resource MUST refresh its
        updated_at timestamp."

        Ground truth on the historical "Bug #2" comment this test used to
        carry: verified by tracing get_current_time() (app/models.py:23-34,
        using datetime.utcnow(), which has microsecond resolution) and by
        running this exact scenario directly against the app - the route
        (app/api.py:175) calls get_current_time() fresh on every PUT, so
        updated_at reliably changes after a 0.1s sleep. The comment
        claiming this assertion "will fail due to Bug #2" is stale; the
        bug is not present in the current code and the assertion passes.
        """
        # Create a prompt first
        create_response = client.post("/prompts", json=sample_prompt_data)
        created = create_response.json()
        prompt_id = created["id"]
        original_updated_at = created["updated_at"]
        original_created_at = created["created_at"]

        # Update it
        updated_data = {
            "title": "Updated Title",
            "content": "Updated content for the prompt",
            "description": "Updated description"
        }

        import time
        time.sleep(0.1)  # Small delay to ensure timestamp would change

        response = client.put(f"/prompts/{prompt_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content for the prompt"
        assert data["description"] == "Updated description"
        # id and created_at must be preserved verbatim (update_prompt
        # docstring: "Preserves the original prompt's ID and creation
        # timestamp").
        assert data["id"] == prompt_id
        assert data["created_at"] == original_created_at
        # updated_at must be refreshed - this is the behavior the stale
        # "Bug #2" comment claimed was broken; verified above that it is
        # not.
        assert data["updated_at"] != original_updated_at

    def test_update_prompt_response_shape_matches_prompt_model(
        self, client: TestClient, sample_prompt_data
    ):
        """PUT /prompts/{id} response must contain exactly the fields
        declared on the Prompt model (response_model=Prompt on the route),
        matching docs/API_REFERENCE.md's PUT sample response shape."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "New Title", "content": "New content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {
            "title", "content", "description", "collection_id",
            "id", "created_at", "updated_at",
        }

    def test_update_prompt_clears_description_when_omitted(
        self, client: TestClient, sample_prompt_data
    ):
        """PUT is a full replace, not a partial update (update_prompt
        docstring / PromptUpdate(PromptBase) - description has no
        "leave unchanged if omitted" semantics, unlike PATCH). Omitting
        description from the PUT body must clear it to None, per
        docs/API_REFERENCE.md's "Fully replaces ... All fields in the
        body are required (full replace, not a partial update - use
        PATCH for that)."."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        assert created["description"] is not None  # sanity: fixture sets one

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "No description now", "content": "Some content"},
        )
        assert response.status_code == 200
        assert response.json()["description"] is None

    def test_update_prompt_can_assign_a_collection_id(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """Providing a valid collection_id on PUT must succeed and be
        reflected on the updated prompt - update_prompt docstring's Raises
        clause only fires when the collection does NOT exist; a valid
        reference is the documented non-error branch."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        collection = client.post("/collections", json=sample_collection_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={
                "title": created["title"],
                "content": created["content"],
                "collection_id": collection["id"],
            },
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] == collection["id"]

    def test_update_prompt_omitting_collection_id_clears_existing_assignment(
        self, client: TestClient, sample_collection_data
    ):
        """Full-replace PUT semantics mean an existing collection_id is
        cleared (set to None) if the PUT body omits it - PromptUpdate's
        collection_id has no "leave unchanged" behavior (that is PATCH's
        job per PromptPatch/patch_prompt), and PromptBase.collection_id
        defaults to None when absent from the payload."""
        collection = client.post("/collections", json=sample_collection_data).json()
        created = client.post(
            "/prompts",
            json={
                "title": "In a collection",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        ).json()
        assert created["collection_id"] == collection["id"]  # sanity

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "Now unassigned", "content": "Some content"},
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] is None

    def test_update_prompt_with_explicit_null_collection_id_clears_it(
        self, client: TestClient, sample_collection_data
    ):
        """An explicit JSON null for collection_id must behave the same as
        omitting it - the route's `if prompt_data.collection_id:` check
        (app/api.py:163) is falsy for None, so validation is skipped and
        the prompt ends up unassigned."""
        collection = client.post("/collections", json=sample_collection_data).json()
        created = client.post(
            "/prompts",
            json={
                "title": "In a collection",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        ).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={
                "title": "Now unassigned",
                "content": "Some content",
                "collection_id": None,
            },
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] is None

    def test_update_prompt_not_found_returns_404_with_documented_detail(
        self, client: TestClient
    ):
        """PUT /prompts/{id} for a missing id must return 404 with the
        documented error detail shape - update_prompt docstring ("Raises:
        HTTPException: With status 404 if no prompt with prompt_id
        exists"), api-contract.md's error shape section, and
        constitution.md Principle III ("404 (not 500) for missing
        resources")."""
        response = client.put(
            "/prompts/nonexistent-id",
            json={"title": "Doesn't matter", "content": "Doesn't matter"},
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_update_prompt_after_deletion_returns_404(
        self, client: TestClient, sample_prompt_data
    ):
        """A prompt that existed but was deleted must 404 on PUT, not be
        silently recreated - storage.get_prompt is a plain dict lookup
        keyed by id, and delete_prompt removes the key entirely
        (app/storage.py)."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        client.delete(f"/prompts/{created['id']}")

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "Should not work", "content": "Some content"},
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_update_prompt_with_unknown_collection_id_returns_400(
        self, client: TestClient, sample_prompt_data
    ):
        """A collection_id that does not correspond to any stored
        collection must return 400 with detail "Collection not found" -
        update_prompt docstring ("Raises: HTTPException: With status 400
        if prompt_data.collection_id is provided but does not correspond
        to an existing collection"), matching docs/API_REFERENCE.md's PUT
        errors list and api-contract.md's error shape."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={
                "title": "Bad collection",
                "content": "Some content",
                "collection_id": "does-not-exist",
            },
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection not found"}

    def test_update_prompt_with_unknown_collection_id_does_not_modify_existing_prompt(
        self, client: TestClient, sample_prompt_data
    ):
        """When an update is rejected for an invalid collection_id, the
        existing prompt must be left completely unchanged as a side
        effect - the validation check (app/api.py:163-166) happens before
        storage.update_prompt is ever called, so a failed update must not
        mutate title, content, description, or updated_at."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={
                "title": "Should not be applied",
                "content": "Should not be applied",
                "collection_id": "does-not-exist",
            },
        )
        assert response.status_code == 400

        unchanged = client.get(f"/prompts/{created['id']}").json()
        assert unchanged["title"] == created["title"]
        assert unchanged["content"] == created["content"]
        assert unchanged["description"] == created["description"]
        assert unchanged["updated_at"] == created["updated_at"]

    def test_update_prompt_with_deleted_collection_id_returns_400(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """A collection_id that referenced a real collection which has
        since been deleted must be treated the same as any other unknown
        collection_id - storage.get_collection is a plain dict lookup that
        returns None once the key is removed (storage.delete_collection)."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        collection = client.post("/collections", json=sample_collection_data).json()
        client.delete(f"/collections/{collection['id']}")

        response = client.put(
            f"/prompts/{created['id']}",
            json={
                "title": "Stale collection ref",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection not found"}

    def test_update_prompt_missing_title_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """title is required on PromptUpdate (PromptBase.title:
        Field(..., min_length=1, max_length=200), and PromptUpdate is a
        full-replace PUT body, not partial). Omitting it must fail request
        validation with 422, per api-contract.md's error shape section."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}", json={"content": "Some content"}
        )
        assert response.status_code == 422

    def test_update_prompt_missing_content_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """content is required on PromptUpdate (PromptBase.content:
        Field(..., min_length=1)). Omitting it must fail validation with
        422 on PUT, the same as on POST."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}", json={"title": "Some title"}
        )
        assert response.status_code == 422

    def test_update_prompt_empty_title_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """title has min_length=1 (PromptBase.title Field constraint) - an
        empty string must be rejected with 422 on PUT, not silently
        accepted."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "", "content": "Some content"},
        )
        assert response.status_code == 422

    def test_update_prompt_empty_content_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """content has min_length=1 (PromptBase.content Field constraint) -
        an empty string must be rejected with 422 on PUT."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "Some title", "content": ""},
        )
        assert response.status_code == 422

    def test_update_prompt_title_exceeding_max_length_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """title has max_length=200 (PromptBase.title Field constraint) -
        a 201-character title must be rejected with 422 on PUT."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={"title": "x" * 201, "content": "Some content"},
        )
        assert response.status_code == 422

    def test_update_prompt_description_exceeding_max_length_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """description has max_length=500 (PromptBase.description Field
        constraint) - a 501-character description must be rejected with
        422 on PUT."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}",
            json={
                "title": "Some title",
                "content": "Some content",
                "description": "x" * 501,
            },
        )
        assert response.status_code == 422

    def test_update_prompt_invalid_body_does_not_reach_storage(
        self, client: TestClient, sample_prompt_data
    ):
        """FastAPI/Pydantic request validation (422) must happen before the
        route body runs, so a validation failure must not touch storage at
        all - the existing prompt must be completely unchanged (data-model
        contract: request validation precedes handler execution)."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.put(
            f"/prompts/{created['id']}", json={"content": "Missing title"}
        )
        assert response.status_code == 422

        unchanged = client.get(f"/prompts/{created['id']}").json()
        assert unchanged["title"] == created["title"]
        assert unchanged["updated_at"] == created["updated_at"]

    # ---------- PATCH /prompts/{prompt_id} ----------
    # Intended-behavior sources: patch_prompt docstring (app/api.py:181-220,
    # "Fields omitted from the request body are left unchanged. The
    # updated_at timestamp is always refreshed on a successful update.");
    # PromptPatch model (app/models.py:70-92, all four fields Optional with
    # default None, used with model_dump(exclude_unset=True) for true
    # partial-update semantics); api-contract.md line 21 ("PromptPatch body
    # (partial)" -> 200/404/400/422); docs/API_REFERENCE.md's PATCH section
    # ("only the fields included in the body are changed; omitted fields are
    # left as-is. updated_at is always refreshed on success"); and
    # constitution.md Principle III ("Mutating a resource MUST refresh its
    # updated_at timestamp").

    def test_patch_prompt_single_field_leaves_other_fields_unchanged(
        self, client: TestClient, sample_prompt_data
    ):
        """Patching only title must leave content/description/collection_id
        genuinely untouched - this is the core distinction between PATCH's
        exclude_unset semantics and PUT's full-replace semantics (patch_prompt
        docstring: "Fields omitted from the request body are left
        unchanged")."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "New Title Only"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title Only"
        assert data["content"] == created["content"]
        assert data["description"] == created["description"]
        assert data["collection_id"] == created["collection_id"]

    def test_patch_prompt_multiple_fields_at_once(
        self, client: TestClient, sample_prompt_data
    ):
        """Patching several fields in one request must apply all of them,
        and any field not included must remain unchanged."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}",
            json={"title": "Multi Title", "content": "Multi content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Multi Title"
        assert data["content"] == "Multi content"
        assert data["description"] == created["description"]

    def test_patch_prompt_empty_body_returns_200_and_leaves_fields_unchanged(
        self, client: TestClient, sample_prompt_data
    ):
        """An empty PATCH body has no fields set, so exclude_unset=True
        produces an empty patch dict - every field falls back to its
        existing value via patch.get(field, existing.field). The request
        is still a well-formed partial update (all fields optional per
        PromptPatch), so this must succeed with 200, not error."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(f"/prompts/{created['id']}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == created["title"]
        assert data["content"] == created["content"]
        assert data["description"] == created["description"]
        assert data["collection_id"] == created["collection_id"]

    def test_patch_prompt_updated_at_refreshed_on_success(
        self, client: TestClient, sample_prompt_data
    ):
        """updated_at must always be refreshed on a successful PATCH, per
        the patch_prompt docstring's explicit statement, mirroring the
        already-verified-correct behavior of update_prompt (PUT)."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        original_updated_at = created["updated_at"]

        import time
        time.sleep(0.1)

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "Refresh check"}
        )
        assert response.status_code == 200
        assert response.json()["updated_at"] != original_updated_at

    def test_patch_prompt_updated_at_refreshed_even_with_empty_body(
        self, client: TestClient, sample_prompt_data
    ):
        """The docstring says updated_at is "always refreshed on a
        successful update" with no carve-out for an empty patch body, so
        even a no-field PATCH must still bump updated_at."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        original_updated_at = created["updated_at"]

        import time
        time.sleep(0.1)

        response = client.patch(f"/prompts/{created['id']}", json={})
        assert response.status_code == 200
        assert response.json()["updated_at"] != original_updated_at

    def test_patch_prompt_preserves_id_and_created_at(
        self, client: TestClient, sample_prompt_data
    ):
        """id and created_at must be preserved verbatim across a PATCH,
        same contract as PUT (patch_prompt constructs Prompt with
        id=existing.id and created_at=existing.created_at)."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "Changed"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["created_at"] == created["created_at"]

    def test_patch_prompt_response_shape_matches_prompt_model(
        self, client: TestClient, sample_prompt_data
    ):
        """PATCH /prompts/{id} response must contain exactly the fields
        declared on the Prompt model (response_model=Prompt on the
        route)."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "Shape check"}
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {
            "title", "content", "description", "collection_id",
            "id", "created_at", "updated_at",
        }

    def test_patch_prompt_description_can_be_set_to_a_real_value(
        self, client: TestClient
    ):
        """Patching description with a real string must update it, even
        when the prompt previously had no description."""
        created = client.post(
            "/prompts", json={"title": "T", "content": "C"}
        ).json()
        assert created["description"] is None  # sanity: no fixture desc

        response = client.patch(
            f"/prompts/{created['id']}",
            json={"description": "Now has a description"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Now has a description"

    def test_patch_prompt_omitting_description_leaves_it_unchanged(
        self, client: TestClient, sample_prompt_data
    ):
        """Omitting description entirely (unlike PUT) must leave the
        existing description untouched - this is PATCH's defining
        difference from PUT's test_update_prompt_clears_description_when_omitted."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        assert created["description"] is not None  # sanity: fixture sets one

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "Only title changes"}
        )
        assert response.status_code == 200
        assert response.json()["description"] == created["description"]

    def test_patch_prompt_explicit_null_description_clears_it(
        self, client: TestClient, sample_prompt_data
    ):
        """Explicitly sending description: null must clear it, since
        description is legitimately Optional[str] on both PromptPatch and
        the persisted Prompt model - unlike title/content, None is a valid
        final value here, not just a partial-update sentinel."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        assert created["description"] is not None  # sanity

        response = client.patch(
            f"/prompts/{created['id']}", json={"description": None}
        )
        assert response.status_code == 200
        assert response.json()["description"] is None

    def test_patch_prompt_omitting_collection_id_leaves_existing_assignment_unchanged(
        self, client: TestClient, sample_collection_data
    ):
        """Omitting collection_id from a PATCH body must leave the existing
        assignment untouched - this is the headline behavioral difference
        from PUT (test_update_prompt_omitting_collection_id_clears_existing_assignment),
        and is the entire reason exclude_unset=True is used here."""
        collection = client.post("/collections", json=sample_collection_data).json()
        created = client.post(
            "/prompts",
            json={
                "title": "In a collection",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        ).json()
        assert created["collection_id"] == collection["id"]  # sanity

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "Still in collection"}
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] == collection["id"]

    def test_patch_prompt_can_assign_a_collection_id(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """Providing a valid collection_id on PATCH must succeed and be
        reflected on the updated prompt."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        collection = client.post("/collections", json=sample_collection_data).json()

        response = client.patch(
            f"/prompts/{created['id']}",
            json={"collection_id": collection["id"]},
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] == collection["id"]

    def test_patch_prompt_with_explicit_null_collection_id_clears_it(
        self, client: TestClient, sample_collection_data
    ):
        """Verified directly against the running app (not just traced):
        explicit JSON null for collection_id on PATCH must clear an
        existing assignment. Per the route (app/api.py:207), `"collection_id"
        in patch` is True but `patch["collection_id"] is not None` is False,
        so the 400-validation branch is skipped, and
        `patch.get("collection_id", existing.collection_id)` (app/api.py:216)
        returns the explicit None, clearing the assignment - distinct from
        simply omitting the field, which leaves it unchanged (see
        test_patch_prompt_omitting_collection_id_leaves_existing_assignment_unchanged)."""
        collection = client.post("/collections", json=sample_collection_data).json()
        created = client.post(
            "/prompts",
            json={
                "title": "In a collection",
                "content": "Some content",
                "collection_id": collection["id"],
            },
        ).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"collection_id": None}
        )
        assert response.status_code == 200
        assert response.json()["collection_id"] is None

    def test_patch_prompt_not_found_returns_404_with_documented_detail(
        self, client: TestClient
    ):
        """PATCH /prompts/{id} for a missing id must return 404 with the
        documented error detail shape - patch_prompt docstring ("Raises:
        HTTPException: With status 404 if no prompt with prompt_id
        exists")."""
        response = client.patch(
            "/prompts/nonexistent-id", json={"title": "Doesn't matter"}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_patch_prompt_after_deletion_returns_404(
        self, client: TestClient, sample_prompt_data
    ):
        """A prompt that existed but was deleted must 404 on PATCH, not be
        silently recreated."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        client.delete(f"/prompts/{created['id']}")

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "Should not work"}
        )
        assert response.status_code == 404
        assert response.json() == {"detail": "Prompt not found"}

    def test_patch_prompt_with_unknown_collection_id_returns_400(
        self, client: TestClient, sample_prompt_data
    ):
        """A non-null collection_id that does not correspond to any stored
        collection must return 400 with detail "Collection not found" -
        patch_prompt docstring ("Raises: HTTPException: With status 400 if
        collection_id is explicitly provided and does not correspond to an
        existing collection")."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}",
            json={"collection_id": "does-not-exist"},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection not found"}

    def test_patch_prompt_with_unknown_collection_id_does_not_modify_existing_prompt(
        self, client: TestClient, sample_prompt_data
    ):
        """When a PATCH is rejected for an invalid collection_id, the
        existing prompt must be left completely unchanged - the validation
        check (app/api.py:207-209) happens before storage.update_prompt is
        ever called."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}",
            json={"title": "Should not be applied", "collection_id": "does-not-exist"},
        )
        assert response.status_code == 400

        unchanged = client.get(f"/prompts/{created['id']}").json()
        assert unchanged["title"] == created["title"]
        assert unchanged["updated_at"] == created["updated_at"]

    def test_patch_prompt_with_deleted_collection_id_returns_400(
        self, client: TestClient, sample_prompt_data, sample_collection_data
    ):
        """A collection_id that referenced a real collection which has
        since been deleted must be treated the same as any other unknown
        collection_id."""
        created = client.post("/prompts", json=sample_prompt_data).json()
        collection = client.post("/collections", json=sample_collection_data).json()
        client.delete(f"/collections/{collection['id']}")

        response = client.patch(
            f"/prompts/{created['id']}",
            json={"collection_id": collection["id"]},
        )
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection not found"}

    def test_patch_prompt_empty_title_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """title has min_length=1 on PromptPatch (Field(None, min_length=1,
        max_length=200)) - an explicit empty string must be rejected with
        422 by FastAPI's request validation before the handler ever runs
        (verified directly: PromptPatch's string-length constraint applies
        whenever a string is actually provided, unlike passing None)."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(f"/prompts/{created['id']}", json={"title": ""})
        assert response.status_code == 422

    def test_patch_prompt_empty_content_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """content has min_length=1 on PromptPatch - an explicit empty
        string must be rejected with 422."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(f"/prompts/{created['id']}", json={"content": ""})
        assert response.status_code == 422

    def test_patch_prompt_title_exceeding_max_length_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """title has max_length=200 on PromptPatch - a 201-character title
        must be rejected with 422."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "x" * 201}
        )
        assert response.status_code == 422

    def test_patch_prompt_description_exceeding_max_length_returns_422(
        self, client: TestClient, sample_prompt_data
    ):
        """description has max_length=500 on PromptPatch - a 501-character
        description must be rejected with 422."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"description": "x" * 501}
        )
        assert response.status_code == 422

    def test_patch_prompt_invalid_body_does_not_reach_storage(
        self, client: TestClient, sample_prompt_data
    ):
        """A 422 request-validation failure must happen before the route
        body runs, so the existing prompt must be completely unchanged."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": "x" * 201}
        )
        assert response.status_code == 422

        unchanged = client.get(f"/prompts/{created['id']}").json()
        assert unchanged["title"] == created["title"]
        assert unchanged["updated_at"] == created["updated_at"]

    def test_patch_prompt_explicit_null_title_returns_4xx_not_500(
        self, client: TestClient, sample_prompt_data
    ):
        """A client explicitly sending `{"title": null}` should receive a
        clean 4xx (422, per api-contract.md's documented error shape:
        "422 (request body fails Pydantic validation)"), never an unhandled
        500/exception - a required, non-Optional field on the persisted
        Prompt model (title: str = Field(..., min_length=1, max_length=200),
        app/models.py:56) ending up None is exactly the kind of bad-data
        state the API contract says must be rejected cleanly, not crash on.

        This is the documented/reasonable expectation, not the literal
        current behavior - see bug report if this fails.
        """
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"title": None}
        )
        assert response.status_code in (400, 422), (
            f"Expected a clean 4xx for an explicit null on a required field, "
            f"got {response.status_code}: {response.text}"
        )

    def test_patch_prompt_explicit_null_content_returns_4xx_not_500(
        self, client: TestClient, sample_prompt_data
    ):
        """Same reasoning as test_patch_prompt_explicit_null_title_returns_4xx_not_500,
        but for content (content: str = Field(..., min_length=1),
        app/models.py:57), the other required-non-Optional field on Prompt."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        response = client.patch(
            f"/prompts/{created['id']}", json={"content": None}
        )
        assert response.status_code in (400, 422), (
            f"Expected a clean 4xx for an explicit null on a required field, "
            f"got {response.status_code}: {response.text}"
        )

    def test_patch_prompt_explicit_null_title_does_not_corrupt_storage(
        self, client: TestClient, sample_prompt_data
    ):
        """Regardless of which status code an explicit null title produces,
        it must not leave the stored prompt in a broken/half-updated state -
        a subsequent GET for the same id must still succeed and return the
        original title, not error out or return a corrupted record."""
        created = client.post("/prompts", json=sample_prompt_data).json()

        client.patch(f"/prompts/{created['id']}", json={"title": None})

        followup = client.get(f"/prompts/{created['id']}")
        assert followup.status_code == 200, (
            f"A rejected/failed PATCH must not corrupt the stored prompt; "
            f"follow-up GET returned {followup.status_code}: {followup.text}"
        )
        assert followup.json()["title"] == created["title"]

    def test_sorting_order(self, client: TestClient):
        """Test that prompts are sorted newest first.
        
        """
        import time
        
        # Create prompts with delay
        prompt1 = {"title": "First", "content": "First prompt content"}
        prompt2 = {"title": "Second", "content": "Second prompt content"}
        
        client.post("/prompts", json=prompt1)
        time.sleep(0.1)
        client.post("/prompts", json=prompt2)
        
        response = client.get("/prompts")
        prompts = response.json()["prompts"]
        
        # Newest (Second) should be first
        assert prompts[0]["title"] == "Second" 
    # ---- Additional list_prompts coverage: no-filter, collection_id,
    # ---- search, combined filters, sorting, and total-count invariant.
    # ---- Intended behavior source: list_prompts docstring (app/api.py),
    # ---- filter_prompts_by_collection/search_prompts/sort_prompts_by_date
    # ---- docstrings (app/utils.py), and docs/API_REFERENCE.md's
    # ---- "GET /prompts" section.

    def test_list_prompts_no_filters_returns_all_prompts(self, client: TestClient):
        """With no query params, every stored prompt must be returned."""
        client.post("/prompts", json={"title": "One", "content": "Content one"})
        client.post("/prompts", json={"title": "Two", "content": "Content two"})
        client.post("/prompts", json={"title": "Three", "content": "Content three"})

        response = client.get("/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 3
        assert {p["title"] for p in data["prompts"]} == {"One", "Two", "Three"}

    def test_list_prompts_total_always_matches_returned_prompts_length(self, client: TestClient):
        """total must equal len(prompts) per the PromptList/list_prompts docstring,
        regardless of how many prompts exist or which filters are applied."""
        client.post("/prompts", json={"title": "One", "content": "Content one"})
        client.post("/prompts", json={"title": "Two", "content": "Content two"})

        response = client.get("/prompts")
        data = response.json()
        assert data["total"] == len(data["prompts"])
        assert data["total"] == 2

    def test_list_prompts_filter_by_collection_id_returns_only_matching(self, client: TestClient):
        """collection_id filter must include only prompts belonging to that
        collection (filter_prompts_by_collection docstring, app/utils.py)."""
        col_a = client.post("/collections", json={"name": "Collection A"}).json()
        col_b = client.post("/collections", json={"name": "Collection B"}).json()

        client.post("/prompts", json={
            "title": "In A", "content": "Belongs to A", "collection_id": col_a["id"]
        })
        client.post("/prompts", json={
            "title": "In B", "content": "Belongs to B", "collection_id": col_b["id"]
        })
        client.post("/prompts", json={"title": "Unassigned", "content": "No collection"})

        response = client.get("/prompts", params={"collection_id": col_a["id"]})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["title"] == "In A"
        assert data["prompts"][0]["collection_id"] == col_a["id"]

    def test_list_prompts_filter_by_nonexistent_collection_id_returns_empty(self, client: TestClient):
        """A collection_id that matches no prompt's collection_id yields an
        empty result set, not an error - filter_prompts_by_collection is a
        plain equality filter with no existence validation of the id itself
        (app/utils.py docstring says nothing about raising/validating).
        No written spec resolves this explicitly (spec.md Edge Cases lists
        it as an open question); inferred intent from the filter function's
        docstring/signature, which describes simple equality matching."""
        client.post("/prompts", json={"title": "Orphan-ish", "content": "No real collection"})

        response = client.get("/prompts", params={"collection_id": "does-not-exist"})
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_search_matches_title_case_insensitively(self, client: TestClient):
        """search must match against title case-insensitively (search_prompts
        docstring, app/utils.py)."""
        client.post("/prompts", json={"title": "Cold Outreach Email", "content": "Body text"})
        client.post("/prompts", json={"title": "Unrelated", "content": "Body text"})

        response = client.get("/prompts", params={"search": "EMAIL"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["prompts"][0]["title"] == "Cold Outreach Email"

    def test_list_prompts_search_matches_description_case_insensitively(self, client: TestClient):
        """search must also match against description, case-insensitively
        (search_prompts docstring, app/utils.py)."""
        client.post("/prompts", json={
            "title": "Generic Title",
            "content": "Body text",
            "description": "Great for Marketing Campaigns"
        })
        client.post("/prompts", json={"title": "Other", "content": "Body text"})

        response = client.get("/prompts", params={"search": "marketing"})
        data = response.json()
        assert data["total"] == 1
        assert data["prompts"][0]["title"] == "Generic Title"

    def test_list_prompts_search_does_not_match_content_field(self, client: TestClient):
        """search_prompts docstring explicitly states content is NOT searched:
        'The prompt's content field is not searched.' A query that only
        appears in content must yield no matches."""
        client.post("/prompts", json={
            "title": "Generic Title",
            "content": "This body mentions unicorn somewhere",
            "description": "A generic description"
        })

        response = client.get("/prompts", params={"search": "unicorn"})
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_search_no_match_returns_empty_list(self, client: TestClient):
        """A search term matching nothing must return an empty list and
        total 0, not an error."""
        client.post("/prompts", json={"title": "Alpha", "content": "Content alpha"})

        response = client.get("/prompts", params={"search": "zzz-no-such-text-zzz"})
        assert response.status_code == 200
        data = response.json()
        assert data["prompts"] == []
        assert data["total"] == 0

    def test_list_prompts_combined_collection_and_search_are_anded(self, client: TestClient):
        """Combining collection_id and search must intersect (AND), not
        union (OR): only prompts satisfying both filters should be
        returned. list_prompts applies filter_prompts_by_collection then
        search_prompts sequentially, which composes as an AND."""
        col_x = client.post("/collections", json={"name": "Collection X"}).json()
        col_y = client.post("/collections", json={"name": "Collection Y"}).json()

        client.post("/prompts", json={
            "title": "Alpha in X", "content": "c1", "collection_id": col_x["id"]
        })
        client.post("/prompts", json={
            "title": "Beta in X", "content": "c2", "collection_id": col_x["id"]
        })
        client.post("/prompts", json={
            "title": "Alpha in Y", "content": "c3", "collection_id": col_y["id"]
        })

        response = client.get(
            "/prompts", params={"collection_id": col_x["id"], "search": "Alpha"}
        )
        data = response.json()
        assert data["total"] == 1
        assert data["prompts"][0]["title"] == "Alpha in X"

    def test_list_prompts_sorted_newest_first_with_explicit_timestamps(self, client: TestClient):
        """Results must be ordered by created_at descending (newest first),
        per the list_prompts docstring: 'Results are sorted by creation
        date, newest first.' Uses explicit, well-separated created_at
        values written directly to storage rather than time.sleep, to make
        the ordering assertion deterministic rather than timing-dependent."""
        base = datetime(2026, 1, 1, 12, 0, 0)
        oldest = Prompt(title="Oldest", content="c", created_at=base, updated_at=base)
        middle = Prompt(
            title="Middle", content="c",
            created_at=base + timedelta(hours=1),
            updated_at=base + timedelta(hours=1),
        )
        newest = Prompt(
            title="Newest", content="c",
            created_at=base + timedelta(hours=2),
            updated_at=base + timedelta(hours=2),
        )
        # Insert out of chronological order to ensure the endpoint - not
        # insertion order - determines the returned order.
        backend_storage.create_prompt(middle)
        backend_storage.create_prompt(oldest)
        backend_storage.create_prompt(newest)

        response = client.get("/prompts")
        titles = [p["title"] for p in response.json()["prompts"]]
        assert titles == ["Newest", "Middle", "Oldest"]


class TestCollections:
    """Tests for collection endpoints."""
    
    def test_create_collection(self, client: TestClient, sample_collection_data):
        """POST /collections happy path must return 201 and the full
        Collection shape (app/models.py Collection; response_model=
        Collection on the route), echoing back every submitted field plus
        a server-generated id and created_at - not just a subset. Source:
        create_collection docstring ("Returns: The newly created
        collection, with a generated id and creation timestamp"),
        docs/API_REFERENCE.md's POST /collections sample response (id,
        name, description, created_at). Unlike Prompt, Collection has no
        updated_at field (per Collection's docstring/fields in
        app/models.py), so it must not appear in the response."""
        response = client.post("/collections", json=sample_collection_data)
        assert response.status_code == 201
        data = response.json()

        assert set(data.keys()) == {"id", "name", "description", "created_at"}
        assert data["name"] == sample_collection_data["name"]
        assert data["description"] == sample_collection_data["description"]
        assert isinstance(data["id"], str)
        assert len(data["id"]) > 0
        assert "created_at" in data

    def test_create_collection_persists_and_is_retrievable(
        self, client: TestClient, sample_collection_data
    ):
        """The created collection must actually be stored, not merely
        echoed back - storage.create_collection docstring ("Store a new
        collection") and the create_collection route calling
        storage.create_collection(collection) before returning it."""
        created = client.post("/collections", json=sample_collection_data).json()

        response = client.get(f"/collections/{created['id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_create_collection_without_description_defaults_to_none(
        self, client: TestClient
    ):
        """description is optional (CollectionBase.description docstring:
        "An optional description") - omitting it entirely must succeed
        and yield None, not a validation error or an empty string."""
        response = client.post("/collections", json={"name": "No description"})
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_collection_with_description_is_preserved(
        self, client: TestClient
    ):
        """When description is provided, it must be stored and returned
        verbatim, not dropped or truncated below its max_length=500."""
        response = client.post(
            "/collections",
            json={"name": "Has description", "description": "A helpful description"},
        )
        assert response.status_code == 201
        assert response.json()["description"] == "A helpful description"

    def test_create_collection_generates_unique_ids_across_multiple_creates(
        self, client: TestClient
    ):
        """Each call must generate a fresh unique id (models.generate_id
        docstring: "Generate a unique identifier string" via uuid4) -
        creating two otherwise-identical collections must not collide or
        reuse an id."""
        first = client.post("/collections", json={"name": "Same name"}).json()
        second = client.post("/collections", json={"name": "Same name"}).json()

        assert first["id"] != second["id"]

    def test_create_collection_missing_name_returns_422(self, client: TestClient):
        """name is a required field (CollectionBase.name: Field(...,
        min_length=1, max_length=100) - the `...` marks it required in
        Pydantic). Omitting it must fail FastAPI's request validation with
        422, per api-contract.md's error shape section ("422 (request body
        fails Pydantic validation")."""
        response = client.post("/collections", json={"description": "No name"})
        assert response.status_code == 422

    def test_create_collection_empty_name_returns_422(self, client: TestClient):
        """name has min_length=1 (CollectionBase.name Field constraint) -
        an empty string must be rejected with 422, not silently accepted
        as a name-less collection."""
        response = client.post("/collections", json={"name": ""})
        assert response.status_code == 422

    def test_create_collection_name_exceeding_max_length_returns_422(
        self, client: TestClient
    ):
        """name has max_length=100 (CollectionBase.name Field constraint)
        - a 101-character name must be rejected with 422."""
        response = client.post("/collections", json={"name": "x" * 101})
        assert response.status_code == 422

    def test_create_collection_name_at_max_length_boundary_succeeds(
        self, client: TestClient
    ):
        """A name of exactly 100 characters is within the documented
        boundary (max_length=100 is inclusive in Pydantic) and must be
        accepted."""
        name = "x" * 100
        response = client.post("/collections", json={"name": name})
        assert response.status_code == 201
        assert response.json()["name"] == name

    def test_create_collection_description_exceeding_max_length_returns_422(
        self, client: TestClient
    ):
        """description has max_length=500 (CollectionBase.description
        Field constraint) - a 501-character description must be rejected
        with 422."""
        response = client.post(
            "/collections", json={"name": "Some name", "description": "x" * 501}
        )
        assert response.status_code == 422

    def test_create_collection_description_at_max_length_boundary_succeeds(
        self, client: TestClient
    ):
        """A description of exactly 500 characters is within the
        documented boundary (max_length=500 is inclusive in Pydantic) and
        must be accepted."""
        description = "x" * 500
        response = client.post(
            "/collections", json={"name": "Some name", "description": description}
        )
        assert response.status_code == 201
        assert response.json()["description"] == description

    def test_create_collection_null_description_is_accepted(
        self, client: TestClient
    ):
        """An explicit null description must be treated the same as an
        omitted one (Optional[str] = Field(None, ...)) - must succeed and
        yield None, not a 422."""
        response = client.post(
            "/collections", json={"name": "Explicit null", "description": None}
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_collection_wrong_type_for_name_returns_422(
        self, client: TestClient
    ):
        """name is typed as str (CollectionBase.name: str) - submitting a
        non-string (e.g. an integer) must fail FastAPI/Pydantic's request
        validation with 422."""
        response = client.post("/collections", json={"name": 12345})
        assert response.status_code == 422

    def test_create_collection_missing_body_returns_422(self, client: TestClient):
        """POST /collections requires a JSON body containing at least
        name; sending no body at all must fail validation with 422 rather
        than crashing or defaulting to an empty collection."""
        response = client.post("/collections")
        assert response.status_code == 422

    def test_list_collections(self, client: TestClient, sample_collection_data):
        """A single created collection must be returned with a matching
        total count and its full field set, per the CollectionList/
        list_collections docstrings (app/models.py, app/api.py) and the
        documented GET /collections response shape
        (docs/API_REFERENCE.md)."""
        created = client.post("/collections", json=sample_collection_data).json()

        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 1
        assert data["total"] == 1
        returned = data["collections"][0]
        assert returned["id"] == created["id"]
        assert returned["name"] == sample_collection_data["name"]
        assert returned["description"] == sample_collection_data["description"]
        assert "created_at" in returned

    # ---- Additional list_collections coverage: empty case, multiple
    # ---- collections, and the total/collections-length invariant.
    # ---- Intended behavior source: list_collections docstring and
    # ---- CollectionList docstring (app/api.py, app/models.py),
    # ---- docs/API_REFERENCE.md's "GET /collections" section, and
    # ---- Storage.get_all_collections's docstring (app/storage.py),
    # ---- which explicitly states collections are returned "in no
    # ---- particular order" - no written spec guarantees an order for
    # ---- this endpoint (unlike list_prompts, which is documented to
    # ---- sort newest-first), so these tests deliberately assert on
    # ---- set membership/count rather than a specific order.

    def test_list_collections_empty_returns_empty_list_and_zero_total(
        self, client: TestClient
    ):
        """With no collections created, GET /collections must return an
        empty list and total=0, not an error - mirrors the documented
        empty-list behavior of PromptList/list_prompts and the
        CollectionList docstring's own empty example
        (`CollectionList(collections=[], total=0)`)."""
        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert data["collections"] == []
        assert data["total"] == 0

    def test_list_collections_returns_all_created_collections(
        self, client: TestClient
    ):
        """With no filtering parameters supported by this endpoint, every
        stored collection must be returned - list_collections is
        documented as unconditionally "All stored collections and the
        total count." Order is not asserted since no spec guarantees one
        (see note above); membership is checked via a set of names."""
        client.post("/collections", json={"name": "Alpha"})
        client.post("/collections", json={"name": "Beta"})
        client.post("/collections", json={"name": "Gamma"})

        response = client.get("/collections")
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 3
        assert {c["name"] for c in data["collections"]} == {"Alpha", "Beta", "Gamma"}

    def test_list_collections_total_always_matches_returned_collections_length(
        self, client: TestClient
    ):
        """total must equal len(collections) per the CollectionList
        docstring and list_collections's implementation contract
        (`CollectionList(collections=collections, total=len(collections))`),
        regardless of how many collections exist."""
        client.post("/collections", json={"name": "One"})
        client.post("/collections", json={"name": "Two"})
        client.post("/collections", json={"name": "Three"})
        client.post("/collections", json={"name": "Four"})

        response = client.get("/collections")
        data = response.json()
        assert data["total"] == len(data["collections"])
        assert data["total"] == 4

    def test_list_collections_each_item_has_full_collection_field_set(
        self, client: TestClient
    ):
        """Each item in the collections list must expose the full
        Collection schema - id, name, description, and created_at - per
        the Collection model's documented Attributes (app/models.py),
        not just a subset of fields."""
        client.post(
            "/collections",
            json={"name": "Docs", "description": "Documentation prompts"},
        )
        client.post("/collections", json={"name": "No Description"})

        response = client.get("/collections")
        data = response.json()
        by_name = {c["name"]: c for c in data["collections"]}

        docs = by_name["Docs"]
        assert set(["id", "name", "description", "created_at"]).issubset(docs.keys())
        assert docs["description"] == "Documentation prompts"

        no_desc = by_name["No Description"]
        assert no_desc["description"] is None

    def test_list_collections_reflects_deletions(self, client: TestClient):
        """After a collection is deleted, GET /collections must no longer
        include it and total must decrease accordingly - list_collections
        always reflects current storage state (storage.get_all_collections
        docstring: "Every collection currently in storage")."""
        keep = client.post("/collections", json={"name": "Keep"}).json()
        remove = client.post("/collections", json={"name": "Remove"}).json()

        delete_response = client.delete(f"/collections/{remove['id']}")
        assert delete_response.status_code == 204

        response = client.get("/collections")
        data = response.json()
        assert data["total"] == 1
        assert [c["id"] for c in data["collections"]] == [keep["id"]]

    def test_get_collection_not_found(self, client: TestClient):
        """GET /collections/{id} for a nonexistent id must 404 with the
        documented detail body, per get_collection's docstring ("Raises:
        HTTPException: With status 404 if no collection with collection_id
        exists.") and the documented 404 sample response in
        docs/API_REFERENCE.md ('GET /collections/{collection_id}'):
        `{"detail": "Collection not found"}`. This also exercises the
        constitution's "404 (not 500) for missing resources" rule
        (.specify/memory/constitution.md)."""
        response = client.get("/collections/nonexistent-id")
        assert response.status_code == 404
        assert response.json() == {"detail": "Collection not found"}

    def test_get_collection_success_returns_full_field_set(
        self, client: TestClient, sample_collection_data
    ):
        """A successful GET /collections/{id} must return 200 with the
        full Collection schema (id, name, description, created_at) and
        the values must match what was created, per the Collection
        model's documented Attributes (app/models.py), get_collection's
        docstring ("Returns: Collection: The matching collection."), and
        the documented 200 sample response in docs/API_REFERENCE.md
        ('GET /collections/{collection_id}')."""
        created = client.post("/collections", json=sample_collection_data).json()

        response = client.get(f"/collections/{created['id']}")

        assert response.status_code == 200
        data = response.json()
        assert set(["id", "name", "description", "created_at"]).issubset(
            data.keys()
        )
        assert data["id"] == created["id"]
        assert data["name"] == sample_collection_data["name"]
        assert data["description"] == sample_collection_data["description"]
        assert data["created_at"] == created["created_at"]

    def test_get_collection_with_description_set(self, client: TestClient):
        """When a collection is created with a description, GET
        /collections/{id} must return that same description value - per
        the Collection/CollectionBase docstring's documented
        `description` attribute (app/models.py) and the documented 200
        response shape in docs/API_REFERENCE.md, which always includes a
        (possibly null) `description` field."""
        created = client.post(
            "/collections",
            json={"name": "With Description", "description": "Has a description"},
        ).json()

        response = client.get(f"/collections/{created['id']}")

        assert response.status_code == 200
        assert response.json()["description"] == "Has a description"

    def test_get_collection_with_description_omitted_returns_none(
        self, client: TestClient
    ):
        """When a collection is created without a description, `description`
        is documented as `Optional[str]` (CollectionBase, app/models.py),
        so GET /collections/{id} must return `description: null` rather
        than omitting the field or erroring."""
        created = client.post("/collections", json={"name": "No Description"}).json()

        response = client.get(f"/collections/{created['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "description" in data
        assert data["description"] is None

    def test_get_collection_after_deletion_returns_404(
        self, client: TestClient, sample_collection_data
    ):
        """After a collection has been deleted, GET /collections/{id} must
        404 (matching storage.get_collection's documented Optional[Collection]
        return - None once removed from storage - and get_collection's
        documented 404-on-missing behavior), not continue to succeed and
        not 500, per the constitution's "404 (not 500) for missing
        resources" rule (.specify/memory/constitution.md)."""
        created = client.post("/collections", json=sample_collection_data).json()
        collection_id = created["id"]

        delete_response = client.delete(f"/collections/{collection_id}")
        assert delete_response.status_code == 204

        response = client.get(f"/collections/{collection_id}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Collection not found"}

    def test_delete_collection_with_prompts(self, client: TestClient, sample_collection_data, sample_prompt_data):
        """Deleting a collection must unlink (not delete) its prompts.

        Intended behavior source: delete_collection's docstring ("Any
        prompts assigned to this collection are unassigned (their
        collection_id is set to None) rather than deleted, before the
        collection itself is removed"), docs/API_REFERENCE.md's
        `DELETE /collections/{collection_id}` section ("Any prompts
        assigned to it are **unassigned** ... rather than deleted"),
        specs/001-complete-promptlab-app/contracts/api-contract.md's
        DELETE /collections row ("backend already unassigns affected
        prompts before deleting, satisfying FR-008"), and
        .specify/memory/constitution.md Principle III ("Deleting a parent
        resource ... MUST NOT silently orphan its children").

        This assertion is unconditional (not `if prompts: ...`): the
        prompt MUST still exist afterward with collection_id None. A
        prompt that vanished entirely, or one that kept a dangling
        reference to the deleted collection, is a bug, not an
        acceptable alternative.

        Args:
            client: FastAPI test client backed by isolated in-memory storage.
            sample_collection_data: Fixture supplying a valid collection creation payload.
            sample_prompt_data: Fixture supplying a valid prompt creation payload.

        Returns:
            None

        Raises:
            AssertionError: If the prompt list length is not 1 after collection
                deletion, if the surviving prompt's id does not match, or if
                collection_id is not None on the surviving prompt.
        """
        # Create collection
        col_response = client.post("/collections", json=sample_collection_data)
        collection_id = col_response.json()["id"]

        # Create prompt in collection
        prompt_data = {**sample_prompt_data, "collection_id": collection_id}
        prompt_response = client.post("/prompts", json=prompt_data)
        prompt_id = prompt_response.json()["id"]

        # Delete collection
        delete_response = client.delete(f"/collections/{collection_id}")
        assert delete_response.status_code == 204

        # The prompt must still exist, unlinked (not deleted, not left
        # pointing at the now-gone collection).
        prompts = client.get("/prompts").json()["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["id"] == prompt_id
        assert prompts[0]["collection_id"] is None

    def test_delete_collection_not_found_returns_404(self, client: TestClient):
        """DELETE /collections/{id} for a nonexistent id must 404 with the
        documented detail body, per delete_collection's docstring ("Raises:
        HTTPException: With status 404 if no collection with collection_id
        exists.") and constitution.md Principle III ("404 (not 500) for
        missing resources")."""
        response = client.delete("/collections/nonexistent-id")
        assert response.status_code == 404
        assert response.json() == {"detail": "Collection not found"}

    def test_delete_collection_without_prompts_succeeds(
        self, client: TestClient, sample_collection_data
    ):
        """Deleting a collection with no prompts assigned must succeed
        with 204 and remove the collection - the common/simple case that
        never enters the unlink loop (storage.get_prompts_by_collection
        returns [] per its docstring: "Retrieve all prompts belonging to
        a given collection" -> empty when none match)."""
        created = client.post("/collections", json=sample_collection_data).json()
        collection_id = created["id"]

        response = client.delete(f"/collections/{collection_id}")
        assert response.status_code == 204
        assert response.content == b""

        get_response = client.get(f"/collections/{collection_id}")
        assert get_response.status_code == 404

    def test_delete_collection_removes_the_collection_itself(
        self, client: TestClient, sample_collection_data
    ):
        """After deletion, the collection itself must be gone from
        storage - a subsequent GET must 404, per storage.delete_collection's
        docstring ("Delete a collection by its id") and get_collection's
        documented 404-on-missing behavior. Also covered via
        docs/API_REFERENCE.md's DELETE /collections/{collection_id}
        section."""
        created = client.post("/collections", json=sample_collection_data).json()
        collection_id = created["id"]

        client.delete(f"/collections/{collection_id}")

        response = client.get(f"/collections/{collection_id}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Collection not found"}

    def test_delete_collection_unlinks_all_assigned_prompts_not_just_one(
        self, client: TestClient, sample_collection_data
    ):
        """When multiple prompts are assigned to the deleted collection,
        every one of them must be unlinked, not just the first -
        delete_collection's docstring says "Any prompts assigned to this
        collection are unassigned" (plural, unconditional), and it
        iterates `storage.get_prompts_by_collection(collection_id)` with
        no early exit."""
        collection_id = client.post(
            "/collections", json=sample_collection_data
        ).json()["id"]

        prompt_ids = []
        for i in range(3):
            resp = client.post(
                "/prompts",
                json={
                    "title": f"Prompt {i}",
                    "content": f"Content {i}",
                    "collection_id": collection_id,
                },
            )
            prompt_ids.append(resp.json()["id"])

        delete_response = client.delete(f"/collections/{collection_id}")
        assert delete_response.status_code == 204

        prompts = client.get("/prompts").json()["prompts"]
        assert len(prompts) == 3
        assert {p["id"] for p in prompts} == set(prompt_ids)
        for prompt in prompts:
            assert prompt["collection_id"] is None

    def test_delete_collection_does_not_affect_prompts_in_other_collections(
        self, client: TestClient
    ):
        """Deleting one collection must leave prompts assigned to a
        *different* collection untouched - delete_collection only calls
        `storage.get_prompts_by_collection(collection_id)` for the
        collection being deleted (app/api.py), so prompts belonging to
        other collections must keep both their collection_id and their
        original updated_at."""
        target_collection = client.post(
            "/collections", json={"name": "Target"}
        ).json()
        other_collection = client.post(
            "/collections", json={"name": "Other"}
        ).json()

        target_prompt = client.post(
            "/prompts",
            json={
                "title": "In target",
                "content": "content",
                "collection_id": target_collection["id"],
            },
        ).json()
        other_prompt = client.post(
            "/prompts",
            json={
                "title": "In other",
                "content": "content",
                "collection_id": other_collection["id"],
            },
        ).json()

        client.delete(f"/collections/{target_collection['id']}")

        prompts = {p["id"]: p for p in client.get("/prompts").json()["prompts"]}
        assert prompts[target_prompt["id"]]["collection_id"] is None
        assert prompts[other_prompt["id"]]["collection_id"] == other_collection["id"]
        assert prompts[other_prompt["id"]]["updated_at"] == other_prompt["updated_at"]

    def test_delete_collection_unlink_refreshes_updated_at_and_preserves_other_fields(
        self, client: TestClient, sample_collection_data
    ):
        """The unlink code path (app/api.py delete_collection) explicitly
        rebuilds each affected Prompt with `updated_at=get_current_time()`
        while copying id, title, content, description, and created_at
        verbatim from the original. Per constitution.md Principle III
        ("Mutating a resource MUST refresh its updated_at timestamp"),
        unlinking counts as a mutation of the prompt and must bump
        updated_at; everything else must be preserved unchanged."""
        collection_id = client.post(
            "/collections", json=sample_collection_data
        ).json()["id"]

        created = client.post(
            "/prompts",
            json={
                "title": "Original Title",
                "content": "Original content",
                "description": "Original description",
                "collection_id": collection_id,
            },
        ).json()

        import time
        time.sleep(0.1)  # Small delay to ensure timestamp would change

        client.delete(f"/collections/{collection_id}")

        prompts = client.get("/prompts").json()["prompts"]
        assert len(prompts) == 1
        unlinked = prompts[0]

        assert unlinked["id"] == created["id"]
        assert unlinked["title"] == created["title"]
        assert unlinked["content"] == created["content"]
        assert unlinked["description"] == created["description"]
        assert unlinked["created_at"] == created["created_at"]
        assert unlinked["collection_id"] is None
        assert unlinked["updated_at"] != created["updated_at"]
