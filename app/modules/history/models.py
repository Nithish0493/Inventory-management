import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from app.enums import change_type_enum, record_action_enum


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

    updated_by_user = relationship("User", foreign_keys=[updated_by])
    product = relationship("Product")

    purchase_item = relationship("PurchaseItem")

    sale_item = relationship("SaleItem")


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        # 1. All prices must be NULL or non-negative.
        CheckConstraint(
            """
        (old_cost_price IS NULL OR old_cost_price >= 0)
        AND
        (new_cost_price IS NULL OR new_cost_price >= 0)
        AND
        (old_sale_price IS NULL OR old_sale_price >= 0)
        AND
        (new_sale_price IS NULL OR new_sale_price >= 0)
        """,
            name="chk_price_history_non_negative",
        ),
        # 2. Cost price:
        # Either both values are NULL,
        # OR both values are present and different.
        CheckConstraint(
            """
        (
            old_cost_price IS NULL
            AND new_cost_price IS NULL
        )
        OR
        (
            old_cost_price IS NOT NULL
            AND new_cost_price IS NOT NULL
            AND old_cost_price IS DISTINCT FROM new_cost_price
        )
        """,
            name="chk_cost_price_pair",
        ),
        # 3. Sale price:
        # Either both values are NULL,
        # OR both values are present and different.
        CheckConstraint(
            """
        (
            old_sale_price IS NULL
            AND new_sale_price IS NULL
        )
        OR
        (
            old_sale_price IS NOT NULL
            AND new_sale_price IS NOT NULL
            AND old_sale_price IS DISTINCT FROM new_sale_price
        )
        """,
            name="chk_sale_price_pair",
        ),
        # 4. At least one type of price must have changed.
        CheckConstraint(
            """
        old_cost_price IS NOT NULL
        OR
        old_sale_price IS NOT NULL
        """,
            name="chk_price_history_change",
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

    updated_by_user = relationship("User", foreign_keys=[updated_by])
    product = relationship("Product")


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

    updated_by_user = relationship("User", foreign_keys=[updated_by])
    user = relationship("User", foreign_keys=[user_id])


class CustomerHistory(Base):
    __tablename__ = "customer_history"
    __table_args__ = (
        CheckConstraint(
            "(action = 'created' AND old_data IS NULL AND new_data IS NOT NULL) "
            "OR (action = 'updated' AND old_data IS NOT NULL AND new_data IS NOT NULL)",
            name="chk_customer_history_data",
        ),
        Index("idx_customer_history_customer", "customer_id"),
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
    new_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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

    updated_by_user = relationship("User", foreign_keys=[updated_by])
    customer = relationship("Customer")
