"""Pydantic models for PromptLab"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def generate_id() -> str:
    """Generate a unique identifier string.

    Returns:
        str: A newly generated UUID4 value, formatted as a string.

    Example:
        >>> new_id = generate_id()
        >>> len(new_id)
        36
    """
    return str(uuid4())


def get_current_time() -> datetime:
    """Get the current UTC date and time.

    Returns:
        datetime: The current date and time in UTC.

    Example:
        >>> now = get_current_time()
        >>> isinstance(now, datetime)
        True
    """
    return datetime.utcnow()


def _validate_tag_names(names: Optional[List[str]]) -> Optional[List[str]]:
    """Trim and validate each tag name in a list of tag names supplied on
    a prompt create/update/patch (as distinct from the standalone Tag
    entity's own name validation on TagBase).

    Args:
        names (Optional[List[str]]): The raw tag name strings to validate,
            or None if no tags were supplied.

    Returns:
        Optional[List[str]]: The trimmed tag names, or None if names was
            None.

    Raises:
        ValueError: If any name is empty after trimming, or exceeds 50
            characters after trimming.
    """
    if names is None:
        return None
    validated = []
    for name in names:
        stripped = name.strip()
        if not stripped:
            raise ValueError("tag names must not be empty or whitespace-only")
        if len(stripped) > 50:
            raise ValueError("tag names must be at most 50 characters")
        validated.append(stripped)
    return validated


# ============== Tag Models ==============

class TagBase(BaseModel):
    """Base schema holding the field shared by tag models.

    Attributes:
        name (str): The tag's name, 1-50 characters after trimming
            surrounding whitespace, unique case-insensitively.

    Example:
        >>> base = TagBase(name="marketing")
        >>> base.name
        'marketing'
    """

    name: str = Field(...)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Trim name and reject it if empty or too long after trimming."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be empty or whitespace-only")
        if len(stripped) > 50:
            raise ValueError("name must be at most 50 characters")
        return stripped


class TagCreate(TagBase):
    pass


class TagRename(TagBase):
    pass


class Tag(TagBase):
    """Full tag schema, including server-generated fields.

    Attributes:
        name (str): The tag's name, 1-50 characters after trimming.
        id (str): The tag's unique identifier, generated automatically.
        created_at (datetime): The UTC timestamp when the tag was
            created, set automatically.
        prompt_count (int): The number of prompts currently carrying this
            tag. Computed, not stored - populated wherever tags are
            listed.

    Example:
        >>> tag = Tag(name="marketing")
        >>> tag.prompt_count
        0
    """

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)
    prompt_count: int = 0

    class Config:
        from_attributes = True


class TagList(BaseModel):
    """Response schema for the full list of tags in use.

    Attributes:
        tags (List[Tag]): Every tag currently in use.
        total (int): The total number of tags.

    Example:
        >>> result = TagList(tags=[], total=0)
        >>> result.total
        0
    """

    tags: List[Tag]
    total: int


# ============== Prompt Models ==============

class PromptBase(BaseModel):
    """Base schema holding the common fields shared by prompt models.

    Attributes:
        title (str): The prompt's title, between 1 and 200 characters.
        content (str): The prompt's text content, at least 1 character.
        description (Optional[str]): An optional description, up to 500
            characters.
        collection_id (Optional[str]): The identifier of the collection
            this prompt belongs to, if any.

    Example:
        >>> base = PromptBase(title="Greeting", content="Hello, world!")
        >>> base.title
        'Greeting'
    """

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None


class PromptCreate(PromptBase):
    """Extends PromptBase with an optional list of tag names to attach.

    Attributes:
        tags (Optional[List[str]]): Tag names to attach to the new
            prompt, resolved via case-insensitive get-or-create. Omitting
            this field means the prompt is created with no tags.
    """

    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_tag_names(v)


class PromptUpdate(PromptBase):
    """Extends PromptBase with an optional list of tag names, full-replace.

    Attributes:
        tags (Optional[List[str]]): The prompt's complete tag set after
            this update, resolved via case-insensitive get-or-create.
            Omitting this field means the prompt ends up with no tags
            (full replace, matching the rest of PUT's semantics).
    """

    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_tag_names(v)


class PromptPatch(BaseModel):
    """Schema for partially updating a prompt, with all fields optional.

    Attributes:
        title (Optional[str]): The prompt's new title, between 1 and 200
            characters, if being updated.
        content (Optional[str]): The prompt's new text content, at least
            1 character, if being updated.
        description (Optional[str]): The prompt's new description, up to
            500 characters, if being updated.
        collection_id (Optional[str]): The identifier of the collection
            to move this prompt into, if being updated.
        tags (Optional[List[str]]): The prompt's complete tag set after
            this patch, resolved via case-insensitive get-or-create.
            Omitting this field entirely leaves the prompt's tags
            unchanged; including it (even as []) fully replaces them.

    Example:
        >>> patch = PromptPatch(title="Updated Title")
        >>> patch.title
        'Updated Title'
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _validate_tag_names(v)


class Prompt(PromptBase):
    """Full prompt schema, including server-generated fields.

    Attributes:
        title (str): The prompt's title, between 1 and 200 characters.
        content (str): The prompt's text content, at least 1 character.
        description (Optional[str]): An optional description, up to 500
            characters.
        collection_id (Optional[str]): The identifier of the collection
            this prompt belongs to, if any.
        id (str): The prompt's unique identifier, generated automatically.
        created_at (datetime): The UTC timestamp when the prompt was
            created, set automatically.
        updated_at (datetime): The UTC timestamp when the prompt was last
            updated, set automatically.
        tags (List[Tag]): The prompt's currently-attached tags, embedded
            in full. Defaults to an empty list.

    Example:
        >>> prompt = Prompt(title="Greeting", content="Hello, world!")
        >>> prompt.title
        'Greeting'
    """

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)
    tags: List[Tag] = Field(default_factory=list)

    class Config:
        """Pydantic configuration for the Prompt model.

        Attributes:
            from_attributes (bool): When True, allows the model to be
                populated from an object's attributes (e.g. an ORM
                instance) rather than only from a dict.

        Example:
            >>> Prompt.Config.from_attributes
            True
        """

        from_attributes = True


# ============== Prompt Version Models ==============

class PromptVersion(BaseModel):
    """A historical snapshot of a prompt's wording.

    Attributes:
        id (str): The version's unique identifier, generated automatically.
        prompt_id (str): The identifier of the prompt this version
            belongs to.
        version_number (int): The version's sequential position among the
            prompt's versions, starting at 1 and never reused.
        title (str): The prompt's title at the time this version was
            captured.
        content (str): The prompt's content at the time this version was
            captured.
        description (Optional[str]): The prompt's description at the
            time this version was captured.
        label (Optional[str]): An optional user-supplied note; only set
            on manually-checkpointed versions.
        created_at (datetime): The UTC timestamp when this version was
            captured, set automatically.

    Example:
        >>> version = PromptVersion(prompt_id="abc-123", version_number=1,
        ...     title="Greeting", content="Hello, world!")
        >>> version.version_number
        1
    """

    id: str = Field(default_factory=generate_id)
    prompt_id: str
    version_number: int
    title: str
    content: str
    description: Optional[str] = None
    label: Optional[str] = None
    created_at: datetime = Field(default_factory=get_current_time)


class PromptVersionCreate(BaseModel):
    """Schema for manually saving a labeled checkpoint of a prompt.

    Attributes:
        label (Optional[str]): An optional note describing this
            checkpoint, up to 100 characters.

    Example:
        >>> checkpoint = PromptVersionCreate(label="before shortening")
        >>> checkpoint.label
        'before shortening'
    """

    label: Optional[str] = Field(None, max_length=100)


class PromptVersionList(BaseModel):
    """Response schema for a prompt's version history.

    Attributes:
        versions (List[PromptVersion]): The prompt's versions.
        total (int): The total number of versions.

    Example:
        >>> result = PromptVersionList(versions=[], total=0)
        >>> result.total
        0
    """

    versions: List[PromptVersion]
    total: int


# ============== Collection Models ==============

class CollectionBase(BaseModel):
    """Base schema holding the common fields shared by collection models.

    Attributes:
        name (str): The collection's name, between 1 and 100 characters.
        description (Optional[str]): An optional description, up to 500
            characters.

    Example:
        >>> base = CollectionBase(name="My Collection")
        >>> base.name
        'My Collection'
    """

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CollectionCreate(CollectionBase):
    pass


class Collection(CollectionBase):
    """Full collection schema, including server-generated fields.

    Attributes:
        name (str): The collection's name, between 1 and 100 characters.
        description (Optional[str]): An optional description, up to 500
            characters.
        id (str): The collection's unique identifier, generated
            automatically.
        created_at (datetime): The UTC timestamp when the collection was
            created, set automatically.

    Example:
        >>> collection = Collection(name="My Collection")
        >>> collection.name
        'My Collection'
    """

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)

    class Config:
        """Pydantic configuration for the Collection model.

        Attributes:
            from_attributes (bool): When True, allows the model to be
                populated from an object's attributes (e.g. an ORM
                instance) rather than only from a dict.

        Example:
            >>> Collection.Config.from_attributes
            True
        """

        from_attributes = True


# ============== Response Models ==============

class PromptList(BaseModel):
    """Response schema for a paginated or filtered list of prompts.

    Attributes:
        prompts (List[Prompt]): The list of prompts being returned.
        total (int): The total number of prompts matching the query.

    Example:
        >>> result = PromptList(prompts=[], total=0)
        >>> result.total
        0
    """

    prompts: List[Prompt]
    total: int


class CollectionList(BaseModel):
    """Response schema for a paginated or filtered list of collections.

    Attributes:
        collections (List[Collection]): The list of collections being
            returned.
        total (int): The total number of collections matching the query.

    Example:
        >>> result = CollectionList(collections=[], total=0)
        >>> result.total
        0
    """

    collections: List[Collection]
    total: int


class HealthResponse(BaseModel):
    """Response schema for the API health check endpoint.

    Attributes:
        status (str): The current health status of the service.
        version (str): The running version of the service.

    Example:
        >>> health = HealthResponse(status="ok", version="1.0.0")
        >>> health.status
        'ok'
    """

    status: str
    version: str
