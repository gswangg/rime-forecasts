from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
REQUIRED_FIELDS = ("id", "sessionId", "ts", "source", "type", "prompt")


class WakeEventError(ValueError):
    pass


def safe_part(value: str, *, max_len: int = 60) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._:-]+", "-", value.strip())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-._:")
    if not cleaned:
        cleaned = "event"
    return cleaned[:max_len]


def validate_wake_event(event: dict[str, Any]) -> None:
    for field in REQUIRED_FIELDS:
        if not isinstance(event.get(field), str) or not event[field].strip():
            raise WakeEventError(f"wake event missing non-empty {field}")
    if not SAFE_ID_RE.match(event["id"]):
        raise WakeEventError(f"unsafe wake event id: {event['id']!r}")
    if not isinstance(event.get("priority", 0), int):
        raise WakeEventError("wake event priority must be an integer")


def build_wake_event(
    *,
    event_id: str,
    session_id: str,
    ts: str,
    event_type: str,
    priority: int,
    prompt: str,
    payload: dict[str, Any],
    source: str = "rime-forecasts/polymarket-daemon",
) -> dict[str, Any]:
    event = {
        "id": event_id,
        "sessionId": session_id,
        "ts": ts,
        "source": source,
        "type": event_type,
        "priority": priority,
        "prompt": prompt,
        "payload": payload,
    }
    validate_wake_event(event)
    return event


def write_wake_event(wake_root: Path, event: dict[str, Any]) -> Path:
    validate_wake_event(event)
    inbox = Path(wake_root).expanduser().resolve() / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    target = inbox / f"{event['id']}.json"
    if target.exists():
        raise FileExistsError(f"wake event already exists: {target}")
    tmp = inbox / f".{event['id']}.json.tmp-{os.getpid()}"
    tmp.write_text(json.dumps(event, indent=2, sort_keys=True) + "\n")
    tmp.replace(target)
    return target
