"""
The ONLY entry point the classifier/agent is allowed to call to affect
Gmail state. Everything else in src/gmail/client.py should be considered
internal plumbing this file uses, not something exposed further up.

The principle: "constrain the target/result surface in code, since the
OAuth scope itself is broader than ideal" gmail.modify as a scope
technically permits changing ANY label on ANY message — this wrapper is
what actually limits the agent to one narrow, auditable action.
"""

from src.gmail import client

# Fixed allow-list. The category argument passed to move_to_staging()
# must be a key in this dict, or the call is rejected outright — the
# classifier/LLM never gets to supply an arbitrary label ID.
ALLOWED_STAGING_LABELS = {
    "newsletter_promo": "Label_StagingNewsletters",
    "confirmation": "Label_StagingConfirmations",
}


def move_to_staging(message_id: str, category: str) -> None:
    """
    The one write action this whole project performs: remove INBOX,
    add exactly one pre-approved staging label. Additive with respect
    to any pre-existing labels (e.g. a rule-applied "Voyage" label) —
    this function never removes anything except INBOX.

    Raises:
        ValueError: if `category` isn't in ALLOWED_STAGING_LABELS —
        this is the actual enforcement point. No category outside this
        fixed list can ever result in an API call being made.
    """
    if category not in ALLOWED_STAGING_LABELS:
        raise ValueError(
            f"'{category}' is not an allowed staging category. "
            f"Allowed: {list(ALLOWED_STAGING_LABELS.keys())}"
        )

    label_id = ALLOWED_STAGING_LABELS[category]

    # TODO: call client.modify_message_labels once client.py is implemented:
    # client.modify_message_labels(
    #     message_id=message_id,
    #     add_label_ids=[label_id],
    #     remove_label_ids=["INBOX"],
    # )
    raise NotImplementedError("Wire up the call to client.modify_message_labels() — see TODO above.")
