from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from modules.users.models import User
from modules.history.models import UserHistory
from modules.users.schemas import UserCreate, UserResponse, UserUpdate
from authentication.security import hash_password


class UserAlreadyExistsError(Exception):
    pass


def get_user_with_audit(user_id: UUID, db: Session) -> User:
    statement = (
        select(User)
        .options(selectinload(User.created_by_user), selectinload(User.updated_by_user))
        .where(User.user_id == user_id)
    )
    return db.scalar(statement)


def _old_user_data(user: User) -> dict:
    return {
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "login_id": user.login_id,
        "status": user.status,
    }


def create_user_service(payload: UserCreate, db: Session, created_by: UUID):
    user_data = payload.model_dump(exclude={"password"})

    new_user = User(
        **user_data,
        password_hash=hash_password(payload.password),
        created_by=created_by,
    )

    try:
        db.add(new_user)
        db.flush()

        db.add(
            UserHistory(
                user_id=new_user.user_id,
                action="created",
                old_data=None,
                new_data=_old_user_data(new_user),
                updated_by=created_by,
                remarks="User account created",
            )
        )

        db.commit()
        db.refresh(new_user)

    except IntegrityError as e:
        db.rollback()
        raise UserAlreadyExistsError from e

    return get_user_with_audit(new_user.user_id, db)


def get_user_service(target_user_id: UUID, db: Session, current_user: User):
    user = get_user_with_audit(target_user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_users_service(
    status: Literal["active", "inactive"] | None,
    role: Literal["admin", "staff"] | None,
    limit: int,
    offset: int,
    db: Session,
    current_user: User,
):
    statement = select(User).options(
        selectinload(User.created_by_user), selectinload(User.updated_by_user)
    )
    if status is not None:
        statement = statement.where(User.status == status)
    if role is not None:
        statement = statement.where(User.role == role)
    statement = (
        statement.order_by(User.created_at.desc(), User.user_id)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()


def update_user_service(
    target_user_id: UUID, payload: UserUpdate, db: Session, current_user: User
):
    target_user = db.scalar(
        select(User).where(User.user_id == target_user_id).with_for_update()
    )

    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    if target_user.user_id == current_user.user_id and (
        update_data.get("status") == "inactive" or update_data.get("role") == "staff"
    ):
        raise HTTPException(
            status_code=400, detail="You cannot deactivate or demote your own account"
        )

    old_data = _old_user_data(target_user)
    password_was_changed = "password" in update_data

    if password_was_changed:
        new_password = update_data.pop("password")
        target_user.password_hash = hash_password(new_password)

    update_data["updated_by"] = current_user.user_id

    for field, value in update_data.items():
        setattr(target_user, field, value)

    try:
        db.add(
            UserHistory(
                user_id=target_user.user_id,
                action="updated",
                old_data=old_data,
                new_data=_old_user_data(target_user),
                updated_by=current_user.user_id,
                remarks="User details updated",
            )
        )
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email or login ID already exists, or a database constraint was violated",
        )

    db.refresh(target_user)
    return get_user_with_audit(target_user.user_id, db)
