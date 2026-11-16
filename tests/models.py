from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

class Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    product_name: str = Field(
        default=None,
        min_length=1,
        max_length=255
    )
    product_description: str | None = None
    category_id: int = Field(default=None, gt=0)
    cost_price: Decimal = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2
    )
    sale_price: Decimal = Field(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2
    )
    reorder_level: int = Field(default=None, ge=0)
    status: Literal["active", "inactive"] = Field(default=None)



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


class CustomerCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=10)
    email: EmailStr
    address: str

class CustomerUpdate(BaseModel):
    customer_name: str = Field(default=None, min_length=1, max_length=255)
    phone: str = Field(default=None,min_length=1, max_length=10)
    email: EmailStr = Field(default=None)
    address: str = Field(default=None)


class SupplierCreate(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=255)
    contact_person: str = Field(max_length=150)
    address: str
    phone: str = Field(min_length=1, max_length=10)
    email: EmailStr


class SupplierUpdate(BaseModel):
    supplier_name: str = Field(default=None, min_length=1, max_length=255)
    contact_person: str = Field(default=None, max_length=150)
    address: str= Field(default=None)
    phone: str = Field(default=None,min_length=1, max_length=10)
    email: EmailStr = Field(default=None)
    status: Literal["active", "inactive"] =Field(default=None)


class ProductCategoryCreate(BaseModel):
    category_name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class ProductCategoryUpdate(BaseModel):
    category_name: str = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
#-------------------------------------------------
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
    supplier_name: str = Field(
        validation_alias=AliasPath("supplier", "supplier_name")
    )
    purchase_date: date | None
    status: Literal["draft", "order_placed", "delivered", "cancelled"]
    created_by: str | None = Field(
        default=None,
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
    sku: str = Field(validation_alias=AliasPath("product", "sku"))
    product_name: str = Field(
        validation_alias=AliasPath("product", "product_name")
    )
    quantity: int
    unit_price: Decimal
    total_price: Decimal

class PurchaseOrderDetailResponse(PurchaseOrderListResponse):
    items: list[PurchaseItemResponse]


#------------------------------------------------------------------------------
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
    customer_name: str = Field(
        validation_alias=AliasPath("customer", "customer_name")
    )
    sale_date: date | None
    status: Literal["draft", "order_placed", "delivered", "cancelled"]
    created_by: str = Field(
        validation_alias=AliasPath("created_by_user", "name")
    )
    updated_by: str | None = Field(
        default=None,
        validation_alias=AliasPath("updated_by_user", "name")
    )
    created_at: datetime
    updated_at: datetime | None

class SaleItemResponse(Response):
    sale_item_id: int
    sku: str = Field(validation_alias=AliasPath("product", "sku"))
    product_name: str = Field(
        validation_alias=AliasPath("product", "product_name")
    )
    quantity: int
    unit_price: Decimal
    total_price: Decimal


class SaleOrderDetailResponse(SaleOrderListResponse):
    items: list[SaleItemResponse]


#---------------------------------------------------------------

def mask_phone(phone: str | None):

    if not phone:
        return None

    digits = "".join(
        char for char in phone
        if char.isdigit()
    )

    if len(digits) <= 4:
        return "*" * len(digits)

    return "*" * (len(digits) - 4) + digits[-4:]


class CustomerSearchResponse(Response):

    customer_id: UUID
    customer_name: str
    phone: str | None

    @field_validator("phone", mode="before")
    @classmethod
    def mask_customer_phone(cls, value):
        return mask_phone(value)

#-----------------------------------------------------------------------------

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

    user_id: UUID
    name: str
    phone: str 
    email: str
    role: Literal["admin", "staff"]
    login_id: str
    status: Literal["active", "inactive"]
    created_by: str | None = Field(default=None,validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    created_at: datetime
    updated_at: datetime | None

class CustomerResponse(Response):

    customer_id: UUID
    customer_name: str
    phone: str 
    email: str 
    address: str 
    created_by: str = Field(validation_alias=AliasPath("created_by_user", "name"))
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    created_at: datetime
    updated_at: datetime | None

class SupplierResponse(Response):

    supplier_id: int
    supplier_name: str
    contact_person: str 
    address: str 
    phone: str 
    email: str 

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

    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))

    created_at: datetime
    updated_at: datetime | None


class StockHistoryResponse(Response):
    stock_hist_id: int
    sku: str = Field(
    validation_alias=AliasPath("product", "sku")
    )

    product_name: str = Field(
        validation_alias=AliasPath("product", "product_name")
    )
    purchase_item_id: int | None
    sale_item_id: int | None
    change_type: Literal[
        "purchase",
        "sale",
        "adjustment",
        "reversal"
    ]

    quantity_change: int
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    updated_at: datetime
    remarks: str | None

class PriceHistoryResponse(Response):
    price_hist_id: int
    sku: str = Field(
    validation_alias=AliasPath("product", "sku")
    )

    product_name: str = Field(
        validation_alias=AliasPath("product", "product_name")
    )

    old_cost_price: Decimal | None
    new_cost_price: Decimal | None

    old_sale_price: Decimal | None
    new_sale_price: Decimal | None

    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))

    updated_at: datetime
    remarks: str | None

class UserHistoryResponse(Response):
    user_hist_id: int
    user_id: UUID
    user_name: str = Field(
    validation_alias=AliasPath("user", "name")
)
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
    customer_id: UUID
    customer_name: str = Field(
    validation_alias=AliasPath("customer", "customer_name")
)

    action: Literal[
        "created",
        "updated"
    ]
    old_data: dict[str, Any] | None
    new_data: dict[str, Any]
    updated_by: str | None = Field(default=None,validation_alias=AliasPath("updated_by_user", "name"))
    updated_at: datetime
    remarks: str | None