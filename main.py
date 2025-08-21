import os
# tokenizers 경고 메시지 제거
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from be.config import api_config
from be.api.frontend import router as frontend_router
from be.api.pdf import router as pdf_router
from be.api.rag import router as rag_router
from be.api.system import router as system_router

app = FastAPI(title="ColPali RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 디렉토리 생성
if not os.path.exists(api_config.STATIC_DIR):
    os.makedirs(api_config.STATIC_DIR)

if not os.path.exists(api_config.TEMP_IMAGE_DIR):
    os.makedirs(api_config.TEMP_IMAGE_DIR)

app.mount("/static", StaticFiles(directory=api_config.STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=api_config.TEMP_IMAGE_DIR), name="images")

app.include_router(frontend_router)
app.include_router(pdf_router)
app.include_router(rag_router)
app.include_router(system_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)