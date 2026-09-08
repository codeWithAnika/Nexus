"""add dataset_image_id to firs

Adds a nullable integer column dataset_image_id to the firs table.
This column anchors a backend FIR row to its source image in the
FIR_Dataset_ICDAR2023 dataset (image_id field in FIR_details.json).

The column is:
  - nullable   -> existing / non-dataset FIR records are unaffected
  - unique     -> each ICDAR image_id can only appear in one FIR row

Revision ID: c7d2e8f1a345
Revises: 4b971a90816a
Create Date: 2026-09-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d2e8f1a345"
down_revision: Union[str, Sequence[str], None] = "4b971a90816a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new nullable column first (safe for existing rows)
    op.add_column(
        "firs",
        sa.Column("dataset_image_id", sa.Integer(), nullable=True),
    )
    # Unique constraint (Oracle will automatically create a unique index for this)
    op.create_unique_constraint(
        "uq_firs_dataset_image_id",
        "firs",
        ["dataset_image_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_firs_dataset_image_id", "firs", type_="unique")
    op.drop_column("firs", "dataset_image_id")
