"""create entity_mention_provenance table

Creates entity_mention_provenance table to store canonical resolved
mention spans linking to entities.id and evidence.id.

Revision ID: e8f3b2c1d4a5
Revises: c7d2e8f1a345
Create Date: 2026-09-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8f3b2c1d4a5"
down_revision: Union[str, Sequence[str], None] = "c7d2e8f1a345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entity_mention_provenance",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("matched_text", sa.String(length=500), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=True),
        sa.Column("end_char", sa.Integer(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("extraction_confidence", sa.Float(), nullable=False),
        sa.Column("final_confidence", sa.Float(), nullable=False),
        sa.Column("low_ocr_confidence", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("extraction_method", sa.String(length=100), nullable=False),
        sa.Column("extractor_version", sa.String(length=50), nullable=False),
        # ICDAR-specific provenance columns (nullable for generic evidence)
        sa.Column("source_index", sa.Integer(), nullable=True),
        sa.Column("reconstructed_order", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("bbox_x1", sa.Float(), nullable=True),
        sa.Column("bbox_y1", sa.Float(), nullable=True),
        sa.Column("bbox_x2", sa.Float(), nullable=True),
        sa.Column("bbox_y2", sa.Float(), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id", "source_index", "start_char", "end_char", name="uq_emp_mention"),
    )
    op.create_index("ix_emp_entity_id", "entity_mention_provenance", ["entity_id"])
    op.create_index("ix_emp_evidence_id", "entity_mention_provenance", ["evidence_id"])
    op.create_index("ix_emp_source_index", "entity_mention_provenance", ["source_index"])


def downgrade() -> None:
    op.drop_index("ix_emp_source_index", table_name="entity_mention_provenance")
    op.drop_index("ix_emp_evidence_id", table_name="entity_mention_provenance")
    op.drop_index("ix_emp_entity_id", table_name="entity_mention_provenance")
    op.drop_table("entity_mention_provenance")
