from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from modules.users.models import User
from modules.inventory.models import Product, ProductCategory
from modules.history.models import PriceHistory, StockHistory
from modules.inventory.schemas import (
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)


def get_product_with_audit(product_id: int, db: Session) -> Product:
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user), selectinload(Product.updated_by_user)
        )
        .where(Product.product_id == product_id)
    )
    return db.scalar(statement)


def get_category_with_audit(category_id: int, db: Session) -> ProductCategory:
    statement = (
        select(ProductCategory)
        .options(
            selectinload(ProductCategory.created_by_user),
            selectinload(ProductCategory.updated_by_user),
        )
        .where(ProductCategory.category_id == category_id)
    )
    return db.scalar(statement)


def commit_or_409(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=message)


def create_category_service(
    payload: ProductCategoryCreate, db: Session, current_user: User
):
    new_category = ProductCategory(
        **payload.model_dump(), created_by=current_user.user_id
    )
    try:
        db.add(new_category)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Category name already exists or database constraint violated",
        )
    db.refresh(new_category)
    return get_category_with_audit(new_category.category_id, db)


def get_categories_service(limit: int, offset: int, db: Session, current_user: User):
    statement = (
        select(ProductCategory)
        .options(
            selectinload(ProductCategory.created_by_user),
            selectinload(ProductCategory.updated_by_user),
        )
        .order_by(ProductCategory.category_name)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()


def get_category_service(category_id: int, db: Session, current_user: User):
    category = get_category_with_audit(category_id, db)
    if category is None:
        raise HTTPException(status_code=404, detail="Product category not found")
    return category


def update_category_service(
    target_category_id: int,
    payload: ProductCategoryUpdate,
    db: Session,
    current_user: User,
):
    statement = (
        select(ProductCategory)
        .where(ProductCategory.category_id == target_category_id)
        .with_for_update()
    )
    target_category = db.scalar(statement)
    if target_category is None:
        raise HTTPException(status_code=404, detail="Product category not found")
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    update_data["updated_by"] = current_user.user_id
    for field, value in update_data.items():
        setattr(target_category, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Category name already exists or a database constraint was violated",
        )
    db.refresh(target_category)
    return get_category_with_audit(target_category_id, db)


def create_product_service(payload: ProductCreate, db: Session, current_user: User):
    category = db.scalar(
        select(ProductCategory).where(
            ProductCategory.category_id == payload.category_id
        )
    )
    if category is None:
        raise HTTPException(status_code=404, detail="Product category not found")
    new_product = Product(**payload.model_dump(), created_by=current_user.user_id)
    db.add(new_product)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists or database constraint violated",
        )
    db.refresh(new_product)
    return get_product_with_audit(new_product.product_id, db)


def get_products_service(limit: int, offset: int, db: Session, current_user: User):
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user), selectinload(Product.updated_by_user)
        )
        .order_by(Product.product_id)
        .limit(limit)
        .offset(offset)
    )
    products = db.execute(statement).scalars().all()
    return products


def get_product_service(sku: str, db: Session, current_user: User):
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user), selectinload(Product.updated_by_user)
        )
        .where(Product.sku == sku)
    )
    product = db.execute(statement).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def update_product_service(
    sku: str, payload: ProductUpdate, db: Session, current_user: User
):
    statement = select(Product).where(Product.sku == sku).with_for_update()
    target_product = db.scalar(statement)
    if target_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    if "category_id" in update_data:
        category_statement = select(ProductCategory).where(
            ProductCategory.category_id == update_data["category_id"]
        )
        category = db.scalar(category_statement)
        if category is None:
            raise HTTPException(status_code=404, detail="Product category not found")
    old_cost = target_product.cost_price
    old_sale = target_product.sale_price
    new_cost = update_data.get("cost_price", old_cost)
    new_sale = update_data.get("sale_price", old_sale)
    update_data["updated_by"] = current_user.user_id
    for field, value in update_data.items():
        setattr(target_product, field, value)
    try:
        if new_cost != old_cost or new_sale != old_sale:
            db.add(
                PriceHistory(
                    product_id=target_product.product_id,
                    old_cost_price=old_cost if new_cost != old_cost else None,
                    new_cost_price=new_cost if new_cost != old_cost else None,
                    old_sale_price=old_sale if new_sale != old_sale else None,
                    new_sale_price=new_sale if new_sale != old_sale else None,
                    updated_by=current_user.user_id,
                    remarks="Product price updated",
                )
            )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists or a database constraint was violated",
        )
    db.refresh(target_product)
    return get_product_with_audit(target_product.product_id, db)


def adjust_stock_service(
    sku: str, quantity_change: int, remarks: str, db: Session, current_user: User
):
    if quantity_change == 0:
        raise HTTPException(status_code=400, detail="quantity_change cannot be 0")
    product = db.scalar(select(Product).where(Product.sku == sku).with_for_update())

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.status != "active":
        raise HTTPException(
            status_code=400, detail="Cannot adjust stock for an inactive product"
        )
    if product.stock_quantity + quantity_change < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock adjustment cannot make stock quantity negative",
        )
    remarks = remarks.strip()
    if not remarks:
        raise HTTPException(status_code=400, detail="Remarks cannot be empty")
    product.stock_quantity += quantity_change
    product.updated_by = current_user.user_id
    history = StockHistory(
        product_id=product.product_id,
        purchase_item_id=None,
        sale_item_id=None,
        change_type="adjustment",
        quantity_change=quantity_change,
        updated_by=current_user.user_id,
        remarks=remarks,
    )
    db.add(history)
    commit_or_409(db, "Unable to adjust stock")
    statement = (
        select(StockHistory)
        .options(
            selectinload(StockHistory.product),
            selectinload(StockHistory.updated_by_user),
        )
        .where(StockHistory.stock_hist_id == history.stock_hist_id)
    )
    return db.scalar(statement)
