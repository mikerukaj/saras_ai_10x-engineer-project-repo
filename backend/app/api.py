"""FastAPI routes for PromptLab"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from app.models import (
    Prompt, PromptCreate, PromptUpdate,
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
    return HealthResponse(status="healthy", version=__version__)


# ============== Prompt Endpoints ==============

@app.get("/prompts", response_model=PromptList)
def list_prompts(
    collection_id: Optional[str] = None,
    search: Optional[str] = None
):
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
        The prompt if found, None otherwise.
    Raises: 
        HTTPException: If prompt_id is empty or invalid.
    """
    prompt = storage.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@app.post("/prompts", response_model=Prompt, status_code=201)
def create_prompt(prompt_data: PromptCreate):
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


# NOTE: PATCH endpoint is missing! Students need to implement this.
# It should allow partial updates (only update provided fields)


@app.delete("/prompts/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str):
    if not storage.delete_prompt(prompt_id):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return None


# ============== Collection Endpoints ==============

@app.get("/collections", response_model=CollectionList)
def list_collections():
    collections = storage.get_all_collections()
    return CollectionList(collections=collections, total=len(collections))


@app.get("/collections/{collection_id}", response_model=Collection)
def get_collection(collection_id: str):
    collection = storage.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@app.post("/collections", response_model=Collection, status_code=201)
def create_collection(collection_data: CollectionCreate):
    collection = Collection(**collection_data.model_dump())
    return storage.create_collection(collection)


@app.delete("/collections/{collection_id}", status_code=204)
def delete_collection(collection_id: str):
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
