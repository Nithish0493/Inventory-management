
from fastapi import FastAPI

app = FastAPI(title="Inventory Management API")




@app.get("/")
def home():
    return {"message": "Inventory Management API is running"}
