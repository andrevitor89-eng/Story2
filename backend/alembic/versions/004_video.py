"""add video fields, job kind, and video asset kinds

Revision ID: 004_video
Revises: 003_storage_objects
Create Date: 2026-07-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004_video"
down_revision = "003_storage_objects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("video_url", sa.Text(), nullable=True))
    op.add_column("books", sa.Column("narrated_video_url", sa.Text(), nullable=True))

    job_kind = postgresql.ENUM(
        "GENERATE", "VIDEO", "NARRATED_VIDEO", name="jobkind", create_type=True
    )
    job_kind.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "jobs",
        sa.Column("kind", job_kind, nullable=False, server_default="GENERATE"),
    )
    op.create_index("ix_jobs_kind", "jobs", ["kind"])

    # Extende assetkind (Postgres). Em SQLite/dev o Enum do SQLAlchemy aceita novos valores.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE assetkind ADD VALUE IF NOT EXISTS 'video'")
            op.execute("ALTER TYPE assetkind ADD VALUE IF NOT EXISTS 'storyboard'")
            op.execute("ALTER TYPE assetkind ADD VALUE IF NOT EXISTS 'narrated_video'")
            op.execute("ALTER TYPE assetkind ADD VALUE IF NOT EXISTS 'audio'")


def downgrade() -> None:
    op.drop_index("ix_jobs_kind", table_name="jobs")
    op.drop_column("jobs", "kind")
    op.execute("DROP TYPE IF EXISTS jobkind")
    op.drop_column("books", "narrated_video_url")
    op.drop_column("books", "video_url")
