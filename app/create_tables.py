from app.database import engine,Base
import app.database_models 

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Inventory Management tables created successfully.")
