"""FastAPI routes for PromptLab"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.models import (
    Prompt, PromptCreate, PromptUpdate, PromptPatch,
    Collection, CollectionCreate,
    PromptList, CollectionList, HealthResponse,
    get_current_time
)
from app.storage import storage
from app.utils import sort_prompts_by_date, filter_prompts_by_collection, search_prompts
from app import __version__


app = FastAPI(
    title="PromptLab API",
    description="AI Prompt Engineering Platform",
    version=__version__
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Health Check ==============

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Report the API's current health status and version.

    Returns:
        HealthResponse: An object with status set to "healthy" and the
            running application version.

    Example:
        >>> health_check()
        HealthResponse(status='healthy', version='1.0.0')
    """
    return HealthResponse(status="healthy", version=__version__)


# ============== Prompt Endpoints ==============

@app.get("/prompts", response_model=PromptList)
def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None
):
    """List prompts, optionally filtered by collection and/or search text.

    Results are sorted by creation date, newest first.

    Args:
        collection_id (Optional[str]): If provided, only prompts belonging
            to this collection are included.
        search (Optional[str]): If provided, only prompts whose title or
            description contain this text (case-insensitive) are included.

    Returns:
        PromptList: The matching prompts and the total count.

    Example:
        >>> list_prompts(search="email")
        PromptList(prompts=[...], total=2)
    """
    prompts = storage.get_all_prompts()
    
    # Filter by collection if specified
    if collection_id:
        prompts = filter_prompts_by_collection(prompts, collection_id)
    
    # Search if query provided
    if search:
        prompts = search_prompts(prompts, search)
    
    # Sort by date (newest first)
    # Note: There might be an issue with the sorting...
    prompts = sort_prompts_by_date(prompts, descending=True)
    
    return PromptList(prompts=prompts, total=len(prompts))


@app.get("/prompts/{prompt_id}", response_model=Prompt)
def get_prompt(prompt_id: str):
    """Retrieve a prompt by a unique identifier/
    Args:
        prompt_id: The unique identifier fo the prompt to retrieve.
    Returns:
        The prompt if found, raises exception otherwise.
    Raises: 
        HTTPException: If prompt_id is not found.
    """
    prompt = storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt.

    Args:
        prompt_data (PromptCreate): The title, content, and optional
            description and collection_id for the new prompt.

    Returns:
        Prompt: The newly created prompt, with a generated id and
            creation/update timestamps.

    Raises:
        HTTPException: With status 400 if prompt_data.collection_id is
            provided but does not correspond to an existing collection.

    Example:
        >>> create_prompt(PromptCreate(title="Greeting", content="Hello!"))
        Prompt(id='...', title='Greeting', content='Hello!', ...)
    """
    # Validate collection exists if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")
    
    prompt = Prompt(**prompt_data.model_dump())
    return storage.create_prompt(prompt)


@app.put("/prompts/{prompt_id}", response_model=Prompt)
def update_prompt(prompt_id: str, prompt_data: PromptUpdate):
    """Updates an existing prompt by its ID with new field values.

    Preserves the original prompt's ID and creation timestamp. The
    updated_at timestamp is set to the current time.

    Args:
        prompt_id: The unique identifier of the prompt to update.
        prompt_data: A PromptUpdate object containing the new title,
            content, description, and optional collection_id.

    Returns:
        The updated Prompt object as persisted by storage.

    Raises:
        HTTPException: With status 404 if no prompt with prompt_id exists.
        HTTPException: With status 400 if prompt_data.collection_id is
            provided but does not correspond to an existing collection.
    """
    existing = storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    # Validate collection if provided
    if prompt_data.collection_id:
        collection = storage.get_collection(prompt_data.collection_id)
        if not collection:
            raise HTTPException(status_code=400, detail="Collection not found")
    
    updated_prompt = Prompt(
        id=existing.id,
        title=prompt_data.title,
        content=prompt_data.content,
        description=prompt_data.description,
        collection_id=prompt_data.collection_id,
        created_at=existing.created_at,
        updated_at=get_current_time()
    )
    
    return storage.update_prompt(prompt_id, updated_prompt)


@app.patch("/prompts/{prompt_id}", response_model=Prompt)
def patch_prompt(prompt_id: str, prompt_data: PromptPatch):
    """Partially updates an existing prompt, changing only the provided fields.

    Fields omitted from the request body are left unchanged. The updated_at
    timestamp is always refreshed on a successful update.

    Args:
        prompt_id: The unique identifier of the prompt to update.
        prompt_data: A PromptPatch object containing any subset of title,
            content, description, and collection_id to update.

    Returns:
        The updated Prompt object as persisted by storage.

    Raises:
        HTTPException: With status 404 if no prompt with prompt_id exists.
        HTTPException: With status 400 if collection_id is explicitly provided
            and does not correspond to an existing collection.
    """
    existing = storage.get_prompt(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    patch = prompt_data.model_dump(exclude_unset=True)

    if "collection_id" in patch and patch["collection_id"] is not None:
        if not storage.get_collection(patch["collection_id"]):
            raise HTTPException(status_code=400, detail="Collection not found")

    updated_prompt = Prompt(
        id=existing.id,
        title=patch.get("title", existing.title),
        content=patch.get("content", existing.content),
        description=patch.get("description", existing.description),
        collection_id=patch.get("collection_id", existing.collection_id),
        created_at=existing.created_at,
        updated_at=get_current_time()
    )
    return storage.update_prompt(prompt_id, updated_prompt)


@app.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str):
    """Delete a prompt by its unique identifier.

    Args:
        prompt_id (str): The unique identifier of the prompt to delete.

    Returns:
        None: No content is returned on successful deletion.

    Raises:
        HTTPException: With status 404 if no prompt with prompt_id exists.

    Example:
        >>> delete_prompt("abc-123")
    """
    if not storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Collection Endpoints ==============

@app.get("/collections", response_model=CollectionList)
def list_collections():
    """List all collections.

    Returns:
        CollectionList: All stored collections and the total count.

    Example:
        >>> list_collections()
        CollectionList(collections=[...], total=3)
    """
    collections = storage.get_all_collections()
    return CollectionList(collections=collections, total=len(collections))


@app.get("/collections/{collection_id}", response_model=Collection)
def get_collection(collection_id: str):
    """Retrieve a collection by its unique identifier.

    Args:
        collection_id (str): The unique identifier of the collection to
            retrieve.

    Returns:
        Collection: The matching collection.

    Raises:
        HTTPException: With status 404 if no collection with collection_id
            exists.

    Example:
        >>> get_collection("abc-123")
        Collection(id='abc-123', name='My Collection', ...)
    """
    collection = storage.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@app.post("/collections", response_model=Collection, status_code=201)
def create_collection(collection_data: CollectionCreate):
    """Create a new collection.

    Args:
        collection_data (CollectionCreate): The name and optional
            description for the new collection.

    Returns:
        Collection: The newly created collection, with a generated id and
            creation timestamp.

    Example:
        >>> create_collection(CollectionCreate(name="My Collection"))
        Collection(id='...', name='My Collection', ...)
    """
    collection = Collection(**collection_data.model_dump())
    return storage.create_collection(collection)


@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
    """Delete a collection by its unique identifier.

    Any prompts assigned to this collection are unassigned (their
    collection_id is set to None) rather than deleted, before the
    collection itself is removed.

    Args:
        collection_id (str): The unique identifier of the collection to
            delete.

    Returns:
        None: No content is returned on successful deletion.

    Raises:
        HTTPException: With status 404 if no collection with collection_id
            exists.

    Example:
        >>> delete_collection("abc-123")
    """
    if not storage.get_collection(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    for prompt in storage.get_prompts_by_collection(collection_id):
        storage.update_prompt(prompt.id, Prompt(
            id=prompt.id,
            title=prompt.title,
            content=prompt.content,
            description=prompt.description,
            collection_id=None,
            created_at=prompt.created_at,
            updated_at=get_current_time()
        ))

    storage.delete_collection(collection_id)
    return None
