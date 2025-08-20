"""이벤트 핸들러 관련 JavaScript 함수들"""

def get_event_handlers():
    """모든 이벤트 핸들러들 반환"""
    return """
    <script>
        // DOM이 로드된 후 이벤트 리스너 설정
        document.addEventListener('DOMContentLoaded', function() {
            initializeEventListeners();
            loadInitialData();
        });
        
        /**
         * 이벤트 리스너 초기화
         */
        function initializeEventListeners() {
            // PDF 목록 새로고침
            const loadPdfBtn = document.getElementById('loadPdfBtn');
            if (loadPdfBtn) {
                loadPdfBtn.addEventListener('click', handleLoadPdfList);
            }
            
            // 메시지 전송
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn) {
                sendBtn.addEventListener('click', handleSendMessage);
            }
            
            // Enter 키 처리
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (!isProcessing) {
                            handleSendMessage();
                        }
                    }
                });
            }
            
            // PDF 목록 이벤트 위임
            const pdfList = document.getElementById('pdfList');
            if (pdfList) {
                pdfList.addEventListener('click', function(event) {
                    const pdfItem = event.target.closest('.reference-item');
                    if (pdfItem) {
                        selectPdf(pdfItem);
                    }
                });
            }
        }
        
        /**
         * PDF 목록 로드 핸들러
         */
        async function handleLoadPdfList() {
            showLoading(true);
            
            try {
                const result = await fetchPdfList();
                
                if (result.success) {
                    await displayPdfList(result.pdf_files);
                } else {
                    addMessage('system', `PDF 목록 로드 실패: ${result.message}`);
                }
            } catch (error) {
                addMessage('system', `PDF 목록 로드 중 오류: ${error.message}`);
            } finally {
                showLoading(false);
            }
        }
        
        /**
         * 메시지 전송 핸들러
         */
        async function handleSendMessage() {
            if (isProcessing) return;
            
            const messageInput = document.getElementById('messageInput');
            const message = messageInput.value.trim();
            
            if (!message) return;
            
            if (!selectedPdfPath) {
                addMessage('system', 'PDF를 먼저 선택해주세요.');
                return;
            }
            
            isProcessing = true;
            
            // 사용자 메시지 추가
            addMessage('user', message);
            messageInput.value = '';
            
            try {
                const result = await sendChatQuery(message);
                
                if (result.success && result.answer) {
                    addMessage('assistant', result.answer);
                } else {
                    addMessage('assistant', '답변을 생성할 수 없습니다.');
                }
            } catch (error) {
                addMessage('system', `오류가 발생했습니다: ${error.message}`);
            } finally {
                isProcessing = false;
            }
        }
        
        /**
         * 초기 데이터 로드
         */
        async function loadInitialData() {
            await handleLoadPdfList();
        }
    </script>
    """