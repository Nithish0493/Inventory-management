"""drop table

Revision ID: 95c62cfcbd09
Revises: 001797503d58
Create Date: 2026-11-04 17:46:19.201365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '95c62cfcbd09'
down_revision: Union[str, Sequence[str], None] = '001797503d58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is intentionally destructive and should only be used on a disposable dev/test database.
    op.execute("DROP TABLE IF EXISTS stock_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS customer_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS sale_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS price_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS products CASCADE;")
    op.execute("DROP TABLE IF EXISTS purchase_orders CASCADE;")
    op.execute("DROP TABLE IF EXISTS sale_orders CASCADE;")
    op.execute("DROP TABLE IF EXISTS user_history CASCADE;")
    op.execute("DROP TABLE IF EXISTS suppliers CASCADE;")
    op.execute("DROP TABLE IF EXISTS customers CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
    op.execute("DROP TABLE IF EXISTS product_categories CASCADE;")

    op.execute("DROP TYPE IF EXISTS record_action CASCADE;")
    op.execute("DROP TYPE IF EXISTS change_type CASCADE;")
    op.execute("DROP TYPE IF EXISTS sale_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS purchase_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS record_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS user_role CASCADE;")


def downgrade() -> None:
    """Downgrade schema."""
    # No automatic downgrade for a full reset migration.
    pass
    op.create_table('sale_orders',
    sa.Column('sale_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('sale_date', sa.DATE(), server_default=sa.text('CURRENT_DATE'), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('draft', 'order_placed', 'delivered', 'cancelled', name='sale_status', create_type=False), server_default=sa.text("'draft'::sale_status"), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('sale_orders_created_by_fkey')),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], name=op.f('sale_orders_customer_id_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('sale_orders_updated_by_fkey')),
    sa.PrimaryKeyConstraint('sale_id', name=op.f('sale_orders_pkey'))
    )
    op.create_index(op.f('idx_sale_orders_customer'), 'sale_orders', ['customer_id'], unique=False)
    op.create_table('user_history',
    sa.Column('user_hist_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('action', postgresql.ENUM('created', 'updated', 'password_changed', name='record_action', create_type=False), autoincrement=False, nullable=False),
    sa.Column('old_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('new_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('remarks', sa.TEXT(), autoincrement=False, nullable=True),
    sa.CheckConstraint("action = 'created'::record_action AND old_data IS NULL AND new_data IS NOT NULL OR action = 'updated'::record_action AND old_data IS NOT NULL AND new_data IS NOT NULL OR action = 'password_changed'::record_action AND old_data IS NULL AND new_data IS NULL", name=op.f('chk_user_history_data')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('user_history_updated_by_fkey')),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('user_history_user_id_fkey')),
    sa.PrimaryKeyConstraint('user_hist_id', name=op.f('user_history_pkey'))
    )
    op.create_index(op.f('idx_user_history_user'), 'user_history', ['user_id'], unique=False)
    op.create_table('purchase_orders',
    sa.Column('purchase_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('supplier_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('purchase_date', sa.DATE(), server_default=sa.text('CURRENT_DATE'), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('draft', 'order_placed', 'delivered', 'cancelled', name='purchase_status', create_type=False), server_default=sa.text("'draft'::purchase_status"), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('purchase_orders_created_by_fkey')),
    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.supplier_id'], name=op.f('purchase_orders_supplier_id_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('purchase_orders_updated_by_fkey')),
    sa.PrimaryKeyConstraint('purchase_id', name=op.f('purchase_orders_pkey'))
    )
    op.create_index(op.f('idx_purchase_orders_supplier'), 'purchase_orders', ['supplier_id'], unique=False)
    op.create_table('products',
    sa.Column('product_id', sa.INTEGER(), sa.Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('sku', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('product_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('product_description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('category_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('cost_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
    sa.Column('sale_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
    sa.Column('stock_quantity', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('reorder_level', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('active', 'inactive', name='record_status', create_type=False), server_default=sa.text("'active'::record_status"), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.CheckConstraint('cost_price >= 0::numeric', name=op.f('chk_products_cost_price')),
    sa.CheckConstraint('reorder_level >= 0', name=op.f('chk_products_reorder_level')),
    sa.CheckConstraint('sale_price >= 0::numeric', name=op.f('chk_products_sale_price')),
    sa.CheckConstraint('stock_quantity >= 0', name=op.f('chk_products_stock_quantity')),
    sa.ForeignKeyConstraint(['category_id'], ['product_categories.category_id'], name=op.f('products_category_id_fkey')),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('products_created_by_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('products_updated_by_fkey')),
    sa.PrimaryKeyConstraint('product_id', name=op.f('products_pkey')),
    sa.UniqueConstraint('sku', name=op.f('products_sku_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('idx_products_category'), 'products', ['category_id'], unique=False)
    op.create_table('price_history',
    sa.Column('price_hist_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('old_cost_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=True),
    sa.Column('new_cost_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=True),
    sa.Column('old_sale_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=True),
    sa.Column('new_sale_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('remarks', sa.TEXT(), autoincrement=False, nullable=True),
    sa.CheckConstraint('(old_cost_price IS NULL OR old_cost_price >= 0::numeric) AND (new_cost_price IS NULL OR new_cost_price >= 0::numeric) AND (old_sale_price IS NULL OR old_sale_price >= 0::numeric) AND (new_sale_price IS NULL OR new_sale_price >= 0::numeric)', name=op.f('chk_price_history_non_negative')),
    sa.CheckConstraint('old_cost_price IS NOT NULL OR old_sale_price IS NOT NULL', name=op.f('chk_price_history_change')),
    sa.CheckConstraint('old_cost_price IS NULL AND new_cost_price IS NULL OR old_cost_price IS NOT NULL AND new_cost_price IS NOT NULL AND old_cost_price IS DISTINCT FROM new_cost_price', name=op.f('chk_cost_price_pair')),
    sa.CheckConstraint('old_sale_price IS NULL AND new_sale_price IS NULL OR old_sale_price IS NOT NULL AND new_sale_price IS NOT NULL AND old_sale_price IS DISTINCT FROM new_sale_price', name=op.f('chk_sale_price_pair')),
    sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], name=op.f('price_history_product_id_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('price_history_updated_by_fkey')),
    sa.PrimaryKeyConstraint('price_hist_id', name=op.f('price_history_pkey'))
    )
    op.create_index(op.f('idx_price_history_product'), 'price_history', ['product_id'], unique=False)
    op.create_table('product_categories',
    sa.Column('category_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('category_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('created_by', sa.UUID(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], name=op.f('product_categories_created_by_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('product_categories_updated_by_fkey')),
    sa.PrimaryKeyConstraint('category_id', name=op.f('product_categories_pkey')),
    sa.UniqueConstraint('category_name', name=op.f('product_categories_category_name_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_table('sale_items',
    sa.Column('sale_item_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('sale_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('unit_price', sa.NUMERIC(precision=12, scale=2), autoincrement=False, nullable=False),
    sa.Column('total_price', sa.NUMERIC(precision=22, scale=2), sa.Computed('((quantity)::numeric * unit_price)', persisted=True), autoincrement=False, nullable=False),
    sa.CheckConstraint('quantity > 0', name=op.f('chk_sale_items_quantity')),
    sa.CheckConstraint('unit_price >= 0::numeric', name=op.f('chk_sale_items_unit_price')),
    sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], name=op.f('sale_items_product_id_fkey')),
    sa.ForeignKeyConstraint(['sale_id'], ['sale_orders.sale_id'], name=op.f('sale_items_sale_id_fkey')),
    sa.PrimaryKeyConstraint('sale_item_id', name=op.f('sale_items_pkey'))
    )
    op.create_index(op.f('idx_sale_items_sale'), 'sale_items', ['sale_id'], unique=False)
    op.create_index(op.f('idx_sale_items_product'), 'sale_items', ['product_id'], unique=False)
    op.create_table('customer_history',
    sa.Column('customer_hist_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('customer_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('action', postgresql.ENUM('created', 'updated', 'password_changed', name='record_action', create_type=False), autoincrement=False, nullable=False),
    sa.Column('old_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('new_data', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('remarks', sa.TEXT(), autoincrement=False, nullable=True),
    sa.CheckConstraint("action = 'created'::record_action AND old_data IS NULL AND new_data IS NOT NULL OR action = 'updated'::record_action AND old_data IS NOT NULL AND new_data IS NOT NULL", name=op.f('chk_customer_history_data')),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id'], name=op.f('customer_history_customer_id_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('customer_history_updated_by_fkey')),
    sa.PrimaryKeyConstraint('customer_hist_id', name=op.f('customer_history_pkey'))
    )
    op.create_index(op.f('idx_customer_history_customer'), 'customer_history', ['customer_id'], unique=False)
    op.create_table('stock_history',
    sa.Column('stock_hist_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('purchase_item_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('sale_item_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('change_type', postgresql.ENUM('purchase', 'sale', 'adjustment', 'reversal', name='change_type', create_type=False), autoincrement=False, nullable=False),
    sa.Column('quantity_change', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=False),
    sa.Column('remarks', sa.TEXT(), autoincrement=False, nullable=True),
    sa.CheckConstraint("change_type = 'purchase'::change_type AND purchase_item_id IS NOT NULL AND sale_item_id IS NULL AND quantity_change > 0 OR change_type = 'sale'::change_type AND sale_item_id IS NOT NULL AND purchase_item_id IS NULL AND quantity_change < 0 OR change_type = 'adjustment'::change_type AND purchase_item_id IS NULL AND sale_item_id IS NULL AND NULLIF(TRIM(BOTH FROM remarks), ''::text) IS NOT NULL OR change_type = 'reversal'::change_type AND (purchase_item_id IS NOT NULL AND sale_item_id IS NULL AND quantity_change < 0 OR purchase_item_id IS NULL AND sale_item_id IS NOT NULL AND quantity_change > 0)", name=op.f('chk_stock_history_source')),
    sa.CheckConstraint('quantity_change <> 0', name=op.f('chk_stock_history_quantity_change')),
    sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], name=op.f('stock_history_product_id_fkey')),
    sa.ForeignKeyConstraint(['purchase_item_id'], ['purchase_items.purchase_item_id'], name=op.f('stock_history_purchase_item_id_fkey')),
    sa.ForeignKeyConstraint(['sale_item_id'], ['sale_items.sale_item_id'], name=op.f('stock_history_sale_item_id_fkey')),
    sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], name=op.f('stock_history_updated_by_fkey')),
    sa.PrimaryKeyConstraint('stock_hist_id', name=op.f('stock_history_pkey'))
    )
    op.create_index(op.f('idx_stock_history_updated_at'), 'stock_history', ['updated_at'], unique=False)
    op.create_index(op.f('idx_stock_history_product'), 'stock_history', ['product_id'], unique=False)
    # ### end Alembic commands ###
