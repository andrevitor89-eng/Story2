"""add books.age_band

Revision ID: 002_age_band
Revises: 001_initial
Create Date: 2026-07-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_age_band"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("age_band", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "age_band")
