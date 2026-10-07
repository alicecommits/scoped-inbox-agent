# scoped-inbox-agent

A local LLM agent that triages personal email noise — built around
least-privilege OAuth2 scoping, a deterministic action wrapper
constraining what the model can do, and a strict no-link-interaction
security boundary.

## Why this exists

Gmail's native filters can't handle categories that need content
judgment rather than sender-matching (multilingual promotional content,
ambiguous confirmations). This agent handles exactly that gap — nothing
a deterministic rule could already resolve is handled here.

## Design principles

- **Least privilege, enforced in code, not just in scope.** Gmail's
  `gmail.modify` OAuth scope is broader than this project needs — it
  permits changing any label on any message. `src/gmail/actions.py`
  closes that gap with a fixed allow-list wrapper: the only thing the
  rest of the app can ever do is move a message to one of two
  pre-approved staging labels. No other write path exists.
- **The model never touches Gmail directly.** The LLM only ever returns
  a classification + confidence score; a separate, deterministic
  function decides whether and how to act on that.
- **No link or attachment interaction, ever.** This agent never opens,
  clicks, or fetches any URL or attachment content it encounters in an
  email — full stop, regardless of category or apparent legitimacy.
- **Read-then-move, never delete or modify content.** The agent changes
  _where_ a message lives (via labels), never its content.

## Project structure

```
config/settings.py       All configuration, loaded from .env
src/auth/                OAuth2 flow, implement this myself
src/gmail/client.py      Raw Gmail API calls
src/gmail/actions.py     Least-privilege wrapper — the enforcement point
src/llm/ollama_client.py Local LLM client — WORKING, against Ollama
src/classification/      Category definitions + classifier — WORKING starting point
src/audit/logger.py      Local audit trail (JSONL) — WORKING
src/main.py              Orchestration — skeleton, wires everything together
data/                    Local runtime data (tokens, audit log) — gitignored
```

## What's implemented vs. left for you

| Area                                             | Status                                                  |
| ------------------------------------------------ | ------------------------------------------------------- |
| OAuth2 flow (`src/auth/`)                        | for me to implement, see docstrings                     |
| Gmail API calls (`src/gmail/client.py`)          | **Skeleton**                                            |
| Least-privilege wrapper (`src/gmail/actions.py`) | Allow-list defined; API call wiring left as `TODO`      |
| Local LLM client (`src/llm/ollama_client.py`)    | **Working**                                             |
| Classifier (`src/classification/`)               | **Working starting point** — prompt will need iteration |
| Audit log (`src/audit/logger.py`)                | **Working**                                             |
| Orchestration (`src/main.py`)                    | Skeleton showing intended flow                          |

## Setup

1. `python -m venv .venv && source .venv/bin/activate` (or `uv venv`)
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill in your Gmail OAuth client ID/secret
   (create one at Google Cloud Console → APIs & Services → Credentials →
   OAuth client ID → Desktop app)
4. Install [Ollama](https://ollama.com), then:
   ```
   ollama pull qwen3:8b
   ```
5. Sanity check the LLM side works before touching OAuth at all:
   ```
   python -m src.llm.ollama_client
   ```
6. Implement `src/auth/oauth_flow.py` and `src/auth/token_store.py`
   (see docstrings for the exact shape of each step).
7. Implement `src/gmail/client.py`.
8. Wire up the `TODO` in `src/gmail/actions.py`.
9. Run `python -m src.main`.

## Batch execution strategy

Given the expected volume of emails to process during each batch, I decided

- NOT to implement concurrent email processing, `requests` will process them sequentially, synchronously
- operate process-level separation for execution: in order not to block whatever else I'm doing, let my own OS scheduler invoke `python -m src.main` as a standalone process. That is why I didn't choose thread-level separation in the code itself. Per design, the current logics doesn't (and isn't meant to) live in a persistent app, notebook kernel or background daemon need that would need to stay responsive.

## Security notes

- `.env`, `data/tokens.json`, and `data/audit_log.jsonl` are gitignored —
  never commit real credentials or real message metadata.
- This currently uses the standard client-secret token exchange, which
  is appropriate for local testing. A local script is technically a
  public OAuth client (it can't keep a secret confidential on disk) —
  PKCE is the correct production-grade approach and is a planned next
  step, not yet implemented.
- No data ever leaves your machine — classification runs against a
  locally-hosted model, not a cloud API.
