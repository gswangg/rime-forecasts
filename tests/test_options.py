import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from automation.options import (
    OptionQuoteFilterConfig,
    black_scholes_price,
    breakeven_probability,
    build_credit_vertical,
    build_debit_vertical,
    build_long_option,
    contract_quote_filter_reason,
    evaluate_structure_edge,
    filter_contracts,
    load_option_chain_snapshot,
    normalize_contract,
    parse_option_chain_snapshot,
    risk_neutral_probability_above,
    risk_neutral_probability_between,
    single_leg_spread_limit,
    time_to_expiry_years,
)


_OPTIONS_DAEMON_PATH = Path(__file__).resolve().parents[1] / "scripts" / "options-daemon.py"
_OPTIONS_DAEMON_SPEC = importlib.util.spec_from_file_location("options_daemon", _OPTIONS_DAEMON_PATH)
assert _OPTIONS_DAEMON_SPEC and _OPTIONS_DAEMON_SPEC.loader
options_daemon = importlib.util.module_from_spec(_OPTIONS_DAEMON_SPEC)
_OPTIONS_DAEMON_SPEC.loader.exec_module(options_daemon)


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
        events, rejections = options_daemon.generate_options_events(
            fixture=self.options_fixture(),
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

    def test_options_daemon_dedupes_emitted_signals(self):
        events, rejections = options_daemon.generate_options_events(
            fixture=self.options_fixture(),
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

    def test_options_daemon_dry_run_cli_prints_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(self.options_fixture()), encoding="utf-8")
            # Exercise parser/poll path without wake writes or state writes.
            parser = options_daemon.build_parser()
            args = parser.parse_args([
                "--fixture",
                str(path),
                "--dry-run",
                "--now",
                "2026-05-19T03:25:00Z",
            ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                count = options_daemon.poll_once(args, session_id=None)
        self.assertEqual(count, 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["eventCount"], 1)
        self.assertEqual(payload["events"][0]["payload"]["signalId"], "nvda-upside-spread")


if __name__ == "__main__":
    unittest.main()
