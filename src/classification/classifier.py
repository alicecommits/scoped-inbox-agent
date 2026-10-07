"""
Email classifier — calls the local LLM, expects structured JSON back.

This is a working starting point, not a finished prompt. The plumbing
(call the model, parse the response, validate against the allow-list)
is done; the prompt wording itself is exactly the kind of thing you'll
want to iterate on once you're testing against real emails — especially
given the multilingual (FR/EN/ES) requirement from the project recap.
"""

import json
from src.llm.ollama_client import chat
from src.classification.categories import CATEGORIES

SYSTEM_PROMPT = f"""You classify emails into exactly one of these categories:
{", ".join(CATEGORIES)}

Rules:
- "newsletter_promo": marketing, newsletters, promotional discounts,
  unsubscribe-style content — in French, English, or Spanish.
- "confirmation": booking/order/delivery confirmations (e.g. hotels,
  ride-share, parcel carriers) — EXCEPT anything from French tax
  authorities (Finances Publiques, impots.gouv), which is always "other".
- "other": anything that doesn't clearly match the above — when in
  doubt, use this rather than guessing.

Respond with ONLY a JSON object, no other text:
{{"category": "<one of the categories above>", "confidence": <0.0-1.0>}}
"""


def classify_email(subject: str, sender: str, snippet: str) -> dict:
    """
    Args:
        subject, sender, snippet: pulled from a Gmail message resource
                                    (see src/gmail/client.get_message).

    Returns:
        {"category": str, "confidence": float} — category is guaranteed
        to be a member of CATEGORIES; falls back to "other" with
        confidence 0.0 if the model's output can't be parsed, so a
        malformed LLM response never crashes the batch or gets treated
        as a confident classification.
    """
    user_prompt = f"Sender: {sender}\nSubject: {subject}\nSnippet: {snippet}"

    raw_reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])

    try:
        result = json.loads(raw_reply)
        if result.get("category") not in CATEGORIES:
            raise ValueError(f"Model returned an unrecognized category: {result.get('category')}")
        return {"category": result["category"], "confidence": float(result.get("confidence", 0.0))}
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fail safe: unparseable or invalid output never gets treated as a
        # real classification, and never reaches the action wrapper.
        return {"category": "other", "confidence": 0.0}
