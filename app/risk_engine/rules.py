"""Deterministic Risk Rules Engine."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from app.core.config import settings


@dataclass
class TransactionContext:
    """Encapsulates context needed to evaluate risk rules."""

    amount: float
    merchant: str
    category: Optional[str]
    location: str
    device_id: str
    timestamp: datetime
    user_id: int
    # Historical context
    known_devices: Set[str] = field(default_factory=set)
    known_locations: Set[str] = field(default_factory=set)
    recent_transactions_in_window: int = 0
    recent_failed_attempts: int = 0
    historical_transaction_count: int = 0
    historical_mean_amount: float = 0.0


@dataclass
class RuleResult:
    """Output produced by evaluating a single rule."""

    code: str
    triggered: bool
    score: float
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


class BaseRiskRule(ABC):
    """Abstract base class for all deterministic risk rules."""

    @abstractmethod
    def evaluate(self, ctx: TransactionContext) -> RuleResult:
        """Evaluate rule against transaction context."""
        pass


class HighAmountRule(BaseRiskRule):
    """Rule 1: Flags unusually large transaction amounts exceeding configured threshold."""

    def __init__(self, threshold: Optional[float] = None, score: float = 25.0):
        self.threshold = threshold if threshold is not None else settings.HIGH_AMOUNT_THRESHOLD
        self.score = score

    def evaluate(self, ctx: TransactionContext) -> RuleResult:
        if ctx.amount > self.threshold:
            return RuleResult(
                code="HIGH_AMOUNT",
                triggered=True,
                score=self.score,
                reason=f"Transaction amount (₹{ctx.amount:,.2f}) exceeds high-value threshold of ₹{self.threshold:,.2f}",
                details={"amount": ctx.amount, "threshold": self.threshold},
            )
        return RuleResult(
            code="HIGH_AMOUNT",
            triggered=False,
            score=0.0,
            reason="Transaction amount is within normal threshold",
            details={"amount": ctx.amount, "threshold": self.threshold},
        )


class RapidTransactionsRule(BaseRiskRule):
    """Rule 2: Flags high-velocity transactions in a short time window (velocity abuse)."""

    def __init__(self, count_threshold: Optional[int] = None, score: float = 20.0):
        self.count_threshold = (
            count_threshold if count_threshold is not None else settings.RAPID_TRANSACTION_COUNT
        )
        self.score = score

    def evaluate(self, ctx: TransactionContext) -> RuleResult:
        # If the user already made >= count_threshold transactions in the window
        if ctx.recent_transactions_in_window >= self.count_threshold:
            return RuleResult(
                code="RAPID_TRANSACTIONS",
                triggered=True,
                score=self.score,
                reason=(
                    f"Rapid activity detected: {ctx.recent_transactions_in_window} transactions "
                    f"in the last {settings.RAPID_TRANSACTION_WINDOW_SECONDS}s "
                    f"(threshold: {self.count_threshold})"
                ),
                details={
                    "recent_count": ctx.recent_transactions_in_window,
                    "threshold": self.count_threshold,
                    "window_seconds": settings.RAPID_TRANSACTION_WINDOW_SECONDS,
                },
            )
        return RuleResult(
            code="RAPID_TRANSACTIONS",
            triggered=False,
            score=0.0,
            reason="Transaction velocity is within normal range",
            details={"recent_count": ctx.recent_transactions_in_window},
        )


class NewDeviceRule(BaseRiskRule):
    """Rule 3: Flags transactions originating from an unrecognized device."""

    def __init__(self, score: float = 15.0):
        self.score = score

    def evaluate(self, ctx: TransactionContext) -> RuleResult:
        # If user has a transaction history but this device is new
        if ctx.historical_transaction_count > 0 and ctx.device_id not in ctx.known_devices:
            return RuleResult(
                code="NEW_DEVICE",
                triggered=True,
                score=self.score,
                reason=f"Transaction initiated from an unrecognized device: '{ctx.device_id}'",
                details={
                    "device_id": ctx.device_id,
                    "known_devices_count": len(ctx.known_devices),
                },
            )
        return RuleResult(
            code="NEW_DEVICE",
            triggered=False,
            score=0.0,
            reason="Device is recognized or first user transaction",
            details={"device_id": ctx.device_id},
        )


class LocationAnomalyRule(BaseRiskRule):
    """Rule 4: Flags transactions initiated from a location not in the user's historical profile."""

    def __init__(self, score: float = 20.0):
        self.score = score

    def evaluate(self, ctx: TransactionContext) -> RuleResult:
        if ctx.historical_transaction_count > 0 and ctx.location not in ctx.known_locations:
            return RuleResult(
                code="LOCATION_ANOMALY",
                triggered=True,
                score=self.score,
                reason=f"Transaction location '{ctx.location}' is unusual based on user history",
                details={
                    "location": ctx.location,
                    "known_locations": list(ctx.known_locations)[:5],
                },
            )
        return RuleResult(
            code="LOCATION_ANOMALY",
            triggered=False,
            score=0.0,
            reason="Location is consistent with user history",
            details={"location": ctx.location},
        )


class FailedAttemptRule(BaseRiskRule):
    """Rule 5: Flags recent failed/rejected transactions or credential stuffing attempts."""

    def __init__(self, count_threshold: Optional[int] = None, score: float = 10.0):
        self.count_threshold = (
            count_threshold if count_threshold is not None else settings.FAILED_ATTEMPT_COUNT
        )
        self.score = score

    def evaluate(self, ctx: TransactionContext) -> RuleResult:
        if ctx.recent_failed_attempts >= self.count_threshold:
            return RuleResult(
                code="FAILED_ATTEMPT_PATTERN",
                triggered=True,
                score=self.score,
                reason=f"Multiple recent failed transactions detected ({ctx.recent_failed_attempts} attempts)",
                details={
                    "recent_failed_attempts": ctx.recent_failed_attempts,
                    "threshold": self.count_threshold,
                },
            )
        return RuleResult(
            code="FAILED_ATTEMPT_PATTERN",
            triggered=False,
            score=0.0,
            reason="No suspicious failed attempt pattern detected",
            details={"recent_failed_attempts": ctx.recent_failed_attempts},
        )


def evaluate_all_rules(
    ctx: TransactionContext,
    custom_rules: Optional[List[BaseRiskRule]] = None,
) -> List[RuleResult]:
    """Execute all configured deterministic risk rules against transaction context."""
    rules = custom_rules or [
        HighAmountRule(),
        RapidTransactionsRule(),
        NewDeviceRule(),
        LocationAnomalyRule(),
        FailedAttemptRule(),
    ]
    return [rule.evaluate(ctx) for rule in rules]
