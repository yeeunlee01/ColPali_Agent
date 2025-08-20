from be.services.colpali_service import ColPaliRAGService

class ServiceManager:
    """서비스 인스턴스 관리 (싱글톤 패턴)"""
    _instance = None
    _rag_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def rag_service(self):
        if self._rag_service is None:
            self._rag_service = ColPaliRAGService()
        return self._rag_service

service_manager = ServiceManager()