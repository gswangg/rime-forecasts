from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_state() -> dict[str, Any]:
    return {
        "version": 1,
        "candidate_events": {},
        "candidate_event_groups": {},
        "last_prices": {},
        "price_move_events": {},
        "last_price_move_events": {},
        "clv_checkpoints": {},
        "resolution_events": {},
        "emitted_events": {},
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_state()
    data = json.loads(path.read_text())
    state = default_state()
    if isinstance(data, dict):
        state.update(data)
    for key, default in default_state().items():
        state.setdefault(key, default)
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
