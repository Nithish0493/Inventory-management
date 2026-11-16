from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator
from pydantic import BaseModel, ConfigDict, Field
from app.schemas import Response


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=1, max_length=10)
    email: EmailStr
    role: Literal["admin", "staff"]
    login_id: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: str = Field(default=None, min_length=2, max_length=255)
    phone: str = Field(default=None, min_length=1, max_length=10)
    email: EmailStr = Field(default=None)
    role: Literal["admin", "staff"] = Field(default=None)
    password: str = Field(default=None, min_length=8)
    status: Literal["active", "inactive"] = Field(default=None)


class UserResponse(Response):

    user_id: UUID
    name: str
    phone: str
    email: str
    role: Literal["admin", "staff"]
    login_id: str
    status: Literal["active", "inactive"]
    created_by: str | None = Field(
        default=None, validation_alias=AliasPath("created_by_user", "name")
    )
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    created_at: datetime
    updated_at: datetime | None
