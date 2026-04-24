"""add test webhook tables

Revision ID: 0003_test_webhooks
Revises: 0002_endpoint_sim
Create Date: 2026-04-24 00:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_test_webhooks"
down_revision = "0002_endpoint_sim"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_webhook_receivers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "test_webhook_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("receiver_id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(length=16), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=True),
        sa.Column("raw_body", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["receiver_id"], ["test_webhook_receivers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("test_webhook_requests")
    op.drop_table("test_webhook_receivers")
