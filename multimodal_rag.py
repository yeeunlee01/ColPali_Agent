import os
import torch
import time
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from tqdm import tqdm
from PIL import Image
from pdf import convert_pdf_to_images
from qdrant import create_qdrant_collection, upsert_to_qdrant

from colpali_engine.models import ColPali, ColPaliProcessor

model_name = (
    "vidore/colpali-v1.3" 
)
colpali_model = ColPali.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="mps",  # GPU는 "cuda:0", CPU는 "cpu",  Apple Silicon은 "mps" 사용
)
colpali_processor = ColPaliProcessor.from_pretrained(
    "vidore/colpaligemma2-3b-pt-448-base"
)

# Qdrant 클라이언트 생성 (메모리 기반)
qdrant_client = QdrantClient(":memory:")
collection_name = "colpali-test"

try:
    create_qdrant_collection(qdrant_client, collection_name)
    print("Qdrant 컬렉션 생성 완료")
except Exception as e:
    print(f"Qdrant 컬렉션 생성 중 오류 발생: {e}")
    exit()

torch.cuda.empty_cache()

image_dir = "./output_images"
pdf_path = "./data/2407.01449v6.pdf"
image_files = convert_pdf_to_images(pdf_path, image_dir)

batch_size = 4

with tqdm(total=len(image_files), desc="Indexing Progress") as pbar:
    for i in range(0, len(image_files), batch_size):
        batch_files = image_files[i : i + batch_size]
        images = [Image.open(img_path) for img_path in batch_files]

        with torch.no_grad():
            batch_images = colpali_processor.process_images(images).to(colpali_model.device)
            image_embeddings = colpali_model(**batch_images)
        points = []
        for j, embedding in enumerate(image_embeddings):
            multivector = embedding.cpu().float().numpy().tolist()
            points.append(models.PointStruct(
                id=i + j,
                vector=multivector,
                payload={"source": "pdf_image", "file_path": batch_files[j]},
            ))
        try:
            upsert_to_qdrant(points, qdrant_client, collection_name)
        except Exception as e:
            print(f"업로드 중 오류 발생: {e}")
            continue
        pbar.update(len(batch_files))

print("인덱싱 완료")

query_text = "What is the architecture of ColPali?"

with torch.no_grad():
    batch_query = colpali_processor.process_queries([query_text]).to(colpali_model.device)
    query_embeddings = colpali_model(**batch_query)

multivector_query = query_embeddings[0].cpu().float().numpy().tolist()

start_time = time.time()
search_result = qdrant_client.query_points(
    collection_name=collection_name, # 검색할 컬렉션 이름
    query=multivector_query,
    limit=10, # 최대 10개 결과 반환
    timeout=100, # 쿼리 타임아웃 (100ms)
    search_params=models.SearchParams(
        quantization=models.QuantizationSearchParams(
            ignore=False, #양자화 무시하지 않음
            rescore=True,  # 검색 후 원본 벡터로 복구
            oversampling=2.0, # 양자화 검색 시 2배 더 많은 후보 검색 (정확도 향상)
        )
    )
)
end_time = time.time()

elapsed_time = end_time - start_time
print(f"검색 소요 시간: {elapsed_time:.2f}초")
print(search_result.points)
