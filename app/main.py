from fastapi import FastAPI

from authentication.router import router as authentication_router

from modules.users.router import router as users_router
from modules.inventory.router import router as inventory_router
from modules.customers.router import router as customers_router
from modules.partners.router import router as partners_router
from modules.orders.router import router as orders_router
from modules.history.router import router as history_router

app = FastAPI(title="Inventory Management API")

app.include_router(authentication_router)
app.include_router(users_router)
app.include_router(inventory_router)
app.include_router(customers_router)
app.include_router(partners_router)
app.include_router(orders_router)
app.include_router(history_router)


@app.get("/")
def home():
    return {"message": "Inventory Management API is running"}