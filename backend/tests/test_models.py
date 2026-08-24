"""Unit tests for app.models.

These tests call app/models.py's functions and classes directly (no HTTP
layer, no TestClient) so that each function's/class's own contract can be
pinned down precisely and cheaply, independent of the FastAPI routing
layer - mirroring the pattern established in tests/test_storage.py and
tests/test_utils.py.

This is a new file, and this session's scope is deliberately narrow:
`generate_id` only (the first of several models.py functions/classes to
receive dedicated sessions - `get_current_time` and the various Pydantic
model classes such as `PromptBase`, `PromptCreate`, `PromptUpdate`,
`PromptPatch`, `Prompt`, `CollectionBase`, `CollectionCreate`,
`Collection`, `PromptList`, `CollectionList`, and `HealthResponse` are
intentionally out of scope here and will get their own TestX classes in
future sessions). The file is structured with one pytest class per
function/class under test, so it is naturally extensible: add
`TestGetCurrentTime`, `TestPromptBase`, etc. below `TestGenerateId` in
later sessions, following the same docstring/citation pattern.

Written-spec check for `generate_id` specifically (per the process
established in test_storage.py/test_utils.py's module docstrings):

- `specs/001-complete-promptlab-app/data-model.md` (Entity: Prompt table,
  `id` row) says: "string (UUID) | Primary key, auto-generated | Matches
  existing `generate_id()` behavior in `models.py`". This is the only
  spec text that references `generate_id` at all, and it explicitly
  *defers* to the function's own (existing) behavior rather than
  independently specifying a format - it does not say "UUID4" or specify
  a length; it only commits to "string (UUID)" in the generic sense, and
  says the persisted field must match whatever `generate_id()` already
  does. The `Collection.id` row in the same document says only "string
  (UUID) | Primary key, auto-generated |" with no notes column at all.
- `specs/001-complete-promptlab-app/contracts/api-contract.md` never
  mentions `id`, `uuid`, or `generate_id` at all (grepped; zero matches) -
  it documents endpoint shapes/status codes only, not field-level id
  format.
- `docs/API_REFERENCE.md` also never mentions `uuid` or `generate_id`
  (grepped; zero matches).

Conclusion: no written spec constrains `generate_id`'s own implementation
details (UUID version, exact string length, etc.) beyond generically
calling it a "string (UUID)" and pointing back at the function's existing
behavior as the source of truth. The specific, checkable claims this
session tests against - "UUID4 value", the doctest's `len(new_id) == 36`
- come entirely from `generate_id`'s own docstring in app/models.py,
which is therefore treated as the primary and, for these details, only
contract. This is stated explicitly per test-class docstring below too.
"""

import uuid

import pytest

from app.models import Prompt, generate_id


class TestGenerateId:
    """Tests for app.models.generate_id.

    Source of intended behavior: generate_id's own docstring in
    app/models.py -

        "Generate a unique identifier string.

        Returns:
            str: A newly generated UUID4 value, formatted as a string.

        Example:
            >>> new_id = generate_id()
            >>> len(new_id)
            36"

    No written spec independently constrains generate_id's format beyond
    generically calling the Prompt/Collection `id` field a "string
    (UUID)" and deferring to generate_id's own existing behavior (see the
    module docstring above for the precise grep/citation of
    data-model.md, api-contract.md, and docs/API_REFERENCE.md) - so the
    UUID4-specificity and the 36-character length claims tested below are
    sourced entirely from generate_id's own docstring, not from a
    separate written spec.

    The function is also used as `Field(default_factory=generate_id)` on
    both `Prompt.id` (models.py:117) and `Collection.id` (models.py:179).
    This file therefore also verifies, via a small integration-style
    check against the real `Prompt` class, that generate_id is fit for
    that specific real-world usage pattern (a fresh value per
    construction, not a shared/memoized one).
    """

    # ---- Return type ----------------------------------------------------

    def test_return_value_is_a_genuine_str_not_a_uuid_object(self):
        """docstring: "Returns: str: A newly generated UUID4 value,
        formatted as a string." The implementation is `return
        str(uuid4())` - uuid4() itself returns a `uuid.UUID` object, not a
        str, so this test verifies the str(...) conversion actually
        happens and isn't accidentally skipped (e.g. via a future edit
        that returns the bare UUID object instead)."""
        result = generate_id()

        assert isinstance(result, str)
        assert not isinstance(result, uuid.UUID)
        assert type(result) is str

    # ---- Format: documented length ---------------------------------------

    def test_returned_string_is_exactly_36_characters(self):
        """docstring's own doctest: ">>> len(new_id)\\n36". A standard
        UUID4 string representation is 32 hex digits plus 4 hyphens = 36
        characters total; verify this precisely for a single generated
        value."""
        result = generate_id()

        assert len(result) == 36

    def test_length_is_36_across_many_generated_values(self):
        """Determinism/consistency check: run the length assertion across
        many generated values (not just one), to rule out a rare/edge-case
        format deviation (e.g. a leading-zero component being dropped)."""
        for _ in range(1000):
            assert len(generate_id()) == 36

    # ---- Format: valid UUID4 structure ------------------------------------

    def test_returned_string_parses_back_into_a_uuid_object(self):
        """docstring: "A newly generated UUID4 value, formatted as a
        string." A genuinely UUID-formatted string must round-trip through
        uuid.UUID(...) without raising ValueError."""
        result = generate_id()

        parsed = uuid.UUID(result)

        assert isinstance(parsed, uuid.UUID)

    def test_returned_string_is_specifically_uuid_version_4(self):
        """docstring: "A newly generated UUID4 value" - this is a
        specific, checkable claim (not just "any UUID-shaped string").
        Parsing the returned string back into a uuid.UUID and inspecting
        its `.version` attribute must report 4."""
        result = generate_id()

        parsed = uuid.UUID(result)

        assert parsed.version == 4

    def test_uuid_version_4_holds_across_many_generated_values(self):
        """Same version-4 check as above, but run across many generated
        values to confirm this isn't a coincidence of a single call -
        every value generate_id() produces must be genuinely UUID4, not
        merely UUID4 "on average" or "usually"."""
        for _ in range(1000):
            parsed = uuid.UUID(generate_id())
            assert parsed.version == 4

    def test_returned_string_uses_standard_hyphenated_lowercase_format(self):
        """A standard `str(uuid.UUID(...))` representation is lowercase
        hex with hyphens at positions 8, 13, 18, 23 (8-4-4-4-12 grouping).
        Verifying this precisely confirms the docstring's "formatted as a
        string" language means the canonical str(UUID) form, not e.g. a
        hex digest with no hyphens or an uppercase representation."""
        result = generate_id()

        assert result == result.lower()
        assert result.count("-") == 4
        parts = result.split("-")
        assert [len(p) for p in parts] == [8, 4, 4, 4, 12]

    # ---- Uniqueness across multiple calls ---------------------------------

    def test_many_calls_produce_all_distinct_values(self):
        """The function's real-world job (per Field(default_factory=
        generate_id) usage on Prompt.id/Collection.id in models.py) is to
        produce a fresh, unique id every time. Calling generate_id() 1000
        times must yield 1000 distinct values - no collisions - which is
        the property that makes it fit for purpose as an id generator."""
        generated = [generate_id() for _ in range(1000)]

        assert len(set(generated)) == len(generated)

    def test_two_consecutive_calls_produce_different_values(self):
        """The simplest, most direct form of the uniqueness/freshness
        property: back-to-back calls with no other code in between must
        not return the same value."""
        first = generate_id()
        second = generate_id()

        assert first != second

    # ---- No arguments required / purity / no external state --------------

    def test_generate_id_takes_no_positional_arguments(self):
        """Signature per app/models.py: `def generate_id() -> str`. Calling
        it with a positional argument must raise TypeError, confirming the
        function genuinely takes no parameters (rather than silently
        accepting and ignoring one)."""
        with pytest.raises(TypeError):
            generate_id("unexpected-argument")

    def test_generate_id_takes_no_keyword_arguments(self):
        """Same no-parameters check as above, via a keyword argument
        instead of a positional one."""
        with pytest.raises(TypeError):
            generate_id(seed="unexpected-keyword-argument")

    def test_calls_interleaved_with_other_code_remain_independent(self):
        """Purity/no-shared-external-state check: generating an id,
        running unrelated code in between, and generating another id must
        not influence each other - each call must still be independently
        fresh and distinct, reinforcing that generate_id holds no memo/
        cache/counter state across calls."""
        first = generate_id()

        # Unrelated code executed in between, to rule out any accidental
        # shared/global state influencing subsequent calls.
        _ = [x * 2 for x in range(10)]
        _ = str(uuid.uuid4())

        second = generate_id()

        assert first != second
        assert len(first) == 36
        assert len(second) == 36

    # ---- Fitness as a Field(default_factory=...) --------------------------

    def test_two_prompt_instances_created_without_explicit_id_get_different_ids(self):
        """Integration-style check validating generate_id's actual
        real-world usage pattern: `Prompt.id: str =
        Field(default_factory=generate_id)` (models.py:117). This is
        `default_factory=generate_id` - the function itself, to be CALLED
        fresh on each instantiation - not `default=generate_id()`, which
        would evaluate generate_id() exactly once at class-definition time
        and share that single value across every Prompt instance. This
        test confirms the real failure mode is avoided: two Prompt
        instances constructed with no explicit `id=` must receive
        different ids."""
        prompt_a = Prompt(title="A", content="Content A")
        prompt_b = Prompt(title="B", content="Content B")

        assert prompt_a.id != prompt_b.id

    def test_many_prompt_instances_without_explicit_id_all_get_distinct_ids(self):
        """Same default_factory-freshness property as above, reinforced
        across many instances (not just two) to rule out any small-sample
        coincidence."""
        prompts = [Prompt(title=f"P{i}", content=f"Content {i}") for i in range(100)]

        ids = {p.id for p in prompts}

        assert len(ids) == len(prompts)

    def test_prompt_instances_get_valid_uuid4_ids_via_the_default_factory(self):
        """Confirms the ids produced through the Field(default_factory=
        generate_id) path (not generate_id() called directly) still
        satisfy generate_id's own documented format/version contract -
        i.e. the default_factory wiring doesn't somehow alter or bypass
        generate_id's own guarantees."""
        prompt = Prompt(title="A", content="Content A")

        assert isinstance(prompt.id, str)
        assert len(prompt.id) == 36
        assert uuid.UUID(prompt.id).version == 4

    def test_prompt_with_explicit_id_override_does_not_call_generate_id(self):
        """Complementary confirmation of default_factory semantics: when an
        explicit `id=` is passed to Prompt's constructor, that explicit
        value must be used verbatim rather than being replaced by a
        freshly generated one - the "default" in default_factory only
        applies when the field is omitted, per pydantic's documented
        default_factory behavior."""
        prompt = Prompt(id="explicit-id-value", title="A", content="Content A")

        assert prompt.id == "explicit-id-value"
