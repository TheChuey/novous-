"""LangChain tools for conversation-history lookup."""

from typing import Annotated

from langchain_core.tools import tool

from tools.chatlog import search_text


@tool
def search_chat_logs(query: Annotated[str, "Keyword or phrase to search for."]) -> str:
    """Searches saved conversation history for matching messages."""
    result = search_text(query)
    if not result:
        return f"No matches found in the chat log for the query: '{query}'."
    return result


__all__ = ["search_chat_logs"]
