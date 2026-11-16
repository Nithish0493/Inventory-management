from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator
from pydantic import BaseModel, ConfigDict, Field
from app.schemas import Response


class PurchaseItemCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=1)

    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty")

        return value


class PurchaseOrderCreate(BaseModel):
    supplier_id: int = Field(gt=0)
    items: list[PurchaseItemCreate] = Field(min_length=1)


class PurchaseOrderUpdate(BaseModel):
    supplier_id: int = Field(default=None, gt=0)
    status: Literal["order_placed", "cancelled"] = None


class PurchaseItemDraft(BaseModel):
    purchase_item_id: int | None = Field(default=None, gt=0)
    sku: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=1)

    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty")

        return value


class PurchaseItemsDraftUpdate(BaseModel):
    items: list[PurchaseItemDraft]


class PurchaseOrderListResponse(Response):
    purchase_id: int
    supplier_id: int
    supplier_name: str = Field(validation_alias=AliasPath("supplier", "supplier_name"))
    purchase_date: date | None
    status: Literal["draft", "order_placed", "delivered", "cancelled"]
    created_by: str | None = Field(
        default=None, validation_alias=AliasPath("created_by_user", "name")
    )
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    created_at: datetime
    updated_at: datetime | None


class PurchaseItemResponse(Response):
    purchase_item_id: int
    sku: str = Field(validation_alias=AliasPath("product", "sku"))
    product_name: str = Field(validation_alias=AliasPath("product", "product_name"))
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class PurchaseOrderDetailResponse(PurchaseOrderListResponse):
    items: list[PurchaseItemResponse]


class SaleItemCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=1)

    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty")

        return value


class SaleOrderCreate(BaseModel):
    customer_id: UUID
    items: list[SaleItemCreate] = Field(min_length=1)


class SaleOrderUpdate(BaseModel):
    customer_id: UUID = Field(default=None)
    status: Literal["order_placed", "cancelled"] = None


class SaleItemDraft(BaseModel):
    sale_item_id: int | None = Field(default=None, gt=0)
    sku: str = Field(min_length=1, max_length=50)
    quantity: int = Field(ge=1)

    @field_validator("sku")
    @classmethod
    def clean_sku(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("SKU cannot be empty")

        return value


class SaleItemsDraftUpdate(BaseModel):
    items: list[SaleItemDraft]


class SaleOrderListResponse(Response):
    sale_id: int
    customer_name: str = Field(validation_alias=AliasPath("customer", "customer_name"))
    sale_date: date | None
    status: Literal["draft", "order_placed", "delivered", "cancelled"]
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    created_at: datetime
    updated_at: datetime | None


class SaleItemResponse(Response):
    sale_item_id: int
    sku: str = Field(validation_alias=AliasPath("product", "sku"))
    product_name: str = Field(validation_alias=AliasPath("product", "product_name"))
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class SaleOrderDetailResponse(SaleOrderListResponse):
    items: list[SaleItemResponse]
