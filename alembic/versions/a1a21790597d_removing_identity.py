"""removing identity

Revision ID: a1a21790597d
Revises: 34697ebc3799
Create Date: 2026-11-04 17:27:54.438309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1a21790597d'
down_revision: Union[str, Sequence[str], None] = '34697ebc3799'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE products
        ALTER COLUMN product_id DROP IDENTITY IF EXISTS;

        ALTER TABLE products
        ALTER COLUMN product_id DROP DEFAULT;
    """)

def downgrade() -> None:
    op.execute("""
        ALTER TABLE products
        ALTER COLUMN product_id
        ADD GENERATED ALWAYS AS IDENTITY
        (START WITH 101 INCREMENT BY 1);
    """)
