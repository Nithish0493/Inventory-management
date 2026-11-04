from decimal import Decimal
from unittest import result

from sqlalchemy import select, text

from app.database import SessionLocal
from app.database_models import ProductCategory, User, Product


def main():

    db = SessionLocal()

    try:
        print("Session created successfully")
        statement = select(User).where(User.name== "nithish")

        user = db.execute(statement).scalar_one_or_none()

        if user is None:
            raise ValueError("User not found")

        category=ProductCategory(
            category_name="Watches",
            description="Watches category",
            created_by=user.user_id)

        db.add(category)
        db.flush()  

        new_product=Product(
            sku="WCH-TTN-001",
            product_name= "Titan Edge",
            product_description="Edge series",
            category_id=category.category_id,
            cost_price=1000,
            sale_price=1250.50,
            stock_quantity=50,
            reorder_level=10,
            created_by=user.user_id
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        print("New product added successfully:", new_product)
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        print("Session closed successfully")

        



if __name__ == "__main__":
    main()


