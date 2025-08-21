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
            
            // 사이드바 토글
            const sidebarToggle = document.getElementById('sidebarToggle');
            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', handleSidebarToggle);
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
                // 선택된 PDF가 인덱싱되었는지 확인
                if (!indexedPdfs.has(selectedPdfPath)) {
                    addMessage('system', 'PDF를 인덱싱하고 있습니다. 잠시만 기다려주세요...');
                    
                    // PDF 인덱싱 실행
                    const indexResult = await indexPdf(selectedPdfPath);
                    
                    if (indexResult.success) {
                        indexedPdfs.add(selectedPdfPath);
                        addMessage('system', `인덱싱이 완료되었습니다. (${indexResult.indexed_pages}페이지)`);
                        
                        // 버튼 상태 업데이트
                        const pdfItem = document.querySelector(`[data-pdf-path="${selectedPdfPath}"]`);
                        if (pdfItem) {
                            const button = pdfItem.querySelector('.index-btn');
                            if (button) {
                                button.textContent = '선택됨';
                                button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                                button.classList.add('bg-green-600', 'cursor-not-allowed');
                                button.disabled = true;
                            }
                            pdfItem.classList.add('indexed');
                        }
                    } else {
                        addMessage('system', `인덱싱 실패: ${indexResult.message}`);
                        isProcessing = false;
                        return;
                    }
                }
                
                // 채팅 질의 실행
                const result = await sendChatQuery(message, selectedPdfPath);
                
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
         * 사이드바 토글 핸들러
         */
        function handleSidebarToggle() {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.getElementById('mainContent');
            const toggleIcon = document.querySelector('#sidebarToggle i');
            
            if (sidebar && mainContent && toggleIcon) {
                sidebar.classList.toggle('collapsed');
                mainContent.classList.toggle('sidebar-collapsed');
                
                // 화살표 방향 변경
                if (sidebar.classList.contains('collapsed')) {
                    toggleIcon.classList.remove('fa-chevron-left');
                    toggleIcon.classList.add('fa-chevron-right');
                } else {
                    toggleIcon.classList.remove('fa-chevron-right');
                    toggleIcon.classList.add('fa-chevron-left');
                }
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