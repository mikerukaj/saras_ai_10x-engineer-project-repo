"""Unit tests for app.storage.Storage.

These tests exercise the Storage class directly (no HTTP layer / no
TestClient) to verify the in-memory CRUD behavior documented on
Storage's own docstrings in app/storage.py.

No written spec (specs/001-complete-promptlab-app/contracts/api-contract.md,
data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers the
Storage class directly - it is an internal implementation detail, not a
public API contract. Intended behavior for each method is therefore
inferred from that method's own docstring (Google-style, per
.claude/skills/docstring-func/) plus the surrounding Storage class
docstring ("Holds prompts and collections in dictionaries keyed by
their id ... Data exists only for the lifetime of the process").

This file follows the docstring/citation style established in
tests/test_api.py. `create_prompt`, `get_prompt`, `get_all_prompts`,
`update_prompt`, `delete_prompt`, the Collection equivalents
(`create_collection`, `get_collection`, `get_all_collections`,
`delete_collection`), `get_prompts_by_collection`, and `clear` all now
have dedicated coverage (TestPromptCRUD, TestGetPrompt,
TestGetAllPrompts, TestUpdatePrompt, TestDeletePrompt,
TestCreateCollection, TestGetCollection, TestGetAllCollections,
TestDeleteCollection, TestGetPromptsByCollection, and TestClear
respectively). Every method on Storage now has a dedicated test class.
"""


from app.models import Collection, Prompt
from app.storage import Storage
from app.storage import storage as storage_singleton


class TestPromptCRUD:
    """Tests for Storage.create_prompt.

    Source of intended behavior: Storage.create_prompt's own docstring
    in app/storage.py ("Store a new prompt. ... Returns: Prompt: The
    stored prompt.") plus the Storage class docstring's description of
    _prompts as "Prompts keyed by their id" and data as scoped to "the
    lifetime of the process" (i.e. persists for the life of a Storage
    instance, with no cross-instance sharing).
    """

    def test_create_prompt_returns_the_same_prompt_passed_in(self):
        """docstring: "Returns: Prompt: The stored prompt." - the
        returned object must be the prompt that was stored, not a copy,
        a subset, or a different prompt."""
        storage = Storage()
        prompt = Prompt(title="Greeting", content="Hi")

        result = storage.create_prompt(prompt)

        assert result is prompt

    def test_create_prompt_preserves_all_submitted_field_values(self):
        """The stored/returned prompt's field values must match exactly
        what was submitted - create_prompt must not alter title,
        content, description, or collection_id."""
        storage = Storage()
        prompt = Prompt(
            title="Code Review",
            content="Review this: {{code}}",
            description="A review prompt",
            collection_id="collection-123",
        )

        result = storage.create_prompt(prompt)

        assert result.title == "Code Review"
        assert result.content == "Review this: {{code}}"
        assert result.description == "A review prompt"
        assert result.collection_id == "collection-123"

    def test_create_prompt_is_retrievable_via_get_prompt(self):
        """A prompt stored via create_prompt must be findable afterward
        via get_prompt(prompt.id) - per the Storage class docstring
        describing _prompts as "keyed by their id" and get_prompt's own
        docstring ("Retrieve a single prompt by its id")."""
        storage = Storage()
        prompt = Prompt(title="Greeting", content="Hi")

        storage.create_prompt(prompt)

        fetched = storage.get_prompt(prompt.id)
        assert fetched is not None
        assert fetched.id == prompt.id
        assert fetched.title == "Greeting"
        assert fetched.content == "Hi"

    def test_create_prompt_appears_in_get_all_prompts(self):
        """A prompt stored via create_prompt must appear in
        get_all_prompts()'s result - per get_all_prompts' docstring
        ("Every prompt currently in storage")."""
        storage = Storage()
        prompt = Prompt(title="Greeting", content="Hi")

        storage.create_prompt(prompt)

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].id == prompt.id

    def test_create_prompt_with_only_required_fields_round_trips(self):
        """title and content are the only required fields (PromptBase:
        title/content use Field(...), description and collection_id
        default to None). Creating a prompt with only those must
        succeed and round-trip through get_prompt with the optional
        fields defaulting to None."""
        storage = Storage()
        prompt = Prompt(title="Minimal", content="Just content")

        storage.create_prompt(prompt)
        fetched = storage.get_prompt(prompt.id)

        assert fetched.title == "Minimal"
        assert fetched.content == "Just content"
        assert fetched.description is None
        assert fetched.collection_id is None

    def test_create_prompt_with_all_fields_populated_round_trips(self):
        """When description and collection_id are both provided, they
        must be stored and retrievable verbatim alongside title and
        content."""
        storage = Storage()
        prompt = Prompt(
            title="Full",
            content="Full content",
            description="Full description",
            collection_id="coll-1",
        )

        storage.create_prompt(prompt)
        fetched = storage.get_prompt(prompt.id)

        assert fetched.title == "Full"
        assert fetched.content == "Full content"
        assert fetched.description == "Full description"
        assert fetched.collection_id == "coll-1"


class TestGetPrompt:
    """Dedicated tests for Storage.get_prompt.

    Source of intended behavior: Storage.get_prompt's own docstring in
    app/storage.py ("Retrieve a single prompt by its id. ... Returns:
    Optional[Prompt]: The matching prompt, or None if no prompt with
    prompt_id exists.") plus the Storage class docstring describing
    _prompts as "Prompts keyed by their id" and data as scoped to "the
    lifetime of the process". No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers
    the Storage class directly - it is an internal implementation
    detail, not a public API contract - so intended behavior is
    inferred entirely from the docstrings above plus the natural
    read/write pairing with create_prompt and delete_prompt.
    """

    # ---- Hit case ----

    def test_get_prompt_hit_returns_full_field_fidelity(self):
        """docstring: "Optional[Prompt]: The matching prompt". A prompt
        retrieved right after creation must match on every field, not
        just id - title, content, description, collection_id,
        created_at, and updated_at must all be preserved verbatim."""
        storage = Storage()
        prompt = Prompt(
            title="Code Review",
            content="Review this: {{code}}",
            description="A review prompt",
            collection_id="collection-123",
        )

        storage.create_prompt(prompt)
        fetched = storage.get_prompt(prompt.id)

        assert fetched is not None
        assert fetched.id == prompt.id
        assert fetched.title == prompt.title
        assert fetched.content == prompt.content
        assert fetched.description == prompt.description
        assert fetched.collection_id == prompt.collection_id
        assert fetched.created_at == prompt.created_at
        assert fetched.updated_at == prompt.updated_at

    # ---- Miss case: id never existed ----

    def test_get_prompt_returns_none_on_empty_storage(self):
        """docstring: "or None if no prompt with prompt_id exists". On a
        freshly constructed Storage with zero prompts, any lookup must
        return None, not raise and not return a default/empty Prompt."""
        storage = Storage()

        result = storage.get_prompt("any-id")

        assert result is None

    def test_get_prompt_returns_none_when_id_does_not_match_any_stored_prompt(self):
        """docstring: "or None if no prompt with prompt_id exists". When
        storage is non-empty but the requested id matches none of the
        stored prompts, the result must still be None."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))
        storage.create_prompt(Prompt(title="B", content="Content B"))

        result = storage.get_prompt("id-that-was-never-created")

        assert result is None

    # ---- Miss case: id existed then was deleted ----

    def test_get_prompt_returns_none_after_the_prompt_was_deleted(self):
        """A prompt that existed and was then removed via delete_prompt
        must behave identically to an id that never existed - get_prompt
        must return None, not a stale reference to the deleted prompt
        and not an error. This exercises the natural read/write/delete
        lifecycle implied by the Storage class docstring and
        delete_prompt's own docstring ("Delete a prompt by its id")."""
        storage = Storage()
        prompt = Prompt(title="Temporary", content="Will be deleted")
        storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id) is not None

        deleted = storage.delete_prompt(prompt.id)
        assert deleted is True

        result = storage.get_prompt(prompt.id)
        assert result is None

    # ---- Returned object identity/independence ----

    def test_get_prompt_returns_the_same_object_reference_as_stored(self):
        """Empirical check (not documented, but observable): Storage's
        implementation is `return self._prompts.get(prompt_id)`, and
        Python dict.get returns the exact stored reference rather than a
        copy. Prompt's Config only sets from_attributes = True - it is
        not frozen - so Pydantic does not prevent mutation either. This
        test verifies directly (rather than assuming) that get_prompt
        returns the identical object that create_prompt stored, i.e. NOT
        a defensive copy."""
        storage = Storage()
        prompt = Prompt(title="Original", content="Original content")
        storage.create_prompt(prompt)

        fetched = storage.get_prompt(prompt.id)

        assert fetched is prompt

    def test_mutating_the_returned_prompt_corrupts_stored_state(self):
        """Direct consequence of the object-identity finding above: since
        get_prompt returns a live reference (not a copy), a caller that
        mutates the object obtained via get_prompt will corrupt the
        Storage instance's internal state for future reads. This is not
        promised or forbidden by get_prompt's docstring, but is
        important, non-obvious behavior worth pinning down explicitly -
        it means callers must treat get_prompt's result as read-only by
        convention only, since the storage layer offers no
        enforcement."""
        storage = Storage()
        prompt = Prompt(title="Original", content="Original content")
        storage.create_prompt(prompt)

        fetched = storage.get_prompt(prompt.id)
        fetched.title = "Mutated via returned reference"

        fetched_again = storage.get_prompt(prompt.id)
        assert fetched_again.title == "Mutated via returned reference"

    # ---- Persistence within a session (repeated reads, no side effects) ----

    def test_get_prompt_repeated_calls_return_consistent_results(self):
        """Reading via get_prompt must be side-effect free: calling it
        multiple times in a row for the same id on the same Storage
        instance must keep returning an equal (and, per the identity
        finding above, literally the same-object) result each time -
        the Storage class docstring frames these as "read" operations,
        implying no state change from reading."""
        storage = Storage()
        prompt = Prompt(title="Stable", content="Stable content")
        storage.create_prompt(prompt)

        first_read = storage.get_prompt(prompt.id)
        second_read = storage.get_prompt(prompt.id)
        third_read = storage.get_prompt(prompt.id)

        assert first_read == second_read == third_read
        assert first_read is second_read is third_read

    # ---- Edge cases ----

    def test_get_prompt_with_empty_string_id_returns_none(self):
        """An empty-string id is not a valid id any create_prompt call
        would produce (generate_id always yields a non-empty uuid4
        string), so looking it up must safely return None rather than
        raising - dict.get on a missing key never raises, and
        get_prompt's docstring promises None for "no prompt with
        prompt_id exists", which an empty string trivially satisfies on
        a store with no empty-string-keyed prompt."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))

        result = storage.get_prompt("")

        assert result is None

    def test_get_prompt_with_id_off_by_one_character_does_not_match(self):
        """get_prompt must perform exact-match lookup, not prefix/fuzzy
        matching - per the Storage class docstring describing _prompts
        as a dict "keyed by their id" (dict key lookup is always exact).
        An id that differs from a stored prompt's id by a single
        character must not be treated as a match."""
        storage = Storage()
        prompt = Prompt(id="abcdefgh-id", title="Exact", content="Exact content")
        storage.create_prompt(prompt)

        near_miss_id = "abcdefgh-idX"
        result = storage.get_prompt(near_miss_id)

        assert result is None

    def test_get_prompt_id_lookup_is_case_sensitive(self):
        """Ids are plain strings and dict keys in Python are compared
        case-sensitively, so a differently-cased id must not match a
        stored prompt - exact-match semantics per the "keyed by their
        id" description in the Storage class docstring."""
        storage = Storage()
        prompt = Prompt(id="MixedCase-ID", title="Case", content="Case content")
        storage.create_prompt(prompt)

        assert storage.get_prompt("MixedCase-ID") is not None
        assert storage.get_prompt("mixedcase-id") is None
        assert storage.get_prompt("MIXEDCASE-ID") is None

    def test_get_prompt_among_several_returns_exactly_the_requested_one(self):
        """With multiple prompts stored, requesting one by id must
        return exactly that prompt's data, never a different stored
        prompt's data - per get_prompt's docstring ("Retrieve a single
        prompt by its id") and _prompts being keyed by id (one-to-one
        mapping)."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        prompt_c = Prompt(title="C", content="Content C")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        storage.create_prompt(prompt_c)

        fetched_b = storage.get_prompt(prompt_b.id)

        assert fetched_b is not None
        assert fetched_b.id == prompt_b.id
        assert fetched_b.title == "B"
        assert fetched_b.content == "Content B"
        assert fetched_b.id != prompt_a.id
        assert fetched_b.id != prompt_c.id

    # ---- Cross-instance isolation ----

    def test_get_prompt_never_sees_a_prompt_created_on_a_different_instance(self):
        """Mirrors the pattern established for create_prompt in
        TestCrossInstanceIsolation: a prompt created on one Storage
        instance must be invisible to get_prompt on a different Storage
        instance, since each instance's _prompts dict is per-instance
        state (Storage class docstring's Attributes section, and
        __init__'s docstring/example showing a freshly constructed
        instance starts empty)."""
        storage_one = Storage()
        storage_two = Storage()
        prompt = Prompt(title="Only in one", content="Content")
        storage_one.create_prompt(prompt)

        assert storage_one.get_prompt(prompt.id) is not None
        assert storage_two.get_prompt(prompt.id) is None


class TestGetAllPrompts:
    """Dedicated tests for Storage.get_all_prompts.

    Source of intended behavior: Storage.get_all_prompts' own docstring in
    app/storage.py ("Retrieve all stored prompts. ... Returns: List[Prompt]:
    Every prompt currently in storage, in no particular order.") plus the
    Storage class docstring describing _prompts as "Prompts keyed by their
    id" and data as scoped to "the lifetime of the process". No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers the
    Storage class directly - it is an internal implementation detail, not a
    public API contract - so intended behavior is inferred entirely from
    the docstring above.

    `test_create_prompt_appears_in_get_all_prompts` (TestPromptCRUD) and
    `test_get_all_prompts_accumulates_all_created_prompts`
    (TestPersistenceWithinSession) already cover the single/multiple
    "prompts I created show up" happy path incidentally; this class avoids
    duplicating those and instead focuses on the empty case, return-type
    guarantees, order, snapshot/aliasing semantics, repeated-call
    consistency, staleness after mutation, and cross-instance isolation.
    """

    # ---- Empty case ----

    def test_get_all_prompts_on_fresh_storage_returns_empty_list(self):
        """docstring Example: "storage = Storage(); storage.get_all_prompts()
        -> []". A freshly constructed Storage with zero prompts created must
        return an empty list, not None and not raise."""
        storage = Storage()

        result = storage.get_all_prompts()

        assert result == []
        assert result is not None

    # ---- Return type ----

    def test_get_all_prompts_returns_a_genuine_list_instance(self):
        """Per the `List[Prompt]` return type hint and the implementation
        `return list(self._prompts.values())`, the result must be an actual
        `list` object - not a `dict_values` view or other iterable that
        merely behaves list-like."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))

        result = storage.get_all_prompts()

        assert isinstance(result, list)
        assert type(result) is list

    def test_get_all_prompts_returned_list_supports_len_indexing_and_repeated_iteration(self):
        """Being a real `list` (not a view) means len(), integer indexing,
        and iterating more than once must all work without exhaustion -
        confirms the return type guarantee matters in practice, not just
        nominally."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)

        result = storage.get_all_prompts()

        assert len(result) == 2
        assert result[0] is not None
        assert result[1] is not None
        first_pass_ids = {p.id for p in result}
        second_pass_ids = {p.id for p in result}
        assert first_pass_ids == second_pass_ids == {prompt_a.id, prompt_b.id}

    # ---- Order: documented as unspecified; observe current behavior without asserting it as contract ----

    def test_get_all_prompts_current_implementation_preserves_insertion_order(self):
        """NOTE: get_all_prompts' docstring explicitly says "in no
        particular order" - callers must NOT rely on ordering. This test
        does not assert order as a guaranteed contract; it documents what
        the CURRENT implementation happens to do (Python dicts preserve
        insertion order since 3.7, and dict.values() reflects that order,
        so list(self._prompts.values()) currently comes back in creation
        order). If this test starts failing after an implementation change
        (e.g. switching the backing store), that is NOT a regression against
        the docstring's contract - the docstring never promised order - so
        this test should simply be removed/updated rather than treated as a
        bug report.
        """
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        prompt_c = Prompt(title="C", content="Content C")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        storage.create_prompt(prompt_c)

        result = storage.get_all_prompts()

        assert [p.id for p in result] == [prompt_a.id, prompt_b.id, prompt_c.id]

    # ---- Snapshot semantics: list container vs. the Prompt objects inside it ----

    def test_get_all_prompts_returns_a_new_list_object_on_each_call(self):
        """Unlike get_prompt (which returns the same stored object
        reference), get_all_prompts' implementation wraps the dict values in
        `list(...)`, constructing a brand-new list object on every call.
        Two consecutive calls must therefore NOT be the same list instance,
        even though their contents are equal."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))

        first_call = storage.get_all_prompts()
        second_call = storage.get_all_prompts()

        assert first_call is not second_call
        assert first_call == second_call

    def test_mutating_the_returned_list_container_does_not_corrupt_storage(self):
        """Because get_all_prompts returns a fresh list each call (verified
        above), appending to or removing from that returned list must be
        safe - it must NOT alter Storage's internal _prompts dict. This
        directly answers the snapshot-safety question raised by the
        get_prompt object-identity finding: the LIST wrapper itself is an
        independent snapshot, even though (per the next test) the Prompt
        objects inside it are not."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        storage.create_prompt(prompt_a)

        returned_list = storage.get_all_prompts()
        returned_list.append(Prompt(title="Injected", content="Should not stick"))
        assert len(storage.get_all_prompts()) == 1

        returned_list_2 = storage.get_all_prompts()
        returned_list_2.pop()
        assert len(storage.get_all_prompts()) == 1
        assert storage.get_prompt(prompt_a.id) is not None

    def test_prompt_objects_inside_the_returned_list_are_the_same_references_as_get_prompt(self):
        """The list CONTAINER returned by get_all_prompts is new each call,
        but the individual Prompt OBJECTS inside it are the very same
        references stored in _prompts (list() only copies the container,
        not its elements) - identical to what get_prompt returns for that
        id. This means the in-place-mutation corruption risk documented for
        get_prompt in TestGetPrompt.test_mutating_the_returned_prompt_corrupts_stored_state
        equally applies to elements obtained via get_all_prompts."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        storage.create_prompt(prompt_a)

        [fetched_via_list] = storage.get_all_prompts()
        fetched_via_get = storage.get_prompt(prompt_a.id)

        assert fetched_via_list is prompt_a
        assert fetched_via_list is fetched_via_get

    def test_mutating_a_prompt_object_inside_the_returned_list_corrupts_stored_state(self):
        """Direct consequence of the object-identity finding above: mutating
        a Prompt element reached via get_all_prompts()[i] mutates Storage's
        internal state for future reads, even though the list container
        itself was a safe copy. This mirrors, at the element level, the
        get_prompt mutation finding in TestGetPrompt."""
        storage = Storage()
        prompt_a = Prompt(title="Original", content="Original content")
        storage.create_prompt(prompt_a)

        [fetched] = storage.get_all_prompts()
        fetched.title = "Mutated via get_all_prompts element"

        [fetched_again] = storage.get_all_prompts()
        assert fetched_again.title == "Mutated via get_all_prompts element"
        assert storage.get_prompt(prompt_a.id).title == "Mutated via get_all_prompts element"

    # ---- Repeated calls without intervening writes ----

    def test_get_all_prompts_repeated_calls_return_equal_contents_with_distinct_list_instances(self):
        """Calling get_all_prompts() twice in a row with no writes in
        between must return equal contents (same prompts, per docstring
        "Every prompt currently in storage") while the list instances
        themselves may differ (per the snapshot semantics established
        above) - this is a read operation and must be side-effect free and
        repeatable."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))
        storage.create_prompt(Prompt(title="B", content="Content B"))

        first_read = storage.get_all_prompts()
        second_read = storage.get_all_prompts()

        assert first_read == second_read
        assert [p.id for p in first_read] == [p.id for p in second_read]
        assert first_read is not second_read

    # ---- Consistency after mutation via delete_prompt / update_prompt ----

    def test_get_all_prompts_no_longer_includes_a_deleted_prompt(self):
        """get_all_prompts must reflect current state, not a cached
        snapshot: after delete_prompt removes a prompt, subsequent calls to
        get_all_prompts must no longer include it - per the docstring
        "Every prompt currently in storage" (deleted prompts are no longer
        "currently in storage")."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        assert len(storage.get_all_prompts()) == 2

        deleted = storage.delete_prompt(prompt_a.id)
        assert deleted is True

        remaining = storage.get_all_prompts()
        assert len(remaining) == 1
        assert remaining[0].id == prompt_b.id

    def test_get_all_prompts_reflects_new_data_after_update_prompt_not_stale_data(self):
        """get_all_prompts must not cache or return stale data: after
        update_prompt replaces a prompt's data, subsequent calls to
        get_all_prompts must show the new values, not the pre-update ones -
        per update_prompt's docstring ("Replace an existing prompt with new
        data. ... Returns: ... The stored prompt.") combined with
        get_all_prompts' "currently in storage" language."""
        storage = Storage()
        prompt_a = Prompt(title="Before", content="Before content")
        storage.create_prompt(prompt_a)

        updated = Prompt(
            id=prompt_a.id,
            title="After",
            content="After content",
        )
        result = storage.update_prompt(prompt_a.id, updated)
        assert result is not None

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].title == "After"
        assert all_prompts[0].content == "After content"

    # ---- Cross-instance isolation ----

    def test_get_all_prompts_never_includes_prompts_created_on_a_different_instance(self):
        """Mirrors the pattern established for create_prompt/get_prompt in
        TestCrossInstanceIsolation/TestGetPrompt: prompts created on one
        Storage instance must be invisible to get_all_prompts on a
        different Storage instance, since each instance's _prompts dict is
        per-instance state (Storage class docstring's Attributes section)."""
        storage_one = Storage()
        storage_two = Storage()
        storage_one.create_prompt(Prompt(title="Only in one", content="Content"))
        storage_one.create_prompt(Prompt(title="Also only in one", content="Content 2"))

        assert len(storage_one.get_all_prompts()) == 2
        assert storage_two.get_all_prompts() == []


class TestUpdatePrompt:
    """Dedicated tests for Storage.update_prompt.

    Source of intended behavior: Storage.update_prompt's own docstring in
    app/storage.py ("Replace an existing prompt with new data. ... Returns:
    Optional[Prompt]: The stored prompt, or None if no prompt with
    prompt_id exists.") plus the Storage class docstring describing
    _prompts as "Prompts keyed by their id" and data as scoped to "the
    lifetime of the process". No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers the
    Storage class directly - it is an internal implementation detail, not a
    public API contract - so intended behavior is inferred entirely from
    update_prompt's own docstring, cross-checked against the sibling
    create_prompt/get_prompt/delete_prompt docstrings for consistent
    vocabulary ("Replace an existing prompt" implies an update only ever
    acts on a prompt that already exists, never creating one).

    `test_get_all_prompts_reflects_new_data_after_update_prompt_not_stale_data`
    (TestGetAllPrompts) already exercises update_prompt incidentally, to
    confirm get_all_prompts isn't stale after an update - that test is not
    duplicated here; this class is the dedicated, primary suite for
    update_prompt's own contract.
    """

    # ---- Hit case: replaces stored data, visible on subsequent get_prompt ----

    def test_update_prompt_hit_replaces_stored_data_full_field_fidelity(self):
        """docstring: "Replace an existing prompt with new data." A
        subsequent get_prompt(prompt_id) must return the NEW field values,
        not the old ones, verified across every field (title, content,
        description, collection_id), not just one."""
        storage = Storage()
        original = Prompt(
            title="Before",
            content="Before content",
            description="Before description",
            collection_id="collection-before",
        )
        storage.create_prompt(original)

        replacement = Prompt(
            id=original.id,
            title="After",
            content="After content",
            description="After description",
            collection_id="collection-after",
        )
        storage.update_prompt(original.id, replacement)

        fetched = storage.get_prompt(original.id)
        assert fetched is not None
        assert fetched.title == "After"
        assert fetched.content == "After content"
        assert fetched.description == "After description"
        assert fetched.collection_id == "collection-after"
        assert fetched.title != "Before"
        assert fetched.content != "Before content"

    def test_update_prompt_hit_with_only_required_fields_clears_optional_fields(self):
        """Replacing a prompt that had description/collection_id set with
        a replacement that omits them must result in those fields reading
        back as None - update_prompt REPLACES the prompt
        (self._prompts[prompt_id] = prompt), it does not merge/patch field
        by field, per the docstring's "Replace an existing prompt with new
        data" wording (contrasted with PromptPatch's partial-update
        semantics, which is a separate model/route concern, not this
        method's)."""
        storage = Storage()
        original = Prompt(
            title="Before",
            content="Before content",
            description="Will be dropped",
            collection_id="will-be-dropped",
        )
        storage.create_prompt(original)

        replacement = Prompt(id=original.id, title="After", content="After content")
        storage.update_prompt(original.id, replacement)

        fetched = storage.get_prompt(original.id)
        assert fetched.description is None
        assert fetched.collection_id is None

    # ---- Return value on hit ----

    def test_update_prompt_hit_returns_the_same_object_passed_in(self):
        """docstring: "Returns: Optional[Prompt]: The stored prompt." -
        mirroring the rigor applied to create_prompt's
        test_create_prompt_returns_the_same_prompt_passed_in, this checks
        object identity (`is`), not just equal data: the returned object
        must be the exact `prompt` argument that was passed in."""
        storage = Storage()
        original = Prompt(title="Before", content="Before content")
        storage.create_prompt(original)

        replacement = Prompt(id=original.id, title="After", content="After content")
        result = storage.update_prompt(original.id, replacement)

        assert result is replacement

    def test_update_prompt_hit_return_value_matches_subsequent_get_prompt(self):
        """The object returned by update_prompt must be consistent with
        what get_prompt subsequently reports for that id - both should
        reflect the new, post-update data."""
        storage = Storage()
        original = Prompt(title="Before", content="Before content")
        storage.create_prompt(original)

        replacement = Prompt(id=original.id, title="After", content="After content")
        result = storage.update_prompt(original.id, replacement)

        fetched = storage.get_prompt(original.id)
        assert result is fetched

    # ---- Miss case: "update never creates" ----

    def test_update_prompt_miss_returns_none(self):
        """docstring: "or None if no prompt with prompt_id exists." Calling
        update_prompt with a prompt_id that was never created must return
        None, not raise and not silently create it."""
        storage = Storage()
        replacement = Prompt(title="Ghost", content="Ghost content")

        result = storage.update_prompt("never-existed", replacement)

        assert result is None

    def test_update_prompt_miss_does_not_create_a_new_entry(self):
        """Critical semantic per the docstring's "Replace an EXISTING
        prompt" wording: update_prompt on a missing id must have NO side
        effect at all - not just returning None, but leaving storage
        exactly as it was, with no new entry created under that id (an
        "update never creates/upserts" guarantee). Verified directly via
        get_all_prompts and get_prompt on the missing id, not inferred
        from the return value alone."""
        storage = Storage()
        assert storage.get_all_prompts() == []

        replacement = Prompt(title="Ghost", content="Ghost content")
        result = storage.update_prompt("never-existed", replacement)

        assert result is None
        assert storage.get_all_prompts() == []
        assert storage.get_prompt("never-existed") is None
        assert storage.get_prompt(replacement.id) is None

    def test_update_prompt_miss_on_non_empty_storage_leaves_existing_prompts_untouched(self):
        """When storage already holds other prompts, an update_prompt call
        targeting a nonexistent id must return None and must not create a
        new entry, while leaving the existing, unrelated prompts'
        untouched (same count, same data) - reinforcing "update never
        creates" in the more realistic non-empty-storage case."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        storage.create_prompt(prompt_a)

        replacement = Prompt(title="Ghost", content="Ghost content")
        result = storage.update_prompt("never-existed", replacement)

        assert result is None
        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].id == prompt_a.id
        assert all_prompts[0].title == "A"
        assert storage.get_prompt("never-existed") is None

    def test_update_prompt_miss_after_prompt_was_deleted_returns_none_and_does_not_recreate(self):
        """An id that existed and was then deleted must behave like an id
        that never existed for update_prompt purposes: returns None and
        does not resurrect/recreate the prompt under that id."""
        storage = Storage()
        prompt = Prompt(title="Temporary", content="Will be deleted")
        storage.create_prompt(prompt)
        storage.delete_prompt(prompt.id)
        assert storage.get_prompt(prompt.id) is None

        replacement = Prompt(id=prompt.id, title="Resurrected?", content="Should not stick")
        result = storage.update_prompt(prompt.id, replacement)

        assert result is None
        assert storage.get_prompt(prompt.id) is None
        assert storage.get_all_prompts() == []

    # ---- Persistence within a session ----

    def test_update_prompt_then_read_then_update_again_then_read_again(self):
        """Each update must be visible to subsequent reads on the same
        Storage instance, and a second update must again fully replace the
        first update's data (not merge with it)."""
        storage = Storage()
        original = Prompt(title="V1", content="Content V1")
        storage.create_prompt(original)

        update_one = Prompt(id=original.id, title="V2", content="Content V2")
        storage.update_prompt(original.id, update_one)
        assert storage.get_prompt(original.id).title == "V2"
        assert storage.get_prompt(original.id).content == "Content V2"

        update_two = Prompt(id=original.id, title="V3", content="Content V3")
        storage.update_prompt(original.id, update_two)
        fetched = storage.get_prompt(original.id)
        assert fetched.title == "V3"
        assert fetched.content == "Content V3"
        assert fetched.title != "V2"

    def test_update_prompt_updating_prompt_a_does_not_affect_prompt_b(self):
        """With multiple prompts stored, updating one prompt's data must
        leave every other stored prompt's data untouched - per the Storage
        class docstring describing _prompts as a dict keyed by id (each
        entry independent)."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)

        update_for_a = Prompt(id=prompt_a.id, title="A Updated", content="Content A Updated")
        storage.update_prompt(prompt_a.id, update_for_a)

        fetched_a = storage.get_prompt(prompt_a.id)
        fetched_b = storage.get_prompt(prompt_b.id)
        assert fetched_a.title == "A Updated"
        assert fetched_b.title == "B"
        assert fetched_b.content == "Content B"

    # ---- Key-vs-id mismatch: empirical confirmation ----

    def test_update_prompt_with_mismatched_replacement_id_is_stored_under_the_original_key(self):
        """Empirical check of a non-obvious case the docstring does not
        explicitly address: update_prompt(prompt_id, prompt)'s
        implementation is `self._prompts[prompt_id] = prompt` - it keys the
        dict entry by the `prompt_id` ARGUMENT, not by `prompt.id`. If the
        replacement Prompt object's own `.id` attribute differs from the
        `prompt_id` key being updated, the entry ends up stored under the
        ORIGINAL `prompt_id` key, but the stored object's `.id` ATTRIBUTE
        reflects the mismatched value - i.e. nothing reconciles them. This
        is confirmed here rather than assumed. The docstring only promises
        "Replace an existing prompt with new data" and does not promise
        id/key reconciliation, so this is a documented-as-is gap worth
        flagging (a caller who does not keep prompt_id and prompt.id in
        sync introduces a dict-key/attribute mismatch) rather than a bug
        against the docstring's literal wording.
        """
        storage = Storage()
        original = Prompt(id="key-id", title="Before", content="Before content")
        storage.create_prompt(original)

        mismatched_replacement = Prompt(
            id="totally-different-attribute-id",
            title="After",
            content="After content",
        )
        result = storage.update_prompt("key-id", mismatched_replacement)

        # Stored under the ORIGINAL key ("key-id"), retrievable via it:
        fetched_via_original_key = storage.get_prompt("key-id")
        assert fetched_via_original_key is not None
        assert fetched_via_original_key.title == "After"

        # NOT retrievable via the replacement's own .id attribute - nothing
        # reconciles the dict key with prompt.id:
        assert storage.get_prompt("totally-different-attribute-id") is None

        # The stored object's .id ATTRIBUTE still reflects the mismatched
        # value, distinct from the dict key it lives under:
        assert fetched_via_original_key.id == "totally-different-attribute-id"
        assert fetched_via_original_key.id != "key-id"

        # Return value mirrors the same mismatch (it is the same object):
        assert result.id == "totally-different-attribute-id"

        # Exactly one entry exists in storage - no separate entry was
        # created under the mismatched id either:
        assert len(storage.get_all_prompts()) == 1

    # ---- Cross-instance isolation ----

    def test_update_prompt_on_one_instance_does_not_affect_a_different_instance(self):
        """Mirrors the pattern established for create_prompt/get_prompt in
        TestCrossInstanceIsolation/TestGetPrompt: update_prompt on one
        Storage instance must never affect a different Storage instance's
        data, since each instance's _prompts dict is per-instance state."""
        storage_one = Storage()
        storage_two = Storage()
        prompt = Prompt(title="Shared-looking", content="Content")
        storage_one.create_prompt(prompt)
        storage_two.create_prompt(Prompt(id=prompt.id, title="Shared-looking", content="Content"))

        replacement = Prompt(id=prompt.id, title="Updated on one", content="Updated content")
        storage_one.update_prompt(prompt.id, replacement)

        assert storage_one.get_prompt(prompt.id).title == "Updated on one"
        assert storage_two.get_prompt(prompt.id).title == "Shared-looking"

    # ---- Edge case: duplicating an unrelated prompt's fields ----

    def test_update_prompt_with_data_duplicating_an_unrelated_prompts_title_is_allowed(self):
        """update_prompt's implementation performs a plain dict assignment
        with no uniqueness check across other entries, and its docstring
        makes no promise of title/content uniqueness enforcement. Updating
        prompt A so that its title/content duplicate unrelated prompt B's
        values must succeed normally - no error, no rejection - since
        nothing in the storage layer implies such a constraint."""
        storage = Storage()
        prompt_a = Prompt(title="Unique A", content="Unique content A")
        prompt_b = Prompt(title="Shared Title", content="Shared content")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)

        replacement = Prompt(id=prompt_a.id, title="Shared Title", content="Shared content")
        result = storage.update_prompt(prompt_a.id, replacement)

        assert result is not None
        fetched_a = storage.get_prompt(prompt_a.id)
        fetched_b = storage.get_prompt(prompt_b.id)
        assert fetched_a.title == fetched_b.title == "Shared Title"
        assert fetched_a.content == fetched_b.content == "Shared content"
        assert fetched_a.id != fetched_b.id
        assert len(storage.get_all_prompts()) == 2

    # ---- Object identity/mutation risk on the stored data ----

    def test_update_prompt_get_prompt_afterward_returns_the_same_object_reference(self):
        """Consistent with the object-identity finding for
        create_prompt/get_prompt (TestGetPrompt.
        test_get_prompt_returns_the_same_object_reference_as_stored):
        update_prompt's implementation is `self._prompts[prompt_id] =
        prompt` (plain reference assignment, no copy), so a subsequent
        get_prompt(prompt_id) must return the EXACT object that was passed
        into update_prompt - not a copy. Verified directly, not assumed to
        carry over from create_prompt's behavior."""
        storage = Storage()
        original = Prompt(title="Before", content="Before content")
        storage.create_prompt(original)

        replacement = Prompt(id=original.id, title="After", content="After content")
        storage.update_prompt(original.id, replacement)

        fetched = storage.get_prompt(original.id)
        assert fetched is replacement

    def test_mutating_the_prompt_after_update_prompt_corrupts_stored_state(self):
        """Direct consequence of the object-identity finding above: since
        update_prompt stores a live reference (not a copy) and get_prompt
        also returns that same live reference, a caller that mutates the
        `prompt` object AFTER passing it to update_prompt (or mutates what
        get_prompt returns) will corrupt Storage's internal state for
        future reads - the same mutation-risk pattern already established
        for create_prompt/get_prompt, now confirmed to apply post-update
        too."""
        storage = Storage()
        original = Prompt(title="Before", content="Before content")
        storage.create_prompt(original)

        replacement = Prompt(id=original.id, title="After", content="After content")
        storage.update_prompt(original.id, replacement)

        replacement.title = "Mutated after update_prompt call"

        fetched_again = storage.get_prompt(original.id)
        assert fetched_again.title == "Mutated after update_prompt call"


class TestDeletePrompt:
    """Dedicated tests for Storage.delete_prompt.

    Source of intended behavior: Storage.delete_prompt's own docstring in
    app/storage.py ("Delete a prompt by its id. ... Returns: bool: True if
    the prompt was found and deleted, False if no prompt with prompt_id
    exists." with the doctest Example `storage.delete_prompt("missing-id")
    -> False`) plus the Storage class docstring describing _prompts as
    "Prompts keyed by their id" and data as scoped to "the lifetime of the
    process". No written spec (specs/001-complete-promptlab-app/contracts/
    api-contract.md, data-model.md, docs/API_REFERENCE.md,
    docs/SYSTEM_MODEL.md) covers the Storage class directly - it is an
    internal implementation detail, not a public API contract - so intended
    behavior is inferred entirely from delete_prompt's own docstring,
    cross-checked against the sibling create_prompt/get_prompt/update_prompt
    docstrings for consistent vocabulary.

    `test_get_prompt_returns_none_after_the_prompt_was_deleted`
    (TestGetPrompt), `test_get_all_prompts_no_longer_includes_a_deleted_prompt`
    (TestGetAllPrompts), and
    `test_update_prompt_miss_after_prompt_was_deleted_returns_none_and_does_not_recreate`
    (TestUpdatePrompt) already exercise delete_prompt incidentally, to
    confirm get_prompt/get_all_prompts/update_prompt aren't stale or
    resurrecting data after a delete - those are not duplicated here; this
    class is the dedicated, primary suite for delete_prompt's own contract
    (its own return value, its own idempotency semantics, and its own
    side-effect scope).
    """

    # ---- Return value on hit ----

    def test_delete_prompt_hit_returns_true(self):
        """docstring: "Returns: bool: True if the prompt was found and
        deleted". Deleting a prompt_id that currently exists in storage
        must return True."""
        storage = Storage()
        prompt = Prompt(title="To Delete", content="Will be removed")
        storage.create_prompt(prompt)

        result = storage.delete_prompt(prompt.id)

        assert result is True

    # ---- Removal is real, not a soft-delete ----

    def test_delete_prompt_hit_removes_prompt_from_get_prompt_and_get_all_prompts(self):
        """After a successful delete, the prompt must be genuinely gone -
        not just flagged - verified via BOTH get_prompt(prompt_id) is None
        AND the prompt no longer appearing in get_all_prompts(), per
        get_prompt's "None if no prompt with prompt_id exists" and
        get_all_prompts' "Every prompt currently in storage"."""
        storage = Storage()
        prompt = Prompt(title="To Delete", content="Will be removed")
        storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id) is not None
        assert len(storage.get_all_prompts()) == 1

        storage.delete_prompt(prompt.id)

        assert storage.get_prompt(prompt.id) is None
        all_prompts = storage.get_all_prompts()
        assert prompt.id not in [p.id for p in all_prompts]
        assert all_prompts == []

    # ---- Return value on miss ----

    def test_delete_prompt_miss_on_empty_storage_returns_false(self):
        """docstring Example: `storage.delete_prompt("missing-id") ->
        False`. On a freshly constructed Storage with zero prompts, any
        delete attempt must return False, not raise."""
        storage = Storage()

        result = storage.delete_prompt("missing-id")

        assert result is False

    def test_delete_prompt_miss_on_non_empty_storage_returns_false(self):
        """docstring: "False if no prompt with prompt_id exists". When
        storage is non-empty but the requested id matches none of the
        stored prompts, the result must still be False, per the same
        contract that applies on empty storage."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))
        storage.create_prompt(Prompt(title="B", content="Content B"))

        result = storage.delete_prompt("id-that-was-never-created")

        assert result is False

    # ---- No side effects on miss ----

    def test_delete_prompt_miss_does_not_affect_other_prompts_field_values(self):
        """A failed delete attempt (id not found) must not affect any OTHER
        prompts already in storage - not just "still present" but with
        field values fully unchanged, since delete_prompt's docstring only
        promises removal of a MATCHING prompt_id, implying no effect at all
        when no match exists."""
        storage = Storage()
        prompt_a = Prompt(
            title="A",
            content="Content A",
            description="Description A",
            collection_id="collection-A",
        )
        prompt_b = Prompt(title="B", content="Content B")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)

        result = storage.delete_prompt("never-existed")

        assert result is False
        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 2

        fetched_a = storage.get_prompt(prompt_a.id)
        assert fetched_a is not None
        assert fetched_a.title == "A"
        assert fetched_a.content == "Content A"
        assert fetched_a.description == "Description A"
        assert fetched_a.collection_id == "collection-A"
        assert fetched_a.created_at == prompt_a.created_at
        assert fetched_a.updated_at == prompt_a.updated_at

        fetched_b = storage.get_prompt(prompt_b.id)
        assert fetched_b is not None
        assert fetched_b.title == "B"
        assert fetched_b.content == "Content B"

    # ---- Double-delete idempotency ----

    def test_delete_prompt_called_twice_second_call_returns_false_not_true(self):
        """The single most important idempotency semantic for this method:
        deleting the same prompt_id twice must NOT return True both times.
        The first call finds the prompt (it "was found and deleted" per the
        docstring) and returns True; by the second call the prompt no
        longer exists, so per the same docstring sentence's other branch
        ("False if no prompt with prompt_id exists") the second call must
        return False. delete_prompt must not raise on the second call
        either - it is a plain `if prompt_id in self._prompts` check, which
        is always safe to repeat."""
        storage = Storage()
        prompt = Prompt(title="To Delete", content="Will be removed")
        storage.create_prompt(prompt)

        first_result = storage.delete_prompt(prompt.id)
        second_result = storage.delete_prompt(prompt.id)

        assert first_result is True
        assert second_result is False

    def test_delete_prompt_called_twice_prompt_remains_gone_after_both_calls(self):
        """Reinforces the double-delete finding above from the read side:
        after both delete calls, the prompt must still be absent from both
        get_prompt and get_all_prompts - the second (no-op) call must not
        somehow resurrect it or leave storage in an inconsistent state."""
        storage = Storage()
        prompt = Prompt(title="To Delete", content="Will be removed")
        storage.create_prompt(prompt)

        storage.delete_prompt(prompt.id)
        storage.delete_prompt(prompt.id)

        assert storage.get_prompt(prompt.id) is None
        assert storage.get_all_prompts() == []

    # ---- Persistence within a session: deleting one leaves others intact ----

    def test_delete_prompt_from_the_middle_of_several_leaves_the_others_intact(self):
        """Create several prompts, delete one specific one from the MIDDLE
        of the set (not just when there's only one), confirm the OTHERS are
        all still present and correct via get_all_prompts()/get_prompt() -
        deleting one must not disturb unrelated entries, per the Storage
        class docstring describing _prompts as a dict keyed by id (each
        entry independent)."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        prompt_c = Prompt(title="C", content="Content C")
        prompt_d = Prompt(title="D", content="Content D")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        storage.create_prompt(prompt_c)
        storage.create_prompt(prompt_d)

        result = storage.delete_prompt(prompt_b.id)

        assert result is True
        remaining_ids = {p.id for p in storage.get_all_prompts()}
        assert remaining_ids == {prompt_a.id, prompt_c.id, prompt_d.id}
        assert prompt_b.id not in remaining_ids
        assert storage.get_prompt(prompt_b.id) is None

        fetched_a = storage.get_prompt(prompt_a.id)
        fetched_c = storage.get_prompt(prompt_c.id)
        fetched_d = storage.get_prompt(prompt_d.id)
        assert fetched_a.title == "A"
        assert fetched_c.title == "C"
        assert fetched_d.title == "D"

    def test_delete_prompt_first_then_last_of_several_leaves_the_middle_intact(self):
        """Order-independence check complementing the middle-delete test
        above: deleting the FIRST-created and then the LAST-created prompt
        out of several must leave the ones created in between fully intact,
        confirming delete_prompt's effect is scoped strictly to the
        requested id regardless of insertion position."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        prompt_c = Prompt(title="C", content="Content C")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        storage.create_prompt(prompt_c)

        assert storage.delete_prompt(prompt_a.id) is True
        assert storage.delete_prompt(prompt_c.id) is True

        remaining = storage.get_all_prompts()
        assert len(remaining) == 1
        assert remaining[0].id == prompt_b.id
        assert remaining[0].title == "B"
        assert storage.get_prompt(prompt_a.id) is None
        assert storage.get_prompt(prompt_c.id) is None

    # ---- Cross-instance isolation ----

    def test_delete_prompt_on_one_instance_does_not_affect_a_different_instance(self):
        """Mirrors the pattern established for create_prompt/get_prompt/
        update_prompt in TestCrossInstanceIsolation/TestGetPrompt/
        TestUpdatePrompt: delete_prompt on one Storage instance must never
        affect a different Storage instance's data, since each instance's
        _prompts dict is per-instance state (Storage class docstring's
        Attributes section). To make the isolation check meaningful even
        when ids could otherwise coincide, two prompts are explicitly
        constructed with the SAME id across two separate Storage
        instances."""
        storage_one = Storage()
        storage_two = Storage()
        shared_id = "same-id-on-both-instances"
        storage_one.create_prompt(Prompt(id=shared_id, title="On instance one", content="Content"))
        storage_two.create_prompt(Prompt(id=shared_id, title="On instance two", content="Content"))

        result = storage_one.delete_prompt(shared_id)

        assert result is True
        assert storage_one.get_prompt(shared_id) is None
        assert storage_one.get_all_prompts() == []

        # Instance two's same-id prompt must be entirely untouched:
        fetched_two = storage_two.get_prompt(shared_id)
        assert fetched_two is not None
        assert fetched_two.title == "On instance two"
        assert len(storage_two.get_all_prompts()) == 1

    def test_delete_prompt_miss_on_one_instance_does_not_affect_a_different_instance(self):
        """Complements the hit-case isolation test above: a delete_prompt
        call that MISSES (id not found) on one Storage instance must also
        have zero effect on a different Storage instance, even when that
        other instance happens to hold a prompt under the same id being
        searched for on the first instance."""
        storage_one = Storage()
        storage_two = Storage()
        shared_id = "id-only-on-instance-two"
        storage_two.create_prompt(Prompt(id=shared_id, title="Only on two", content="Content"))

        result = storage_one.delete_prompt(shared_id)

        assert result is False
        assert storage_one.get_all_prompts() == []
        fetched_two = storage_two.get_prompt(shared_id)
        assert fetched_two is not None
        assert fetched_two.title == "Only on two"

    # ---- Edge cases ----

    def test_delete_prompt_with_empty_string_id_on_empty_storage_returns_false(self):
        """An empty-string id is not a valid id any create_prompt call
        would produce (generate_id always yields a non-empty uuid4 string),
        so deleting it on empty storage must safely return False rather
        than raising - `"" in {}` is always False, and the docstring
        promises False for "no prompt with prompt_id exists", which an
        empty string trivially satisfies."""
        storage = Storage()

        result = storage.delete_prompt("")

        assert result is False

    def test_delete_prompt_with_empty_string_id_on_non_empty_storage_returns_false_and_no_side_effects(self):
        """Same empty-string-id edge case as above, but on non-empty
        storage: must return False and must not delete/affect any of the
        real prompts present (an empty string must never be treated as a
        wildcard or accidentally match a real id)."""
        storage = Storage()
        prompt = Prompt(title="A", content="Content A")
        storage.create_prompt(prompt)

        result = storage.delete_prompt("")

        assert result is False
        assert storage.get_prompt(prompt.id) is not None
        assert len(storage.get_all_prompts()) == 1

    def test_delete_prompt_then_recreate_with_the_same_explicit_id_succeeds_cleanly(self):
        """Empirical check of a non-obvious case the docstring does not
        explicitly address: after deleting a prompt, calling create_prompt
        again with a NEW Prompt object that explicitly reuses the same
        .id must succeed cleanly, with no leftover "tombstone" state
        blocking or corrupting the reused id - delete_prompt's
        implementation is a plain `del self._prompts[prompt_id]`, which
        leaves no trace behind in the dict once the key is removed."""
        storage = Storage()
        original = Prompt(id="reusable-id", title="Original", content="Original content")
        storage.create_prompt(original)
        assert storage.delete_prompt("reusable-id") is True
        assert storage.get_prompt("reusable-id") is None

        recreated = Prompt(id="reusable-id", title="Recreated", content="Recreated content")
        result = storage.create_prompt(recreated)

        assert result is recreated
        fetched = storage.get_prompt("reusable-id")
        assert fetched is not None
        assert fetched.title == "Recreated"
        assert fetched.content == "Recreated content"
        assert fetched is recreated
        assert len(storage.get_all_prompts()) == 1

    def test_delete_prompt_return_type_is_a_real_bool_not_a_truthy_object(self):
        """docstring type hint: `-> bool`. Both the hit and miss return
        values must be actual bool instances (True/False), not merely
        truthy/falsy objects (e.g. not None on miss, not the deleted
        Prompt object on hit)."""
        storage = Storage()
        prompt = Prompt(title="A", content="Content A")
        storage.create_prompt(prompt)

        hit_result = storage.delete_prompt(prompt.id)
        miss_result = storage.delete_prompt("does-not-exist")

        assert isinstance(hit_result, bool)
        assert hit_result is True
        assert isinstance(miss_result, bool)
        assert miss_result is False


class TestPersistenceWithinSession:
    """Tests that multiple create_prompt calls on a single Storage
    instance accumulate correctly, per the Storage class docstring
    ("Data exists only for the lifetime of the process") implying data
    persists across calls within that lifetime, and get_all_prompts'
    docstring promising "Every prompt currently in storage" (i.e. all
    of them, not just the most recent).
    """

    def test_creating_multiple_prompts_each_independently_retrievable(self):
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")

        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)

        fetched_a = storage.get_prompt(prompt_a.id)
        fetched_b = storage.get_prompt(prompt_b.id)
        assert fetched_a is not None and fetched_a.title == "A"
        assert fetched_b is not None and fetched_b.title == "B"

    def test_get_all_prompts_accumulates_all_created_prompts(self):
        """get_all_prompts must return every prompt created so far, not
        just the last one created - per its docstring "Every prompt
        currently in storage"."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        prompt_c = Prompt(title="C", content="Content C")

        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        storage.create_prompt(prompt_c)

        all_prompts = storage.get_all_prompts()
        ids = {p.id for p in all_prompts}
        assert len(all_prompts) == 3
        assert ids == {prompt_a.id, prompt_b.id, prompt_c.id}

    def test_creating_prompt_b_does_not_affect_prompt_a_stored_data(self):
        """Creating a second prompt must not mutate a previously stored
        prompt's field values - each dict entry is independent."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A", description="desc A")

        storage.create_prompt(prompt_a)
        storage.create_prompt(Prompt(title="B", content="Content B", description="desc B"))

        fetched_a = storage.get_prompt(prompt_a.id)
        assert fetched_a.title == "A"
        assert fetched_a.content == "Content A"
        assert fetched_a.description == "desc A"

    def test_creating_many_prompts_all_present_and_uncollided(self):
        """Basic stress/sanity check on the dict-backed store: creating
        several prompts (each with its own generate_id-derived id) must
        result in all of them being present with no loss or
        collision."""
        storage = Storage()
        created = [Prompt(title=f"Title {i}", content=f"Content {i}") for i in range(10)]

        for prompt in created:
            storage.create_prompt(prompt)

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 10

        stored_by_id = {p.id: p for p in all_prompts}
        for original in created:
            assert original.id in stored_by_id
            assert stored_by_id[original.id].title == original.title
            assert stored_by_id[original.id].content == original.content


class TestCrossInstanceIsolation:
    """Guards against any accidental shared/class-level mutable state on
    Storage - each Storage() instance's docstring/attributes
    (_prompts: Dict[str, Prompt]) implies per-instance state, and
    __init__'s docstring/example ("storage = Storage(); ...
    get_all_prompts() -> []") shows a freshly constructed instance
    starts empty regardless of what other instances hold.
    """

    def test_two_storage_instances_do_not_share_created_prompts(self):
        storage_one = Storage()
        storage_two = Storage()
        prompt = Prompt(title="Only in one", content="Content")

        storage_one.create_prompt(prompt)

        assert storage_one.get_prompt(prompt.id) is not None
        assert storage_two.get_prompt(prompt.id) is None
        assert storage_two.get_all_prompts() == []

    def test_two_storage_instances_maintain_independent_counts(self):
        storage_one = Storage()
        storage_two = Storage()

        storage_one.create_prompt(Prompt(title="A", content="Content A"))
        storage_one.create_prompt(Prompt(title="B", content="Content B"))
        storage_two.create_prompt(Prompt(title="C", content="Content C"))

        assert len(storage_one.get_all_prompts()) == 2
        assert len(storage_two.get_all_prompts()) == 1


class TestEdgeCases:
    """Boundary and edge-case behavior for create_prompt that is not
    explicitly promised or forbidden by the docstring, but is worth
    pinning down empirically (per instructions: confirm directly,
    don't assume).
    """

    def test_create_prompt_with_duplicate_id_silently_overwrites(self):
        """create_prompt's implementation is a plain dict assignment
        (self._prompts[prompt.id] = prompt) with no uniqueness check,
        and its docstring makes no promise of duplicate-id rejection or
        of preserving a prior prompt sharing the same id. Two Prompt
        objects manually constructed with the same explicit id must
        therefore result in the second call overwriting the first, with
        only the second prompt's data retrievable afterward and
        get_all_prompts reporting exactly one entry for that id.

        This is a documented gap (no uniqueness enforcement at the
        storage layer) rather than a bug: the docstring never promises
        id-collision protection, so this test pins down the observed
        (and, per the docstring, permitted) behavior rather than
        asserting it is desirable.
        """
        storage = Storage()
        shared_id = "duplicate-id"
        first = Prompt(id=shared_id, title="First", content="First content")
        second = Prompt(id=shared_id, title="Second", content="Second content")

        storage.create_prompt(first)
        storage.create_prompt(second)

        fetched = storage.get_prompt(shared_id)
        assert fetched.title == "Second"
        assert fetched.content == "Second content"

        all_prompts = storage.get_all_prompts()
        matching = [p for p in all_prompts if p.id == shared_id]
        assert len(matching) == 1

    def test_create_prompt_on_empty_storage_results_in_exactly_one_prompt(self):
        """Boundary case: the very first create_prompt call on a fresh
        Storage() (zero -> one prompts) must leave storage with exactly
        one prompt, per __init__'s docstring showing get_all_prompts()
        starts as []."""
        storage = Storage()
        assert storage.get_all_prompts() == []

        prompt = Prompt(title="First ever", content="Content")
        storage.create_prompt(prompt)

        assert len(storage.get_all_prompts()) == 1

    def test_create_prompt_generated_ids_are_unique_across_instances(self):
        """Sanity check that relying on Prompt's default id generation
        (generate_id, via uuid4) rather than explicit ids does not by
        itself produce collisions when creating many prompts - this is
        what production callers (the API routes) actually do."""
        storage = Storage()
        prompts = [Prompt(title=f"T{i}", content=f"C{i}") for i in range(8)]

        for prompt in prompts:
            storage.create_prompt(prompt)

        ids = [p.id for p in prompts]
        assert len(ids) == len(set(ids))
        assert len(storage.get_all_prompts()) == 8


class TestCreateCollection:
    """Tests for Storage.create_collection.

    Source of intended behavior: Storage.create_collection's own docstring
    in app/storage.py ("Store a new collection. ... Returns: Collection:
    The stored collection.") plus the Storage class docstring's
    description of _collections as "Collections keyed by their id" and
    data as scoped to "the lifetime of the process" (i.e. persists across
    calls within a single Storage instance's lifetime, with no
    cross-instance sharing). No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers the
    Storage class directly - it is an internal implementation detail, not
    a public API contract - so intended behavior is inferred entirely from
    create_collection's own docstring, cross-checked against
    CollectionBase/Collection's field contract in app/models.py (name is
    required via Field(...); description is optional, defaulting to None;
    unlike Prompt, Collection has NO updated_at field - confirmed by
    reading app/models.py directly, so no updated_at assertions appear
    below).

    This class deliberately mirrors TestPromptCRUD's structure (identity
    return value, field preservation, retrievability, required-vs-optional
    round-tripping) as well as the persistence-within-session,
    cross-instance-isolation, and duplicate-id-overwrite edge cases
    already established for create_prompt in TestPersistenceWithinSession/
    TestCrossInstanceIsolation/TestEdgeCases - those classes are currently
    scoped to Prompt operations only (per their own docstrings/class
    names), so the Collection-side equivalents are included directly in
    this class rather than added to the Prompt-scoped classes. This is
    also the first test class in this file to exercise
    _prompts/_collections store independence directly.
    """

    # ---- Return value ----

    def test_create_collection_returns_the_same_collection_passed_in(self):
        """docstring: "Returns: Collection: The stored collection." - the
        returned object must be the collection that was stored, not a
        copy, a subset, or a different collection (identity check, not
        just equality - mirrors
        TestPromptCRUD.test_create_prompt_returns_the_same_prompt_passed_in)."""
        storage = Storage()
        collection = Collection(name="My Collection")

        result = storage.create_collection(collection)

        assert result is collection

    # ---- Field preservation ----

    def test_create_collection_preserves_all_submitted_field_values(self):
        """The stored/returned collection's field values must match
        exactly what was submitted - create_collection must not alter
        name or description."""
        storage = Storage()
        collection = Collection(
            name="Engineering Prompts",
            description="A collection of engineering-related prompts",
        )

        result = storage.create_collection(collection)

        assert result.name == "Engineering Prompts"
        assert result.description == "A collection of engineering-related prompts"

    # ---- Retrievability ----

    def test_create_collection_is_retrievable_via_get_collection(self):
        """A collection stored via create_collection must be findable
        afterward via get_collection(collection.id) - per the Storage
        class docstring describing _collections as "keyed by their id"
        and get_collection's own docstring ("Retrieve a single collection
        by its id")."""
        storage = Storage()
        collection = Collection(name="My Collection")

        storage.create_collection(collection)

        fetched = storage.get_collection(collection.id)
        assert fetched is not None
        assert fetched.id == collection.id
        assert fetched.name == "My Collection"

    def test_create_collection_appears_in_get_all_collections(self):
        """A collection stored via create_collection must appear in
        get_all_collections()'s result - per get_all_collections'
        docstring ("Every collection currently in storage")."""
        storage = Storage()
        collection = Collection(name="My Collection")

        storage.create_collection(collection)

        all_collections = storage.get_all_collections()
        assert len(all_collections) == 1
        assert all_collections[0].id == collection.id

    # ---- Required vs optional fields ----

    def test_create_collection_with_only_required_fields_round_trips(self):
        """name is the only required field on CollectionBase
        (Field(..., min_length=1, max_length=100)); description defaults
        to None (Field(None, max_length=500)). Creating a collection with
        only name set must succeed and round-trip through get_collection
        with description defaulting to None."""
        storage = Storage()
        collection = Collection(name="Minimal")

        storage.create_collection(collection)
        fetched = storage.get_collection(collection.id)

        assert fetched.name == "Minimal"
        assert fetched.description is None

    def test_create_collection_with_all_fields_populated_round_trips(self):
        """When description is also provided, it must be stored and
        retrievable verbatim alongside name."""
        storage = Storage()
        collection = Collection(name="Full", description="Full description")

        storage.create_collection(collection)
        fetched = storage.get_collection(collection.id)

        assert fetched.name == "Full"
        assert fetched.description == "Full description"

    # ---- Persistence within a session ----

    def test_creating_multiple_collections_each_independently_retrievable(self):
        """Mirrors
        TestPersistenceWithinSession.test_creating_multiple_prompts_each_independently_retrievable
        for the Collection side: per the Storage class docstring ("Data
        exists only for the lifetime of the process"), multiple
        create_collection calls on a single Storage instance must each
        remain independently retrievable."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")

        storage.create_collection(collection_a)
        storage.create_collection(collection_b)

        fetched_a = storage.get_collection(collection_a.id)
        fetched_b = storage.get_collection(collection_b.id)
        assert fetched_a is not None and fetched_a.name == "A"
        assert fetched_b is not None and fetched_b.name == "B"

    def test_get_all_collections_accumulates_all_created_collections(self):
        """get_all_collections must return every collection created so
        far, not just the most recent one - per its docstring "Every
        collection currently in storage"."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        collection_c = Collection(name="C")

        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_collection(collection_c)

        all_collections = storage.get_all_collections()
        ids = {c.id for c in all_collections}
        assert len(all_collections) == 3
        assert ids == {collection_a.id, collection_b.id, collection_c.id}

    def test_creating_collection_b_does_not_affect_collection_a_stored_data(self):
        """Creating a second collection must not mutate a previously
        stored collection's field values - each dict entry is
        independent, per the Storage class docstring describing
        _collections as "keyed by their id"."""
        storage = Storage()
        collection_a = Collection(name="A", description="desc A")

        storage.create_collection(collection_a)
        storage.create_collection(Collection(name="B", description="desc B"))

        fetched_a = storage.get_collection(collection_a.id)
        assert fetched_a.name == "A"
        assert fetched_a.description == "desc A"

    def test_creating_several_collections_all_present_and_uncollided(self):
        """Basic stress/sanity check on the dict-backed store: creating
        several collections (each with its own generate_id-derived id)
        must result in all of them being present with no loss or
        collision - mirrors
        TestEdgeCases.test_create_prompt_generated_ids_are_unique_across_instances
        for the Collection side."""
        storage = Storage()
        created = [Collection(name=f"Collection {i}") for i in range(8)]

        for collection in created:
            storage.create_collection(collection)

        all_collections = storage.get_all_collections()
        assert len(all_collections) == 8

        stored_by_id = {c.id: c for c in all_collections}
        for original in created:
            assert original.id in stored_by_id
            assert stored_by_id[original.id].name == original.name

    # ---- Cross-instance isolation ----

    def test_two_storage_instances_do_not_share_created_collections(self):
        """Mirrors
        TestCrossInstanceIsolation.test_two_storage_instances_do_not_share_created_prompts
        for the Collection side: each Storage() instance's _collections
        dict is per-instance state (Storage class docstring's Attributes
        section), so a collection created on one instance must be
        invisible to a different instance."""
        storage_one = Storage()
        storage_two = Storage()
        collection = Collection(name="Only in one")

        storage_one.create_collection(collection)

        assert storage_one.get_collection(collection.id) is not None
        assert storage_two.get_collection(collection.id) is None
        assert storage_two.get_all_collections() == []

    def test_two_storage_instances_maintain_independent_collection_counts(self):
        storage_one = Storage()
        storage_two = Storage()

        storage_one.create_collection(Collection(name="A"))
        storage_one.create_collection(Collection(name="B"))
        storage_two.create_collection(Collection(name="C"))

        assert len(storage_one.get_all_collections()) == 2
        assert len(storage_two.get_all_collections()) == 1

    # ---- Edge case: duplicate-id overwrite (empirically verified, not assumed) ----

    def test_create_collection_with_duplicate_id_silently_overwrites(self):
        """Empirically verified for create_collection specifically (not
        assumed to carry over from the create_prompt finding in
        TestEdgeCases.test_create_prompt_with_duplicate_id_silently_overwrites),
        since both methods share the exact same implementation pattern:
        `self._collections[collection.id] = collection`, a plain dict
        assignment with no uniqueness check. create_collection's docstring
        makes no promise of duplicate-id rejection or of preserving a
        prior collection sharing the same id. Two Collection objects
        manually constructed with the same explicit id must therefore
        result in the second call overwriting the first, with only the
        second collection's data retrievable afterward and
        get_all_collections reporting exactly one entry for that id.

        This is a documented gap (no uniqueness enforcement at the
        storage layer), consistent with the identical finding already
        made for create_prompt - not a NEW bug, but confirmed here to
        empirically hold for create_collection too rather than assumed:
        the docstring never promises id-collision protection, so this
        test pins down the observed (and, per the docstring, permitted)
        behavior rather than asserting it is desirable.
        """
        storage = Storage()
        shared_id = "duplicate-collection-id"
        first = Collection(id=shared_id, name="First")
        second = Collection(id=shared_id, name="Second")

        storage.create_collection(first)
        storage.create_collection(second)

        fetched = storage.get_collection(shared_id)
        assert fetched.name == "Second"

        all_collections = storage.get_all_collections()
        matching = [c for c in all_collections if c.id == shared_id]
        assert len(matching) == 1

    # ---- Other boundary cases ----

    def test_create_collection_on_empty_storage_results_in_exactly_one_collection(self):
        """Boundary case: the very first create_collection call on a
        fresh Storage() (zero -> one collections) must leave storage with
        exactly one collection, per __init__'s docstring showing a
        freshly constructed instance starts empty."""
        storage = Storage()
        assert storage.get_all_collections() == []

        collection = Collection(name="First ever")
        storage.create_collection(collection)

        assert len(storage.get_all_collections()) == 1

    def test_create_collection_generated_ids_are_unique_across_instances(self):
        """Sanity check that relying on Collection's default id
        generation (generate_id, via uuid4) rather than explicit ids does
        not by itself produce collisions when creating many collections -
        this is what production callers (the API routes) actually do."""
        storage = Storage()
        collections = [Collection(name=f"C{i}") for i in range(8)]

        for collection in collections:
            storage.create_collection(collection)

        ids = [c.id for c in collections]
        assert len(ids) == len(set(ids))
        assert len(storage.get_all_collections()) == 8

    # ---- Edge case: _prompts and _collections stores are genuinely independent ----

    def test_create_collection_does_not_affect_the_prompts_store(self):
        """Sanity check that _prompts and _collections are genuinely
        independent dicts on the same Storage instance, per the Storage
        class docstring's Attributes section listing them as two separate
        attributes. Creating a Collection must never add, remove, or
        alter anything in _prompts - this has been implicitly true
        throughout every prior create_prompt-focused test in this file,
        but is asserted directly here for the first time."""
        storage = Storage()
        prompt = Prompt(title="Existing prompt", content="Some content")
        storage.create_prompt(prompt)
        assert len(storage.get_all_prompts()) == 1

        storage.create_collection(Collection(name="A new collection"))

        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].id == prompt.id
        assert all_prompts[0].title == "Existing prompt"

    def test_create_prompt_does_not_affect_the_collections_store(self):
        """Reverse direction of the independence check above: creating a
        Prompt must never add, remove, or alter anything in
        _collections."""
        storage = Storage()
        collection = Collection(name="Existing collection")
        storage.create_collection(collection)
        assert len(storage.get_all_collections()) == 1

        storage.create_prompt(Prompt(title="A new prompt", content="Some content"))

        all_collections = storage.get_all_collections()
        assert len(all_collections) == 1
        assert all_collections[0].id == collection.id
        assert all_collections[0].name == "Existing collection"


class TestGetCollection:
    """Dedicated tests for Storage.get_collection.

    Source of intended behavior: Storage.get_collection's own docstring in
    app/storage.py ("Retrieve a single collection by its id. ... Returns:
    Optional[Collection]: The matching collection, or None if no
    collection with collection_id exists.") plus the Storage class
    docstring describing _collections as "Collections keyed by their id"
    and data as scoped to "the lifetime of the process". No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers
    the Storage class directly - it is an internal implementation
    detail, not a public API contract - so intended behavior is
    inferred entirely from the docstrings above plus the natural
    read/write pairing with create_collection and delete_collection.

    This class is the direct Collection-side analog of TestGetPrompt and
    mirrors its structure and rigor exactly. Field contract verified
    directly against app/models.py: Collection (via CollectionBase) has
    name (required) and description (optional, defaults to None), plus
    server-generated id and created_at. Unlike Prompt, Collection has NO
    updated_at field - confirmed by reading app/models.py directly (only
    Prompt declares `updated_at: datetime = Field(default_factory=
    get_current_time)`; Collection declares only `id` and `created_at`
    beyond the CollectionBase fields) - so no updated_at assertions
    appear below, and created_at is asserted instead.

    TestCreateCollection already exercises get_collection incidentally
    (e.g. test_create_collection_is_retrievable_via_get_collection,
    test_create_collection_with_only_required_fields_round_trips) but
    only to verify create_collection's own contract (that created data
    round-trips at all) - those tests are not duplicated here. This
    class instead treats get_collection itself as the subject under
    test: miss cases, deletion, object identity/mutation, repeated-read
    consistency, exact-match/case-sensitivity, and cross-instance
    isolation.
    """

    # ---- Hit case ----

    def test_get_collection_hit_returns_full_field_fidelity(self):
        """docstring: "Optional[Collection]: The matching collection". A
        collection retrieved right after creation must match on every
        field, not just id - name, description, and created_at must all
        be preserved verbatim. (Collection has no updated_at field, per
        app/models.py - confirmed directly, not assumed.)"""
        storage = Storage()
        collection = Collection(
            name="Engineering Prompts",
            description="A collection of engineering-related prompts",
        )

        storage.create_collection(collection)
        fetched = storage.get_collection(collection.id)

        assert fetched is not None
        assert fetched.id == collection.id
        assert fetched.name == collection.name
        assert fetched.description == collection.description
        assert fetched.created_at == collection.created_at
        assert not hasattr(fetched, "updated_at")

    # ---- Miss case: id never existed ----

    def test_get_collection_returns_none_on_empty_storage(self):
        """docstring: "or None if no collection with collection_id
        exists". On a freshly constructed Storage with zero collections,
        any lookup must return None, not raise and not return a
        default/empty Collection."""
        storage = Storage()

        result = storage.get_collection("any-id")

        assert result is None

    def test_get_collection_returns_none_when_id_does_not_match_any_stored_collection(self):
        """docstring: "or None if no collection with collection_id
        exists". When storage is non-empty but the requested id matches
        none of the stored collections, the result must still be None."""
        storage = Storage()
        storage.create_collection(Collection(name="A"))
        storage.create_collection(Collection(name="B"))

        result = storage.get_collection("id-that-was-never-created")

        assert result is None

    # ---- Miss case: id existed then was deleted ----

    def test_get_collection_returns_none_after_the_collection_was_deleted(self):
        """A collection that existed and was then removed via
        delete_collection must behave identically to an id that never
        existed - get_collection must return None, not a stale reference
        to the deleted collection and not an error. This exercises the
        natural read/write/delete lifecycle implied by the Storage class
        docstring and delete_collection's own docstring ("Delete a
        collection by its id")."""
        storage = Storage()
        collection = Collection(name="Temporary")
        storage.create_collection(collection)
        assert storage.get_collection(collection.id) is not None

        deleted = storage.delete_collection(collection.id)
        assert deleted is True

        result = storage.get_collection(collection.id)
        assert result is None

    # ---- Returned object identity/independence ----

    def test_get_collection_returns_the_same_object_reference_as_stored(self):
        """Empirical check (not documented, but observable): Storage's
        implementation is `return self._collections.get(collection_id)`,
        and Python dict.get returns the exact stored reference rather
        than a copy. Collection's Config only sets from_attributes =
        True - it is not frozen - so Pydantic does not prevent mutation
        either. This test verifies directly (rather than assuming the
        get_prompt finding carries over just because the implementation
        pattern is identical) that get_collection returns the identical
        object that create_collection stored, i.e. NOT a defensive
        copy."""
        storage = Storage()
        collection = Collection(name="Original")
        storage.create_collection(collection)

        fetched = storage.get_collection(collection.id)

        assert fetched is collection

    def test_mutating_the_returned_collection_corrupts_stored_state(self):
        """Direct consequence of the object-identity finding above: since
        get_collection returns a live reference (not a copy), a caller
        that mutates the object obtained via get_collection will corrupt
        the Storage instance's internal state for future reads. This is
        not promised or forbidden by get_collection's docstring, but is
        important, non-obvious behavior worth pinning down explicitly -
        it means callers must treat get_collection's result as read-only
        by convention only, since the storage layer offers no
        enforcement. Mirrors the identical finding already confirmed for
        get_prompt (TestGetPrompt), now empirically verified to hold for
        get_collection too rather than assumed."""
        storage = Storage()
        collection = Collection(name="Original")
        storage.create_collection(collection)

        fetched = storage.get_collection(collection.id)
        fetched.name = "Mutated via returned reference"

        fetched_again = storage.get_collection(collection.id)
        assert fetched_again.name == "Mutated via returned reference"

    # ---- Persistence within a session (repeated reads, no side effects) ----

    def test_get_collection_repeated_calls_return_consistent_results(self):
        """Reading via get_collection must be side-effect free: calling
        it multiple times in a row for the same id on the same Storage
        instance must keep returning an equal (and, per the identity
        finding above, literally the same-object) result each time - the
        Storage class docstring frames these as "read" operations,
        implying no state change from reading."""
        storage = Storage()
        collection = Collection(name="Stable")
        storage.create_collection(collection)

        first_read = storage.get_collection(collection.id)
        second_read = storage.get_collection(collection.id)
        third_read = storage.get_collection(collection.id)

        assert first_read == second_read == third_read
        assert first_read is second_read is third_read

    # ---- Edge cases ----

    def test_get_collection_with_empty_string_id_returns_none(self):
        """An empty-string id is not a valid id any create_collection
        call would produce (generate_id always yields a non-empty uuid4
        string), so looking it up must safely return None rather than
        raising - dict.get on a missing key never raises, and
        get_collection's docstring promises None for "no collection with
        collection_id exists", which an empty string trivially satisfies
        on a store with no empty-string-keyed collection."""
        storage = Storage()
        storage.create_collection(Collection(name="A"))

        result = storage.get_collection("")

        assert result is None

    def test_get_collection_with_id_off_by_one_character_does_not_match(self):
        """get_collection must perform exact-match lookup, not
        prefix/fuzzy matching - per the Storage class docstring
        describing _collections as a dict "keyed by their id" (dict key
        lookup is always exact). An id that differs from a stored
        collection's id by a single character must not be treated as a
        match."""
        storage = Storage()
        collection = Collection(id="abcdefgh-id", name="Exact")
        storage.create_collection(collection)

        near_miss_id = "abcdefgh-idX"
        result = storage.get_collection(near_miss_id)

        assert result is None

    def test_get_collection_id_lookup_is_case_sensitive(self):
        """Ids are plain strings and dict keys in Python are compared
        case-sensitively, so a differently-cased id must not match a
        stored collection - exact-match semantics per the "keyed by
        their id" description in the Storage class docstring."""
        storage = Storage()
        collection = Collection(id="MixedCase-ID", name="Case")
        storage.create_collection(collection)

        assert storage.get_collection("MixedCase-ID") is not None
        assert storage.get_collection("mixedcase-id") is None
        assert storage.get_collection("MIXEDCASE-ID") is None

    def test_get_collection_among_several_returns_exactly_the_requested_one(self):
        """With multiple collections stored, requesting one by id must
        return exactly that collection's data, never a different stored
        collection's data - per get_collection's docstring ("Retrieve a
        single collection by its id") and _collections being keyed by id
        (one-to-one mapping)."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        collection_c = Collection(name="C")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_collection(collection_c)

        fetched_b = storage.get_collection(collection_b.id)

        assert fetched_b is not None
        assert fetched_b.id == collection_b.id
        assert fetched_b.name == "B"
        assert fetched_b.id != collection_a.id
        assert fetched_b.id != collection_c.id

    # ---- Cross-instance isolation ----

    def test_get_collection_never_sees_a_collection_created_on_a_different_instance(self):
        """Mirrors the pattern established for get_prompt in
        TestGetPrompt and for create_collection in TestCreateCollection:
        a collection created on one Storage instance must be invisible
        to get_collection on a different Storage instance, since each
        instance's _collections dict is per-instance state (Storage
        class docstring's Attributes section, and __init__'s
        docstring/example showing a freshly constructed instance starts
        empty)."""
        storage_one = Storage()
        storage_two = Storage()
        collection = Collection(name="Only in one")
        storage_one.create_collection(collection)

        assert storage_one.get_collection(collection.id) is not None
        assert storage_two.get_collection(collection.id) is None


class TestGetAllCollections:
    """Dedicated tests for Storage.get_all_collections.

    Source of intended behavior: Storage.get_all_collections' own
    docstring in app/storage.py ("Retrieve all stored collections. ...
    Returns: List[Collection]: Every collection currently in storage, in
    no particular order.") plus the Storage class docstring describing
    _collections as "Collections keyed by their id" and data as scoped
    to "the lifetime of the process". No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers
    the Storage class directly - it is an internal implementation
    detail, not a public API contract - so intended behavior is
    inferred entirely from the docstring above.

    This class is the direct Collection-side analog of
    TestGetAllPrompts and mirrors its structure and rigor exactly.
    TestCreateCollection already calls get_all_collections incidentally
    (e.g. to verify create_collection's own round-trip contract); those
    calls are not duplicated here. This class instead treats
    get_all_collections itself as the subject under test: the empty
    case, return-type guarantees, order, snapshot/aliasing semantics,
    repeated-call consistency, staleness after mutation, and
    cross-instance isolation.
    """

    # ---- Empty case ----

    def test_get_all_collections_on_fresh_storage_returns_empty_list(self):
        """docstring Example: "storage = Storage();
        storage.get_all_collections() -> []". A freshly constructed
        Storage with zero collections created must return an empty
        list, not None and not raise."""
        storage = Storage()

        result = storage.get_all_collections()

        assert result == []
        assert result is not None

    # ---- Return type ----

    def test_get_all_collections_returns_a_genuine_list_instance(self):
        """Per the `List[Collection]` return type hint and the
        implementation `return list(self._collections.values())`, the
        result must be an actual `list` object - not a `dict_values`
        view or other iterable that merely behaves list-like."""
        storage = Storage()
        storage.create_collection(Collection(name="A"))

        result = storage.get_all_collections()

        assert isinstance(result, list)
        assert type(result) is list

    def test_get_all_collections_returned_list_supports_len_indexing_and_repeated_iteration(self):
        """Being a real `list` (not a view) means len(), integer
        indexing, and iterating more than once must all work without
        exhaustion - confirms the return type guarantee matters in
        practice, not just nominally."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)

        result = storage.get_all_collections()

        assert len(result) == 2
        assert result[0] is not None
        assert result[1] is not None
        first_pass_ids = {c.id for c in result}
        second_pass_ids = {c.id for c in result}
        assert first_pass_ids == second_pass_ids == {collection_a.id, collection_b.id}

    # ---- Order: documented as unspecified; observe current behavior without asserting it as contract ----

    def test_get_all_collections_current_implementation_preserves_insertion_order(self):
        """NOTE: get_all_collections' docstring explicitly says "in no
        particular order" - callers must NOT rely on ordering. This test
        does not assert order as a guaranteed contract; it documents
        what the CURRENT implementation happens to do (Python dicts
        preserve insertion order since 3.7, and dict.values() reflects
        that order, so list(self._collections.values()) currently comes
        back in creation order). If this test starts failing after an
        implementation change (e.g. switching the backing store), that
        is NOT a regression against the docstring's contract - the
        docstring never promised order - so this test should simply be
        removed/updated rather than treated as a bug report.
        """
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        collection_c = Collection(name="C")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_collection(collection_c)

        result = storage.get_all_collections()

        assert [c.id for c in result] == [collection_a.id, collection_b.id, collection_c.id]

    # ---- Snapshot semantics: list container vs. the Collection objects inside it ----

    def test_get_all_collections_returns_a_new_list_object_on_each_call(self):
        """Unlike get_collection (which returns the same stored object
        reference), get_all_collections' implementation wraps the dict
        values in `list(...)`, constructing a brand-new list object on
        every call. Two consecutive calls must therefore NOT be the same
        list instance, even though their contents are equal."""
        storage = Storage()
        storage.create_collection(Collection(name="A"))

        first_call = storage.get_all_collections()
        second_call = storage.get_all_collections()

        assert first_call is not second_call
        assert first_call == second_call

    def test_mutating_the_returned_list_container_does_not_corrupt_storage(self):
        """Because get_all_collections returns a fresh list each call
        (verified above), appending to or removing from that returned
        list must be safe - it must NOT alter Storage's internal
        _collections dict. This directly answers the snapshot-safety
        question raised by the get_collection object-identity finding
        (TestGetCollection): the LIST wrapper itself is an independent
        snapshot, even though (per the next test) the Collection objects
        inside it are not."""
        storage = Storage()
        collection_a = Collection(name="A")
        storage.create_collection(collection_a)

        returned_list = storage.get_all_collections()
        returned_list.append(Collection(name="Injected"))
        assert len(storage.get_all_collections()) == 1

        returned_list_2 = storage.get_all_collections()
        returned_list_2.pop()
        assert len(storage.get_all_collections()) == 1
        assert storage.get_collection(collection_a.id) is not None

    def test_collection_objects_inside_the_returned_list_are_the_same_references_as_get_collection(self):
        """The list CONTAINER returned by get_all_collections is new
        each call, but the individual Collection OBJECTS inside it are
        the very same references stored in _collections (list() only
        copies the container, not its elements) - identical to what
        get_collection returns for that id. This means the
        in-place-mutation corruption risk documented for get_collection
        in TestGetCollection.test_mutating_the_returned_collection_corrupts_stored_state
        equally applies to elements obtained via get_all_collections.
        Verified empirically here rather than assumed just because the
        Prompt-side pattern (TestGetAllPrompts) matches."""
        storage = Storage()
        collection_a = Collection(name="A")
        storage.create_collection(collection_a)

        [fetched_via_list] = storage.get_all_collections()
        fetched_via_get = storage.get_collection(collection_a.id)

        assert fetched_via_list is collection_a
        assert fetched_via_list is fetched_via_get

    def test_mutating_a_collection_object_inside_the_returned_list_corrupts_stored_state(self):
        """Direct consequence of the object-identity finding above:
        mutating a Collection element reached via
        get_all_collections()[i] mutates Storage's internal state for
        future reads, even though the list container itself was a safe
        copy. This mirrors, at the element level, the get_collection
        mutation finding in TestGetCollection, and confirms - rather
        than assumes - that the get_all_prompts finding for Prompt
        elements carries over to Collection elements too."""
        storage = Storage()
        collection_a = Collection(name="Original")
        storage.create_collection(collection_a)

        [fetched] = storage.get_all_collections()
        fetched.name = "Mutated via get_all_collections element"

        [fetched_again] = storage.get_all_collections()
        assert fetched_again.name == "Mutated via get_all_collections element"
        assert storage.get_collection(collection_a.id).name == "Mutated via get_all_collections element"

    # ---- Repeated calls without intervening writes ----

    def test_get_all_collections_repeated_calls_return_equal_contents_with_distinct_list_instances(self):
        """Calling get_all_collections() twice in a row with no writes
        in between must return equal contents (same collections, per
        docstring "Every collection currently in storage") while the
        list instances themselves may differ (per the snapshot
        semantics established above) - this is a read operation and
        must be side-effect free and repeatable."""
        storage = Storage()
        storage.create_collection(Collection(name="A"))
        storage.create_collection(Collection(name="B"))

        first_read = storage.get_all_collections()
        second_read = storage.get_all_collections()

        assert first_read == second_read
        assert [c.id for c in first_read] == [c.id for c in second_read]
        assert first_read is not second_read

    # ---- Consistency after mutation via delete_collection ----

    def test_get_all_collections_no_longer_includes_a_deleted_collection(self):
        """get_all_collections must reflect current state, not a cached
        snapshot: after delete_collection removes a collection,
        subsequent calls to get_all_collections must no longer include
        it - per the docstring "Every collection currently in storage"
        (deleted collections are no longer "currently in storage")."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        assert len(storage.get_all_collections()) == 2

        deleted = storage.delete_collection(collection_a.id)
        assert deleted is True

        remaining = storage.get_all_collections()
        assert len(remaining) == 1
        assert remaining[0].id == collection_b.id

    # ---- Cross-instance isolation ----

    def test_get_all_collections_never_includes_collections_created_on_a_different_instance(self):
        """Mirrors the pattern established for create_collection/
        get_collection in TestCrossInstanceIsolation-style tests and
        get_all_prompts in TestGetAllPrompts: collections created on one
        Storage instance must be invisible to get_all_collections on a
        different Storage instance, since each instance's _collections
        dict is per-instance state (Storage class docstring's
        Attributes section)."""
        storage_one = Storage()
        storage_two = Storage()
        storage_one.create_collection(Collection(name="Only in one"))
        storage_one.create_collection(Collection(name="Also only in one"))

        assert len(storage_one.get_all_collections()) == 2
        assert storage_two.get_all_collections() == []


class TestDeleteCollection:
    """Dedicated tests for Storage.delete_collection.

    Source of intended behavior: Storage.delete_collection's own
    docstring in app/storage.py ("Delete a collection by its id. ...
    Returns: bool: True if the collection was found and deleted, False
    if no collection with collection_id exists." with the doctest
    Example `storage.delete_collection("missing-id") -> False`) plus the
    Storage class docstring describing _collections as "Collections
    keyed by their id" and data as scoped to "the lifetime of the
    process". No written spec (specs/001-complete-promptlab-app/
    contracts/api-contract.md, data-model.md, docs/API_REFERENCE.md,
    docs/SYSTEM_MODEL.md) covers the Storage class directly - it is an
    internal implementation detail, not a public API contract - so
    intended behavior is inferred entirely from delete_collection's own
    docstring, cross-checked against the sibling create_collection/
    get_collection/get_all_collections docstrings for consistent
    vocabulary, and against delete_prompt's docstring/behavior as the
    direct structural analog on the Prompt side (TestDeletePrompt above).

    `test_get_collection_returns_none_after_the_collection_was_deleted`
    (TestGetCollection) and
    `test_get_all_collections_no_longer_includes_a_deleted_collection`
    (TestGetAllCollections) already exercise delete_collection
    incidentally, to confirm get_collection/get_all_collections aren't
    stale or resurrecting data after a delete - those are not duplicated
    here; this class is the dedicated, primary suite for
    delete_collection's own contract (its own return value, its own
    idempotency semantics, and its own side-effect scope - including the
    explicit boundary that delete_collection has no awareness of
    _prompts at all, unlike the API-layer route handler which cascades
    the unlink).
    """

    # ---- Return value on hit ----

    def test_delete_collection_hit_returns_true(self):
        """docstring: "Returns: bool: True if the collection was found
        and deleted". Deleting a collection_id that currently exists in
        storage must return True."""
        storage = Storage()
        collection = Collection(name="To Delete")
        storage.create_collection(collection)

        result = storage.delete_collection(collection.id)

        assert result is True

    # ---- Removal is real, not a soft-delete ----

    def test_delete_collection_hit_removes_collection_from_get_collection_and_get_all_collections(self):
        """After a successful delete, the collection must be genuinely
        gone - not just flagged - verified via BOTH
        get_collection(collection_id) is None AND the collection no
        longer appearing in get_all_collections(), per get_collection's
        "None if no collection with collection_id exists" and
        get_all_collections' "Every collection currently in storage"."""
        storage = Storage()
        collection = Collection(name="To Delete")
        storage.create_collection(collection)
        assert storage.get_collection(collection.id) is not None
        assert len(storage.get_all_collections()) == 1

        storage.delete_collection(collection.id)

        assert storage.get_collection(collection.id) is None
        all_collections = storage.get_all_collections()
        assert collection.id not in [c.id for c in all_collections]
        assert all_collections == []

    # ---- Return value on miss ----

    def test_delete_collection_miss_on_empty_storage_returns_false(self):
        """docstring Example: `storage.delete_collection("missing-id")
        -> False`. On a freshly constructed Storage with zero
        collections, any delete attempt must return False, not raise."""
        storage = Storage()

        result = storage.delete_collection("missing-id")

        assert result is False

    def test_delete_collection_miss_on_non_empty_storage_returns_false(self):
        """docstring: "False if no collection with collection_id
        exists". When storage is non-empty but the requested id matches
        none of the stored collections, the result must still be False,
        per the same contract that applies on empty storage."""
        storage = Storage()
        storage.create_collection(Collection(name="A"))
        storage.create_collection(Collection(name="B"))

        result = storage.delete_collection("id-that-was-never-created")

        assert result is False

    # ---- No side effects on miss ----

    def test_delete_collection_miss_does_not_affect_other_collections_field_values(self):
        """A failed delete attempt (id not found) must not affect any
        OTHER collections already in storage - not just "still present"
        but with field values fully unchanged, since delete_collection's
        docstring only promises removal of a MATCHING collection_id,
        implying no effect at all when no match exists."""
        storage = Storage()
        collection_a = Collection(
            name="A",
            description="Description A",
        )
        collection_b = Collection(name="B")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)

        result = storage.delete_collection("never-existed")

        assert result is False
        all_collections = storage.get_all_collections()
        assert len(all_collections) == 2

        fetched_a = storage.get_collection(collection_a.id)
        assert fetched_a is not None
        assert fetched_a.name == "A"
        assert fetched_a.description == "Description A"
        assert fetched_a.created_at == collection_a.created_at

        fetched_b = storage.get_collection(collection_b.id)
        assert fetched_b is not None
        assert fetched_b.name == "B"

    # ---- Double-delete idempotency ----

    def test_delete_collection_called_twice_second_call_returns_false_not_true(self):
        """The single most important idempotency semantic for this
        method: deleting the same collection_id twice must NOT return
        True both times. The first call finds the collection (it "was
        found and deleted" per the docstring) and returns True; by the
        second call the collection no longer exists, so per the same
        docstring sentence's other branch ("False if no collection with
        collection_id exists") the second call must return False.
        delete_collection must not raise on the second call either - it
        is a plain `if collection_id in self._collections` check, which
        is always safe to repeat. Same semantic as delete_prompt's
        already-confirmed double-delete idempotency
        (test_delete_prompt_called_twice_second_call_returns_false_not_true)."""
        storage = Storage()
        collection = Collection(name="To Delete")
        storage.create_collection(collection)

        first_result = storage.delete_collection(collection.id)
        second_result = storage.delete_collection(collection.id)

        assert first_result is True
        assert second_result is False

    def test_delete_collection_called_twice_collection_remains_gone_after_both_calls(self):
        """Reinforces the double-delete finding above from the read
        side: after both delete calls, the collection must still be
        absent from both get_collection and get_all_collections - the
        second (no-op) call must not somehow resurrect it or leave
        storage in an inconsistent state."""
        storage = Storage()
        collection = Collection(name="To Delete")
        storage.create_collection(collection)

        storage.delete_collection(collection.id)
        storage.delete_collection(collection.id)

        assert storage.get_collection(collection.id) is None
        assert storage.get_all_collections() == []

    # ---- Persistence within a session: deleting one leaves others intact ----

    def test_delete_collection_from_the_middle_of_several_leaves_the_others_intact(self):
        """Create several collections, delete one specific one from the
        MIDDLE of the set (not just when there's only one), confirm the
        OTHERS are all still present and correct via
        get_all_collections()/get_collection() - deleting one must not
        disturb unrelated entries, per the Storage class docstring
        describing _collections as a dict keyed by id (each entry
        independent)."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        collection_c = Collection(name="C")
        collection_d = Collection(name="D")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_collection(collection_c)
        storage.create_collection(collection_d)

        result = storage.delete_collection(collection_b.id)

        assert result is True
        remaining_ids = {c.id for c in storage.get_all_collections()}
        assert remaining_ids == {collection_a.id, collection_c.id, collection_d.id}
        assert collection_b.id not in remaining_ids
        assert storage.get_collection(collection_b.id) is None

        fetched_a = storage.get_collection(collection_a.id)
        fetched_c = storage.get_collection(collection_c.id)
        fetched_d = storage.get_collection(collection_d.id)
        assert fetched_a.name == "A"
        assert fetched_c.name == "C"
        assert fetched_d.name == "D"

    def test_delete_collection_first_then_last_of_several_leaves_the_middle_intact(self):
        """Order-independence check complementing the middle-delete test
        above: deleting the FIRST-created and then the LAST-created
        collection out of several must leave the ones created in between
        fully intact, confirming delete_collection's effect is scoped
        strictly to the requested id regardless of insertion position."""
        storage = Storage()
        collection_a = Collection(name="A")
        collection_b = Collection(name="B")
        collection_c = Collection(name="C")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_collection(collection_c)

        assert storage.delete_collection(collection_a.id) is True
        assert storage.delete_collection(collection_c.id) is True

        remaining = storage.get_all_collections()
        assert len(remaining) == 1
        assert remaining[0].id == collection_b.id
        assert remaining[0].name == "B"
        assert storage.get_collection(collection_a.id) is None
        assert storage.get_collection(collection_c.id) is None

    # ---- Cross-instance isolation ----

    def test_delete_collection_on_one_instance_does_not_affect_a_different_instance(self):
        """Mirrors the pattern established for create_collection/
        get_collection/get_all_collections in the corresponding test
        classes and for delete_prompt in TestDeletePrompt:
        delete_collection on one Storage instance must never affect a
        different Storage instance's data, since each instance's
        _collections dict is per-instance state (Storage class
        docstring's Attributes section). To make the isolation check
        meaningful even when ids could otherwise coincide, two
        collections are explicitly constructed with the SAME id across
        two separate Storage instances."""
        storage_one = Storage()
        storage_two = Storage()
        shared_id = "same-id-on-both-instances"
        storage_one.create_collection(Collection(id=shared_id, name="On instance one"))
        storage_two.create_collection(Collection(id=shared_id, name="On instance two"))

        result = storage_one.delete_collection(shared_id)

        assert result is True
        assert storage_one.get_collection(shared_id) is None
        assert storage_one.get_all_collections() == []

        # Instance two's same-id collection must be entirely untouched:
        fetched_two = storage_two.get_collection(shared_id)
        assert fetched_two is not None
        assert fetched_two.name == "On instance two"
        assert len(storage_two.get_all_collections()) == 1

    def test_delete_collection_miss_on_one_instance_does_not_affect_a_different_instance(self):
        """Complements the hit-case isolation test above: a
        delete_collection call that MISSES (id not found) on one Storage
        instance must also have zero effect on a different Storage
        instance, even when that other instance happens to hold a
        collection under the same id being searched for on the first
        instance."""
        storage_one = Storage()
        storage_two = Storage()
        shared_id = "id-only-on-instance-two"
        storage_two.create_collection(Collection(id=shared_id, name="Only on two"))

        result = storage_one.delete_collection(shared_id)

        assert result is False
        assert storage_one.get_all_collections() == []
        fetched_two = storage_two.get_collection(shared_id)
        assert fetched_two is not None
        assert fetched_two.name == "Only on two"

    # ---- Edge cases ----

    def test_delete_collection_with_empty_string_id_on_empty_storage_returns_false(self):
        """An empty-string id is not a valid id any create_collection
        call would produce (generate_id always yields a non-empty uuid4
        string), so deleting it on empty storage must safely return
        False rather than raising - `"" in {}` is always False, and the
        docstring promises False for "no collection with collection_id
        exists", which an empty string trivially satisfies."""
        storage = Storage()

        result = storage.delete_collection("")

        assert result is False

    def test_delete_collection_with_empty_string_id_on_non_empty_storage_returns_false_and_no_side_effects(self):
        """Same empty-string-id edge case as above, but on non-empty
        storage: must return False and must not delete/affect any of
        the real collections present (an empty string must never be
        treated as a wildcard or accidentally match a real id)."""
        storage = Storage()
        collection = Collection(name="A")
        storage.create_collection(collection)

        result = storage.delete_collection("")

        assert result is False
        assert storage.get_collection(collection.id) is not None
        assert len(storage.get_all_collections()) == 1

    def test_delete_collection_then_recreate_with_the_same_explicit_id_succeeds_cleanly(self):
        """Empirical check of a non-obvious case the docstring does not
        explicitly address: after deleting a collection, calling
        create_collection again with a NEW Collection object that
        explicitly reuses the same .id must succeed cleanly, with no
        leftover "tombstone" state blocking or corrupting the reused id
        - delete_collection's implementation is a plain `del
        self._collections[collection_id]`, which leaves no trace behind
        in the dict once the key is removed. Same finding as
        delete_prompt's already-confirmed
        test_delete_prompt_then_recreate_with_the_same_explicit_id_succeeds_cleanly."""
        storage = Storage()
        original = Collection(id="reusable-id", name="Original")
        storage.create_collection(original)
        assert storage.delete_collection("reusable-id") is True
        assert storage.get_collection("reusable-id") is None

        recreated = Collection(id="reusable-id", name="Recreated")
        result = storage.create_collection(recreated)

        assert result is recreated
        fetched = storage.get_collection("reusable-id")
        assert fetched is not None
        assert fetched.name == "Recreated"
        assert fetched is recreated
        assert len(storage.get_all_collections()) == 1

    def test_delete_collection_return_type_is_a_real_bool_not_a_truthy_object(self):
        """docstring type hint: `-> bool`. Both the hit and miss return
        values must be actual bool instances (True/False), not merely
        truthy/falsy objects (e.g. not None on miss, not the deleted
        Collection object on hit)."""
        storage = Storage()
        collection = Collection(name="A")
        storage.create_collection(collection)

        hit_result = storage.delete_collection(collection.id)
        miss_result = storage.delete_collection("does-not-exist")

        assert isinstance(hit_result, bool)
        assert hit_result is True
        assert isinstance(miss_result, bool)
        assert miss_result is False

    # ---- Layering boundary: no prompt-unlinking cascade at the storage layer ----

    def test_delete_collection_does_not_touch_or_unlink_prompts_referencing_it(self):
        """Explicit documentation-via-test of a deliberate scope
        boundary: delete_collection's own docstring makes no promise
        whatsoever about _prompts - it only describes removing an entry
        from _collections ("Delete a collection by its id" /
        `del self._collections[collection_id]`). The prompt-unlinking
        cascade (setting a prompt's collection_id to None when its
        parent collection is deleted) is implemented entirely in the
        HTTP route handler in app/api.py, not in Storage. Calling
        storage.delete_collection directly (bypassing the API layer)
        must therefore leave any prompt that references the deleted
        collection_id completely unchanged / orphaned at this layer -
        this is not a bug, it documents where the responsibility
        legitimately lives."""
        storage = Storage()
        collection = Collection(name="Parent Collection")
        storage.create_collection(collection)
        prompt = Prompt(
            title="Child Prompt",
            content="References the collection above",
            collection_id=collection.id,
        )
        storage.create_prompt(prompt)

        result = storage.delete_collection(collection.id)

        assert result is True
        assert storage.get_collection(collection.id) is None

        # The prompt itself must still exist, untouched, still pointing
        # at the now-deleted collection_id:
        fetched_prompt = storage.get_prompt(prompt.id)
        assert fetched_prompt is not None
        assert fetched_prompt.collection_id == collection.id
        assert fetched_prompt.title == "Child Prompt"
        all_prompts = storage.get_all_prompts()
        assert len(all_prompts) == 1
        assert all_prompts[0].collection_id == collection.id


class TestGetPromptsByCollection:
    """Dedicated tests for Storage.get_prompts_by_collection.

    Source of intended behavior: Storage.get_prompts_by_collection's own
    docstring in app/storage.py ("Retrieve all prompts belonging to a
    given collection. ... Returns: List[Prompt]: The prompts whose
    collection_id matches collection_id, in no particular order." with
    the doctest Example `storage.get_prompts_by_collection("missing-id")
    -> []`), plus Prompt's field contract in app/models.py
    (`collection_id: Optional[str] = None` on PromptBase - confirmed
    directly rather than assumed - meaning a prompt with no collection
    assigned has collection_id=None, which can never equal a real,
    non-None collection_id string via `==`). No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers
    the Storage class directly - it is an internal implementation
    detail, not a public API contract - so intended behavior is inferred
    entirely from get_prompts_by_collection's own docstring, cross-checked
    against Prompt's field contract and the sibling get_all_prompts/
    get_collection/delete_collection docstrings for consistent
    vocabulary and layering conventions (in particular,
    TestDeleteCollection's
    test_delete_collection_does_not_touch_or_unlink_prompts_referencing_it,
    which already established that delete_collection has zero awareness
    of _prompts - this class independently confirms the mirror-image
    fact from the read side: get_prompts_by_collection has zero
    awareness of _collections).

    Unlike get_prompt/get_collection (id-keyed single-item lookups),
    get_prompts_by_collection is a many-to-one filter over _prompts with
    no existing dedicated coverage anywhere in this file (confirmed via
    a project-wide grep prior to writing this class - the only prior
    mention was this file's own module docstring, in a TODO-style note
    listing methods awaiting dedicated coverage, now updated above).
    This class is therefore built from the ground up rather than
    factored out of an existing class, following the same
    docstring-citing, one-class-per-method convention established
    throughout this file.
    """

    # ---- Basic filter: hit case ----

    def test_get_prompts_by_collection_returns_only_prompts_in_the_requested_collection(self):
        """docstring: "The prompts whose collection_id matches
        collection_id". With prompts spread across two different
        collections, querying one collection_id must return exactly the
        prompts belonging to it - none from the other collection."""
        storage = Storage()
        collection_a_id = "collection-a"
        collection_b_id = "collection-b"
        prompt_a1 = Prompt(title="A1", content="Content A1", collection_id=collection_a_id)
        prompt_a2 = Prompt(title="A2", content="Content A2", collection_id=collection_a_id)
        prompt_b1 = Prompt(title="B1", content="Content B1", collection_id=collection_b_id)
        storage.create_prompt(prompt_a1)
        storage.create_prompt(prompt_a2)
        storage.create_prompt(prompt_b1)

        result = storage.get_prompts_by_collection(collection_a_id)

        result_ids = {p.id for p in result}
        assert result_ids == {prompt_a1.id, prompt_a2.id}
        assert prompt_b1.id not in result_ids

    # ---- Empty case: no prompts at all ----

    def test_get_prompts_by_collection_on_fresh_storage_returns_empty_list(self):
        """On a freshly constructed Storage with zero prompts created,
        querying any collection_id must return an empty list, not None
        and not raise - mirrors the docstring Example's "missing-id ->
        []" on the more extreme case of zero prompts existing at all."""
        storage = Storage()

        result = storage.get_prompts_by_collection("any-collection-id")

        assert result == []
        assert result is not None

    # ---- Empty case: prompts exist but none match ----

    def test_get_prompts_by_collection_returns_empty_list_when_no_prompt_matches(self):
        """docstring Example: `storage.get_prompts_by_collection(
        "missing-id") -> []`. When storage holds prompts, but none of
        them have the queried collection_id, the result must still be an
        empty list, not None and not raise."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A", collection_id="real-collection"))
        storage.create_prompt(Prompt(title="B", content="Content B"))

        result = storage.get_prompts_by_collection("missing-id")

        assert result == []

    # ---- Prompts with collection_id=None are excluded from real-id queries ----

    def test_get_prompts_by_collection_excludes_prompts_with_no_collection_assigned(self):
        """Per Prompt's field contract (PromptBase.collection_id:
        Optional[str] = None), a prompt with no collection assigned has
        collection_id=None. None can never equal a real, non-None
        collection_id string via `==`, so such a prompt must never be
        included in the results for any specific, real collection_id
        query."""
        storage = Storage()
        real_collection_id = "real-collection"
        unassigned_prompt = Prompt(title="Unassigned", content="No collection")
        assigned_prompt = Prompt(title="Assigned", content="Has collection", collection_id=real_collection_id)
        storage.create_prompt(unassigned_prompt)
        storage.create_prompt(assigned_prompt)

        result = storage.get_prompts_by_collection(real_collection_id)

        result_ids = {p.id for p in result}
        assert result_ids == {assigned_prompt.id}
        assert unassigned_prompt.id not in result_ids

    # ---- Collection-existence-agnostic: pure filter over _prompts, no dependency on _collections ----

    def test_get_prompts_by_collection_returns_matches_even_when_collection_was_never_created(self):
        """Empirical confirmation of a deliberate layering boundary: the
        implementation `[p for p in self._prompts.values() if
        p.collection_id == collection_id]` never touches
        self._collections at all - get_prompts_by_collection's docstring
        makes no promise about collection existence either. A prompt
        whose collection_id references a collection_id string that was
        NEVER passed to create_collection must still be returned - this
        is a pure field filter over _prompts, completely decoupled from
        _collections."""
        storage = Storage()
        never_created_collection_id = "never-created-collection"
        prompt = Prompt(
            title="Orphan-by-construction",
            content="References a collection that never existed",
            collection_id=never_created_collection_id,
        )
        storage.create_prompt(prompt)
        assert storage.get_collection(never_created_collection_id) is None

        result = storage.get_prompts_by_collection(never_created_collection_id)

        assert len(result) == 1
        assert result[0].id == prompt.id

    def test_get_prompts_by_collection_returns_matches_after_the_referenced_collection_was_deleted(self):
        """Direct mechanism this test confirms: this is exactly what
        app/api.py's delete_collection route relies on to find prompts
        to unlink after removing the Collection row. A collection is
        created, a prompt references it, the collection is then deleted
        via delete_collection (already confirmed in
        TestDeleteCollection.test_delete_collection_does_not_touch_or_unlink_prompts_referencing_it
        to leave the prompt's collection_id untouched) - querying
        get_prompts_by_collection for that now-deleted collection_id
        must still return the orphaned prompt, proving the storage-layer
        primitive api.py depends on behaves correctly in isolation."""
        storage = Storage()
        collection = Collection(name="Will be deleted")
        storage.create_collection(collection)
        prompt = Prompt(
            title="Orphan-after-delete",
            content="References the soon-to-be-deleted collection",
            collection_id=collection.id,
        )
        storage.create_prompt(prompt)

        assert storage.delete_collection(collection.id) is True
        assert storage.get_collection(collection.id) is None

        result = storage.get_prompts_by_collection(collection.id)

        assert len(result) == 1
        assert result[0].id == prompt.id
        assert result[0].collection_id == collection.id

    # ---- Multiple prompts in the same collection ----

    def test_get_prompts_by_collection_returns_all_matching_prompts_not_just_one(self):
        """With three or more prompts sharing the same collection_id, all
        of them must be returned - not just the first/last one created -
        per the docstring's plural framing ("The prompts whose
        collection_id matches collection_id")."""
        storage = Storage()
        shared_collection_id = "shared-collection"
        prompt_1 = Prompt(title="1", content="Content 1", collection_id=shared_collection_id)
        prompt_2 = Prompt(title="2", content="Content 2", collection_id=shared_collection_id)
        prompt_3 = Prompt(title="3", content="Content 3", collection_id=shared_collection_id)
        prompt_4 = Prompt(title="4", content="Content 4", collection_id=shared_collection_id)
        storage.create_prompt(prompt_1)
        storage.create_prompt(prompt_2)
        storage.create_prompt(prompt_3)
        storage.create_prompt(prompt_4)

        result = storage.get_prompts_by_collection(shared_collection_id)

        result_ids = {p.id for p in result}
        assert len(result) == 4
        assert result_ids == {prompt_1.id, prompt_2.id, prompt_3.id, prompt_4.id}

    # ---- Prompts in different collections don't leak into each other's results ----

    def test_get_prompts_by_collection_does_not_leak_prompts_between_collections(self):
        """Querying collection A's prompts must never include collection
        B's prompts and vice versa - each collection_id's results are
        strictly scoped to prompts whose own collection_id field matches
        exactly."""
        storage = Storage()
        collection_a_id = "collection-a"
        collection_b_id = "collection-b"
        prompt_a1 = Prompt(title="A1", content="Content A1", collection_id=collection_a_id)
        prompt_a2 = Prompt(title="A2", content="Content A2", collection_id=collection_a_id)
        prompt_b1 = Prompt(title="B1", content="Content B1", collection_id=collection_b_id)
        prompt_b2 = Prompt(title="B2", content="Content B2", collection_id=collection_b_id)
        storage.create_prompt(prompt_a1)
        storage.create_prompt(prompt_a2)
        storage.create_prompt(prompt_b1)
        storage.create_prompt(prompt_b2)

        result_a = storage.get_prompts_by_collection(collection_a_id)
        result_b = storage.get_prompts_by_collection(collection_b_id)

        result_a_ids = {p.id for p in result_a}
        result_b_ids = {p.id for p in result_b}
        assert result_a_ids == {prompt_a1.id, prompt_a2.id}
        assert result_b_ids == {prompt_b1.id, prompt_b2.id}
        assert result_a_ids.isdisjoint(result_b_ids)

    # ---- Return type and snapshot semantics ----

    def test_get_prompts_by_collection_returns_a_genuine_list_instance(self):
        """Per the `List[Prompt]` return type hint and the implementation
        `[p for p in self._prompts.values() if ...]` (a list
        comprehension - a genuine list, distinct from get_all_prompts'
        `list(dict.values())` wrapping but producing the same concrete
        type), the result must be an actual `list` object."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A", collection_id="coll-1"))

        result = storage.get_prompts_by_collection("coll-1")

        assert isinstance(result, list)
        assert type(result) is list

    def test_get_prompts_by_collection_returns_a_new_list_object_on_each_call(self):
        """Mirrors the snapshot-container finding already confirmed for
        get_all_prompts/get_all_collections (TestGetAllPrompts/
        TestGetAllCollections): since the implementation is a list
        comprehension, it constructs a brand-new list object on every
        call. Two consecutive calls must therefore NOT be the same list
        instance, even though their contents are equal. Verified
        empirically here rather than assumed to carry over just because
        the pattern matches the other two list-returning methods."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A", collection_id="coll-1"))

        first_call = storage.get_prompts_by_collection("coll-1")
        second_call = storage.get_prompts_by_collection("coll-1")

        assert first_call is not second_call
        assert first_call == second_call

    def test_mutating_the_returned_list_container_does_not_corrupt_storage(self):
        """Because get_prompts_by_collection returns a fresh list each
        call (verified above), appending to or removing from that
        returned list must be safe - it must NOT alter Storage's
        internal _prompts dict, mirroring the container-safety finding
        already confirmed for get_all_prompts."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A", collection_id="coll-1")
        storage.create_prompt(prompt_a)

        returned_list = storage.get_prompts_by_collection("coll-1")
        returned_list.append(Prompt(title="Injected", content="Should not stick", collection_id="coll-1"))
        assert len(storage.get_prompts_by_collection("coll-1")) == 1

        returned_list_2 = storage.get_prompts_by_collection("coll-1")
        returned_list_2.pop()
        assert len(storage.get_prompts_by_collection("coll-1")) == 1
        assert storage.get_prompt(prompt_a.id) is not None

    def test_prompt_objects_inside_the_returned_list_are_the_same_references_as_get_prompt(self):
        """The list CONTAINER returned by get_prompts_by_collection is
        new each call, but the individual Prompt OBJECTS inside it are
        the very same references stored in _prompts (the comprehension
        iterates and filters self._prompts.values() without copying
        elements) - identical to what get_prompt/get_all_prompts return
        for that id. Verified empirically here rather than assumed to
        carry over just because the pattern matches the other two
        list-returning methods."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A", collection_id="coll-1")
        storage.create_prompt(prompt_a)

        [fetched_via_filter] = storage.get_prompts_by_collection("coll-1")
        fetched_via_get = storage.get_prompt(prompt_a.id)

        assert fetched_via_filter is prompt_a
        assert fetched_via_filter is fetched_via_get

    def test_mutating_a_prompt_object_inside_the_returned_list_corrupts_stored_state(self):
        """Direct consequence of the object-identity finding above:
        mutating a Prompt element reached via
        get_prompts_by_collection(...)[i] mutates Storage's internal
        state for future reads, even though the list container itself
        was a safe copy - the same mutation-risk pattern already
        established for get_prompt/get_all_prompts, now confirmed to
        apply here too."""
        storage = Storage()
        prompt_a = Prompt(title="Original", content="Original content", collection_id="coll-1")
        storage.create_prompt(prompt_a)

        [fetched] = storage.get_prompts_by_collection("coll-1")
        fetched.title = "Mutated via get_prompts_by_collection element"

        [fetched_again] = storage.get_prompts_by_collection("coll-1")
        assert fetched_again.title == "Mutated via get_prompts_by_collection element"
        assert storage.get_prompt(prompt_a.id).title == "Mutated via get_prompts_by_collection element"

    # ---- Persistence within a session ----

    def test_get_prompts_by_collection_repeated_calls_return_equal_contents_with_distinct_list_instances(self):
        """Calling get_prompts_by_collection(...) twice in a row with no
        writes in between must return equal contents (same prompts, per
        docstring "The prompts whose collection_id matches
        collection_id") while the list instances themselves may differ
        (per the snapshot semantics established above) - this is a read
        operation and must be side-effect free and repeatable."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A", collection_id="coll-1"))
        storage.create_prompt(Prompt(title="B", content="Content B", collection_id="coll-1"))

        first_read = storage.get_prompts_by_collection("coll-1")
        second_read = storage.get_prompts_by_collection("coll-1")

        assert first_read == second_read
        assert {p.id for p in first_read} == {p.id for p in second_read}
        assert first_read is not second_read

    def test_get_prompts_by_collection_reflects_a_newly_added_matching_prompt(self):
        """get_prompts_by_collection must not cache or return stale
        data: after a new prompt is created with a matching
        collection_id, a subsequent call must include it - per the
        docstring's "in storage"-scoped framing (mirroring
        get_all_prompts' "currently in storage" language) implying
        results always reflect current state."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A", collection_id="coll-1")
        storage.create_prompt(prompt_a)
        assert len(storage.get_prompts_by_collection("coll-1")) == 1

        prompt_b = Prompt(title="B", content="Content B", collection_id="coll-1")
        storage.create_prompt(prompt_b)

        result = storage.get_prompts_by_collection("coll-1")
        result_ids = {p.id for p in result}
        assert len(result) == 2
        assert result_ids == {prompt_a.id, prompt_b.id}

    def test_get_prompts_by_collection_no_longer_includes_a_deleted_matching_prompt(self):
        """get_prompts_by_collection must reflect current state, not a
        cached snapshot: after delete_prompt removes a matching prompt,
        subsequent calls must no longer include it - mirroring
        get_all_prompts' identical staleness guarantee
        (test_get_all_prompts_no_longer_includes_a_deleted_prompt)."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A", collection_id="coll-1")
        prompt_b = Prompt(title="B", content="Content B", collection_id="coll-1")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        assert len(storage.get_prompts_by_collection("coll-1")) == 2

        deleted = storage.delete_prompt(prompt_a.id)
        assert deleted is True

        remaining = storage.get_prompts_by_collection("coll-1")
        assert len(remaining) == 1
        assert remaining[0].id == prompt_b.id

    def test_get_prompts_by_collection_reflects_a_prompt_moved_out_via_update_prompt(self):
        """A prompt that is updated (via update_prompt) so its
        collection_id no longer matches the queried collection_id must
        stop appearing in that collection's results on the next call -
        per the docstring's "whose collection_id matches collection_id"
        framing being a live, current-state check, not a
        point-in-time snapshot."""
        storage = Storage()
        prompt = Prompt(title="Movable", content="Will change collections", collection_id="coll-1")
        storage.create_prompt(prompt)
        assert len(storage.get_prompts_by_collection("coll-1")) == 1

        moved = Prompt(
            id=prompt.id,
            title="Movable",
            content="Will change collections",
            collection_id="coll-2",
        )
        storage.update_prompt(prompt.id, moved)

        assert storage.get_prompts_by_collection("coll-1") == []
        result_coll_2 = storage.get_prompts_by_collection("coll-2")
        assert len(result_coll_2) == 1
        assert result_coll_2[0].id == prompt.id

    # ---- Edge cases ----

    def test_get_prompts_by_collection_with_empty_string_id_returns_empty_list_when_no_prompt_has_it(self):
        """An empty-string collection_id does not normally arise via the
        API layer (PromptCreate/PromptPatch's collection_id is
        Optional[str] = None, not empty-string, when unset), but the
        storage method itself performs a plain `==` comparison with no
        special-casing of the empty string - querying it on a store with
        no prompt whose collection_id is genuinely "" must safely return
        an empty list, not raise."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A", collection_id="real-collection"))
        storage.create_prompt(Prompt(title="B", content="Content B"))

        result = storage.get_prompts_by_collection("")

        assert result == []

    def test_get_prompts_by_collection_with_empty_string_id_matches_a_prompt_whose_collection_id_is_genuinely_empty_string(self):
        """Direct confirmation that get_prompts_by_collection performs
        no special-casing of the empty string at all: it is a plain `==`
        filter, so a Prompt object explicitly constructed with
        collection_id="" (bypassing the API layer, which would not
        normally produce this) must be matched by a `""` query, just
        like any other exact string match would be."""
        storage = Storage()
        empty_id_prompt = Prompt(title="Empty-id", content="Explicit empty string collection_id", collection_id="")
        storage.create_prompt(empty_id_prompt)
        storage.create_prompt(Prompt(title="Real", content="Real collection", collection_id="real-collection"))

        result = storage.get_prompts_by_collection("")

        assert len(result) == 1
        assert result[0].id == empty_id_prompt.id

    def test_get_prompts_by_collection_id_matching_is_case_sensitive(self):
        """collection_id is a plain string field and Python's `==` on
        strings is case-sensitive, so a differently-cased query must not
        match a stored prompt's collection_id - exact-match semantics,
        mirroring the case-sensitivity rigor already applied to
        get_prompt/get_collection (TestGetPrompt.
        test_get_prompt_id_lookup_is_case_sensitive /
        TestGetCollection.test_get_collection_id_lookup_is_case_sensitive)."""
        storage = Storage()
        prompt = Prompt(title="Case", content="Case content", collection_id="MixedCase-Collection")
        storage.create_prompt(prompt)

        assert len(storage.get_prompts_by_collection("MixedCase-Collection")) == 1
        assert storage.get_prompts_by_collection("mixedcase-collection") == []
        assert storage.get_prompts_by_collection("MIXEDCASE-COLLECTION") == []

    def test_get_prompts_by_collection_with_id_off_by_one_character_does_not_match(self):
        """get_prompts_by_collection must perform exact-match filtering,
        not prefix/fuzzy matching - a collection_id that differs from a
        stored prompt's collection_id by a single character must not be
        treated as a match, mirroring
        TestGetPrompt.test_get_prompt_with_id_off_by_one_character_does_not_match."""
        storage = Storage()
        prompt = Prompt(title="Exact", content="Exact content", collection_id="collection-abc")
        storage.create_prompt(prompt)

        result = storage.get_prompts_by_collection("collection-abcX")

        assert result == []

    def test_get_prompts_by_collection_called_with_none_matches_unassigned_prompts(self):
        """Empirical, undocumented-but-observable edge case: the
        `collection_id` parameter is type-hinted as `str` (not
        `Optional[str]`), and get_prompts_by_collection's docstring Args
        section describes it as "the unique identifier of the collection"
        - implying callers are expected to pass a real collection id
        string, not None. Nonetheless, Python does not enforce type
        hints at runtime, and the implementation's `==` comparison
        treats None like any other value: calling
        get_prompts_by_collection(None) matches every prompt whose OWN
        collection_id is also None (i.e. every prompt with no collection
        assigned). This is flagged as an inferred/uncertain behavior
        (calling with None violates the documented `str` contract) rather
        than a claimed part of the method's intended contract - included
        here only to pin down what actually happens if a caller violates
        the type hint, not to endorse doing so."""
        storage = Storage()
        unassigned_a = Prompt(title="Unassigned A", content="Content A")
        unassigned_b = Prompt(title="Unassigned B", content="Content B")
        assigned = Prompt(title="Assigned", content="Content C", collection_id="real-collection")
        storage.create_prompt(unassigned_a)
        storage.create_prompt(unassigned_b)
        storage.create_prompt(assigned)

        result = storage.get_prompts_by_collection(None)

        result_ids = {p.id for p in result}
        assert result_ids == {unassigned_a.id, unassigned_b.id}
        assert assigned.id not in result_ids

    # ---- Cross-instance isolation ----

    def test_get_prompts_by_collection_never_sees_prompts_created_on_a_different_instance(self):
        """Mirrors the pattern established for get_prompt/get_all_prompts
        in TestGetPrompt/TestGetAllPrompts: prompts created on one
        Storage instance must be invisible to get_prompts_by_collection
        on a different Storage instance, since each instance's _prompts
        dict is per-instance state (Storage class docstring's Attributes
        section), even when both instances use the exact same
        collection_id string value."""
        storage_one = Storage()
        storage_two = Storage()
        shared_collection_id = "same-collection-id-on-both-instances"
        storage_one.create_prompt(
            Prompt(title="Only on one", content="Content", collection_id=shared_collection_id)
        )

        result_one = storage_one.get_prompts_by_collection(shared_collection_id)
        result_two = storage_two.get_prompts_by_collection(shared_collection_id)

        assert len(result_one) == 1
        assert result_two == []


class TestClear:
    """Dedicated tests for Storage.clear.

    Source of intended behavior: Storage.clear's own docstring in
    app/storage.py ("Remove all stored prompts and collections. Resets
    the in-memory storage to an empty state, discarding all prompts and
    collections that have been created. Returns: None." with the
    doctest Example showing a created prompt becoming unreachable via
    get_all_prompts() after clear()) plus the Storage class docstring
    describing _prompts/_collections as per-instance dicts and data as
    scoped to "the lifetime of the process". No written spec
    (specs/001-complete-promptlab-app/contracts/api-contract.md,
    data-model.md, docs/API_REFERENCE.md, docs/SYSTEM_MODEL.md) covers
    the Storage class directly - it is an internal implementation
    detail, not a public API contract - so intended behavior is
    inferred entirely from clear's own docstring, cross-checked against
    the sibling create/get/delete docstrings for consistent vocabulary.

    clear's docstring explicitly names BOTH nouns ("all stored prompts
    AND collections") as being removed by a single call, so this class
    pays particular attention to verifying both stores are emptied
    together, not just one at a time - unlike the other Storage
    methods, which each operate on only one of the two stores.

    `Storage.clear` also plays a special, critical role in this test
    suite's own infrastructure: tests/conftest.py's autouse
    `clear_storage` fixture calls `storage.clear()` (on the
    module-level singleton `storage` defined at the bottom of
    app/storage.py) before AND after every single test in the entire
    backend suite, to guarantee test isolation. Despite that central
    role, `clear` had no dedicated test class prior to this one - it
    was only ever exercised incidentally via that fixture. This class
    closes that gap, including one test that exercises the exact same
    module-level singleton object the fixture manipulates.
    """

    # ---- Basic clear: prompts only ----

    def test_clear_removes_all_prompts_when_only_prompts_are_present(self):
        """docstring: "Remove all stored prompts and collections." With
        several prompts and no collections present, clear() must empty
        _prompts entirely - get_all_prompts() must return [] and
        get_prompt() for a previously-existing id must return None."""
        storage = Storage()
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")
        prompt_c = Prompt(title="C", content="Content C")
        storage.create_prompt(prompt_a)
        storage.create_prompt(prompt_b)
        storage.create_prompt(prompt_c)
        assert len(storage.get_all_prompts()) == 3

        storage.clear()

        assert storage.get_all_prompts() == []
        assert storage.get_prompt(prompt_a.id) is None
        assert storage.get_prompt(prompt_b.id) is None
        assert storage.get_prompt(prompt_c.id) is None

    # ---- Basic clear: collections only ----

    def test_clear_removes_all_collections_when_only_collections_are_present(self):
        """docstring: "Remove all stored prompts and collections." With
        several collections and no prompts present, clear() must empty
        _collections entirely - get_all_collections() must return []
        and get_collection() for a previously-existing id must return
        None."""
        storage = Storage()
        collection_a = Collection(name="Collection A")
        collection_b = Collection(name="Collection B")
        collection_c = Collection(name="Collection C")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_collection(collection_c)
        assert len(storage.get_all_collections()) == 3

        storage.clear()

        assert storage.get_all_collections() == []
        assert storage.get_collection(collection_a.id) is None
        assert storage.get_collection(collection_b.id) is None
        assert storage.get_collection(collection_c.id) is None

    # ---- Clear removes BOTH stores together in one call ----

    def test_clear_removes_both_prompts_and_collections_in_a_single_call(self):
        """docstring names BOTH nouns in one sentence: "Remove all
        stored prompts AND collections" - a single clear() call must
        empty BOTH stores together, not just whichever one a caller
        happens to check first. This is the central, defining behavior
        distinguishing clear() from every other Storage method (each of
        which only ever touches one of the two stores)."""
        storage = Storage()
        prompt = Prompt(title="A Prompt", content="Some content")
        collection = Collection(name="A Collection")
        storage.create_prompt(prompt)
        storage.create_collection(collection)
        assert len(storage.get_all_prompts()) == 1
        assert len(storage.get_all_collections()) == 1

        storage.clear()

        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []
        assert storage.get_prompt(prompt.id) is None
        assert storage.get_collection(collection.id) is None

    def test_clear_with_multiple_prompts_and_multiple_collections_empties_both_stores_completely(self):
        """Reinforces the "both stores, one call" guarantee above with a
        larger, more realistic mixed dataset (several prompts, several
        collections, including prompts assigned to collections via
        collection_id) - clear() must leave nothing behind in either
        store."""
        storage = Storage()
        collection_a = Collection(name="Collection A")
        collection_b = Collection(name="Collection B")
        storage.create_collection(collection_a)
        storage.create_collection(collection_b)
        storage.create_prompt(Prompt(title="A", content="Content A", collection_id=collection_a.id))
        storage.create_prompt(Prompt(title="B", content="Content B", collection_id=collection_a.id))
        storage.create_prompt(Prompt(title="C", content="Content C", collection_id=collection_b.id))
        storage.create_prompt(Prompt(title="D", content="Content D"))
        assert len(storage.get_all_prompts()) == 4
        assert len(storage.get_all_collections()) == 2

        storage.clear()

        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []
        assert storage.get_prompts_by_collection(collection_a.id) == []
        assert storage.get_prompts_by_collection(collection_b.id) == []

    # ---- Return value ----

    def test_clear_returns_none(self):
        """docstring: "Returns: None." Storage.clear has no explicit
        `return` statement, so per Python semantics the call must
        evaluate to None - verified directly, not assumed."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))
        storage.create_collection(Collection(name="Collection A"))

        result = storage.clear()

        assert result is None

    def test_clear_returns_none_even_on_already_empty_storage(self):
        """The None return value must hold regardless of whether there
        was anything to clear - docstring's "Returns: None" makes no
        distinction between clearing populated vs. already-empty
        storage."""
        storage = Storage()

        result = storage.clear()

        assert result is None

    # ---- No-op safety on empty storage ----

    def test_clear_on_fresh_empty_storage_does_not_raise_and_stays_empty(self):
        """Calling clear() on a freshly constructed Storage with nothing
        in it must not raise (dict.clear() on an already-empty dict is
        always safe) and must leave storage in the same empty state -
        per __init__'s docstring showing a fresh instance starts with
        get_all_prompts() == []."""
        storage = Storage()
        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

        storage.clear()

        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

    # ---- Idempotency: calling clear() multiple times in a row ----

    def test_clear_called_twice_in_a_row_on_populated_storage_is_safe_and_stays_empty(self):
        """Calling clear() twice consecutively (with no writes in
        between) must be safe - the second call operates on
        already-empty dicts, which dict.clear() handles without error -
        and storage must remain empty after both calls, not raise or
        somehow "un-clear" on the second call."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))
        storage.create_collection(Collection(name="Collection A"))

        storage.clear()
        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

        storage.clear()
        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

    def test_clear_called_three_times_consecutively_never_raises(self):
        """Extends the idempotency check to three consecutive calls with
        nothing re-added in between, confirming there is no hidden
        state (e.g. a counter or flag) that would cause a later
        redundant clear() call to behave differently or error out."""
        storage = Storage()
        storage.create_prompt(Prompt(title="A", content="Content A"))

        storage.clear()
        storage.clear()
        storage.clear()

        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

    # ---- Storage is fully usable after clear(), not just empty ----

    def test_storage_accepts_new_prompts_after_clear(self):
        """clear()'s implementation calls dict.clear() on _prompts,
        which empties the dict in place rather than rebinding
        self._prompts to a new object - so storage must remain fully
        usable afterward: creating a new prompt post-clear must succeed
        and be retrievable normally, confirming clear() does not leave
        any broken/half-reset internal state that would silently break
        subsequent writes."""
        storage = Storage()
        storage.create_prompt(Prompt(title="Before Clear", content="Old content"))
        storage.clear()
        assert storage.get_all_prompts() == []

        new_prompt = Prompt(title="After Clear", content="New content")
        result = storage.create_prompt(new_prompt)

        assert result is new_prompt
        fetched = storage.get_prompt(new_prompt.id)
        assert fetched is not None
        assert fetched.title == "After Clear"
        assert fetched.content == "New content"
        assert storage.get_all_prompts() == [new_prompt]

    def test_storage_accepts_new_collections_after_clear(self):
        """Mirrors the prompt-side check above for collections: creating
        a new collection after clear() must succeed and be retrievable
        normally, confirming _collections is likewise left in a fully
        usable state."""
        storage = Storage()
        storage.create_collection(Collection(name="Before Clear"))
        storage.clear()
        assert storage.get_all_collections() == []

        new_collection = Collection(name="After Clear")
        result = storage.create_collection(new_collection)

        assert result is new_collection
        fetched = storage.get_collection(new_collection.id)
        assert fetched is not None
        assert fetched.name == "After Clear"
        assert storage.get_all_collections() == [new_collection]

    def test_storage_full_crud_cycle_works_normally_after_clear(self):
        """Broader confirmation that clear() doesn't corrupt the
        instance for ANY subsequent operation, not just create: after
        clearing, a full create -> update -> delete cycle on a freshly
        created prompt must behave exactly as it would on a Storage
        instance that had never been cleared."""
        storage = Storage()
        storage.create_prompt(Prompt(title="Old", content="Old content"))
        storage.clear()

        prompt = Prompt(title="V1", content="Content V1")
        storage.create_prompt(prompt)
        assert storage.get_prompt(prompt.id).title == "V1"

        updated = Prompt(id=prompt.id, title="V2", content="Content V2")
        update_result = storage.update_prompt(prompt.id, updated)
        assert update_result is not None
        assert storage.get_prompt(prompt.id).title == "V2"

        delete_result = storage.delete_prompt(prompt.id)
        assert delete_result is True
        assert storage.get_prompt(prompt.id) is None
        assert storage.get_all_prompts() == []

    def test_a_second_clear_after_repopulating_storage_empties_it_again(self):
        """Confirms clear() is not a one-shot operation that only works
        the first time: create -> clear -> create again -> clear again
        must empty storage both times, reinforcing that clear() leaves
        the instance's create/read machinery fully intact for repeated
        clear-then-use cycles."""
        storage = Storage()
        storage.create_prompt(Prompt(title="First batch", content="Content"))
        storage.clear()
        assert storage.get_all_prompts() == []

        storage.create_prompt(Prompt(title="Second batch", content="Content"))
        storage.create_collection(Collection(name="Second batch collection"))
        assert len(storage.get_all_prompts()) == 1
        assert len(storage.get_all_collections()) == 1

        storage.clear()

        assert storage.get_all_prompts() == []
        assert storage.get_all_collections() == []

    # ---- Cross-instance isolation ----

    def test_clear_on_one_instance_does_not_affect_a_different_instances_prompts(self):
        """Mirrors the cross-instance isolation pattern established for
        every other Storage method (TestGetPrompt, TestUpdatePrompt,
        TestDeletePrompt, etc.): clear() on one Storage instance must
        leave a DIFFERENT Storage instance's prompts fully intact, since
        each instance's _prompts dict is independent per-instance state
        (Storage class docstring's Attributes section). This matters
        more here than for other methods, since accidentally sharing or
        clearing class-level state would be an unusually severe bug
        (silently wiping unrelated data)."""
        storage_one = Storage()
        storage_two = Storage()
        prompt_one = Prompt(title="On instance one", content="Content one")
        prompt_two = Prompt(title="On instance two", content="Content two")
        storage_one.create_prompt(prompt_one)
        storage_two.create_prompt(prompt_two)

        storage_one.clear()

        assert storage_one.get_all_prompts() == []
        assert storage_one.get_prompt(prompt_one.id) is None

        fetched_two = storage_two.get_prompt(prompt_two.id)
        assert fetched_two is not None
        assert fetched_two.title == "On instance two"
        assert len(storage_two.get_all_prompts()) == 1

    def test_clear_on_one_instance_does_not_affect_a_different_instances_collections(self):
        """Collection-side counterpart to the prompt cross-instance
        isolation test above: clear() on one Storage instance must not
        affect a different Storage instance's collections either."""
        storage_one = Storage()
        storage_two = Storage()
        collection_one = Collection(name="On instance one")
        collection_two = Collection(name="On instance two")
        storage_one.create_collection(collection_one)
        storage_two.create_collection(collection_two)

        storage_one.clear()

        assert storage_one.get_all_collections() == []
        assert storage_one.get_collection(collection_one.id) is None

        fetched_two = storage_two.get_collection(collection_two.id)
        assert fetched_two is not None
        assert fetched_two.name == "On instance two"
        assert len(storage_two.get_all_collections()) == 1

    def test_clear_on_one_instance_with_shared_ids_does_not_affect_the_other_instance(self):
        """Strengthens the cross-instance isolation check by using the
        SAME explicit id on both instances (mirroring
        TestDeletePrompt.test_delete_prompt_on_one_instance_does_not_affect_a_different_instance's
        approach) - if _prompts/_collections were ever accidentally
        shared (e.g. a class-level rather than instance-level
        attribute), this would be the test most likely to expose it,
        since a shared dict would make the id collide rather than merely
        coincide."""
        storage_one = Storage()
        storage_two = Storage()
        shared_id = "same-id-on-both-instances"
        storage_one.create_prompt(Prompt(id=shared_id, title="On one", content="Content"))
        storage_two.create_prompt(Prompt(id=shared_id, title="On two", content="Content"))

        storage_one.clear()

        assert storage_one.get_prompt(shared_id) is None
        fetched_two = storage_two.get_prompt(shared_id)
        assert fetched_two is not None
        assert fetched_two.title == "On two"

    def test_two_fresh_storage_instances_have_independent_prompts_dicts_confirmed_via_clear(self):
        """Direct confirmation (not merely inferred from behavior) that
        _prompts is genuinely a per-instance attribute rather than a
        shared/class-level object: two freshly constructed Storage
        instances must not be `is`-identical on their internal dicts.
        This is the most literal possible check against the severe-bug
        scenario the user flagged (clear() accidentally wiping shared
        state) - if __init__ ever regressed to using a mutable
        class-level default instead of assigning a new dict per
        instance in __init__, this check would catch it directly."""
        storage_one = Storage()
        storage_two = Storage()

        assert storage_one._prompts is not storage_two._prompts
        assert storage_one._collections is not storage_two._collections

    # ---- The module-level singleton, per conftest.py's usage pattern ----

    def test_clear_on_the_module_level_singleton_empties_it_exactly_like_any_other_instance(self):
        """tests/conftest.py's autouse `clear_storage` fixture imports
        `storage` from app.storage (the module-level singleton
        instantiated at the bottom of app/storage.py, `storage =
        Storage()`) and calls `storage.clear()` before AND after every
        test in the whole backend suite, to guarantee isolation between
        tests. This test exercises that EXACT object/usage pattern
        directly, rather than relying on it being only implicitly
        proven by every other test in the suite happening to pass.

        Cleanup note: this test adds data to, and then clears, the same
        singleton the autouse `clear_storage` fixture already resets
        before and after every test (including this one) - so even
        without the explicit clear() call below, the fixture's own
        `yield; storage.clear()` teardown would leave the singleton
        empty for subsequent tests. The explicit clear() call and
        assertions here are the actual subject under test, not merely
        cleanup - but they also happen to satisfy the cleanup
        requirement as a side effect, confirmed directly below rather
        than assumed.
        """
        assert storage_singleton.get_all_prompts() == []
        assert storage_singleton.get_all_collections() == []

        prompt = storage_singleton.create_prompt(Prompt(title="Singleton Prompt", content="Content"))
        collection = storage_singleton.create_collection(Collection(name="Singleton Collection"))
        assert len(storage_singleton.get_all_prompts()) == 1
        assert len(storage_singleton.get_all_collections()) == 1

        result = storage_singleton.clear()

        assert result is None
        assert storage_singleton.get_all_prompts() == []
        assert storage_singleton.get_all_collections() == []
        assert storage_singleton.get_prompt(prompt.id) is None
        assert storage_singleton.get_collection(collection.id) is None
