
from fastapi import FastAPI

from app.database import Base, engine
from app import models

app = FastAPI(title="Inventory Management API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "Inventory Management API is running"}
