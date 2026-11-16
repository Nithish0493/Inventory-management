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

from app.enums import purchase_status_enum, sale_status_enum


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (Index("idx_purchase_orders_supplier", "supplier_id"),)
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
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
    created_by_user = relationship("User", foreign_keys=[created_by])

    updated_by_user = relationship("User", foreign_keys=[updated_by])

    supplier = relationship("Supplier")
    items = relationship(
        "PurchaseItem",
        back_populates="purchase_order",
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_purchase_items_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_purchase_items_unit_price"),
        Index("idx_purchase_items_purchase", "purchase_id"),
        Index("idx_purchase_items_product", "product_id"),
        UniqueConstraint(
            "purchase_id", "product_id", name="uq_purchase_items_purchase_product"
        ),
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
    product = relationship("Product")
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="items",
    )


class SaleOrder(Base):
    __tablename__ = "sale_orders"
    __table_args__ = (Index("idx_sale_orders_customer", "customer_id"),)

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
    sale_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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

    created_by_user = relationship("User", foreign_keys=[created_by])

    updated_by_user = relationship("User", foreign_keys=[updated_by])

    customer = relationship("Customer")

    items = relationship("SaleItem", back_populates="sale_order")


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_sale_items_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_sale_items_unit_price"),
        Index("idx_sale_items_sale", "sale_id"),
        Index("idx_sale_items_product", "product_id"),
        UniqueConstraint("sale_id", "product_id", name="uq_sale_items_sale_product"),
    )

    sale_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sale_orders.sale_id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.product_id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(22, 2),
        Computed("quantity * unit_price", persisted=True),
    )

    # Relationships
    sale_order = relationship("SaleOrder", back_populates="items")

    product = relationship("Product")
