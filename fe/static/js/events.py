"""이벤트 핸들러 관련 JavaScript 함수들"""

def get_event_handlers():
    """모든 이벤트 핸들러들 반환"""
    return """
        // DOM이 로드된 후 이벤트 리스너 설정
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOMContentLoaded 이벤트 실행됨');
            initializeEventListeners();
            // 약간의 지연 후 초기 데이터 로드
            setTimeout(() => {
                console.log('초기 데이터 로드 시작');
                loadInitialData().catch(error => {
                    console.error('초기 데이터 로드 실패:', error);
                });
            }, 100);
        });
        
        // window load 이벤트도 추가 (DOMContentLoaded가 실행되지 않을 경우 백업)
        window.addEventListener('load', function() {
            console.log('Window load 이벤트 실행됨');
            // DOMContentLoaded에서 이미 실행되었는지 확인
            if (!document.querySelector('#pdfList').hasChildNodes()) {
                console.log('PDF 목록이 비어있어서 다시 로드 시도');
                loadInitialData().catch(error => {
                    console.error('Window load에서 초기 데이터 로드 실패:', error);
                });
            }
        });
        
        /**
         * 이벤트 리스너 초기화
         */
        function initializeEventListeners() {
            console.log('이벤트 리스너 초기화 시작');
            
            // PDF 목록 새로고침
            const loadPdfBtn = document.getElementById('loadPdfBtn');
            console.log('loadPdfBtn 요소:', loadPdfBtn);
            if (loadPdfBtn) {
                loadPdfBtn.addEventListener('click', handleLoadPdfList);
                console.log('loadPdfBtn 이벤트 리스너 등록 완료');
            } else {
                console.error('loadPdfBtn 요소를 찾을 수 없습니다!');
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
            console.log('handleLoadPdfList 함수 호출됨');
            showLoading(true);
            
            try {
                console.log('fetchPdfList 호출 시작');
                const result = await fetchPdfList();
                console.log('fetchPdfList 결과:', result);
                
                if (result.success) {
                    console.log('PDF 목록 표시 시작');
                    await displayPdfList(result.pdf_files);
                    console.log('PDF 목록 표시 완료');
                } else {
                    console.error('PDF 목록 로드 실패:', result.message);
                    addMessage('system', `PDF 목록 로드 실패: ${result.message}`);
                }
            } catch (error) {
                console.error('PDF 목록 로드 중 오류:', error);
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
                    // 채팅창에 progress bar 메시지 추가
                    const progressMessageDiv = addProgressMessage();
                    
                    // 채팅 progress bar 요소들 참조
                    const chatProgressBar = document.getElementById('chatProgressBar');
                    const chatProgressPercentage = document.getElementById('chatProgressPercentage');
                    const chatProgressMessage = document.getElementById('chatProgressMessage');
                    const chatProgressPages = document.getElementById('chatProgressPages');
                    
                    // 진행 상황 콜백 함수 (채팅 progress bar 업데이트)
                    const progressCallback = (data) => {
                        if (data.current_page && data.total_pages) {
                            const percentage = Math.round((data.current_page / data.total_pages) * 100);
                            if (chatProgressBar) chatProgressBar.style.width = `${percentage}%`;
                            if (chatProgressPercentage) chatProgressPercentage.textContent = `${percentage}%`;
                            if (chatProgressPages) chatProgressPages.textContent = `${data.current_page} / ${data.total_pages} 페이지`;
                            if (chatProgressMessage) chatProgressMessage.textContent = `페이지 임베딩 생성 중...`;
                        } else if (data.status === 'processing') {
                            if (chatProgressMessage) chatProgressMessage.textContent = data.message || '인덱싱 진행 중...';
                        }
                    };
                    
                    // PDF 인덱싱 실행 (스트리밍)
                    const indexResult = await indexPdf(selectedPdfPath, progressCallback);
                    
                    if (indexResult.success) {
                        indexedPdfs.add(selectedPdfPath);
                        
                        // 채팅 progress bar 제거
                        removeProgressMessage();
                        
                        // 완료 메시지만 채팅에 표시
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
                        // 채팅 progress bar 제거
                        removeProgressMessage();
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
    """