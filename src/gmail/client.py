"""
Thin Gmail API client — skeleton.

Every function here should call get_valid_access_token() from
src/auth/token_store.py and use it as a Bearer token, e.g.:

    headers = {"Authorization": f"Bearer {access_token}"}

Base URL for all calls: settings.GMAIL_API_BASE
("https://gmail.googleapis.com/gmail/v1")
"""

from config.settings import settings


def list_inbox_messages(max_results: int = 50) -> list[dict]:
    """
    GET {GMAIL_API_BASE}/users/me/messages
        ?labelIds=INBOX&maxResults={max_results}

    Returns a list of {"id": ..., "threadId": ...} — NOT full message
    content. You need get_message() below to fetch the actual body/subject
    for each one.
    """
    raise NotImplementedError("List inbox message IDs — see docstring above.")


def get_message(message_id: str) -> dict:
    """
    GET {GMAIL_API_BASE}/users/me/messages/{message_id}
        ?format=full  (or "metadata" if you only need headers, which is
        faster and enough for subject/sender-based classification)

    Returns the full message resource — payload, headers, labelIds, etc.
    You'll likely want to parse out just subject/sender/snippet for
    passing to the classifier rather than the raw payload.
    """
    raise NotImplementedError("Fetch a single message's content — see docstring above.")


def modify_message_labels(message_id: str, add_label_ids: list[str], remove_label_ids: list[str]) -> dict:
    """
    POST {GMAIL_API_BASE}/users/me/messages/{message_id}/modify
    Body: {"addLabelIds": add_label_ids, "removeLabelIds": remove_label_ids}

    This is the ONE raw API call in the whole project that can actually
    change a message's labels. It is intentionally not exposed directly
    to the classifier or the LLM — see src/gmail/actions.py, which wraps
    this behind a fixed, validated set of allowed moves. Nothing else in
    the app should call this function directly.
    """
    raise NotImplementedError("Modify a message's labels — see docstring above.")
