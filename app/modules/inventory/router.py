from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from modules.users.models import User
from modules.inventory.models import Product, ProductCategory
from modules.history.schemas import StockHistoryResponse
from modules.inventory.schemas import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from modules.inventory.service import (
    create_category_service,
    get_categories_service,
    get_category_service,
    update_category_service,
    create_product_service,
    get_products_service,
    get_product_service,
    update_product_service,
    adjust_stock_service,
)

router = APIRouter()


@router.post("/categories", response_model=ProductCategoryResponse, status_code=201)
def create_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_category_service(payload=payload, db=db, current_user=current_user)


@router.get("/categories", response_model=list[ProductCategoryResponse])
def get_categories(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_categories_service(
        limit=limit, offset=offset, db=db, current_user=current_user
    )


@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_category_service(
        category_id=category_id, db=db, current_user=current_user
    )


@router.patch(
    "/categories/{target_category_id}",
    response_model=ProductCategoryResponse,
    status_code=200,
)
def update_category(
    target_category_id: int,
    payload: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_category_service(
        target_category_id=target_category_id,
        payload=payload,
        db=db,
        current_user=current_user,
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    return create_product_service(payload=payload, db=db, current_user=current_user)


@router.get("/products", response_model=list[ProductResponse])
def get_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_products_service(
        limit=limit, offset=offset, db=db, current_user=current_user
    )


@router.get("/products/{sku}", response_model=ProductResponse)
def get_product(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_product_service(sku=sku, db=db, current_user=current_user)


@router.patch("/products/{sku}", response_model=ProductResponse, status_code=200)
def update_product(
    sku: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_product_service(
        sku=sku, payload=payload, db=db, current_user=current_user
    )


@router.post(
    "/products/{sku}/stock-adjustments",
    response_model=StockHistoryResponse,
    status_code=201,
)
def adjust_stock(
    sku: str,
    quantity_change: int = Query(...),
    remarks: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return adjust_stock_service(
        sku=sku,
        quantity_change=quantity_change,
        remarks=remarks,
        db=db,
        current_user=current_user,
    )
