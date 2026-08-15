"""In-memory storage for PromptLab

This module provides simple in-memory storage for prompts and collections.
In a production environment, this would be replaced with a database.
"""

from typing import Dict, List, Optional
from app.models import Prompt, Collection


class Storage:
    """In-memory store for prompts and collections.

    Holds prompts and collections in dictionaries keyed by their id, and
    provides basic create/read/update/delete operations for each. Data
    exists only for the lifetime of the process; nothing is persisted to
    disk.

    Attributes:
        _prompts (Dict[str, Prompt]): Prompts keyed by their id.
        _collections (Dict[str, Collection]): Collections keyed by their
            id.

    Example:
        >>> storage = Storage()
        >>> storage.create_collection(Collection(name="My Collection"))
        Collection(id='...', name='My Collection', ...)
    """

    def __init__(self):
        """Initialize empty in-memory stores for prompts and collections.

        Returns:
            None

        Example:
            >>> storage = Storage()
            >>> storage.get_all_prompts()
            []
        """
        self._prompts: Dict[str, Prompt] = {}
        self._collections: Dict[str, Collection] = {}
    
    # ============== Prompt Operations ==============
    
    def create_prompt(self, prompt: Prompt) -> Prompt:
        """Store a new prompt.

        Args:
            prompt (Prompt): The prompt to store, keyed by its id.

        Returns:
            Prompt: The stored prompt.

        Example:
            >>> storage = Storage()
            >>> storage.create_prompt(Prompt(title="Greeting", content="Hi"))
            Prompt(id='...', title='Greeting', content='Hi', ...)
        """
        self._prompts[prompt.id] = prompt
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Retrieve a single prompt by its id.

        Args:
            prompt_id (str): The unique identifier of the prompt to
                retrieve.

        Returns:
            Optional[Prompt]: The matching prompt, or None if no prompt
                with prompt_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.get_prompt("missing-id")
        """
        return self._prompts.get(prompt_id)

    def get_all_prompts(self) -> List[Prompt]:
        """Retrieve all stored prompts.

        Returns:
            List[Prompt]: Every prompt currently in storage, in no
                particular order.

        Example:
            >>> storage = Storage()
            >>> storage.get_all_prompts()
            []
        """
        return list(self._prompts.values())
    
    def update_prompt(self, prompt_id: str, prompt: Prompt) -> Optional[Prompt]:
        """Replace an existing prompt with new data.

        Args:
            prompt_id (str): The unique identifier of the prompt to
                update.
            prompt (Prompt): The replacement prompt data to store.

        Returns:
            Optional[Prompt]: The stored prompt, or None if no prompt
                with prompt_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.update_prompt("missing-id", some_prompt)
        """
        if prompt_id not in self._prompts:
            return None
        self._prompts[prompt_id] = prompt
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt by its id.

        Args:
            prompt_id (str): The unique identifier of the prompt to
                delete.

        Returns:
            bool: True if the prompt was found and deleted, False if no
                prompt with prompt_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.delete_prompt("missing-id")
            False
        """
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            return True
        return False
    
    # ============== Collection Operations ==============
    
    def create_collection(self, collection: Collection) -> Collection:
        """Store a new collection.

        Args:
            collection (Collection): The collection to store, keyed by
                its id.

        Returns:
            Collection: The stored collection.

        Example:
            >>> storage = Storage()
            >>> storage.create_collection(Collection(name="My Collection"))
            Collection(id='...', name='My Collection', ...)
        """
        self._collections[collection.id] = collection
        return collection

    def get_collection(self, collection_id: str) -> Optional[Collection]:
        """Retrieve a single collection by its id.

        Args:
            collection_id (str): The unique identifier of the collection
                to retrieve.

        Returns:
            Optional[Collection]: The matching collection, or None if no
                collection with collection_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.get_collection("missing-id")
        """
        return self._collections.get(collection_id)
    
    def get_all_collections(self) -> List[Collection]:
        """Retrieve all stored collections.

        Returns:
            List[Collection]: Every collection currently in storage, in
                no particular order.

        Example:
            >>> storage = Storage()
            >>> storage.get_all_collections()
            []
        """
        return list(self._collections.values())

    def delete_collection(self, collection_id: str) -> bool:
        """Delete a collection by its id.

        Args:
            collection_id (str): The unique identifier of the collection
                to delete.

        Returns:
            bool: True if the collection was found and deleted, False if
                no collection with collection_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.delete_collection("missing-id")
            False
        """
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False
    
    def get_prompts_by_collection(self, collection_id: str) -> List[Prompt]:
        """Retrieve all prompts belonging to a given collection.

        Args:
            collection_id (str): The unique identifier of the collection
                whose prompts should be retrieved.

        Returns:
            List[Prompt]: The prompts whose collection_id matches
                collection_id, in no particular order.

        Example:
            >>> storage = Storage()
            >>> storage.get_prompts_by_collection("missing-id")
            []
        """
        return [p for p in self._prompts.values() if p.collection_id == collection_id]
    
    # ============== Utility ==============
    
    def clear(self):
        """Remove all stored prompts and collections.

        Resets the in-memory storage to an empty state, discarding all
        prompts and collections that have been created.

        Returns:
            None

        Example:
            >>> storage = Storage()
            >>> storage.create_prompt(Prompt(id="1", ...))
            >>> storage.clear()
            >>> storage.get_all_prompts()
            []
        """
        self._prompts.clear()
        self._collections.clear()


# Global storage instance
storage = Storage()
