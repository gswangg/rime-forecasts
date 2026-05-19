from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
import json
import math
from typing import Any, Iterable, Literal

from .timeutil import isoformat_z, parse_iso

OptionRight = Literal["call", "put"]
OptionStructureType = Literal["long_call", "long_put", "debit_vertical", "credit_vertical"]


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
            "underlying_bid": self.underlying_bid,
            "underlying_ask": self.underlying_ask,
            "contracts": [contract.to_dict() for contract in self.contracts],
            "raw": self.raw,
        }


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
    return parse_option_chain_snapshot(json.loads(Path(path).read_text(encoding="utf-8")))


def days_to_expiry(expiry: date, *, now: datetime) -> int:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (expiry - now.astimezone(timezone.utc).date()).days


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
