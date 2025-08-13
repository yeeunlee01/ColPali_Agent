import logging
from typing import Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

from be.config import ColPaliConfig, settings

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """데이터베이스 연결 실패 시 발생하는 예외"""
    pass

 
class QdrantManager:
    """
    Qdrant 벡터 데이터베이스를 관리하는 싱글톤 클래스
    ColPaliRAGService의 _initialize_qdrant() 로직을 기반으로 작성
    """
    
    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self._url: str = settings.qdrant_url
        self._collection_name: str = ColPaliConfig.COLLECTION_NAME
        self._initialized: bool = False
        
    @property
    def is_initialized(self) -> bool:
        """데이터베이스가 초기화되었는지 확인"""
        return self._initialized and self._client is not None
    
    @property
    def collection_name(self) -> str:
        """현재 사용 중인 컬렉션 이름 반환"""
        return self._collection_name

    def create_collection(self):
        """
        Qdrant 컬렉션 존재 확인 및 생성
        """
        try:
            # 컬렉션이 이미 존재하는지 확인
            collections = self._client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if self._collection_name in existing_collections:
                logger.info(f"컬렉션이 이미 존재합니다: {self._collection_name}")
                return
            
            # 새 컬렉션 생성 (ColPali multi-vector 지원)
            self._client.create_collection(
                collection_name=self._collection_name,
                on_disk_payload=True,  # 페이로드를 디스크에 저장
                vectors_config=models.VectorParams(
                    size=128,  # 벡터 차원 수 (128차원)
                    distance=models.Distance.COSINE,  # 코사인 유사도 측정 방식 사용
                    on_disk=True,  # 원본 벡터를 디스크로 이동하여 메모리 사용량 감소
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM  # 다중 벡터 중 최대 유사도 사용
                    ),
                    quantization_config=models.BinaryQuantization(
                        binary=models.BinaryQuantizationConfig(
                            always_ram=True  # 양자화된 벡터만 RAM에 유지하여 검색 속도 향상
                        ),
                    ),
                ),
            )
            logger.info(f"새 컬렉션 생성 완료: {self._collection_name}")
            
        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {e}")
            raise
    
    def initialize(self) -> bool:
        """
        Qdrant 클라이언트 및 컬렉션 초기화
        
        Returns:
            bool: 초기화 성공 여부
            
        Raises:
            DatabaseConnectionError: 데이터베이스 연결/컬렉션 생성 실패 시
        """
        if self.is_initialized:
            logger.info("Qdrant 클라이언트가 이미 초기화되어 있습니다.")
            return True
            
        try:
            # 클라이언트 생성
            self._client = QdrantClient(self._url)
            
            # 컬렉션 확인 및 생성
            self.create_collection()
            print("Qdrant 컬렉션 생성 완료")
            
            self._initialized = True
            logger.info("Qdrant 데이터베이스 초기화 완료")
            return True
            
        except Exception as e:
            print(f"Qdrant 컬렉션 생성 중 오류: {e}")
            logger.error(f"Qdrant 초기화 실패: {e}")
            raise DatabaseConnectionError(f"Qdrant 초기화 실패: {e}")
    
    def get_client(self) -> QdrantClient:
        """
        Qdrant 클라이언트 반환
        
        Returns:
            QdrantClient: 연결된 클라이언트
            
        Raises:
            DatabaseConnectionError: 클라이언트가 초기화되지 않은 경우
        """
        if not self.is_initialized:
            raise DatabaseConnectionError("Qdrant 클라이언트가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._client
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        컬렉션 정보 반환 (get_status에서 사용)
        
        Returns:
            Dict: 컬렉션 정보
        """
        if not self.is_initialized:
            raise DatabaseConnectionError("Qdrant 클라이언트가 초기화되지 않았습니다.")
        
        try:
            collection_info = self._client.get_collection(self._collection_name)
            return {
                "name": self._collection_name,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            logger.error(f"컬렉션 정보 조회 실패: {e}")
            raise
    
    def query_points(self, query_vector, limit: int = 10, timeout: int = 100, 
                    search_params=None) -> models.QueryResponse:
        """
        벡터 검색 (query 메소드에서 사용)
        
        Args:
            query_vector: 검색 벡터
            limit: 결과 개수 제한
            timeout: 검색 타임아웃
            search_params: 검색 파라미터
            
        Returns:
            QueryResponse: 검색 결과
        """
        if not self.is_initialized:
            raise DatabaseConnectionError("Qdrant 클라이언트가 초기화되지 않았습니다.")
        
        return self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            limit=limit,
            timeout=timeout,
            search_params=search_params
        )
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        데이터베이스 정보 반환 (상태 체크용)
        
        Returns:
            Dict: 데이터베이스 정보
        """
        if not self.is_initialized:
            return {
                "initialized": False,
                "url": self._url,
                "collection_name": self._collection_name
            }
        
        try:
            collection_info = self.get_collection_info()
            return {
                "initialized": True,
                "url": self._url,
                "collection_name": self._collection_name,
                "points_count": collection_info["points_count"]
            }
        except Exception as e:
            logger.error(f"데이터베이스 정보 조회 실패: {e}")
            return {
                "initialized": True,
                "url": self._url,
                "error": str(e)
            }
    
    def disconnect(self):
        """연결 해제"""
        if self._client is not None:
            try:
                self._client.close()
            except:
                pass  # 정리 시 에러는 무시
            self._client = None
            logger.info("Qdrant 클라이언트 연결 해제 완료")
            
        self._initialized = False


qdrant_manager = QdrantManager()