"""Utility functions for PromptLab"""

from typing import List
from app.models import Prompt


def sort_prompts_by_date(prompts: List[Prompt], descending: bool = True) -> List[Prompt]:
    """Sort prompts by their creation date.

    Args:
        prompts (List[Prompt]): The prompts to sort.
        descending (bool): If True, sort newest first; if False, sort
            oldest first. Defaults to True.

    Returns:
        List[Prompt]: A new list of prompts sorted by created_at.

    Example:
        >>> sort_prompts_by_date([older_prompt, newer_prompt])
        [newer_prompt, older_prompt]
    """
    return sorted(prompts, key=lambda p: p.created_at, reverse=descending)


def filter_prompts_by_collection(prompts: List[Prompt], collection_id: str) -> List[Prompt]:
    """Filter prompts down to those belonging to a specific collection.

    Args:
        prompts (List[Prompt]): The prompts to filter.
        collection_id (str): The collection id to match against each
            prompt's collection_id.

    Returns:
        List[Prompt]: The prompts whose collection_id equals
            collection_id.

    Example:
        >>> filter_prompts_by_collection(prompts, "abc-123")
        [Prompt(id='...', collection_id='abc-123', ...)]
    """
    return [p for p in prompts if p.collection_id == collection_id]


def search_prompts(prompts: List[Prompt], query: str) -> List[Prompt]:
    """Search prompts by title and description text.

    Matching is a case-insensitive substring check against each prompt's
    title and description. The prompt's content field is not searched.

    Args:
        prompts (List[Prompt]): The prompts to search.
        query (str): The search text to look for.

    Returns:
        List[Prompt]: The prompts whose title or description contains
            query, case-insensitively.

    Example:
        >>> search_prompts(prompts, "email")
        [Prompt(id='...', title='Cold outreach email', ...)]
    """
    query_lower = query.lower()
    return [
        p for p in prompts
        if query_lower in p.title.lower() or
           (p.description and query_lower in p.description.lower())
    ]


def validate_prompt_content(content: str) -> bool:
    """Check if prompt content is valid.

    A valid prompt should:
    - Not be empty
    - Not be just whitespace
    - Be at least 10 characters

    Args:
        content (str): The prompt content to validate.

    Returns:
        bool: True if content is non-empty, non-whitespace-only, and at
            least 10 characters after stripping. False otherwise.

    Example:
        >>> validate_prompt_content("Write a short story")
        True
        >>> validate_prompt_content("   ")
        False
    """
    if not content or not content.strip():
        return False
    return len(content.strip()) >= 10


def extract_variables(content: str) -> List[str]:
    """Extract template variables from prompt content.

    Variables are in the format {{variable_name}}.

    Args:
        content (str): The prompt content to scan for variables.

    Returns:
        List[str]: The variable names found, in order of appearance,
            without the surrounding braces. Empty if none are found.

    Example:
        >>> extract_variables("Hello {{name}}, welcome to {{place}}!")
        ['name', 'place']
    """
    import re
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, content)
