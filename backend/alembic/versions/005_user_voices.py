"""user_voices table + jobs.payload

Revision ID: 005_user_voices
Revises: 004_video
Create Date: 2026-07-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "005_user_voices"
down_revision = "004_video"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_voices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("elevenlabs_voice_id", sa.String(64), nullable=False),
        sa.Column("sample_storage_key", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False, server_default="audio/mpeg"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_voices_user_id", "user_voices", ["user_id"])
    op.add_column("jobs", sa.Column("payload", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "payload")
    op.drop_index("ix_user_voices_user_id", table_name="user_voices")
    op.drop_table("user_voices")
