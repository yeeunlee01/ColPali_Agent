import os
import json
import queue
import threading
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from be.config import api_config
from be.services.service_manager import service_manager

router = APIRouter()


@router.get("/pdf-list")
async def get_pdf_list():
    """./data 폴더의 PDF 파일 목록 반환"""
    return service_manager.rag_service.get_pdf_list()

@router.get("/pdf-preview")
async def get_pdf_preview(pdf_path: str):
    """PDF 첫 페이지 미리보기 이미지 생성"""
    result = service_manager.rag_service.get_pdf_preview(pdf_path, api_config.TEMP_IMAGE_DIR)
    
    if result.get("success") and result.get("preview_path"):
        # 파일명만 추출해서 반환
        preview_path = result["preview_path"]
        filename = os.path.basename(preview_path)
        result["image_name"] = filename
    
    return result

class IndexPdfRequest(BaseModel):
    pdf_path: str

@router.post("/index-pdf")
async def index_pdf(request: IndexPdfRequest):
    """선택된 PDF 인덱싱 (논블로킹)"""
    return service_manager.rag_service.process_pdf(request.pdf_path)


@router.get("/index-pdf-stream")
async def index_pdf_stream(pdf_path: str):
    """선택된 PDF 인덱싱 with 실시간 진행상황 스트리밍"""
    
    async def generate_progress():
        # 스레드 안전한 큐 사용
        progress_queue = queue.Queue()
        
        def progress_callback(data):
            # 동기적으로 큐에 데이터 추가
            progress_queue.put(data)
        
        # 백그라운드에서 인덱싱 실행
        def run_indexing():
            try:
                result = service_manager.rag_service.process_pdf(pdf_path, progress_callback)
                progress_queue.put({"status": "done", "result": result})
            except Exception as e:
                progress_queue.put({
                    "status": "error", 
                    "message": f"인덱싱 중 오류 발생: {str(e)}"
                })
        
        # 스레드로 인덱싱 작업 시작
        indexing_thread = threading.Thread(target=run_indexing)
        indexing_thread.start()
        
        try:
            while True:
                try:
                    # 논블로킹으로 큐에서 데이터 가져오기 (타임아웃 1초)
                    try:
                        data = progress_queue.get(timeout=1.0)
                        
                        # SSE 형식으로 데이터 전송
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                        
                        # 완료 또는 에러 시 종료
                        if data.get("status") in ["done", "error"]:
                            break
                            
                    except queue.Empty:
                        # 타임아웃 시 연결 유지를 위한 heartbeat
                        yield f"data: {json.dumps({'status': 'heartbeat'})}\n\n"
                        
                    # 스레드가 종료되었는지 확인
                    if not indexing_thread.is_alive():
                        # 큐에 남은 데이터가 있는지 확인
                        try:
                            while True:
                                data = progress_queue.get_nowait()
                                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                if data.get("status") in ["done", "error"]:
                                    break
                        except queue.Empty:
                            break
                        break
                        
                except Exception as e:
                    yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                    break
                    
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
        finally:
            # 스레드가 아직 실행 중이면 종료될 때까지 대기
            if indexing_thread.is_alive():
                indexing_thread.join(timeout=5.0)
    
    return StreamingResponse(
        generate_progress(), 
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )
