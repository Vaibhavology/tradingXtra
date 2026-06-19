"""Add market_brief_cache table

Revision ID: 002_market_brief_cache
Revises: 001_initial
Create Date: 2026-06-19

Stores daily market brief JSON for instant dashboard loads.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_market_brief_cache"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_brief_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cache_date", sa.String(10), nullable=False),
        sa.Column("brief_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_date"),
    )
    op.create_index(
        "ix_market_brief_cache_date", "market_brief_cache", ["cache_date"]
    )


def downgrade() -> None:
    op.drop_table("market_brief_cache")
