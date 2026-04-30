from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping

from automation.timeutil import isoformat_z
from automation.wake import build_wake_event, safe_part


@dataclass(frozen=True)
class ParticipantTrade:
    venue: str
    wallet: str
    side: str
    outcome: str
    outcome_index: int | None
    price: float
    size: float
    timestamp: datetime
    market_slug: str
    event_slug: str | None
    title: str
    condition_id: str | None = None
    asset: str | None = None
    transaction_hash: str | None = None
    name: str | None = None
    pseudonym: str | None = None

    @property
    def notional(self) -> float:
        return self.price * self.size

    @property
    def trader_label(self) -> str:
        if self.pseudonym:
            return self.pseudonym
        if self.name:
            return self.name
        return self.wallet


@dataclass(frozen=True)
class MarketBook:
    yes_bid: float | None
    yes_ask: float | None
    yes_price: float | None = None
    liquidity: float | None = None
    volume: float | None = None

    @property
    def actionable(self) -> bool:
        return (
            self.yes_bid is not None
            and self.yes_ask is not None
            and 0 < self.yes_bid < 1
            and 0 < self.yes_ask < 1
            and self.yes_bid <= self.yes_ask
        )

    @property
    def spread(self) -> float | None:
        if not self.actionable:
            return None
        assert self.yes_bid is not None and self.yes_ask is not None
        return self.yes_ask - self.yes_bid


@dataclass(frozen=True)
class CopyEntry:
    side: str
    executable_price: float
    reference_price: float
    bid: float
    ask: float
    spread_pp: float
    max_notional_usd: float | None = None


@dataclass(frozen=True)
class ParticipantScore:
    wallet: str
    domain: str
    horizon_bucket: str
    sample_size: int
    mean_clv_pp: float
    copy_after_delay_mean_clv_pp: float
    realized_roi: float | None
    shrinkage_weight: float
    score: float


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _to_datetime_from_unix(value: Any) -> datetime:
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


def normalize_polymarket_trade(row: Mapping[str, Any]) -> ParticipantTrade:
    """Normalize one public data-api Polymarket trade row."""
    return ParticipantTrade(
        venue="Polymarket",
        wallet=str(row.get("proxyWallet") or row.get("user") or ""),
        side=str(row.get("side") or "").upper(),
        outcome=str(row.get("outcome") or ""),
        outcome_index=int(row["outcomeIndex"]) if row.get("outcomeIndex") not in (None, "") else None,
        price=_to_float(row.get("price")),
        size=_to_float(row.get("size")),
        timestamp=_to_datetime_from_unix(row.get("timestamp")),
        market_slug=str(row.get("slug") or ""),
        event_slug=str(row.get("eventSlug")) if row.get("eventSlug") else None,
        title=str(row.get("title") or ""),
        condition_id=str(row.get("conditionId")) if row.get("conditionId") else None,
        asset=str(row.get("asset")) if row.get("asset") else None,
        transaction_hash=str(row.get("transactionHash")) if row.get("transactionHash") else None,
        name=str(row.get("name")) if row.get("name") else None,
        pseudonym=str(row.get("pseudonym")) if row.get("pseudonym") else None,
    )


CRYPTO_TERMS = re.compile(r"\b(bitcoin|btc|ethereum|eth|solana|sol\b|chainlink|link\b|doge|xrp|crypto|token)\b", re.I)
EARNINGS_TERMS = re.compile(r"\b(earnings|eps|revenue|quarterly|guidance|gaap|non-gaap)\b", re.I)
SPORTS_TERMS = re.compile(r"\b(vs\.?|fc\b|nba|nfl|mlb|nhl|uefa|ucl|lakers|rockets|arsenal|bayern|psg|score|win on)\b", re.I)
MACRO_TERMS = re.compile(r"\b(fed|fomc|powell|cpi|inflation|gdp|jobs|payrolls?|unemployment|rates?|wti|crude|oil|gold|silver|xag|fx|treasury)\b", re.I)
POLITICS_TERMS = re.compile(r"\b(trump|biden|election|senate|house|congress|bill|act|law|minister|president|war|russia|ukraine|iran|israel|government)\b", re.I)
SOURCE_TERMS = re.compile(r"\b(xtracker|post counter|substack|official|announcement|resolution source|tracker|reported|reporting|mythos|claude|leaderboard)\b", re.I)
CULTURE_TERMS = re.compile(r"\b(stream|streamer|netflix|tweets?|posts?|elon|celebrity|music|movie|show|youtube|tiktok|truth social|white house)\b", re.I)


def domain_bucket(title: str, slug: str = "") -> str:
    text = f"{title} {slug}"
    if CRYPTO_TERMS.search(text):
        return "crypto"
    if EARNINGS_TERMS.search(text):
        return "earnings"
    if SPORTS_TERMS.search(text):
        return "sports"
    if MACRO_TERMS.search(text):
        return "macro"
    if SOURCE_TERMS.search(text):
        return "source"
    if CULTURE_TERMS.search(text):
        return "culture"
    if POLITICS_TERMS.search(text):
        return "politics"
    return "other"


def horizon_bucket(end_time: datetime | None, now: datetime) -> str:
    if end_time is None:
        return "long"
    days = (end_time - now).total_seconds() / 86400
    if days < 0:
        return "closed"
    if days < 1 / 24:
        return "micro"
    if days < 1:
        return "intraday"
    if days <= 7:
        return "1-7d"
    if days <= 21:
        return "8-21d"
    if days <= 45:
        return "22-45d"
    return "long"


def shrinkage_weight(sample_size: int, prior_n: int = 25) -> float:
    if sample_size <= 0:
        return 0.0
    return sample_size / (sample_size + prior_n)


def score_participant(
    *,
    wallet: str,
    domain: str,
    horizon: str,
    sample_size: int,
    mean_clv_pp: float,
    copy_after_delay_mean_clv_pp: float,
    realized_roi: float | None = None,
    prior_n: int = 25,
) -> ParticipantScore:
    weight = shrinkage_weight(sample_size, prior_n=prior_n)
    # CLV is already in percentage points. Keep score in pp so thresholds are interpretable.
    score = copy_after_delay_mean_clv_pp * weight
    return ParticipantScore(
        wallet=wallet,
        domain=domain,
        horizon_bucket=horizon,
        sample_size=sample_size,
        mean_clv_pp=mean_clv_pp,
        copy_after_delay_mean_clv_pp=copy_after_delay_mean_clv_pp,
        realized_roi=realized_roi,
        shrinkage_weight=weight,
        score=score,
    )


def copy_entry_from_book(trade: ParticipantTrade, book: MarketBook, *, max_notional_usd: float | None = None) -> CopyEntry | None:
    """Approximate executable copy entry for a binary YES/NO market from YES bid/ask.

    Polymarket Gamma exposes `bestBid`/`bestAsk` for the first/YES outcome on binary markets.
    For NO exposure, approximate executable NO ask as `1 - yes_bid` and NO bid as `1 - yes_ask`.
    """
    if not book.actionable:
        return None
    assert book.yes_bid is not None and book.yes_ask is not None

    outcome = trade.outcome.lower()
    side = trade.side.upper()
    wants_yes = None
    if outcome in {"yes", "up"} or trade.outcome_index == 0:
        wants_yes = side == "BUY"
    elif outcome in {"no", "down"} or trade.outcome_index == 1:
        wants_yes = side == "SELL"

    if wants_yes is None:
        return None

    if wants_yes:
        bid = book.yes_bid
        ask = book.yes_ask
        executable = ask
        copy_side = "BUY_YES"
    else:
        bid = 1 - book.yes_ask
        ask = 1 - book.yes_bid
        executable = ask
        copy_side = "BUY_NO"

    return CopyEntry(
        side=copy_side,
        executable_price=executable,
        reference_price=trade.price,
        bid=bid,
        ask=ask,
        spread_pp=(ask - bid) * 100,
        max_notional_usd=max_notional_usd,
    )


def is_micro_market(title: str, slug: str = "") -> bool:
    text = f"{title} {slug}".lower()
    return "up or down" in text or "updown" in text or "5m" in text or "15m" in text


def participant_signal_filter_reason(
    trade: ParticipantTrade,
    *,
    score: ParticipantScore | None = None,
    book: MarketBook | None = None,
    min_notional_usd: float = 10.0,
    min_score_pp: float = 1.0,
    max_spread_pp: float = 10.0,
    allow_micro: bool = False,
) -> tuple[bool, str]:
    if not trade.wallet:
        return False, "missing wallet"
    if not trade.market_slug or not trade.title:
        return False, "missing market identity"
    if trade.side not in {"BUY", "SELL"}:
        return False, "unsupported side"
    if trade.price <= 0 or trade.price >= 1 or trade.size <= 0:
        return False, "invalid price/size"
    if trade.notional < min_notional_usd:
        return False, f"trade notional below ${min_notional_usd:g}"
    if not allow_micro and is_micro_market(trade.title, trade.market_slug):
        return False, "micro-duration market"
    if score is not None and score.score < min_score_pp:
        return False, "participant score below threshold"
    if book is not None:
        entry = copy_entry_from_book(trade, book)
        if entry is None:
            return False, "no actionable copy book"
        if entry.spread_pp > max_spread_pp:
            return False, "copy book spread too wide"
    return True, "ok"


def participant_signal_id(trade: ParticipantTrade) -> str:
    tx = trade.transaction_hash or f"{int(trade.timestamp.timestamp())}:{trade.asset or trade.outcome_index}"
    safe_wallet = re.sub(r"[^a-zA-Z0-9]+", "-", trade.wallet.lower()).strip("-")
    safe_slug = re.sub(r"[^a-zA-Z0-9]+", "-", trade.market_slug.lower()).strip("-")
    safe_tx = re.sub(r"[^a-zA-Z0-9]+", "-", tx.lower()).strip("-")[:32]
    return f"participant:{safe_wallet}:{safe_slug}:{safe_tx}"


def participant_state_default() -> dict[str, Any]:
    return {
        "version": 1,
        "processed_transactions": {},
        "emitted_signals": {},
        "wallet_scores": {},
    }


def trade_payload(trade: ParticipantTrade) -> dict[str, Any]:
    return {
        "venue": trade.venue,
        "wallet": trade.wallet,
        "name": trade.name,
        "pseudonym": trade.pseudonym,
        "side": trade.side,
        "outcome": trade.outcome,
        "outcomeIndex": trade.outcome_index,
        "price": trade.price,
        "size": trade.size,
        "notional": trade.notional,
        "timestamp": isoformat_z(trade.timestamp),
        "marketSlug": trade.market_slug,
        "eventSlug": trade.event_slug,
        "title": trade.title,
        "conditionId": trade.condition_id,
        "asset": trade.asset,
        "transactionHash": trade.transaction_hash,
    }


def copy_entry_payload(entry: CopyEntry | None) -> dict[str, Any] | None:
    if entry is None:
        return None
    return {
        "side": entry.side,
        "executablePrice": entry.executable_price,
        "referencePrice": entry.reference_price,
        "bid": entry.bid,
        "ask": entry.ask,
        "spreadPp": entry.spread_pp,
        "maxNotionalUsd": entry.max_notional_usd,
    }


def participant_score_payload(score: ParticipantScore | None) -> dict[str, Any] | None:
    if score is None:
        return None
    return {
        "wallet": score.wallet,
        "domain": score.domain,
        "horizonBucket": score.horizon_bucket,
        "sampleSize": score.sample_size,
        "meanClvPp": score.mean_clv_pp,
        "copyAfterDelayMeanClvPp": score.copy_after_delay_mean_clv_pp,
        "realizedRoi": score.realized_roi,
        "shrinkageWeight": score.shrinkage_weight,
        "score": score.score,
    }


def generate_participant_events(
    *,
    trades: list[ParticipantTrade],
    state: dict[str, Any],
    now: datetime,
    session_id: str,
    books_by_slug: Mapping[str, MarketBook] | None = None,
    end_times_by_slug: Mapping[str, datetime] | None = None,
    scores_by_wallet_domain: Mapping[tuple[str, str, str], ParticipantScore] | None = None,
    min_notional_usd: float = 10.0,
    min_score_pp: float = 1.0,
    max_spread_pp: float = 10.0,
    max_events: int = 5,
    emit_unscored: bool = False,
    allow_micro: bool = False,
) -> list[dict[str, Any]]:
    """Generate participant_signal_candidate wake events from normalized trades.

    Cold-start operation should generally keep `emit_unscored=False`; fixture tests and
    explicit discovery runs can set it true to inspect proposed payloads without claiming
    an established trader edge.
    """
    state.setdefault("processed_transactions", {})
    state.setdefault("emitted_signals", {})
    books_by_slug = books_by_slug or {}
    end_times_by_slug = end_times_by_slug or {}
    scores_by_wallet_domain = scores_by_wallet_domain or {}

    events: list[dict[str, Any]] = []
    for trade in sorted(trades, key=lambda item: item.timestamp, reverse=True):
        signal_key = participant_signal_id(trade)
        tx_key = trade.transaction_hash or signal_key
        if tx_key in state["processed_transactions"] or signal_key in state["emitted_signals"]:
            continue

        domain = domain_bucket(trade.title, trade.market_slug)
        horizon = horizon_bucket(end_times_by_slug.get(trade.market_slug), now)
        score = scores_by_wallet_domain.get((trade.wallet.lower(), domain, horizon))
        book = books_by_slug.get(trade.market_slug)
        if score is None and not emit_unscored:
            state["processed_transactions"][tx_key] = {"observed_at": isoformat_z(now), "reason": "unscored cold-start"}
            continue

        ok, reason = participant_signal_filter_reason(
            trade,
            score=score,
            book=book,
            min_notional_usd=min_notional_usd,
            min_score_pp=min_score_pp,
            max_spread_pp=max_spread_pp,
            allow_micro=allow_micro,
        )
        if not ok:
            state["processed_transactions"][tx_key] = {"observed_at": isoformat_z(now), "reason": reason}
            continue

        copy_entry = copy_entry_from_book(trade, book) if book else None
        event_id = f"rime-participant-signal-{safe_part(trade.market_slug, max_len=46)}-{safe_part(trade.wallet[-8:] or 'wallet', max_len=12)}-{safe_part(tx_key[-10:], max_len=12)}"
        payload = {
            "dedupeKey": signal_key,
            "domain": domain,
            "horizonBucket": horizon,
            "trade": trade_payload(trade),
            "participantScore": participant_score_payload(score),
            "copyEntry": copy_entry_payload(copy_entry),
            "qualityReason": reason,
            "book": {
                "yesBid": book.yes_bid,
                "yesAsk": book.yes_ask,
                "yesPrice": book.yes_price,
                "liquidity": book.liquidity,
                "volume": book.volume,
                "spreadPp": None if book.spread is None else book.spread * 100,
            }
            if book
            else None,
        }
        prompt = (
            f"Review this shadow participant signal for {trade.trader_label} on {trade.title}. "
            "If post-detection copy economics and participant score justify tracking, update participant-ledger.md; "
            "do not place trades."
        )
        events.append(
            build_wake_event(
                event_id=event_id,
                session_id=session_id,
                ts=isoformat_z(now),
                event_type="participant_signal_candidate",
                priority=55,
                prompt=prompt,
                payload=payload,
                source="rime-forecasts/polymarket-participant-daemon",
            )
        )
        if len(events) >= max_events:
            break
    return events


def mark_participant_events_emitted(state: dict[str, Any], events: list[dict[str, Any]], *, now: datetime) -> None:
    state.setdefault("processed_transactions", {})
    state.setdefault("emitted_signals", {})
    for event in events:
        payload = event.get("payload", {})
        dedupe_key = payload.get("dedupeKey")
        tx = payload.get("trade", {}).get("transactionHash") if isinstance(payload.get("trade"), dict) else None
        record = {"event_id": event.get("id"), "emitted_at": isoformat_z(now), "type": event.get("type")}
        if dedupe_key:
            state["emitted_signals"][dedupe_key] = record
        if tx:
            state["processed_transactions"][tx] = record
