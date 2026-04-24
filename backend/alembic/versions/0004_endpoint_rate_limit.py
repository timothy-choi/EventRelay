"""add endpoint rate limit field

Revision ID: 0004_endpoint_rate
Revises: 0003_test_webhooks
Create Date: 2026-04-24 05:20:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_endpoint_rate"
down_revision = "0003_test_webhooks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [column["name"] for column in inspector.get_columns("endpoints")]

    if "max_requests_per_second" not in columns:
        op.add_column(
            "endpoints",
            sa.Column(
                "max_requests_per_second",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [column["name"] for column in inspector.get_columns("endpoints")]

    if "max_requests_per_second" in columns:
        op.drop_column("endpoints", "max_requests_per_second")
