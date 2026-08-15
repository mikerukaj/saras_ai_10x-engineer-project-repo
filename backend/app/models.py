"""Pydantic models for PromptLab"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import uuid4


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
    pass


class PromptUpdate(PromptBase):
    pass


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

    Example:
        >>> patch = PromptPatch(title="Updated Title")
        >>> patch.title
        'Updated Title'
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    collection_id: Optional[str] = None


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

    Example:
        >>> prompt = Prompt(title="Greeting", content="Hello, world!")
        >>> prompt.title
        'Greeting'
    """

    id: str = Field(default_factory=generate_id)
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)

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
