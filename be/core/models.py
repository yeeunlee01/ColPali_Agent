import torch
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from colpali_engine.models import ColPali, ColPaliProcessor
from be.config import ColPaliConfig, settings

logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """모델 로딩 실패 시 발생하는 예외"""
    pass


class ColPaliModelManager:
    """
    ColPali 모델과 프로세서를 관리하는 싱글톤 클래스

    """
    
    def __init__(self):
        self._model: Optional[ColPali] = None
        self._processor: Optional[ColPaliProcessor] = None
        
        self.model_name = ColPaliConfig.MODEL_NAME
        self.processor_name = ColPaliConfig.PROCESSOR_NAME
        self.torch_dtype = ColPaliConfig.TORCH_DTYPE
        self.device = settings.device
        
        self._initialized: bool = False
        self._loading: bool = False
    
    @property
    def is_initialized(self) -> bool:
        """모델이 초기화되었는지 확인"""
        return self._initialized and self._model is not None and self._processor is not None
    
    @property
    def is_loading(self) -> bool:
        """모델이 로딩 중인지 확인"""
        return self._loading
    
    def initialize(self, force_reload: bool = False) -> bool:
        """
        ColPali 모델과 프로세서 초기화
        기존 ColPaliRAGService._initialize_models() 로직 사용
        
        Args:
            force_reload: 이미 로드된 모델을 강제로 다시 로드할지 여부
            
        Returns:
            bool: 초기화 성공 여부
            
        Raises:
            ModelLoadError: 모델 로딩 실패 시
        """
        if self.is_initialized and not force_reload:
            logger.info("ColPali 모델이 이미 로드되어 있습니다.")
            return True
            
        if self._loading:
            logger.warning("ColPali 모델이 이미 로딩 중입니다.")
            return False
            
        try:
            self._loading = True
            
            # 기존 모델이 있다면 메모리 해제
            if force_reload and self.is_initialized:
                self._cleanup_models()
            
            # 기존 ColPaliRAGService._initialize_models() 로직
            print("ColPali 모델 로딩 중...")
            logger.info(f"ColPali 모델 로딩 시작: {self.model_name}")
            
            # ColPali 모델 로딩
            self._model = ColPali.from_pretrained(
                self.model_name,
                torch_dtype=self.torch_dtype,
                device_map=self.device,
            )
            logger.info(f"ColPali 모델 로딩 완료: {self.model_name}")
            
            # ColPali 프로세서 로딩
            self._processor = ColPaliProcessor.from_pretrained(
                self.processor_name
            )
            logger.info(f"ColPali 프로세서 로딩 완료: {self.processor_name}")
            
            # 메모리 정리 (기존 로직)
            torch.cuda.empty_cache()
            
            self._initialized = True
            print("모델 로딩 완료")
            logger.info("ColPali 모델 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"ColPali 모델 로딩 실패: {e}")
            self._cleanup_models()
            raise ModelLoadError(f"ColPali 모델 로딩 실패: {e}")
            
        finally:
            self._loading = False
    
    def get_model(self) -> ColPali:
        """
        ColPali 모델 반환
        
        Returns:
            ColPali: 로드된 모델
            
        Raises:
            ModelLoadError: 모델이 로드되지 않은 경우
        """
        if not self.is_initialized:
            raise ModelLoadError("ColPali 모델이 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._model
    
    def get_processor(self) -> ColPaliProcessor:
        """
        ColPali 프로세서 반환
        
        Returns:
            ColPaliProcessor: 로드된 프로세서
            
        Raises:
            ModelLoadError: 프로세서가 로드되지 않은 경우
        """
        if not self.is_initialized:
            raise ModelLoadError("ColPali 프로세서가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._processor
    
    @contextmanager
    def inference_mode(self):
        """
        추론 모드 컨텍스트 매니저
        torch.no_grad()와 모델 eval() 모드를 자동으로 관리

        """
        if not self.is_initialized:
            raise ModelLoadError("모델이 초기화되지 않았습니다.")
            
        model = self.get_model()
        was_training = model.training
        
        try:
            model.eval()
            with torch.no_grad():
                yield
        finally:
            if was_training:
                model.train()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 반환
        
        Returns:
            Dict: 모델 관련 정보
        """
        if not self.is_initialized:
            return {
                "initialized": False,
                "model_name": self.model_name,
                "processor_name": self.processor_name,
                "device": self.device,
                "loading": self._loading
            }
        
        # 모델 메모리 사용량 계산 (대략적)
        model_memory = 0
        if self._model is not None:
            for param in self._model.parameters():
                model_memory += param.numel() * param.element_size()
        
        return {
            "initialized": True,
            "model_name": self.model_name,
            "processor_name": self.processor_name,
            "device": self.device,
            "model_memory_mb": round(model_memory / (1024 * 1024), 2),
            "model_dtype": str(self.torch_dtype),
            "loading": self._loading
        }
    
    def _cleanup_models(self):
        """모델과 프로세서 메모리 해제"""
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("ColPali 모델 메모리 해제")
            
        if self._processor is not None:
            del self._processor
            self._processor = None
            logger.info("ColPali 프로세서 메모리 해제")
            
        self._initialized = False
        self._clear_cache()
    
    def _clear_cache(self):
        """GPU/CPU 캐시 정리 (기존 로직과 동일)"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
    def unload(self):
        """모델 언로드 및 메모리 해제"""
        logger.info("ColPali 모델 언로드 시작...")
        self._cleanup_models()
        logger.info("ColPali 모델 언로드 완료")
    
    def reload(self):
        """모델 재로드"""
        logger.info("ColPali 모델 재로드 시작...")
        self.initialize(force_reload=True)
        logger.info("ColPali 모델 재로드 완료")

colpali_manager = ColPaliModelManager()