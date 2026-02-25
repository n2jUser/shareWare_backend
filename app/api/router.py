from fastapi import APIRouter
from app.api.v1 import admin
from app.api.v1 import auth
from app.api.v1 import cart
from app.api.v1 import orders
from app.api.v1 import products
from app.api.v1 import upload  # <-- nouveau

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)  