from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from modules.users.models import User
from modules.history.models import (
    CustomerHistory,
    PriceHistory,
    StockHistory,
    UserHistory,
)
from modules.history.schemas import (
    CustomerHistoryResponse,
    PriceHistoryResponse,
    StockHistoryResponse,
    UserHistoryResponse,
)
from modules.history.service import (
    get_stock_history_service,
    get_stock_history_by_sku_service,
    get_price_history_service,
    get_price_history_by_sku_service,
    get_user_history_service,
    get_user_history_by_user_service,
    get_customer_history_service,
    get_customer_history_by_customer_service,
)

router = APIRouter()


@router.get("/stock-history", response_model=list[StockHistoryResponse])
def get_stock_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return get_stock_history_service(db=db, current_user=current_user)


@router.get("/stock-history/{sku}", response_model=list[StockHistoryResponse])
def get_stock_history_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_stock_history_by_sku_service(sku=sku, db=db, current_user=current_user)


@router.get("/price-history", response_model=list[PriceHistoryResponse])
def get_price_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return get_price_history_service(db=db, current_user=current_user)


@router.get("/price-history/{sku}", response_model=list[PriceHistoryResponse])
def get_price_history_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_price_history_by_sku_service(sku=sku, db=db, current_user=current_user)


@router.get("/user-history", response_model=list[UserHistoryResponse])
def get_user_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return get_user_history_service(db=db, current_user=current_user)


@router.get("/user-history/{target_user_id}", response_model=list[UserHistoryResponse])
def get_user_history_by_user(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_history_by_user_service(
        target_user_id=target_user_id, db=db, current_user=current_user
    )


@router.get("/customer-history", response_model=list[CustomerHistoryResponse])
def get_customer_history(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return get_customer_history_service(db=db, current_user=current_user)


@router.get(
    "/customer-history/{target_customer_id}",
    response_model=list[CustomerHistoryResponse],
)
def get_customer_history_by_customer(
    target_customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_customer_history_by_customer_service(
        target_customer_id=target_customer_id, db=db, current_user=current_user
    )
