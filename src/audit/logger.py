"""
Append-only local audit trail. Every classification and every action the
wrapper takes gets logged here — this is the evidence trail for "what did
the agent do and why", independent of Gmail's own state.

data/audit_log.jsonl is gitignored — it will contain real message
metadata (subject lines, senders) once you run this for real.
"""

import json
from datetime import datetime, timezone
from config.settings import settings


def log_entry(message_id: str, category: str, confidence: float, action_taken: str | None = None) -> None:
    """
    Append one JSON record per line (JSONL) — easy to tail, grep, or
    load into pandas later if you want to review classification
    accuracy over time.

    Args:
        action_taken: e.g. "moved_to_staging_confirmations", or None if
                      no Gmail write happened (e.g. category was "other").
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message_id": message_id,
        "category": category,
        "confidence": confidence,
        "action_taken": action_taken,
    }
    with open(settings.AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
