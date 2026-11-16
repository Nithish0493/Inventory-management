from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from modules.users.models import User
from modules.users.schemas import UserCreate, UserResponse, UserUpdate
from modules.users.service import (
    create_user_service,
    UserAlreadyExistsError,
    get_user_service,
    get_users_service,
    update_user_service,
)

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    try:
        return create_user_service(
            payload=payload,
            db=db,
            created_by=current_user.user_id,
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Email or login ID already exists",
        )


@router.get("/users/{target_user_id}", response_model=UserResponse)
def get_user(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_service(
        target_user_id=target_user_id, db=db, current_user=current_user
    )


@router.get("/users", response_model=list[UserResponse])
def get_users(
    status: Literal["active", "inactive"] | None = None,
    role: Literal["admin", "staff"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_users_service(
        status=status,
        role=role,
        limit=limit,
        offset=offset,
        db=db,
        current_user=current_user,
    )


@router.patch("/users/{target_user_id}", response_model=UserResponse, status_code=200)
def update_user(
    target_user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    return update_user_service(
        target_user_id=target_user_id, payload=payload, db=db, current_user=current_user
    )
