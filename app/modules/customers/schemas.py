from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator
from pydantic import BaseModel, ConfigDict, Field
from app.schemas import Response

from app.schemas import mask_phone


class CustomerCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=10)
    email: EmailStr
    address: str


class CustomerUpdate(BaseModel):
    customer_name: str = Field(default=None, min_length=1, max_length=255)
    phone: str = Field(default=None, min_length=1, max_length=10)
    email: EmailStr = Field(default=None)
    address: str = Field(default=None)


class CustomerSearchResponse(Response):

    customer_id: UUID
    customer_name: str
    phone: str | None

    @field_validator("phone", mode="before")
    @classmethod
    def mask_customer_phone(cls, value):
        return mask_phone(value)


class CustomerResponse(Response):

    customer_id: UUID
    customer_name: str
    phone: str
    email: str
    address: str
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    created_at: datetime
    updated_at: datetime | None
