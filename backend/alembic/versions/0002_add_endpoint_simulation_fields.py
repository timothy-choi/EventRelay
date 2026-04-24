"""add endpoint simulation fields

Revision ID: 0002_endpoint_sim
Revises: 0001_core
Create Date: 2026-04-23 00:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_endpoint_sim"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "endpoints",
        sa.Column(
            "simulation_latency_ms",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "simulation_failure_rate",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "endpoints",
        sa.Column(
            "simulation_timeout_rate",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("endpoints", "simulation_timeout_rate")
    op.drop_column("endpoints", "simulation_failure_rate")
    op.drop_column("endpoints", "simulation_latency_ms")
