from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from modules.users.models import User
from modules.customers.models import Customer
from modules.customers.schemas import (
    CustomerCreate,
    CustomerResponse,
    CustomerSearchResponse,
    CustomerUpdate,
)
from modules.customers.service import (
    create_customer_service,
    get_customers_service,
    search_customers_service,
    get_customer_service,
    update_customer_service,
)

router = APIRouter()


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_customer_service(payload=payload, db=db, current_user=current_user)


@router.get("/customers", response_model=list[CustomerResponse])
def get_customers(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_customers_service(
        q=q, limit=limit, offset=offset, db=db, current_user=current_user
    )


@router.get("/customers/search", response_model=list[CustomerSearchResponse])
def search_customers(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=20, ge=1, le=20),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_customers_service(
        q=q, limit=limit, offset=offset, db=db, current_user=current_user
    )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_customer_service(
        customer_id=customer_id, db=db, current_user=current_user
    )


@router.patch(
    "/customers/{target_customer_id}", response_model=CustomerResponse, status_code=200
)
def update_customer(
    target_customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_customer_service(
        target_customer_id=target_customer_id,
        payload=payload,
        db=db,
        current_user=current_user,
    )
