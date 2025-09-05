"""API 호출 관련 JavaScript 함수들"""

def get_api_functions():
    """모든 API 호출 함수들 반환"""
    return """
        // API 기본 설정
        const API_BASE_URL = window.location.origin;
        
        // 전역 변수
        let selectedPdfPath = null;
        let indexedPdfs = new Set();
        let isProcessing = false;
        
        /**
         * PDF 목록 조회
         */
        async function fetchPdfList() {
            try {
                const response = await fetch('/pdf-list');
                return await response.json();
            } catch (error) {
                console.error('PDF 목록 조회 실패:', error);
                return { success: false, message: error.message };
            }
        }
        
        /**
         * PDF 미리보기 조회
         */
        async function fetchPdfPreview(pdfPath) {
            try {
                const response = await fetch(`/pdf-preview?pdf_path=${encodeURIComponent(pdfPath)}`);
                return await response.json();
            } catch (error) {
                console.error('PDF 미리보기 조회 실패:', error);
                return { success: false, message: error.message };
            }
        }
        
        /**
         * PDF 인덱싱 (스트리밍)
         */
        async function indexPdf(pdfPath, progressCallback) {
            try {
                const response = await fetch(`/index-pdf-stream?pdf_path=${encodeURIComponent(pdfPath)}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) {
                        break;
                    }
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                
                                if (data.status === 'done') {
                                    return data.result;
                                } else if (data.status === 'error') {
                                    return { success: false, message: data.message };
                                } else if (data.status !== 'heartbeat' && progressCallback) {
                                    progressCallback(data);
                                }
                            } catch (parseError) {
                                console.warn('JSON 파싱 오류:', parseError);
                            }
                        }
                    }
                }
                
                return { success: false, message: '스트리밍이 예기치 않게 종료되었습니다.' };
            } catch (error) {
                console.error('PDF 인덱싱 실패:', error);
                return { success: false, message: error.message };
            }
        }
        
        /**
         * 채팅 질의
         */
        async function sendChatQuery(query, pdfPath = null, limit = 3) {
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        query: query, 
                        pdf_path: pdfPath,
                        limit: limit,
                        use_context: true
                    })
                });
                
                return await response.json();
            } catch (error) {
                console.error('채팅 질의 실패:', error);
                return { 
                    success: false, 
                    message: error.message 
                };
            }
        }
    """