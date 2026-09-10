"""create initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-10 20:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="USER", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. Create transactions table
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("merchant", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("device_id", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="APPROVED", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_id"), "transactions", ["id"], unique=False)
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_transactions_merchant"), "transactions", ["merchant"], unique=False)
    op.create_index(op.f("ix_transactions_location"), "transactions", ["location"], unique=False)
    op.create_index(op.f("ix_transactions_device_id"), "transactions", ["device_id"], unique=False)
    op.create_index(op.f("ix_transactions_timestamp"), "transactions", ["timestamp"], unique=False)

    # 3. Create risk_assessments table
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("rule_score", sa.Float(), nullable=False),
        sa.Column("ml_score", sa.Float(), nullable=False),
        sa.Column("final_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("reasons_json", sa.Text(), server_default="[]", nullable=False),
        sa.Column("model_version", sa.String(length=50), server_default="v1.0.0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index(op.f("ix_risk_assessments_id"), "risk_assessments", ["id"], unique=False)
    op.create_index(
        op.f("ix_risk_assessments_transaction_id"),
        "risk_assessments",
        ["transaction_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_risk_assessments_risk_level"), "risk_assessments", ["risk_level"], unique=False
    )

    # 4. Create alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("transaction_id", sa.String(length=36), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="OPEN", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_transaction_id"), "alerts", ["transaction_id"], unique=False)
    op.create_index(op.f("ix_alerts_severity"), "alerts", ["severity"], unique=False)
    op.create_index(op.f("ix_alerts_status"), "alerts", ["status"], unique=False)
    op.create_index(op.f("ix_alerts_created_at"), "alerts", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("risk_assessments")
    op.drop_table("transactions")
    op.drop_table("users")
