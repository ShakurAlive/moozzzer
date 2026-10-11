from fastapi import APIRouter

from app.api.v1 import admin, auth, health, invites, library, media, playlists, preview, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(search.router)
api_router.include_router(preview.router)
api_router.include_router(media.router)
api_router.include_router(library.router)
api_router.include_router(playlists.router)
api_router.include_router(invites.router)
api_router.include_router(admin.router)
