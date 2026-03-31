from fastapi import APIRouter

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.planning import router as planning_router
from backend.app.api.routes.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/v1/health", tags=["health"])
api_router.include_router(planning_router, prefix="/v1/planning", tags=["planning"])
api_router.include_router(chat_router, prefix="/v1/chat", tags=["chat"])

