from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from modules.users.models import User
from modules.customers.models import Customer
from modules.partners.models import Supplier
from modules.inventory.models import Product
from modules.orders.models import PurchaseItem, PurchaseOrder, SaleItem, SaleOrder
from modules.history.models import StockHistory
from modules.orders.schemas import (
    PurchaseItemsDraftUpdate,
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderListResponse,
    PurchaseOrderUpdate,
    SaleItemsDraftUpdate,
    SaleOrderCreate,
    SaleOrderDetailResponse,
    SaleOrderListResponse,
    SaleOrderUpdate,
)


def get_purchase_order_with_details(purchase_id: int, db: Session) -> PurchaseOrder:
    statement = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).selectinload(PurchaseItem.product),
            selectinload(PurchaseOrder.created_by_user),
            selectinload(PurchaseOrder.updated_by_user),
        )
        .where(PurchaseOrder.purchase_id == purchase_id)
    )
    return db.scalar(statement)


def get_sale_order_with_details(sale_id: int, db: Session) -> SaleOrder:
    statement = (
        select(SaleOrder)
        .options(
            selectinload(SaleOrder.customer),
            selectinload(SaleOrder.items).selectinload(SaleItem.product),
            selectinload(SaleOrder.created_by_user),
            selectinload(SaleOrder.updated_by_user),
        )
        .where(SaleOrder.sale_id == sale_id)
    )
    return db.scalar(statement)


def create_purchase_order_service(
    payload: PurchaseOrderCreate, db: Session, current_user: User
):
    try:
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.supplier_id == payload.supplier_id, Supplier.status == "active"
            )
        )
        if supplier is None:
            raise HTTPException(
                status_code=404, detail="Supplier not found or inactive"
            )
        skus = [item.sku for item in payload.items]
        if len(skus) != len(set(skus)):
            raise HTTPException(
                status_code=400, detail="Duplicate products are not allowed"
            )
        purchase_order = PurchaseOrder(
            supplier_id=supplier.supplier_id, created_by=current_user.user_id
        )
        db.add(purchase_order)
        db.flush()
        purchase_items = []
        for item in payload.items:
            product = db.scalar(
                select(Product).where(
                    Product.sku == item.sku, Product.status == "active"
                )
            )
            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Active product not found: {item.sku}"
                )
            purchase_items.append(
                PurchaseItem(
                    purchase_id=purchase_order.purchase_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.cost_price,
                )
            )
        db.add_all(purchase_items)
        db.commit()
        purchase_id = purchase_order.purchase_id
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create purchase order. Check for duplicate or invalid records.",
        )
    except Exception:
        db.rollback()
        raise
    return get_purchase_order_with_details(purchase_order.purchase_id, db)


def update_purchase_order_service(
    purchase_id: int, payload: PurchaseOrderUpdate, db: Session, current_user: User
):
    try:
        purchase_order = db.scalar(
            select(PurchaseOrder)
            .where(PurchaseOrder.purchase_id == purchase_id)
            .with_for_update()
        )
        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        update_data = payload.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        if purchase_order.status in ("delivered", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail="Delivered or cancelled orders cannot be modified",
            )
        
        if "supplier_id" in update_data:
            if purchase_order.status != "draft":
                raise HTTPException(
                    status_code=400, detail="Only draft purchase orders can be modified"
                )
            supplier = db.scalar(
                select(Supplier).where(
                    Supplier.supplier_id == update_data["supplier_id"],
                    Supplier.status == "active",
                )
            )
            if supplier is None:
                raise HTTPException(
                    status_code=404, detail="Supplier not found or inactive"
                )
            purchase_order.supplier_id = supplier.supplier_id
            
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status == "cancelled":
                if purchase_order.status not in ("draft", "order_placed"):
                    raise HTTPException(
                        status_code=400,
                        detail="This purchase order cannot be cancelled",
                    )
                if len(update_data) > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Only status can be updated when cancelling an order",
                    )
                purchase_order.status = "cancelled"
            elif new_status == "order_placed":
                if purchase_order.status != "draft":
                    raise HTTPException(
                        status_code=400,
                        detail="Only draft purchase orders can be placed",
                    )
                item_count = db.scalar(
                    select(func.count())
                    .select_from(PurchaseItem)
                    .where(PurchaseItem.purchase_id == purchase_id)
                )
                if item_count == 0:
                    raise HTTPException(
                        status_code=400, detail="Cannot place an order without items"
                    )
                purchase_order.status = "order_placed"
                purchase_order.purchase_date = date.today()
            else:
                raise HTTPException(status_code=400, detail="Invalid status transition")
        purchase_order.updated_by = current_user.user_id
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to update purchase order")
    except Exception:
        db.rollback()
        raise
    return get_purchase_order_with_details(purchase_id, db)


def update_purchase_order_items_service(
    purchase_id: int, payload: PurchaseItemsDraftUpdate, db: Session, current_user: User
):
    order = db.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.purchase_id == purchase_id)
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status != "draft":
        raise HTTPException(
            status_code=400, detail="Only draft purchase orders can be modified"
        )
    existing = db.scalars(
        select(PurchaseItem)
        .options(selectinload(PurchaseItem.product))
        .where(PurchaseItem.purchase_id == purchase_id)
    ).all()
    existing_map = {item.purchase_item_id: item for item in existing}
    item_ids = [
        item.purchase_item_id
        for item in payload.items
        if item.purchase_item_id is not None
    ]
    skus = [item.sku for item in payload.items]
    if len(item_ids) != len(set(item_ids)):
        raise HTTPException(status_code=400, detail="Duplicate purchase item IDs")
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=400, detail="Duplicate product SKUs")
    new_items = []
    for item in payload.items:
        if item.purchase_item_id is not None:
            old_item = existing_map.get(item.purchase_item_id)
            if old_item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Purchase item {item.purchase_item_id} not found in this order",
                )
            if old_item.product.sku != item.sku:
                raise HTTPException(
                    status_code=400,
                    detail="SKU cannot be changed for an existing purchase item",
                )
            old_item.quantity = item.quantity
        else:
            product = db.scalar(
                select(Product).where(
                    Product.sku == item.sku, Product.status == "active"
                )
            )
            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Active product not found: {item.sku}"
                )
            new_items.append(
                PurchaseItem(
                    purchase_id=purchase_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.cost_price,
                )
            )
    submitted_ids = set(item_ids)
    for item_id, old_item in existing_map.items():
        if item_id not in submitted_ids:
            db.delete(old_item)
    try:
        db.flush()
        db.add_all(new_items)
        order.updated_by = current_user.user_id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to update purchase items")
    return get_purchase_order_with_details(purchase_id, db)


def receive_purchase_order_service(purchase_id: int, db: Session, current_user: User):
    try:
        purchase_order = db.scalar(
            select(PurchaseOrder)
            .where(PurchaseOrder.purchase_id == purchase_id)
            .with_for_update()
        )
        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        if purchase_order.status != "order_placed":
            raise HTTPException(
                status_code=400, detail="Only placed purchase orders can be received"
            )
        purchase_items = db.scalars(
            select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id)
        ).all()
        if not purchase_items:
            raise HTTPException(status_code=400, detail="Purchase order has no items")
        product_ids = sorted({item.product_id for item in purchase_items})
        products = db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
        ).all()
        product_map = {product.product_id: product for product in products}
        if len(product_map) != len(product_ids):
            raise HTTPException(
                status_code=409, detail="One or more products no longer exist"
            )
        history_records = []
        for item in purchase_items:
            product = product_map[item.product_id]
            product.stock_quantity += item.quantity
            history_records.append(
                StockHistory(
                    product_id=product.product_id,
                    purchase_item_id=item.purchase_item_id,
                    sale_item_id=None,
                    change_type="purchase",
                    quantity_change=item.quantity,
                    updated_by=current_user.user_id,
                    remarks=f"Goods received for purchase order {purchase_id}",
                )
            )
        db.add_all(history_records)
        purchase_order.status = "delivered"
        purchase_order.updated_by = current_user.user_id
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to receive purchase order")
    except Exception:
        db.rollback()
        raise
    return get_purchase_order_with_details(purchase_id, db)


def get_purchase_orders_service(
    status: Literal["draft", "order_placed", "delivered", "cancelled"] | None,
    supplier_id: int | None,
    limit: int,
    offset: int,
    db: Session,
    current_user: User,
):
    statement = select(PurchaseOrder).options(
        selectinload(PurchaseOrder.supplier),
        selectinload(PurchaseOrder.created_by_user),
        selectinload(PurchaseOrder.updated_by_user),
    )
    if status is not None:
        statement = statement.where(PurchaseOrder.status == status)
    else:
        statement = statement.where(PurchaseOrder.status != "cancelled")
    if supplier_id is not None:
        statement = statement.where(PurchaseOrder.supplier_id == supplier_id)
    statement = (
        statement.order_by(
            PurchaseOrder.created_at.desc(), PurchaseOrder.purchase_id.desc()
        )
        .limit(limit)
        .offset(offset)
    )
    purchase_orders = db.scalars(statement).all()
    return purchase_orders


def get_purchase_order_service(purchase_id: int, db: Session, current_user: User):
    purchase_order = get_purchase_order_with_details(purchase_id, db)
    if purchase_order is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return purchase_order


def create_sale_order_service(
    payload: SaleOrderCreate, db: Session, current_user: User
):
    try:
        customer = db.scalar(
            select(Customer).where(Customer.customer_id == payload.customer_id)
        )
        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")
        skus = [item.sku for item in payload.items]
        if len(skus) != len(set(skus)):
            raise HTTPException(
                status_code=400, detail="Duplicate products are not allowed"
            )
        sale_order = SaleOrder(
            customer_id=customer.customer_id, created_by=current_user.user_id
        )
        db.add(sale_order)
        db.flush()
        sale_items = []
        for item in payload.items:
            product = db.scalar(
                select(Product).where(
                    Product.sku == item.sku, Product.status == "active"
                )
            )
            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Active product not found: {item.sku}"
                )
            sale_items.append(
                SaleItem(
                    sale_id=sale_order.sale_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.sale_price,
                )
            )
        db.add_all(sale_items)
        db.commit()
        sale_id = sale_order.sale_id
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to create sale order")
    except Exception:
        db.rollback()
        raise
    return get_sale_order_with_details(sale_order.sale_id, db)


def update_sale_order_service(
    sale_id: int, payload: SaleOrderUpdate, db: Session, current_user: User
):
    try:
        sale_order = db.scalar(
            select(SaleOrder).where(SaleOrder.sale_id == sale_id).with_for_update()
        )
        if sale_order is None:
            raise HTTPException(status_code=404, detail="Sale order not found")
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        if sale_order.status in ("delivered", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail="Delivered or cancelled orders cannot be modified",
            )
        if "customer_id" in update_data:
            if sale_order.status != "draft":
                raise HTTPException(
                    status_code=400, detail="Only draft sale orders can be modified"
                )
            customer = db.scalar(
                select(Customer).where(
                    Customer.customer_id == update_data["customer_id"]
                )
            )
            if customer is None:
                raise HTTPException(status_code=404, detail="Customer not found")
            sale_order.customer_id = customer.customer_id
        if "status" in update_data:
            new_status = update_data["status"]
            if new_status == "cancelled":
                if sale_order.status not in ("draft", "order_placed"):
                    raise HTTPException(
                        status_code=400, detail="This sale order cannot be cancelled"
                    )
                if len(update_data) > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Only status can be updated when cancelling an order",
                    )
                sale_order.status = "cancelled"
            elif new_status == "order_placed":
                if sale_order.status != "draft":
                    raise HTTPException(
                        status_code=400, detail="Only draft sale orders can be placed"
                    )
                item_count = db.scalar(
                    select(func.count())
                    .select_from(SaleItem)
                    .where(SaleItem.sale_id == sale_id)
                )
                if item_count == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot place a sale order without items",
                    )
                sale_order.status = "order_placed"
            else:
                raise HTTPException(status_code=400, detail="Invalid status transition")
        sale_order.updated_by = current_user.user_id
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to update sale order")
    except Exception:
        db.rollback()
        raise
    return get_sale_order_with_details(sale_id, db)


def update_sale_order_items_service(
    sale_id: int, payload: SaleItemsDraftUpdate, db: Session, current_user: User
):
    try:
        sale_order = db.scalar(
            select(SaleOrder).where(SaleOrder.sale_id == sale_id).with_for_update()
        )
        if sale_order is None:
            raise HTTPException(status_code=404, detail="Sale order not found")
        if sale_order.status != "draft":
            raise HTTPException(
                status_code=400, detail="Only draft sale orders can be modified"
            )
        existing_items = db.scalars(
            select(SaleItem)
            .options(selectinload(SaleItem.product))
            .where(SaleItem.sale_id == sale_id)
        ).all()
        existing_map = {item.sale_item_id: item for item in existing_items}
        item_ids = [
            item.sale_item_id for item in payload.items if item.sale_item_id is not None
        ]
        skus = [item.sku for item in payload.items]
        if len(item_ids) != len(set(item_ids)):
            raise HTTPException(status_code=400, detail="Duplicate sale item IDs")
        if len(skus) != len(set(skus)):
            raise HTTPException(status_code=400, detail="Duplicate product SKUs")
        new_items = []
        for item in payload.items:
            if item.sale_item_id is not None:
                existing_item = existing_map.get(item.sale_item_id)
                if existing_item is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Sale item {item.sale_item_id} not found in this order",
                    )
                if item.sku != existing_item.product.sku:
                    raise HTTPException(
                        status_code=400,
                        detail="SKU cannot be changed for an existing sale item",
                    )
                existing_item.quantity = item.quantity
            else:
                product = db.scalar(
                    select(Product).where(
                        Product.sku == item.sku, Product.status == "active"
                    )
                )
                if product is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Active product with SKU {item.sku} not found",
                    )
                new_items.append(
                    SaleItem(
                        sale_id=sale_id,
                        product_id=product.product_id,
                        quantity=item.quantity,
                        unit_price=product.sale_price,
                    )
                )
        submitted_ids = set(item_ids)
        for item_id, existing_item in existing_map.items():
            if item_id not in submitted_ids:
                db.delete(existing_item)
        db.flush()
        db.add_all(new_items)
        sale_order.updated_by = current_user.user_id
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to update sale items")
    except Exception:
        db.rollback()
        raise
    return get_sale_order_with_details(sale_id, db)


def complete_sale_order_service(sale_id: int, db: Session, current_user: User):
    try:
        sale_order = db.scalar(
            select(SaleOrder).where(SaleOrder.sale_id == sale_id).with_for_update()
        )
        if sale_order is None:
            raise HTTPException(status_code=404, detail="Sale order not found")
        if sale_order.status != "order_placed":
            raise HTTPException(
                status_code=400, detail="Only placed sale orders can be completed"
            )
        sale_items = db.scalars(
            select(SaleItem).where(SaleItem.sale_id == sale_id)
        ).all()
        if not sale_items:
            raise HTTPException(status_code=400, detail="Sale order has no items")
        product_ids = sorted({item.product_id for item in sale_items})
        products = db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
        ).all()
        product_map = {product.product_id: product for product in products}
        if len(product_map) != len(product_ids):
            raise HTTPException(
                status_code=409, detail="One or more products no longer exist"
            )
        for item in sale_items:
            product = product_map[item.product_id]
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for SKU {product.sku}. Available: {product.stock_quantity}, Required: {item.quantity}",
                )
        history_records = []
        for item in sale_items:
            product = product_map[item.product_id]
            product.stock_quantity -= item.quantity
            history_records.append(
                StockHistory(
                    product_id=product.product_id,
                    purchase_item_id=None,
                    sale_item_id=item.sale_item_id,
                    change_type="sale",
                    quantity_change=-item.quantity,
                    updated_by=current_user.user_id,
                    remarks=f"Sale completed for sale order {sale_id}",
                )
            )
        db.add_all(history_records)
        sale_order.status = "delivered"
        sale_order.sale_date = date.today()
        sale_order.updated_by = current_user.user_id
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to complete sale order")
    except Exception:
        db.rollback()
        raise
    return get_sale_order_with_details(sale_id, db)


def get_sale_orders_service(
    status: Literal["draft", "order_placed", "delivered", "cancelled"] | None,
    customer_id: UUID | None,
    limit: int,
    offset: int,
    db: Session,
    current_user: User,
):
    statement = select(SaleOrder).options(
        selectinload(SaleOrder.customer),
        selectinload(SaleOrder.created_by_user),
        selectinload(SaleOrder.updated_by_user),
    )
    if status is not None:
        statement = statement.where(SaleOrder.status == status)
    else:
        statement = statement.where(SaleOrder.status != "cancelled")
    if customer_id is not None:
        statement = statement.where(SaleOrder.customer_id == customer_id)
    statement = (
        statement.order_by(SaleOrder.created_at.desc(), SaleOrder.sale_id.desc())
        .limit(limit)
        .offset(offset)
    )
    sale_orders = db.scalars(statement).all()
    return sale_orders


def get_sale_order_service(sale_id: int, db: Session, current_user: User):
    sale_order = get_sale_order_with_details(sale_id, db)
    if sale_order is None:
        raise HTTPException(status_code=404, detail="Sale order not found")
    return sale_order
