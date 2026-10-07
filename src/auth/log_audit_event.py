import json
from datetime import datetime, timezone
from pathlib import Path
from config.settings import settings


def _log_audit_event(event_type: str, details: str):
    """Helper to append an event to data/audit.json safely."""
    token_path = Path(settings.TOKEN_STORE_PATH)
    audit_path = token_path.parent / "audit.json"

    # Ensure the 'data/' directory exists
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "details": details
    }

    # Load existing audit trail or start a fresh list
    audit_data = []
    if audit_path.exists():
        try:
            with open(audit_path, 'r', encoding="utf-8") as f:
                audit_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If the audit log itself is somehow broken, 
            # don't crash the app; just overwrite or reset
            audit_data = []

    audit_path.append(event)

    with open(audit_path, 'w', encoding="utf-8") as f:
        json.dump(audit_data, f, indent=4)