"""API 호출 관련 JavaScript 함수들"""

def get_api_functions():
    """모든 API 호출 함수들 반환"""
    return """
    <script>
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
         * PDF 인덱싱
         */
        async function indexPdf(pdfPath) {
            try {
                const response = await fetch('/index-pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        pdf_path: pdfPath
                    })
                });
                
                return await response.json();
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
    </script>
    """