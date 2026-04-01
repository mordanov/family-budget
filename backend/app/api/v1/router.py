from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, categories, operations, attachments, reports, balances, payment_methods

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(operations.router)
api_router.include_router(attachments.router)
api_router.include_router(reports.router)
api_router.include_router(balances.router)
api_router.include_router(payment_methods.router)
