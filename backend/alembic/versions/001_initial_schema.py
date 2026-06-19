"""Initial schema — all 5 tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-06-18

Tables:
  - ohlcv_data: Daily OHLCV price data
  - fetch_tracker: yfinance fetch timestamps
  - invest_smart_cache: Gemini analysis cache
  - trades: Trade journal with PnL tracking
  - scan_results: Pre-computed stock evaluations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ohlcv_data ──────────────────────────────────────────────────
    op.create_table(
        "ohlcv_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=True),
        sa.Column("high", sa.Float(), nullable=True),
        sa.Column("low", sa.Float(), nullable=True),
        sa.Column("close", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", "timestamp", name="uq_ohlcv_symbol_ts"),
    )
    op.create_index("idx_ohlcv_symbol", "ohlcv_data", ["symbol"])
    op.create_index("idx_ohlcv_symbol_ts", "ohlcv_data", ["symbol", "timestamp"])

    # ── fetch_tracker ───────────────────────────────────────────────
    op.create_table(
        "fetch_tracker",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("last_fetched_at", sa.DateTime(), nullable=True),
        sa.Column("rows_fetched", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_fetch_tracker_symbol", "fetch_tracker", ["symbol"])

    # ── invest_smart_cache ──────────────────────────────────────────
    op.create_table(
        "invest_smart_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("video_link", sa.String(255), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_link"),
    )
    op.create_index("ix_invest_smart_cache_video_link", "invest_smart_cache", ["video_link"])

    # ── trades ──────────────────────────────────────────────────────
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("stop_loss", sa.Float(), nullable=False),
        sa.Column("target_price", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(10), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("exit_timestamp", sa.DateTime(), nullable=True),
        sa.Column("outcome", sa.String(10), nullable=True),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("pnl_pct", sa.Float(), nullable=True),
        sa.Column("mfe", sa.Float(), nullable=True),
        sa.Column("mae", sa.Float(), nullable=True),
        sa.Column("predicted_probability", sa.Float(), nullable=True),
        sa.Column("predicted_ev", sa.Float(), nullable=True),
        sa.Column("actual_result", sa.Float(), nullable=True),
        sa.Column("regime_at_entry", sa.String(20), nullable=True),
        sa.Column("score_at_entry", sa.Float(), nullable=True),
        sa.Column("position_size", sa.Float(), nullable=True),
        sa.Column("capital_at_entry", sa.Float(), nullable=True),
        sa.Column("slippage_applied", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trades_symbol", "trades", ["symbol"])
    op.create_index("idx_trades_symbol_status", "trades", ["symbol", "status"])
    op.create_index("idx_trades_status", "trades", ["status"])

    # ── scan_results ────────────────────────────────────────────────
    op.create_table(
        "scan_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.Column("decision", sa.String(10), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.Column("ev", sa.Float(), nullable=True),
        sa.Column("entry_price", sa.Float(), nullable=True),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("atr", sa.Float(), nullable=True),
        sa.Column("reward_risk", sa.Float(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol"),
    )
    op.create_index("ix_scan_results_symbol", "scan_results", ["symbol"])
    op.create_index("idx_scan_decision", "scan_results", ["decision"])
    op.create_index("idx_scan_eval_time", "scan_results", ["evaluated_at"])


def downgrade() -> None:
    op.drop_table("scan_results")
    op.drop_table("trades")
    op.drop_table("invest_smart_cache")
    op.drop_table("fetch_tracker")
    op.drop_table("ohlcv_data")
