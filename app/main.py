
from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.database_models import Product



app = FastAPI(title="Inventory Management API")




@app.get("/")
def home():
    return {"message": "Inventory Management API is running"}


@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    # 1. Create SELECT query
    statement = select(Product).order_by(Product.product_id)

    # 2. Execute query and retrieve products
    products = db.execute(statement).scalars().all()

    # 3. Return product information
    return [
        {
            "product_id": product.product_id,
            "sku": product.sku,
            "product_name": product.product_name,
            "description": product.product_description,
            "category_id": product.category_id,
            "cost_price": str(product.cost_price),
            "sale_price": str(product.sale_price),
            "stock_quantity": product.stock_quantity,
            "reorder_level": product.reorder_level,
            "status": product.status
        }
        for product in products
    ]