import os
import torch
import time
import tempfile
import glob
import shutil
import logging
import base64
from typing import List, Dict, Any, Callable, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from PIL import Image
from langchain_core.messages import HumanMessage

from be.core.models import colpali_manager, azure_openai_manager
from be.core.database import qdrant_manager
from be.utils.pdf import convert_pdf_to_images
from be.utils.qdrant import upsert_to_qdrant
from be.config import ColPaliConfig, settings

logger = logging.getLogger(__name__)

class ColPaliRAGService:
    def __init__(self):
        self.collection_name = ColPaliConfig.COLLECTION_NAME
        self.batch_size = settings.batch_size
        self.model_manager = colpali_manager
        self.db_manager = qdrant_manager
        self.llm_manager = azure_openai_manager
        if not self.model_manager.is_initialized:
            self.model_manager.initialize() 
        if not self.db_manager.is_initialized:
            self.db_manager.initialize()
        if not self.llm_manager.is_initialized:
            self.llm_manager.initialize()
    @property
    def colpali_model(self):
        """ColPali 모델 반환"""
        return self.model_manager.get_model()
    
    @property
    def colpali_processor(self):
        """ColPali 프로세서 반환"""
        return self.model_manager.get_processor()
    
    @property
    def qdrant_client(self):
        """Qdrant 클라이언트 반환"""
        return self.db_manager.get_client()
    
    @property
    def azure_llm(self):
        """Azure OpenAI LLM 반환"""
        return self.llm_manager.get_llm()
    
    def process_pdf(self, pdf_file_path: str, progress_callback: Optional[Callable] = None, output_dir: str = None) -> Dict[str, Any]:
        """PDF 파일을 처리하고 인덱싱"""
        try:
            if output_dir is None:
                output_dir = settings.output_dir
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
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
    
    def query(self, query_text: str, limit: int = None) -> Dict[str, Any]:
        """텍스트 쿼리로 검색 수행"""
        try:
            start_time = time.time()
            
            with torch.no_grad():
                batch_query = self.colpali_processor.process_queries([query_text]).to(
                    self.colpali_model.device
                )
                query_embeddings = self.colpali_model(**batch_query)
            
            multivector_query = query_embeddings[0].cpu().float().numpy().tolist()
            
            if limit is None:
                limit = ColPaliConfig.DEFAULT_SEARCH_LIMIT
            
            search_result = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=multivector_query,
                limit=limit,
                timeout=ColPaliConfig.SEARCH_TIMEOUT,
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
    
    def get_pdf_list(self, data_dir: str = None) -> Dict[str, Any]:
        """데이터 폴더에서 PDF 파일 목록 반환"""
        try:
            if data_dir is None:
                data_dir = settings.data_dir
                
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
    
    def get_pdf_preview(self, pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
        """PDF의 첫 페이지 미리보기 이미지 생성"""
        try:
            if not os.path.exists(pdf_path):
                return {
                    "success": False,
                    "message": "PDF 파일이 존재하지 않습니다."
                }
            
            # 출력 디렉토리 설정 및 생성
            if output_dir is None:
                output_dir = settings.output_dir
                
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
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"이미지 인코딩 실패: {e}")
            return ""
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """이미지에서 텍스트 추출 (Azure OpenAI Vision 사용)"""
        try:
            if not os.path.exists(image_path):
                return ""
            
            # 이미지를 base64로 인코딩
            base64_image = self._encode_image_to_base64(image_path)
            if not base64_image:
                return ""
            
            # Azure OpenAI Vision을 사용하여 텍스트 추출
            llm = self.azure_llm
            
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "이 이미지에 있는 모든 텍스트를 정확히 추출해주세요. 텍스트만 반환하고 다른 설명은 하지 마세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            )
            
            response = llm.invoke([message])
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"이미지에서 텍스트 추출 실패: {e}")
            return ""
    
    def chat_query(self, query_text: str, limit: int = None, use_context: bool = True) -> Dict[str, Any]:
        """텍스트 쿼리로 검색하고 Azure LLM으로 답변 생성"""
        try:
            start_time = time.time()
            
            # 1. 기존 검색 기능으로 관련 페이지들 찾기
            search_result = self.query(query_text, limit)
            
            if not search_result["success"]:
                return search_result
            
            # 2. 검색된 페이지들에서 텍스트 추출
            context_texts = []
            page_info = []
            
            if use_context and search_result["results"]:
                for result in search_result["results"][:5]:  # 상위 5개 페이지만 사용
                    image_path = result["image_path"]
                    if os.path.exists(image_path):
                        extracted_text = self._extract_text_from_image(image_path)
                        if extracted_text:
                            context_texts.append(extracted_text)
                            page_info.append({
                                "page_number": result["page_number"],
                                "pdf_name": result["pdf_name"],
                                "score": result["score"]
                            })
            
            # 3. 컨텍스트와 함께 프롬프트 구성
            if context_texts:
                context = "\n\n---\n\n".join(context_texts)
                prompt = f"""
                다음은 사용자의 질문과 관련된 문서 내용입니다:

                {context}

                ---

                위 문서 내용을 바탕으로 다음 질문에 답변해주세요:
                질문: {query_text}

                답변할 때:
                1. 문서 내용에 기반하여 정확하고 구체적으로 답변하세요
                2. 문서에서 직접 찾을 수 없는 정보에 대해서는 "문서에서 해당 정보를 찾을 수 없습니다"라고 명시하세요
                3. 가능한 한 인용이나 참조를 포함하세요
                """
            else:
                prompt = f"""
                질문: {query_text}

                관련 문서를 찾을 수 없어서 일반적인 지식을 바탕으로 답변드리겠습니다. 더 정확한 답변을 위해서는 관련 문서를 업로드해주세요.
                """
                            
            # 4. Azure LLM으로 답변 생성
            llm = self.azure_llm
            response = llm.invoke(prompt)
            
            end_time = time.time()
            
            return {
                "success": True,
                "query": query_text,
                "answer": response.content,
                "context_used": bool(context_texts),
                "source_pages": page_info,
                "search_results": search_result.get("results", []),
                "total_time": end_time - start_time,
                "search_time": search_result.get("search_time", 0)
            }
            
        except Exception as e:
            logger.error(f"채팅 쿼리 처리 중 오류: {e}")
            return {
                "success": False,
                "message": f"채팅 쿼리 처리 중 오류: {str(e)}",
                "search_results": []
            }