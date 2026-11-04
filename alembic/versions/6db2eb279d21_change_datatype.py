"""change datatype

Revision ID: 6db2eb279d21
Revises: 5d5e830dbae3
Create Date: 2026-11-04 16:09:05.615627

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6db2eb279d21'
down_revision: Union[str, Sequence[str], None] = '5d5e830dbae3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Only reset the sequence to 101 if it already exists.
    op.execute("SELECT setval('products_product_id_seq', 100, true)")


def downgrade() -> None:
    """Downgrade schema."""
    # No-op: the original schema did not depend on the custom sequence start.
    pass
