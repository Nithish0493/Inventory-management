from database import engine
from database import Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Inventory Management tables created successfully.")
