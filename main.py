import os
import tempfile
import shutil
import asyncio
import json
import queue
import threading
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from be.services.colpali_service import ColPaliRAGService
from fe.ui import HTML_TEMPLATE

app = FastAPI(title="ColPali RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
rag_service = ColPaliRAGService()

# 정적 파일 서빙
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 업로드된 이미지를 서빙하기 위한 임시 디렉토리
TEMP_IMAGE_DIR = "temp_images"
if not os.path.exists(TEMP_IMAGE_DIR):
    os.makedirs(TEMP_IMAGE_DIR)
app.mount("/images", StaticFiles(directory=TEMP_IMAGE_DIR), name="images")


class QueryRequest(BaseModel):
    query: str
    limit: int = 5


@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """프론트엔드 HTML 페이지 반환"""
    return HTMLResponse(content=HTML_TEMPLATE)


@app.get("/pdf-list")
async def get_pdf_list():
    """./data 폴더의 PDF 파일 목록 반환"""
    return rag_service.get_pdf_list()


@app.get("/pdf-preview")
async def get_pdf_preview(pdf_path: str):
    """PDF 첫 페이지 미리보기 이미지 생성"""
    result = rag_service.get_pdf_preview(pdf_path, TEMP_IMAGE_DIR)
    
    if result.get("success") and result.get("preview_path"):
        # 파일명만 추출해서 반환
        preview_path = result["preview_path"]
        filename = os.path.basename(preview_path)
        result["image_name"] = filename
    
    return result


class IndexPdfRequest(BaseModel):
    pdf_path: str


@app.post("/index-pdf")
async def index_pdf(request: IndexPdfRequest):
    """선택된 PDF 인덱싱 (논블로킹)"""
    return rag_service.process_pdf(request.pdf_path)


@app.get("/index-pdf-stream")
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
                result = rag_service.process_pdf(pdf_path, progress_callback)
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


@app.post("/query")
async def query_documents(request: QueryRequest):
    """문서 검색"""
    result = rag_service.query(request.query, request.limit)
    
    # 결과에서 이미지 경로를 웹 접근 가능한 경로로 변환
    if result.get("success") and result.get("results"):
        for item in result["results"]:
            if item.get("image_path") and os.path.exists(item["image_path"]):
                # 이미지 파일 경로를 /images 경로 형태로 변환
                full_path = item["image_path"]
                
                # temp_images 디렉토리 기준으로 상대 경로 생성
                if TEMP_IMAGE_DIR in full_path:
                    relative_path = os.path.relpath(full_path, TEMP_IMAGE_DIR)
                    item["image_path"] = relative_path
                else:
                    # 기존 파일이 temp_images에 없으면 복사
                    filename = os.path.basename(full_path)
                    pdf_name = item.get("pdf_name", "unknown").replace('.pdf', '')
                    
                    # PDF별 서브디렉토리 생성
                    pdf_dir = os.path.join(TEMP_IMAGE_DIR, pdf_name)
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


@app.get("/status")
async def get_status():
    """서비스 상태 확인"""
    return rag_service.get_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)