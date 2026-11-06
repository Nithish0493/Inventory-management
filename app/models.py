from datetime import date, datetime
from typing import Literal,Any
import uuid
from pydantic import BaseModel, ConfigDict, Field,AliasPath,EmailStr
from decimal import Decimal

class ProductCreate(BaseModel):

    sku: str = Field(min_length=1, max_length=50)
    product_name: str = Field(min_length=1, max_length=255)
    product_description: str | None = None
    category_id: int = Field(gt=0)
    cost_price: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2
    )
    sale_price: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2
    )
    reorder_level: int = Field(default=0, ge=0)



class Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)


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
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    created_at: datetime
    updated_at: datetime | None

class UserResponse(Response):

    user_id: uuid.UUID
    name: str
    phone: str | None
    email: str
    role: Literal["admin", "staff"]
    login_id: str
    status: Literal["active", "inactive"]
    created_by: str | None = Field(default=None,validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    created_at: datetime
    updated_at: datetime | None

class CustomerResponse(Response):

    customer_id: uuid.UUID
    customer_name: str
    phone: str | None
    email: str | None
    address: str | None
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    created_at: datetime
    updated_at: datetime | None

class SupplierResponse(Response):

    supplier_id: int
    supplier_name: str
    contact_person: str | None
    address: str | None
    phone: str | None
    email: str | None

    status: Literal["active", "inactive"]

    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))

    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))

    created_at: datetime
    updated_at: datetime | None

class ProductCategoryResponse(Response):

    category_id: int
    category_name: str
    description: str | None
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))

    updated_by: str | None = Field(
        default=None,
        validation_alias=AliasPath("updated_by_user", "name")
    )

    created_at: datetime
    updated_at: datetime | None

class PurchaseOrderResponse(Response):

    purchase_id: int
    supplier_id: int
    purchase_date: date
    status: Literal[
        "draft",
        "order_placed",
        "delivered",
        "cancelled"
    ]

    created_by: str = Field(
        validation_alias=AliasPath("created_by_user", "name")
    )

    updated_by: str | None = Field(
        default=None,
        validation_alias=AliasPath("updated_by_user", "name")
    )

    created_at: datetime
    updated_at: datetime | None

class PurchaseItemResponse(Response):

    purchase_item_id: int
    purchase_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal

class SaleOrderResponse(Response):

    sale_id: int
    customer_id: uuid.UUID
    sale_date: date
    status: Literal[
        "draft",
        "order_placed",
        "delivered",
        "cancelled"
    ]

    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))

    created_at: datetime
    updated_at: datetime | None

class SaleItemResponse(Response):
    sale_item_id: int
    sale_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal

class StockHistoryResponse(Response):
    stock_hist_id: int
    product_id: int
    purchase_item_id: int | None
    sale_item_id: int | None
    change_type: Literal[
        "purchase",
        "sale",
        "adjustment",
        "reversal"
    ]

    quantity_change: int
    updated_by: str = Field(validation_alias=AliasPath("updated_by_user", "name"))
    updated_at: datetime
    remarks: str | None

class PriceHistoryResponse(Response):
    price_hist_id: int
    product_id: int

    old_cost_price: Decimal | None
    new_cost_price: Decimal | None

    old_sale_price: Decimal | None
    new_sale_price: Decimal | None

    updated_by: str = Field(
        validation_alias=AliasPath("updated_by_user", "name")
    )

    updated_at: datetime
    remarks: str | None

class UserHistoryResponse(Response):
    user_hist_id: int
    user_id: uuid.UUID
    action: Literal[
        "created",
        "updated",
        "password_changed"
    ]

    old_data: dict[str, Any] | None
    new_data: dict[str, Any] | None

    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))

    updated_at: datetime
    remarks: str | None

class CustomerHistoryResponse(Response):
    customer_hist_id: int
    customer_id: uuid.UUID

    action: Literal[
        "created",
        "updated"
    ]
    old_data: dict[str, Any] | None
    new_data: dict[str, Any]
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    updated_at: datetime
    remarks: str | None