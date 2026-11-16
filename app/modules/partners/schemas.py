from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator
from pydantic import BaseModel, ConfigDict, Field
from app.schemas import Response


class SupplierCreate(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=255)
    contact_person: str = Field(max_length=150)
    address: str
    phone: str = Field(min_length=1, max_length=10)
    email: EmailStr


class SupplierUpdate(BaseModel):
    supplier_name: str = Field(default=None, min_length=1, max_length=255)
    contact_person: str = Field(default=None, max_length=150)
    address: str = Field(default=None)
    phone: str = Field(default=None, min_length=1, max_length=10)
    email: EmailStr = Field(default=None)
    status: Literal["active", "inactive"] = Field(default=None)


class SupplierResponse(Response):

    supplier_id: int
    supplier_name: str
    contact_person: str
    address: str
    phone: str
    email: str

    status: Literal["active", "inactive"]

    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))

    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )

    created_at: datetime
    updated_at: datetime | None
