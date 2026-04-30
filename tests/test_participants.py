import unittest
from datetime import datetime, timezone

from automation.participants import (
    MarketBook,
    copy_entry_from_book,
    current_aligned_clv_pp,
    domain_bucket,
    horizon_bucket,
    normalize_polymarket_trade,
    generate_participant_events,
    mark_participant_events_emitted,
    participant_observation_key,
    participant_signal_filter_reason,
    participant_signal_id,
    participant_state_default,
    score_backfilled_wallet_trades,
    score_participant,
    shrinkage_weight,
)


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ParticipantTests(unittest.TestCase):
    def sample_row(self, **overrides):
        row = {
            "proxyWallet": "0xabc",
            "side": "BUY",
            "asset": "123",
            "conditionId": "0xcond",
            "size": 50,
            "price": 0.42,
            "timestamp": 1777515902,
            "title": "Will Anthropic provide Mythos to the US government by April 30?",
            "slug": "will-anthropic-provide-mythos-to-the-us-government-by-april-30-2026",
            "eventSlug": "will-anthropic-provide-mythos-to-the-us-government-by-june-30",
            "outcome": "Yes",
            "outcomeIndex": 0,
            "name": "Name",
            "pseudonym": "Sharp-Fox",
            "transactionHash": "0xtx",
        }
        row.update(overrides)
        return row

    def test_normalize_polymarket_trade(self):
        trade = normalize_polymarket_trade(self.sample_row())
        self.assertEqual(trade.venue, "Polymarket")
        self.assertEqual(trade.wallet, "0xabc")
        self.assertEqual(trade.side, "BUY")
        self.assertEqual(trade.outcome, "Yes")
        self.assertAlmostEqual(trade.notional, 21.0)
        self.assertEqual(trade.timestamp, datetime.fromtimestamp(1777515902, tz=timezone.utc))
        self.assertEqual(trade.trader_label, "Sharp-Fox")

    def test_domain_bucket_heuristics(self):
        self.assertEqual(domain_bucket("Bitcoin Up or Down - April 29", "btc-updown-5m"), "crypto")
        self.assertEqual(domain_bucket("Will Amazon beat quarterly earnings?", "amzn-quarterly-earnings"), "earnings")
        self.assertEqual(domain_bucket("Rockets vs. Lakers", "nba-hou-lal"), "sports")
        self.assertEqual(domain_bucket('Will Powell say "Pandemic"?', "fomc-powell-pandemic"), "macro")
        self.assertEqual(domain_bucket("Will Anthropic provide Mythos to the US government?", "anthropic-mythos"), "source")
        self.assertEqual(domain_bucket("Will Clavicular cry on stream?", "clavicular-cry-stream"), "culture")
        self.assertEqual(domain_bucket("Will the SAVE Act become law?", "save-act"), "politics")

    def test_horizon_bucket(self):
        now = dt("2026-04-30T00:00:00Z")
        self.assertEqual(horizon_bucket(dt("2026-04-30T00:30:00Z"), now), "micro")
        self.assertEqual(horizon_bucket(dt("2026-04-30T12:00:00Z"), now), "intraday")
        self.assertEqual(horizon_bucket(dt("2026-05-03T00:00:00Z"), now), "1-7d")
        self.assertEqual(horizon_bucket(dt("2026-05-15T00:00:00Z"), now), "8-21d")
        self.assertEqual(horizon_bucket(dt("2026-06-01T00:00:00Z"), now), "22-45d")
        self.assertEqual(horizon_bucket(dt("2026-07-01T00:00:00Z"), now), "long")

    def test_shrinkage_score(self):
        self.assertAlmostEqual(shrinkage_weight(25, prior_n=25), 0.5)
        score = score_participant(
            wallet="0xabc",
            domain="source",
            horizon="1-7d",
            sample_size=25,
            mean_clv_pp=4.0,
            copy_after_delay_mean_clv_pp=2.0,
            realized_roi=0.1,
            prior_n=25,
        )
        self.assertAlmostEqual(score.shrinkage_weight, 0.5)
        self.assertAlmostEqual(score.score, 1.0)

    def test_copy_entry_from_yes_and_no_books(self):
        yes_trade = normalize_polymarket_trade(self.sample_row(outcome="Yes", outcomeIndex=0, side="BUY", price=0.40))
        book = MarketBook(yes_bid=0.41, yes_ask=0.45, yes_price=0.43)
        entry = copy_entry_from_book(yes_trade, book)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.side, "BUY_YES")
        self.assertAlmostEqual(entry.executable_price, 0.45)
        self.assertAlmostEqual(entry.spread_pp, 4.0)

        no_trade = normalize_polymarket_trade(self.sample_row(outcome="No", outcomeIndex=1, side="BUY", price=0.60))
        no_entry = copy_entry_from_book(no_trade, book)
        self.assertIsNotNone(no_entry)
        self.assertEqual(no_entry.side, "BUY_NO")
        self.assertAlmostEqual(no_entry.executable_price, 1 - 0.41)
        self.assertAlmostEqual(no_entry.bid, 1 - 0.45)

        sell_yes = normalize_polymarket_trade(self.sample_row(outcome="Yes", outcomeIndex=0, side="SELL", price=0.40))
        sell_yes_entry = copy_entry_from_book(sell_yes, book)
        self.assertEqual(sell_yes_entry.side, "BUY_NO")
        self.assertAlmostEqual(sell_yes_entry.reference_price, 0.60)

    def test_current_aligned_clv_pp_handles_directional_exposure(self):
        buy_yes = normalize_polymarket_trade(self.sample_row(outcome="Yes", outcomeIndex=0, side="BUY", price=0.42))
        self.assertAlmostEqual(current_aligned_clv_pp(buy_yes, 0.47), 5.0)

        buy_no = normalize_polymarket_trade(self.sample_row(outcome="No", outcomeIndex=1, side="BUY", price=0.42))
        self.assertAlmostEqual(current_aligned_clv_pp(buy_no, 0.47), 11.0)

        sell_yes = normalize_polymarket_trade(self.sample_row(outcome="Yes", outcomeIndex=0, side="SELL", price=0.42))
        self.assertAlmostEqual(current_aligned_clv_pp(sell_yes, 0.47), -5.0)

    def test_score_backfilled_wallet_trades_outputs_score_fixture_rows(self):
        trades = [
            normalize_polymarket_trade(self.sample_row(transactionHash="0x1", price=0.42, size=100, timestamp=1777512302)),
            normalize_polymarket_trade(self.sample_row(transactionHash="0x2", price=0.44, size=50, timestamp=1777515902)),
        ]
        rows = score_backfilled_wallet_trades(
            trades=trades,
            books_by_slug={trades[0].market_slug: MarketBook(yes_bid=0.46, yes_ask=0.48, yes_price=0.47)},
            end_times_by_slug={trades[0].market_slug: dt("2026-05-01T00:00:00Z")},
            min_samples=2,
            prior_n=2,
            copy_delay_penalty_pp=1.0,
        )
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["wallet"], "0xabc")
        self.assertEqual(row["domain"], "source")
        self.assertEqual(row["horizonBucket"], "intraday")
        self.assertEqual(row["sampleSize"], 2)
        self.assertAlmostEqual(row["meanClvPp"], 4.0)
        self.assertAlmostEqual(row["copyAfterDelayMeanClvPp"], 3.0)
        self.assertAlmostEqual(row["shrinkageWeight"], 0.5)
        self.assertAlmostEqual(row["score"], 1.5)
        self.assertAlmostEqual(row["totalNotionalUsd"], 64.0)
        self.assertEqual(row["scoreSource"], "current-price-backfill")

    def test_signal_filter_quality_gates(self):
        trade = normalize_polymarket_trade(self.sample_row())
        book = MarketBook(yes_bid=0.40, yes_ask=0.44)
        ok, reason = participant_signal_filter_reason(trade, book=book)
        self.assertTrue(ok, reason)

        tiny = normalize_polymarket_trade(self.sample_row(size=2, price=0.20))
        ok, reason = participant_signal_filter_reason(tiny)
        self.assertFalse(ok)
        self.assertIn("notional", reason)

        micro = normalize_polymarket_trade(self.sample_row(title="Bitcoin Up or Down - April 29, 10:20PM-10:25PM ET", slug="btc-updown-5m-1777515600"))
        ok, reason = participant_signal_filter_reason(micro)
        self.assertFalse(ok)
        self.assertIn("micro", reason)

        wide_book = MarketBook(yes_bid=0.20, yes_ask=0.45)
        ok, reason = participant_signal_filter_reason(trade, book=wide_book, max_spread_pp=10.0)
        self.assertFalse(ok)
        self.assertIn("spread", reason)

        weak_score = score_participant(
            wallet="0xabc",
            domain="source",
            horizon="1-7d",
            sample_size=5,
            mean_clv_pp=1.0,
            copy_after_delay_mean_clv_pp=1.0,
            prior_n=25,
        )
        ok, reason = participant_signal_filter_reason(trade, score=weak_score, min_score_pp=1.0)
        self.assertFalse(ok)
        self.assertIn("score", reason)

    def test_participant_signal_id_is_stable(self):
        trade = normalize_polymarket_trade(self.sample_row(transactionHash="0xABCDEF"))
        self.assertEqual(
            participant_signal_id(trade),
            "participant:0xabc:will-anthropic-provide-mythos-to-the-us-government-by-april-30-2026:0xabcdef",
        )

    def test_generate_participant_events_dedupes_and_marks(self):
        now = dt("2026-04-30T00:00:00Z")
        trade = normalize_polymarket_trade(self.sample_row(transactionHash="0xABCDEF"))
        state = participant_state_default()
        score = score_participant(
            wallet="0xabc",
            domain="source",
            horizon="1-7d",
            sample_size=100,
            mean_clv_pp=4.0,
            copy_after_delay_mean_clv_pp=3.0,
            prior_n=25,
        )
        events = generate_participant_events(
            trades=[trade],
            state=state,
            now=now,
            session_id="session-123",
            books_by_slug={trade.market_slug: MarketBook(yes_bid=0.40, yes_ask=0.44)},
            end_times_by_slug={trade.market_slug: dt("2026-05-01T00:00:00Z")},
            scores_by_wallet_domain={("0xabc", "source", "1-7d"): score},
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "participant_signal_candidate")
        self.assertEqual(events[0]["source"], "rime-forecasts/polymarket-participant-daemon")
        self.assertEqual(events[0]["payload"]["copyEntry"]["side"], "BUY_YES")
        self.assertEqual(events[0]["payload"]["participantScore"]["score"], score.score)

        mark_participant_events_emitted(state, events, now=now)
        repeated = generate_participant_events(
            trades=[trade],
            state=state,
            now=now,
            session_id="session-123",
            books_by_slug={trade.market_slug: MarketBook(yes_bid=0.40, yes_ask=0.44)},
            end_times_by_slug={trade.market_slug: dt("2026-05-01T00:00:00Z")},
            scores_by_wallet_domain={("0xabc", "source", "1-7d"): score},
        )
        self.assertEqual(repeated, [])

    def test_generate_participant_events_cold_start_requires_opt_in(self):
        now = dt("2026-04-30T00:00:00Z")
        trade = normalize_polymarket_trade(self.sample_row(transactionHash="0xCOLD"))
        state = participant_state_default()
        suppressed = generate_participant_events(
            trades=[trade],
            state=state,
            now=now,
            session_id="session-123",
            books_by_slug={trade.market_slug: MarketBook(yes_bid=0.40, yes_ask=0.44)},
        )
        self.assertEqual(suppressed, [])
        observation_key = participant_observation_key("0xabc", "source", "long")
        observation = state["wallet_observations"][observation_key]
        self.assertEqual(observation["count"], 1)
        self.assertEqual(observation["buyCount"], 1)
        self.assertAlmostEqual(observation["totalNotionalUsd"], 21.0)
        self.assertEqual(observation["lastTradeAt"], "2026-04-30T02:25:02Z")
        self.assertEqual(state["processed_transactions"]["0xCOLD"]["reason"], "unscored cold-start")

        state = participant_state_default()
        emitted = generate_participant_events(
            trades=[trade],
            state=state,
            now=now,
            session_id="session-123",
            books_by_slug={trade.market_slug: MarketBook(yes_bid=0.40, yes_ask=0.44)},
            emit_unscored=True,
        )
        self.assertEqual(len(emitted), 1)
        self.assertIsNone(emitted[0]["payload"]["participantScore"])

    def test_wallet_observations_aggregate_by_domain_horizon(self):
        now = dt("2026-04-30T00:00:00Z")
        newer = normalize_polymarket_trade(self.sample_row(transactionHash="0xNEW", timestamp=1777515902, size=50, price=0.42))
        older = normalize_polymarket_trade(self.sample_row(transactionHash="0xOLD", timestamp=1777512302, side="SELL", size=10, price=0.30))
        state = participant_state_default()
        events = generate_participant_events(
            trades=[older, newer],
            state=state,
            now=now,
            session_id="session-123",
            end_times_by_slug={newer.market_slug: dt("2026-05-01T00:00:00Z")},
        )
        self.assertEqual(events, [])
        observation = state["wallet_observations"][participant_observation_key("0xabc", "source", "1-7d")]
        self.assertEqual(observation["count"], 2)
        self.assertEqual(observation["buyCount"], 1)
        self.assertEqual(observation["sellCount"], 1)
        self.assertAlmostEqual(observation["totalNotionalUsd"], 24.0)
        self.assertEqual(observation["firstTradeAt"], "2026-04-30T01:25:02Z")
        self.assertEqual(observation["lastTradeAt"], "2026-04-30T02:25:02Z")
        self.assertEqual(observation["lastMarketSlug"], newer.market_slug)


if __name__ == "__main__":
    unittest.main()
