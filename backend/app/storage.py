"""In-memory storage for PromptLab

This module provides simple in-memory storage for prompts and collections.
In a production environment, this would be replaced with a database.
"""

from typing import Dict, List, Optional, Set

from app.models import Collection, Prompt, PromptVersion, Tag


class Storage:
    """In-memory store for prompts, collections, and prompt versions.

    Holds prompts, collections, and prompt versions in dictionaries keyed
    by their id, and provides basic create/read/update/delete operations
    for each. Data exists only for the lifetime of the process; nothing
    is persisted to disk.

    Attributes:
        _prompts (Dict[str, Prompt]): Prompts keyed by their id.
        _collections (Dict[str, Collection]): Collections keyed by their
            id.
        _versions (Dict[str, PromptVersion]): Prompt versions keyed by
            their id.
        _tags (Dict[str, Tag]): Tags keyed by their id.
        _prompt_tags (Dict[str, Set[str]]): Tag id sets keyed by prompt
            id, representing the Prompt<->Tag many-to-many relationship.

    Example:
        >>> storage = Storage()
        >>> storage.create_collection(Collection(name="My Collection"))
        Collection(id='...', name='My Collection', ...)
    """

    def __init__(self):
        """Initialize empty in-memory stores for prompts, collections,
        prompt versions, and tags.

        Returns:
            None

        Example:
            >>> storage = Storage()
            >>> storage.get_all_prompts()
            []
        """
        self._prompts: Dict[str, Prompt] = {}
        self._collections: Dict[str, Collection] = {}
        self._versions: Dict[str, PromptVersion] = {}
        self._tags: Dict[str, Tag] = {}
        self._prompt_tags: Dict[str, Set[str]] = {}
    
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

    # ============== Prompt Version Operations ==============

    def create_version(
        self,
        prompt_id: str,
        title: str,
        content: str,
        description: Optional[str] = None,
        label: Optional[str] = None,
    ) -> PromptVersion:
        """Capture a new version snapshot for a prompt.

        Args:
            prompt_id (str): The unique identifier of the prompt this
                version belongs to.
            title (str): The prompt's title at the time of capture.
            content (str): The prompt's content at the time of capture.
            description (Optional[str]): The prompt's description at the
                time of capture.
            label (Optional[str]): An optional user-supplied note, for a
                manually-saved checkpoint.

        Returns:
            PromptVersion: The newly created version, with version_number
                set to one more than the highest existing version for
                prompt_id (or 1 if none exist yet).

        Example:
            >>> storage = Storage()
            >>> storage.create_version("prompt-1", "Greeting", "Hi")
            PromptVersion(prompt_id='prompt-1', version_number=1, ...)
        """
        next_number = max(
            (v.version_number for v in self.get_versions_by_prompt(prompt_id)),
            default=0,
        ) + 1
        version = PromptVersion(
            prompt_id=prompt_id,
            version_number=next_number,
            title=title,
            content=content,
            description=description,
            label=label,
        )
        self._versions[version.id] = version
        return version

    def get_version(self, version_id: str) -> Optional[PromptVersion]:
        """Retrieve a single version by its id.

        Args:
            version_id (str): The unique identifier of the version to
                retrieve.

        Returns:
            Optional[PromptVersion]: The matching version, or None if no
                version with version_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.get_version("missing-id")
        """
        return self._versions.get(version_id)

    def get_versions_by_prompt(self, prompt_id: str) -> List[PromptVersion]:
        """Retrieve all versions belonging to a given prompt.

        Args:
            prompt_id (str): The unique identifier of the prompt whose
                versions should be retrieved.

        Returns:
            List[PromptVersion]: The versions whose prompt_id matches
                prompt_id, in no particular order.

        Example:
            >>> storage = Storage()
            >>> storage.get_versions_by_prompt("missing-id")
            []
        """
        return [v for v in self._versions.values() if v.prompt_id == prompt_id]

    def delete_version(self, version_id: str) -> bool:
        """Delete a version by its id.

        Args:
            version_id (str): The unique identifier of the version to
                delete.

        Returns:
            bool: True if the version was found and deleted, False if no
                version with version_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.delete_version("missing-id")
            False
        """
        if version_id in self._versions:
            del self._versions[version_id]
            return True
        return False

    def delete_versions_by_prompt(self, prompt_id: str) -> None:
        """Delete every version belonging to a given prompt.

        Args:
            prompt_id (str): The unique identifier of the prompt whose
                versions should all be deleted.

        Returns:
            None

        Example:
            >>> storage = Storage()
            >>> storage.delete_versions_by_prompt("missing-id")
        """
        for version in self.get_versions_by_prompt(prompt_id):
            self.delete_version(version.id)

    # ============== Tag Operations ==============

    def create_tag(self, name: str) -> Tag:
        """Store a new tag.

        Args:
            name (str): The new tag's name. Not checked for a
                case-insensitive collision here - callers that need that
                (explicit tag creation) must check via
                get_tag_by_name_case_insensitive first.

        Returns:
            Tag: The newly created tag, with prompt_count 0.

        Example:
            >>> storage = Storage()
            >>> storage.create_tag("marketing")
            Tag(id='...', name='marketing', prompt_count=0, ...)
        """
        tag = Tag(name=name)
        self._tags[tag.id] = tag
        return tag

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """Retrieve a single tag by its id, with its current prompt_count.

        Args:
            tag_id (str): The unique identifier of the tag to retrieve.

        Returns:
            Optional[Tag]: The matching tag, or None if no tag with
                tag_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.get_tag("missing-id")
        """
        tag = self._tags.get(tag_id)
        if tag is None:
            return None
        return self._tag_with_count(tag)

    def get_tag_by_name_case_insensitive(self, name: str) -> Optional[Tag]:
        """Retrieve a tag whose name matches name, ignoring case.

        Args:
            name (str): The tag name to match case-insensitively.

        Returns:
            Optional[Tag]: The matching tag, or None if no tag with that
                name (in any capitalization) exists.

        Example:
            >>> storage = Storage()
            >>> storage.create_tag("Marketing")
            >>> storage.get_tag_by_name_case_insensitive("marketing")
            Tag(name='Marketing', ...)
        """
        lowered = name.lower()
        for tag in self._tags.values():
            if tag.name.lower() == lowered:
                return tag
        return None

    def get_all_tags_with_counts(self) -> List[Tag]:
        """Retrieve every tag currently in use, each with its prompt_count.

        Returns:
            List[Tag]: Every stored tag, in no particular order.

        Example:
            >>> storage = Storage()
            >>> storage.get_all_tags_with_counts()
            []
        """
        return [self._tag_with_count(tag) for tag in self._tags.values()]

    def rename_tag(self, tag_id: str, new_name: str) -> Optional[Tag]:
        """Rename an existing tag.

        Does not check for a name collision - callers that need that
        must check via get_tag_by_name_case_insensitive first.

        Args:
            tag_id (str): The unique identifier of the tag to rename.
            new_name (str): The tag's new name.

        Returns:
            Optional[Tag]: The renamed tag with its current prompt_count,
                or None if no tag with tag_id exists.

        Example:
            >>> storage = Storage()
            >>> tag = storage.create_tag("markting")
            >>> storage.rename_tag(tag.id, "marketing")
            Tag(name='marketing', ...)
        """
        tag = self._tags.get(tag_id)
        if tag is None:
            return None
        renamed = tag.model_copy(update={"name": new_name})
        self._tags[tag_id] = renamed
        return self._tag_with_count(renamed)

    def delete_tag(self, tag_id: str) -> bool:
        """Delete a tag by its id, unlinking it from every prompt that
        carried it (without deleting those prompts).

        Args:
            tag_id (str): The unique identifier of the tag to delete.

        Returns:
            bool: True if the tag was found and deleted, False if no tag
                with tag_id exists.

        Example:
            >>> storage = Storage()
            >>> storage.delete_tag("missing-id")
            False
        """
        if tag_id not in self._tags:
            return False
        del self._tags[tag_id]
        for tag_ids in self._prompt_tags.values():
            tag_ids.discard(tag_id)
        return True

    def get_prompt_tags(self, prompt_id: str) -> List[Tag]:
        """Retrieve the tags currently attached to a prompt.

        Args:
            prompt_id (str): The unique identifier of the prompt whose
                tags should be retrieved.

        Returns:
            List[Tag]: The prompt's attached tags, each with its current
                prompt_count, in no particular order.

        Example:
            >>> storage = Storage()
            >>> storage.get_prompt_tags("missing-id")
            []
        """
        tag_ids = self._prompt_tags.get(prompt_id, set())
        return [self._tag_with_count(self._tags[tid]) for tid in tag_ids if tid in self._tags]

    def set_prompt_tags(self, prompt_id: str, tag_names: List[str]) -> List[Tag]:
        """Set a prompt's complete tag set, resolving each name via
        case-insensitive get-or-create.

        Replaces the prompt's entire previous tag set - names left off
        tag_names are detached, matching tags is a full-replace list.
        Duplicate names (including case-only duplicates) resolve to the
        same tag and are deduplicated automatically.

        Args:
            prompt_id (str): The unique identifier of the prompt whose
                tags should be set.
            tag_names (List[str]): The prompt's complete new set of tag
                names. An empty list clears all of the prompt's tags.

        Returns:
            List[Tag]: The prompt's tags after the update.

        Example:
            >>> storage = Storage()
            >>> storage.set_prompt_tags("prompt-1", ["marketing", "draft"])
            [Tag(name='marketing', ...), Tag(name='draft', ...)]
        """
        tag_ids: Set[str] = set()
        for name in tag_names:
            existing = self.get_tag_by_name_case_insensitive(name)
            tag_ids.add(existing.id if existing else self.create_tag(name).id)
        self._prompt_tags[prompt_id] = tag_ids
        return self.get_prompt_tags(prompt_id)

    def remove_prompt_tag_links(self, prompt_id: str) -> None:
        """Remove all of a prompt's tag links, without deleting the Tag
        records themselves (used when the prompt itself is deleted).

        Args:
            prompt_id (str): The unique identifier of the prompt whose
                tag links should be removed.

        Returns:
            None

        Example:
            >>> storage = Storage()
            >>> storage.remove_prompt_tag_links("missing-id")
        """
        self._prompt_tags.pop(prompt_id, None)

    def _tag_with_count(self, tag: Tag) -> Tag:
        """Return a copy of tag with prompt_count set to how many prompts
        currently carry it.

        Args:
            tag (Tag): The tag to compute the current prompt_count for.

        Returns:
            Tag: A copy of tag with prompt_count populated.
        """
        count = sum(1 for tag_ids in self._prompt_tags.values() if tag.id in tag_ids)
        return tag.model_copy(update={"prompt_count": count})

    # ============== Utility ==============

    def clear(self):
        """Remove all stored prompts, collections, prompt versions, and
        tags.

        Resets the in-memory storage to an empty state, discarding all
        prompts, collections, prompt versions, and tags that have been
        created.

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
        self._versions.clear()
        self._tags.clear()
        self._prompt_tags.clear()


# Global storage instance
storage = Storage()
