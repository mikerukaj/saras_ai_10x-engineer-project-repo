"""Unit tests for app.utils.

These tests call the functions in app/utils.py directly (no HTTP layer,
no TestClient) so that each function's contract can be pinned down
precisely and cheaply, independent of the FastAPI routing layer.

No written spec (specs/001-complete-promptlab-app/contracts/api-contract.md,
specs/001-complete-promptlab-app/data-model.md, docs/API_REFERENCE.md,
docs/SYSTEM_MODEL.md) covers app/utils.py's individual functions directly -
these are internal helper/utility functions, not public API contracts.
docs/API_REFERENCE.md and the list_prompts endpoint documentation describe
the *combined* effect of these helpers as exercised through GET /prompts,
but not the functions' standalone contracts (e.g. what sort_prompts_by_date
does with an empty list, or with descending=False). Intended behavior for
each function is therefore inferred from that function's own docstring
(Google-style, per .claude/skills/docstring-func/) in app/utils.py.

Note on docs/SYSTEM_MODEL.md: it references a "sorting bug" associated
with GET /prompts and sort_prompts_by_date under an older "ENTRY POINTS"
note. A prior test-writing session (see tests/test_api.py,
test_list_prompts_sorted_newest_first_with_explicit_timestamps and
test_sorting_order) investigated this and reconfirmed correct sorting
behavior at the API layer - the tracked note appears stale/already
resolved by the time of that investigation. This file independently and
directly unit-tests sort_prompts_by_date's own contract for the first
time to confirm (or refute) that at the function level, in isolation.

This file follows the docstring/citation style established in
tests/test_storage.py: one pytest class per function under test, with
each test's docstring citing the specific behavior/docstring line it is
verifying. Structured to be extended in future sessions with
TestSearchPrompts, TestValidatePromptContent, and TestExtractVariables -
one class per remaining function in app/utils.py.

TestFilterPromptsByCollection tests filter_prompts_by_collection, the
pure-function analog of Storage.get_prompts_by_collection (see
tests/test_storage.py) - but unlike that Storage method,
filter_prompts_by_collection takes an arbitrary in-memory List[Prompt]
directly (no Storage/_collections dependency, no awareness of whether
the collection itself exists). No written spec covers this function
directly either (same grep as above); its own docstring in app/utils.py
is the sole intended-behavior source, confirmed explicitly in that
class's docstring below.

TestSearchPrompts (added in this session) tests search_prompts, which
has more internal branching than the two functions above: an OR across
two fields (title, description), a short-circuit guard on description
being present (`p.description and ...`), and case-folding via `.lower()`
on three separate strings (query, title, description). No written spec
covers this function directly either (same grep as above); its own
docstring in app/utils.py is the sole intended-behavior source,
confirmed explicitly in that class's docstring below. This function is
also exercised incidentally through the HTTP layer in
tests/test_api.py's TestPrompts class (e.g.
test_list_prompts_search_matches_title_case_insensitively,
test_list_prompts_search_matches_description_case_insensitively,
test_list_prompts_search_does_not_match_content_field,
test_list_prompts_search_no_match_returns_empty_list) - those tests
confirm the same guarantees at the integration level; this class tests
the function directly and in much finer-grained isolation (e.g. the
None-vs-""-description distinction, whitespace handling, and the
query=None failure point, none of which are practical to isolate
through the HTTP layer).

TestValidatePromptContent (added in this session) tests
validate_prompt_content, which takes a plain str (not a List[Prompt]) and
has a precise numeric boundary (>= 10 characters after stripping) rather
than the qualitative behaviors of the three functions above. No written
spec covers this function directly either (same grep as above); its own
docstring in app/utils.py is the sole intended-behavior source, confirmed
explicitly in that class's docstring below.

Notable finding independently verified for this session:
validate_prompt_content appears to be dead/orphaned code.
`grep -rn "validate_prompt_content" backend/` (repo root) matches only
its own definition and its own docstring's doctest examples in
app/utils.py itself - it is never imported by app/api.py (which imports
only sort_prompts_by_date, filter_prompts_by_collection, and
search_prompts from app.utils) and is not referenced anywhere else in
backend/app/ or backend/tests/ prior to this session. The actual prompt
content validation enforced by the running API is done entirely via
Pydantic's `Field(..., min_length=1)` on PromptBase.content in
app/models.py (a 1-character minimum, not the 10-character minimum this
function documents) - a materially different rule than this function's
own. This function is still tested below since it is public, documented,
directly callable logic and was the explicit target of this session, but
it is flagged here as unused/unreachable through the live API.

TestExtractVariables (added in this session, the last of the four
app/utils.py functions) tests extract_variables, which - like
validate_prompt_content - takes a plain str and is confirmed
independently, a second time, to be dead/orphaned code:
`grep -rn "extract_variables" backend/app/ backend/tests/` (prior to this
session) matches only its own definition (app/utils.py:96) and its own
docstring's doctest example (app/utils.py:109) - it is not imported by
app/api.py (whose `from app.utils import ...` line only names
sort_prompts_by_date, filter_prompts_by_collection, and search_prompts,
identically to the validate_prompt_content finding above) and is not
referenced anywhere else in the application. Unlike the three other
functions, extract_variables is regex-driven (`re.findall(r'\\{\\{(\\w+)\\}\\}',
content)`) rather than list-comprehension/sort-driven, giving it a
distinct and much richer edge-case surface around pattern-matching
semantics (duplicate matches, malformed/unbalanced braces, nested
braces, non-word characters) that the other three functions have no
analog of. No written spec covers this function directly either (same
grep as above); its own docstring in app/utils.py is the sole
intended-behavior source, confirmed explicitly in that class's docstring
below. With this class added, all four of app/utils.py's public
functions now have dedicated, direct unit-test coverage: three
(sort_prompts_by_date, filter_prompts_by_collection, search_prompts) are
live and used by list_prompts in app/api.py, while the remaining two
(validate_prompt_content, extract_variables) are confirmed dead/orphaned
code, exercised only by these direct unit tests - i.e. half of this
module's public functions are unused by the actual running application.
"""

from datetime import datetime, timedelta

import pytest

from app.models import Prompt
from app.utils import (
    extract_variables,
    filter_prompts_by_collection,
    search_prompts,
    sort_prompts_by_date,
    validate_prompt_content,
)


def _make_prompt(title: str, created_at: datetime) -> Prompt:
    """Build a Prompt with an explicit, deterministic created_at.

    Prompt.created_at defaults via Field(default_factory=get_current_time),
    but pydantic allows explicitly overriding any field with a default by
    passing it as a keyword argument to the constructor - confirmed via
    app/models.py's Prompt definition and the existing usage pattern in
    tests/test_api.py (test_list_prompts_sorted_newest_first_with_explicit_timestamps).
    """
    return Prompt(title=title, content="content", created_at=created_at)


def _make_prompt_in_collection(title: str, collection_id) -> Prompt:
    """Build a Prompt with an explicit collection_id (or None/omitted).

    Prompt.collection_id defaults to None per app/models.py's
    PromptBase.collection_id: Optional[str] = None. Passing it explicitly
    as a keyword argument overrides that default, the same pattern used
    by _make_prompt above for created_at.
    """
    return Prompt(title=title, content="content", collection_id=collection_id)


def _make_searchable_prompt(title: str, description=None, content: str = "content") -> Prompt:
    """Build a Prompt with explicit title, description, and content.

    Prompt.description defaults to None per app/models.py's
    PromptBase.description: Optional[str] = Field(None, max_length=500).
    Passing it explicitly (including "" or None) overrides that default,
    the same pattern used by the other _make_* helpers above. `content`
    is exposed here too since search_prompts's docstring explicitly
    states content is NOT searched - tests need control over it to prove
    that guarantee.
    """
    return Prompt(title=title, content=content, description=description)


class TestSortPromptsByDate:
    """Tests for app.utils.sort_prompts_by_date.

    Source of intended behavior: sort_prompts_by_date's own docstring in
    app/utils.py -

        "Sort prompts by their creation date.

        Args:
            prompts (List[Prompt]): The prompts to sort.
            descending (bool): If True, sort newest first; if False, sort
                oldest first. Defaults to True.

        Returns:
            List[Prompt]: A new list of prompts sorted by created_at."

    No written spec (see module docstring above) covers this function
    directly; the function's own docstring is treated as the sole
    intended-behavior source, per instructions - explicitly noted here.
    """

    def test_descending_default_sorts_newest_first(self):
        """docstring: "descending (bool): If True, sort newest first" and
        "Defaults to True." With no descending argument passed, well
        separated timestamps must come back newest-first."""
        base = datetime(2026, 1, 1, 12, 0, 0)
        oldest = _make_prompt("Oldest", base)
        middle = _make_prompt("Middle", base + timedelta(days=1))
        newest = _make_prompt("Newest", base + timedelta(days=2))

        result = sort_prompts_by_date([oldest, newest, middle])

        assert [p.title for p in result] == ["Newest", "Middle", "Oldest"]

    def test_descending_true_explicit_sorts_newest_first(self):
        """Same as the default case, but with descending=True passed
        explicitly, to verify the parameter (not just its default) drives
        newest-first ordering."""
        base = datetime(2026, 1, 1, 12, 0, 0)
        oldest = _make_prompt("Oldest", base)
        newest = _make_prompt("Newest", base + timedelta(days=1))

        result = sort_prompts_by_date([oldest, newest], descending=True)

        assert [p.title for p in result] == ["Newest", "Oldest"]

    def test_descending_false_sorts_oldest_first(self):
        """docstring: "if False, sort oldest first." Verifies the
        parameter actually flips the order relative to the descending=True
        case above, not merely that "some" order is produced."""
        base = datetime(2026, 1, 1, 12, 0, 0)
        oldest = _make_prompt("Oldest", base)
        middle = _make_prompt("Middle", base + timedelta(days=1))
        newest = _make_prompt("Newest", base + timedelta(days=2))

        result = sort_prompts_by_date([newest, oldest, middle], descending=False)

        assert [p.title for p in result] == ["Oldest", "Middle", "Newest"]

    def test_empty_list_returns_empty_list(self):
        """An empty input must yield an empty output, not an error -
        sorted() over an empty sequence is well-defined and the docstring
        does not carve out an exception for the empty case."""
        result = sort_prompts_by_date([])

        assert result == []

    def test_empty_list_with_descending_false_returns_empty_list(self):
        """Same as above, confirming the empty-list case holds for both
        values of descending, not just the default."""
        result = sort_prompts_by_date([], descending=False)

        assert result == []

    def test_single_element_list_descending_true_returns_unchanged(self):
        """A single-element list has no ordering ambiguity; it must come
        back as a one-element list containing the same prompt."""
        solo = _make_prompt("Solo", datetime(2026, 1, 1))

        result = sort_prompts_by_date([solo], descending=True)

        assert len(result) == 1
        assert result[0] is solo

    def test_single_element_list_descending_false_returns_unchanged(self):
        """Same single-element check for descending=False."""
        solo = _make_prompt("Solo", datetime(2026, 1, 1))

        result = sort_prompts_by_date([solo], descending=False)

        assert len(result) == 1
        assert result[0] is solo

    def test_already_sorted_descending_input_stays_in_the_same_order(self):
        """An input list that is already newest-first must come back in
        the same order when sorted descending (idempotency-style check)."""
        base = datetime(2026, 1, 1)
        newest = _make_prompt("Newest", base + timedelta(days=2))
        middle = _make_prompt("Middle", base + timedelta(days=1))
        oldest = _make_prompt("Oldest", base)

        result = sort_prompts_by_date([newest, middle, oldest], descending=True)

        assert [p.title for p in result] == ["Newest", "Middle", "Oldest"]

    def test_already_sorted_ascending_input_stays_in_the_same_order(self):
        """An input list that is already oldest-first must come back in
        the same order when sorted ascending (idempotency-style check)."""
        base = datetime(2026, 1, 1)
        oldest = _make_prompt("Oldest", base)
        middle = _make_prompt("Middle", base + timedelta(days=1))
        newest = _make_prompt("Newest", base + timedelta(days=2))

        result = sort_prompts_by_date([oldest, middle, newest], descending=False)

        assert [p.title for p in result] == ["Oldest", "Middle", "Newest"]

    def test_fully_reverse_ordered_input_is_flipped_when_descending(self):
        """A fully oldest-to-newest input list must be flipped to
        newest-first when sorted with descending=True."""
        base = datetime(2026, 1, 1)
        oldest = _make_prompt("Oldest", base)
        middle = _make_prompt("Middle", base + timedelta(days=1))
        newest = _make_prompt("Newest", base + timedelta(days=2))

        result = sort_prompts_by_date([oldest, middle, newest], descending=True)

        assert [p.title for p in result] == ["Newest", "Middle", "Oldest"]

    def test_fully_reverse_ordered_input_is_flipped_when_ascending(self):
        """A fully newest-to-oldest input list must be flipped to
        oldest-first when sorted with descending=False."""
        base = datetime(2026, 1, 1)
        newest = _make_prompt("Newest", base + timedelta(days=2))
        middle = _make_prompt("Middle", base + timedelta(days=1))
        oldest = _make_prompt("Oldest", base)

        result = sort_prompts_by_date([newest, middle, oldest], descending=False)

        assert [p.title for p in result] == ["Oldest", "Middle", "Newest"]

    def test_duplicate_timestamps_do_not_error_and_preserve_all_elements(self):
        """Multiple prompts sharing the exact same created_at must not
        raise, and the result must contain every input element exactly
        once - the docstring does not guarantee a specific tie-breaking
        order, so this only checks completeness, not order among ties."""
        same_time = datetime(2026, 1, 1, 12, 0, 0)
        a = _make_prompt("A", same_time)
        b = _make_prompt("B", same_time)
        c = _make_prompt("C", same_time)

        result = sort_prompts_by_date([a, b, c])

        assert len(result) == 3
        assert {p.title for p in result} == {"A", "B", "C"}

    def test_duplicate_timestamps_preserve_relative_input_order_stability(self):
        """Python's sorted() is a stable sort: elements comparing equal
        under the sort key retain their relative order from the input.
        This is a genuine, documented guarantee of sorted() (not of this
        function's own docstring, which is silent on ties), and is worth
        pinning down explicitly since it is real, testable behavior."""
        same_time = datetime(2026, 1, 1, 12, 0, 0)
        a = _make_prompt("A", same_time)
        b = _make_prompt("B", same_time)
        c = _make_prompt("C", same_time)

        result_desc = sort_prompts_by_date([a, b, c], descending=True)
        result_asc = sort_prompts_by_date([a, b, c], descending=False)

        assert [p.title for p in result_desc] == ["A", "B", "C"]
        assert [p.title for p in result_asc] == ["A", "B", "C"]

    def test_mixed_duplicate_and_distinct_timestamps_sort_correctly(self):
        """A mix of tied and distinct timestamps must still place the
        distinct-timestamp groups in the correct relative order, with
        ties among themselves preserved in input order (stability)."""
        base = datetime(2026, 1, 1)
        old_a = _make_prompt("OldA", base)
        old_b = _make_prompt("OldB", base)
        newer = _make_prompt("Newer", base + timedelta(days=1))

        result = sort_prompts_by_date([old_a, old_b, newer], descending=True)

        assert [p.title for p in result] == ["Newer", "OldA", "OldB"]

    def test_returns_a_new_list_object_not_the_same_list(self):
        """docstring: "Returns: List[Prompt]: A new list of prompts..."
        The returned list must be a different object from the input
        list, even though its elements are the same Prompt instances."""
        base = datetime(2026, 1, 1)
        prompts = [_make_prompt("A", base), _make_prompt("B", base + timedelta(days=1))]

        result = sort_prompts_by_date(prompts)

        assert result is not prompts

    def test_does_not_mutate_the_input_list_order(self):
        """Sorting must not reorder the caller's original list in place -
        the input list's own order must be unchanged after the call,
        consistent with returning "a new list" rather than sorting
        in-place."""
        base = datetime(2026, 1, 1)
        newest = _make_prompt("Newest", base + timedelta(days=2))
        oldest = _make_prompt("Oldest", base)
        middle = _make_prompt("Middle", base + timedelta(days=1))
        prompts = [newest, oldest, middle]
        original_order = list(prompts)

        sort_prompts_by_date(prompts, descending=True)

        assert prompts == original_order

    def test_does_not_mutate_prompt_objects_fields(self):
        """Sorting should only reorder references; it must not alter any
        field on the Prompt objects themselves (created_at, title,
        content, etc.)."""
        base = datetime(2026, 1, 1)
        p1 = _make_prompt("P1", base)
        p2 = _make_prompt("P2", base + timedelta(days=1))
        p1_created_at_before = p1.created_at
        p2_created_at_before = p2.created_at

        sort_prompts_by_date([p1, p2])

        assert p1.created_at == p1_created_at_before
        assert p2.created_at == p2_created_at_before
        assert p1.title == "P1"
        assert p2.title == "P2"

    def test_return_type_is_a_genuine_list(self):
        """docstring: "Returns: List[Prompt]" - the return value must be
        an actual list instance."""
        result = sort_prompts_by_date([_make_prompt("A", datetime(2026, 1, 1))])

        assert isinstance(result, list)

    def test_return_type_is_a_genuine_list_for_empty_input(self):
        """The empty-input case must also return a genuine list, not
        None or some other falsy-but-not-list value."""
        result = sort_prompts_by_date([])

        assert isinstance(result, list)

    def test_result_elements_are_the_same_prompt_instances_as_input(self):
        """Sorting must reorder references, not copy or reconstruct
        prompts - each element in the result must be `is` the
        corresponding original Prompt object."""
        base = datetime(2026, 1, 1)
        oldest = _make_prompt("Oldest", base)
        newest = _make_prompt("Newest", base + timedelta(days=1))

        result = sort_prompts_by_date([oldest, newest])

        assert result[0] is newest
        assert result[1] is oldest

    # ---- Error conditions ---------------------------------------------
    # The function's type hint declares `prompts: List[Prompt]`. Passing
    # values that violate this hint (non-Prompt items, or None instead of
    # a list) is a contract violation by the *caller*, not a documented
    # behavior of sort_prompts_by_date itself. These tests pin down the
    # resulting (currently unhandled) exceptions empirically so the
    # behavior is known and regression-tested, without asserting that
    # this constitutes a bug in the function - see the final report for
    # the bug-vs-expected-consequence determination.

    def test_prompts_containing_a_plain_dict_raises_attributeerror(self):
        """The implementation does `key=lambda p: p.created_at`. A dict
        has no `.created_at` attribute, so accessing it must raise
        AttributeError. This documents the (unhandled) consequence of a
        caller violating the `List[Prompt]` type hint - it is not a
        contract violation of sort_prompts_by_date's own documented
        behavior, which only promises to sort Prompt objects."""
        valid_prompt = _make_prompt("Valid", datetime(2026, 1, 1))
        not_a_prompt = {"title": "Not a Prompt", "created_at": datetime(2026, 1, 2)}

        with pytest.raises(AttributeError):
            sort_prompts_by_date([valid_prompt, not_a_prompt])

    def test_prompts_containing_none_raises_attributeerror(self):
        """A None entry in the list also has no `.created_at` attribute
        and must raise AttributeError for the same reason as above."""
        valid_prompt = _make_prompt("Valid", datetime(2026, 1, 1))

        with pytest.raises(AttributeError):
            sort_prompts_by_date([valid_prompt, None])

    def test_prompts_equal_to_none_raises_typeerror(self):
        """Passing None instead of a list violates the `List[Prompt]`
        type hint. `sorted(None, ...)` raises TypeError because None is
        not iterable - this documents that consequence explicitly. This
        is a type-hint violation by the caller, not a bug in
        sort_prompts_by_date, which declares (and is entitled to assume)
        a list argument."""
        with pytest.raises(TypeError):
            sort_prompts_by_date(None)

    def test_descending_accepts_falsy_non_bool_values_as_ascending(self):
        """descending is type-hinted as bool, but Python does not enforce
        this at runtime and `reverse=` in sorted() accepts any truthy/
        falsy value. Passing 0 (falsy) should behave like descending=False
        (oldest first) since `reverse=0` is equivalent to `reverse=False`.
        This is not a documented case, but it is a reasonable, testable
        consequence of the implementation's parameter being passed
        straight through to sorted(reverse=...)."""
        base = datetime(2026, 1, 1)
        oldest = _make_prompt("Oldest", base)
        newest = _make_prompt("Newest", base + timedelta(days=1))

        result = sort_prompts_by_date([newest, oldest], descending=0)

        assert [p.title for p in result] == ["Oldest", "Newest"]


class TestFilterPromptsByCollection:
    """Tests for app.utils.filter_prompts_by_collection.

    Source of intended behavior: filter_prompts_by_collection's own
    docstring in app/utils.py -

        "Filter prompts down to those belonging to a specific collection.

        Args:
            prompts (List[Prompt]): The prompts to filter.
            collection_id (str): The collection id to match against each
                prompt's collection_id.

        Returns:
            List[Prompt]: The prompts whose collection_id equals
                collection_id."

    No written spec (see module docstring above) covers this function
    directly; the function's own docstring is treated as the sole
    intended-behavior source, per instructions - explicitly noted here.
    The implementation itself is a single equality-based list
    comprehension: `[p for p in prompts if p.collection_id == collection_id]`.
    """

    def test_returns_only_prompts_matching_the_given_collection_id(self):
        """docstring: "Filter prompts down to those belonging to a
        specific collection." Prompts from other collections must be
        excluded, and only the matching ones returned."""
        match_a = _make_prompt_in_collection("MatchA", "col-1")
        match_b = _make_prompt_in_collection("MatchB", "col-1")
        other = _make_prompt_in_collection("Other", "col-2")

        result = filter_prompts_by_collection([match_a, other, match_b], "col-1")

        assert {p.title for p in result} == {"MatchA", "MatchB"}
        assert "Other" not in {p.title for p in result}

    def test_empty_prompts_list_returns_empty_list(self):
        """An empty input must yield an empty output, not an error - a
        list comprehension over an empty sequence is well-defined and the
        docstring does not carve out an exception for the empty case."""
        result = filter_prompts_by_collection([], "any-id")

        assert result == []

    def test_no_matching_prompts_returns_empty_list(self):
        """Prompts exist, but none belong to the queried collection - the
        result must be an empty list, not an error or None."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        p2 = _make_prompt_in_collection("P2", "col-2")

        result = filter_prompts_by_collection([p1, p2], "col-nonexistent")

        assert result == []

    def test_excludes_prompts_with_collection_id_none_from_real_collection_query(self):
        """app/models.py: `collection_id: Optional[str] = None` -
        prompts with no collection assigned must never match a real
        (non-None) collection_id query, since None == "col-1" is False."""
        unassigned = _make_prompt_in_collection("Unassigned", None)
        assigned = _make_prompt_in_collection("Assigned", "col-1")

        result = filter_prompts_by_collection([unassigned, assigned], "col-1")

        assert [p.title for p in result] == ["Assigned"]

    def test_querying_with_collection_id_none_matches_prompts_with_collection_id_none(self):
        """Edge case explicitly called out in the task: the type hint
        declares `collection_id: str` (not Optional[str]), so passing
        None violates the hint, but Python does not enforce type hints at
        runtime. The implementation does a plain `==` comparison, so
        `p.collection_id == None` is True for prompts whose collection_id
        is itself None. Verified empirically here: querying with
        collection_id=None matches unassigned prompts rather than
        erroring or returning an empty list. This is a reasonable,
        non-erroring consequence of the equality check (not a crash), but
        it is also not a documented/intended usage per the `str` type
        hint - flagged as a notable edge case in the report, not treated
        as a bug since it does not violate any stated contract."""
        unassigned_a = _make_prompt_in_collection("UnassignedA", None)
        unassigned_b = _make_prompt_in_collection("UnassignedB", None)
        assigned = _make_prompt_in_collection("Assigned", "col-1")

        result = filter_prompts_by_collection(
            [unassigned_a, assigned, unassigned_b], None
        )

        assert {p.title for p in result} == {"UnassignedA", "UnassignedB"}

    def test_querying_with_collection_id_none_excludes_prompts_with_real_collection_id(self):
        """Complement of the above: querying with collection_id=None must
        not match prompts that do have a real, non-None collection_id."""
        assigned = _make_prompt_in_collection("Assigned", "col-1")

        result = filter_prompts_by_collection([assigned], None)

        assert result == []

    def test_all_prompts_matching_returns_full_list_unchanged_in_length(self):
        """Every prompt in the input belongs to the queried collection -
        the full list must be returned, with none dropped."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        p2 = _make_prompt_in_collection("P2", "col-1")
        p3 = _make_prompt_in_collection("P3", "col-1")

        result = filter_prompts_by_collection([p1, p2, p3], "col-1")

        assert len(result) == 3
        assert {p.title for p in result} == {"P1", "P2", "P3"}

    def test_multiple_prompts_in_same_collection_all_returned_not_just_first(self):
        """Multiple prompts sharing the same collection_id must all be
        returned, not truncated to the first match - the docstring
        promises "the prompts" (plural) whose collection_id equals the
        query, not a single result."""
        p1 = _make_prompt_in_collection("First", "col-1")
        p2 = _make_prompt_in_collection("Second", "col-1")
        p3 = _make_prompt_in_collection("Third", "col-1")
        other = _make_prompt_in_collection("Other", "col-2")

        result = filter_prompts_by_collection([p1, other, p2, p3], "col-1")

        assert len(result) == 3
        assert [p.title for p in result] == ["First", "Second", "Third"]

    def test_case_differing_collection_id_does_not_match(self):
        """Confirms exact-match (case-sensitive) semantics, not
        case-insensitive matching - "COL-1" must not match a prompt whose
        collection_id is "col-1", mirroring the exact-equality rigor
        already applied to Storage.get_collection/get_prompt in prior
        sessions."""
        p1 = _make_prompt_in_collection("P1", "col-1")

        result = filter_prompts_by_collection([p1], "COL-1")

        assert result == []

    def test_substring_collection_id_does_not_match(self):
        """A query that is a substring of the actual collection_id must
        not match - confirms exact equality, not substring/fuzzy
        matching."""
        p1 = _make_prompt_in_collection("P1", "col-123")

        result = filter_prompts_by_collection([p1], "col-1")

        assert result == []

    def test_superstring_collection_id_does_not_match(self):
        """A query that is a superstring of the actual collection_id must
        not match either - confirms exact equality in both directions."""
        p1 = _make_prompt_in_collection("P1", "col-1")

        result = filter_prompts_by_collection([p1], "col-123")

        assert result == []

    def test_empty_string_query_does_not_match_collection_id_none(self):
        """"" != None in Python, so querying with an empty string must
        not match prompts with collection_id=None (confirms the
        implementation does not falsy-check collection_id before
        comparing, e.g. via `if p.collection_id else ...`)."""
        unassigned = _make_prompt_in_collection("Unassigned", None)

        result = filter_prompts_by_collection([unassigned], "")

        assert result == []

    def test_empty_string_query_matches_prompts_with_collection_id_explicitly_empty_string(self):
        """A prompt whose collection_id is genuinely the empty string
        ("" is a valid, if unusual, str value permitted by the
        Optional[str] type hint) must match an empty-string query, since
        "" == "" is True - confirms exact equality rather than a
        falsy/truthiness check that would incorrectly treat "" like
        None."""
        empty_id_prompt = _make_prompt_in_collection("EmptyId", "")

        result = filter_prompts_by_collection([empty_id_prompt], "")

        assert [p.title for p in result] == ["EmptyId"]

    def test_returns_a_new_list_object_not_the_same_list(self):
        """docstring: "Returns: List[Prompt]: The prompts whose
        collection_id equals collection_id." Implementation is a list
        comprehension, which always constructs a new list object -
        verified the result is not the same object as the input list."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        prompts = [p1]

        result = filter_prompts_by_collection(prompts, "col-1")

        assert result is not prompts

    def test_does_not_mutate_the_input_list_order_or_contents(self):
        """Filtering must not alter the caller's original list in place -
        the input list's own order and contents must be unchanged after
        the call."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        p2 = _make_prompt_in_collection("P2", "col-2")
        p3 = _make_prompt_in_collection("P3", "col-1")
        prompts = [p1, p2, p3]
        original_order = list(prompts)

        filter_prompts_by_collection(prompts, "col-1")

        assert prompts == original_order

    def test_does_not_mutate_prompt_objects_fields(self):
        """Filtering should only select references; it must not alter any
        field on the Prompt objects themselves (collection_id, title,
        content, etc.)."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        collection_id_before = p1.collection_id
        title_before = p1.title

        filter_prompts_by_collection([p1], "col-1")

        assert p1.collection_id == collection_id_before
        assert p1.title == title_before

    def test_return_type_is_a_genuine_list(self):
        """docstring: "Returns: List[Prompt]" - the return value must be
        an actual list instance for a non-empty match."""
        p1 = _make_prompt_in_collection("P1", "col-1")

        result = filter_prompts_by_collection([p1], "col-1")

        assert isinstance(result, list)

    def test_return_type_is_a_genuine_list_for_empty_input(self):
        """The empty-input case must also return a genuine list, not
        None or some other falsy-but-not-list value."""
        result = filter_prompts_by_collection([], "col-1")

        assert isinstance(result, list)

    def test_return_type_is_a_genuine_list_when_no_prompts_match(self):
        """The no-match case (non-empty input, zero results) must also
        return a genuine (empty) list, not None."""
        p1 = _make_prompt_in_collection("P1", "col-1")

        result = filter_prompts_by_collection([p1], "col-nonexistent")

        assert isinstance(result, list)

    def test_result_elements_are_the_same_prompt_instances_as_input(self):
        """Filtering must select references, not copy or reconstruct
        prompts - each element in the result must be `is` the
        corresponding original Prompt object. Note: unlike the
        Storage-layer methods tested in tests/test_storage.py, this
        function has no persistent internal state of its own to
        "corrupt" via such aliasing (it doesn't own `prompts`) - but the
        same general mutation-risk pattern applies to whatever list the
        *caller* passed in: mutating a returned element still mutates the
        object the caller's own list references, since no copying
        occurs."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        p2 = _make_prompt_in_collection("P2", "col-2")

        result = filter_prompts_by_collection([p1, p2], "col-1")

        assert result[0] is p1

    # ---- Error conditions ---------------------------------------------
    # The function's type hint declares `prompts: List[Prompt]` and
    # `collection_id: str`. Passing values that violate these hints
    # (non-Prompt items or None instead of a list; a non-str
    # collection_id) is a contract violation by the *caller*, not a
    # documented behavior of filter_prompts_by_collection itself. These
    # tests pin down the resulting (currently unhandled, or safely
    # no-op) behavior empirically - see the final report for the
    # bug-vs-expected-consequence determination and the explicit contrast
    # with sort_prompts_by_date's error behavior.

    def test_prompts_containing_a_plain_dict_raises_attributeerror(self):
        """The implementation does `p.collection_id` inside the list
        comprehension's condition. A dict has no `.collection_id`
        attribute, so accessing it must raise AttributeError - the same
        class of consequence documented for sort_prompts_by_date above,
        since both functions assume every element is a Prompt-like object
        with the relevant attribute."""
        valid_prompt = _make_prompt_in_collection("Valid", "col-1")
        not_a_prompt = {"title": "Not a Prompt", "collection_id": "col-1"}

        with pytest.raises(AttributeError):
            filter_prompts_by_collection([valid_prompt, not_a_prompt], "col-1")

    def test_prompts_containing_none_raises_attributeerror(self):
        """A None entry in the list also has no `.collection_id`
        attribute and must raise AttributeError for the same reason as
        above."""
        valid_prompt = _make_prompt_in_collection("Valid", "col-1")

        with pytest.raises(AttributeError):
            filter_prompts_by_collection([valid_prompt, None], "col-1")

    def test_prompts_equal_to_none_raises_typeerror(self):
        """Passing None instead of a list violates the `List[Prompt]`
        type hint. Iterating over None in the list comprehension
        (`for p in prompts`) raises TypeError because None is not
        iterable - this documents that consequence explicitly, mirroring
        the equivalent case for sort_prompts_by_date. This is a
        type-hint violation by the caller, not a bug in
        filter_prompts_by_collection, which declares (and is entitled to
        assume) a list argument."""
        with pytest.raises(TypeError):
            filter_prompts_by_collection(None, "col-1")

    def test_collection_id_as_non_string_type_does_not_error_and_returns_no_matches(self):
        """collection_id is type-hinted as str, but the implementation
        only ever does `p.collection_id == collection_id` - a plain
        equality comparison. Unlike attribute access (which raises for
        the wrong type), `==` between a str and an unrelated type (e.g.
        an int) is always safe in Python and simply evaluates to False
        rather than raising. Verified empirically here: passing an int
        collection_id must not raise, and must yield no matches against
        prompts whose collection_id values are all strings or None -
        this is a meaningfully different error-behavior profile than
        sort_prompts_by_date's `key=lambda p: p.created_at` (which relies
        on attribute access, not just equality, when the *list* elements
        are wrong-typed) - explicitly noted as a contrast in the
        report."""
        p1 = _make_prompt_in_collection("P1", "col-1")
        p2 = _make_prompt_in_collection("P2", None)

        result = filter_prompts_by_collection([p1, p2], 12345)

        assert result == []

    def test_collection_id_as_non_string_type_can_match_a_prompt_with_that_exact_non_string_value(self):
        """Complement of the above: since the comparison is a plain `==`
        with no type coercion, if a Prompt object somehow held a
        non-string collection_id equal to the query (constructible here
        only by bypassing pydantic validation via model_construct, since
        the Prompt schema enforces Optional[str] on normal construction),
        the equality check would still match it. This pins down that the
        "no match" result above is a genuine consequence of no prompt
        having an equal value - not of the function special-casing
        non-string queries to always return no matches."""
        # Prompt.collection_id is validated as Optional[str] via pydantic
        # on normal construction, so an int value can only be attached by
        # bypassing validation (model_construct), confirming this is a
        # deliberately constructed synthetic edge case, not a value that
        # could arise through the model's normal, documented contract.
        weird_prompt = Prompt.model_construct(
            id="fake-id",
            title="Weird",
            content="content",
            description=None,
            collection_id=12345,
        )

        result = filter_prompts_by_collection([weird_prompt], 12345)

        assert result == [weird_prompt]


class TestSearchPrompts:
    """Tests for app.utils.search_prompts.

    Source of intended behavior: search_prompts's own docstring in
    app/utils.py -

        "Search prompts by title and description text.

        Matching is a case-insensitive substring check against each
        prompt's title and description. The prompt's content field is
        not searched.

        Args:
            prompts (List[Prompt]): The prompts to search.
            query (str): The search text to look for.

        Returns:
            List[Prompt]: The prompts whose title or description
                contains query, case-insensitively."

    No written spec (see module docstring above) covers this function
    directly; the function's own docstring is treated as the sole
    intended-behavior source, per instructions - explicitly noted here.
    The implementation is:

        query_lower = query.lower()
        return [
            p for p in prompts
            if query_lower in p.title.lower() or
               (p.description and query_lower in p.description.lower())
        ]
    """

    # ---- Basic matching -------------------------------------------------

    def test_query_matching_substring_of_title_matches(self):
        """docstring: "case-insensitive substring check against each
        prompt's title" - a query that is a substring (not the full
        title) must still match, confirming substring (not exact-match)
        semantics."""
        prompt = _make_searchable_prompt("Cold outreach email")

        result = search_prompts([prompt], "outreach")

        assert result == [prompt]

    def test_query_matching_substring_of_description_when_title_does_not_match(self):
        """docstring: matching checks "title and description" - a query
        that only appears in description (not title at all) must still
        match, confirming the OR actually checks both fields rather than
        title alone."""
        prompt = _make_searchable_prompt(
            "Greeting generator", description="Useful for marketing campaigns"
        )

        result = search_prompts([prompt], "marketing")

        assert result == [prompt]

    def test_query_matching_both_title_and_description_returns_prompt_once(self):
        """When a query matches both fields on the same prompt, the OR
        short-circuits/combines to a single inclusion - the prompt must
        appear exactly once in the results, not duplicated."""
        prompt = _make_searchable_prompt(
            "Email campaign generator", description="Great for email marketing"
        )

        result = search_prompts([prompt], "email")

        assert result == [prompt]
        assert len(result) == 1

    def test_content_field_is_not_searched(self):
        """docstring: "The prompt's content field is not searched." A
        prompt whose content contains the query, but whose title and
        description do not, must NOT appear in the results - this is the
        single most important documented guarantee of this function."""
        prompt = _make_searchable_prompt(
            "Greeting generator",
            description="Says hello",
            content="This prompt mentions unicorn somewhere in its body",
        )

        result = search_prompts([prompt], "unicorn")

        assert result == []

    # ---- Case-insensitivity ---------------------------------------------

    def test_uppercase_query_matches_lowercase_title(self):
        """docstring: "case-insensitive substring check" - an uppercase
        query must match a lowercase title."""
        prompt = _make_searchable_prompt("cold outreach email")

        result = search_prompts([prompt], "EMAIL")

        assert result == [prompt]

    def test_lowercase_query_matches_uppercase_title(self):
        """Complement of the above: a lowercase query must match an
        uppercase (or mixed-case) title."""
        prompt = _make_searchable_prompt("COLD OUTREACH EMAIL")

        result = search_prompts([prompt], "email")

        assert result == [prompt]

    def test_mixed_case_query_matches_mixed_case_title(self):
        """Case-insensitivity must hold for arbitrary mixed-case query
        against arbitrary mixed-case title, not just the all-upper/
        all-lower extremes."""
        prompt = _make_searchable_prompt("Cold Outreach Email")

        result = search_prompts([prompt], "OuTrEaCh")

        assert result == [prompt]

    def test_uppercase_query_matches_lowercase_description(self):
        """Case-insensitivity must be verified independently for the
        description field, not only for title."""
        prompt = _make_searchable_prompt(
            "Greeting generator", description="great for marketing campaigns"
        )

        result = search_prompts([prompt], "MARKETING")

        assert result == [prompt]

    def test_lowercase_query_matches_uppercase_description(self):
        """Complement of the above for description: a lowercase query
        must match an uppercase description."""
        prompt = _make_searchable_prompt(
            "Greeting generator", description="GREAT FOR MARKETING CAMPAIGNS"
        )

        result = search_prompts([prompt], "marketing")

        assert result == [prompt]

    # ---- description=None vs description="" -----------------------------

    def test_description_none_does_not_error_and_falls_through_to_title_only_matching(self):
        """Implementation: `(p.description and query_lower in
        p.description.lower())`. When description is None, `p.description
        and ...` short-circuits before `.lower()` is ever called on None,
        so this must not raise AttributeError - and a query that only
        matches title must still work normally for a None-description
        prompt."""
        prompt = _make_searchable_prompt("Cold outreach email", description=None)

        result = search_prompts([prompt], "email")

        assert result == [prompt]

    def test_description_none_and_query_does_not_match_title_returns_no_match(self):
        """Complement of the above: a None description must never
        contribute a false-positive match - if the query doesn't appear
        in title either, the prompt must be excluded, and no
        AttributeError should occur along the way."""
        prompt = _make_searchable_prompt("Greeting generator", description=None)

        result = search_prompts([prompt], "unrelated-term")

        assert result == []

    def test_description_empty_string_never_matches_via_description_even_for_empty_query(self):
        """Implementation: `p.description and query_lower in
        p.description.lower()`. When description is "" (empty string,
        not None), `p.description` itself is falsy, so the `and` still
        short-circuits to False *without* evaluating the `in` check -
        even when query_lower is also "" (which would trivially be `in`
        ""). This must be verified precisely: an empty-string query must
        NOT be considered a description match via an empty-string
        description (though it may still match via title, since title
        matching does not have this falsy guard)."""
        prompt = _make_searchable_prompt("xyz", description="")

        result = search_prompts([prompt], "")

        # Matches only because "" is a substring of title "xyz", not
        # because of the (falsy, short-circuited) description branch.
        assert result == [prompt]

    def test_description_empty_string_vs_none_both_safely_excluded_for_non_matching_title(self):
        """Distinguishes "" from None precisely: both must behave
        identically (safely falsy, no error, no match contribution) when
        the title does not match either - confirming "" is handled via
        the same short-circuit path as None, not via a `.lower()` call on
        an empty string that happens to also not match."""
        prompt_none = _make_searchable_prompt("Greeting generator", description=None)
        prompt_empty = _make_searchable_prompt("Greeting generator", description="")

        result = search_prompts([prompt_none, prompt_empty], "nonexistent-term")

        assert result == []

    # ---- No matches / empty inputs ---------------------------------------

    def test_no_matches_returns_empty_list(self):
        """A query that appears in neither title nor description of any
        prompt must return an empty list."""
        prompt = _make_searchable_prompt("Greeting generator", description="Says hello")

        result = search_prompts([prompt], "zzz-no-such-text-zzz")

        assert result == []

    def test_empty_prompts_list_returns_empty_list(self):
        """An empty input must yield an empty output, not an error - a
        list comprehension over an empty sequence is well-defined."""
        result = search_prompts([], "anything")

        assert result == []

    # ---- Empty query string -----------------------------------------------

    def test_empty_query_string_matches_every_prompt_via_title(self):
        """Python semantics: "" in any_string is always True, so an empty
        query is a substring of every title, meaning search_prompts([...],
        "") must match every prompt in the input. The docstring does not
        explicitly address the empty-query case, but "substring check"
        naturally implies this per Python's `in` operator - verified here
        precisely, and flagged in the report as a notable, non-obvious
        (but not contract-violating) behavior rather than a bug."""
        p1 = _make_searchable_prompt("Alpha")
        p2 = _make_searchable_prompt("Beta", description="something")
        p3 = _make_searchable_prompt("Gamma", description=None)

        result = search_prompts([p1, p2, p3], "")

        assert result == [p1, p2, p3]

    # ---- Whitespace handling -----------------------------------------------

    def test_query_with_leading_and_trailing_whitespace_is_treated_literally_not_stripped(self):
        """The docstring describes a plain "substring check" with no
        mention of trimming/stripping whitespace. A query with surrounding
        spaces must be treated as a literal substring, including the
        spaces - so it will NOT match a title that contains the trimmed
        word but has no such literal whitespace-padded substring anywhere
        (in particular, "email" at the very start of the title has no
        preceding space to satisfy the leading-space requirement, and
        nothing in the title supplies a trailing space either since
        "email" is the only word)."""
        prompt = _make_searchable_prompt("email")

        result = search_prompts([prompt], " email ")

        assert result == []

    def test_query_with_whitespace_matches_when_title_contains_the_literal_padded_substring(self):
        """Complement of the above: confirms the whitespace-inclusive
        literal substring DOES match when the title actually contains
        that exact padded substring, proving the previous test's empty
        result is due to literal (non-stripped) substring semantics, not
        some other failure."""
        prompt = _make_searchable_prompt("Cold outreach email template")

        result = search_prompts([prompt], " email t")

        assert result == [prompt]

    # ---- Mixed list: some match, some do not -------------------------------

    def test_mixed_list_returns_exactly_the_matching_subset(self):
        """With several prompts in the input, only those genuinely
        matching (via title or description) must be returned - no false
        positives, no false negatives."""
        title_match = _make_searchable_prompt("Cold outreach email")
        desc_match = _make_searchable_prompt(
            "Greeting generator", description="Email marketing campaigns"
        )
        content_only_match = _make_searchable_prompt(
            "Story generator", description="For fiction", content="mentions email here"
        )
        no_match = _make_searchable_prompt("Weather forecast", description="Sunny today")

        result = search_prompts(
            [title_match, desc_match, content_only_match, no_match], "email"
        )

        assert result == [title_match, desc_match]

    # ---- Non-mutation / return semantics -----------------------------------

    def test_returns_a_new_list_object_not_the_same_list(self):
        """docstring: "Returns: List[Prompt]: The prompts whose title or
        description contains query..." Implementation is a list
        comprehension, which always constructs a new list object -
        verified the result is not the same object as the input list."""
        prompt = _make_searchable_prompt("Cold outreach email")
        prompts = [prompt]

        result = search_prompts(prompts, "email")

        assert result is not prompts

    def test_does_not_mutate_the_input_list_order_or_contents(self):
        """Searching must not alter the caller's original list in place -
        the input list's own order and contents must be unchanged after
        the call."""
        p1 = _make_searchable_prompt("Alpha email")
        p2 = _make_searchable_prompt("Beta")
        p3 = _make_searchable_prompt("Gamma email")
        prompts = [p1, p2, p3]
        original_order = list(prompts)

        search_prompts(prompts, "email")

        assert prompts == original_order

    def test_does_not_mutate_prompt_objects_fields(self):
        """Searching should only select references; it must not alter
        any field on the Prompt objects themselves (title, description,
        content, etc.)."""
        prompt = _make_searchable_prompt("Cold outreach email", description="Sales")
        title_before = prompt.title
        description_before = prompt.description

        search_prompts([prompt], "email")

        assert prompt.title == title_before
        assert prompt.description == description_before

    def test_return_type_is_a_genuine_list(self):
        """docstring: "Returns: List[Prompt]" - the return value must be
        an actual list instance for a non-empty match."""
        prompt = _make_searchable_prompt("Cold outreach email")

        result = search_prompts([prompt], "email")

        assert isinstance(result, list)

    def test_return_type_is_a_genuine_list_for_empty_input(self):
        """The empty-input case must also return a genuine list, not
        None or some other falsy-but-not-list value."""
        result = search_prompts([], "email")

        assert isinstance(result, list)

    def test_return_type_is_a_genuine_list_when_no_prompts_match(self):
        """The no-match case (non-empty input, zero results) must also
        return a genuine (empty) list, not None."""
        prompt = _make_searchable_prompt("Weather forecast")

        result = search_prompts([prompt], "nonexistent-term")

        assert isinstance(result, list)

    def test_result_elements_are_the_same_prompt_instances_as_input(self):
        """Searching must select references, not copy or reconstruct
        prompts - each element in the result must be `is` the
        corresponding original Prompt object."""
        p1 = _make_searchable_prompt("Cold outreach email")
        p2 = _make_searchable_prompt("Weather forecast")

        result = search_prompts([p1, p2], "email")

        assert result[0] is p1

    # ---- Error conditions ---------------------------------------------
    # The function's type hint declares `prompts: List[Prompt]` and
    # `query: str`. Passing values that violate these hints (non-Prompt
    # items or None instead of a list; a non-str/None query) is a
    # contract violation by the *caller*, not a documented behavior of
    # search_prompts itself. These tests pin down the resulting
    # (currently unhandled) exceptions empirically - see the final report
    # for the bug-vs-expected-consequence determination and the explicit
    # contrast with sort_prompts_by_date's and
    # filter_prompts_by_collection's error-behavior profiles.

    def test_prompts_containing_a_plain_dict_raises_attributeerror(self):
        """The implementation does `p.title.lower()` inside the list
        comprehension's condition. A dict has no `.title` attribute, so
        accessing it must raise AttributeError - the same class of
        consequence documented for sort_prompts_by_date and
        filter_prompts_by_collection above."""
        valid_prompt = _make_searchable_prompt("Valid prompt")
        not_a_prompt = {"title": "Not a Prompt", "description": None}

        with pytest.raises(AttributeError):
            search_prompts([valid_prompt, not_a_prompt], "valid")

    def test_prompts_containing_none_raises_attributeerror(self):
        """A None entry in the list also has no `.title` attribute and
        must raise AttributeError for the same reason as above."""
        valid_prompt = _make_searchable_prompt("Valid prompt")

        with pytest.raises(AttributeError):
            search_prompts([valid_prompt, None], "valid")

    def test_prompts_equal_to_none_raises_typeerror(self):
        """Passing None instead of a list violates the `List[Prompt]`
        type hint. Iterating over None in the list comprehension
        (`for p in prompts`) raises TypeError because None is not
        iterable - mirroring the equivalent case for the other two
        functions in this module. Note this only manifests after
        `query.lower()` has already succeeded, since that line executes
        unconditionally before the list comprehension begins (see the
        test below for the case where query itself is the invalid one)."""
        with pytest.raises(TypeError):
            search_prompts(None, "valid")

    def test_query_none_raises_attributeerror_even_with_empty_prompts_list(self):
        """Implementation: `query_lower = query.lower()` executes FIRST,
        unconditionally, before the list comprehension over `prompts`
        even begins. Passing query=None must therefore raise
        AttributeError (None has no `.lower()`) immediately - and,
        notably, this happens even when `prompts` is empty, since the
        failure point is entirely independent of prompts and is reached
        before any prompt would otherwise be examined. This is a
        meaningfully different failure point than sort_prompts_by_date
        and filter_prompts_by_collection, whose only type-hint-violation
        failures are keyed off individual `prompts` elements (or `prompts`
        itself being non-iterable) - neither of those functions has an
        unconditional pre-loop failure point analogous to search_prompts's
        `query.lower()` call."""
        with pytest.raises(AttributeError):
            search_prompts([], None)

    def test_query_none_raises_attributeerror_with_non_empty_prompts_list(self):
        """Same failure point as above, but with a non-empty, otherwise
        well-formed prompts list - confirming the AttributeError comes
        from `query.lower()` itself and not from anything related to the
        prompts contents (which are never reached)."""
        valid_prompt = _make_searchable_prompt("Valid prompt")

        with pytest.raises(AttributeError):
            search_prompts([valid_prompt], None)


class TestValidatePromptContent:
    """Tests for app.utils.validate_prompt_content.

    Source of intended behavior: validate_prompt_content's own docstring
    in app/utils.py -

        "Check if prompt content is valid.

        A valid prompt should:
        - Not be empty
        - Not be just whitespace
        - Be at least 10 characters

        Args:
            content (str): The prompt content to validate.

        Returns:
            bool: True if content is non-empty, non-whitespace-only, and
                at least 10 characters after stripping. False otherwise."

    No written spec (see module docstring above) covers this function
    directly; the function's own docstring is treated as the sole
    intended-behavior source, per instructions - explicitly noted here.
    The implementation is:

        if not content or not content.strip():
            return False
        return len(content.strip()) >= 10

    Note: unlike the three functions above, this one takes a plain `str`
    (not a `List[Prompt]`), so no `_make_prompt`-style helper is needed -
    tests call the function directly with string literals.

    Dead-code note: this function is not imported or called anywhere in
    app/api.py or elsewhere in the application (verified via
    `grep -rn "validate_prompt_content" backend/`, which matches only
    this function's own definition and its own docstring's doctest
    examples). The API's real content validation is a *different* rule
    entirely - Pydantic's `Field(..., min_length=1)` on
    PromptBase.content in app/models.py, a 1-character minimum, not this
    function's 10-character minimum. See the final report for the full
    write-up of this finding.
    """

    # ---- Clearly valid content -----------------------------------------

    def test_normal_string_well_over_ten_characters_returns_true(self):
        """docstring: a valid prompt is "at least 10 characters" and not
        empty/whitespace-only. A normal, well-formed prompt string far
        exceeding 10 characters must return True - the documented happy
        path, matching the docstring's own doctest example."""
        result = validate_prompt_content("Write a short story about a dragon")

        assert result is True

    # ---- Empty string ----------------------------------------------------

    def test_empty_string_returns_false(self):
        """docstring: "Not be empty" is the first documented rule. An
        empty string must return False."""
        result = validate_prompt_content("")

        assert result is False

    # ---- Whitespace-only content ------------------------------------------

    def test_spaces_only_returns_false(self):
        """docstring: "Not be just whitespace" - a string of only space
        characters must return False, matching the docstring's own
        doctest example (validate_prompt_content("   ") -> False)."""
        result = validate_prompt_content("   ")

        assert result is False

    def test_tabs_only_returns_false(self):
        """Whitespace-only must hold for tab characters too, not just
        spaces - str.strip() treats tabs as whitespace, and the docstring
        does not carve out an exception for any particular whitespace
        character."""
        result = validate_prompt_content("\t\t\t\t\t\t\t\t\t\t\t")

        assert result is False

    def test_newlines_only_returns_false(self):
        """Whitespace-only must hold for newline characters too."""
        result = validate_prompt_content("\n\n\n\n\n\n\n\n\n\n\n")

        assert result is False

    def test_mixed_whitespace_characters_only_returns_false(self):
        """A mix of spaces, tabs, and newlines (still entirely
        whitespace, no real characters) must also return False, not just
        a single repeated whitespace character."""
        result = validate_prompt_content("  \t\n \t\n  \t \n ")

        assert result is False

    def test_whitespace_only_string_that_is_very_long_returns_false(self):
        """Confirms whitespace-only is checked independently of raw
        length: even a long (20-character) whitespace-only string must
        return False, since `content.strip()` reduces it to an empty
        string regardless of how long the original padding was."""
        result = validate_prompt_content(" " * 20)

        assert result is False

    # ---- Exact 10-character boundary --------------------------------------

    def test_exactly_ten_characters_returns_true(self):
        """docstring: "Be at least 10 characters" - "at least" is
        inclusive, so a string of EXACTLY 10 non-whitespace characters
        after stripping must return True, not False."""
        content = "1234567890"
        assert len(content) == 10  # sanity-check the fixture itself

        result = validate_prompt_content(content)

        assert result is True

    def test_nine_characters_returns_false(self):
        """One character under the 10-character threshold must return
        False - the boundary is not inclusive of 9."""
        content = "123456789"
        assert len(content) == 9  # sanity-check the fixture itself

        result = validate_prompt_content(content)

        assert result is False

    def test_eleven_characters_returns_true(self):
        """One character over the 10-character threshold must return
        True, confirming the boundary does not somehow cap out at
        exactly 10."""
        content = "12345678901"
        assert len(content) == 11  # sanity-check the fixture itself

        result = validate_prompt_content(content)

        assert result is True

    # ---- Raw length vs. stripped length ------------------------------------

    def test_length_check_uses_stripped_length_not_raw_length(self):
        """docstring's Returns section: "at least 10 characters after
        stripping" - the length check must be performed on the STRIPPED
        content, not the raw content. Constructed here: "  123456  " has
        a raw length of 10 (>= the threshold) but a stripped length of
        only 6 ("123456", < the threshold). If the implementation
        incorrectly checked raw length instead of stripped length, this
        would return True; per the documented "after stripping" rule, it
        must return False."""
        content = "  123456  "
        assert len(content) == 10  # raw length meets/exceeds the threshold
        assert len(content.strip()) == 6  # stripped length does not

        result = validate_prompt_content(content)

        assert result is False

    def test_stripping_can_only_shorten_never_lengthen_so_reverse_case_is_impossible(self):
        """Complement/reasoning check for the above: str.strip() can only
        remove leading/trailing whitespace, so a stripped string can
        never be LONGER than the raw string - there is no possible input
        where raw length < 10 but stripped length >= 10. This is
        confirmed here structurally (not as a behavioral test of
        validate_prompt_content itself, since no such input exists to
        construct): for the exact boundary-crossing string used above,
        stripped length must be <= raw length, ruling out the reverse
        direction entirely."""
        content = "  123456  "

        assert len(content.strip()) <= len(content)

    # ---- Internal whitespace (only leading/trailing is stripped) -----------

    def test_nine_characters_with_internal_spaces_returns_false(self):
        """str.strip() only removes LEADING/TRAILING whitespace, not
        internal whitespace - internal spaces count toward the length.
        "a b c d e" is 9 characters total (5 letters + 4 internal
        spaces), with no leading/trailing whitespace to strip, so it
        remains 9 characters after stripping and must return False (one
        under the threshold)."""
        content = "a b c d e"
        assert len(content) == 9  # sanity-check: internal spaces counted
        assert content.strip() == content  # no leading/trailing whitespace to strip

        result = validate_prompt_content(content)

        assert result is False

    def test_eleven_characters_with_internal_spaces_returns_true(self):
        """Complement of the above: "a b c d e f" is 11 characters total
        (6 letters + 5 internal spaces), with no leading/trailing
        whitespace to strip, so it remains 11 characters after stripping
        and must return True (one over the threshold) - confirming
        internal whitespace is counted precisely, not discounted."""
        content = "a b c d e f"
        assert len(content) == 11  # sanity-check: internal spaces counted
        assert content.strip() == content  # no leading/trailing whitespace to strip

        result = validate_prompt_content(content)

        assert result is True

    # ---- Error conditions / non-str input ----------------------------------
    # The function's type hint declares `content: str`. Passing values
    # that violate this hint is a contract violation by the *caller*, not
    # a documented behavior of validate_prompt_content itself. These
    # tests pin down the resulting (sometimes gracefully handled,
    # sometimes unhandled) behavior empirically - see the final report
    # for the explicit contrast with the None/non-str error profiles of
    # the three functions above.

    def test_none_returns_false_without_raising(self):
        """Implementation: `if not content or not content.strip():
        return False`. `not None` evaluates to True in Python, so this
        short-circuits to `return False` BEFORE `.strip()` is ever called
        on None - meaning validate_prompt_content(None) must return False
        gracefully, NOT raise AttributeError. This is a genuinely
        different, defensive error profile compared to
        sort_prompts_by_date, filter_prompts_by_collection, and
        search_prompts, all three of which raise on None-related bad
        input (see their own Error conditions sections above) - this is
        the first of the four app/utils.py functions confirmed to guard
        against None gracefully rather than let it propagate to an
        exception."""
        result = validate_prompt_content(None)

        assert result is False

    def test_non_string_truthy_input_raises_attributeerror(self):
        """Contrast case for the None finding above: the type hint says
        `content: str`, but Python does not enforce this at runtime. For
        a TRUTHY non-string value like the int 42, `not 42` is False, so
        the guard clause does NOT short-circuit - execution proceeds to
        `content.strip()`, which does not exist on int, raising
        AttributeError. This proves the None-handling above is a genuine
        consequence of None being falsy (and thus caught by the `not
        content` guard before any attribute access), not evidence that
        this function safely handles all non-string input in general -
        only falsy, no-strip-method inputs are safe; truthy non-string
        inputs still crash."""
        with pytest.raises(AttributeError):
            validate_prompt_content(42)

    def test_non_string_truthy_list_input_raises_attributeerror(self):
        """Second, independent example of the same crash class as above,
        using a non-empty list instead of an int - confirms the
        AttributeError is a general consequence of any truthy object
        lacking a `.strip()` method, not specific to numeric types."""
        with pytest.raises(AttributeError):
            validate_prompt_content(["not", "a", "string"])

    def test_falsy_non_string_input_returns_false_without_raising(self):
        """Complement of the None case: any FALSY non-string value (not
        just None) is caught by the `not content` guard before
        `.strip()` is reached. An empty list is falsy in Python, so
        validate_prompt_content([]) must return False gracefully, the
        same as None and "" - reinforcing that the guard's protection is
        keyed on falsiness in general, not a None-specific special
        case."""
        result = validate_prompt_content([])

        assert result is False

    # ---- Return type -------------------------------------------------------

    def test_return_type_is_a_genuine_bool_for_true_case(self):
        """docstring: "Returns: bool: True if ..." - the return value for
        a valid case must be an actual bool instance (Python's `>=`
        comparison on the final line returns a genuine bool), not merely
        a truthy non-bool value."""
        result = validate_prompt_content("Well over ten characters long")

        assert isinstance(result, bool)

    def test_return_type_is_a_genuine_bool_for_false_case(self):
        """The False case (via the early-return guard clause, which
        returns the literal `False`) must also be a genuine bool
        instance."""
        result = validate_prompt_content("")

        assert isinstance(result, bool)


class TestExtractVariables:
    """Tests for app.utils.extract_variables.

    Source of intended behavior: extract_variables's own docstring in
    app/utils.py -

        "Extract template variables from prompt content.

        Variables are in the format {{variable_name}}.

        Args:
            content (str): The prompt content to scan for variables.

        Returns:
            List[str]: The variable names found, in order of appearance,
                without the surrounding braces. Empty if none are found.

        Example:
            >>> extract_variables("Hello {{name}}, welcome to {{place}}!")
            ['name', 'place']"

    No written spec (see module docstring above) covers this function
    directly; the function's own docstring is treated as the sole
    intended-behavior source, per instructions - explicitly noted here.
    The implementation is:

        import re
        pattern = r'\\{\\{(\\w+)\\}\\}'
        return re.findall(pattern, content)

    Dead-code note: like validate_prompt_content, this function is not
    imported or called anywhere in app/api.py or elsewhere in the
    application (verified via `grep -rn "extract_variables"
    backend/app/ backend/tests/`, which matches only this function's own
    definition and its own docstring's doctest example in app/utils.py
    itself; `app/api.py`'s `from app.utils import ...` line names only
    sort_prompts_by_date, filter_prompts_by_collection, and
    search_prompts). This is the second of app/utils.py's four functions
    confirmed dead/orphaned in this session-series. It is still tested
    below since it is public, documented, directly callable logic and
    was the explicit target of this session.

    This function's matching semantics are governed entirely by the
    regex pattern `\\{\\{(\\w+)\\}\\}` - unlike the other three functions in
    this module (which operate on List[Prompt] via plain attribute
    access/comparison), this one is regex-driven, giving it a distinct
    edge-case surface: duplicate-match preservation, non-word-character
    exclusion, malformed/unbalanced braces, and nested-brace matching.
    All non-obvious cases below were verified empirically against a
    plain `re.findall(r'\\{\\{(\\w+)\\}\\}', ...)` call before being
    encoded as assertions, per the docstring's own stated contract
    (order of appearance, no explicit dedup guarantee, no explicit
    validation of "word-like" braces content).
    """

    # ---- Basic single variable -------------------------------------------

    def test_single_variable_extracts_its_name(self):
        """Basic case: one variable in the format {{variable_name}} must
        be extracted as its bare name, without braces."""
        result = extract_variables("Hello {{name}}")

        assert result == ["name"]

    # ---- Multiple variables, order preserved -------------------------------

    def test_multiple_variables_returned_in_order_of_appearance(self):
        """docstring's own Example: "Hello {{name}}, welcome to
        {{place}}!" -> ['name', 'place']. Order of appearance must be
        preserved - not sorted alphabetically, not reversed."""
        result = extract_variables("Hello {{name}}, welcome to {{place}}!")

        assert result == ["name", "place"]

    def test_three_variables_preserve_input_order_not_sorted(self):
        """A third variable, deliberately placed so that alphabetical
        order would differ from appearance order, must still come back
        in appearance order - confirming this isn't accidentally sorted
        (e.g. "zebra" would sort last alphabetically but appears first
        here)."""
        result = extract_variables("{{zebra}} then {{apple}} then {{mango}}")

        assert result == ["zebra", "apple", "mango"]

    # ---- No variables / empty input ----------------------------------------

    def test_plain_text_with_no_variables_returns_empty_list(self):
        """docstring: "Empty if none are found." Plain text containing no
        {{...}} pattern at all must return an empty list."""
        result = extract_variables("This is plain text with no variables at all.")

        assert result == []

    def test_empty_string_returns_empty_list(self):
        """An empty string trivially contains no variables and must
        return an empty list, not raise."""
        result = extract_variables("")

        assert result == []

    # ---- Duplicate variable names -------------------------------------------

    def test_duplicate_variable_name_is_preserved_not_deduplicated(self):
        """docstring says results are returned "in order of appearance"
        with no mention of deduplication. re.findall returns one match
        per occurrence in the string, so the same variable name appearing
        twice must appear twice in the result, verified empirically:
        re.findall(r'\\{\\{(\\w+)\\}\\}', '{{name}} and {{name}} again') ==
        ['name', 'name']."""
        result = extract_variables("{{name}} and {{name}} again")

        assert result == ["name", "name"]

    # ---- Underscore/digit variable names ------------------------------------

    def test_variable_name_with_underscore_extracts_exactly(self):
        """\\w+ matches word characters including underscore - a variable
        name containing an underscore must be extracted exactly, with no
        truncation at the underscore."""
        result = extract_variables("{{my_var}}")

        assert result == ["my_var"]

    def test_variable_name_with_trailing_digit_extracts_exactly(self):
        """\\w+ matches digits too - a variable name ending in a digit
        must be extracted exactly."""
        result = extract_variables("{{var1}}")

        assert result == ["var1"]

    def test_variable_name_with_underscore_and_digit_extracts_exactly(self):
        """Combined underscore-and-digit variable name must be extracted
        exactly, in full."""
        result = extract_variables("{{my_var_2}}")

        assert result == ["my_var_2"]

    def test_variable_name_starting_with_a_digit_still_matches(self):
        """\\w+ has no notion of "valid Python identifier" (which would
        forbid a leading digit) - it only requires one-or-more word
        characters. A variable name starting with a digit, like
        "1abc", is therefore still matched and extracted verbatim, even
        though "1abc" would not be a legal Python/template identifier.
        Verified empirically: re.findall(r'\\{\\{(\\w+)\\}\\}', '{{1abc}}')
        == ['1abc']. This is a deliberate, notable edge case: the
        function does not validate identifier-ness, only character
        class."""
        result = extract_variables("{{1abc}}")

        assert result == ["1abc"]

    # ---- Non-word characters inside braces must NOT match -------------------

    def test_hyphen_inside_braces_does_not_match(self):
        """\\w+ excludes the hyphen character. A variable-looking pattern
        containing a hyphen, {{my-var}}, must NOT match at all (not
        partially match "my" or "var") - verified empirically:
        re.findall(r'\\{\\{(\\w+)\\}\\}', '{{my-var}}') == []."""
        result = extract_variables("{{my-var}}")

        assert result == []

    def test_space_inside_braces_does_not_match(self):
        """\\w+ excludes the space character. {{my var}} must not match -
        verified empirically to yield an empty list, not a partial
        match on "my" or "var"."""
        result = extract_variables("{{my var}}")

        assert result == []

    def test_dot_inside_braces_does_not_match(self):
        """\\w+ excludes the dot character. {{my.var}} must not match -
        verified empirically to yield an empty list."""
        result = extract_variables("{{my.var}}")

        assert result == []

    # ---- Empty braces --------------------------------------------------------

    def test_empty_braces_do_not_match(self):
        """\\w+ requires at least one word character (the `+` quantifier
        is one-or-more, not zero-or-more) - {{}} has zero characters
        between the braces and therefore must NOT match, returning an
        empty list, not an empty-string variable name."""
        result = extract_variables("{{}}")

        assert result == []

    # ---- Malformed braces ------------------------------------------------------

    def test_single_braces_do_not_match(self):
        """The pattern requires DOUBLE braces (\\{\\{...\\}\\}) - a
        single-brace pattern {name} must not match at all."""
        result = extract_variables("{name}")

        assert result == []

    def test_unbalanced_missing_closing_brace_does_not_match(self):
        """{{name} has two opening braces but only one closing brace -
        the pattern requires exactly \\}\\} (two closing braces), so this
        must not match. Verified empirically:
        re.findall(r'\\{\\{(\\w+)\\}\\}', '{{name}') == []."""
        result = extract_variables("{{name}")

        assert result == []

    def test_unbalanced_missing_opening_brace_does_not_match(self):
        """{name}} has only one opening brace but two closing braces -
        the pattern requires exactly \\{\\{ (two opening braces), so this
        must not match either. Verified empirically:
        re.findall(r'\\{\\{(\\w+)\\}\\}', '{name}}') == []."""
        result = extract_variables("{name}}")

        assert result == []

    # ---- Nested/doubled braces --------------------------------------------------

    def test_quadruple_braces_extract_the_inner_name_exactly_once(self):
        """{{{{name}}}} has four opening and four closing braces around
        "name". Verified empirically that re.findall(
        r'\\{\\{(\\w+)\\}\\}', '{{{{name}}}}') == ['name'] - the regex
        engine scans left-to-right and greedily consumes the first two
        `{` characters it finds as the literal \\{\\{ prefix (the outer
        two of the four), then \\w+ matches "name", then the next two `}`
        characters satisfy the literal \\}\\} suffix (the first two of the
        four trailing braces). This leaves the pattern with no further
        {{...}} to match in the two braces still left over on each side
        (they're consumed as plain leftover characters, not re-scanned
        as a second nested match), so exactly one match is produced, not
        two and not zero."""
        result = extract_variables("{{{{name}}}}")

        assert result == ["name"]

    # ---- Adjacent variables with no separator --------------------------------

    def test_adjacent_variables_with_no_separator_both_extracted_separately(self):
        """{{a}}{{b}} has two variables directly adjacent, with no space
        or other separator between them. Both must be extracted as
        separate matches, in order - not merged into one match and not
        missed."""
        result = extract_variables("{{a}}{{b}}")

        assert result == ["a", "b"]

    # ---- Determinism / purity --------------------------------------------------

    def test_same_input_called_twice_produces_identical_results(self):
        """The function does a local `import re` on every call (module
        caching makes this cheap) and has no other state - calling it
        twice with the same input must produce the same result both
        times, confirming it is pure/deterministic with no hidden state
        leaking between calls."""
        content = "Hello {{name}}, welcome to {{place}}!"

        first_call = extract_variables(content)
        second_call = extract_variables(content)

        assert first_call == ["name", "place"]
        assert second_call == ["name", "place"]
        assert first_call == second_call

    # ---- Return type ------------------------------------------------------------

    def test_return_type_is_a_genuine_list(self):
        """docstring: "Returns: List[str]" - the return value must be an
        actual list instance for a non-empty match."""
        result = extract_variables("{{name}}")

        assert isinstance(result, list)

    def test_return_type_is_a_genuine_list_for_no_matches(self):
        """The no-match case must also return a genuine (empty) list,
        not None."""
        result = extract_variables("no variables here")

        assert isinstance(result, list)

    def test_return_elements_are_plain_strings_not_tuples(self):
        """The pattern r'\\{\\{(\\w+)\\}\\}' has exactly one capture group.
        re.findall returns a list of tuples ONLY when the pattern has
        two-or-more capture groups; with exactly one group, it returns a
        list of plain strings (the captured group's text directly) - a
        common re.findall gotcha worth pinning down explicitly. Each
        element of the result must be a str, never a tuple."""
        result = extract_variables("{{a}} and {{b}}")

        assert all(isinstance(item, str) for item in result)
        assert all(not isinstance(item, tuple) for item in result)

    # ---- Error conditions ---------------------------------------------
    # The function's type hint declares `content: str`. Passing values
    # that violate this hint is a contract violation by the *caller*, not
    # a documented behavior of extract_variables itself. re.findall
    # requires a string-or-bytes-like `content` argument (its second
    # positional parameter, the string to scan) - passing None or a
    # non-string, non-bytes value raises TypeError, a DIFFERENT
    # exception class and failure point than validate_prompt_content's
    # graceful `False`-return-on-None (see TestValidatePromptContent
    # above) and than the AttributeError/TypeError profiles of the three
    # List[Prompt]-based functions (see their own Error conditions
    # sections above) - explicitly contrasted in the final report.

    def test_none_content_raises_typeerror(self):
        """re.findall(pattern, content) requires content to be a string
        or bytes-like object. Passing None must raise TypeError (NOT
        return False/[] gracefully, and NOT AttributeError) - verified
        empirically: re.findall(r'\\{\\{(\\w+)\\}\\}', None) raises
        `TypeError: expected string or bytes-like object`. This is a
        materially different error profile than
        validate_prompt_content(None), which returns False gracefully
        via its `not content` guard clause - extract_variables has no
        such guard, so None propagates straight into re.findall and
        crashes."""
        with pytest.raises(TypeError):
            extract_variables(None)

    def test_non_string_int_content_raises_typeerror(self):
        """A non-string, non-None, non-bytes value (e.g. the int 42)
        also fails re's string-or-bytes-like requirement and must raise
        TypeError for the same underlying reason as the None case above -
        confirming the failure is general to "not a string/bytes value",
        not specific to None."""
        with pytest.raises(TypeError):
            extract_variables(42)

    def test_non_string_list_content_raises_typeerror(self):
        """Second, independent example of the same crash class as above,
        using a list instead of an int - confirms the TypeError is a
        general consequence of any non-string/non-bytes object being
        passed to re.findall, not specific to numeric types."""
        with pytest.raises(TypeError):
            extract_variables(["not", "a", "string"])
