
from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.database_models import Product



app = FastAPI(title="Inventory Management API")




@app.get("/")
def home():
    return {"message": "Inventory Management API is running"}


