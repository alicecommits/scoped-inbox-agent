"""
Fixed set of categories the classifier is allowed to output.

Kept separate from src/gmail/actions.py's ALLOWED_STAGING_LABELS on
purpose — this is "what the model is allowed to say", that's "what the
system is allowed to do as a result." Keeping them as two distinct
allow-lists, checked independently, means a classifier bug (e.g. a typo
or a hallucinated category) fails safely instead of accidentally passing
straight through to a Gmail write.
"""

CATEGORIES = [
    "newsletter_promo",
    "confirmation",
    "other",  # explicit fallback — anything that doesn't clearly fit stays untouched
]
