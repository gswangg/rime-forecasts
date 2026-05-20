import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from automation.options import (
    FixtureOptionProvider,
    OptionQuoteFilterConfig,
    black_scholes_price,
    breakeven_probability,
    build_credit_vertical,
    build_debit_vertical,
    build_long_option,
    contract_quote_filter_reason,
    evaluate_structure_edge,
    filter_contracts,
    find_opportunities_for_thesis,
    generate_structures_for_thesis,
    load_option_chain_snapshot,
    mark_structure_value_from_chain,
    model_fair_value_from_thesis,
    normalize_contract,
    normalize_thesis,
    option_markout,
    option_ticket_from_event,
    options_ledger_row,
    parse_option_chain_snapshot,
    payoff_at_price,
    quote_delay_seconds,
    risk_neutral_probability_above,
    risk_neutral_probability_between,
    single_leg_spread_limit,
    time_to_expiry_years,
    add_option_markout,
    write_option_ticket,
)
from automation.options_providers import TradierOptionProvider


_OPTIONS_DAEMON_PATH = Path(__file__).resolve().parents[1] / "scripts" / "options-daemon.py"
_OPTIONS_DAEMON_SPEC = importlib.util.spec_from_file_location("options_daemon", _OPTIONS_DAEMON_PATH)
assert _OPTIONS_DAEMON_SPEC and _OPTIONS_DAEMON_SPEC.loader
options_daemon = importlib.util.module_from_spec(_OPTIONS_DAEMON_SPEC)
_OPTIONS_DAEMON_SPEC.loader.exec_module(options_daemon)

_OPTIONS_MARKOUT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "options-markout.py"
_OPTIONS_MARKOUT_SPEC = importlib.util.spec_from_file_location("options_markout", _OPTIONS_MARKOUT_PATH)
assert _OPTIONS_MARKOUT_SPEC and _OPTIONS_MARKOUT_SPEC.loader
options_markout = importlib.util.module_from_spec(_OPTIONS_MARKOUT_SPEC)
_OPTIONS_MARKOUT_SPEC.loader.exec_module(options_markout)

_OPTIONS_CHAIN_FETCH_PATH = Path(__file__).resolve().parents[1] / "scripts" / "options-chain-fetch.py"
_OPTIONS_CHAIN_FETCH_SPEC = importlib.util.spec_from_file_location("options_chain_fetch", _OPTIONS_CHAIN_FETCH_PATH)
assert _OPTIONS_CHAIN_FETCH_SPEC and _OPTIONS_CHAIN_FETCH_SPEC.loader
options_chain_fetch = importlib.util.module_from_spec(_OPTIONS_CHAIN_FETCH_SPEC)
_OPTIONS_CHAIN_FETCH_SPEC.loader.exec_module(options_chain_fetch)


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def raw_contract(**overrides):
    data = {
        "underlying": "NVDA",
        "provider": "fixture",
        "symbol": "NVDA260522C00250000",
        "expiry": "2026-05-22",
        "right": "call",
        "strike": 250.0,
        "style": "american",
        "settlement": "physical",
        "multiplier": 100,
        "underlying_bid": 224.40,
        "underlying_ask": 224.45,
        "bid": 1.20,
        "ask": 1.28,
        "last": 1.25,
        "iv": 0.62,
        "delta": 0.31,
        "gamma": 0.02,
        "theta": -0.11,
        "vega": 0.08,
        "volume": 1200,
        "open_interest": 5400,
        "quote_ts": "2026-05-19T03:20:00Z",
    }
    data.update(overrides)
    return data


class OptionsCoreTests(unittest.TestCase):
    def test_normalize_contract_parses_schema_and_mid(self):
        contract = normalize_contract(raw_contract())
        self.assertEqual(contract.underlying, "NVDA")
        self.assertEqual(contract.provider, "fixture")
        self.assertEqual(contract.symbol, "NVDA260522C00250000")
        self.assertEqual(contract.expiry.isoformat(), "2026-05-22")
        self.assertEqual(contract.right, "call")
        self.assertAlmostEqual(contract.strike, 250.0)
        self.assertEqual(contract.multiplier, 100)
        self.assertAlmostEqual(contract.mid, 1.24)
        self.assertAlmostEqual(contract.spread, 0.08)
        self.assertEqual(contract.quote_ts, dt("2026-05-19T03:20:00Z"))
        serialized = contract.to_dict()
        self.assertEqual(serialized["expiry"], "2026-05-22")
        self.assertEqual(serialized["quote_ts"], "2026-05-19T03:20:00Z")

    def test_normalize_contract_accepts_aliases(self):
        contract = normalize_contract(
            raw_contract(
                right="P",
                expiry=None,
                expiration_date="2026-05-29",
                bid=None,
                bestBid="2.10",
                ask=None,
                bestAsk="2.25",
                open_interest=None,
                openInterest="800",
                quote_ts=None,
                quoteTime="2026-05-19T03:21:00Z",
            )
        )
        self.assertEqual(contract.right, "put")
        self.assertEqual(contract.expiry.isoformat(), "2026-05-29")
        self.assertAlmostEqual(contract.bid, 2.10)
        self.assertAlmostEqual(contract.ask, 2.25)
        self.assertAlmostEqual(contract.open_interest, 800)
        self.assertEqual(contract.quote_ts, dt("2026-05-19T03:21:00Z"))

    def test_parse_option_chain_snapshot_applies_defaults(self):
        snapshot = parse_option_chain_snapshot(
            {
                "underlying": "spy",
                "provider": "fixture",
                "underlying_bid": 520.10,
                "underlying_ask": 520.14,
                "quote_ts": "2026-05-19T14:30:00Z",
                "contracts": [
                    {
                        "symbol": "SPY260522C00525000",
                        "expiry": "2026-05-22",
                        "right": "C",
                        "strike": 525,
                        "bid": 1.00,
                        "ask": 1.04,
                        "volume": 500,
                        "open_interest": 1000,
                    },
                    {
                        "symbol": "SPY260522P00515000",
                        "expiry": "2026-05-22",
                        "right": "put",
                        "strike": 515,
                        "bid": 1.10,
                        "ask": 1.16,
                        "volume": 700,
                        "open_interest": 1200,
                    },
                ],
            }
        )
        self.assertEqual(snapshot.underlying, "SPY")
        self.assertEqual(snapshot.provider, "fixture")
        self.assertAlmostEqual(snapshot.underlying_mid, 520.12)
        self.assertEqual(len(snapshot.contracts), 2)
        self.assertEqual(snapshot.contracts[0].underlying, "SPY")
        self.assertEqual(snapshot.contracts[0].quote_ts, dt("2026-05-19T14:30:00Z"))

    def test_load_option_chain_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chain.json"
            path.write_text(
                '{"underlying":"NVDA","provider":"fixture","contracts":[{"symbol":"NVDA260522C00250000","expiry":"2026-05-22","right":"call","strike":250,"bid":1.20,"ask":1.28,"volume":1200,"open_interest":5400}]}',
                encoding="utf-8",
            )
            snapshot = load_option_chain_snapshot(path)
        self.assertEqual(snapshot.underlying, "NVDA")
        self.assertEqual(len(snapshot.contracts), 1)

    def test_tradier_option_provider_normalizes_expiries_chain_and_quote(self):
        def fake_fetch(path, params):
            if path == "markets/options/expirations":
                return {"expirations": {"date": ["2026-05-22", "2026-05-29"]}}
            if path == "markets/quotes" and params.get("symbols") == "NVDA":
                return {"quotes": {"quote": {"symbol": "NVDA", "bid": 224.40, "ask": 224.45}}}
            if path == "markets/options/chains":
                return {
                    "options": {
                        "option": [
                            {
                                "symbol": "NVDA260522C00250000",
                                "root_symbol": "NVDA",
                                "expiration_date": "2026-05-22",
                                "option_type": "call",
                                "strike": 250,
                                "bid": 1.20,
                                "ask": 1.28,
                                "last": 1.25,
                                "volume": 1200,
                                "open_interest": 5400,
                                "bid_date": 1779160800000,
                                "greeks": {"delta": 0.31, "gamma": 0.02, "theta": -0.11, "vega": 0.08, "mid_iv": 0.62},
                            }
                        ]
                    }
                }
            if path == "markets/quotes" and params.get("symbols") == "NVDA260522C00250000":
                return {
                    "quotes": {
                        "quote": {
                            "symbol": "NVDA260522C00250000",
                            "root_symbol": "NVDA",
                            "expiration_date": "2026-05-22",
                            "option_type": "call",
                            "strike": 250,
                            "bid": 1.20,
                            "ask": 1.28,
                            "volume": 1200,
                            "open_interest": 5400,
                            "greeks": {"delta": 0.31},
                        }
                    }
                }
            raise AssertionError((path, params))

        provider = TradierOptionProvider(token="test-token", fetch_json=fake_fetch)
        self.assertEqual([d.isoformat() for d in provider.list_expiries("nvda")], ["2026-05-22", "2026-05-29"])
        chain = provider.fetch_chain("NVDA", datetime.fromisoformat("2026-05-22").date())
        self.assertEqual(chain.provider, "tradier")
        self.assertEqual(len(chain.contracts), 1)
        self.assertEqual(chain.contracts[0].symbol, "NVDA260522C00250000")
        self.assertAlmostEqual(chain.contracts[0].underlying_bid, 224.40)
        self.assertAlmostEqual(chain.contracts[0].delta, 0.31)
        quote = provider.fetch_quote("NVDA260522C00250000")
        self.assertEqual(quote.underlying, "NVDA")
        self.assertEqual(quote.right, "call")

    def test_tradier_from_env_accepts_api_key_alias(self):
        provider = TradierOptionProvider.from_env({"TRADIER_API_KEY": "alias-token", "TRADIER_BASE_URL": "https://example.test/v1"})
        self.assertEqual(provider.token, "alias-token")
        self.assertEqual(provider.base_url, "https://example.test/v1")

    def test_fixture_option_provider_interface(self):
        provider = FixtureOptionProvider.from_mapping(
            {
                "chain": {
                    "underlying": "NVDA",
                    "provider": "fixture",
                    "underlying_bid": 224.40,
                    "underlying_ask": 224.45,
                    "quote_ts": "2026-05-19T03:20:00Z",
                    "contracts": [
                        raw_contract(symbol="NVDA260522C00250000", strike=250),
                        raw_contract(symbol="NVDA260529C00260000", expiry="2026-05-29", strike=260),
                    ],
                }
            }
        )
        self.assertEqual(provider.provider, "fixture")
        self.assertEqual([d.isoformat() for d in provider.list_expiries("nvda")], ["2026-05-22", "2026-05-29"])
        chain = provider.fetch_chain("NVDA", datetime.fromisoformat("2026-05-22").date())
        self.assertEqual(len(chain.contracts), 1)
        self.assertEqual(chain.contracts[0].symbol, "NVDA260522C00250000")
        quote = provider.fetch_quote("NVDA260529C00260000")
        self.assertEqual(quote.expiry.isoformat(), "2026-05-29")
        self.assertEqual(quote_delay_seconds(quote.quote_ts, now=dt("2026-05-19T03:25:00Z")), 300)
        with self.assertRaises(KeyError):
            provider.fetch_quote("NOPE")

    def test_quote_filter_accepts_liquid_contract(self):
        now = dt("2026-05-19T03:25:00Z")
        contract = normalize_contract(raw_contract())
        ok, reason = contract_quote_filter_reason(contract, now=now)
        self.assertTrue(ok, reason)

    def test_quote_filter_rejects_allowlist_miss(self):
        now = dt("2026-05-19T03:25:00Z")
        contract = normalize_contract(raw_contract(underlying="TSLA"))
        ok, reason = contract_quote_filter_reason(
            contract,
            now=now,
            config=OptionQuoteFilterConfig(allow_underlyings=("NVDA",)),
        )
        self.assertFalse(ok)
        self.assertIn("allowlist", reason)

    def test_quote_filter_rejects_bad_expiry(self):
        now = dt("2026-05-19T03:25:00Z")
        same_day = normalize_contract(raw_contract(expiry="2026-05-19"))
        ok, reason = contract_quote_filter_reason(same_day, now=now)
        self.assertFalse(ok)
        self.assertIn("outside", reason)

        too_far = normalize_contract(raw_contract(expiry="2026-08-01"))
        ok, reason = contract_quote_filter_reason(too_far, now=now)
        self.assertFalse(ok)
        self.assertIn("outside", reason)

    def test_quote_filter_rejects_invalid_bid_ask_and_wide_spread(self):
        now = dt("2026-05-19T03:25:00Z")
        missing = normalize_contract(raw_contract(bid=None))
        ok, reason = contract_quote_filter_reason(missing, now=now)
        self.assertFalse(ok)
        self.assertIn("missing bid/ask", reason)

        crossed = normalize_contract(raw_contract(bid=1.40, ask=1.20))
        ok, reason = contract_quote_filter_reason(crossed, now=now)
        self.assertFalse(ok)
        self.assertIn("invalid bid/ask", reason)

        wide = normalize_contract(raw_contract(bid=1.00, ask=1.40))
        ok, reason = contract_quote_filter_reason(wide, now=now)
        self.assertFalse(ok)
        self.assertIn("spread", reason)

    def test_quote_filter_rejects_low_premium_and_low_liquidity(self):
        now = dt("2026-05-19T03:25:00Z")
        low_premium = normalize_contract(raw_contract(bid=0.01, ask=0.04))
        ok, reason = contract_quote_filter_reason(low_premium, now=now)
        self.assertFalse(ok)
        self.assertIn("premium", reason)

        illiquid = normalize_contract(raw_contract(volume=50, open_interest=100))
        ok, reason = contract_quote_filter_reason(illiquid, now=now)
        self.assertFalse(ok)
        self.assertIn("liquidity", reason)

    def test_quote_filter_rejects_corporate_action_and_stale_quote(self):
        now = dt("2026-05-19T03:25:00Z")
        adjusted = normalize_contract(raw_contract(non_standard=True))
        ok, reason = contract_quote_filter_reason(adjusted, now=now)
        self.assertFalse(ok)
        self.assertIn("corporate-action", reason)

        stale = normalize_contract(raw_contract(quote_ts="2026-05-19T03:00:00Z"))
        ok, reason = contract_quote_filter_reason(
            stale,
            now=now,
            config=OptionQuoteFilterConfig(max_quote_age_seconds=300),
        )
        self.assertFalse(ok)
        self.assertIn("quote age", reason)

    def test_filter_contracts_returns_only_accepted(self):
        now = dt("2026-05-19T03:25:00Z")
        good = normalize_contract(raw_contract(symbol="NVDA260522C00250000"))
        bad = normalize_contract(raw_contract(symbol="NVDA260522C00350000", bid=0.01, ask=0.04))
        accepted = filter_contracts([good, bad], now=now)
        self.assertEqual(accepted, (good,))

    def test_single_leg_spread_limit_uses_abs_or_percent(self):
        self.assertAlmostEqual(single_leg_spread_limit(1.00), 0.15)
        self.assertAlmostEqual(single_leg_spread_limit(0.20), 0.05)

    def test_black_scholes_and_risk_neutral_distribution_helpers(self):
        t = time_to_expiry_years(datetime.fromisoformat("2026-06-19").date(), now=dt("2026-05-19T00:00:00Z"))
        self.assertGreater(t, 0)
        call = black_scholes_price("call", spot=100, strike=100, time_years=1.0, volatility=0.20, risk_free_rate=0.0)
        put = black_scholes_price("put", spot=100, strike=100, time_years=1.0, volatility=0.20, risk_free_rate=0.0)
        self.assertAlmostEqual(call, 7.965567, places=5)
        self.assertAlmostEqual(put, 7.965567, places=5)
        above = risk_neutral_probability_above(spot=100, threshold=100, time_years=1.0, volatility=0.20)
        self.assertAlmostEqual(above, 0.460172, places=5)
        between = risk_neutral_probability_between(spot=100, lower=95, upper=105, time_years=1.0, volatility=0.20)
        self.assertGreater(between, 0.0)
        self.assertLess(between, 1.0)

    def test_build_long_option_structure(self):
        contract = normalize_contract(raw_contract(strike=250, bid=1.20, ask=1.28, delta=0.31, theta=-0.11))
        structure = build_long_option(contract)
        self.assertEqual(structure.structure_type, "long_call")
        self.assertEqual(len(structure.legs), 1)
        self.assertAlmostEqual(structure.net_debit, 128.0)
        self.assertAlmostEqual(structure.max_loss, 128.0)
        self.assertIsNone(structure.max_gain)
        self.assertAlmostEqual(structure.breakeven, 251.28)
        self.assertAlmostEqual(structure.net_delta, 0.31)
        self.assertAlmostEqual(structure.net_theta, -0.11)

    def test_build_call_debit_vertical_structure(self):
        long_call = normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28, delta=0.31, gamma=0.02, theta=-0.11, vega=0.08))
        short_call = normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48, delta=0.18, gamma=0.01, theta=-0.07, vega=0.05))
        structure = build_debit_vertical(long_call, short_call)
        self.assertEqual(structure.structure_type, "debit_vertical")
        self.assertAlmostEqual(structure.net_debit, 86.0)
        self.assertAlmostEqual(structure.max_loss, 86.0)
        self.assertAlmostEqual(structure.max_gain, 914.0)
        self.assertAlmostEqual(structure.breakeven, 250.86)
        self.assertAlmostEqual(structure.width, 10.0)
        self.assertAlmostEqual(structure.executable_spread, 7.0)
        self.assertAlmostEqual(structure.net_delta, 0.13)
        self.assertAlmostEqual(structure.net_gamma, 0.01)
        self.assertAlmostEqual(structure.net_theta, -0.04)
        self.assertAlmostEqual(structure.net_vega, 0.03)
        self.assertAlmostEqual(breakeven_probability(structure), 0.086)

    def test_build_put_debit_vertical_structure(self):
        long_put = normalize_contract(raw_contract(symbol="NVDA260522P00220000", right="put", strike=220, bid=2.30, ask=2.40))
        short_put = normalize_contract(raw_contract(symbol="NVDA260522P00210000", right="put", strike=210, bid=1.10, ask=1.18))
        structure = build_debit_vertical(long_put, short_put)
        self.assertEqual(structure.right, "put")
        self.assertAlmostEqual(structure.net_debit, 130.0)
        self.assertAlmostEqual(structure.max_loss, 130.0)
        self.assertAlmostEqual(structure.max_gain, 870.0)
        self.assertAlmostEqual(structure.breakeven, 218.7)

    def test_build_credit_vertical_structure(self):
        short_call = normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28))
        long_call = normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48))
        structure = build_credit_vertical(short_call, long_call)
        self.assertEqual(structure.structure_type, "credit_vertical")
        self.assertAlmostEqual(structure.net_credit, 72.0)
        self.assertAlmostEqual(structure.max_loss, 928.0)
        self.assertAlmostEqual(structure.max_gain, 72.0)
        self.assertAlmostEqual(structure.breakeven, 250.72)

    def test_structure_builders_reject_bad_vertical_orientation(self):
        lower = normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28))
        higher = normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48))
        with self.assertRaises(ValueError):
            build_debit_vertical(higher, lower)
        with self.assertRaises(ValueError):
            build_credit_vertical(higher, lower)

    def test_evaluate_structure_edge_passes_and_blocks(self):
        long_call = normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28))
        short_call = normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48))
        structure = build_debit_vertical(long_call, short_call)
        evaluation = evaluate_structure_edge(
            structure,
            model_fair_value=125.0,
            min_edge_pct_of_risk=0.20,
            model_probability=0.25,
            min_probability_margin=0.05,
            max_loss_cap=100.0,
        )
        self.assertTrue(evaluation.passes, evaluation.blocked_reasons)
        self.assertAlmostEqual(evaluation.edge_dollars, 39.0)
        self.assertAlmostEqual(evaluation.edge_pct_of_risk, 39.0 / 86.0)
        self.assertAlmostEqual(evaluation.breakeven_probability, 0.086)

        blocked = evaluate_structure_edge(
            structure,
            model_fair_value=90.0,
            min_edge_pct_of_risk=0.20,
            model_probability=0.10,
            min_probability_margin=0.05,
            max_loss_cap=80.0,
        )
        self.assertFalse(blocked.passes)
        self.assertTrue(any("edge" in reason for reason in blocked.blocked_reasons))
        self.assertTrue(any("max loss" in reason for reason in blocked.blocked_reasons))
        self.assertTrue(any("probability margin" in reason for reason in blocked.blocked_reasons))

    def test_normalize_thesis_and_generate_upside_structures(self):
        contracts = [
            normalize_contract(raw_contract(symbol="NVDA260522C00245000", strike=245, bid=2.00, ask=2.10)),
            normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28)),
            normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48)),
            normalize_contract(raw_contract(symbol="NVDA260522P00220000", right="put", strike=220, bid=2.30, ask=2.40)),
        ]
        thesis = normalize_thesis(
            {
                "id": "nvda-guidance-upside",
                "direction": "up",
                "targetPrice": 260,
                "targetProbability": 0.35,
                "eventDate": "2026-05-22",
                "maxLossCap": 150,
                "minRewardRisk": 2.0,
                "minEdgePctOfRisk": 0.20,
                "allowedStructures": ["debit_vertical", "long_call"],
                "thesis": "guidance is underpriced",
            }
        )
        structures = generate_structures_for_thesis(
            contracts,
            thesis,
            now=dt("2026-05-19T03:25:00Z"),
            config=OptionQuoteFilterConfig(),
        )
        self.assertTrue(any(s.structure_type == "long_call" for s in structures))
        self.assertTrue(any(s.structure_type == "debit_vertical" for s in structures))
        self.assertTrue(all(s.right == "call" for s in structures))
        self.assertTrue(all(s.expiry.isoformat() == "2026-05-22" for s in structures))

    def test_normalize_thesis_distinguishes_catalyst_date_and_option_expiry(self):
        contracts = [
            normalize_contract(raw_contract(symbol="NVDA260522C00250000", expiry="2026-05-22", strike=250, bid=1.20, ask=1.28)),
            normalize_contract(raw_contract(symbol="NVDA260522C00260000", expiry="2026-05-22", strike=260, bid=0.42, ask=0.48)),
            normalize_contract(raw_contract(symbol="NVDA260529C00250000", expiry="2026-05-29", strike=250, bid=2.10, ask=2.20)),
            normalize_contract(raw_contract(symbol="NVDA260529C00260000", expiry="2026-05-29", strike=260, bid=0.90, ask=0.98)),
        ]
        thesis = normalize_thesis(
            {
                "id": "nvda-catalyst-upside",
                "direction": "up",
                "targetPrice": 260,
                "targetProbability": 0.35,
                "eventDate": "2026-05-22",
                "optionExpiry": "2026-05-29",
                "maxLossCap": 150,
                "minRewardRisk": 2.0,
                "allowedStructures": ["debit_vertical"],
            }
        )
        self.assertEqual(thesis.event_date.isoformat(), "2026-05-22")
        self.assertEqual(thesis.option_expiry.isoformat(), "2026-05-29")
        structures = generate_structures_for_thesis(contracts, thesis, now=dt("2026-05-19T03:25:00Z"))
        self.assertGreaterEqual(len(structures), 1)
        self.assertTrue(all(structure.expiry.isoformat() == "2026-05-29" for structure in structures))

    def test_payoff_and_model_fair_value_from_thesis(self):
        long_call = normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28))
        short_call = normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48))
        structure = build_debit_vertical(long_call, short_call)
        thesis = normalize_thesis({"id": "t", "direction": "up", "targetPrice": 260, "targetProbability": 0.35, "maxLossCap": 100})
        self.assertAlmostEqual(payoff_at_price(structure, 260), 1000.0)
        fair, payoff, rr = model_fair_value_from_thesis(structure, thesis)
        self.assertAlmostEqual(payoff, 1000.0)
        self.assertAlmostEqual(fair, 350.0)
        self.assertAlmostEqual(rr, (1000.0 - 86.0) / 86.0)

    def test_find_opportunities_for_thesis_ranks_asymmetric_debit_verticals(self):
        contracts = [
            normalize_contract(raw_contract(symbol="NVDA260522C00245000", strike=245, bid=2.00, ask=2.10)),
            normalize_contract(raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28)),
            normalize_contract(raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48)),
            normalize_contract(raw_contract(symbol="NVDA260522C00270000", strike=270, bid=0.12, ask=0.16)),
        ]
        thesis = normalize_thesis(
            {
                "id": "nvda-upside",
                "direction": "up",
                "targetPrice": 260,
                "targetProbability": 0.35,
                "eventDate": "2026-05-22",
                "maxLossCap": 150,
                "minRewardRisk": 3.0,
                "minEdgePctOfRisk": 0.20,
                "minProbabilityMargin": 0.05,
                "allowedStructures": ["debit_vertical", "long_call"],
            }
        )
        opportunities = find_opportunities_for_thesis(
            contracts,
            thesis,
            now=dt("2026-05-19T03:25:00Z"),
            config=OptionQuoteFilterConfig(),
        )
        self.assertGreaterEqual(len(opportunities), 1)
        self.assertTrue(all(opp.evaluation.passes for opp in opportunities))
        self.assertTrue(all(opp.structure.max_loss <= 150 for opp in opportunities if opp.structure.max_loss is not None))
        self.assertGreaterEqual(opportunities[0].score, opportunities[-1].score)
        self.assertGreater(opportunities[0].reward_risk, 3.0)
        self.assertEqual(opportunities[0].thesis.id, "nvda-upside")

    def test_find_opportunities_for_downside_thesis_uses_puts(self):
        contracts = [
            normalize_contract(raw_contract(symbol="NVDA260522P00220000", right="put", strike=220, bid=2.30, ask=2.40)),
            normalize_contract(raw_contract(symbol="NVDA260522P00210000", right="put", strike=210, bid=1.10, ask=1.18)),
            normalize_contract(raw_contract(symbol="NVDA260522C00250000", right="call", strike=250, bid=1.20, ask=1.28)),
        ]
        thesis = normalize_thesis(
            {
                "id": "nvda-downside",
                "direction": "down",
                "targetPrice": 210,
                "targetProbability": 0.40,
                "eventDate": "2026-05-22",
                "maxLossCap": 150,
                "minRewardRisk": 3.0,
                "allowedStructures": ["debit_vertical"],
            }
        )
        opportunities = find_opportunities_for_thesis(contracts, thesis, now=dt("2026-05-19T03:25:00Z"))
        self.assertEqual(len(opportunities), 1)
        self.assertEqual(opportunities[0].structure.right, "put")
        self.assertEqual(opportunities[0].structure.structure_type, "debit_vertical")

    def options_fixture(self):
        return {
            "chain": {
                "underlying": "NVDA",
                "provider": "fixture",
                "underlying_bid": 224.40,
                "underlying_ask": 224.45,
                "quote_ts": "2026-05-19T03:20:00Z",
                "contracts": [
                    raw_contract(symbol="NVDA260522C00250000", strike=250, bid=1.20, ask=1.28, delta=0.31),
                    raw_contract(symbol="NVDA260522C00260000", strike=260, bid=0.42, ask=0.48, delta=0.18),
                    raw_contract(symbol="NVDA260522C00350000", strike=350, bid=0.01, ask=0.04, volume=10, open_interest=20),
                ],
            },
            "theses": [
                {
                    "id": "nvda-generated-upside",
                    "direction": "up",
                    "targetPrice": 260,
                    "targetProbability": 0.35,
                    "eventDate": "2026-05-22",
                    "maxLossCap": 100,
                    "minRewardRisk": 3.0,
                    "allowedStructures": ["debit_vertical"],
                    "thesis": "generated fixture upside thesis",
                    "catalyst": "earnings guidance",
                    "plannedExit": "post-event mark",
                    "falsifier": "guide unchanged",
                }
            ],
            "signals": [
                {
                    "id": "nvda-upside-spread",
                    "structure": "debit_vertical",
                    "long": "NVDA260522C00250000",
                    "short": "NVDA260522C00260000",
                    "modelFairValue": 125.0,
                    "modelProbability": 0.25,
                    "thesis": "fixture catalyst creates upside distribution mismatch",
                    "catalyst": "earnings guidance",
                    "plannedExit": "post-event mark",
                    "falsifier": "guide unchanged",
                },
                {
                    "id": "bad-lottery-ticket",
                    "structure": "long_call",
                    "contract": "NVDA260522C00350000",
                    "modelFairValue": 6.0,
                    "modelProbability": 0.03,
                },
            ],
        }

    def test_options_daemon_generates_fixture_candidate_event_and_rejections(self):
        fixture = self.options_fixture()
        fixture["theses"] = []
        events, rejections = options_daemon.generate_options_events(
            fixture=fixture,
            now=dt("2026-05-19T03:25:00Z"),
            session_id="session-123",
            state={"emitted_signals": {}},
            config=OptionQuoteFilterConfig(),
            min_edge_pct_of_risk=0.20,
            min_probability_margin=0.05,
            max_loss_cap=100.0,
            max_events=5,
        )
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["type"], "options_signal_candidate")
        self.assertEqual(event["source"], "rime-forecasts/options-daemon")
        self.assertEqual(event["sessionId"], "session-123")
        self.assertEqual(event["payload"]["signalId"], "nvda-upside-spread")
        self.assertEqual(event["payload"]["structure"]["structure_type"], "debit_vertical")
        self.assertAlmostEqual(event["payload"]["evaluation"]["edge_dollars"], 39.0)
        self.assertTrue(event["payload"]["evaluation"]["passes"])
        self.assertEqual(event["payload"]["dedupeKey"], "options_signal:nvda-upside-spread")
        self.assertEqual(len(rejections), 1)
        self.assertEqual(rejections[0]["signalId"], "bad-lottery-ticket")
        self.assertIn("leg quote filter failed", rejections[0]["reason"])

    def test_options_daemon_generates_events_from_thesis_search(self):
        fixture = self.options_fixture()
        fixture["signals"] = []
        events, rejections = options_daemon.generate_options_events(
            fixture=fixture,
            now=dt("2026-05-19T03:25:00Z"),
            session_id="session-123",
            state={"emitted_signals": {}},
            config=OptionQuoteFilterConfig(),
            min_edge_pct_of_risk=0.20,
            min_probability_margin=0.05,
            max_loss_cap=100.0,
            max_events=5,
        )
        self.assertGreaterEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["type"], "options_signal_candidate")
        self.assertEqual(event["payload"]["sourceMode"], "thesis_search")
        self.assertEqual(event["payload"]["thesis"]["id"], "nvda-generated-upside")
        self.assertEqual(event["payload"]["structure"]["structure_type"], "debit_vertical")
        self.assertTrue(event["payload"]["evaluation"]["passes"])
        self.assertGreater(event["payload"]["rewardRisk"], 3.0)

    def test_options_daemon_skips_inactive_provider_fixture_without_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp) / "theses"
            fixture_dir.mkdir()
            (fixture_dir / "inactive.json").write_text(
                json.dumps(
                    {
                        "active": False,
                        "underlying": "NVDA",
                        "theses": [
                            {
                                "id": "inactive-provider-thesis",
                                "direction": "up",
                                "targetPrice": 260,
                                "targetProbability": 0.35,
                                "optionExpiry": "2026-05-22",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = options_daemon.build_parser().parse_args(
                [
                    "--fixture-dir",
                    str(fixture_dir),
                    "--state-path",
                    str(Path(tmp) / "state.json"),
                    "--ticket-dir",
                    str(Path(tmp) / "tickets"),
                    "--dry-run",
                    "--no-ticket-events",
                ]
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = options_daemon.poll_once(args, session_id=None)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(payload["eventCount"], 0)
            self.assertEqual(payload["rejections"][0]["reason"], "inactive fixture")

    def test_options_daemon_materializes_provider_backed_thesis_fixture(self):
        chain_fixture = self.options_fixture()["chain"]
        provider = FixtureOptionProvider.from_mapping({"chain": chain_fixture})
        provider_fixture = {
            "underlying": "NVDA",
            "theses": [
                {
                    "id": "provider-upside",
                    "direction": "up",
                    "targetPrice": 260,
                    "targetProbability": 0.35,
                    "eventDate": "2026-05-22",
                    "maxLossCap": 100,
                    "minRewardRisk": 3.0,
                    "allowedStructures": ["debit_vertical"],
                }
            ],
        }
        materialized = options_daemon.materialize_provider_fixture(provider_fixture, provider)
        self.assertIn("chain", materialized)
        events, rejections = options_daemon.generate_options_events(
            fixture=materialized,
            now=dt("2026-05-19T03:25:00Z"),
            session_id="session-123",
            state={"emitted_signals": {}},
            config=OptionQuoteFilterConfig(),
            min_edge_pct_of_risk=0.20,
            min_probability_margin=0.05,
            max_loss_cap=100.0,
            max_events=5,
        )
        self.assertEqual(rejections, [])
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["payload"]["sourceMode"], "thesis_search")

    def test_options_daemon_dedupes_emitted_signals(self):
        fixture = self.options_fixture()
        fixture["theses"] = []
        events, rejections = options_daemon.generate_options_events(
            fixture=fixture,
            now=dt("2026-05-19T03:25:00Z"),
            session_id="session-123",
            state={"emitted_signals": {"nvda-upside-spread": {"event_id": "old"}}},
            config=OptionQuoteFilterConfig(),
            min_edge_pct_of_risk=0.20,
            min_probability_margin=0.05,
            max_loss_cap=100.0,
            max_events=5,
        )
        self.assertEqual(events, [])
        self.assertTrue(any(row.get("reason") == "already emitted" for row in rejections))

    def _sample_option_ticket(self):
        fixture = self.options_fixture()
        fixture["signals"] = []
        events, _ = options_daemon.generate_options_events(
            fixture=fixture,
            now=dt("2026-05-19T03:25:00Z"),
            session_id="session-123",
            state={"emitted_signals": {}},
            config=OptionQuoteFilterConfig(),
            min_edge_pct_of_risk=0.20,
            min_probability_margin=0.05,
            max_loss_cap=100.0,
            max_events=1,
        )
        return option_ticket_from_event(events[0], now=dt("2026-05-19T03:25:00Z"))

    def test_option_ticket_artifact_markout_and_ledger_row(self):
        ticket = self._sample_option_ticket()
        self.assertEqual(ticket["status"], "draft")
        self.assertFalse(ticket["live_submit_allowed"])
        self.assertEqual(ticket["source_mode"], "thesis_search")
        self.assertEqual(ticket["underlying"], "NVDA")
        self.assertIn("entry", ticket)
        mark = option_markout(
            ticket,
            checkpoint="1h",
            mark_value=120.0,
            underlying_price=252.0,
            now=dt("2026-05-19T04:25:00Z"),
            notes="favorable early mark",
        )
        self.assertAlmostEqual(mark["pnl"], 34.0)
        updated = add_option_markout(ticket, mark)
        self.assertEqual(updated["status"], "paper_open")
        self.assertIn("1h", updated["markouts"])
        row = options_ledger_row(updated)
        self.assertIn("NVDA", row)
        self.assertIn("$120.00", row)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_option_ticket(updated, tmp)
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["ticket_id"], updated["ticket_id"])

    def test_thesis_refresh_events_emit_stale_active_search_review(self):
        fixture = self.options_fixture()
        fixture["signals"] = []
        fixture["strategy"] = "situational-awareness-ai-stack"
        fixture["source"] = "rime-forecasts/sa-thesis-scan"
        fixture["reviewedAt"] = "2026-05-10T00:00:00Z"
        state = {"emitted_signals": {}, "thesis_refresh_events": {}, "thesis_refresh_status": {}}
        events, rejections = options_daemon.generate_thesis_refresh_events(
            fixture=fixture,
            now=dt("2026-05-19T03:25:00Z"),
            session_id="session-123",
            state=state,
            config=OptionQuoteFilterConfig(),
            max_events=5,
            refresh_days=7,
            expiry_review_days=7,
            spot_move_pct=0.08,
        )
        self.assertEqual(rejections, [])
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["type"], "options_thesis_refresh_due")
        self.assertEqual(event["sessionId"], "session-123")
        self.assertEqual(event["payload"]["thesisId"], "nvda-generated-upside")
        self.assertIn("review_stale_7d", event["payload"]["reasons"])
        self.assertIn("no_signal_7d", event["payload"]["reasons"])
        self.assertIn("expiry_within_7d", event["payload"]["reasons"])
        self.assertGreaterEqual(event["payload"]["structureSearch"]["passingStructureCount"], 1)
        self.assertIn("nvda-generated-upside", state["thesis_refresh_status"])
        options_daemon.mark_thesis_refresh_events_emitted(state, events, now=dt("2026-05-19T03:25:00Z"))
        again, rejections = options_daemon.generate_thesis_refresh_events(
            fixture=fixture,
            now=dt("2026-05-19T04:25:00Z"),
            session_id="session-123",
            state=state,
            config=OptionQuoteFilterConfig(),
            max_events=5,
            refresh_days=7,
            expiry_review_days=7,
        )
        self.assertEqual(again, [])
        self.assertTrue(any(row.get("reason") == "refresh already emitted" for row in rejections))

    def test_ticket_lifecycle_events_emit_clv_and_expiry_wakes(self):
        ticket = self._sample_option_ticket()
        ticket["status"] = "paper_open"
        with tempfile.TemporaryDirectory() as tmp:
            ticket_path = write_option_ticket(ticket, tmp)
            events, rejections = options_daemon.generate_ticket_lifecycle_events(
                ticket_dir=Path(tmp),
                state={"clv_events": {}, "exit_events": {}},
                now=dt("2026-05-19T04:26:00Z"),
                session_id="session-123",
                max_events=5,
                schedule_statuses=("paper_open",),
            )
            self.assertEqual(rejections, [])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["type"], "options_clv_checkpoint_due")
            self.assertEqual(events[0]["payload"]["checkpoint"], "1h")
            self.assertEqual(events[0]["payload"]["ticketPath"], str(ticket_path))

            exit_events, _ = options_daemon.generate_ticket_lifecycle_events(
                ticket_dir=Path(tmp),
                state={"clv_events": {}, "exit_events": {}},
                now=dt("2026-05-22T21:30:00Z"),
                session_id="session-123",
                max_events=5,
                schedule_statuses=("paper_open",),
            )
        self.assertTrue(any(event["type"] == "options_expiry_or_exit" for event in exit_events))

    def test_options_daemon_can_run_lifecycle_only_from_ticket_dir(self):
        ticket = self._sample_option_ticket()
        ticket["status"] = "paper_open"
        with tempfile.TemporaryDirectory() as tmp:
            ticket_dir = Path(tmp) / "tickets"
            fixture_dir = Path(tmp) / "empty-fixtures"
            fixture_dir.mkdir()
            write_option_ticket(ticket, ticket_dir)
            parser = options_daemon.build_parser()
            args = parser.parse_args([
                "--fixture-dir",
                str(fixture_dir),
                "--ticket-dir",
                str(ticket_dir),
                "--dry-run",
                "--now",
                "2026-05-19T04:26:00Z",
            ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                count = options_daemon.poll_once(args, session_id=None)
        payload = json.loads(output.getvalue())
        self.assertEqual(count, 1)
        self.assertEqual(payload["lifecycleEventCount"], 1)
        self.assertEqual(payload["events"][0]["type"], "options_clv_checkpoint_due")

    def test_mark_structure_value_from_chain_and_markout_cli(self):
        ticket = self._sample_option_ticket()
        mark_chain = {
            "underlying": "NVDA",
            "provider": "fixture",
            "underlying_bid": 251.90,
            "underlying_ask": 252.10,
            "quote_ts": "2026-05-19T04:25:00Z",
            "contracts": [
                raw_contract(symbol="NVDA260522C00250000", strike=250, bid=5.90, ask=6.10, quote_ts="2026-05-19T04:25:00Z"),
                raw_contract(symbol="NVDA260522C00260000", strike=260, bid=1.90, ask=2.10, quote_ts="2026-05-19T04:25:00Z"),
            ],
        }
        snapshot = parse_option_chain_snapshot(mark_chain)
        self.assertAlmostEqual(mark_structure_value_from_chain(ticket["structure"], snapshot), 400.0)
        with tempfile.TemporaryDirectory() as tmp:
            ticket_path = write_option_ticket(ticket, tmp)
            fixture_path = Path(tmp) / "mark-chain.json"
            fixture_path.write_text(json.dumps(mark_chain), encoding="utf-8")
            old_argv = __import__("sys").argv
            output = io.StringIO()
            try:
                __import__("sys").argv = [
                    "options-markout.py",
                    "--ticket",
                    str(ticket_path),
                    "--fixture",
                    str(fixture_path),
                    "--checkpoint",
                    "1h",
                    "--now",
                    "2026-05-19T04:25:00Z",
                    "--append-ledger",
                    "--ledger",
                    str(Path(tmp) / "ledger.md"),
                ]
                with contextlib.redirect_stdout(output):
                    rc = options_markout.main()
            finally:
                __import__("sys").argv = old_argv
            saved = json.loads(ticket_path.read_text(encoding="utf-8"))
            ledger_text = (Path(tmp) / "ledger.md").read_text(encoding="utf-8")
        self.assertEqual(rc, 0)
        self.assertIn("$400.00", output.getvalue())
        self.assertIn("$400.00", ledger_text)
        self.assertIn("1h", saved["markouts"])
        self.assertAlmostEqual(saved["markouts"]["1h"]["pnl"], 314.0)

    def test_options_chain_fetch_cli_uses_fixture_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture_path = Path(tmp) / "fixture.json"
            output_path = Path(tmp) / "chain.json"
            fixture_path.write_text(json.dumps({"chain": self.options_fixture()["chain"]}), encoding="utf-8")
            old_argv = __import__("sys").argv
            try:
                __import__("sys").argv = [
                    "options-chain-fetch.py",
                    "--provider",
                    "fixture",
                    "--fixture",
                    str(fixture_path),
                    "--underlying",
                    "NVDA",
                    "--expiry",
                    "2026-05-22",
                    "--output",
                    str(output_path),
                ]
                rc = options_chain_fetch.main()
            finally:
                __import__("sys").argv = old_argv
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(payload["underlying"], "NVDA")
        self.assertGreaterEqual(len(payload["contracts"]), 2)

    def test_options_daemon_dry_run_cli_prints_event_and_can_write_tickets(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            ticket_dir = Path(tmp) / "tickets"
            path.write_text(json.dumps(self.options_fixture()), encoding="utf-8")
            # Exercise parser/poll path without wake writes or state writes.
            parser = options_daemon.build_parser()
            args = parser.parse_args([
                "--fixture",
                str(path),
                "--dry-run",
                "--now",
                "2026-05-19T03:25:00Z",
                "--write-tickets",
                "--ticket-dir",
                str(ticket_dir),
            ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                count = options_daemon.poll_once(args, session_id=None)
            ticket_files = sorted(ticket_dir.glob("*.json"))
        self.assertEqual(count, 2)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["eventCount"], 2)
        self.assertEqual(payload["events"][0]["payload"]["sourceMode"], "thesis_search")
        self.assertEqual(payload["events"][1]["payload"]["signalId"], "nvda-upside-spread")
        self.assertEqual(payload["ticketsWritten"], 2)
        self.assertEqual(len(ticket_files), 2)


if __name__ == "__main__":
    unittest.main()
