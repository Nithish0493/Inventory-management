from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from modules.users.models import User
from modules.partners.models import Supplier
from modules.partners.schemas import SupplierCreate, SupplierResponse, SupplierUpdate
from modules.partners.service import (
    create_supplier_service,
    get_suppliers_service,
    get_supplier_service,
    update_supplier_service,
)

router = APIRouter()


@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_supplier_service(payload=payload, db=db, current_user=current_user)


@router.get("/suppliers", response_model=list[SupplierResponse])
def get_suppliers(
    status: Literal["active", "inactive"] | None = None,
    q: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_suppliers_service(
        status=status, q=q, limit=limit, offset=offset, db=db, current_user=current_user
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_supplier_service(
        supplier_id=supplier_id, db=db, current_user=current_user
    )


@router.patch(
    "/suppliers/{target_supplier_id}", response_model=SupplierResponse, status_code=200
)
def update_supplier(
    target_supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_supplier_service(
        target_supplier_id=target_supplier_id,
        payload=payload,
        db=db,
        current_user=current_user,
    )
