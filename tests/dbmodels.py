def get_active_user(user_id: UUID, db: Session):

    statement = select(User).where(
    User.user_id == user_id,
    User.status == "active"
    )

    user = db.scalar(statement)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive user"
        )

    return user

def get_user_with_audit(user_id: UUID, db: Session) -> User:
    statement = (
        select(User)
        .options(
            selectinload(User.created_by_user),
            selectinload(User.updated_by_user),
        )
        .where(User.user_id == user_id)
    )
    return db.scalar(statement)

def get_admin_user(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can perform this action",
        )

def _old_user_data(user: User) -> dict:
    # Never put password_hash in an audit JSON object.
    return {
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
        "login_id": user.login_id,
        "status": user.status,
    }

def _old_customer_data(customer: Customer) -> dict:
    return {
        "customer_name": customer.customer_name,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
    }

def get_product_with_audit(product_id: int, db: Session) -> Product:
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user),
            selectinload(Product.updated_by_user),
        )
        .where(Product.product_id == product_id)
    )
    return db.scalar(statement)

def get_category_with_audit(category_id: int, db: Session) -> ProductCategory:
    statement = (
        select(ProductCategory)
        .options(
            selectinload(ProductCategory.created_by_user),
            selectinload(ProductCategory.updated_by_user),
        )
        .where(ProductCategory.category_id == category_id)
    )
    return db.scalar(statement)

def get_supplier_with_audit(supplier_id: int, db: Session) -> Supplier:
    statement = (
        select(Supplier)
        .options(
            selectinload(Supplier.created_by_user),
            selectinload(Supplier.updated_by_user),
        )
        .where(Supplier.supplier_id == supplier_id)
    )
    return db.scalar(statement)

def get_customer_with_audit(customer_id: UUID, db: Session) -> Customer:
    statement = (
        select(Customer)
        .options(
            selectinload(Customer.created_by_user),
            selectinload(Customer.updated_by_user),
        )
        .where(Customer.customer_id == customer_id)
    )
    return db.scalar(statement)

def get_purchase_order_with_details(purchase_id: int, db: Session) -> PurchaseOrder:
    statement = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.items).selectinload(PurchaseItem.product),
            selectinload(PurchaseOrder.created_by_user),
            selectinload(PurchaseOrder.updated_by_user),
        )
        .where(PurchaseOrder.purchase_id == purchase_id)
    )
    return db.scalar(statement)

def get_sale_order_with_details(sale_id: int, db: Session) -> SaleOrder:
    statement = (
        select(SaleOrder)
        .options(
            selectinload(SaleOrder.customer),
            selectinload(SaleOrder.items).selectinload(SaleItem.product),
            selectinload(SaleOrder.created_by_user),
            selectinload(SaleOrder.updated_by_user),
        )
        .where(SaleOrder.sale_id == sale_id)
    )
    return db.scalar(statement)

