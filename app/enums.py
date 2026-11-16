from app.database import Base
from sqlalchemy.dialects.postgresql import ENUM

user_role_enum = ENUM(
    "admin",
    "staff",
    name="user_role",
    metadata=Base.metadata,
)

purchase_status_enum = ENUM(
    "draft",
    "order_placed",
    "delivered",
    "cancelled",
    name="purchase_status",
    metadata=Base.metadata,
)

sale_status_enum = ENUM(
    "draft",
    "order_placed",
    "delivered",
    "cancelled",
    name="sale_status",
    metadata=Base.metadata,
)

record_status_enum = ENUM(
    "active",
    "inactive",
    name="record_status",
    metadata=Base.metadata,
)

change_type_enum = ENUM(
    "purchase",
    "sale",
    "adjustment",
    "reversal",
    name="change_type",
    metadata=Base.metadata,
)

record_action_enum = ENUM(
    "created",
    "updated",
    "password_changed",
    name="record_action",
    metadata=Base.metadata,
)