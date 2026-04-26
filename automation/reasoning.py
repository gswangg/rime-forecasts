from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .timeutil import parse_iso


@dataclass(frozen=True)
class PredictionWatch:
    path: Path
    title: str
    slug: str
    written_at: object
    prediction: float | None
    price_at_writing: float | None
    primary_venue: str | None
    primary_url: str | None

    @property
    def key(self) -> str:
        return f"{self.path.name}:{self.slug}"


def _field(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _pct(pattern: str, text: str) -> float | None:
    value = _field(pattern, text)
    if value is None:
        return None
    try:
        return float(value) / 100
    except ValueError:
        return None


def extract_polymarket_watches(reasoning_dir: Path) -> list[PredictionWatch]:
    watches: list[PredictionWatch] = []
    if not reasoning_dir.exists():
        return watches

    for path in sorted(reasoning_dir.glob("*.md")):
        text = path.read_text()
        slug = _field(r"\*\*Polymarket market slug\*\*:\s*([^\s]+)", text)
        if not slug:
            match = re.search(r"polymarket\.com/market/([a-zA-Z0-9-]+)", text)
            slug = match.group(1) if match else None
        if not slug:
            continue

        written_raw = _field(r"\*\*Written\*\*:\s*([^\n]+)", text)
        if not written_raw:
            continue
        try:
            written_at = parse_iso(written_raw)
        except ValueError:
            continue

        title_match = re.search(r"^#\s+(.+?)(?:\s+[—-]\s+resolves|$)", text, re.MULTILINE | re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else path.stem

        watches.append(
            PredictionWatch(
                path=path,
                title=title,
                slug=slug,
                written_at=written_at,
                prediction=_pct(r"\*\*Prediction\*\*:\s*(\d+(?:\.\d+)?)%", text),
                price_at_writing=(
                    _pct(r"\*\*Primary venue price at writing\*\*:\s*(\d+(?:\.\d+)?)%", text)
                    or _pct(r"\*\*Polymarket price at writing\*\*:\s*(\d+(?:\.\d+)?)%", text)
                    or _pct(r"\*\*Market price at writing\*\*:\s*(\d+(?:\.\d+)?)%", text)
                ),
                primary_venue=_field(r"\*\*Primary venue\*\*:\s*([^\n]+)", text),
                primary_url=_field(r"\*\*Primary URL\*\*:\s*(https?://[^\s]+)", text),
            )
        )
    return watches


def watch_payload(watch: PredictionWatch) -> dict:
    return {
        "reasoningPath": str(watch.path),
        "title": watch.title,
        "slug": watch.slug,
        "writtenAt": watch.written_at.isoformat().replace("+00:00", "Z"),
        "prediction": watch.prediction,
        "priceAtWriting": watch.price_at_writing,
        "primaryVenue": watch.primary_venue,
        "primaryUrl": watch.primary_url,
    }
