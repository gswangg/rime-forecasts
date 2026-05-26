import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from automation.options import FixtureOptionProvider, normalize_contract, parse_option_chain_snapshot
from automation.sa_thesis import (
    build_candidate,
    chain_summary,
    entry_directions,
    load_watchlist,
    merged_entry,
    quote_config_from_entry,
    select_expiry,
    spot_mid,
    trigger_reasons_for_entry,
)

_SA_SCAN_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sa-thesis-scan.py"
_SA_SCAN_SPEC = importlib.util.spec_from_file_location("sa_thesis_scan", _SA_SCAN_PATH)
assert _SA_SCAN_SPEC and _SA_SCAN_SPEC.loader
sa_thesis_scan = importlib.util.module_from_spec(_SA_SCAN_SPEC)
_SA_SCAN_SPEC.loader.exec_module(sa_thesis_scan)


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def raw_contract(**overrides):
    data = {
        "underlying": "CBRS",
        "provider": "fixture",
        "symbol": "CBRS260618C00400000",
        "expiry": "2026-06-18",
        "right": "call",
        "strike": 400.0,
        "style": "american",
        "settlement": "physical",
        "multiplier": 100,
        "underlying_bid": 330.0,
        "underlying_ask": 332.0,
        "bid": 25.30,
        "ask": 27.20,
        "last": 26.25,
        "volume": 254,
        "open_interest": 754,
        "quote_ts": "2026-05-20T13:57:00Z",
    }
    data.update(overrides)
    return data


def fixture_snapshot():
    return parse_option_chain_snapshot(
        {
            "underlying": "CBRS",
            "provider": "fixture",
            "underlying_bid": 330.0,
            "underlying_ask": 332.0,
            "quote_ts": "2026-05-20T13:57:00Z",
            "contracts": [
                raw_contract(symbol="CBRS260618C00400000", expiry="2026-06-18", right="call", strike=400, bid=25.30, ask=27.20, volume=254, open_interest=754),
                raw_contract(symbol="CBRS260618C00450000", expiry="2026-06-18", right="call", strike=450, bid=17.30, ask=18.90, volume=419, open_interest=603),
                raw_contract(symbol="CBRS260618P00300000", expiry="2026-06-18", right="put", strike=300, bid=27.80, ask=29.40, volume=408, open_interest=90),
                raw_contract(symbol="CBRS260717C00400000", expiry="2026-07-17", right="call", strike=400, bid=63.90, ask=69.10, volume=102, open_interest=30),
            ],
        }
    )


def watchlist_payload(**entry_overrides):
    entry = {
        "underlying": "CBRS",
        "theme": "frontier_compute",
        "priority": 95,
        "emitOnFirstSeen": True,
        "directions": ["up", "down"],
        "targetDays": 30,
        "minDaysToExpiry": 7,
        "maxDaysToExpiry": 60,
        "minLiquidContracts": 2,
        "targetMovePct": {"up": 0.35, "down": 0.25},
        "targetProbability": {"up": 0.25, "down": 0.30},
        "allowedStructures": ["debit_vertical"],
        "maxLossCap": 200,
        "minRewardRisk": 3,
        "minEdgePctOfRisk": 0.30,
        "minProbabilityMargin": 0.08,
        "catalyst": "post-IPO option liquidity",
        "mechanism": "frontier-compute scarcity repricing versus hype unwind",
        "falsifier": "chain remains too wide",
    }
    entry.update(entry_overrides)
    return {"version": 1, "strategy": "situational-awareness-ai-stack", "defaults": {}, "entries": [entry]}


class SAThesisTests(unittest.TestCase):
    def test_select_expiry_chooses_nearest_target_inside_window(self):
        expiry = select_expiry(
            [date(2026, 5, 22), date(2026, 6, 18), date(2026, 7, 17)],
            now=dt("2026-05-20T13:57:00Z"),
            target_days=30,
            min_days_to_expiry=7,
            max_days_to_expiry=60,
        )
        self.assertEqual(expiry, date(2026, 6, 18))

    def test_chain_summary_counts_liquid_contracts(self):
        snapshot = fixture_snapshot()
        entry = watchlist_payload()["entries"][0]
        summary = chain_summary(snapshot, now=dt("2026-05-20T14:00:00Z"), config=quote_config_from_entry(entry))
        self.assertAlmostEqual(spot_mid(snapshot), 331.0)
        self.assertEqual(summary["contractCount"], 4)
        self.assertGreaterEqual(summary["liquidContractCount"], 3)
        self.assertEqual(summary["liquidCallCount"], 3)

    def test_trigger_reasons_first_seen_and_spot_move(self):
        entry = watchlist_payload()["entries"][0]
        self.assertEqual(trigger_reasons_for_entry(entry=entry, state_row=None, current_spot=331.0, current_liquid_contracts=3), ("first_seen",))
        self.assertEqual(
            trigger_reasons_for_entry(entry=entry, state_row={"last_spot": 331.0, "last_liquid_contracts": 3}, current_spot=331.0, current_liquid_contracts=3),
            ("first_seen",),
        )
        moved = trigger_reasons_for_entry(
            entry={**entry, "emitOnFirstSeen": False, "spotMoveTriggerPct": 0.10},
            state_row={"last_spot": 290.0, "last_liquid_contracts": 3},
            current_spot=331.0,
            current_liquid_contracts=3,
        )
        self.assertTrue(any(reason.startswith("spot_move_") for reason in moved))

    def test_build_candidate_is_inactive_fixture_with_option_expiry(self):
        snapshot = fixture_snapshot()
        entry = watchlist_payload()["entries"][0]
        summary = chain_summary(snapshot, now=dt("2026-05-20T14:00:00Z"), config=quote_config_from_entry(entry))
        candidate = build_candidate(
            strategy="situational-awareness-ai-stack",
            entry=entry,
            direction="up",
            now=dt("2026-05-20T14:00:00Z"),
            spot=331.0,
            option_expiry=date(2026, 6, 18),
            chain_summary=summary,
            trigger_reasons=("first_seen",),
        )
        self.assertEqual(candidate.underlying, "CBRS")
        self.assertEqual(candidate.direction, "up")
        self.assertFalse(candidate.thesis_fixture["active"])
        thesis = candidate.thesis_fixture["theses"][0]
        self.assertFalse(thesis["active"])
        self.assertEqual(thesis["optionExpiry"], "2026-06-18")
        self.assertAlmostEqual(thesis["targetPrice"], 446.85)
        self.assertEqual(thesis["allowedStructures"], ["debit_vertical"])

    def test_scan_once_generates_and_dedupes_candidates(self):
        provider = FixtureOptionProvider(snapshot=fixture_snapshot())
        state = {"version": 1, "underlyings": {}, "emitted_candidates": {}}
        candidates, rejections = sa_thesis_scan.scan_once(
            watchlist=watchlist_payload(prequalifyEmissions=False),
            provider=provider,
            state=state,
            now=dt("2026-05-20T14:00:00Z"),
            max_events=5,
        )
        self.assertEqual(len(candidates), 2)
        self.assertEqual({candidate.direction for candidate in candidates}, {"up", "down"})
        self.assertIn("CBRS", state["underlyings"])
        state["emitted_candidates"] = {candidate.dedupe_key: {"event_id": "old"} for candidate in candidates}
        again, rejections = sa_thesis_scan.scan_once(
            watchlist=watchlist_payload(prequalifyEmissions=False),
            provider=provider,
            state=state,
            now=dt("2026-05-20T15:00:00Z"),
            max_events=5,
            force=True,
        )
        self.assertEqual(again, [])
        self.assertTrue(any(row.get("reason") == "already emitted" for row in rejections))

    def test_scan_once_prequalifies_first_seen(self):
        snapshot = parse_option_chain_snapshot(
            {
                "underlying": "CBRS",
                "provider": "fixture",
                "underlying_bid": 330.0,
                "underlying_ask": 332.0,
                "quote_ts": "2026-05-20T13:57:00Z",
                "contracts": [
                    raw_contract(symbol="CBRS260618C00400000", expiry="2026-06-18", right="call", strike=400, bid=1.10, ask=1.20, volume=254, open_interest=754),
                    raw_contract(symbol="CBRS260618C00450000", expiry="2026-06-18", right="call", strike=450, bid=0.90, ask=0.95, volume=419, open_interest=603),
                    raw_contract(symbol="CBRS260618P00300000", expiry="2026-06-18", right="put", strike=300, bid=0.50, ask=0.55, volume=408, open_interest=90),
                    raw_contract(symbol="CBRS260618P00250000", expiry="2026-06-18", right="put", strike=250, bid=0.30, ask=0.35, volume=408, open_interest=90),
                ],
            }
        )
        provider = FixtureOptionProvider(snapshot=snapshot)
        state = {"version": 1, "underlyings": {}, "emitted_candidates": {}}
        candidates, rejections = sa_thesis_scan.scan_once(
            watchlist=watchlist_payload(directions=["up"], targetMovePct={"up": 0.4, "down": 0.25}),
            provider=provider,
            state=state,
            now=dt("2026-05-20T14:00:00Z"),
            max_events=5,
        )
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0].prequalification["prequalified"])
        self.assertGreater(candidates[0].prequalification["structureSearch"]["passingStructureCount"], 0)

    def test_scan_once_blocks_unqualified_first_seen(self):
        provider = FixtureOptionProvider(snapshot=fixture_snapshot())
        state = {"version": 1, "underlyings": {}, "emitted_candidates": {}}
        candidates, rejections = sa_thesis_scan.scan_once(
            watchlist=watchlist_payload(directions=["up"]),
            provider=provider,
            state=state,
            now=dt("2026-05-20T14:00:00Z"),
            max_events=5,
        )
        self.assertEqual(candidates, [])
        self.assertTrue(any(row.get("reason") == "first_seen prequalification failed" for row in rejections))

    def test_emission_requires_prequalification_gates_all_non_force_triggers(self):
        from automation.sa_thesis import emission_requires_prequalification
        entry_default = {"underlying": "X"}
        # default: prequalification required for any non-force trigger
        self.assertTrue(emission_requires_prequalification(entry_default, ("first_seen",)))
        self.assertTrue(emission_requires_prequalification(entry_default, ("liquidity_crossed_2",)))
        self.assertTrue(emission_requires_prequalification(entry_default, ("spot_move_+12.3%",)))
        self.assertTrue(emission_requires_prequalification(entry_default, ("first_seen", "liquidity_crossed_2")))
        # force always bypasses
        self.assertFalse(emission_requires_prequalification(entry_default, ("force",)))
        self.assertFalse(emission_requires_prequalification(entry_default, ("force", "liquidity_crossed_2")))
        # explicit opt-out via new flag
        entry_opt_out = {"underlying": "X", "prequalifyEmissions": False}
        self.assertFalse(emission_requires_prequalification(entry_opt_out, ("liquidity_crossed_2",)))
        self.assertFalse(emission_requires_prequalification(entry_opt_out, ("first_seen",)))
        # legacy prequalifyFirstSeen=False only carves out the first-seen-only case
        entry_legacy = {"underlying": "X", "prequalifyFirstSeen": False}
        self.assertFalse(emission_requires_prequalification(entry_legacy, ("first_seen",)))
        self.assertTrue(emission_requires_prequalification(entry_legacy, ("liquidity_crossed_2",)))
        self.assertTrue(emission_requires_prequalification(entry_legacy, ("first_seen", "liquidity_crossed_2")))

    def test_scan_once_blocks_non_first_seen_unqualified_emission(self):
        # Build a sparse-chain snapshot that previously would emit unprequalified
        # liquidity_crossed_2 wakes (the MRVL/CRWV bug from operations).
        sparse_snapshot = parse_option_chain_snapshot({
            "underlying": "CBRS", "provider": "fixture",
            "underlying_bid": 330.0, "underlying_ask": 332.0,
            "quote_ts": "2026-05-26T17:00:00Z",
            "contracts": [
                raw_contract(symbol="CBRS260618P00300000", expiry="2026-06-18", right="put", strike=300, bid=27.80, ask=29.40, volume=408, open_interest=620),
                raw_contract(symbol="CBRS260618P00280000", expiry="2026-06-18", right="put", strike=280, bid=15.30, ask=16.10, volume=412, open_interest=520),
            ],
        })
        provider = FixtureOptionProvider(snapshot=sparse_snapshot)
        # Prior state had 0 liquid contracts; current chain has 2 -> crosses min.
        state = {
            "version": 1,
            "underlyings": {"CBRS": {"last_liquid_contracts": 0, "last_spot": 331.0, "first_seen_reviewed": True}},
            "emitted_candidates": {},
        }
        candidates, rejections = sa_thesis_scan.scan_once(
            watchlist=watchlist_payload(),
            provider=provider,
            state=state,
            now=dt("2026-05-26T17:00:00Z"),
            max_events=5,
        )
        # Up direction: 0 liquid calls -> prequalification fails -> no emit.
        # Down direction: 2 liquid puts but structure search produces nothing
        # passing -> prequalification fails -> no emit.
        self.assertEqual(candidates, [])
        self.assertTrue(any("prequalification failed" in str(r.get("reason", "")) for r in rejections))

    def test_scan_once_suppresses_first_seen_without_flag(self):
        provider = FixtureOptionProvider(snapshot=fixture_snapshot())
        state = {"version": 1, "underlyings": {}, "emitted_candidates": {}}
        candidates, rejections = sa_thesis_scan.scan_once(
            watchlist=watchlist_payload(emitOnFirstSeen=False),
            provider=provider,
            state=state,
            now=dt("2026-05-20T14:00:00Z"),
            max_events=5,
        )
        self.assertEqual(candidates, [])
        self.assertTrue(any(row.get("reason") == "no trigger" for row in rejections))

    def test_cli_dry_run_with_fixture_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            watchlist = tmp_path / "watchlist.json"
            fixture = tmp_path / "chain.json"
            watchlist.write_text(json.dumps(watchlist_payload(prequalifyEmissions=False)), encoding="utf-8")
            fixture.write_text(json.dumps(fixture_snapshot().to_dict()), encoding="utf-8")
            args = sa_thesis_scan.build_parser().parse_args(
                [
                    "--watchlist",
                    str(watchlist),
                    "--provider",
                    "fixture",
                    "--fixture",
                    str(fixture),
                    "--dry-run",
                    "--now",
                    "2026-05-20T14:00:00Z",
                ]
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = sa_thesis_scan.poll_once(args, session_id=None)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(result, 2)
            self.assertEqual(payload["candidateCount"], 2)
            self.assertEqual(payload["eventCount"], 2)
            self.assertEqual(payload["events"][0]["type"], "options_thesis_review_due")
            self.assertEqual(payload["events"][0]["sessionId"], "dry-run-session")


if __name__ == "__main__":
    unittest.main()
