from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_PATH = REPO_ROOT / "automation" / "state" / "polymarket-daemon.json"
DEFAULT_WAKE_ROOT = Path.home() / ".pi" / "agent" / "wake"
DEFAULT_REASONING_DIR = REPO_ROOT / "reasoning"


def require_session_id(cli_session_id: str | None, env: dict[str, str] | None = None, *, dry_run: bool = False) -> str | None:
    """Resolve the wake routing session id.

    There are intentionally only two sources: explicit CLI arg, then explicit env var.
    No cwd/latest-session fallback is allowed.
    """

    env = env if env is not None else os.environ
    session_id = (cli_session_id or "").strip() or (env.get("RIME_WAKE_SESSION_ID", "").strip())
    if session_id:
        return session_id
    if dry_run:
        return None
    raise ValueError("missing explicit session id: pass --session-id or set RIME_WAKE_SESSION_ID")
