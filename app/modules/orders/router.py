from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from modules.users.models import User
from modules.orders.models import PurchaseItem, PurchaseOrder, SaleItem, SaleOrder
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
from modules.orders.service import (
    create_purchase_order_service,
    update_purchase_order_service,
    update_purchase_order_items_service,
    receive_purchase_order_service,
    get_purchase_orders_service,
    get_purchase_order_service,
    create_sale_order_service,
    update_sale_order_service,
    update_sale_order_items_service,
    complete_sale_order_service,
    get_sale_orders_service,
    get_sale_order_service,
)

router = APIRouter()


@router.post(
    "/purchase-orders", response_model=PurchaseOrderDetailResponse, status_code=201
)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_purchase_order_service(
        payload=payload, db=db, current_user=current_user
    )


@router.patch(
    "/purchase-orders/{purchase_id}", response_model=PurchaseOrderDetailResponse
)
def update_purchase_order(
    purchase_id: int,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_purchase_order_service(
        purchase_id=purchase_id, payload=payload, db=db, current_user=current_user
    )


@router.patch(
    "/purchase-orders/{purchase_id}/items", response_model=PurchaseOrderDetailResponse
)
def update_purchase_order_items(
    purchase_id: int,
    payload: PurchaseItemsDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_purchase_order_items_service(
        purchase_id=purchase_id, payload=payload, db=db, current_user=current_user
    )


@router.post(
    "/purchase-orders/{purchase_id}/receive", response_model=PurchaseOrderDetailResponse
)
def receive_purchase_order(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return receive_purchase_order_service(
        purchase_id=purchase_id, db=db, current_user=current_user
    )


@router.get("/purchase-orders", response_model=list[PurchaseOrderListResponse])
def get_purchase_orders(
    status: Literal["draft", "order_placed", "delivered", "cancelled"] | None = Query(
        default=None
    ),
    supplier_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_purchase_orders_service(
        status=status,
        supplier_id=supplier_id,
        limit=limit,
        offset=offset,
        db=db,
        current_user=current_user,
    )


@router.get(
    "/purchase-orders/{purchase_id}", response_model=PurchaseOrderDetailResponse
)
def get_purchase_order(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_purchase_order_service(
        purchase_id=purchase_id, db=db, current_user=current_user
    )


@router.post("/sale-orders", response_model=SaleOrderDetailResponse, status_code=201)
def create_sale_order(
    payload: SaleOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_sale_order_service(payload=payload, db=db, current_user=current_user)


@router.patch("/sale-orders/{sale_id}", response_model=SaleOrderDetailResponse)
def update_sale_order(
    sale_id: int,
    payload: SaleOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_sale_order_service(
        sale_id=sale_id, payload=payload, db=db, current_user=current_user
    )


@router.patch("/sale-orders/{sale_id}/items", response_model=SaleOrderDetailResponse)
def update_sale_order_items(
    sale_id: int,
    payload: SaleItemsDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_sale_order_items_service(
        sale_id=sale_id, payload=payload, db=db, current_user=current_user
    )


@router.post("/sale-orders/{sale_id}/complete", response_model=SaleOrderDetailResponse)
def complete_sale_order(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return complete_sale_order_service(
        sale_id=sale_id, db=db, current_user=current_user
    )


@router.get("/sale-orders", response_model=list[SaleOrderListResponse])
def get_sale_orders(
    status: Literal["draft", "order_placed", "delivered", "cancelled"] | None = Query(
        default=None
    ),
    customer_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_sale_orders_service(
        status=status,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
        db=db,
        current_user=current_user,
    )


@router.get("/sale-orders/{sale_id}", response_model=SaleOrderDetailResponse)
def get_sale_order(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_sale_order_service(sale_id=sale_id, db=db, current_user=current_user)
