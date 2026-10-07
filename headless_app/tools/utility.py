"""LangChain tools for date and time utilities."""

from langchain_core.tools import tool


@tool
def get_current_date() -> str:
    """Returns today's local date in a readable format."""
    from datetime import datetime

    return datetime.now().strftime("%A, %B %d, %Y")


@tool
def tell_me_the_date_and_time() -> str:
    """Returns the current local date and time."""
    from datetime import datetime

    return f"The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


__all__ = ["get_current_date", "tell_me_the_date_and_time"]
