from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .reasoning import PredictionWatch

DEFAULT_CHECKPOINTS = (("1h", timedelta(hours=1)), ("6h", timedelta(hours=6)), ("24h", timedelta(hours=24)))


@dataclass(frozen=True)
class ClvDue:
    watch: PredictionWatch
    checkpoint: str
    due_at: datetime


def due_clv_checkpoints(
    watches: list[PredictionWatch],
    state: dict,
    *,
    now: datetime,
    checkpoints=DEFAULT_CHECKPOINTS,
) -> list[ClvDue]:
    emitted = state.get("clv_checkpoints", {})
    due: list[ClvDue] = []
    for watch in watches:
        by_checkpoint = emitted.get(watch.key, {})
        for label, delta in checkpoints:
            if label in by_checkpoint:
                continue
            due_at = watch.written_at + delta
            if now >= due_at:
                due.append(ClvDue(watch=watch, checkpoint=label, due_at=due_at))
    due.sort(key=lambda item: (item.due_at, item.watch.slug, item.checkpoint))
    return due
