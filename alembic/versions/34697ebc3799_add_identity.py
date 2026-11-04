"""add Identity

Revision ID: 34697ebc3799
Revises: f5386196666a
Create Date: 2026-11-04 16:29:47.278410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34697ebc3799'
down_revision: Union[str, Sequence[str], None] = 'f5386196666a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE products
        ALTER COLUMN product_id DROP DEFAULT;

        ALTER TABLE products
        ALTER COLUMN product_id DROP IDENTITY IF EXISTS;

        ALTER TABLE products
        ALTER COLUMN product_id
        ADD GENERATED ALWAYS AS IDENTITY
        (START WITH 101 INCREMENT BY 1);
        """
    )

    op.alter_column('product_categories', 'created_by', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('product_categories', 'created_by', nullable=True)
    op.execute(
        """
        ALTER TABLE products
        ALTER COLUMN product_id DROP IDENTITY IF EXISTS;

        ALTER TABLE products
        ALTER COLUMN product_id SET DEFAULT nextval('products_product_id_seq');
        """
    )
