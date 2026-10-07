"""
Orchestration skeleton — the intended end-to-end flow, wiring together
pieces that are mostly still stubs (auth, gmail.client) with pieces that
already work (llm.ollama_client, classification.classifier, audit.logger).

Won't run yet until src/auth/ and src/gmail/client.py are implemented.
Left deliberately thin so the flow is easy to read at a glance.
"""

from src.auth import token_store  # noqa: F401 — not yet implemented, see src/auth/
from src.gmail import client, actions
from src.classification.classifier import classify_email
from src.audit.logger import log_entry
from src.llm.ollama_client import health_check


def run_once(max_messages: int = 50) -> None:
    if not health_check():
        print("Ollama isn't ready — check it's running and the model is pulled.")
        return

    # TODO: once src/auth/ is implemented, the first call into
    # src/gmail/client.py should transparently get a valid access token
    # via token_store.get_valid_access_token() — no token handling
    # should be needed here in main.py itself.

    message_ids = client.list_inbox_messages(max_results=max_messages)

    for msg_id in message_ids:
        message = client.get_message(msg_id)

        # TODO: extract subject/sender/snippet from the raw message
        # resource — the exact parsing depends on format=full vs
        # format=metadata, chosen when you implement get_message().
        subject, sender, snippet = "", "", ""

        result = classify_email(subject=subject, sender=sender, snippet=snippet)
        action_taken = None

        if result["category"] in ("newsletter_promo", "confirmation") and result["confidence"] >= 0.7:
            actions.move_to_staging(msg_id, result["category"])
            action_taken = f"moved_to_staging_{result['category']}"

        log_entry(
            message_id=msg_id,
            category=result["category"],
            confidence=result["confidence"],
            action_taken=action_taken,
        )


if __name__ == "__main__":
    run_once()
