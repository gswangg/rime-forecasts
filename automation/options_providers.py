from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import os
import urllib.parse
import urllib.request
from typing import Any, Callable, Mapping

from .options import OptionChainSnapshot, OptionContract, parse_option_chain_snapshot, normalize_contract

JsonFetcher = Callable[[str, Mapping[str, str]], Any]


class OptionProviderError(RuntimeError):
    pass


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _timestamp_from_tradier(value: Any, *, fallback: datetime) -> datetime:
    if value in (None, ""):
        return fallback
    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric > 10_000_000_000:  # milliseconds
            numeric /= 1000
        return datetime.fromtimestamp(numeric, tz=timezone.utc)
    text = str(value).strip()
    if text.isdigit():
        return _timestamp_from_tradier(float(text), fallback=fallback)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return fallback
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class TradierOptionProvider:
    """Tradier market-data provider adapter.

    Requires a market-data token supplied out-of-repo via TRADIER_TOKEN or
    TRADIER_API_KEY unless a test fetcher is injected. This class does not place
    orders and does not use account endpoints.
    """

    token: str
    base_url: str = "https://api.tradier.com/v1"
    fetch_json: JsonFetcher | None = None
    provider: str = "tradier"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "TradierOptionProvider":
        env = env or os.environ
        token = env.get("TRADIER_TOKEN") or env.get("TRADIER_API_KEY")
        if not token:
            raise OptionProviderError("TRADIER_TOKEN or TRADIER_API_KEY is required for Tradier option-chain access")
        return cls(token=token, base_url=env.get("TRADIER_BASE_URL", "https://api.tradier.com/v1"))

    def _get(self, path: str, params: Mapping[str, str]) -> Any:
        if self.fetch_json is not None:
            return self.fetch_json(path, params)
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "User-Agent": "rime-forecasts/options-provider-tradier/0.1",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def list_expiries(self, underlying: str) -> tuple[date, ...]:
        data = self._get("markets/options/expirations", {"symbol": underlying.upper(), "includeAllRoots": "true"})
        raw_dates = data.get("expirations", {}).get("date") if isinstance(data, dict) else None
        expiries = []
        for item in _as_list(raw_dates):
            try:
                expiries.append(date.fromisoformat(str(item)))
            except ValueError:
                continue
        return tuple(sorted(expiries))

    def _underlying_book(self, underlying: str) -> tuple[float | None, float | None, dict[str, Any] | None]:
        data = self._get("markets/quotes", {"symbols": underlying.upper()})
        quote = data.get("quotes", {}).get("quote") if isinstance(data, dict) else None
        if isinstance(quote, list):
            quote = quote[0] if quote else None
        if not isinstance(quote, dict):
            return None, None, None
        bid = _float_or_none(quote.get("bid"))
        ask = _float_or_none(quote.get("ask"))
        return bid, ask, quote

    def fetch_chain(self, underlying: str, expiry: date | None = None) -> OptionChainSnapshot:
        underlying = underlying.upper()
        if expiry is None:
            expiries = self.list_expiries(underlying)
            if not expiries:
                raise OptionProviderError(f"Tradier returned no expiries for {underlying}")
            expiry = expiries[0]
        now = datetime.now(timezone.utc)
        underlying_bid, underlying_ask, underlying_raw = self._underlying_book(underlying)
        data = self._get(
            "markets/options/chains",
            {"symbol": underlying, "expiration": expiry.isoformat(), "greeks": "true"},
        )
        options = data.get("options", {}).get("option") if isinstance(data, dict) else None
        contracts: list[dict[str, Any]] = []
        for row in _as_list(options):
            if not isinstance(row, dict):
                continue
            greeks = row.get("greeks") if isinstance(row.get("greeks"), dict) else {}
            quote_ts = _timestamp_from_tradier(row.get("bid_date") or row.get("ask_date") or row.get("trade_date"), fallback=now)
            contracts.append(
                {
                    "underlying": row.get("root_symbol") or row.get("underlying") or underlying,
                    "provider": self.provider,
                    "symbol": row.get("symbol"),
                    "expiry": row.get("expiration_date") or expiry.isoformat(),
                    "right": row.get("option_type"),
                    "strike": row.get("strike"),
                    "style": row.get("style") or "american",
                    "settlement": row.get("settlement") or "physical",
                    "multiplier": row.get("multiplier") or 100,
                    "underlying_bid": underlying_bid,
                    "underlying_ask": underlying_ask,
                    "bid": row.get("bid"),
                    "ask": row.get("ask"),
                    "last": row.get("last"),
                    "iv": greeks.get("mid_iv") or greeks.get("smv_vol") or greeks.get("iv"),
                    "delta": greeks.get("delta"),
                    "gamma": greeks.get("gamma"),
                    "theta": greeks.get("theta"),
                    "vega": greeks.get("vega"),
                    "volume": row.get("volume"),
                    "open_interest": row.get("open_interest"),
                    "quote_ts": quote_ts.isoformat(),
                    "raw": row,
                }
            )
        return parse_option_chain_snapshot(
            {
                "underlying": underlying,
                "provider": self.provider,
                "quote_ts": now.isoformat(),
                "underlying_bid": underlying_bid,
                "underlying_ask": underlying_ask,
                "contracts": contracts,
                "raw": {"provider": self.provider, "underlying_quote": underlying_raw, "chain": data},
            }
        )

    def fetch_quote(self, symbol: str) -> OptionContract:
        data = self._get("markets/quotes", {"symbols": symbol, "greeks": "true"})
        quote = data.get("quotes", {}).get("quote") if isinstance(data, dict) else None
        if isinstance(quote, list):
            quote = quote[0] if quote else None
        if not isinstance(quote, dict):
            raise OptionProviderError(f"Tradier returned no quote for {symbol}")
        greeks = quote.get("greeks") if isinstance(quote.get("greeks"), dict) else {}
        now = datetime.now(timezone.utc)
        raw = {
            "underlying": quote.get("root_symbol") or quote.get("underlying") or quote.get("underlying_symbol") or "UNKNOWN",
            "provider": self.provider,
            "symbol": quote.get("symbol") or symbol,
            "expiry": quote.get("expiration_date"),
            "right": quote.get("option_type"),
            "strike": quote.get("strike"),
            "style": quote.get("style") or "american",
            "settlement": quote.get("settlement") or "physical",
            "multiplier": quote.get("multiplier") or 100,
            "bid": quote.get("bid"),
            "ask": quote.get("ask"),
            "last": quote.get("last"),
            "iv": greeks.get("mid_iv") or greeks.get("smv_vol") or greeks.get("iv"),
            "delta": greeks.get("delta"),
            "gamma": greeks.get("gamma"),
            "theta": greeks.get("theta"),
            "vega": greeks.get("vega"),
            "volume": quote.get("volume"),
            "open_interest": quote.get("open_interest"),
            "quote_ts": _timestamp_from_tradier(quote.get("bid_date") or quote.get("ask_date") or quote.get("trade_date"), fallback=now).isoformat(),
        }
        return normalize_contract(raw)
