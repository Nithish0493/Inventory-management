from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator
from pydantic import BaseModel, ConfigDict, Field
from app.schemas import Response


class ProductCreate(BaseModel):
    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty")

        return value

    sku: str = Field(min_length=1, max_length=50)
    product_name: str = Field(min_length=1, max_length=255)
    product_description: str | None = None
    category_id: int = Field(gt=0)
    cost_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    sale_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    reorder_level: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty")

        return value

    sku: str = Field(default=None, min_length=1, max_length=50)
    product_name: str = Field(default=None, min_length=1, max_length=255)
    product_description: str | None = None
    category_id: int = Field(default=None, gt=0)
    cost_price: Decimal = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    sale_price: Decimal = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    reorder_level: int = Field(default=None, ge=0)
    status: Literal["active", "inactive"] = Field(default=None)


class ProductResponse(Response):

    sku: str
    product_name: str
    product_description: str | None
    category_id: int
    cost_price: Decimal
    sale_price: Decimal
    stock_quantity: int
    reorder_level: int
    status: Literal["active", "inactive"]
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    created_at: datetime
    updated_at: datetime | None


class ProductCategoryCreate(BaseModel):
    category_name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class ProductCategoryUpdate(BaseModel):
    category_name: str = Field(default=None, min_length=1, max_length=100)
    description: str | None = None


class ProductCategoryResponse(Response):

    category_id: int
    category_name: str
    description: str | None
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))

    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )

    created_at: datetime
    updated_at: datetime | None
