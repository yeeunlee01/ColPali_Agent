import os
import torch
import time
import tempfile
import glob
import shutil
from typing import List, Dict, Any, Callable, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from tqdm import tqdm
from PIL import Image
from pdf import convert_pdf_to_images
from qdrant import create_qdrant_collection, upsert_to_qdrant
from colpali_engine.models import ColPali, ColPaliProcessor


class ColPaliRAGService:
    def __init__(self):
        self.model_name = "vidore/colpali-v1.3"
        self.processor_name = "vidore/colpaligemma2-3b-pt-448-base"
        self.collection_name = "colpali-documents"
        self.batch_size = 4
        
        # 모델 초기화
        self._initialize_models()
        self._initialize_qdrant()
    
    def _initialize_models(self):
        """ColPali 모델과 프로세서 초기화"""
        print("ColPali 모델 로딩 중...")
        self.colpali_model = ColPali.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            device_map="mps",  # GPU는 "cuda:0", CPU는 "cpu", Apple Silicon은 "mps"
        )
        self.colpali_processor = ColPaliProcessor.from_pretrained(
            self.processor_name
        )
        torch.cuda.empty_cache()
        print("모델 로딩 완료")
    
    def _initialize_qdrant(self):
        """Qdrant 클라이언트 초기화"""
        self.qdrant_client = QdrantClient(":memory:")
        try:
            create_qdrant_collection(self.qdrant_client, self.collection_name)
            print("Qdrant 컬렉션 생성 완료")
        except Exception as e:
            print(f"Qdrant 컬렉션 생성 중 오류: {e}")
            raise
    
    def process_pdf(self, pdf_file_path: str, progress_callback: Optional[Callable] = None, output_dir: str = "./temp_images") -> Dict[str, Any]:
        """PDF 파일을 처리하고 인덱싱"""
        try:
            # 웹에서 접근 가능한 디렉토리에 이미지 저장
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # PDF 파일명을 기반으로 서브디렉토리 생성
            pdf_name = os.path.basename(pdf_file_path).replace('.pdf', '')
            pdf_image_dir = os.path.join(output_dir, pdf_name)
            if not os.path.exists(pdf_image_dir):
                os.makedirs(pdf_image_dir)
            
            image_files = convert_pdf_to_images(pdf_file_path, pdf_image_dir)
            total_pages = len(image_files)
            
            if progress_callback:
                progress_callback({
                    "status": "started",
                    "message": f"PDF 변환 완료. {total_pages}페이지 인덱싱 시작...",
                    "current_page": 0,
                    "total_pages": total_pages,
                    "percentage": 0
                })
            
            total_indexed = 0
            
            for i in range(0, len(image_files), self.batch_size):
                batch_files = image_files[i : i + self.batch_size]
                images = [Image.open(img_path) for img_path in batch_files]
                
                # 진행상황 업데이트 - 임베딩 생성 중
                if progress_callback:
                    progress_callback({
                        "status": "processing",
                        "message": f"페이지 {i+1}-{min(i+len(batch_files), total_pages)} 임베딩 생성 중...",
                        "current_page": i,
                        "total_pages": total_pages,
                        "percentage": int((i / total_pages) * 100)
                    })
                
                with torch.no_grad():
                    batch_images = self.colpali_processor.process_images(images).to(
                        self.colpali_model.device
                    )
                    image_embeddings = self.colpali_model(**batch_images)
                
                points = []
                for j, embedding in enumerate(image_embeddings):
                    multivector = embedding.cpu().float().numpy().tolist()
                    points.append(models.PointStruct(
                        id=total_indexed + j,
                        vector=multivector,
                        payload={
                            "source": "pdf_image", 
                            "file_path": batch_files[j],
                            "page_number": i + j + 1,
                            "pdf_name": os.path.basename(pdf_file_path)
                        },
                    ))
                
                # 진행상황 업데이트 - 벡터 저장 중
                if progress_callback:
                    progress_callback({
                        "status": "storing",
                        "message": f"페이지 {i+1}-{min(i+len(batch_files), total_pages)} 벡터 저장 중...",
                        "current_page": i,
                        "total_pages": total_pages,
                        "percentage": int((i / total_pages) * 100)
                    })
                
                try:
                    upsert_to_qdrant(points, self.qdrant_client, self.collection_name)
                    total_indexed += len(points)
                    
                    # 진행상황 업데이트 - 배치 완료
                    current_page = min(i + len(batch_files), total_pages)
                    if progress_callback:
                        progress_callback({
                            "status": "progress",
                            "message": f"{current_page}/{total_pages} 페이지 완료",
                            "current_page": current_page,
                            "total_pages": total_pages,
                            "percentage": int((current_page / total_pages) * 100)
                        })
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback({
                            "status": "error",
                            "message": f"페이지 {i+1}-{min(i+len(batch_files), total_pages)} 저장 중 오류: {e}",
                            "current_page": i,
                            "total_pages": total_pages,
                            "percentage": int((i / total_pages) * 100)
                        })
                    continue
            
            # 완료 알림
            if progress_callback:
                progress_callback({
                    "status": "completed",
                    "message": f"인덱싱 완료! 총 {total_indexed}페이지 처리됨",
                    "current_page": total_pages,
                    "total_pages": total_pages,
                    "percentage": 100
                })
            
            return {
                "success": True,
                "message": f"PDF 인덱싱 완료",
                "total_pages": len(image_files),
                "indexed_pages": total_indexed
            }
        
        except Exception as e:
            if progress_callback:
                progress_callback({
                    "status": "error",
                    "message": f"PDF 처리 중 오류: {str(e)}",
                    "current_page": 0,
                    "total_pages": 0,
                    "percentage": 0
                })
            return {
                "success": False,
                "message": f"PDF 처리 중 오류: {str(e)}"
            }
    
    def query(self, query_text: str, limit: int = 5) -> Dict[str, Any]:
        """텍스트 쿼리로 검색 수행"""
        try:
            start_time = time.time()
            
            with torch.no_grad():
                batch_query = self.colpali_processor.process_queries([query_text]).to(
                    self.colpali_model.device
                )
                query_embeddings = self.colpali_model(**batch_query)
            
            multivector_query = query_embeddings[0].cpu().float().numpy().tolist()
            
            search_result = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=multivector_query,
                limit=limit,
                timeout=100,
                search_params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        ignore=False,
                        rescore=True,
                        oversampling=2.0,
                    )
                )
            )
            
            end_time = time.time()
            
            results = []
            for point in search_result.points:
                results.append({
                    "score": float(point.score),
                    "page_number": point.payload.get("page_number", 0),
                    "pdf_name": point.payload.get("pdf_name", ""),
                    "image_path": point.payload.get("file_path", "")
                })
            
            return {
                "success": True,
                "query": query_text,
                "results": results,
                "search_time": end_time - start_time,
                "total_results": len(results)
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"검색 중 오류: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """서비스 상태 정보 반환"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "success": True,
                "model_loaded": True,
                "collection_name": self.collection_name,
                "total_documents": collection_info.points_count
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"상태 확인 중 오류: {str(e)}"
            }
    
    def get_pdf_list(self, data_dir: str = "./data") -> Dict[str, Any]:
        """데이터 폴더에서 PDF 파일 목록 반환"""
        try:
            if not os.path.exists(data_dir):
                return {
                    "success": False,
                    "message": f"데이터 폴더가 존재하지 않습니다: {data_dir}"
                }
            
            pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
            
            pdf_list = []
            for pdf_path in pdf_files:
                pdf_name = os.path.basename(pdf_path)
                pdf_size = os.path.getsize(pdf_path)
                
                pdf_list.append({
                    "name": pdf_name,
                    "path": pdf_path,
                    "size": pdf_size,
                    "size_mb": round(pdf_size / (1024 * 1024), 2)
                })
            
            return {
                "success": True,
                "pdf_files": pdf_list,
                "total_files": len(pdf_list)
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"PDF 목록 조회 중 오류: {str(e)}"
            }
    
    def get_pdf_preview(self, pdf_path: str, output_dir: str = "./temp_images") -> Dict[str, Any]:
        """PDF의 첫 페이지 미리보기 이미지 생성"""
        try:
            if not os.path.exists(pdf_path):
                return {
                    "success": False,
                    "message": "PDF 파일이 존재하지 않습니다."
                }
            
            # 출력 디렉토리 생성
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # PDF 파일명을 기반으로 미리보기 파일명 생성
            pdf_name_without_ext = os.path.basename(pdf_path).replace('.pdf', '')
            preview_filename = f"preview_{pdf_name_without_ext}.png"
            preview_path = os.path.join(output_dir, preview_filename)
            
            # 이미 미리보기가 존재하면 재사용
            if os.path.exists(preview_path):
                return {
                    "success": True,
                    "preview_path": preview_path,
                    "pdf_name": os.path.basename(pdf_path)
                }
            
            # 미리보기 이미지 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                image_files = convert_pdf_to_images(pdf_path, temp_dir, max_pages=1)
                
                if not image_files:
                    return {
                        "success": False,
                        "message": "PDF에서 이미지를 생성할 수 없습니다."
                    }
                
                # 첫 번째 페이지 이미지를 temp_images로 복사
                first_page_temp = image_files[0]
                shutil.copy2(first_page_temp, preview_path)
                
                return {
                    "success": True,
                    "preview_path": preview_path,
                    "pdf_name": os.path.basename(pdf_path)
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"미리보기 생성 중 오류: {str(e)}"
            }