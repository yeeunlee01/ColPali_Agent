import os
import torch
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class ColPaliConfig:
    """ColPali 모델 및 서비스 설정"""
    
    MODEL_NAME = "vidore/colpali-v1.3"
    PROCESSOR_NAME = "vidore/colpaligemma2-3b-pt-448-base"
    COLLECTION_NAME = "colpali-documents"
    QDRANT_URL = ":memory:"  # 메모리 DB 사용, 실제 배포시에는 외부 URL 사용
    BATCH_SIZE = 4
    
    @staticmethod
    def get_device() -> str:
        """사용 가능한 최적의 디바이스 반환"""
        if torch.cuda.is_available():
            return "cuda:0"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    DEFAULT_DATA_DIR = "./data"
    DEFAULT_OUTPUT_DIR = "./temp_images"
    
    DEFAULT_SEARCH_LIMIT = 5
    SEARCH_TIMEOUT = 100
    
    TORCH_DTYPE = torch.bfloat16


class AzureConfig:
    """Azure OpenAI 설정"""
    
    def __init__(self):
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT")
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
        self.azure_api_key = os.getenv("AZURE_API_KEY")
        self.azure_model = os.getenv("AZURE_MODEL", "gpt-4o")
        self.azure_deployment = os.getenv("AZURE_DEPLOYMENT")
        self.n = 1
        self.temperature = 0
        self.max_tokens = 10000
        self.streaming = False
        self.verbose = True

azure_config = AzureConfig()


class Settings:
    """환경변수 기반 설정"""
    
    def __init__(self):
        self.data_dir = os.getenv("COLPALI_DATA_DIR", ColPaliConfig.DEFAULT_DATA_DIR)
        self.output_dir = os.getenv("COLPALI_OUTPUT_DIR", ColPaliConfig.DEFAULT_OUTPUT_DIR)
        self.qdrant_url = os.getenv("QDRANT_URL", ColPaliConfig.QDRANT_URL)
        self.batch_size = int(os.getenv("COLPALI_BATCH_SIZE", ColPaliConfig.BATCH_SIZE))
        self.device = os.getenv("COLPALI_DEVICE", ColPaliConfig.get_device())

settings = Settings()