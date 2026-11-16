from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload



from pwdlib import PasswordHash

from app.database import get_db
from authentication.dependencies import get_current_user, require_roles
from authentication.security import hash_password
from tests.database_models import (
    Customer,
    CustomerHistory,
    PriceHistory,
    Product,
    ProductCategory,
    PurchaseItem,
    PurchaseOrder,
    SaleItem,
    SaleOrder,
    StockHistory,
    Supplier,
    User,
    UserHistory,
)
from tests.models import (
    CustomerCreate,
    CustomerHistoryResponse,
    CustomerResponse,
    CustomerSearchResponse,
    CustomerUpdate,
    PriceHistoryResponse,
    ProductCategoryCreate,
    ProductCategoryResponse,
    ProductCategoryUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    PurchaseItemsDraftUpdate,
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderListResponse,
    PurchaseOrderUpdate,
    SaleItemsDraftUpdate,
    SaleOrderCreate,
    SaleOrderDetailResponse,
    SaleOrderListResponse,
    SaleOrderUpdate,
    StockHistoryResponse,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
    UserCreate,
    UserHistoryResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter()
password_hash = PasswordHash.recommended()







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

def commit_or_409(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=message)

#---------------------------------------------------------------------------------

@router.post("/users",response_model=UserResponse,status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):

    # 1. Convert Pydantic data into dictionary
    user_data = payload.model_dump(exclude={"password"})

    # 2. Create SQLAlchemy User object
    new_user = User(
        **user_data,
        password_hash=hash_password(payload.password),
        created_by=current_user.user_id
    )

    # 3. Insert into database
    try:
        db.add(new_user)
        db.flush()

        db.add(
            UserHistory(
                user_id=new_user.user_id,
                action="created",
                old_data=None,
                new_data=_old_user_data(new_user),
                updated_by=current_user.user_id,
                remarks="User account created",
            )
        )

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Email or login ID already exists"
        )

    # 4. Refresh the newly created user
    db.refresh(new_user)

    return get_user_with_audit(new_user.user_id, db)

@router.get("/users/{target_user_id}", response_model=UserResponse)
def get_user(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = get_user_with_audit(target_user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=list[UserResponse])
def get_users(
    status: Literal["active", "inactive"] | None = None,
    role: Literal["admin", "staff"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    statement = select(User).options(
        selectinload(User.created_by_user),
        selectinload(User.updated_by_user),
    )
    if status is not None:
        statement = statement.where(User.status == status)
    if role is not None:
        statement = statement.where(User.role == role)

    statement = (
        statement.order_by(User.created_at.desc(), User.user_id)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()



@router.patch("/users/{target_user_id}",response_model=UserResponse,status_code=200)
def update_user(
    target_user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    # 1. Retrieve and lock user
    target_user = db.scalar(
        select(User)
        .where(User.user_id == target_user_id)
        .with_for_update()
    )
    
    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 2. Get supplied fields
    update_data = payload.model_dump(exclude_unset=True)

    
    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    if target_user.user_id == current_user.user_id and (
            update_data.get("status") == "inactive" or update_data.get("role") == "staff"):
                raise HTTPException(status_code=400, detail="You cannot deactivate or demote your own account")

    # 3. Capture old details
    old_data = _old_user_data(target_user)

    password_was_changed = "password" in update_data

    # Hash password
    if password_was_changed:
        new_password = update_data.pop("password")
        target_user.password_hash = hash_password(new_password)

    # 4. Update audit field
    update_data["updated_by"] = current_user.user_id

    # 5. Apply updates
    for field, value in update_data.items():
        setattr(target_user, field, value)

    # 6. Save user history
    try:
        db.add(
            UserHistory(
                user_id=target_user.user_id,
                action="updated",
                old_data=old_data,
                new_data=_old_user_data(target_user),
                updated_by=current_user.user_id,
                remarks="User details updated",
            )
        )

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email or login ID already exists, or a database constraint was violated"
        )

    # 7. Refresh and return
    db.refresh(target_user)

    return get_user_with_audit(target_user.user_id, db)


#------------------------------------------------------------------------



@router.post("/categories",response_model=ProductCategoryResponse,status_code=201)
def create_category(
    payload: ProductCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 2. Create category object
    new_category = ProductCategory(
        **payload.model_dump(),
        created_by=current_user.user_id
    )

    # 3. Insert into database
    try:
        db.add(new_category)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Category name already exists or database constraint violated"
        )

    # 4. Refresh the category
    db.refresh(new_category)


    # 6. Return category
    return get_category_with_audit(new_category.category_id,db)


@router.get("/categories", response_model=list[ProductCategoryResponse])
def get_categories(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(ProductCategory)
        .options(
            selectinload(ProductCategory.created_by_user),
            selectinload(ProductCategory.updated_by_user),
        )
        .order_by(ProductCategory.category_name)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()

@router.get("/categories/{category_id}", response_model=ProductCategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    category = get_category_with_audit(category_id, db)
    if category is None:
        raise HTTPException(status_code=404, detail="Product category not found")
    return category


@router.patch("/categories/{target_category_id}",response_model=ProductCategoryResponse,status_code=200)
def update_category(
    target_category_id: int,
    payload: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 2. Retrieve the category to be updated
    statement = select(ProductCategory).where(ProductCategory.category_id == target_category_id).with_for_update()

    target_category = db.scalar(statement)

    if target_category is None:
        raise HTTPException(
            status_code=404,
            detail="Product category not found"
        )

    # 3. Get only the fields supplied in the request
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # 4. Set the user who updated the category
    update_data["updated_by"] = current_user.user_id

    # 5. Apply the updates
    for field, value in update_data.items():
        setattr(target_category, field, value)

    # 6. Commit changes
    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Category name already exists or a database constraint was violated"
        )

    # 7. Refresh the category
    db.refresh(target_category)

    return get_category_with_audit(target_category_id,db)

#-----------------------------------------------------------------------------------------------

@router.post("/suppliers",response_model=SupplierResponse,status_code=201)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 2. Create supplier object
    new_supplier = Supplier(
        **payload.model_dump(),
        created_by=current_user.user_id
    )

    # 3. Insert into database
    try:
        db.add(new_supplier)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unable to create supplier. Database constraint violated."
        )

    # 4. Refresh the supplier
    db.refresh(new_supplier)

    # 5. Retrieve supplier with creator and updater names
    return get_supplier_with_audit(new_supplier.supplier_id,db)

@router.get("/suppliers", response_model=list[SupplierResponse])
def get_suppliers(
    status: Literal["active", "inactive"] | None = None,
    q: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Supplier).options(
        selectinload(Supplier.created_by_user),
        selectinload(Supplier.updated_by_user),
    )
    if status is not None:
        statement = statement.where(Supplier.status == status)
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Supplier.supplier_name.ilike(term),
                Supplier.contact_person.ilike(term),
                Supplier.phone.ilike(term),
            )
        )
    statement = (
        statement.order_by(Supplier.supplier_name)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()

@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    supplier = get_supplier_with_audit(supplier_id, db)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.patch("/suppliers/{target_supplier_id}",response_model=SupplierResponse,status_code=200)
def update_supplier(
    target_supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 2. Retrieve the supplier to be updated
    statement = select(Supplier).where(
        Supplier.supplier_id == target_supplier_id
    ).with_for_update()

    target_supplier = db.scalar(statement)

    if target_supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    # 3. Get only the fields supplied in the request
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # 4. Set the user who updated the supplier
    update_data["updated_by"] = current_user.user_id

    # 5. Apply the updates
    for field, value in update_data.items():
        setattr(target_supplier, field, value)

    # 6. Commit changes
    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Supplier email already exists or a database constraint was violated"
        )

    # 7. Refresh the supplier
    db.refresh(target_supplier)


    return get_supplier_with_audit(target_supplier_id,db)


#----------------------------------------------------


@router.post("/customers",response_model=CustomerResponse,status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 2. Create customer object
    new_customer = Customer(
        **payload.model_dump(),
        created_by=current_user.user_id
    )

    # 3. Insert into database
    try:
        db.add(new_customer)
        db.flush()
        db.add(
            CustomerHistory(
                customer_id=new_customer.customer_id,
                action="created",
                old_data=None,
                new_data=_old_customer_data(new_customer),
                updated_by=current_user.user_id,
                remarks="Customer record created",
            )
        )

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Unable to create customer. Database constraint violated."
        )

    # 4. Refresh the customer
    db.refresh(new_customer)

    return get_customer_with_audit(new_customer.customer_id,db)


@router.get("/customers", response_model=list[CustomerResponse])
def get_customers(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Customer).options(
        selectinload(Customer.created_by_user),
        selectinload(Customer.updated_by_user),
    )
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                Customer.customer_name.ilike(term),
                Customer.phone.ilike(term),
                Customer.email.ilike(term),
            )
        )
    statement = (
        statement.order_by(Customer.customer_name)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(statement).all()


@router.get("/customers/search", response_model=list[CustomerSearchResponse])
def search_customers(
    q: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=20, ge=1, le=20),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    q = q.strip()

    if not q:
        raise HTTPException(
            status_code=400,
            detail="Search term cannot be empty"
        )

    term = f"%{q}%"

    statement = (
        select(Customer)
        .where(
            or_(
                Customer.customer_name.ilike(term),
                Customer.phone.ilike(term),
            )
        )
        .order_by(Customer.customer_name)
        .limit(limit)
        .offset(offset)
    )

    customers = db.scalars(statement).all()

    return customers

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = get_customer_with_audit(customer_id, db)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/customers/{target_customer_id}",response_model=CustomerResponse,status_code=200)
def update_customer(
    target_customer_id: UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # 2. Retrieve the customer to be updated
    statement = select(Customer).where(
        Customer.customer_id == target_customer_id
    ).with_for_update()

    target_customer = db.scalar(statement)

    if target_customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # 3. Get only the fields supplied in the request
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )
    old_data=_old_customer_data(target_customer)


    # 5. Apply the updates
    update_data["updated_by"] = current_user.user_id
    for field, value in update_data.items():
        setattr(target_customer, field, value)

    # 6. Commit changes
    try:
        db.add(
            CustomerHistory(
                customer_id=target_customer.customer_id,
                action="updated",
                old_data=old_data,
                new_data=_old_customer_data(target_customer),
                updated_by=current_user.user_id,
                remarks="Customer details updated",
            )
        )
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Customer email already exists or a database constraint was violated"
        )

    # 7. Refresh the customer
    db.refresh(target_customer)


    return get_customer_with_audit(target_customer_id,db)


#-------------------------------------
@router.post("/products",response_model=ProductResponse,status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):

    # 2. Check whether the product category exists
    category = db.scalar(
        select(ProductCategory).where(
            ProductCategory.category_id == payload.category_id
        )
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Product category not found"
        )

    # 3. Create a Product object using the Pydantic data
    new_product = Product(
        **payload.model_dump(),
        created_by=current_user.user_id
    )

    # 4. Add the product to the session
    db.add(new_product)

    # 5. Commit the transaction
    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists or database constraint violated"
        )

    # 6. Refresh the newly created product
    db.refresh(new_product)

    # 7. Retrieve the product with related user information
 
    return get_product_with_audit(new_product.product_id,db)

# fetch all the products
@router.get("/products", response_model=list[ProductResponse])
def get_products(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Create SELECT query
    statement = (
    select(Product)
    .options(
        selectinload(Product.created_by_user),
        selectinload(Product.updated_by_user)
    )
    .order_by(Product.product_id)
    .limit(limit)
    .offset(offset)
    )


    # 2. Execute query and retrieve products
    products = db.execute(statement).scalars().all()

    # 3. Return product information
    return products

# fetch a single product by SKU
@router.get( "/products/{sku}",response_model=ProductResponse)
def get_product(sku: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Create SELECT query
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user),
            selectinload(Product.updated_by_user)
        )
        .where(Product.sku == sku)
    )

    # 2. Execute query and retrieve one product
    product = db.execute(statement).scalar_one_or_none()

    # 3. Check whether the product exists
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 4. Return the product
    return product


@router.patch("/products/{sku}", response_model=ProductResponse, status_code=200)
def update_product(
    sku: str,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Retrieve product using SKU and lock the row
    statement = (
        select(Product)
        .where(Product.sku == sku)
        .with_for_update()
    )

    target_product = db.scalar(statement)

    if target_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 2. Get only the fields supplied in the request
    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # 3. Validate category if category_id is being updated
    if "category_id" in update_data:
        category_statement = select(ProductCategory).where(
            ProductCategory.category_id == update_data["category_id"]
        )

        category = db.scalar(category_statement)

        if category is None:
            raise HTTPException(
                status_code=404,
                detail="Product category not found"
            )

    # 4. Capture old and new prices
    old_cost = target_product.cost_price
    old_sale = target_product.sale_price

    new_cost = update_data.get("cost_price", old_cost)
    new_sale = update_data.get("sale_price", old_sale)

    # 5. Apply updates
    update_data["updated_by"] = current_user.user_id

    for field, value in update_data.items():
        setattr(target_product, field, value)

    # 6. Commit changes and record price history
    try:
        if new_cost != old_cost or new_sale != old_sale:
            db.add(
                PriceHistory(
                    product_id=target_product.product_id,
                    old_cost_price=old_cost if new_cost != old_cost else None,
                    new_cost_price=new_cost if new_cost != old_cost else None,
                    old_sale_price=old_sale if new_sale != old_sale else None,
                    new_sale_price=new_sale if new_sale != old_sale else None,
                    updated_by=current_user.user_id,
                    remarks="Product price updated",
                )
            )

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists or a database constraint was violated"
        )

    # 7. Refresh the product
    db.refresh(target_product)

    # 8. Return updated product
    return get_product_with_audit(target_product.product_id, db)

@router.post( "/purchase-orders", response_model=PurchaseOrderDetailResponse, status_code=201)
def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        # 1. Validate supplier
        supplier = db.scalar(
            select(Supplier).where(
                Supplier.supplier_id == payload.supplier_id,
                Supplier.status == "active"
            )
        )

        if supplier is None:
            raise HTTPException(
                status_code=404,
                detail="Supplier not found or inactive"
            )

        # 2. Check duplicate SKUs
        skus = [item.sku for item in payload.items]

        if len(skus) != len(set(skus)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate products are not allowed"
            )

        # 3. Create purchase order
        purchase_order = PurchaseOrder(
            supplier_id=supplier.supplier_id,
            created_by=current_user.user_id
        )

        db.add(purchase_order)
        db.flush()

        # 4. Create purchase items
        purchase_items = []

        for item in payload.items:

            product = db.scalar(
                select(Product).where(
                    Product.sku == item.sku,
                    Product.status == "active"
                )
            )

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Active product not found: {item.sku}"
                )

            purchase_items.append(
                PurchaseItem(
                    purchase_id=purchase_order.purchase_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.cost_price
                )
            )

        db.add_all(purchase_items)
        db.commit()

        purchase_id = purchase_order.purchase_id

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create purchase order. Check for duplicate or invalid records."
        )

    except Exception:
        db.rollback()
        raise


    return get_purchase_order_with_details(purchase_order.purchase_id,db)

@router.patch("/purchase-orders/{purchase_id}",response_model=PurchaseOrderDetailResponse)
def update_purchase_order(
    purchase_id: int,
    payload: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        # 1. Fetch and lock the purchase order
        purchase_order = db.scalar(
            select(PurchaseOrder)
            .where(PurchaseOrder.purchase_id == purchase_id)
            .with_for_update()
        )

        if purchase_order is None:
            raise HTTPException(
                status_code=404,
                detail="Purchase order not found"
            )

        # 2. Get supplied fields
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        

        if purchase_order.status in ("delivered", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail="Delivered or cancelled orders cannot be modified"
            )

    
        # 4. Validate supplier if supplied
        if "supplier_id" in update_data:
            if purchase_order.status != "draft":
                raise HTTPException(
                    status_code=400,
                    detail="Only draft purchase orders can be modified"
                )
            
            supplier = db.scalar(
                select(Supplier).where(
                    Supplier.supplier_id == update_data["supplier_id"],
                    Supplier.status == "active"
                )
            )

            if supplier is None:
                raise HTTPException(
                    status_code=404,
                    detail="Supplier not found or inactive"
                )

            purchase_order.supplier_id = supplier.supplier_id

        # 5. Handle status
        if "status" in update_data:
            new_status = update_data["status"]

            if new_status == "cancelled":

                if purchase_order.status not in ("draft", "order_placed"):
                    raise HTTPException(
                        status_code=400,
                        detail="This purchase order cannot be cancelled"
                    )
                # Do not update other fields during cancellation
                if len(update_data) > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Only status can be updated when cancelling an order"
                    )

                purchase_order.status = "cancelled"


            elif new_status == "order_placed":

                if purchase_order.status != "draft":
                    raise HTTPException(
                        status_code=400,
                        detail="Only draft purchase orders can be placed"
                    )

                item_count = db.scalar(
                    select(func.count())
                    .select_from(PurchaseItem)
                    .where(PurchaseItem.purchase_id == purchase_id)
                )

                if item_count == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot place an order without items"
                    )

                purchase_order.status="order_placed"
                purchase_order.purchase_date = date.today()

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition"
                )

        purchase_order.updated_by = current_user.user_id

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update purchase order"
        )

    except Exception:
        db.rollback()
        raise


    return get_purchase_order_with_details(purchase_id,db)

@router.patch("/purchase-orders/{purchase_id}/items",response_model=PurchaseOrderDetailResponse,)
def update_purchase_order_items(
    purchase_id: int,
    payload: PurchaseItemsDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.purchase_id == purchase_id)
        .with_for_update()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft purchase orders can be modified")

    existing = db.scalars(
        select(PurchaseItem)
        .options(selectinload(PurchaseItem.product))
        .where(PurchaseItem.purchase_id == purchase_id)
    ).all()
    existing_map = {item.purchase_item_id: item for item in existing}

    item_ids = [
        item.purchase_item_id
        for item in payload.items
        if item.purchase_item_id is not None
    ]
    skus = [item.sku for item in payload.items]
    if len(item_ids) != len(set(item_ids)):
        raise HTTPException(status_code=400, detail="Duplicate purchase item IDs")
    if len(skus) != len(set(skus)):
        raise HTTPException(status_code=400, detail="Duplicate product SKUs")

    new_items = []
    for item in payload.items:
        if item.purchase_item_id is not None:
            old_item = existing_map.get(item.purchase_item_id)
            if old_item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Purchase item {item.purchase_item_id} not found in this order",
                )
            if old_item.product.sku != item.sku:
                raise HTTPException(
                    status_code=400,
                    detail="SKU cannot be changed for an existing purchase item",
                )
            old_item.quantity = item.quantity
        else:
            product = db.scalar(
                select(Product).where(
                    Product.sku == item.sku,
                    Product.status == "active",
                )
            )
            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Active product not found: {item.sku}",
                )
            new_items.append(
                PurchaseItem(
                    purchase_id=purchase_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.cost_price,
                )
            )

    submitted_ids = set(item_ids)
    for item_id, old_item in existing_map.items():
        if item_id not in submitted_ids:
            db.delete(old_item)

    try:
        db.flush()
        db.add_all(new_items)
        order.updated_by = current_user.user_id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unable to update purchase items")

    return get_purchase_order_with_details(purchase_id, db)


@router.post("/purchase-orders/{purchase_id}/receive",response_model=PurchaseOrderDetailResponse)
def receive_purchase_order(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        # 1. Lock the purchase order
        purchase_order = db.scalar(
            select(PurchaseOrder)
            .where(PurchaseOrder.purchase_id == purchase_id)
            .with_for_update()
        )

        if purchase_order is None:
            raise HTTPException(
                status_code=404,
                detail="Purchase order not found"
            )

        # 2. Only placed orders can be received
        if purchase_order.status != "order_placed":
            raise HTTPException(
                status_code=400,
                detail="Only placed purchase orders can be received"
            )

        # 3. Get purchase items
        purchase_items = db.scalars(
            select(PurchaseItem)
            .where(PurchaseItem.purchase_id == purchase_id)
        ).all()

        if not purchase_items:
            raise HTTPException(
                status_code=400,
                detail="Purchase order has no items"
            )

        # 4. Get product IDs and lock products in a consistent order
        product_ids = sorted({
            item.product_id for item in purchase_items
        })

        products = db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
        ).all()

        product_map = {
            product.product_id: product
            for product in products
        }

        if len(product_map) != len(product_ids):
            raise HTTPException(
                status_code=409,
                detail="One or more products no longer exist"
            )

        # 5. Increase stock and create history records
        history_records = []

        for item in purchase_items:
            product = product_map[item.product_id]

            product.stock_quantity += item.quantity

            history_records.append(
                StockHistory(
                    product_id=product.product_id,
                    purchase_item_id=item.purchase_item_id,
                    sale_item_id=None,
                    change_type="purchase",
                    quantity_change=item.quantity,
                    updated_by=current_user.user_id,
                    remarks=f"Goods received for purchase order {purchase_id}"
                )
            )

        db.add_all(history_records)

        # 6. Mark purchase order as delivered
        purchase_order.status = "delivered"
        purchase_order.updated_by = current_user.user_id

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to receive purchase order"
        )

    except Exception:
        db.rollback()
        raise



    return get_purchase_order_with_details(purchase_id,db)

@router.get("/purchase-orders", response_model=list[PurchaseOrderListResponse])
def get_purchase_orders(
    status: Literal[
        "draft",
        "order_placed",
        "delivered",
        "cancelled",
    ]
    | None = Query(default=None),
    supplier_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    statement = (
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.supplier),
            selectinload(PurchaseOrder.created_by_user),
            selectinload(PurchaseOrder.updated_by_user),
        )
    )

    # Filter by status
    if status is not None:
        statement = statement.where(
            PurchaseOrder.status == status
        )
    else:
        # Default: exclude cancelled orders
        statement = statement.where(
            PurchaseOrder.status != "cancelled"
        )

    # Filter by supplier
    if supplier_id is not None:
        statement = statement.where(
            PurchaseOrder.supplier_id == supplier_id
        )

    # Latest orders first
    statement = (
        statement
        .order_by(
            PurchaseOrder.created_at.desc(),
            PurchaseOrder.purchase_id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    purchase_orders = db.scalars(statement).all()

    return purchase_orders

@router.get("/purchase-orders/{purchase_id}",response_model=PurchaseOrderDetailResponse)
def get_purchase_order(
    purchase_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    purchase_order = get_purchase_order_with_details(purchase_id,db)

    if purchase_order is None:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found"
        )

    return purchase_order

#----------------------------------------------------------


@router.post("/sale-orders",response_model=SaleOrderDetailResponse,status_code=201)
def create_sale_order(
    payload: SaleOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        # 1. Validate customer
        customer = db.scalar(
            select(Customer).where(
                Customer.customer_id == payload.customer_id
            )
        )

        if customer is None:
            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

        # If Customer has a status column, also validate active status.

        # 2. Check duplicate SKUs
        skus = [item.sku for item in payload.items]

        if len(skus) != len(set(skus)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate products are not allowed"
            )

        # 3. Create sale order
        sale_order = SaleOrder(
            customer_id=customer.customer_id,
            created_by=current_user.user_id
        )

        db.add(sale_order)
        db.flush()

        # 4. Create sale items
        sale_items = []

        for item in payload.items:

            product = db.scalar(
                select(Product).where(
                    Product.sku == item.sku,
                    Product.status == "active"
                )
            )

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Active product not found: {item.sku}"
                )

            sale_items.append(
                SaleItem(
                    sale_id=sale_order.sale_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.sale_price
                )
            )

        db.add_all(sale_items)
        db.commit()

        sale_id = sale_order.sale_id

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create sale order"
        )

    except Exception:
        db.rollback()
        raise

    return get_sale_order_with_details(sale_order.sale_id,db)


@router.patch("/sale-orders/{sale_id}",response_model=SaleOrderDetailResponse)
def update_sale_order(
    sale_id: int,
    payload: SaleOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):


    try:
        # 1. Fetch and lock sale order
        sale_order = db.scalar(
            select(SaleOrder)
            .where(SaleOrder.sale_id == sale_id)
            .with_for_update()
        )

        if sale_order is None:
            raise HTTPException(
                status_code=404,
                detail="Sale order not found"
            )

        # 2. Get supplied fields
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        # 3. Do not allow changes to delivered or cancelled orders
        if sale_order.status in ("delivered", "cancelled"):
            raise HTTPException(
                status_code=400,
                detail="Delivered or cancelled orders cannot be modified"
            )


        if "customer_id" in update_data:
        
            if sale_order.status != "draft":
                raise HTTPException(
                    status_code=400,
                    detail="Only draft sale orders can be modified"
                )

            customer = db.scalar(
                select(Customer).where(
                    Customer.customer_id == update_data["customer_id"]
                )
            )

            if customer is None:
                raise HTTPException(
                    status_code=404,
                    detail="Customer not found"
                )

            sale_order.customer_id = customer.customer_id

        # 4. Handle status changes
        if "status" in update_data:

            new_status = update_data["status"]

            # Cancellation is allowed from draft and order_placed
            if new_status == "cancelled":

                if sale_order.status not in ("draft", "order_placed"):
                    raise HTTPException(
                        status_code=400,
                        detail="This sale order cannot be cancelled"
                    )

                # Do not update other fields during cancellation
                if len(update_data) > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="Only status can be updated when cancelling an order"
                    )

                sale_order.status = "cancelled"

            # Place a draft order
            elif new_status == "order_placed":

                if sale_order.status != "draft":
                    raise HTTPException(
                        status_code=400,
                        detail="Only draft sale orders can be placed"
                    )

                item_count = db.scalar(
                    select(func.count())
                    .select_from(SaleItem)
                    .where(SaleItem.sale_id == sale_id)
                )

                if item_count == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot place a sale order without items"
                    )

                sale_order.status = "order_placed"

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status transition"
                )

       
        

        # 6. Update audit field
        sale_order.updated_by = current_user.user_id

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update sale order"
        )

    except Exception:
        db.rollback()
        raise

    # 7. Return updated order with details
    return get_sale_order_with_details(sale_id, db)



@router.patch("/sale-orders/{sale_id}/items",response_model=SaleOrderDetailResponse)
def update_sale_order_items(
    sale_id: int,
    payload: SaleItemsDraftUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):


    try:

        # 1. Get and lock sale order
        sale_order = db.scalar(
            select(SaleOrder)
            .where(SaleOrder.sale_id == sale_id)
            .with_for_update()
        )

        if sale_order is None:
            raise HTTPException(
                status_code=404,
                detail="Sale order not found"
            )

        # 2. Only draft orders can be modified
        if sale_order.status != "draft":
            raise HTTPException(
                status_code=400,
                detail="Only draft sale orders can be modified"
            )

        # 3. Get existing sale items
        existing_items = db.scalars(
            select(SaleItem)
            .options(selectinload(SaleItem.product))
            .where(SaleItem.sale_id == sale_id)
        ).all()

        # 4. Map existing items by ID
        existing_map = {
            item.sale_item_id: item
            for item in existing_items
        }

        # 5. Validate duplicate IDs and SKUs
        item_ids = [
            item.sale_item_id
            for item in payload.items
            if item.sale_item_id is not None
        ]

        skus = [item.sku for item in payload.items]

        if len(item_ids) != len(set(item_ids)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate sale item IDs"
            )

        if len(skus) != len(set(skus)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate product SKUs"
            )

        # 6. Process submitted items
        new_items = []

        for item in payload.items:

            if item.sale_item_id is not None:

                # Existing item
                existing_item = existing_map.get(
                    item.sale_item_id
                )

                if existing_item is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Sale item {item.sale_item_id} "
                            "not found in this order"
                        )
                    )

                # Existing item's product cannot be changed
                if item.sku != existing_item.product.sku:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "SKU cannot be changed for an "
                            "existing sale item"
                        )
                    )

                # Update only quantity
                # Keep the original unit price
                existing_item.quantity = item.quantity

            else:

                # New item: find active product by SKU
                product = db.scalar(
                    select(Product).where(
                        Product.sku == item.sku,
                        Product.status == "active"
                    )
                )

                if product is None:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Active product with SKU "
                            f"{item.sku} not found"
                        )
                    )

                new_items.append(
                    SaleItem(
                        sale_id=sale_id,
                        product_id=product.product_id,
                        quantity=item.quantity,
                        unit_price=product.sale_price
                    )
                )

        # 7. Delete existing items omitted from request
        submitted_ids = set(item_ids)

        for item_id, existing_item in existing_map.items():

            if item_id not in submitted_ids:
                db.delete(existing_item)

        # 8. Flush deletions before adding new items
        db.flush()

        # 9. Add new items
        db.add_all(new_items)

        # 10. Update audit information
        sale_order.updated_by = current_user.user_id

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update sale items"
        )

    except Exception:
        db.rollback()
        raise

    return get_sale_order_with_details(sale_id,db)


@router.post("/sale-orders/{sale_id}/complete",response_model=SaleOrderDetailResponse)
def complete_sale_order(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        # 1. Fetch and lock the sale order
        sale_order = db.scalar(
            select(SaleOrder)
            .where(SaleOrder.sale_id == sale_id)
            .with_for_update()
        )

        if sale_order is None:
            raise HTTPException(
                status_code=404,
                detail="Sale order not found"
            )

        # 2. Only placed orders can be completed
        if sale_order.status != "order_placed":
            raise HTTPException(
                status_code=400,
                detail="Only placed sale orders can be completed"
            )

        # 3. Get sale items
        sale_items = db.scalars(
            select(SaleItem)
            .where(SaleItem.sale_id == sale_id)
        ).all()

        if not sale_items:
            raise HTTPException(
                status_code=400,
                detail="Sale order has no items"
            )

        # 4. Lock products in a consistent order
        product_ids = sorted({
            item.product_id for item in sale_items
        })

        products = db.scalars(
            select(Product)
            .where(Product.product_id.in_(product_ids))
            .order_by(Product.product_id)
            .with_for_update()
        ).all()

        product_map = {
            product.product_id: product
            for product in products
        }

        if len(product_map) != len(product_ids):
            raise HTTPException(
                status_code=409,
                detail="One or more products no longer exist"
            )

        # 5. Check stock for ALL items before deducting anything
        for item in sale_items:
            product = product_map[item.product_id]

            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient stock for SKU {product.sku}. "
                        f"Available: {product.stock_quantity}, "
                        f"Required: {item.quantity}"
                    )
                )

        # 6. Deduct stock and create history records
        history_records = []

        for item in sale_items:
            product = product_map[item.product_id]

            product.stock_quantity -= item.quantity

            history_records.append(
                StockHistory(
                    product_id=product.product_id,
                    purchase_item_id=None,
                    sale_item_id=item.sale_item_id,
                    change_type="sale",
                    quantity_change=-item.quantity,
                    updated_by=current_user.user_id,
                    remarks=f"Sale completed for sale order {sale_id}"
                )
            )

        db.add_all(history_records)

        # 7. Update sale order
        sale_order.status = "delivered"
        sale_order.sale_date = date.today()
        sale_order.updated_by = current_user.user_id

        # 8. Save everything in one transaction
        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to complete sale order"
        )

    except Exception:
        db.rollback()
        raise

    return get_sale_order_with_details(sale_id,db)



@router.get("/sale-orders",response_model=list[SaleOrderListResponse])
def get_sale_orders(
    status: Literal[
        "draft",
        "order_placed",
        "delivered",
        "cancelled"
    ] | None = Query(default=None),

    customer_id: UUID | None = Query(default=None),

    limit: int = Query(default=20, ge=1, le=100),

    offset: int = Query(default=0, ge=0),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    statement = (
        select(SaleOrder)
        .options(
            selectinload(SaleOrder.customer),
            selectinload(SaleOrder.created_by_user),
            selectinload(SaleOrder.updated_by_user),
        )
    )

    # 1. Filter by status
    if status is not None:
        statement = statement.where(
            SaleOrder.status == status
        )
    else:
        # Default: exclude cancelled orders
        statement = statement.where(
            SaleOrder.status != "cancelled"
        )

    # 2. Filter by customer
    if customer_id is not None:
        statement = statement.where(
            SaleOrder.customer_id == customer_id
        )

    # 3. Latest orders first
    statement = (
        statement
        .order_by(
            SaleOrder.created_at.desc(),
            SaleOrder.sale_id.desc()
        )
        .limit(limit)
        .offset(offset)
    )

    sale_orders = db.scalars(statement).all()

    return sale_orders


@router.get("/sale-orders/{sale_id}",response_model=SaleOrderDetailResponse)
def get_sale_order(

    sale_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

 
    sale_order = get_sale_order_with_details(sale_id,db)

    if sale_order is None:
        raise HTTPException(
            status_code=404,
            detail="Sale order not found"
        )

    return sale_order

# ---------------------------------------------------------------------------

@router.post("/products/{sku}/stock-adjustments", response_model=StockHistoryResponse, status_code=201)
def adjust_stock(

    sku: str,
    quantity_change: int = Query(...),
    remarks: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if quantity_change == 0:
        raise HTTPException(status_code=400, detail="quantity_change cannot be 0")
    product = db.scalar(
        select(Product)
        .where(Product.sku == sku)
        .with_for_update()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.status != "active":
        raise HTTPException(status_code=400, detail="Cannot adjust stock for an inactive product")

    if product.stock_quantity + quantity_change < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock adjustment cannot make stock quantity negative",
        )
    remarks = remarks.strip()

    if not remarks:
        raise HTTPException(
            status_code=400,
            detail="Remarks cannot be empty"
        )
    
    product.stock_quantity += quantity_change
    product.updated_by = current_user.user_id
    
    history = StockHistory(
        product_id=product.product_id,
        purchase_item_id=None,
        sale_item_id=None,
        change_type="adjustment",
        quantity_change=quantity_change,
        updated_by=current_user.user_id,
        remarks=remarks,
    )
    db.add(history)
    commit_or_409(db, "Unable to adjust stock")
    statement = (
        select(StockHistory)
        .options(
            selectinload(StockHistory.product),
            selectinload(StockHistory.updated_by_user),
        )
        .where(StockHistory.stock_hist_id == history.stock_hist_id)
    )
    return db.scalar(statement)

# 1. Get the 10 most recent stock history records
@router.get("/stock-history", response_model=list[StockHistoryResponse])
def get_stock_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(StockHistory)
        .options(
            selectinload(StockHistory.product),
            selectinload(StockHistory.updated_by_user),
        )
        .order_by(
            StockHistory.updated_at.desc(),
            StockHistory.stock_hist_id.desc()
        )
        .limit(10)
    )

    return db.scalars(statement).all()


# 2. Get stock history for a particular SKU
@router.get("/stock-history/{sku}", response_model=list[StockHistoryResponse])
def get_stock_history_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(StockHistory)
        .join(Product)
        .options(
            selectinload(StockHistory.product),
            selectinload(StockHistory.updated_by_user),
        )
        .where(Product.sku == sku)
        .order_by(
            StockHistory.updated_at.desc(),
            StockHistory.stock_hist_id.desc()
        )
    )

    return db.scalars(statement).all()


# 1. Get the 10 most recent price history records
@router.get("/price-history", response_model=list[PriceHistoryResponse])
def get_price_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(PriceHistory)
        .options(
            selectinload(PriceHistory.product),
            selectinload(PriceHistory.updated_by_user),
        )
        .order_by(
            PriceHistory.updated_at.desc(),
            PriceHistory.price_hist_id.desc()
        )
        .limit(10)
    )

    return db.scalars(statement).all()


# 2. Get price history for a particular SKU
@router.get("/price-history/{sku}", response_model=list[PriceHistoryResponse])
def get_price_history_by_sku(
    sku: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(PriceHistory)
        .join(Product)
        .options(
            selectinload(PriceHistory.product),
            selectinload(PriceHistory.updated_by_user),
        )
        .where(Product.sku == sku)
        .order_by(
            PriceHistory.updated_at.desc(),
            PriceHistory.price_hist_id.desc()
        )
    )

    return db.scalars(statement).all()

# 1. Get the 10 most recent user history records
@router.get("/user-history", response_model=list[UserHistoryResponse])
def get_user_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(UserHistory)
        .options(
            selectinload(UserHistory.user),
            selectinload(UserHistory.updated_by_user),
        )
        .order_by(
            UserHistory.updated_at.desc(),
            UserHistory.user_hist_id.desc()
        )
        .limit(10)
    )

    return db.scalars(statement).all()


# 2. Get history for a particular user
@router.get("/user-history/{target_user_id}", response_model=list[UserHistoryResponse])
def get_user_history_by_user(
    target_user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(UserHistory)
        .options(
            selectinload(UserHistory.user),
            selectinload(UserHistory.updated_by_user),
        )
        .where(UserHistory.user_id == target_user_id)
        .order_by(
            UserHistory.updated_at.desc(),
            UserHistory.user_hist_id.desc()
        )
    )

    return db.scalars(statement).all()

# 1. Get the 10 most recent customer history records
@router.get("/customer-history", response_model=list[CustomerHistoryResponse])
def get_customer_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(CustomerHistory)
        .options(
            selectinload(CustomerHistory.customer),
            selectinload(CustomerHistory.updated_by_user),
        )
        .order_by(
            CustomerHistory.updated_at.desc(),
            CustomerHistory.customer_hist_id.desc()
        )
        .limit(10)
    )

    return db.scalars(statement).all()


# 2. Get history for a particular customer
@router.get("/customer-history/{target_customer_id}", response_model=list[CustomerHistoryResponse])
def get_customer_history_by_customer(
    target_customer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(CustomerHistory)
        .options(
            selectinload(CustomerHistory.customer),
            selectinload(CustomerHistory.updated_by_user),
        )
        .where(CustomerHistory.customer_id == target_customer_id)
        .order_by(
            CustomerHistory.updated_at.desc(),
            CustomerHistory.customer_hist_id.desc()
        )
    )

    return db.scalars(statement).all()