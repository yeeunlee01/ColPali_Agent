"""ColPali RAG Interface UI HTML Template"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ColPali RAG Chat Interface</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .sidebar {
            width: 320px;
            min-width: 320px;
            max-width: 320px;
            transition: all 0.3s ease;
        }
        .sidebar.collapsed {
            width: 60px;
            min-width: 60px;
            max-width: 60px;
        }
        .sidebar-toggle {
            transition: transform 0.3s ease;
        }
        .sidebar.collapsed .sidebar-toggle {
            transform: rotate(180deg);
        }
        .reference-item {
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid transparent;
        }
        .reference-item:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
        }
        .reference-item.active {
            border-color: #1d4ed8;
            background-color: #eff6ff;
        }
        .chat-container {
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            scroll-behavior: smooth;
        }
        .message {
            margin-bottom: 1rem;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .assistant-message {
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
        }
        .reference-preview {
            max-height: 200px;
            object-fit: cover;
            object-position: top;
        }
        .chat-input {
            border-top: 1px solid #e5e7eb;
            background: white;
        }
        .typing-indicator {
            display: none;
        }
        .typing-indicator.active {
            display: flex;
        }
        .dot {
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        .progress-section {
            background: #f0f9ff;
            border-left: 4px solid #0ea5e9;
        }
        .sidebar-content {
            transition: opacity 0.3s ease;
        }
        .sidebar.collapsed .sidebar-content {
            opacity: 0;
            pointer-events: none;
        }
    </style>
</head>
<body class="bg-gray-100">
    <div class="flex h-screen">
        <!-- 왼쪽 사이드바 -->
        <div id="sidebar" class="sidebar bg-white border-r border-gray-200 flex flex-col shadow-lg">
            <!-- 사이드바 헤더 -->
            <div class="p-4 border-b border-gray-200 flex items-center justify-between">
                <div class="sidebar-content">
                    <h2 class="text-lg font-semibold text-gray-800">참조 자료</h2>
                    <p class="text-sm text-gray-600">PDF 문서 관리</p>
                </div>
                <button id="sidebarToggle" class="sidebar-toggle p-2 rounded-lg hover:bg-gray-100">
                    <i class="fas fa-chevron-left text-gray-600"></i>
                </button>
            </div>

            <!-- PDF 관리 섹션 -->
            <div class="sidebar-content p-4 border-b border-gray-200">
                <button id="loadPdfBtn" class="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm mb-3">
                    <i class="fas fa-sync-alt mr-2"></i>PDF 목록 새로고침
                </button>
                
                <!-- 진행상황 표시 -->
                <div id="progressSection" class="progress-section p-3 rounded-lg mb-3 hidden">
                    <div class="flex items-center justify-between mb-2">
                        <span id="progressMessage" class="text-xs text-blue-800">처리 중...</span>
                        <span id="progressPercentage" class="text-xs text-blue-600">0%</span>
                    </div>
                    <div class="w-full bg-blue-200 rounded-full h-1.5">
                        <div id="progressBar" class="bg-blue-600 h-1.5 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                    <div class="mt-1 text-xs text-blue-600">
                        <span id="progressPages">0 / 0 페이지</span>
                    </div>
                </div>
                
                <div id="uploadStatus" class="hidden text-xs p-2 rounded"></div>
            </div>

            <!-- PDF 리스트 -->
            <div class="sidebar-content flex-1 overflow-y-auto">
                <div id="pdfList" class="p-4">
                    <div class="text-center text-gray-500 py-8">
                        <i class="fas fa-file-pdf text-4xl mb-3 text-gray-300"></i>
                        <p class="text-sm">PDF 목록을 불러와주세요</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 메인 채팅 영역 -->
        <div class="flex-1 flex flex-col">
            <!-- 채팅 헤더 -->
            <div class="bg-white border-b border-gray-200 px-6 py-4">
                <h1 class="text-xl font-semibold text-gray-800">ColPali RAG Assistant</h1>
                <p class="text-sm text-gray-600">PDF 문서 기반 질의응답 시스템</p>
            </div>

            <!-- 채팅 메시지 영역 -->
            <div id="chatMessages" class="chat-messages flex-1 p-6 overflow-y-auto">
                <!-- 환영 메시지 -->
                <div class="message assistant-message p-4 rounded-lg max-w-3xl">
                    <div class="flex items-start space-x-3">
                        <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                            <i class="fas fa-robot text-white text-sm"></i>
                        </div>
                        <div class="flex-1">
                            <div class="text-sm text-gray-600 mb-1">Assistant</div>
                            <div class="text-gray-800">
                                안녕하세요! ColPali RAG Assistant입니다.<br>
                                왼쪽 사이드바에서 PDF를 선택하고 인덱싱한 후, 문서에 대해 질문해보세요.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 타이핑 인디케이터 -->
            <div id="typingIndicator" class="typing-indicator px-6 pb-2">
                <div class="flex items-start space-x-3 max-w-3xl">
                    <div class="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center">
                        <i class="fas fa-robot text-white text-sm"></i>
                    </div>
                    <div class="bg-gray-100 px-4 py-3 rounded-lg">
                        <div class="flex space-x-1">
                            <div class="dot w-2 h-2 bg-gray-500 rounded-full"></div>
                            <div class="dot w-2 h-2 bg-gray-500 rounded-full"></div>
                            <div class="dot w-2 h-2 bg-gray-500 rounded-full"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 채팅 입력 영역 -->
            <div class="chat-input p-6">
                <div class="flex items-end space-x-4">
                    <div class="flex-1">
                        <textarea 
                            id="messageInput" 
                            placeholder="문서에 대해 질문해보세요..." 
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            rows="1"
                        ></textarea>
                    </div>
                    <button 
                        id="sendBtn" 
                        class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="text-xs text-gray-500 mt-2">
                    Shift + Enter로 줄바꿈, Enter로 전송
                </div>
            </div>
        </div>
    </div>

    <!-- 로딩 모달 -->
    <div id="loading" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p class="mt-4 text-center text-gray-700">처리 중...</p>
        </div>
    </div>

    <script>
        // DOM 요소들
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const loadPdfBtn = document.getElementById('loadPdfBtn');
        const pdfList = document.getElementById('pdfList');
        const progressSection = document.getElementById('progressSection');
        const progressMessage = document.getElementById('progressMessage');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressBar = document.getElementById('progressBar');
        const progressPages = document.getElementById('progressPages');
        const uploadStatus = document.getElementById('uploadStatus');
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const typingIndicator = document.getElementById('typingIndicator');
        const loading = document.getElementById('loading');

        let selectedPdfPath = null;
        let isIndexed = false;

        // 사이드바 토글
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });

        // 메시지 입력 자동 크기 조절
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Enter 키 처리
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });

        // 메시지 전송
        sendBtn.addEventListener('click', handleSendMessage);

        async function handleSendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            if (!isIndexed) {
                addMessage('system', 'PDF를 먼저 인덱싱해주세요.');
                return;
            }

            // 사용자 메시지 추가
            addMessage('user', message);
            messageInput.value = '';
            messageInput.style.height = 'auto';
            
            // 전송 버튼 비활성화
            sendBtn.disabled = true;
            showTyping(true);

            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: message, limit: 3 })
                });

                const result = await response.json();
                showTyping(false);

                if (result.success && result.results.length > 0) {
                    // 검색 결과와 함께 응답 생성
                    const references = result.results.map((item, index) => ({
                        page: item.page_number,
                        pdf: item.pdf_name,
                        score: item.score,
                        image: item.image_path
                    }));

                    const responseText = `다음 ${result.results.length}개의 관련 문서를 찾았습니다:`;
                    addMessage('assistant', responseText, references);
                } else {
                    addMessage('assistant', '관련된 문서를 찾을 수 없습니다. 다른 질문을 시도해보세요.');
                }
            } catch (error) {
                showTyping(false);
                addMessage('system', `검색 중 오류가 발생했습니다: ${error.message}`);
            } finally {
                sendBtn.disabled = false;
            }
        }

        function addMessage(type, content, references = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';

            let messageClass = '';
            let icon = '';
            let sender = '';

            switch (type) {
                case 'user':
                    messageClass = 'user-message text-white';
                    icon = 'fas fa-user';
                    sender = 'You';
                    break;
                case 'assistant':
                    messageClass = 'assistant-message';
                    icon = 'fas fa-robot';
                    sender = 'Assistant';
                    break;
                case 'system':
                    messageClass = 'bg-yellow-100 border-l-4 border-yellow-400';
                    icon = 'fas fa-info-circle';
                    sender = 'System';
                    break;
            }

            let referencesHtml = '';
            if (references && references.length > 0) {
                referencesHtml = `
                    <div class="mt-4 space-y-3">
                        <div class="text-sm font-medium text-gray-700">참조 문서:</div>
                        ${references.map(ref => `
                            <div class="bg-white border rounded-lg p-3">
                                <div class="flex items-start space-x-3">
                                    <div class="flex-shrink-0">
                                        ${ref.image ? 
                                            `<img src="/images/${ref.image}" alt="페이지 ${ref.page}" class="reference-preview w-16 h-20 rounded border object-cover">` :
                                            `<div class="w-16 h-20 bg-gray-200 rounded border flex items-center justify-center">
                                                <i class="fas fa-file-alt text-gray-400"></i>
                                             </div>`
                                        }
                                    </div>
                                    <div class="flex-1 min-w-0">
                                        <div class="text-sm font-medium text-gray-900">페이지 ${ref.page}</div>
                                        <div class="text-xs text-gray-600 truncate">${ref.pdf}</div>
                                        <div class="text-xs text-gray-500 mt-1">유사도: ${ref.score.toFixed(3)}</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            messageDiv.innerHTML = `
                <div class="${messageClass} p-4 rounded-lg max-w-3xl ${type === 'user' ? 'ml-auto' : ''}">
                    <div class="flex items-start space-x-3">
                        ${type !== 'user' ? `
                            <div class="w-8 h-8 ${type === 'assistant' ? 'bg-blue-600' : 'bg-yellow-500'} rounded-full flex items-center justify-center flex-shrink-0">
                                <i class="${icon} text-white text-sm"></i>
                            </div>
                        ` : ''}
                        <div class="flex-1 min-w-0">
                            ${type !== 'user' ? `<div class="text-sm ${type === 'user' ? 'text-blue-100' : 'text-gray-600'} mb-1">${sender}</div>` : ''}
                            <div class="${type === 'user' ? 'text-white' : 'text-gray-800'}">${content}</div>
                            ${referencesHtml}
                        </div>
                        ${type === 'user' ? `
                            <div class="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center flex-shrink-0">
                                <i class="${icon} text-white text-sm"></i>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;

            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTyping(show) {
            typingIndicator.classList.toggle('active', show);
            if (show) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        // PDF 목록 불러오기
        loadPdfBtn.addEventListener('click', loadPdfList);

        async function loadPdfList() {
            showLoading(true);
            
            try {
                const response = await fetch('/pdf-list');
                const result = await response.json();
                
                if (result.success) {
                    displayPdfList(result.pdf_files);
                } else {
                    showStatus(`PDF 목록 로드 실패: ${result.message}`, 'error');
                }
            } catch (error) {
                showStatus(`PDF 목록 로드 중 오류: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }

        async function displayPdfList(pdfFiles) {
            if (pdfFiles.length === 0) {
                pdfList.innerHTML = `
                    <div class="text-center text-gray-500 py-8">
                        <i class="fas fa-folder-open text-4xl mb-3 text-gray-300"></i>
                        <p class="text-sm">./data 폴더에 PDF 파일이 없습니다</p>
                    </div>
                `;
                return;
            }

            const pdfItems = await Promise.all(pdfFiles.map(async (pdf) => {
                try {
                    const previewResponse = await fetch(`/pdf-preview?pdf_path=${encodeURIComponent(pdf.path)}`);
                    const previewResult = await previewResponse.json();
                    
                    const previewImg = previewResult.success 
                        ? `<img src="/images/${previewResult.image_name}" alt="미리보기" class="w-full h-24 object-cover rounded" onerror="this.style.display='none'; this.parentElement.querySelector('.no-preview').style.display='flex';">`
                        : '';

                    return `
                        <div class="reference-item bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3" 
                             data-pdf-path="${pdf.path}" data-pdf-name="${pdf.name}">
                            <div class="relative">
                                ${previewImg}
                                <div class="no-preview w-full h-24 bg-gray-200 rounded flex items-center justify-center ${previewResult.success ? 'hidden' : ''}">
                                    <i class="fas fa-file-pdf text-gray-400 text-2xl"></i>
                                </div>
                            </div>
                            <div class="mt-2">
                                <div class="text-sm font-medium text-gray-800 truncate" title="${pdf.name}">${pdf.name}</div>
                                <div class="text-xs text-gray-500 mt-1">${pdf.size_mb} MB</div>
                                <button class="index-btn w-full mt-2 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors">
                                    인덱싱
                                </button>
                            </div>
                        </div>
                    `;
                } catch (error) {
                    return `
                        <div class="reference-item bg-gray-50 border border-gray-200 rounded-lg p-3 mb-3" 
                             data-pdf-path="${pdf.path}" data-pdf-name="${pdf.name}">
                            <div class="w-full h-24 bg-gray-200 rounded flex items-center justify-center">
                                <i class="fas fa-exclamation-triangle text-gray-400"></i>
                            </div>
                            <div class="mt-2">
                                <div class="text-sm font-medium text-gray-800 truncate" title="${pdf.name}">${pdf.name}</div>
                                <div class="text-xs text-gray-500 mt-1">${pdf.size_mb} MB</div>
                                <button class="index-btn w-full mt-2 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors">
                                    인덱싱
                                </button>
                            </div>
                        </div>
                    `;
                }
            }));

            pdfList.innerHTML = pdfItems.join('');

            // 이벤트 리스너 추가
            document.querySelectorAll('.reference-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('index-btn')) {
                        selectPdf(item);
                    }
                });
            });

            document.querySelectorAll('.index-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const item = e.target.closest('.reference-item');
                    indexPdf(item.getAttribute('data-pdf-path'), btn);
                });
            });
        }

        function selectPdf(element) {
            document.querySelectorAll('.reference-item').forEach(item => {
                item.classList.remove('active');
            });
            element.classList.add('active');
            selectedPdfPath = element.getAttribute('data-pdf-path');
        }

        async function indexPdf(pdfPath, button) {
            const originalText = button.textContent;
            button.textContent = '처리중...';
            button.disabled = true;
            
            progressSection.classList.remove('hidden');
            
            try {
                const eventSource = new EventSource(`/index-pdf-stream?pdf_path=${encodeURIComponent(pdfPath)}`);
                
                eventSource.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.status === 'heartbeat') {
                            return;
                        }
                        
                        if (data.status === 'done') {
                            const result = data.result;
                            if (result.success) {
                                updateProgress({
                                    message: `완료: ${result.indexed_pages}페이지`,
                                    percentage: 100,
                                    current_page: result.total_pages,
                                    total_pages: result.total_pages
                                });
                                showStatus(`인덱싱 완료: ${result.indexed_pages}페이지`, 'success');
                                button.textContent = '완료';
                                button.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                                button.classList.add('bg-green-600');
                                isIndexed = true;
                                addMessage('system', `${result.indexed_pages}페이지가 인덱싱되었습니다. 이제 질문을 해보세요!`);
                            } else {
                                showStatus(`인덱싱 실패: ${result.message}`, 'error');
                                button.textContent = originalText;
                            }
                            eventSource.close();
                            hideProgressAfterDelay();
                            
                        } else if (data.status === 'error') {
                            showStatus(`오류: ${data.message}`, 'error');
                            button.textContent = originalText;
                            eventSource.close();
                            hideProgressAfterDelay();
                            
                        } else {
                            updateProgress({
                                message: data.message || '처리 중...',
                                percentage: data.percentage || 0,
                                current_page: data.current_page || 0,
                                total_pages: data.total_pages || 0
                            });
                        }
                        
                    } catch (error) {
                        console.error('진행상황 파싱 오류:', error);
                    }
                };
                
                eventSource.onerror = function(event) {
                    console.error('EventSource 오류:', event);
                    showStatus('인덱싱 중 연결 오류가 발생했습니다.', 'error');
                    eventSource.close();
                    button.textContent = originalText;
                    hideProgressAfterDelay();
                };
                
            } catch (error) {
                showStatus(`인덱싱 중 오류: ${error.message}`, 'error');
                button.textContent = originalText;
                hideProgressAfterDelay();
            } finally {
                button.disabled = false;
            }
        }

        function updateProgress(data) {
            if (data.message) {
                progressMessage.textContent = data.message;
            }
            
            if (typeof data.percentage === 'number') {
                progressPercentage.textContent = `${data.percentage}%`;
                progressBar.style.width = `${data.percentage}%`;
            }
            
            if (data.total_pages > 0) {
                progressPages.textContent = `${data.current_page} / ${data.total_pages} 페이지`;
            }
        }

        function hideProgressAfterDelay() {
            setTimeout(() => {
                progressSection.classList.add('hidden');
            }, 3000);
        }

        function showStatus(message, type) {
            uploadStatus.className = `text-xs p-2 rounded ${
                type === 'success' ? 'bg-green-100 text-green-800' :
                type === 'error' ? 'bg-red-100 text-red-800' :
                'bg-blue-100 text-blue-800'
            }`;
            uploadStatus.textContent = message;
            uploadStatus.classList.remove('hidden');
        }

        function showLoading(show) {
            loading.classList.toggle('hidden', !show);
        }

        // 초기 PDF 목록 로드
        window.addEventListener('load', () => {
            loadPdfList();
        });
    </script>
</body>
</html>
"""