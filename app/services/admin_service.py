"""Admin and Analytics Service."""

import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.ml.model_registry import get_model_registry
from app.ml.train import train_isolation_forest
from app.models.alert import Alert
from app.models.risk import RiskAssessment
from app.models.transaction import Transaction
from app.schemas.admin import ModelRetrainResponse, ModelStatusResponse, SystemStatsResponse


class AdminService:
    """Provides platform aggregations and administrative model actions."""

    def __init__(self, db: Session):
        self.db = db

    def get_system_statistics(self) -> SystemStatsResponse:
        """Compute aggregate platform KPIs."""
        # 1. Transactions count and volume
        tx_stats = self.db.execute(
            select(
                func.count(Transaction.id).label("total_count"),
                func.coalesce(func.sum(Transaction.amount), 0.0).label("total_volume"),
            )
        ).one()
        total_tx = tx_stats.total_count or 0
        total_vol = float(tx_stats.total_volume or 0.0)

        # 2. Risk distribution
        risk_rows = self.db.execute(
            select(RiskAssessment.risk_level, func.count(RiskAssessment.id)).group_by(
                RiskAssessment.risk_level
            )
        ).all()
        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for level, cnt in risk_rows:
            if level in risk_dist:
                risk_dist[level] = cnt

        suspicious_count = risk_dist["HIGH"] + risk_dist["CRITICAL"]
        anomaly_rate = round((suspicious_count / total_tx * 100), 2) if total_tx > 0 else 0.0

        # 3. Alert stats
        alert_status_rows = self.db.execute(
            select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        ).all()
        open_alerts = 0
        resolved_alerts = 0
        for status_val, cnt in alert_status_rows:
            if status_val == "OPEN":
                open_alerts = cnt
            elif status_val == "RESOLVED":
                resolved_alerts = cnt

        # 4. Severity distribution
        severity_rows = self.db.execute(
            select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
        ).all()
        severity_dist = {"HIGH": 0, "CRITICAL": 0}
        for sev, cnt in severity_rows:
            if sev in severity_dist:
                severity_dist[sev] = cnt

        # 5. Top suspicious merchants
        top_merchants_stmt = (
            select(Transaction.merchant, func.count(Transaction.id).label("cnt"))
            .join(Transaction.risk_assessment)
            .where(RiskAssessment.risk_level.in_(["HIGH", "CRITICAL"]))
            .group_by(Transaction.merchant)
            .order_by(desc("cnt"))
            .limit(5)
        )
        top_merchants = [
            {"merchant": m, "count": cnt} for m, cnt in self.db.execute(top_merchants_stmt).all()
        ]

        # 6. Top suspicious locations
        top_locs_stmt = (
            select(Transaction.location, func.count(Transaction.id).label("cnt"))
            .join(Transaction.risk_assessment)
            .where(RiskAssessment.risk_level.in_(["HIGH", "CRITICAL"]))
            .group_by(Transaction.location)
            .order_by(desc("cnt"))
            .limit(5)
        )
        top_locations = [
            {"location": loc, "count": cnt} for loc, cnt in self.db.execute(top_locs_stmt).all()
        ]

        return SystemStatsResponse(
            total_transactions=total_tx,
            total_volume=round(total_vol, 2),
            suspicious_transactions=suspicious_count,
            anomaly_rate=anomaly_rate,
            open_alerts=open_alerts,
            resolved_alerts=resolved_alerts,
            risk_distribution=risk_dist,
            severity_distribution=severity_dist,
            top_suspicious_merchants=top_merchants,
            top_suspicious_locations=top_locations,
        )

    def get_model_status(self) -> ModelStatusResponse:
        """Inspect ML model registry state."""
        registry = get_model_registry()
        is_loaded = registry.is_loaded()
        metadata = registry.get_metadata() or {}

        features = metadata.get(
            "features",
            [
                "amount",
                "hour_of_day",
                "day_of_week",
                "user_tx_count_24h",
                "amount_deviation",
                "is_new_device",
                "is_new_location",
                "failed_attempts_count",
            ],
        )

        return ModelStatusResponse(
            model_loaded=is_loaded,
            model_version=registry.get_model_version(),
            model_type=metadata.get("model_type", "IsolationForest"),
            features=features,
            trained_at=metadata.get("trained_at"),
            training_sample_count=metadata.get("training_sample_count"),
            metrics={
                "training_anomaly_rate_pct": metadata.get("training_anomaly_rate_pct"),
                "contamination": metadata.get("contamination", 0.05),
                "n_estimators": metadata.get("n_estimators", 150),
            },
        )

    def retrain_model_from_database(self) -> ModelRetrainResponse:
        """Train and reload model artifact from database transactions."""
        # Query existing transactions
        transactions = list(
            self.db.scalars(select(Transaction).order_by(Transaction.timestamp)).all()
        )

        if len(transactions) < 20:
            # Not enough transactions in DB to train a robust model
            from scripts.generate_dataset import generate_synthetic_transactions

            df = generate_synthetic_transactions(num_transactions=1000)
            logger.info(
                "Using 1,000 synthetic records to retrain ML model due to sparse DB records."
            )
        else:
            data = [
                {
                    "amount": t.amount,
                    "timestamp": t.timestamp,
                    "merchant": t.merchant,
                    "location": t.location,
                    "device_id": t.device_id,
                }
                for t in transactions
            ]
            df = pd.DataFrame(data)

        meta = train_isolation_forest(df=df, model_version="v1.1.0-retrained")
        get_model_registry().reload()

        return ModelRetrainResponse(
            message="Model successfully retrained and reloaded into memory.",
            status="SUCCESS",
            model_version=meta["model_version"],
            sample_count=meta["training_sample_count"],
        )
