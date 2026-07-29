"""add storage_objects for db-backed assets

Revision ID: 003_storage_objects
Revises: 002_age_band
Create Date: 2026-07-29
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "003_storage_objects"
down_revision = "002_age_band"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storage_objects",
        sa.Column("key", sa.String(512), primary_key=True),
        sa.Column("mime_type", sa.String(100), nullable=False, server_default="application/octet-stream"),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("storage_objects")
