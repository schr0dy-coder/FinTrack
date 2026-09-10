"""Unit Tests for Deterministic Risk Rules and Boundary Edge Cases."""

from datetime import datetime, timezone

from app.risk_engine.rules import (
    FailedAttemptRule,
    HighAmountRule,
    LocationAnomalyRule,
    NewDeviceRule,
    RapidTransactionsRule,
    TransactionContext,
    evaluate_all_rules,
)


def make_context(
    amount=1000.0,
    merchant="Amazon",
    category="Shopping",
    location="Mumbai, IN",
    device_id="device-iphone",
    known_devices=None,
    known_locations=None,
    recent_transactions=0,
    recent_failed=0,
    hist_count=0,
    hist_mean=1000.0,
) -> TransactionContext:
    """Helper to instantiate test TransactionContext."""
    return TransactionContext(
        amount=amount,
        merchant=merchant,
        category=category,
        location=location,
        device_id=device_id,
        timestamp=datetime.now(timezone.utc),
        user_id=1,
        known_devices=known_devices or set(),
        known_locations=known_locations or set(),
        recent_transactions_in_window=recent_transactions,
        recent_failed_attempts=recent_failed,
        historical_transaction_count=hist_count,
        historical_mean_amount=hist_mean,
    )


def test_high_amount_rule_exact_boundaries():
    rule = HighAmountRule(threshold=50000.0, score=25.0)

    # 1 unit below threshold
    ctx_below = make_context(amount=49999.0)
    res_below = rule.evaluate(ctx_below)
    assert res_below.triggered is False
    assert res_below.score == 0.0

    # Exactly at threshold
    ctx_exact = make_context(amount=50000.0)
    res_exact = rule.evaluate(ctx_exact)
    assert res_exact.triggered is False
    assert res_exact.score == 0.0

    # 1 unit above threshold
    ctx_above = make_context(amount=50001.0)
    res_above = rule.evaluate(ctx_above)
    assert res_above.triggered is True
    assert res_above.score == 25.0
    assert res_above.code == "HIGH_AMOUNT"


def test_high_amount_rule_zero_and_negative():
    rule = HighAmountRule(threshold=50000.0, score=25.0)

    # Zero amount
    res_zero = rule.evaluate(make_context(amount=0.0))
    assert res_zero.triggered is False

    # Negative amount
    res_neg = rule.evaluate(make_context(amount=-100.0))
    assert res_neg.triggered is False


def test_rapid_transactions_rule_boundaries():
    rule = RapidTransactionsRule(count_threshold=5, score=20.0)

    # 1 count below threshold (4 txns)
    assert rule.evaluate(make_context(recent_transactions=4)).triggered is False

    # Exactly at threshold (5 txns)
    res_exact = rule.evaluate(make_context(recent_transactions=5))
    assert res_exact.triggered is True
    assert res_exact.score == 20.0
    assert res_exact.code == "RAPID_TRANSACTIONS"

    # Well above threshold (20 txns)
    assert rule.evaluate(make_context(recent_transactions=20)).triggered is True


def test_new_device_rule_scenarios():
    rule = NewDeviceRule(score=15.0)

    # User with 0 historical transactions (First transaction)
    ctx_first = make_context(device_id="device-new", known_devices=set(), hist_count=0)
    assert rule.evaluate(ctx_first).triggered is False

    # User with history using known device
    ctx_known = make_context(device_id="device-known", known_devices={"device-known"}, hist_count=5)
    assert rule.evaluate(ctx_known).triggered is False

    # User with history using new device
    ctx_unrec = make_context(
        device_id="device-unknown", known_devices={"device-known"}, hist_count=5
    )
    res = rule.evaluate(ctx_unrec)
    assert res.triggered is True
    assert res.score == 15.0
    assert res.code == "NEW_DEVICE"


def test_location_anomaly_rule_scenarios():
    rule = LocationAnomalyRule(score=20.0)

    # First transaction -> no anomaly
    ctx_first = make_context(location="London, UK", known_locations=set(), hist_count=0)
    assert rule.evaluate(ctx_first).triggered is False

    # Known location
    ctx_known = make_context(
        location="Mumbai, IN", known_locations={"Mumbai, IN", "Pune, IN"}, hist_count=10
    )
    assert rule.evaluate(ctx_known).triggered is False

    # Location not in history
    ctx_anom = make_context(
        location="Dubai, AE", known_locations={"Mumbai, IN", "Pune, IN"}, hist_count=10
    )
    res = rule.evaluate(ctx_anom)
    assert res.triggered is True
    assert res.score == 20.0
    assert res.code == "LOCATION_ANOMALY"


def test_failed_attempt_rule_boundaries():
    rule = FailedAttemptRule(count_threshold=3, score=10.0)

    # 2 attempts (1 below threshold)
    assert rule.evaluate(make_context(recent_failed=2)).triggered is False

    # 3 attempts (exactly at threshold)
    res_exact = rule.evaluate(make_context(recent_failed=3))
    assert res_exact.triggered is True
    assert res_exact.score == 10.0
    assert res_exact.code == "FAILED_ATTEMPT_PATTERN"

    # 0 attempts
    assert rule.evaluate(make_context(recent_failed=0)).triggered is False


def test_evaluate_all_rules_execution():
    ctx = make_context(
        amount=95000.0,
        device_id="device-emulator-404",
        location="London, UK",
        known_devices={"device-mobile-1"},
        known_locations={"Mumbai, IN"},
        recent_transactions=6,
        recent_failed=4,
        hist_count=10,
    )
    results = evaluate_all_rules(ctx)

    triggered_codes = [r.code for r in results if r.triggered]
    assert set(triggered_codes) == {
        "HIGH_AMOUNT",
        "RAPID_TRANSACTIONS",
        "NEW_DEVICE",
        "LOCATION_ANOMALY",
        "FAILED_ATTEMPT_PATTERN",
    }
