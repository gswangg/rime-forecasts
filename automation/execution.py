from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any, Literal

Side = Literal["YES", "NO"]
SizingMode = Literal["max_payout", "cash"]
TicketStatus = Literal["draft", "blocked"]


@dataclass(frozen=True)
class ExecutionPolicy:
    min_edge: float = 0.10
    max_spread: float = 0.10
    sizing_mode: SizingMode = "max_payout"
    amount: float = 100.0
    max_cash_risk: float = 100.0
    allow_live_submit: bool = False


@dataclass(frozen=True)
class MarketQuote:
    venue: str
    market_id: str
    title: str
    url: str
    yes_bid: float | None
    yes_ask: float | None
    no_bid: float | None = None
    no_ask: float | None = None
    liquidity: float | None = None
    volume: float | None = None


@dataclass(frozen=True)
class OrderSizing:
    mode: SizingMode
    amount: float
    cost: float
    max_loss: float
    max_payout: float
    shares: float


@dataclass(frozen=True)
class OrderTicket:
    ticket_id: str
    created_at: str
    status: TicketStatus
    venue: str
    market_id: str
    title: str
    url: str
    side: Side
    forecast_yes: float
    fair_side_probability: float
    yes_bid: float | None
    yes_ask: float | None
    no_bid: float | None
    no_ask: float | None
    executable_price: float | None
    limit_price: float | None
    spread: float | None
    edge: float | None
    sizing: OrderSizing | None
    blocked_reasons: tuple[str, ...]
    policy: ExecutionPolicy
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def isoformat_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_part(value: str, *, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return (cleaned or "market")[:max_len]


def _round_money(value: float) -> float:
    return round(value + 1e-12, 6)


def _valid_probability(value: float | None) -> bool:
    return value is not None and 0 < value < 1


def side_price(quote: MarketQuote, side: Side) -> float | None:
    if side == "YES":
        return quote.yes_ask if _valid_probability(quote.yes_ask) else None
    if _valid_probability(quote.no_ask):
        return quote.no_ask
    if _valid_probability(quote.yes_bid):
        return 1.0 - quote.yes_bid
    return None


def side_bid(quote: MarketQuote, side: Side) -> float | None:
    if side == "YES":
        return quote.yes_bid if _valid_probability(quote.yes_bid) else None
    if _valid_probability(quote.no_bid):
        return quote.no_bid
    if _valid_probability(quote.yes_ask):
        return 1.0 - quote.yes_ask
    return None


def side_spread(quote: MarketQuote, side: Side) -> float | None:
    bid = side_bid(quote, side)
    ask = side_price(quote, side)
    if bid is None or ask is None:
        return None
    return max(0.0, ask - bid)


def fair_side_probability(forecast_yes: float, side: Side) -> float:
    return forecast_yes if side == "YES" else 1.0 - forecast_yes


def executable_edge(quote: MarketQuote, forecast_yes: float, side: Side) -> float | None:
    price = side_price(quote, side)
    if price is None:
        return None
    return fair_side_probability(forecast_yes, side) - price


def choose_side(quote: MarketQuote, forecast_yes: float) -> Side:
    yes_edge = executable_edge(quote, forecast_yes, "YES")
    no_edge = executable_edge(quote, forecast_yes, "NO")
    if yes_edge is None and no_edge is None:
        return "YES" if forecast_yes >= 0.5 else "NO"
    if yes_edge is None:
        return "NO"
    if no_edge is None:
        return "YES"
    return "YES" if yes_edge >= no_edge else "NO"


def size_order(price: float, policy: ExecutionPolicy) -> OrderSizing:
    if policy.amount <= 0:
        raise ValueError("policy amount must be positive")
    if not _valid_probability(price):
        raise ValueError("price must be inside (0, 1)")

    if policy.sizing_mode == "max_payout":
        max_payout = policy.amount
        shares = max_payout
        cost = max_payout * price
    elif policy.sizing_mode == "cash":
        cost = policy.amount
        shares = cost / price
        max_payout = shares
    else:  # pragma: no cover - Literal protects normal callers
        raise ValueError(f"unknown sizing mode: {policy.sizing_mode}")

    return OrderSizing(
        mode=policy.sizing_mode,
        amount=_round_money(policy.amount),
        cost=_round_money(cost),
        max_loss=_round_money(cost),
        max_payout=_round_money(max_payout),
        shares=_round_money(shares),
    )


def build_order_ticket(
    *,
    quote: MarketQuote,
    forecast_yes: float,
    policy: ExecutionPolicy | None = None,
    side: Side | None = None,
    now: datetime | None = None,
    notes: str = "",
) -> OrderTicket:
    policy = policy or ExecutionPolicy()
    now = now or datetime.now(timezone.utc)
    created_at = isoformat_z(now)

    blocked: list[str] = []
    if not _valid_probability(forecast_yes):
        blocked.append(f"forecast_yes must be inside (0, 1); got {forecast_yes!r}")

    chosen_side: Side = side or choose_side(quote, forecast_yes if _valid_probability(forecast_yes) else 0.5)
    price = side_price(quote, chosen_side)
    spread = side_spread(quote, chosen_side)
    fair = fair_side_probability(forecast_yes, chosen_side) if _valid_probability(forecast_yes) else 0.0
    edge = fair - price if price is not None else None
    sizing = size_order(price, policy) if price is not None else None

    if price is None:
        blocked.append(f"missing executable {chosen_side} ask/price")
    if spread is None:
        blocked.append("missing actionable bid/ask spread")
    elif spread > policy.max_spread:
        blocked.append(f"spread {spread:.3f} exceeds max {policy.max_spread:.3f}")
    if edge is None:
        blocked.append("missing executable edge")
    elif edge < policy.min_edge:
        blocked.append(f"edge {edge:.3f} below min {policy.min_edge:.3f}")
    if sizing is not None and sizing.max_loss > policy.max_cash_risk:
        blocked.append(f"max loss {sizing.max_loss:.2f} exceeds policy cap {policy.max_cash_risk:.2f}")

    status: TicketStatus = "blocked" if blocked else "draft"
    ticket_id = "-".join(
        [
            "rime-ticket",
            safe_part(quote.venue, max_len=20),
            safe_part(quote.market_id, max_len=60),
            created_at.replace("-", "").replace(":", "").replace("Z", "Z"),
        ]
    )

    return OrderTicket(
        ticket_id=ticket_id,
        created_at=created_at,
        status=status,
        venue=quote.venue,
        market_id=quote.market_id,
        title=quote.title,
        url=quote.url,
        side=chosen_side,
        forecast_yes=forecast_yes,
        fair_side_probability=_round_money(fair),
        yes_bid=quote.yes_bid,
        yes_ask=quote.yes_ask,
        no_bid=quote.no_bid,
        no_ask=quote.no_ask,
        executable_price=_round_money(price) if price is not None else None,
        limit_price=_round_money(price) if price is not None else None,
        spread=_round_money(spread) if spread is not None else None,
        edge=_round_money(edge) if edge is not None else None,
        sizing=sizing,
        blocked_reasons=tuple(blocked),
        policy=policy,
        notes=notes,
    )


def write_ticket(ticket: OrderTicket, ticket_dir: str | Path) -> Path:
    directory = Path(ticket_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{ticket.ticket_id}.json"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(ticket.to_json() + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def ticket_summary(ticket: OrderTicket) -> str:
    lines = [
        f"{ticket.status.upper()} {ticket.side} ticket: {ticket.title}",
        f"venue={ticket.venue} market={ticket.market_id}",
        f"forecast_yes={ticket.forecast_yes:.3f} executable_price={ticket.executable_price}",
        f"edge={ticket.edge} spread={ticket.spread}",
    ]
    if ticket.sizing:
        lines.append(
            f"sizing={ticket.sizing.mode} amount={ticket.sizing.amount} cost={ticket.sizing.cost} max_payout={ticket.sizing.max_payout}"
        )
    if ticket.blocked_reasons:
        lines.append("blocked=" + "; ".join(ticket.blocked_reasons))
    return "\n".join(lines)
