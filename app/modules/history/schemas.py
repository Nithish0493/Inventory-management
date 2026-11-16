from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import AliasPath, EmailStr, Field, field_validator

from app.schemas import Response


class StockHistoryResponse(Response):
    stock_hist_id: int
    sku: str = Field(validation_alias=AliasPath("product", "sku"))

    product_name: str = Field(validation_alias=AliasPath("product", "product_name"))
    purchase_item_id: int | None
    sale_item_id: int | None
    change_type: Literal["purchase", "sale", "adjustment", "reversal"]

    quantity_change: int
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    updated_at: datetime
    remarks: str | None


class PriceHistoryResponse(Response):
    price_hist_id: int
    sku: str = Field(validation_alias=AliasPath("product", "sku"))

    product_name: str = Field(validation_alias=AliasPath("product", "product_name"))

    old_cost_price: Decimal | None
    new_cost_price: Decimal | None

    old_sale_price: Decimal | None
    new_sale_price: Decimal | None

    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )

    updated_at: datetime
    remarks: str | None


class UserHistoryResponse(Response):
    user_hist_id: int
    user_id: UUID
    user_name: str = Field(validation_alias=AliasPath("user", "name"))
    action: Literal["created", "updated", "password_changed"]

    old_data: dict[str, Any] | None
    new_data: dict[str, Any] | None

    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )

    updated_at: datetime
    remarks: str | None


class CustomerHistoryResponse(Response):
    customer_hist_id: int
    customer_id: UUID
    customer_name: str = Field(validation_alias=AliasPath("customer", "customer_name"))

    action: Literal["created", "updated"]
    old_data: dict[str, Any] | None
    new_data: dict[str, Any]
    updated_by: str | None = Field(
        default=None, validation_alias=AliasPath("updated_by_user", "name")
    )
    updated_at: datetime
    remarks: str | None
