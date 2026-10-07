"""
OAuth2 Authorization Code Grant flow, Gmail.

This file is a SKELETON on purpose. The whole point of this project is to
implement this flow by hand rather than use a Google client SDK — so the
functions below are stubs with comments pointing at what each step needs,
not working code. Fill them in yourself.

Reminder of the shape (see project recap for the full walkthrough):
  1. build_authorization_url()   -> send the user to Google to consent
  2. run_local_callback_server() -> catch the redirect, grab the `code`
  3. exchange_code_for_tokens()  -> trade the code for access + refresh tokens
  4. refresh_access_token()      -> get a new access token when the old one expires
"""
import secrets
import http.server
import requests
import threading
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from config.settings import settings
from token_store import load_tokens

_PENDING_STATE = None
_CODE = None

class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global _CODE

        # 1. Parse the incoming URL path and query params
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        # optional safeguard for accidental root visits / missing params
        if "error" in query_params:
            error_code = query_params["error"][0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"OAuth Error: {error_code}. You can close this window.".encode())
          
        elif "code" not in query_params or "state" not in query_params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad request: Missing OAuth parameters.")

        else:
            # 2. Extract `code` and `state` from query_params
            code = query_params["code"][0]
            state = query_params["state"][0]

            # 3. Validate `state` against stored global state
            if (state != _PENDING_STATE):
                raise ValueError("Misaligned OAuth state")
            _CODE = code

            # 5. Send a friendly 200 OK response back to the browser tab
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authentication complete! You can now close this window.")

        # 6. Signal the server to shut down after handling this single request
        # Safe trigger shutdown in separate bg thread to avoid deadlock
        # Without this thread, Python's serve_forever() loop is blocked waiting end of do_GET()
        # whilst server.shutdown() waits for serve_forever() to stop
        # thus leading to mutual, forever waiting (deadlock)
        threading.Thread(target=self.server.shutdown).start()
        

def build_authorization_url() -> str:

    global _PENDING_STATE
    state = secrets.token_urlsafe(32)
    _PENDING_STATE = state  # Store it here temporarily

    params = {
        "client_id": settings.GMAIL_CLIENT_ID,
        "redirect_uri": settings.GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GMAIL_SCOPES,
        "access_type": "offline",
        "state": state,
    }

    query_string = urlencode(params)
    url = f"{settings.GOOGLE_AUTH_ENDPOINT}?{query_string}"

    return url


def run_local_callback_server(port: int = 8080) -> str:
    global _CODE
    _CODE = None # Reset state for a clean run

    server_address = ("127.0.0.1", port)
    httpd = http.server.HTTPServer(server_address, OAuthCallbackHandler)
    print(f"Listening for OAuth redirect on http://localhost:{port} ...")

    # Start the sever loop. This blocks (freezes) execution,
    # waiting for Google's redirect.
    # Once the OAuthCallbackHandler instance calls `self.server.shutdown()`
    # in the background thread, the loop will unblock and exit.
    httpd.serve_forever()

    # Clean up the socket connection so the port is freed up
    httpd.server_close()

    if not _CODE:
        raise RuntimeError("Failed to capture authorization code.")

    return _CODE

def exchange_code_for_tokens(code: str) -> dict:
    # deliberate choice of `requests` and not `aiohttp`, even though blocking,
    # as the local agent will be executed in its own process
    try:
        r = requests.post(
            url=settings.GOOGLE_TOKEN_ENDPOINT, 
            data={
                "code" : code,
                "client_id" : settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GMAIL_REDIRECT_URI
            }
        )

        if r.status_code == 200:
            # Success! Parse and return the tokens dictionary
            return r.json()

        elif r.status_code == 400:
            # Parse Google's specific error message (e.g., 'invalid_grant')
            error_data = r.json()
            error_reason = error_data.get("error", "unknown error")

            if error_reason == "invalid_grant":
                raise ValueError("Authorization code expired or already used. Please restart AuthZ flow.")
            else:
                raise RuntimeError(f"OAuth Token Error: {error_reason}")

    except requests.exceptions.RequestException as e:
        # Catch network-level issues (e.g. DNS, connection timeout)
        raise RuntimeError(f"Network error during token exchange: {e}")


def refresh_access_token(refresh_token: str) -> dict:
    """
    Same token endpoint as exchange_code_for_tokens(), but with:
      - grant_type = "refresh_token"
      - refresh_token = <the stored refresh token>
      - client_id, client_secret

    Note: Google does NOT return a new refresh_token on this call —
    keep reusing the original one you got at first consent.

    Returns:
        The parsed token response as a dict (new access_token + expires_in).
    """
    raise NotImplementedError("Refresh an expired access token — see docstring above.")

def main():


if __name__ == "__main__":
    print("--- Step 1: Building Authorization URL ---")
    url = build_authorization_url()
    print("Generated URL:\n", url)

    # Optional convenience: Automatically open the URL in your default browser
    webbrowser.open(url)
    
    print("\n--- Step 2: Waiting for OAuth Redirect ---")
    print("Please open the URL above in your browser, log in, and grant access.")
    
    # This will block and wait until Google redirects back to localhost:8080
    captured_code = run_local_callback_server()
    
    print("\n--- Success! ---")
    # no more code printing, and no token at the exchange phase either.

# --- Stretch goal, not needed for the first working version ---
# notes of security about retrieving the code in an html page
# associated best practice with other redirect uri
# then DPoP 
# - read google dev doc about it

# PKCE (Proof Key for Code Exchange) hardens this exact flow for public
# clients like this one, which can't keep client_secret confidential on
# disk. It doesn't replace anything above — it adds a code_verifier /
# code_challenge pair to steps 1 and 3, and lets you drop client_secret
# from the token exchange. Worth implementing once the plain flow works,
# not before.
