import os
import shutil
from fastapi import APIRouter
from pydantic import BaseModel
from be.config import api_config
from be.services.service_manager import service_manager

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    limit: int = 5

class ChatQueryRequest(BaseModel):
    query: str
    limit: int = 5
    use_context: bool = True

@router.post("/query")
async def query_documents(request: QueryRequest):
    """문서 검색"""
    result = service_manager.rag_service.query(request.query, request.limit)
    
    if result.get("success") and result.get("results"):
        for item in result["results"]:
            if item.get("image_path") and os.path.exists(item["image_path"]):

                full_path = item["image_path"]
                
                if api_config.TEMP_IMAGE_DIR in full_path:
                    relative_path = os.path.relpath(full_path, api_config.TEMP_IMAGE_DIR)
                    item["image_path"] = relative_path
                else:
                    filename = os.path.basename(full_path)
                    pdf_name = item.get("pdf_name", "unknown").replace('.pdf', '')
                    
                    pdf_dir = os.path.join(api_config.TEMP_IMAGE_DIR, pdf_name)
                    if not os.path.exists(pdf_dir):
                        os.makedirs(pdf_dir)
                    
                    target_path = os.path.join(pdf_dir, filename)
                    relative_path = os.path.join(pdf_name, filename)
                    
                    try:
                        if not os.path.exists(target_path):
                            shutil.copy2(full_path, target_path)
                        item["image_path"] = relative_path
                    except Exception as e:
                        print(f"이미지 복사 오류: {e}")
                        item["image_path"] = None
            else:
                item["image_path"] = None
    
    return result

@router.post("/chat")
async def chat_with_documents(request: ChatQueryRequest):
    """문서 기반 채팅 - 검색된 페이지 내용을 바탕으로 답변 생성"""
    result = service_manager.rag_service.chat_query(request.query, request.limit, request.use_context)
    
    if result.get("success") and result.get("search_results"):
        for item in result["search_results"]:
            if item.get("image_path") and os.path.exists(item["image_path"]):

                full_path = item["image_path"]
                
                if api_config.TEMP_IMAGE_DIR in full_path:
                    relative_path = os.path.relpath(full_path, api_config.TEMP_IMAGE_DIR)
                    item["image_path"] = relative_path
                else:
                    filename = os.path.basename(full_path)
                    pdf_name = item.get("pdf_name", "unknown").replace('.pdf', '')
                    
                    pdf_dir = os.path.join(api_config.TEMP_IMAGE_DIR, pdf_name)
                    if not os.path.exists(pdf_dir):
                        os.makedirs(pdf_dir)
                    
                    target_path = os.path.join(pdf_dir, filename)
                    relative_path = os.path.join(pdf_name, filename)
                    
                    try:
                        if not os.path.exists(target_path):
                            shutil.copy2(full_path, target_path)
                        item["image_path"] = relative_path
                    except Exception as e:
                        print(f"이미지 복사 오류: {e}")
                        item["image_path"] = None
            else:
                item["image_path"] = None
    
    return result
