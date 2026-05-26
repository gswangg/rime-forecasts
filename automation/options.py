from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import json
import math
import re
from typing import Any, Iterable, Literal, Protocol

from .timeutil import isoformat_z, parse_iso

OptionRight = Literal["call", "put"]
OptionStructureType = Literal["long_call", "long_put", "debit_vertical", "credit_vertical"]
OptionThesisDirection = Literal["up", "down"]
OptionTicketStatus = Literal["draft", "blocked", "paper_open", "paper_closed"]


@dataclass(frozen=True)
class OptionContract:
    underlying: str
    provider: str
    symbol: str
    expiry: date
    right: OptionRight
    strike: float
    style: str
    settlement: str
    multiplier: int
    underlying_bid: float | None
    underlying_ask: float | None
    bid: float | None
    ask: float | None
    last: float | None
    mid: float | None
    iv: float | None
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    volume: float
    open_interest: float
    quote_ts: datetime | None
    raw: dict[str, Any]

    @property
    def spread(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return max(0.0, self.ask - self.bid)

    @property
    def executable_debit(self) -> float | None:
        return self.ask

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["expiry"] = self.expiry.isoformat()
        data["quote_ts"] = isoformat_z(self.quote_ts) if self.quote_ts is not None else None
        return data


@dataclass(frozen=True)
class OptionChainSnapshot:
    underlying: str
    provider: str
    quote_ts: datetime | None
    underlying_bid: float | None
    underlying_ask: float | None
    contracts: tuple[OptionContract, ...]
    raw: dict[str, Any]

    @property
    def quote_delay_seconds(self) -> int | None:
        if self.quote_ts is None:
            return None
        return max(0, int((datetime.now(timezone.utc) - self.quote_ts).total_seconds()))

    @property
    def underlying_mid(self) -> float | None:
        if self.underlying_bid is None or self.underlying_ask is None:
            return None
        if self.underlying_bid <= 0 or self.underlying_ask <= 0 or self.underlying_bid > self.underlying_ask:
            return None
        return (self.underlying_bid + self.underlying_ask) / 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "underlying": self.underlying,
            "provider": self.provider,
            "quote_ts": isoformat_z(self.quote_ts) if self.quote_ts is not None else None,
            "quote_delay_seconds": self.quote_delay_seconds,
            "underlying_bid": self.underlying_bid,
            "underlying_ask": self.underlying_ask,
            "contracts": [contract.to_dict() for contract in self.contracts],
            "raw": self.raw,
        }


class OptionChainProvider(Protocol):
    provider: str

    def list_expiries(self, underlying: str) -> tuple[date, ...]:
        ...

    def fetch_chain(self, underlying: str, expiry: date | None = None) -> OptionChainSnapshot:
        ...

    def fetch_quote(self, symbol: str) -> OptionContract:
        ...


@dataclass(frozen=True)
class OptionQuoteFilterConfig:
    allow_underlyings: tuple[str, ...] = ()
    min_days_to_expiry: int = 1
    max_days_to_expiry: int = 45
    min_volume: float = 100.0
    min_open_interest: float = 500.0
    min_premium: float = 0.05
    max_single_leg_abs_spread: float = 0.05
    max_single_leg_spread_pct_of_mid: float = 0.15
    max_quote_age_seconds: int | None = None


@dataclass(frozen=True)
class OptionLeg:
    contract: OptionContract
    quantity: int

    @property
    def action(self) -> str:
        return "buy" if self.quantity > 0 else "sell"

    def to_dict(self) -> dict[str, Any]:
        return {"quantity": self.quantity, "action": self.action, "contract": self.contract.to_dict()}


@dataclass(frozen=True)
class OptionStructure:
    structure_type: OptionStructureType
    underlying: str
    expiry: date
    right: OptionRight
    legs: tuple[OptionLeg, ...]
    net_debit: float | None
    net_credit: float | None
    max_loss: float | None
    max_gain: float | None
    breakeven: float | None
    width: float | None
    max_loss_per_contract: float | None
    max_gain_per_contract: float | None
    executable_spread: float | None
    net_delta: float | None
    net_gamma: float | None
    net_theta: float | None
    net_vega: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure_type": self.structure_type,
            "underlying": self.underlying,
            "expiry": self.expiry.isoformat(),
            "right": self.right,
            "legs": [leg.to_dict() for leg in self.legs],
            "net_debit": self.net_debit,
            "net_credit": self.net_credit,
            "max_loss": self.max_loss,
            "max_gain": self.max_gain,
            "breakeven": self.breakeven,
            "width": self.width,
            "max_loss_per_contract": self.max_loss_per_contract,
            "max_gain_per_contract": self.max_gain_per_contract,
            "executable_spread": self.executable_spread,
            "net_delta": self.net_delta,
            "net_gamma": self.net_gamma,
            "net_theta": self.net_theta,
            "net_vega": self.net_vega,
        }


@dataclass(frozen=True)
class OptionEdgeEvaluation:
    structure: OptionStructure
    model_fair_value: float
    edge_dollars: float | None
    edge_pct_of_risk: float | None
    model_probability: float | None
    breakeven_probability: float | None
    passes: bool
    blocked_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "structure": self.structure.to_dict(),
            "model_fair_value": self.model_fair_value,
            "edge_dollars": self.edge_dollars,
            "edge_pct_of_risk": self.edge_pct_of_risk,
            "model_probability": self.model_probability,
            "breakeven_probability": self.breakeven_probability,
            "passes": self.passes,
            "blocked_reasons": list(self.blocked_reasons),
        }


@dataclass(frozen=True)
class OptionThesis:
    id: str
    direction: OptionThesisDirection
    target_price: float
    target_probability: float
    event_date: date | None
    option_expiry: date | None
    max_loss_cap: float
    min_reward_risk: float
    min_edge_pct_of_risk: float
    min_probability_margin: float | None
    allowed_structures: tuple[OptionStructureType, ...]
    thesis: str
    catalyst: str | None = None
    planned_exit: str | None = None
    falsifier: str | None = None
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "direction": self.direction,
            "target_price": self.target_price,
            "target_probability": self.target_probability,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "option_expiry": self.option_expiry.isoformat() if self.option_expiry else None,
            "max_loss_cap": self.max_loss_cap,
            "min_reward_risk": self.min_reward_risk,
            "min_edge_pct_of_risk": self.min_edge_pct_of_risk,
            "min_probability_margin": self.min_probability_margin,
            "allowed_structures": list(self.allowed_structures),
            "thesis": self.thesis,
            "catalyst": self.catalyst,
            "planned_exit": self.planned_exit,
            "falsifier": self.falsifier,
        }


@dataclass(frozen=True)
class OptionOpportunity:
    thesis: OptionThesis
    structure: OptionStructure
    evaluation: OptionEdgeEvaluation
    model_payoff_if_hit: float | None
    reward_risk: float | None
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "thesis": self.thesis.to_dict(),
            "structure": self.structure.to_dict(),
            "evaluation": self.evaluation.to_dict(),
            "model_payoff_if_hit": self.model_payoff_if_hit,
            "reward_risk": self.reward_risk,
            "score": self.score,
        }


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _float_or_zero(value: Any) -> float:
    parsed = _float_or_none(value)
    return parsed if parsed is not None else 0.0


def _int_or_default(value: Any, default: int) -> int:
    parsed = _float_or_none(value)
    if parsed is None:
        return default
    return int(parsed)


def _first(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _parse_expiry(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str) or not value.strip():
        raise ValueError("option expiry must be a non-empty ISO date")
    text = value.strip()
    if "T" in text or text.endswith("Z"):
        return parse_iso(text).date()
    return date.fromisoformat(text)


def _parse_quote_ts(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return parse_iso(str(value))


def _normalize_right(value: Any) -> OptionRight:
    text = str(value or "").strip().lower()
    if text in {"c", "call", "calls"}:
        return "call"
    if text in {"p", "put", "puts"}:
        return "put"
    raise ValueError(f"unknown option right: {value!r}")


def _normalized_underlying(value: Any) -> str:
    underlying = str(value or "").strip().upper()
    if not underlying:
        raise ValueError("option underlying is required")
    return underlying


def _normalized_provider(value: Any) -> str:
    provider = str(value or "").strip().lower()
    if not provider:
        raise ValueError("option provider is required")
    return provider


def _with_defaults(raw: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    merged.update(raw)
    return merged


def normalize_contract(raw: dict[str, Any], *, defaults: dict[str, Any] | None = None) -> OptionContract:
    if not isinstance(raw, dict):
        raise TypeError("option contract must be a mapping")
    merged = _with_defaults(raw, defaults or {})
    bid = _float_or_none(_first(merged.get("bid"), merged.get("best_bid"), merged.get("bestBid")))
    ask = _float_or_none(_first(merged.get("ask"), merged.get("best_ask"), merged.get("bestAsk")))
    explicit_mid = _float_or_none(merged.get("mid"))
    mid = explicit_mid
    if mid is None and bid is not None and ask is not None and bid <= ask:
        mid = (bid + ask) / 2

    symbol = str(_first(merged.get("symbol"), merged.get("occ_symbol"), merged.get("contract_symbol")) or "").strip()
    if not symbol:
        raise ValueError("option symbol is required")

    strike = _float_or_none(merged.get("strike"))
    if strike is None:
        raise ValueError("option strike is required")

    return OptionContract(
        underlying=_normalized_underlying(merged.get("underlying")),
        provider=_normalized_provider(merged.get("provider")),
        symbol=symbol,
        expiry=_parse_expiry(_first(merged.get("expiry"), merged.get("expiration"), merged.get("expiration_date"))),
        right=_normalize_right(_first(merged.get("right"), merged.get("type"), merged.get("option_type"))),
        strike=strike,
        style=str(_first(merged.get("style"), "american")).strip().lower(),
        settlement=str(_first(merged.get("settlement"), "physical")).strip().lower(),
        multiplier=_int_or_default(merged.get("multiplier"), 100),
        underlying_bid=_float_or_none(_first(merged.get("underlying_bid"), merged.get("underlyingBid"))),
        underlying_ask=_float_or_none(_first(merged.get("underlying_ask"), merged.get("underlyingAsk"))),
        bid=bid,
        ask=ask,
        last=_float_or_none(_first(merged.get("last"), merged.get("last_price"), merged.get("lastPrice"))),
        mid=mid,
        iv=_float_or_none(_first(merged.get("iv"), merged.get("implied_volatility"), merged.get("impliedVolatility"))),
        delta=_float_or_none(merged.get("delta")),
        gamma=_float_or_none(merged.get("gamma")),
        theta=_float_or_none(merged.get("theta")),
        vega=_float_or_none(merged.get("vega")),
        volume=_float_or_zero(merged.get("volume")),
        open_interest=_float_or_zero(_first(merged.get("open_interest"), merged.get("openInterest"), merged.get("oi"))),
        quote_ts=_parse_quote_ts(_first(merged.get("quote_ts"), merged.get("quoteTime"), merged.get("quote_time"))),
        raw=dict(raw),
    )


def parse_option_chain_snapshot(raw: dict[str, Any] | list[dict[str, Any]]) -> OptionChainSnapshot:
    if isinstance(raw, list):
        raw = {"contracts": raw}
    if not isinstance(raw, dict):
        raise TypeError("option chain snapshot must be a mapping or list of contracts")

    contracts_raw = _first(raw.get("contracts"), raw.get("options"), raw.get("data"))
    if not isinstance(contracts_raw, list):
        raise ValueError("option chain snapshot requires a contracts/options list")

    defaults = {
        "underlying": raw.get("underlying"),
        "provider": raw.get("provider"),
        "quote_ts": raw.get("quote_ts") or raw.get("quoteTime") or raw.get("quote_time"),
        "underlying_bid": raw.get("underlying_bid") or raw.get("underlyingBid"),
        "underlying_ask": raw.get("underlying_ask") or raw.get("underlyingAsk"),
    }
    contracts = tuple(normalize_contract(contract, defaults=defaults) for contract in contracts_raw)
    if contracts:
        underlying = contracts[0].underlying
        provider = contracts[0].provider
        quote_ts = contracts[0].quote_ts
        underlying_bid = contracts[0].underlying_bid
        underlying_ask = contracts[0].underlying_ask
    else:
        underlying = _normalized_underlying(raw.get("underlying"))
        provider = _normalized_provider(raw.get("provider"))
        quote_ts = _parse_quote_ts(defaults["quote_ts"])
        underlying_bid = _float_or_none(defaults["underlying_bid"])
        underlying_ask = _float_or_none(defaults["underlying_ask"])

    return OptionChainSnapshot(
        underlying=underlying,
        provider=provider,
        quote_ts=quote_ts,
        underlying_bid=underlying_bid,
        underlying_ask=underlying_ask,
        contracts=contracts,
        raw=dict(raw),
    )


def load_option_chain_snapshot(path: str | Path) -> OptionChainSnapshot:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "chain" in data:
        data = data["chain"]
    return parse_option_chain_snapshot(data)


@dataclass(frozen=True)
class FixtureOptionProvider:
    """Credential-free provider adapter backed by a normalized fixture snapshot."""

    snapshot: OptionChainSnapshot
    provider: str = "fixture"

    @classmethod
    def from_file(cls, path: str | Path) -> "FixtureOptionProvider":
        snapshot = load_option_chain_snapshot(path)
        return cls(snapshot=snapshot, provider=snapshot.provider)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "FixtureOptionProvider":
        snapshot = parse_option_chain_snapshot(raw.get("chain", raw))
        return cls(snapshot=snapshot, provider=snapshot.provider)

    def list_expiries(self, underlying: str) -> tuple[date, ...]:
        normalized = _normalized_underlying(underlying)
        expiries = {contract.expiry for contract in self.snapshot.contracts if contract.underlying == normalized}
        return tuple(sorted(expiries))

    def fetch_chain(self, underlying: str, expiry: date | None = None) -> OptionChainSnapshot:
        normalized = _normalized_underlying(underlying)
        contracts = tuple(
            contract
            for contract in self.snapshot.contracts
            if contract.underlying == normalized and (expiry is None or contract.expiry == expiry)
        )
        if not contracts:
            raise KeyError(f"no fixture option chain for {normalized} {expiry or ''}".strip())
        first = contracts[0]
        return OptionChainSnapshot(
            underlying=normalized,
            provider=self.provider,
            quote_ts=self.snapshot.quote_ts or first.quote_ts,
            underlying_bid=self.snapshot.underlying_bid or first.underlying_bid,
            underlying_ask=self.snapshot.underlying_ask or first.underlying_ask,
            contracts=contracts,
            raw={"source": "fixture", "filtered_expiry": expiry.isoformat() if expiry else None},
        )

    def fetch_quote(self, symbol: str) -> OptionContract:
        for contract in self.snapshot.contracts:
            if contract.symbol == symbol:
                return contract
        raise KeyError(f"no fixture option quote for {symbol}")


def quote_delay_seconds(quote_ts: datetime | None, *, now: datetime) -> int | None:
    if quote_ts is None:
        return None
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0, int((now.astimezone(timezone.utc) - quote_ts).total_seconds()))


def days_to_expiry(expiry: date, *, now: datetime) -> int:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (expiry - now.astimezone(timezone.utc).date()).days


# US market holidays through 2027 (NYSE-observed, full closures only).
# Used by SA scanner / options-daemon emission guards. Updated annually as the
# NYSE schedule is published.
US_MARKET_HOLIDAYS: tuple[str, ...] = (
    # 2026
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
    "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    # 2027
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
    "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
)


def is_us_market_open_at(ts: datetime) -> bool:
    """Approximate whether the US equity options market is open at ``ts``.

    Returns True only for weekday RTH (13:30-20:00 UTC = 09:30-16:00 ET
    ignoring DST) on non-holiday calendar dates. Half-day closes are still
    reported as open here; the chain-staleness guard handles those cases
    operationally.
    """
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ts = ts.astimezone(timezone.utc)
    if ts.weekday() >= 5:
        return False
    if ts.date().isoformat() in US_MARKET_HOLIDAYS:
        return False
    minutes = ts.hour * 60 + ts.minute
    # 13:30 UTC = 810 minutes, 20:00 UTC = 1200 minutes
    return 13 * 60 + 30 <= minutes <= 20 * 60


def chain_quote_is_stale(
    snapshot: OptionChainSnapshot,
    *,
    now: datetime,
    max_delay_seconds: int = 4 * 3600,
) -> tuple[bool, str | None]:
    """Return (is_stale, reason) for a chain snapshot.

    Treats absent quote_ts, weekend/holiday timestamps, and any quote older than
    ``max_delay_seconds`` as stale. The threshold default of 4h covers ordinary
    intraday daemon polls without flagging routine overnight gaps.
    """
    if snapshot.quote_ts is None:
        return True, "chain quote_ts missing"
    if not is_us_market_open_at(snapshot.quote_ts):
        return True, f"chain quote_ts {isoformat_z(snapshot.quote_ts)} is outside US RTH"
    delay = (now - snapshot.quote_ts).total_seconds() if now.tzinfo else (now.replace(tzinfo=timezone.utc) - snapshot.quote_ts).total_seconds()
    if delay > max_delay_seconds:
        return True, f"chain quote_ts is {delay/3600:.1f}h old (max {max_delay_seconds/3600:.1f}h)"
    return False, None


def atm_straddle_implied_move(
    snapshot: OptionChainSnapshot,
    *,
    expiry: date | None = None,
    spot: float | None = None,
) -> dict[str, Any] | None:
    """Estimate the ATM-straddle implied move to a given expiry.

    The straddle premium = call mid + put mid at the strike nearest to spot.
    Implied move (to expiry) = straddle / spot. This is approximately the
    one-sigma price range the chain is pricing for the underlying by the
    target expiry. It is the natural hurdle a thesis-target move must clear:
    a target move smaller than the implied move means the option market
    already prices the directional outcome inside its distribution.

    Returns None if there is no usable call/put pair at the chosen expiry.
    """
    if not snapshot.contracts:
        return None
    if spot is None:
        spot = snapshot.underlying_mid
    if spot is None or spot <= 0:
        return None
    candidates = [c for c in snapshot.contracts if expiry is None or c.expiry == expiry]
    if not candidates:
        return None
    # Pick the strike nearest to spot that has both a call and a put with usable mids
    by_strike: dict[float, dict[str, OptionContract]] = {}
    for c in candidates:
        if c.mid is None or c.mid <= 0:
            continue
        by_strike.setdefault(c.strike, {})[c.right] = c
    pairs = [(strike, legs) for strike, legs in by_strike.items() if "call" in legs and "put" in legs]
    if not pairs:
        return None
    pairs.sort(key=lambda item: (abs(item[0] - spot), item[0]))
    strike, legs = pairs[0]
    call = legs["call"]
    put = legs["put"]
    straddle = (call.mid or 0.0) + (put.mid or 0.0)
    if straddle <= 0:
        return None
    implied_move = straddle / spot
    return {
        "strike": strike,
        "spot": spot,
        "expiry": call.expiry.isoformat(),
        "callSymbol": call.symbol,
        "putSymbol": put.symbol,
        "callMid": call.mid,
        "putMid": put.mid,
        "straddle": _round_money(straddle),
        "impliedMovePct": _round_metric(implied_move),
    }


def target_move_pct_from_spot(*, direction: str, target_price: float, spot: float) -> float | None:
    if not spot or spot <= 0 or not target_price or target_price <= 0:
        return None
    if direction == "up":
        return target_price / spot - 1
    if direction == "down":
        return spot / target_price - 1
    return None


def single_leg_spread_limit(mid: float, config: OptionQuoteFilterConfig | None = None) -> float:
    config = config or OptionQuoteFilterConfig()
    return max(config.max_single_leg_abs_spread, config.max_single_leg_spread_pct_of_mid * mid)


def has_corporate_action_ambiguity(contract: OptionContract) -> bool:
    raw = contract.raw
    values = (
        raw.get("corporate_action"),
        raw.get("corporateAction"),
        raw.get("adjusted"),
        raw.get("non_standard"),
        raw.get("nonStandard"),
    )
    return any(bool(value) for value in values)


def contract_quote_filter_reason(
    contract: OptionContract,
    *,
    now: datetime,
    config: OptionQuoteFilterConfig | None = None,
) -> tuple[bool, str]:
    config = config or OptionQuoteFilterConfig()
    allow = tuple(symbol.upper() for symbol in config.allow_underlyings)
    if allow and contract.underlying.upper() not in allow:
        return False, f"underlying {contract.underlying} not in allowlist"

    dte = days_to_expiry(contract.expiry, now=now)
    if dte < config.min_days_to_expiry or dte > config.max_days_to_expiry:
        return False, f"expiry {dte}d outside {config.min_days_to_expiry}-{config.max_days_to_expiry}d window"

    if contract.multiplier <= 0:
        return False, "invalid contract multiplier"

    if contract.bid is None or contract.ask is None:
        return False, "missing bid/ask"
    if contract.bid <= 0 or contract.ask <= 0 or contract.bid > contract.ask:
        return False, "invalid bid/ask"

    mid = contract.mid if contract.mid is not None else (contract.bid + contract.ask) / 2
    if mid <= 0:
        return False, "invalid mid premium"
    if contract.ask < config.min_premium:
        return False, f"premium {contract.ask:.2f} below min {config.min_premium:.2f}"

    spread = contract.ask - contract.bid
    limit = single_leg_spread_limit(mid, config)
    if spread > limit:
        return False, f"spread {spread:.2f} exceeds max {limit:.2f}"

    if contract.volume < config.min_volume and contract.open_interest < config.min_open_interest:
        return False, f"liquidity below min volume {config.min_volume:.0f} or open interest {config.min_open_interest:.0f}"

    if has_corporate_action_ambiguity(contract):
        return False, "corporate-action ambiguity"

    if config.max_quote_age_seconds is not None:
        if contract.quote_ts is None:
            return False, "missing quote timestamp"
        age = (now.astimezone(timezone.utc) - contract.quote_ts).total_seconds()
        if age < 0:
            return False, "quote timestamp is in the future"
        if age > config.max_quote_age_seconds:
            return False, f"quote age {age:.0f}s exceeds max {config.max_quote_age_seconds}s"

    return True, "ok"


def filter_contracts(
    contracts: Iterable[OptionContract],
    *,
    now: datetime,
    config: OptionQuoteFilterConfig | None = None,
) -> tuple[OptionContract, ...]:
    accepted: list[OptionContract] = []
    for contract in contracts:
        ok, _ = contract_quote_filter_reason(contract, now=now, config=config)
        if ok:
            accepted.append(contract)
    return tuple(accepted)


def _round_money(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value + 1e-12, 6)


def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value + 1e-12, 8)


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def time_to_expiry_years(expiry: date, *, now: datetime) -> float:
    dte = max(0, days_to_expiry(expiry, now=now))
    return dte / 365.0


def black_scholes_d1(spot: float, strike: float, time_years: float, volatility: float, risk_free_rate: float = 0.0) -> float:
    if spot <= 0 or strike <= 0 or time_years <= 0 or volatility <= 0:
        raise ValueError("spot, strike, time, and volatility must be positive")
    return (math.log(spot / strike) + (risk_free_rate + 0.5 * volatility * volatility) * time_years) / (volatility * math.sqrt(time_years))


def black_scholes_price(
    right: OptionRight,
    *,
    spot: float,
    strike: float,
    time_years: float,
    volatility: float,
    risk_free_rate: float = 0.0,
) -> float:
    if time_years <= 0:
        return max(0.0, spot - strike) if right == "call" else max(0.0, strike - spot)
    d1 = black_scholes_d1(spot, strike, time_years, volatility, risk_free_rate)
    d2 = d1 - volatility * math.sqrt(time_years)
    discount = math.exp(-risk_free_rate * time_years)
    if right == "call":
        return spot * normal_cdf(d1) - strike * discount * normal_cdf(d2)
    if right == "put":
        return strike * discount * normal_cdf(-d2) - spot * normal_cdf(-d1)
    raise ValueError(f"unknown option right: {right!r}")


def risk_neutral_probability_above(
    *,
    spot: float,
    threshold: float,
    time_years: float,
    volatility: float,
    risk_free_rate: float = 0.0,
) -> float:
    if time_years <= 0:
        return 1.0 if spot > threshold else 0.0
    d1 = black_scholes_d1(spot, threshold, time_years, volatility, risk_free_rate)
    d2 = d1 - volatility * math.sqrt(time_years)
    return normal_cdf(d2)


def risk_neutral_probability_between(
    *,
    spot: float,
    lower: float,
    upper: float,
    time_years: float,
    volatility: float,
    risk_free_rate: float = 0.0,
) -> float:
    if lower >= upper:
        raise ValueError("lower threshold must be below upper threshold")
    return max(
        0.0,
        risk_neutral_probability_above(
            spot=spot,
            threshold=lower,
            time_years=time_years,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
        )
        - risk_neutral_probability_above(
            spot=spot,
            threshold=upper,
            time_years=time_years,
            volatility=volatility,
            risk_free_rate=risk_free_rate,
        ),
    )


def _leg_entry_value(leg: OptionLeg) -> float | None:
    if leg.quantity > 0:
        return leg.contract.ask
    return leg.contract.bid


def _leg_exit_value_at_mid(leg: OptionLeg) -> float | None:
    return leg.contract.mid


def _net_debit_per_share(legs: Iterable[OptionLeg]) -> float | None:
    total = 0.0
    for leg in legs:
        entry = _leg_entry_value(leg)
        if entry is None:
            return None
        total += leg.quantity * entry
    return total


def _net_mid_per_share(legs: Iterable[OptionLeg]) -> float | None:
    total = 0.0
    for leg in legs:
        mid = _leg_exit_value_at_mid(leg)
        if mid is None:
            return None
        total += leg.quantity * mid
    return total


def _net_greek(legs: Iterable[OptionLeg], attr: str) -> float | None:
    total = 0.0
    seen = False
    for leg in legs:
        value = getattr(leg.contract, attr)
        if value is None:
            continue
        # Short option positions have opposite Greek exposure from the quoted long-contract Greek.
        total += leg.quantity * value
        seen = True
    return total if seen else None


def _same_expiry_right(a: OptionContract, b: OptionContract) -> None:
    if a.underlying != b.underlying:
        raise ValueError("spread legs must share underlying")
    if a.expiry != b.expiry:
        raise ValueError("spread legs must share expiry")
    if a.right != b.right:
        raise ValueError("vertical legs must share right")
    if a.multiplier != b.multiplier:
        raise ValueError("spread legs must share multiplier")


def _structure_from_legs(
    *,
    structure_type: OptionStructureType,
    legs: tuple[OptionLeg, ...],
    max_loss_per_share: float | None,
    max_gain_per_share: float | None,
    breakeven: float | None,
    width: float | None,
) -> OptionStructure:
    first = legs[0].contract
    net_debit_per_share = _net_debit_per_share(legs)
    net_credit_per_share = -net_debit_per_share if net_debit_per_share is not None and net_debit_per_share < 0 else None
    net_debit = net_debit_per_share if net_debit_per_share is not None and net_debit_per_share > 0 else None
    multiplier = first.multiplier
    max_loss = max_loss_per_share * multiplier if max_loss_per_share is not None else None
    max_gain = max_gain_per_share * multiplier if max_gain_per_share is not None else None
    executable_spread = None
    mid_value = _net_mid_per_share(legs)
    if net_debit_per_share is not None and mid_value is not None:
        executable_spread = abs(net_debit_per_share - mid_value) * multiplier

    return OptionStructure(
        structure_type=structure_type,
        underlying=first.underlying,
        expiry=first.expiry,
        right=first.right,
        legs=legs,
        net_debit=_round_money(net_debit * multiplier) if net_debit is not None else None,
        net_credit=_round_money(net_credit_per_share * multiplier) if net_credit_per_share is not None else None,
        max_loss=_round_money(max_loss),
        max_gain=_round_money(max_gain),
        breakeven=_round_metric(breakeven),
        width=_round_metric(width),
        max_loss_per_contract=_round_metric(max_loss_per_share),
        max_gain_per_contract=_round_metric(max_gain_per_share),
        executable_spread=_round_money(executable_spread),
        net_delta=_round_metric(_net_greek(legs, "delta")),
        net_gamma=_round_metric(_net_greek(legs, "gamma")),
        net_theta=_round_metric(_net_greek(legs, "theta")),
        net_vega=_round_metric(_net_greek(legs, "vega")),
    )


def build_long_option(contract: OptionContract) -> OptionStructure:
    if contract.ask is None:
        raise ValueError("long option requires ask")
    max_loss_per_share = contract.ask
    max_gain_per_share = None
    breakeven = contract.strike + contract.ask if contract.right == "call" else contract.strike - contract.ask
    return _structure_from_legs(
        structure_type="long_call" if contract.right == "call" else "long_put",
        legs=(OptionLeg(contract=contract, quantity=1),),
        max_loss_per_share=max_loss_per_share,
        max_gain_per_share=max_gain_per_share,
        breakeven=breakeven,
        width=None,
    )


def build_debit_vertical(long_contract: OptionContract, short_contract: OptionContract) -> OptionStructure:
    _same_expiry_right(long_contract, short_contract)
    if long_contract.ask is None or short_contract.bid is None:
        raise ValueError("debit vertical requires long ask and short bid")
    if long_contract.right == "call" and long_contract.strike >= short_contract.strike:
        raise ValueError("call debit vertical requires lower long strike and higher short strike")
    if long_contract.right == "put" and long_contract.strike <= short_contract.strike:
        raise ValueError("put debit vertical requires higher long strike and lower short strike")
    width = abs(short_contract.strike - long_contract.strike)
    debit = long_contract.ask - short_contract.bid
    if debit <= 0:
        raise ValueError("debit vertical net debit must be positive")
    max_loss_per_share = debit
    max_gain_per_share = width - debit
    breakeven = long_contract.strike + debit if long_contract.right == "call" else long_contract.strike - debit
    return _structure_from_legs(
        structure_type="debit_vertical",
        legs=(OptionLeg(long_contract, 1), OptionLeg(short_contract, -1)),
        max_loss_per_share=max_loss_per_share,
        max_gain_per_share=max_gain_per_share,
        breakeven=breakeven,
        width=width,
    )


def build_credit_vertical(short_contract: OptionContract, long_contract: OptionContract) -> OptionStructure:
    _same_expiry_right(short_contract, long_contract)
    if short_contract.bid is None or long_contract.ask is None:
        raise ValueError("credit vertical requires short bid and long ask")
    if short_contract.right == "call" and short_contract.strike >= long_contract.strike:
        raise ValueError("call credit vertical requires lower short strike and higher long strike")
    if short_contract.right == "put" and short_contract.strike <= long_contract.strike:
        raise ValueError("put credit vertical requires higher short strike and lower long strike")
    width = abs(long_contract.strike - short_contract.strike)
    credit = short_contract.bid - long_contract.ask
    if credit <= 0:
        raise ValueError("credit vertical net credit must be positive")
    max_loss_per_share = width - credit
    max_gain_per_share = credit
    breakeven = short_contract.strike + credit if short_contract.right == "call" else short_contract.strike - credit
    return _structure_from_legs(
        structure_type="credit_vertical",
        legs=(OptionLeg(short_contract, -1), OptionLeg(long_contract, 1)),
        max_loss_per_share=max_loss_per_share,
        max_gain_per_share=max_gain_per_share,
        breakeven=breakeven,
        width=width,
    )


def breakeven_probability(structure: OptionStructure) -> float | None:
    if structure.max_loss is None or structure.max_gain is None:
        return None
    total = structure.max_loss + structure.max_gain
    if total <= 0:
        return None
    return structure.max_loss / total


def evaluate_structure_edge(
    structure: OptionStructure,
    *,
    model_fair_value: float,
    min_edge_pct_of_risk: float = 0.20,
    model_probability: float | None = None,
    min_probability_margin: float | None = None,
    max_loss_cap: float | None = None,
) -> OptionEdgeEvaluation:
    blocked: list[str] = []
    if model_fair_value < 0:
        blocked.append("model fair value must be non-negative")

    cost_or_collateral = structure.max_loss
    if cost_or_collateral is None or cost_or_collateral <= 0:
        blocked.append("missing positive max loss")

    if max_loss_cap is not None and structure.max_loss is not None and structure.max_loss > max_loss_cap:
        blocked.append(f"max loss {structure.max_loss:.2f} exceeds cap {max_loss_cap:.2f}")

    if structure.net_debit is not None:
        edge_dollars = model_fair_value - structure.net_debit
    elif structure.net_credit is not None:
        edge_dollars = structure.net_credit - model_fair_value
    else:
        edge_dollars = None
        blocked.append("missing executable debit/credit")

    edge_pct = None
    if edge_dollars is not None and cost_or_collateral is not None and cost_or_collateral > 0:
        edge_pct = edge_dollars / cost_or_collateral
        if edge_pct < min_edge_pct_of_risk:
            blocked.append(f"edge {edge_pct:.3f} below min {min_edge_pct_of_risk:.3f} of risk")

    be_prob = breakeven_probability(structure)
    if model_probability is not None:
        if model_probability <= 0 or model_probability >= 1:
            blocked.append("model probability must be inside (0, 1)")
        if min_probability_margin is not None and be_prob is not None:
            margin = model_probability - be_prob
            if margin < min_probability_margin:
                blocked.append(f"probability margin {margin:.3f} below min {min_probability_margin:.3f}")

    return OptionEdgeEvaluation(
        structure=structure,
        model_fair_value=_round_money(model_fair_value) or 0.0,
        edge_dollars=_round_money(edge_dollars),
        edge_pct_of_risk=_round_metric(edge_pct),
        model_probability=_round_metric(model_probability),
        breakeven_probability=_round_metric(be_prob),
        passes=not blocked,
        blocked_reasons=tuple(blocked),
    )


def normalize_thesis(raw: dict[str, Any]) -> OptionThesis:
    if not isinstance(raw, dict):
        raise TypeError("option thesis must be a mapping")
    thesis_id = str(raw.get("id") or raw.get("thesisId") or "").strip()
    if not thesis_id:
        raise ValueError("option thesis id is required")
    direction = str(raw.get("direction") or "").strip().lower()
    if direction not in {"up", "down"}:
        raise ValueError("option thesis direction must be 'up' or 'down'")
    target_price = _float_or_none(_first(raw.get("targetPrice"), raw.get("target_price"), raw.get("target")))
    if target_price is None or target_price <= 0:
        raise ValueError("option thesis target price must be positive")
    target_probability = _float_or_none(_first(raw.get("targetProbability"), raw.get("target_probability"), raw.get("probability")))
    if target_probability is None or not (0 < target_probability < 1):
        raise ValueError("option thesis target probability must be inside (0, 1)")
    event_date_raw = _first(raw.get("eventDate"), raw.get("event_date"), raw.get("catalystDate"), raw.get("catalyst_date"))
    event_date = _parse_expiry(event_date_raw) if event_date_raw else None
    option_expiry_raw = _first(
        raw.get("optionExpiry"),
        raw.get("option_expiry"),
        raw.get("targetExpiry"),
        raw.get("target_expiry"),
        raw.get("expiry"),
        event_date_raw,
    )
    option_expiry = _parse_expiry(option_expiry_raw) if option_expiry_raw else None
    allowed_raw = raw.get("allowedStructures") or raw.get("allowed_structures") or ("debit_vertical", "long_call", "long_put")
    if isinstance(allowed_raw, str):
        allowed_values = (allowed_raw,)
    else:
        allowed_values = tuple(allowed_raw)
    allowed: list[OptionStructureType] = []
    for value in allowed_values:
        text = str(value).strip().lower()
        if text not in {"long_call", "long_put", "debit_vertical", "credit_vertical"}:
            raise ValueError(f"unsupported allowed structure: {text!r}")
        allowed.append(text)  # type: ignore[arg-type]
    return OptionThesis(
        id=thesis_id,
        direction=direction,  # type: ignore[arg-type]
        target_price=target_price,
        target_probability=target_probability,
        event_date=event_date,
        option_expiry=option_expiry,
        max_loss_cap=float(_first(raw.get("maxLossCap"), raw.get("max_loss_cap"), 100.0)),
        min_reward_risk=float(_first(raw.get("minRewardRisk"), raw.get("min_reward_risk"), 2.0)),
        min_edge_pct_of_risk=float(_first(raw.get("minEdgePctOfRisk"), raw.get("min_edge_pct_of_risk"), 0.20)),
        min_probability_margin=(
            float(_first(raw.get("minProbabilityMargin"), raw.get("min_probability_margin")))
            if _first(raw.get("minProbabilityMargin"), raw.get("min_probability_margin")) is not None
            else 0.05
        ),
        allowed_structures=tuple(allowed),
        thesis=str(raw.get("thesis") or raw.get("mechanism") or thesis_id),
        catalyst=str(raw.get("catalyst")) if raw.get("catalyst") is not None else None,
        planned_exit=str(_first(raw.get("plannedExit"), raw.get("planned_exit"))) if _first(raw.get("plannedExit"), raw.get("planned_exit")) is not None else None,
        falsifier=str(raw.get("falsifier")) if raw.get("falsifier") is not None else None,
        raw=dict(raw),
    )


def payoff_at_price(structure: OptionStructure, underlying_price: float) -> float:
    total = 0.0
    for leg in structure.legs:
        contract = leg.contract
        if contract.right == "call":
            intrinsic = max(0.0, underlying_price - contract.strike)
        else:
            intrinsic = max(0.0, contract.strike - underlying_price)
        total += leg.quantity * intrinsic * contract.multiplier
    return max(0.0, total)


def model_fair_value_from_thesis(structure: OptionStructure, thesis: OptionThesis) -> tuple[float, float | None, float | None]:
    payoff_if_hit = payoff_at_price(structure, thesis.target_price)
    model_fair_value = thesis.target_probability * payoff_if_hit
    reward_risk = None
    if structure.max_loss is not None and structure.max_loss > 0:
        reward_risk = (payoff_if_hit - structure.max_loss) / structure.max_loss
    return model_fair_value, payoff_if_hit, reward_risk


def _candidate_contracts_for_thesis(
    contracts: Iterable[OptionContract],
    thesis: OptionThesis,
    *,
    now: datetime,
    config: OptionQuoteFilterConfig,
) -> tuple[OptionContract, ...]:
    right: OptionRight = "call" if thesis.direction == "up" else "put"
    candidates: list[OptionContract] = []
    for contract in contracts:
        if contract.right != right:
            continue
        if thesis.option_expiry is not None and contract.expiry != thesis.option_expiry:
            continue
        ok, _ = contract_quote_filter_reason(contract, now=now, config=config)
        if ok:
            candidates.append(contract)
    return tuple(sorted(candidates, key=lambda c: (c.expiry, c.strike)))


def generate_structures_for_thesis(
    contracts: Iterable[OptionContract],
    thesis: OptionThesis,
    *,
    now: datetime,
    config: OptionQuoteFilterConfig | None = None,
) -> tuple[OptionStructure, ...]:
    config = config or OptionQuoteFilterConfig()
    candidates = _candidate_contracts_for_thesis(contracts, thesis, now=now, config=config)
    structures: list[OptionStructure] = []
    allow = set(thesis.allowed_structures)
    long_type = "long_call" if thesis.direction == "up" else "long_put"
    if long_type in allow:
        for contract in candidates:
            try:
                structures.append(build_long_option(contract))
            except ValueError:
                pass
    if "debit_vertical" in allow:
        for long_contract in candidates:
            for short_contract in candidates:
                if long_contract is short_contract:
                    continue
                if thesis.direction == "up":
                    if not (long_contract.strike < short_contract.strike <= thesis.target_price):
                        continue
                else:
                    if not (long_contract.strike > short_contract.strike >= thesis.target_price):
                        continue
                try:
                    structures.append(build_debit_vertical(long_contract, short_contract))
                except ValueError:
                    continue
    return tuple(structures)


def find_opportunities_for_thesis(
    contracts: Iterable[OptionContract],
    thesis: OptionThesis,
    *,
    now: datetime,
    config: OptionQuoteFilterConfig | None = None,
) -> tuple[OptionOpportunity, ...]:
    opportunities: list[OptionOpportunity] = []
    for structure in generate_structures_for_thesis(contracts, thesis, now=now, config=config):
        model_fair, payoff_if_hit, reward_risk = model_fair_value_from_thesis(structure, thesis)
        evaluation = evaluate_structure_edge(
            structure,
            model_fair_value=model_fair,
            min_edge_pct_of_risk=thesis.min_edge_pct_of_risk,
            model_probability=thesis.target_probability,
            min_probability_margin=thesis.min_probability_margin,
            max_loss_cap=thesis.max_loss_cap,
        )
        if reward_risk is None or reward_risk < thesis.min_reward_risk:
            blocked = tuple(evaluation.blocked_reasons) + (f"reward/risk {reward_risk if reward_risk is not None else 'unknown'} below min {thesis.min_reward_risk:.3f}",)
            evaluation = OptionEdgeEvaluation(
                structure=evaluation.structure,
                model_fair_value=evaluation.model_fair_value,
                edge_dollars=evaluation.edge_dollars,
                edge_pct_of_risk=evaluation.edge_pct_of_risk,
                model_probability=evaluation.model_probability,
                breakeven_probability=evaluation.breakeven_probability,
                passes=False,
                blocked_reasons=blocked,
            )
        if not evaluation.passes:
            continue
        spread_penalty = (structure.executable_spread or 0.0) / structure.max_loss if structure.max_loss else 0.0
        score = (evaluation.edge_pct_of_risk or 0.0) + 0.05 * (reward_risk or 0.0) - 0.25 * spread_penalty
        opportunities.append(
            OptionOpportunity(
                thesis=thesis,
                structure=structure,
                evaluation=evaluation,
                model_payoff_if_hit=_round_money(payoff_if_hit),
                reward_risk=_round_metric(reward_risk),
                score=_round_metric(score) or 0.0,
            )
        )
    return tuple(
        sorted(
            opportunities,
            key=lambda opp: (
                opp.score,
                opp.evaluation.edge_pct_of_risk or -999,
                -(opp.structure.executable_spread or 999),
            ),
            reverse=True,
        )
    )


def _safe_ticket_part(value: str, *, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower()).strip("-._")
    return (cleaned or "option")[:max_len]


def option_ticket_id(signal_id: str, now: datetime) -> str:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # Use a long enough signal_id slice that strike/leg differentiators are not truncated
    # for thesis-driven structure search ids (typically <= 90 chars before stamp).
    return f"rime-options-ticket-{_safe_ticket_part(signal_id, max_len=120)}-{stamp}"


def build_option_ticket_artifact(
    *,
    signal_id: str,
    source_mode: str,
    structure: dict[str, Any],
    evaluation: dict[str, Any],
    thesis: dict[str, Any] | str | None,
    now: datetime,
    status: OptionTicketStatus = "draft",
    catalyst: str | None = None,
    planned_exit: str | None = None,
    falsifier: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    created_at = isoformat_z(now)
    if isinstance(thesis, str):
        thesis_payload: dict[str, Any] = {"thesis": thesis}
    elif isinstance(thesis, dict):
        thesis_payload = dict(thesis)
    else:
        thesis_payload = {}
    return {
        "ticket_id": option_ticket_id(signal_id, now),
        "created_at": created_at,
        "status": status,
        "instrument_type": "listed_option_structure",
        "signal_id": signal_id,
        "source_mode": source_mode,
        "underlying": structure.get("underlying"),
        "structure": structure,
        "evaluation": evaluation,
        "thesis": thesis_payload,
        "catalyst": catalyst,
        "planned_exit": planned_exit,
        "falsifier": falsifier,
        "entry": {
            "net_debit": structure.get("net_debit"),
            "net_credit": structure.get("net_credit"),
            "max_loss": structure.get("max_loss"),
            "max_gain": structure.get("max_gain"),
            "breakeven": structure.get("breakeven"),
            "edge_dollars": evaluation.get("edge_dollars"),
            "edge_pct_of_risk": evaluation.get("edge_pct_of_risk"),
            "model_probability": evaluation.get("model_probability"),
            "breakeven_probability": evaluation.get("breakeven_probability"),
        },
        "markouts": {},
        "notes": notes,
        "live_submit_allowed": False,
    }


def option_ticket_from_event(event: dict[str, Any], *, now: datetime | None = None, status: OptionTicketStatus = "draft") -> dict[str, Any]:
    now = now or utcnow_like()
    payload = event.get("payload", {}) if isinstance(event, dict) else {}
    if not isinstance(payload, dict):
        raise ValueError("options event payload must be a mapping")
    signal_id = str(payload.get("signalId") or event.get("id") or "option-signal")
    thesis_payload = payload.get("thesis")
    return build_option_ticket_artifact(
        signal_id=signal_id,
        source_mode=str(payload.get("sourceMode") or "event"),
        structure=dict(payload.get("structure") or {}),
        evaluation=dict(payload.get("evaluation") or {}),
        thesis=thesis_payload if isinstance(thesis_payload, (dict, str)) else None,
        now=now,
        status=status,
        catalyst=payload.get("catalyst"),
        planned_exit=payload.get("plannedExit"),
        falsifier=payload.get("falsifier"),
        notes=str(event.get("prompt") or ""),
    )


def utcnow_like() -> datetime:
    return datetime.now(timezone.utc)


def write_option_ticket(ticket: dict[str, Any], ticket_dir: str | Path) -> Path:
    directory = Path(ticket_dir)
    directory.mkdir(parents=True, exist_ok=True)
    ticket_id = _safe_ticket_part(str(ticket.get("ticket_id") or "option-ticket"), max_len=120)
    path = directory / f"{ticket_id}.json"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(ticket, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path


def mark_structure_value_from_chain(structure: dict[str, Any], snapshot: OptionChainSnapshot) -> float:
    contracts = {contract.symbol: contract for contract in snapshot.contracts}
    legs = structure.get("legs") if isinstance(structure.get("legs"), list) else []
    total = 0.0
    for leg in legs:
        if not isinstance(leg, dict):
            continue
        quantity = int(leg.get("quantity", 0))
        contract_payload = leg.get("contract", {}) if isinstance(leg.get("contract"), dict) else {}
        symbol = str(contract_payload.get("symbol") or "")
        if symbol not in contracts:
            raise KeyError(f"missing mark quote for {symbol}")
        mark_contract = contracts[symbol]
        mid = mark_contract.mid
        if mid is None:
            raise ValueError(f"missing mark mid for {symbol}")
        total += quantity * mid * mark_contract.multiplier
    if structure.get("net_credit") is not None:
        return _round_money(max(0.0, -total)) or 0.0
    return _round_money(max(0.0, total)) or 0.0


def option_markout(
    ticket: dict[str, Any],
    *,
    checkpoint: str,
    mark_value: float,
    underlying_price: float | None,
    now: datetime,
    iv: float | None = None,
    delta: float | None = None,
    gamma: float | None = None,
    theta: float | None = None,
    vega: float | None = None,
    notes: str = "",
) -> dict[str, Any]:
    entry = ticket.get("entry", {}) if isinstance(ticket.get("entry"), dict) else {}
    net_debit = _float_or_none(entry.get("net_debit"))
    net_credit = _float_or_none(entry.get("net_credit"))
    max_loss = _float_or_none(entry.get("max_loss"))
    if net_debit is not None:
        pnl = mark_value - net_debit
    elif net_credit is not None:
        # For credit structures, mark_value is interpreted as current cost to close.
        pnl = net_credit - mark_value
    else:
        pnl = None
    return_on_risk = pnl / max_loss if pnl is not None and max_loss and max_loss > 0 else None
    return {
        "checkpoint": checkpoint,
        "ts": isoformat_z(now),
        "mark_value": _round_money(mark_value),
        "underlying_price": _round_money(underlying_price),
        "pnl": _round_money(pnl),
        "return_on_risk": _round_metric(return_on_risk),
        "iv": _round_metric(iv),
        "delta": _round_metric(delta),
        "gamma": _round_metric(gamma),
        "theta": _round_metric(theta),
        "vega": _round_metric(vega),
        "notes": notes,
    }


def add_option_markout(ticket: dict[str, Any], markout: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(ticket))
    checkpoint = str(markout.get("checkpoint") or "mark")
    updated.setdefault("markouts", {})[checkpoint] = markout
    if checkpoint in {"exit", "expiry", "close"}:
        updated["status"] = "paper_closed"
    elif updated.get("status") == "draft":
        updated["status"] = "paper_open"
    return updated


def _fmt_money(value: Any) -> str:
    parsed = _float_or_none(value)
    return "" if parsed is None else f"${parsed:.2f}"


def _fmt_pct(value: Any) -> str:
    parsed = _float_or_none(value)
    return "" if parsed is None else f"{parsed * 100:.1f}%"


def _pipe_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def option_structure_label(structure: dict[str, Any]) -> str:
    structure_type = str(structure.get("structure_type") or "option_structure")
    legs = structure.get("legs") if isinstance(structure.get("legs"), list) else []
    leg_labels = []
    for leg in legs:
        contract = leg.get("contract", {}) if isinstance(leg, dict) else {}
        qty = leg.get("quantity") if isinstance(leg, dict) else None
        leg_labels.append(f"{qty:+d} {contract.get('right')} {contract.get('strike')}" if isinstance(qty, int) else str(contract.get("symbol") or "leg"))
    return f"{structure_type} {' / '.join(leg_labels)}".strip()


def options_ledger_row(ticket: dict[str, Any]) -> str:
    entry = ticket.get("entry", {}) if isinstance(ticket.get("entry"), dict) else {}
    markouts = ticket.get("markouts", {}) if isinstance(ticket.get("markouts"), dict) else {}
    thesis = ticket.get("thesis", {}) if isinstance(ticket.get("thesis"), dict) else {}
    thesis_text = thesis.get("thesis") or ticket.get("notes") or ticket.get("signal_id")
    entry_text = "; ".join(
        part
        for part in (
            f"debit {_fmt_money(entry.get('net_debit'))}" if entry.get("net_debit") is not None else None,
            f"credit {_fmt_money(entry.get('net_credit'))}" if entry.get("net_credit") is not None else None,
            f"max loss {_fmt_money(entry.get('max_loss'))}" if entry.get("max_loss") is not None else None,
            f"max gain {_fmt_money(entry.get('max_gain'))}" if entry.get("max_gain") is not None else None,
            f"edge {_fmt_money(entry.get('edge_dollars'))} / {_fmt_pct(entry.get('edge_pct_of_risk'))}" if entry.get("edge_dollars") is not None else None,
        )
        if part
    )
    def mark_text(key: str) -> str:
        mark = markouts.get(key)
        if not isinstance(mark, dict):
            return ""
        return f"{_fmt_money(mark.get('mark_value'))} ({_fmt_money(mark.get('pnl'))})"
    latest_exit = markouts.get("exit") or markouts.get("expiry") or markouts.get("close")
    exit_text = "" if not isinstance(latest_exit, dict) else f"{_fmt_money(latest_exit.get('mark_value'))} ({_fmt_money(latest_exit.get('pnl'))})"
    pnl_text = "" if not isinstance(latest_exit, dict) else _fmt_money(latest_exit.get("pnl"))
    cols = [
        str(ticket.get("created_at") or "")[:10],
        ticket.get("underlying") or "",
        option_structure_label(ticket.get("structure", {}) if isinstance(ticket.get("structure"), dict) else {}),
        thesis_text,
        entry_text,
        mark_text("1h"),
        mark_text("6h"),
        mark_text("24h"),
        exit_text,
        pnl_text,
        ticket.get("status") or "",
    ]
    return "| " + " | ".join(_pipe_escape(col) for col in cols) + " |"
