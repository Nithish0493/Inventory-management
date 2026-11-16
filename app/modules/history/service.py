from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from modules.users.models import User
from modules.history.models import (
    CustomerHistory,
    PriceHistory,
    StockHistory,
    UserHistory,
)
from modules.inventory.models import Product
from modules.history.schemas import (
    CustomerHistoryResponse,
    PriceHistoryResponse,
    StockHistoryResponse,
    UserHistoryResponse,
)


def get_stock_history_service(db: Session, current_user: User):
    statement = (
        select(StockHistory)
        .options(
            selectinload(StockHistory.product),
            selectinload(StockHistory.updated_by_user),
        )
        .order_by(StockHistory.updated_at.desc(), StockHistory.stock_hist_id.desc())
        .limit(10)
    )
    return db.scalars(statement).all()


def get_stock_history_by_sku_service(sku: str, db: Session, current_user: User):
    statement = (
        select(StockHistory)
        .join(Product)
        .options(
            selectinload(StockHistory.product),
            selectinload(StockHistory.updated_by_user),
        )
        .where(Product.sku == sku)
        .order_by(StockHistory.updated_at.desc(), StockHistory.stock_hist_id.desc())
    )
    return db.scalars(statement).all()


def get_price_history_service(db: Session, current_user: User):
    statement = (
        select(PriceHistory)
        .options(
            selectinload(PriceHistory.product),
            selectinload(PriceHistory.updated_by_user),
        )
        .order_by(PriceHistory.updated_at.desc(), PriceHistory.price_hist_id.desc())
        .limit(10)
    )
    return db.scalars(statement).all()


def get_price_history_by_sku_service(sku: str, db: Session, current_user: User):
    statement = (
        select(PriceHistory)
        .join(Product)
        .options(
            selectinload(PriceHistory.product),
            selectinload(PriceHistory.updated_by_user),
        )
        .where(Product.sku == sku)
        .order_by(PriceHistory.updated_at.desc(), PriceHistory.price_hist_id.desc())
    )
    return db.scalars(statement).all()


def get_user_history_service(db: Session, current_user: User):
    statement = (
        select(UserHistory)
        .options(
            selectinload(UserHistory.user), selectinload(UserHistory.updated_by_user)
        )
        .order_by(UserHistory.updated_at.desc(), UserHistory.user_hist_id.desc())
        .limit(10)
    )
    return db.scalars(statement).all()


def get_user_history_by_user_service(
    target_user_id: UUID, db: Session, current_user: User
):
    statement = (
        select(UserHistory)
        .options(
            selectinload(UserHistory.user), selectinload(UserHistory.updated_by_user)
        )
        .where(UserHistory.user_id == target_user_id)
        .order_by(UserHistory.updated_at.desc(), UserHistory.user_hist_id.desc())
    )
    return db.scalars(statement).all()


def get_customer_history_service(db: Session, current_user: User):
    statement = (
        select(CustomerHistory)
        .options(
            selectinload(CustomerHistory.customer),
            selectinload(CustomerHistory.updated_by_user),
        )
        .order_by(
            CustomerHistory.updated_at.desc(), CustomerHistory.customer_hist_id.desc()
        )
        .limit(10)
    )
    return db.scalars(statement).all()


def get_customer_history_by_customer_service(
    target_customer_id: UUID, db: Session, current_user: User
):
    statement = (
        select(CustomerHistory)
        .options(
            selectinload(CustomerHistory.customer),
            selectinload(CustomerHistory.updated_by_user),
        )
        .where(CustomerHistory.customer_id == target_customer_id)
        .order_by(
            CustomerHistory.updated_at.desc(), CustomerHistory.customer_hist_id.desc()
        )
    )
    return db.scalars(statement).all()
