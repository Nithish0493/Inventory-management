from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from modules.users.models import User
from modules.partners.models import Supplier
from modules.partners.schemas import SupplierCreate, SupplierResponse, SupplierUpdate


def get_supplier_with_audit(supplier_id: int, db: Session) -> Supplier:
    statement = (
        select(Supplier)
        .options(
            selectinload(Supplier.created_by_user),
            selectinload(Supplier.updated_by_user),
        )
        .where(Supplier.supplier_id == supplier_id)
    )
    return db.scalar(statement)


def create_supplier_service(payload: SupplierCreate, db: Session, current_user: User):
    new_supplier = Supplier(**payload.model_dump(), created_by=current_user.user_id)
    try:
        db.add(new_supplier)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create supplier. Database constraint violated.",
        )
    db.refresh(new_supplier)
    return get_supplier_with_audit(new_supplier.supplier_id, db)


def get_suppliers_service(
    status: Literal["active", "inactive"] | None,
    q: str | None,
    limit: int,
    offset: int,
    db: Session,
    current_user: User,
):
    statement = select(Supplier).options(
        selectinload(Supplier.created_by_user), selectinload(Supplier.updated_by_user)
    )
    if status is not None:
        statement = statement.where(Supplier.status == status)
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Supplier.supplier_name.ilike(term),
                Supplier.contact_person.ilike(term),
                Supplier.phone.ilike(term),
            )
        )
    statement = statement.order_by(Supplier.supplier_name).limit(limit).offset(offset)
    return db.scalars(statement).all()


def get_supplier_service(supplier_id: int, db: Session, current_user: User):
    supplier = get_supplier_with_audit(supplier_id, db)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


def update_supplier_service(
    target_supplier_id: int, payload: SupplierUpdate, db: Session, current_user: User
):
    statement = (
        select(Supplier)
        .where(Supplier.supplier_id == target_supplier_id)
        .with_for_update()
    )
    target_supplier = db.scalar(statement)
    if target_supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    update_data["updated_by"] = current_user.user_id
    for field, value in update_data.items():
        setattr(target_supplier, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Supplier email already exists or a database constraint was violated",
        )
    db.refresh(target_supplier)
    return get_supplier_with_audit(target_supplier_id, db)
