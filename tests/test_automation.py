import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from automation.clv import due_clv_checkpoints
from automation.config import require_session_id
from automation.daemon_core import default_state, generate_events, mark_emitted
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
        "volumeNum": 12000,
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.42", "0.58"]',
        "bestBid": 0.41,
        "bestAsk": 0.43,
        "lastTradePrice": 0.42,
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
        self.assertIn("liquidity", reason)

        non_binary = normalize_market(raw_market(outcomes='["A", "B", "C"]', outcomePrices='["0.2", "0.3", "0.5"]'))
        ok, reason = candidate_filter_reason(non_binary, now=now)
        self.assertFalse(ok)
        self.assertIn("binary", reason)

        too_soon = normalize_market(raw_market(endDate="2026-05-01T00:00:00Z"))
        ok, reason = candidate_filter_reason(too_soon, now=now)
        self.assertFalse(ok)
        self.assertIn("window", reason)

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
