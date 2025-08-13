import os
import torch
from typing import Optional


class ColPaliConfig:
    """ColPali 모델 및 서비스 설정"""
    
    # 모델 설정
    MODEL_NAME = "vidore/colpali-v1.3"
    PROCESSOR_NAME = "vidore/colpaligemma2-3b-pt-448-base"
    
    # Qdrant 설정
    COLLECTION_NAME = "colpali-documents"
    QDRANT_URL = ":memory:"  # 메모리 DB 사용, 실제 배포시에는 외부 URL 사용
    
    # 처리 설정
    BATCH_SIZE = 4
    
    # 디바이스 설정 (자동 감지)
    @staticmethod
    def get_device() -> str:
        """사용 가능한 최적의 디바이스 반환"""
        if torch.cuda.is_available():
            return "cuda:0"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    # 파일 경로 설정
    DEFAULT_DATA_DIR = "./data"
    DEFAULT_OUTPUT_DIR = "./temp_images"
    
    # 검색 설정
    DEFAULT_SEARCH_LIMIT = 5
    SEARCH_TIMEOUT = 100
    
    # 처리 설정
    TORCH_DTYPE = torch.bfloat16


class Settings:
    """환경변수 기반 설정"""
    
    def __init__(self):
        self.data_dir = os.getenv("COLPALI_DATA_DIR", ColPaliConfig.DEFAULT_DATA_DIR)
        self.output_dir = os.getenv("COLPALI_OUTPUT_DIR", ColPaliConfig.DEFAULT_OUTPUT_DIR)
        self.qdrant_url = os.getenv("QDRANT_URL", ColPaliConfig.QDRANT_URL)
        self.batch_size = int(os.getenv("COLPALI_BATCH_SIZE", ColPaliConfig.BATCH_SIZE))
        self.device = os.getenv("COLPALI_DEVICE", ColPaliConfig.get_device())


# 전역 설정 인스턴스
settings = Settings()