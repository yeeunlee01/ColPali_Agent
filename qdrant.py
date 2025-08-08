from qdrant_client import QdrantClient
from qdrant_client.http import models

# Qdrant 컬렉션 생성
def create_qdrant_collection(qdrant_client, collection_name):
    qdrant_client.create_collection(
        collection_name=collection_name,
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
    return True

def upsert_to_qdrant(points, qdrant_client, collection_name):
    """
    Qdrant 벡터 데이터베이스에 데이터를 업서트(삽입 또는 업데이트)하는 함수
    
    Args:
        batch: 업서트할 데이터 배치
        
    Returns:
        bool: 업서트 성공 여부
    """
    try:
        qdrant_client.upsert(
            collection_name=collection_name,  # 데이터를 저장할 컬렉션 이름
            points=points,                    # 업서트할 데이터 포인트
            wait=False,                       # 비동기 처리를 위해 응답 대기하지 않음
        )
    except Exception as e:
        print(f"Error during upsert: {e}")    # 오류 발생 시 출력
        return False                          # 실패 시 False 반환
    return True  