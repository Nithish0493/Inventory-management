

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# BASE CLASS
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy ORM models."""


# ---------------------------------------------------------------------------
# POSTGRESQL ENUM TYPES
# The Python variable is used in mapped_column(); name= is the PostgreSQL type.
# ---------------------------------------------------------------------------

user_role_enum = ENUM(
    "admin",
    "staff",
    name="user_role",
    metadata=Base.metadata,
)

purchase_status_enum = ENUM(
    "draft",
    "order_placed",
    "delivered",
    "cancelled",
    name="purchase_status",
    metadata=Base.metadata,
)

sale_status_enum = ENUM(
    "draft",
    "order_placed",
    "delivered",
    "cancelled",
    name="sale_status",
    metadata=Base.metadata,
)

record_status_enum = ENUM(
    "active",
    "inactive",
    name="record_status",
    metadata=Base.metadata,
)

change_type_enum = ENUM(
    "purchase",
    "sale",
    "adjustment",
    "reversal",
    name="change_type",
    metadata=Base.metadata,
)

record_action_enum = ENUM(
    "created",
    "updated",
    "password_changed",
    name="record_action",
    metadata=Base.metadata,
)


# ---------------------------------------------------------------------------
# COMMON AUDIT-COLUMN CONVENTION
#
# For mutable business tables:
# - created_at is populated by PostgreSQL on INSERT (server_default).
# - updated_at is NULL on INSERT and is populated by SQLAlchemy on UPDATE
#   (onupdate). It does not run for UPDATE statements issued outside SQLAlchemy.
# - updated_by is NULL on INSERT and must be assigned by application logic
#   to the authenticated user's UUID when updating a record.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 1. USERS
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,  # UUID generated in Python by SQLAlchemy
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(user_role_enum, nullable=False)
    login_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(
        record_status_enum,
        nullable=False,
        server_default=text("'active'::record_status"),
    )

    # NULL is allowed for the first administrator because no creator exists yet.
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 2. CUSTOMERS
# ---------------------------------------------------------------------------

class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 3. SUPPLIERS
# ---------------------------------------------------------------------------

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        record_status_enum,
        nullable=False,
        server_default=text("'active'::record_status"),
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 4. PRODUCT CATEGORIES
# ---------------------------------------------------------------------------

class ProductCategory(Base):
    __tablename__ = "product_categories"

    category_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Added so category updates can be attributed to a user.
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 5. PRODUCTS
# ---------------------------------------------------------------------------

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="chk_products_cost_price"),
        CheckConstraint("sale_price >= 0", name="chk_products_sale_price"),
        CheckConstraint("stock_quantity >= 0", name="chk_products_stock_quantity"),
        CheckConstraint("reorder_level >= 0", name="chk_products_reorder_level"),
        Index("idx_products_category", "category_id"),
    )

    product_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    sku: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_categories.category_id"),
        nullable=False,
    )

    cost_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    reorder_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    status: Mapped[str] = mapped_column(
        record_status_enum,
        nullable=False,
        server_default=text("'active'::record_status"),
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    # Renamed from last_updated_by to updated_by for consistency.
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 6. PURCHASE ORDERS
# ---------------------------------------------------------------------------

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("idx_purchase_orders_supplier", "supplier_id"),
    )

    purchase_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    supplier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("suppliers.supplier_id"),
        nullable=False,
    )
    purchase_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
    )
    status: Mapped[str] = mapped_column(
        purchase_status_enum,
        nullable=False,
        server_default=text("'draft'::purchase_status"),
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 7. PURCHASE ITEMS
# ---------------------------------------------------------------------------

class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_purchase_items_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_purchase_items_unit_price"),
        Index("idx_purchase_items_purchase", "purchase_id"),
        Index("idx_purchase_items_product", "product_id"),
    )

    purchase_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    purchase_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("purchase_orders.purchase_id"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.product_id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(22, 2),
        Computed("quantity * unit_price", persisted=True),
    )


# ---------------------------------------------------------------------------
# 8. SALE ORDERS
# ---------------------------------------------------------------------------

class SaleOrder(Base):
    __tablename__ = "sale_orders"
    __table_args__ = (
        Index("idx_sale_orders_customer", "customer_id"),
    )

    sale_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.customer_id"),
        nullable=False,
    )
    sale_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
    )
    status: Mapped[str] = mapped_column(
        sale_status_enum,
        nullable=False,
        server_default=text("'draft'::sale_status"),
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.current_timestamp(),
    )


# ---------------------------------------------------------------------------
# 9. SALE ITEMS
# ---------------------------------------------------------------------------

class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_sale_items_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_sale_items_unit_price"),
        Index("idx_sale_items_sale", "sale_id"),
        Index("idx_sale_items_product", "product_id"),
    )

    sale_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    sale_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sale_orders.sale_id"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.product_id"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(22, 2),
        Computed("quantity * unit_price", persisted=True),
    )


# ---------------------------------------------------------------------------
# 10. STOCK HISTORY
# History rows are event records: updated_by and updated_at are populated
# when the history row is INSERTED, not on a later update.
# ---------------------------------------------------------------------------

class StockHistory(Base):
    __tablename__ = "stock_history"
    __table_args__ = (
        CheckConstraint(
            "quantity_change <> 0",
            name="chk_stock_history_quantity_change",
        ),
        CheckConstraint(
            """
            (
                change_type = 'purchase'
                AND purchase_item_id IS NOT NULL
                AND sale_item_id IS NULL
                AND quantity_change > 0
            )
            OR
            (
                change_type = 'sale'
                AND sale_item_id IS NOT NULL
                AND purchase_item_id IS NULL
                AND quantity_change < 0
            )
            OR
            (
                change_type = 'adjustment'
                AND purchase_item_id IS NULL
                AND sale_item_id IS NULL
                AND NULLIF(TRIM(remarks), '') IS NOT NULL
            )
            OR
            (
                change_type = 'reversal'
                AND (
                    (
                        purchase_item_id IS NOT NULL
                        AND sale_item_id IS NULL
                        AND quantity_change < 0
                    )
                    OR
                    (
                        purchase_item_id IS NULL
                        AND sale_item_id IS NOT NULL
                        AND quantity_change > 0
                    )
                )
            )
            """,
            name="chk_stock_history_source",
        ),
        Index("idx_stock_history_product", "product_id"),
        Index("idx_stock_history_updated_at", "updated_at"),
    )

    stock_hist_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.product_id"),
        nullable=False,
    )
    purchase_item_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("purchase_items.purchase_item_id"),
        nullable=True,
    )
    sale_item_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sale_items.sale_item_id"),
        nullable=True,
    )
    change_type: Mapped[str] = mapped_column(change_type_enum, nullable=False)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# 11. PRICE HISTORY
# ---------------------------------------------------------------------------

class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        CheckConstraint(
            "old_cost_price IS NULL OR old_cost_price >= 0",
            name="chk_old_cost_price",
        ),
        CheckConstraint(
            "new_cost_price IS NULL OR new_cost_price >= 0",
            name="chk_new_cost_price",
        ),
        CheckConstraint(
            "old_sale_price IS NULL OR old_sale_price >= 0",
            name="chk_old_sale_price",
        ),
        CheckConstraint(
            "new_sale_price IS NULL OR new_sale_price >= 0",
            name="chk_new_sale_price",
        ),
        CheckConstraint(
            "(old_cost_price IS NULL AND new_cost_price IS NULL) "
            "OR (old_cost_price IS NOT NULL AND new_cost_price IS NOT NULL)",
            name="chk_cost_price_pair",
        ),
        CheckConstraint(
            "(old_sale_price IS NULL AND new_sale_price IS NULL) "
            "OR (old_sale_price IS NOT NULL AND new_sale_price IS NOT NULL)",
            name="chk_sale_price_pair",
        ),
        CheckConstraint(
            "old_cost_price IS NOT NULL OR old_sale_price IS NOT NULL",
            name="chk_price_history_change",
        ),
        CheckConstraint(
            "old_cost_price IS DISTINCT FROM new_cost_price "
            "OR old_sale_price IS DISTINCT FROM new_sale_price",
            name="chk_price_history_actual_change",
        ),
        Index("idx_price_history_product", "product_id"),
    )

    price_hist_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.product_id"),
        nullable=False,
    )
    old_cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    new_cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    old_sale_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    new_sale_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# 12. USER HISTORY
# changed_by was renamed to updated_by as requested.
# changed_at is retained because it records when this history event occurred.
# ---------------------------------------------------------------------------

class UserHistory(Base):
    __tablename__ = "user_history"
    __table_args__ = (
        CheckConstraint(
            """
            (
                action = 'created'
                AND old_data IS NULL
                AND new_data IS NOT NULL
            )
            OR
            (
                action = 'updated'
                AND old_data IS NOT NULL
                AND new_data IS NOT NULL
            )
            OR
            (
                action = 'password_changed'
                AND old_data IS NULL
                AND new_data IS NULL
            )
            """,
            name="chk_user_history_data",
        ),
        Index("idx_user_history_user", "user_id"),
        Index("idx_user_history_changed_at", "changed_at"),
    )

    user_hist_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(record_action_enum, nullable=False)
    old_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# 13. CUSTOMER HISTORY
# changed_by was renamed to updated_by as requested.
# changed_at is retained because it records when this history event occurred.
# ---------------------------------------------------------------------------

class CustomerHistory(Base):
    __tablename__ = "customer_history"
    __table_args__ = (
        CheckConstraint(
            "(action = 'created' AND old_data IS NULL AND new_data IS NOT NULL) "
            "OR (action = 'updated' AND old_data IS NOT NULL AND new_data IS NOT NULL)",
            name="chk_customer_history_data",
        ),
        Index("idx_customer_history_customer", "customer_id"),
        Index("idx_customer_history_changed_at", "changed_at"),
    )

    customer_hist_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.customer_id"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(record_action_enum, nullable=False)
    old_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)