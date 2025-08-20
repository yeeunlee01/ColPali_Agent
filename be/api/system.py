from fastapi import APIRouter
from be.services.service_manager import service_manager

router = APIRouter()

@router.get("/status")
async def get_status():
    """서비스 상태 확인"""
    return service_manager.rag_service.get_status()