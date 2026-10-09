from fastapi import APIRouter

from app.api.v1 import auth, health, preview, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(search.router)
api_router.include_router(preview.router)
