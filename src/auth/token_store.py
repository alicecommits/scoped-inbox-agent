"""
Local token persistence — skeleton.

Just enough structure to show where tokens should live between runs, so
you don't have to re-consent in a browser every single time you run the
agent. Implementation left to you, same as oauth_flow.py.

data/tokens.json is gitignored — never commit this file once it's real.
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from config.settings import settings
from auth.log_audit_event import _log_audit_event

class TokenStorageError(Exception):
    """Raised when tokens cannot be read or written to disk."""
    pass

def save_tokens(tokens: dict) -> None:
    """
    Persist the token response from exchange_code_for_tokens() or
    refresh_access_token() to settings.TOKEN_STORE_PATH.
    """
    token_path = Path(settings.TOKEN_STORE_PATH)

    try:
        # Ensure the 'data/' directory exists before trying to write
        token_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle the OAuth edge case: Google only sends a refresh_token
        # on initial grant. If we are updating tokens later, retain
        # the existing refresh_token if it's missing.
        refresh_token = tokens.get("refresh_token")
        if not refresh_token and token_path.exists():
            try:
                with open(token_path, 'r', encoding="utf-8") as f:
                    old_data = json.load(f)
                    refresh_token = old_data.get("refresh_token")
            except (json.JSONDecodeError, IOError):
                pass # If reading the old file fails, proceed with what we have

        # Compute absolute expiration timestamp from current time + expires_in (s)
        expires_in = tokens.get("expires_in", 3600) #3600s is default, if omitted
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Structure the final dictionary to persist
        token_data = {
            "access_token": tokens.get("access_token"),
            "refresh_token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "token_type": tokens.get("token_type", "Bearer")
        }

        # Write out to disk securely
        with open(token_path, 'w', encoding="utf-8") as f:
            json.dump(token_data, f, indent=4)

        _log_audit_event("TOKENS_SAVED", f"Successfully persisted tokens to {token_path}")    

    except IOError as e:
        error_msg = f"Failed to persist tokens to {token_path}: {e}"
        logging.error(error_msg)
        _log_audit_event("TOKEN_STORE_SAVE_IO_ERROR", str(e))
        raise TokenStorageError(error_msg) from e

def load_tokens() -> dict | None:
    """
    Read settings.TOKEN_STORE_PATH if it exists, return the stored dict.
    Return None if no token file exists yet (first run).
    """
    token_path = Path(settings.TOKEN_STORE_PATH) 

    if not token_path.exists():
        return None

    try:
        with open(token_path, 'r', encoding="utf-8") as f:
            return json.load(f)

    except json.JSONDecodeError as e:
        # Flag any token file corruption explicitly, and audit it
        # remediation: remove dead file to avoid looping the flow on it
        logging.error(f"Token store at {token_path} is corrupted: {e}")
        _log_audit_event("TOKEN_STORE_CORRUPTED", str(e))
        token_path.unlink(missing_ok=True)

        # let the orchestrator cleanly triggers a fresh AuthZ flow
        return None

    except IOError as eio:
        error_msg = f"IO error reading token store at {token_path}: {eio}"
        logging.error(error_msg)
        
        # Audit the IO failure and halt execution 
        # (requires human/system intervention)
        _log_audit_event("TOKEN_STORE_IO_ERROR", str(eio))

        raise RuntimeError(error_msg) from eio

def get_valid_access_token() -> str:
    """
    The function the rest of the app should actually call.

    Load stored tokens; if the access_token is expired (or close to it),
    call oauth_flow.refresh_access_token() to get a new one and save it;
    otherwise return the existing access_token as-is.

    This is the function src/gmail/client.py should use — nothing else
    in the app should touch the raw token file directly.
    """
    raise NotImplementedError("Return a valid, non-expired access token — see docstring above.")
