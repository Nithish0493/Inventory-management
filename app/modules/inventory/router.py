from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.database import get_db
from app.database_models import Product
from app.models import ProductResponse, ProductCreate

app = FastAPI(title="Inventory Management API")

# fetch all the products
@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):

    # 1. Create SELECT query
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user),
            selectinload(Product.updated_by_user)
        )
        .order_by(Product.product_id)
    )

    # 2. Execute query and retrieve products
    products = db.execute(statement).scalars().all()

    # 3. Return product information
    return products

# fetch a single product by SKU
@app.get( "/products/{sku}",response_model=ProductResponse)
def get_product(sku: str, db: Session = Depends(get_db)):
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

@app.post("/products", response_model=ProductResponse)
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    new_product = Product(**product_data.model_dump(),created_by=1)
   
    # 2. Add the object to the session
    db.add(new_product)

    # 3. Commit the transaction
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to insert product. Check SKU, category and user."
        )

    # 4. Refresh the object
    db.refresh(new_product)

    # 5. Load related user information for the response
    statement = (
        select(Product)
        .options(
            selectinload(Product.created_by_user),
            selectinload(Product.updated_by_user)
        )
        .where(Product.product_id == new_product.product_id)
    )

    product = db.execute(statement).scalar_one()

    # 6. Return inserted product
    return product


    



