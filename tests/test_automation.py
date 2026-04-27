import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from automation.clv import due_clv_checkpoints
from automation.config import require_session_id
from automation.daemon_core import default_state, generate_events, mark_emitted
from automation.horizons import horizon_decision
from automation.kalshi import candidate_filter_reason as kalshi_candidate_filter_reason
from automation.kalshi import normalize_market as normalize_kalshi_market
from automation.kalshi_core import default_state as kalshi_default_state
from automation.kalshi_core import generate_events as generate_kalshi_events
from automation.polymarket import candidate_filter_reason, normalize_market
from automation.reasoning import extract_polymarket_watches
from automation.wake import write_wake_event


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def raw_market(**overrides):
    data = {
        "id": "123",
        "question": "Will test happen by May 31?",
        "slug": "will-test-happen-by-may-31",
        "active": True,
        "closed": False,
        "endDate": "2026-05-31T00:00:00Z",
        "liquidityNum": 6000,
        "volumeNum": 120000,
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.42", "0.58"]',
        "bestBid": 0.41,
        "bestAsk": 0.43,
        "lastTradePrice": 0.42,
    }
    data.update(overrides)
    return data


def raw_kalshi_market(**overrides):
    data = {
        "ticker": "KXTEST-26APR-T1",
        "event_ticker": "KXTEST-26APR",
        "market_type": "binary",
        "title": "Will test happen this week?",
        "status": "active",
        "close_time": "2026-04-30T00:00:00Z",
        "expiration_time": "2026-04-30T00:00:00Z",
        "yes_bid_dollars": "0.41",
        "yes_ask_dollars": "0.43",
        "last_price_dollars": "0.42",
        "liquidity_dollars": "6000",
        "volume_fp": "12000",
        "open_interest_fp": "2000",
        "category": "Economics",
    }
    data.update(overrides)
    return data


class AutomationTests(unittest.TestCase):
    def test_require_session_id_is_explicit(self):
        self.assertEqual(require_session_id("cli-session", {}, dry_run=False), "cli-session")
        self.assertEqual(require_session_id(None, {"RIME_WAKE_SESSION_ID": "env-session"}, dry_run=False), "env-session")
        with self.assertRaises(ValueError):
            require_session_id(None, {}, dry_run=False)
        self.assertIsNone(require_session_id(None, {}, dry_run=True))

    def test_polymarket_candidate_filter(self):
        now = dt("2026-04-26T00:00:00Z")
        market = normalize_market(raw_market())
        ok, reason = candidate_filter_reason(market, now=now)
        self.assertTrue(ok, reason)
        self.assertAlmostEqual(market.yes_price, 0.42)

        low_liquidity = normalize_market(raw_market(liquidityNum=100, volumeNum=100))
        ok, reason = candidate_filter_reason(low_liquidity, now=now)
        self.assertFalse(ok)
        self.assertIn("real volume", reason)

        passive_liquidity = normalize_market(raw_market(liquidityNum=75_000, volumeNum=135))
        ok, reason = candidate_filter_reason(passive_liquidity, now=now)
        self.assertFalse(ok)
        self.assertIn("real volume", reason)

        tail_price = normalize_market(raw_market(outcomePrices='["0.028", "0.972"]', bestBid=0.026, bestAsk=0.03))
        ok, reason = candidate_filter_reason(tail_price, now=now)
        self.assertFalse(ok)
        self.assertIn("candidate band", reason)

        wide_spread = normalize_market(raw_market(bestBid=0.20, bestAsk=0.40, outcomePrices='["0.30", "0.70"]'))
        ok, reason = candidate_filter_reason(wide_spread, now=now)
        self.assertFalse(ok)
        self.assertIn("spread", reason)

        generic_draw = normalize_market(raw_market(question="Will Southampton FC vs. Ipswich Town FC end in a draw?"))
        ok, reason = candidate_filter_reason(generic_draw, now=now)
        self.assertFalse(ok)
        self.assertIn("generic team-match", reason)

        generic_win = normalize_market(raw_market(question="Will CA Unión win on 2026-04-27?"))
        ok, reason = candidate_filter_reason(generic_win, now=now)
        self.assertFalse(ok)
        self.assertIn("generic team-match", reason)

        generic_btts = normalize_market(raw_market(question="Paris Saint-Germain FC vs. FC Bayern München: Both Teams to Score"))
        ok, reason = candidate_filter_reason(generic_btts, now=now)
        self.assertFalse(ok)
        self.assertIn("generic team-match", reason)

        weather_range_f = normalize_market(raw_market(question="Will the highest temperature in Dallas be between 82-83°F on April 28?"))
        ok, reason = candidate_filter_reason(weather_range_f, now=now)
        self.assertFalse(ok)
        self.assertIn("weather range", reason)

        weather_exact_c = normalize_market(raw_market(question="Will the highest temperature in Chengdu be 24°C on April 28?"))
        ok, reason = candidate_filter_reason(weather_exact_c, now=now)
        self.assertFalse(ok)
        self.assertIn("weather range", reason)

        weather_threshold_c = normalize_market(raw_market(question="Will the highest temperature in Taipei be 34°C or higher on April 28?"))
        ok, reason = candidate_filter_reason(weather_threshold_c, now=now)
        self.assertFalse(ok)
        self.assertIn("weather range", reason)

        crypto_threshold = normalize_market(raw_market(question="Will the price of Ethereum be above $2,400 on April 28?"))
        ok, reason = candidate_filter_reason(crypto_threshold, now=now)
        self.assertFalse(ok)
        self.assertIn("crypto price market", reason)

        crypto_range = normalize_market(raw_market(question="Will the price of Bitcoin be between $80,000 and $82,000 on April 28?"))
        ok, reason = candidate_filter_reason(crypto_range, now=now)
        self.assertFalse(ok)
        self.assertIn("crypto price market", reason)

        crypto_greater_than = normalize_market(raw_market(question="Will the price of Bitcoin be greater than $84,000 on April 28?"))
        ok, reason = candidate_filter_reason(crypto_greater_than, now=now)
        self.assertFalse(ok)
        self.assertIn("crypto price market", reason)

        non_binary = normalize_market(raw_market(outcomes='["A", "B", "C"]', outcomePrices='["0.2", "0.3", "0.5"]'))
        ok, reason = candidate_filter_reason(non_binary, now=now)
        self.assertFalse(ok)
        self.assertIn("binary", reason)

        too_soon = normalize_market(raw_market(endDate="2026-04-26T12:00:00Z"))
        ok, reason = candidate_filter_reason(too_soon, now=now)
        self.assertFalse(ok)
        self.assertIn("too near", reason)

        tertiary_low_signal = normalize_market(raw_market(endDate="2026-05-25T00:00:00Z", liquidityNum=6000, volumeNum=12000))
        ok, reason = candidate_filter_reason(tertiary_low_signal, now=now)
        self.assertFalse(ok)
        self.assertIn("tertiary", reason)

        tertiary_high_signal = normalize_market(raw_market(endDate="2026-05-25T00:00:00Z", liquidityNum=26000, volumeNum=12000))
        ok, reason = candidate_filter_reason(tertiary_high_signal, now=now)
        self.assertTrue(ok, reason)

    def test_horizon_priority_ladder(self):
        now = dt("2026-04-26T00:00:00Z")
        primary = horizon_decision(dt("2026-04-30T00:00:00Z"), now=now, liquidity=6000, volume=12000)
        secondary = horizon_decision(dt("2026-05-10T00:00:00Z"), now=now, liquidity=6000, volume=12000)
        tertiary = horizon_decision(dt("2026-05-25T00:00:00Z"), now=now, liquidity=26000, volume=12000)
        self.assertEqual((primary.bucket, primary.priority), ("primary", 80))
        self.assertEqual((secondary.bucket, secondary.priority), ("secondary", 65))
        self.assertEqual((tertiary.bucket, tertiary.priority), ("tertiary", 45))

    def test_kalshi_candidate_filter_and_event_generation(self):
        now = dt("2026-04-26T00:00:00Z")
        market = normalize_kalshi_market(raw_kalshi_market())
        ok, reason = kalshi_candidate_filter_reason(market, now=now)
        self.assertTrue(ok, reason)
        self.assertAlmostEqual(market.yes_price, 0.42)

        missing_price = normalize_kalshi_market(raw_kalshi_market(yes_bid_dollars="0.0000", yes_ask_dollars="0.0000", last_price_dollars="0.0000"))
        ok, reason = kalshi_candidate_filter_reason(missing_price, now=now)
        self.assertFalse(ok)
        self.assertIn("YES price", reason)

        stale_last_wide_spread = normalize_kalshi_market(raw_kalshi_market(yes_bid_dollars="0.0000", yes_ask_dollars="1.0000", last_price_dollars="0.098"))
        ok, reason = kalshi_candidate_filter_reason(stale_last_wide_spread, now=now)
        self.assertFalse(ok)
        self.assertIn("not actionable", reason)

        near_certain = normalize_kalshi_market(raw_kalshi_market(yes_bid_dollars="0.9800", yes_ask_dollars="0.9900", last_price_dollars="0.985"))
        ok, reason = kalshi_candidate_filter_reason(near_certain, now=now)
        self.assertFalse(ok)
        self.assertIn("candidate band", reason)

        low_real_volume = normalize_kalshi_market(raw_kalshi_market(liquidity_dollars="10000", volume_fp="50"))
        ok, reason = kalshi_candidate_filter_reason(low_real_volume, now=now)
        self.assertFalse(ok)
        self.assertIn("real volume", reason)

        state = kalshi_default_state()
        events = generate_kalshi_events(markets=[market], state=state, now=now, session_id="session-123")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["source"], "rime-forecasts/kalshi-daemon")
        self.assertEqual(events[0]["type"], "candidate_found")
        self.assertEqual(events[0]["priority"], 80)
        self.assertEqual(events[0]["payload"]["venue"], "Kalshi")
        self.assertEqual(events[0]["payload"]["horizon"]["bucket"], "primary")

    def test_extract_polymarket_watches_from_reasoning(self):
        with tempfile.TemporaryDirectory() as tmp:
            reasoning = Path(tmp) / "reasoning"
            reasoning.mkdir()
            path = reasoning / "example.md"
            path.write_text(
                "# Example market — resolves 2026-05-31\n\n"
                "**Primary venue**: Polymarket\n"
                "**Primary URL**: https://polymarket.com/event/example\n"
                "**Polymarket market slug**: will-test-happen-by-may-31\n"
                "**Written**: 2026-04-26T00:00:00+00:00\n"
                "**Prediction**: 55%\n"
                "**Primary venue price at writing**: 42% YES\n"
            )
            watches = extract_polymarket_watches(reasoning)
            self.assertEqual(len(watches), 1)
            self.assertEqual(watches[0].slug, "will-test-happen-by-may-31")
            self.assertEqual(watches[0].prediction, 0.55)
            self.assertEqual(watches[0].price_at_writing, 0.42)

    def test_clv_checkpoint_scheduling_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            reasoning = Path(tmp) / "reasoning"
            reasoning.mkdir()
            path = reasoning / "example.md"
            path.write_text(
                "# Example\n\n"
                "**Polymarket market slug**: will-test-happen-by-may-31\n"
                "**Written**: 2026-04-26T00:00:00+00:00\n"
                "**Prediction**: 55%\n"
                "**Primary venue price at writing**: 42% YES\n"
            )
            watch = extract_polymarket_watches(reasoning)[0]
            state = default_state()
            due = due_clv_checkpoints([watch], state, now=dt("2026-04-26T07:00:00Z"))
            self.assertEqual([d.checkpoint for d in due], ["1h", "6h"])
            state["clv_checkpoints"][watch.key] = {"1h": {"event_id": "already"}}
            due = due_clv_checkpoints([watch], state, now=dt("2026-04-26T07:00:00Z"))
            self.assertEqual([d.checkpoint for d in due], ["6h"])

    def test_clv_is_aligned_to_prediction_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            reasoning = Path(tmp) / "reasoning"
            reasoning.mkdir()
            (reasoning / "running.md").write_text(
                "# Running Point\n\n"
                "**Polymarket market slug**: running-point\n"
                "**Written**: 2026-04-26T21:21:37+00:00\n"
                "**Prediction**: 30%\n"
                "**Primary venue price at writing**: 92.4% YES\n"
            )
            watch = extract_polymarket_watches(reasoning)[0]
            market = normalize_market(
                raw_market(
                    slug="running-point",
                    question="Running Point",
                    outcomePrices='["0.91", "0.09"]',
                    bestBid=0.902,
                    bestAsk=0.918,
                    lastTradePrice=0.919,
                )
            )
            events = generate_events(
                markets=[market],
                watches=[watch],
                state=default_state(),
                now=dt("2026-04-26T22:33:00Z"),
                session_id="session-123",
                max_candidate_events=0,
                max_events=5,
            )
            clv_events = [event for event in events if event["type"] == "clv_checkpoint_due"]
            self.assertEqual(len(clv_events), 1)
            payload = clv_events[0]["payload"]
            self.assertEqual(payload["checkpoint"], "1h")
            self.assertAlmostEqual(payload["rawYesMovePp"], -1.4)
            self.assertAlmostEqual(payload["clvPp"], 1.4)
            self.assertEqual(payload["clvDirection"], "toward_no")

    def test_write_wake_event_is_atomic_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = {
                "id": "rime-test-event",
                "sessionId": "session-123",
                "ts": "2026-04-26T00:00:00Z",
                "source": "test",
                "type": "candidate_found",
                "priority": 50,
                "prompt": "process it",
                "payload": {"x": 1},
            }
            path = write_wake_event(Path(tmp), event)
            self.assertEqual(path, Path(tmp) / "inbox" / "rime-test-event.json")
            stored = json.loads(path.read_text())
            self.assertEqual(stored["sessionId"], "session-123")
            self.assertFalse(list((Path(tmp) / "inbox").glob("*.tmp*")))

    def test_candidate_generation_suppresses_same_event_clusters(self):
        now = dt("2026-04-27T12:00:00Z")
        event = [{"slug": "elon-musk-of-tweets-april-21-april-28"}]
        first = normalize_market(
            raw_market(
                slug="elon-musk-of-tweets-april-21-april-28-180-199",
                question="Will Elon Musk post 180-199 tweets from April 21 to April 28, 2026?",
                endDate="2026-04-28T16:00:00Z",
                liquidityNum=40_000,
                volumeNum=500_000,
                outcomePrices='["0.12", "0.88"]',
                bestBid=0.11,
                bestAsk=0.13,
                events=event,
            )
        )
        second = normalize_market(
            raw_market(
                slug="elon-musk-of-tweets-april-21-april-28-200-219",
                question="Will Elon Musk post 200-219 tweets from April 21 to April 28, 2026?",
                endDate="2026-04-28T16:00:00Z",
                liquidityNum=37_000,
                volumeNum=314_000,
                outcomePrices='["0.455", "0.545"]',
                bestBid=0.45,
                bestAsk=0.46,
                events=event,
            )
        )
        state = default_state()
        events = generate_events(
            markets=[second, first],
            watches=[],
            state=state,
            now=now,
            session_id="session-123",
            max_candidate_events=5,
            max_events=5,
        )
        self.assertEqual([event["type"] for event in events], ["candidate_found"])
        self.assertEqual(events[0]["payload"]["candidateGroupKey"], "event:elon-musk-of-tweets-april-21-april-28")
        self.assertEqual(
            {market["slug"] for market in events[0]["payload"]["siblingMarkets"]},
            {first.slug, second.slug},
        )

        mark_emitted(state, events, now=now)
        events = generate_events(
            markets=[second],
            watches=[],
            state=state,
            now=now,
            session_id="session-123",
            max_candidate_events=5,
            max_events=5,
        )
        self.assertEqual(events, [])

    def test_generate_events_dedupes_candidates_and_detects_price_moves(self):
        now = dt("2026-04-26T00:00:00Z")
        market = normalize_market(raw_market())
        state = default_state()
        events = generate_events(
            markets=[market],
            watches=[],
            state=state,
            now=now,
            session_id="session-123",
            max_candidate_events=5,
            max_events=5,
        )
        self.assertEqual([e["type"] for e in events], ["candidate_found"])
        self.assertEqual(events[0]["priority"], 45)
        self.assertEqual(events[0]["payload"]["horizon"]["bucket"], "tertiary")
        mark_emitted(state, events, now=now)
        events = generate_events(
            markets=[market],
            watches=[],
            state=state,
            now=now,
            session_id="session-123",
            max_candidate_events=5,
            max_events=5,
        )
        self.assertEqual(events, [])

        with tempfile.TemporaryDirectory() as tmp:
            reasoning = Path(tmp) / "reasoning"
            reasoning.mkdir()
            (reasoning / "example.md").write_text(
                "# Example\n\n"
                "**Polymarket market slug**: will-test-happen-by-may-31\n"
                "**Written**: 2026-04-26T00:00:00+00:00\n"
                "**Prediction**: 55%\n"
                "**Primary venue price at writing**: 42% YES\n"
            )
            watch = extract_polymarket_watches(reasoning)[0]
            state = default_state()
            state["last_prices"][watch.slug] = {"price": 0.32, "observed_at": "2026-04-25T00:00:00Z"}
            moved_market = normalize_market(raw_market(outcomePrices='["0.40", "0.60"]', bestBid=0.39, bestAsk=0.41))
            events = generate_events(
                markets=[moved_market],
                watches=[watch],
                state=state,
                now=now,
                session_id="session-123",
                price_move_threshold=0.05,
                max_candidate_events=0,
                max_events=5,
            )
            self.assertIn("price_moved", [e["type"] for e in events])


if __name__ == "__main__":
    unittest.main()
