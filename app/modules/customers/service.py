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
from modules.history.models import CustomerHistory
from modules.customers.schemas import (
    CustomerCreate,
    CustomerResponse,
    CustomerSearchResponse,
    CustomerUpdate,
)


def _old_customer_data(customer: Customer) -> dict:
    return {
        "customer_name": customer.customer_name,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
    }


def get_customer_with_audit(customer_id: UUID, db: Session) -> Customer:
    statement = (
        select(Customer)
        .options(
            selectinload(Customer.created_by_user),
            selectinload(Customer.updated_by_user),
        )
        .where(Customer.customer_id == customer_id)
    )
    return db.scalar(statement)


def create_customer_service(payload: CustomerCreate, db: Session, current_user: User):
    new_customer = Customer(**payload.model_dump(), created_by=current_user.user_id)
    try:
        db.add(new_customer)
        db.flush()
        db.add(
            CustomerHistory(
                customer_id=new_customer.customer_id,
                action="created",
                old_data=None,
                new_data=_old_customer_data(new_customer),
                updated_by=current_user.user_id,
                remarks="Customer record created",
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create customer. Database constraint violated.",
        )
    db.refresh(new_customer)
    return get_customer_with_audit(new_customer.customer_id, db)


def get_customers_service(
    q: str | None, limit: int, offset: int, db: Session, current_user: User
):
    statement = select(Customer).options(
        selectinload(Customer.created_by_user), selectinload(Customer.updated_by_user)
    )
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Customer.customer_name.ilike(term),
                Customer.phone.ilike(term),
                Customer.email.ilike(term),
            )
        )
    statement = statement.order_by(Customer.customer_name).limit(limit).offset(offset)
    return db.scalars(statement).all()


def search_customers_service(
    q: str, limit: int, offset: int, db: Session, current_user: User
):
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Search term cannot be empty")
    term = f"%{q}%"
    statement = (
        select(Customer)
        .where(or_(Customer.customer_name.ilike(term), Customer.phone.ilike(term)))
        .order_by(Customer.customer_name)
        .limit(limit)
        .offset(offset)
    )
    customers = db.scalars(statement).all()
    return customers


def get_customer_service(customer_id: UUID, db: Session, current_user: User):
    customer = get_customer_with_audit(customer_id, db)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def update_customer_service(
    target_customer_id: UUID, payload: CustomerUpdate, db: Session, current_user: User
):
    statement = (
        select(Customer)
        .where(Customer.customer_id == target_customer_id)
        .with_for_update()
    )
    target_customer = db.scalar(statement)
    if target_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    old_data = _old_customer_data(target_customer)
    update_data["updated_by"] = current_user.user_id
    for field, value in update_data.items():
        setattr(target_customer, field, value)
    try:
        db.add(
            CustomerHistory(
                customer_id=target_customer.customer_id,
                action="updated",
                old_data=old_data,
                new_data=_old_customer_data(target_customer),
                updated_by=current_user.user_id,
                remarks="Customer details updated",
            )
        )
        db.commit()
    except IntegrityError:

        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Customer email already exists or a database constraint was violated",
        )
    
    db.refresh(target_customer)
    return get_customer_with_audit(target_customer_id, db)
