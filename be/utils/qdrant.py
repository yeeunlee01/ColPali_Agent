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