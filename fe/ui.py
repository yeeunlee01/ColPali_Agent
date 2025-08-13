"""ColPali RAG Interface UI HTML Template"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ColPali RAG Interface</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
    <style>
        .pdf-card {
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .pdf-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }
        .pdf-card.selected {
            border: 2px solid #3b82f6;
            background-color: #eff6ff;
        }
        .preview-image {
            width: 100% !important;
            height: 200px !important;
            object-fit: cover !important;
            object-position: top !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 4px !important;
            margin: 0 auto !important;
            display: block !important;
        }
        .preview-container {
            width: 100%;
            height: 200px;
            overflow: hidden !important;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            position: relative;
        }
        .preview-container .preview-image {
            border: none !important;
            border-radius: 0 !important;
            transform: scaleY(1.67) !important;
            transform-origin: top !important;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4 py-8 max-w-6xl">
        <h1 class="text-3xl font-bold text-center mb-8 text-gray-800">ColPali RAG Interface</h1>
        
        <!-- PDF 선택 섹션 -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">PDF 문서 선택</h2>
            <button 
                id="loadPdfBtn" 
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors mb-4"
            >
                PDF 목록 불러오기
            </button>
            <div id="pdfGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4"></div>
            <div id="selectedPdf" class="mt-4 hidden">
                <div class="p-4 bg-blue-50 rounded-lg">
                    <p class="text-sm text-blue-800">선택된 PDF: <span id="selectedPdfName"></span></p>
                    <button 
                        id="indexPdfBtn" 
                        class="mt-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                        PDF 인덱싱하기
                    </button>
                </div>
            </div>
            
            <!-- 진행상황 표시 섹션 -->
            <div id="progressSection" class="mt-4 hidden">
                <div class="p-4 bg-gray-50 rounded-lg">
                    <div class="flex justify-between items-center mb-2">
                        <span id="progressMessage" class="text-sm text-gray-700">인덱싱 준비 중...</span>
                        <span id="progressPercentage" class="text-sm text-gray-600">0%</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-2">
                        <div id="progressBar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                    <div class="mt-2 text-xs text-gray-500">
                        <span id="progressPages">0 / 0 페이지</span>
                    </div>
                </div>
            </div>
            
            <div id="uploadStatus" class="mt-4 hidden"></div>
        </div>
        
        <!-- 검색 섹션 -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">검색</h2>
            <div class="flex gap-4">
                <input 
                    type="text" 
                    id="queryInput" 
                    placeholder="검색할 내용을 입력하세요..." 
                    class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                <button 
                    id="searchBtn" 
                    class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    검색
                </button>
            </div>
        </div>
        
        <!-- 결과 섹션 -->
        <div id="resultsSection" class="hidden">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-semibold mb-4">검색 결과</h2>
                <div id="searchResults"></div>
            </div>
        </div>
        
        <!-- 로딩 스피너 -->
        <div id="loading" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white p-6 rounded-lg">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p class="mt-4 text-center">처리 중...</p>
            </div>
        </div>
    </div>
    
    <script>
        // DOM 요소들
        const loadPdfBtn = document.getElementById('loadPdfBtn');
        const pdfGrid = document.getElementById('pdfGrid');
        const selectedPdf = document.getElementById('selectedPdf');
        const selectedPdfName = document.getElementById('selectedPdfName');
        const indexPdfBtn = document.getElementById('indexPdfBtn');
        const progressSection = document.getElementById('progressSection');
        const progressMessage = document.getElementById('progressMessage');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressBar = document.getElementById('progressBar');
        const progressPages = document.getElementById('progressPages');
        const uploadStatus = document.getElementById('uploadStatus');
        const queryInput = document.getElementById('queryInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsSection = document.getElementById('resultsSection');
        const searchResults = document.getElementById('searchResults');
        const loading = document.getElementById('loading');
        
        let selectedPdfPath = null;
        
        // PDF 목록 불러오기
        loadPdfBtn.addEventListener('click', loadPdfList);
        
        async function loadPdfList() {
            showLoading(true);
            
            try {
                const response = await fetch('/pdf-list');
                const result = await response.json();
                
                if (result.success) {
                    displayPdfGrid(result.pdf_files);
                } else {
                    showStatus(`PDF 목록 로드 실패: ${result.message}`, 'error');
                }
            } catch (error) {
                showStatus(`PDF 목록 로드 중 오류: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        // PDF 그리드 표시
        async function displayPdfGrid(pdfFiles) {
            if (pdfFiles.length === 0) {
                pdfGrid.innerHTML = '<p class="text-gray-600 col-span-full text-center">./data 폴더에 PDF 파일이 없습니다.</p>';
                return;
            }
            
            const pdfCards = await Promise.all(pdfFiles.map(async (pdf) => {
                try {
                    const previewResponse = await fetch(`/pdf-preview?pdf_path=${encodeURIComponent(pdf.path)}`);
                    const previewResult = await previewResponse.json();
                    
                    const previewImg = previewResult.success 
                        ? `<div class="preview-container mx-auto mb-2">
                             <img src="/images/${previewResult.image_name}" alt="미리보기" class="preview-image" onerror="this.style.display='none'; this.parentElement.nextElementSibling.style.display='flex';">
                           </div>
                           <div class="w-full h-32 bg-gray-200 flex items-center justify-center mb-2" style="display: none;"><span class="text-gray-500">이미지 로드 실패</span></div>`
                        : '<div class="w-full h-32 bg-gray-200 flex items-center justify-center mb-2"><span class="text-gray-500">미리보기 없음</span></div>';
                    
                    return `
                        <div class="pdf-card bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg" 
                             data-pdf-path="${pdf.path}" data-pdf-name="${pdf.name}">
                            ${previewImg}
                            <h3 class="font-semibold text-sm mb-1 truncate" title="${pdf.name}">${pdf.name}</h3>
                            <p class="text-xs text-gray-500">${pdf.size_mb} MB</p>
                        </div>
                    `;
                } catch (error) {
                    return `
                        <div class="pdf-card bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg" 
                             data-pdf-path="${pdf.path}" data-pdf-name="${pdf.name}">
                            <div class="w-full h-32 bg-gray-200 flex items-center justify-center mb-2">
                                <span class="text-gray-500">미리보기 오류</span>
                            </div>
                            <h3 class="font-semibold text-sm mb-1 truncate" title="${pdf.name}">${pdf.name}</h3>
                            <p class="text-xs text-gray-500">${pdf.size_mb} MB</p>
                        </div>
                    `;
                }
            }));
            
            pdfGrid.innerHTML = pdfCards.join('');
            
            // PDF 카드 클릭 이벤트 추가
            document.querySelectorAll('.pdf-card').forEach(card => {
                card.addEventListener('click', () => selectPdf(card));
            });
        }
        
        // PDF 선택 처리
        function selectPdf(cardElement) {
            // 이전 선택 해제
            document.querySelectorAll('.pdf-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // 새로운 선택 표시
            cardElement.classList.add('selected');
            
            selectedPdfPath = cardElement.getAttribute('data-pdf-path');
            const pdfName = cardElement.getAttribute('data-pdf-name');
            
            selectedPdfName.textContent = pdfName;
            selectedPdf.classList.remove('hidden');
        }
        
        // PDF 인덱싱 처리 (실시간 진행상황 포함)
        indexPdfBtn.addEventListener('click', async () => {
            if (!selectedPdfPath) {
                showStatus('PDF를 선택해주세요.', 'error');
                return;
            }
            
            // 진행상황 섹션 표시
            progressSection.classList.remove('hidden');
            indexPdfBtn.disabled = true;
            indexPdfBtn.textContent = '인덱싱 중...';
            
            // 초기 상태 설정
            updateProgress({
                message: '인덱싱 준비 중...',
                percentage: 0,
                current_page: 0,
                total_pages: 0
            });
            
            try {
                // EventSource로 실시간 진행상황 수신
                const eventSource = new EventSource(`/index-pdf-stream?pdf_path=${encodeURIComponent(selectedPdfPath)}`);
                
                eventSource.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.status === 'heartbeat') {
                            // heartbeat는 무시
                            return;
                        }
                        
                        if (data.status === 'done') {
                            // 완료 처리
                            const result = data.result;
                            if (result.success) {
                                updateProgress({
                                    message: `인덱싱 완료: ${result.indexed_pages}페이지 처리됨`,
                                    percentage: 100,
                                    current_page: result.total_pages,
                                    total_pages: result.total_pages
                                });
                                showStatus(`인덱싱 완료: ${result.indexed_pages}페이지 처리됨`, 'success');
                            } else {
                                updateProgress({
                                    message: `인덱싱 실패: ${result.message}`,
                                    percentage: 0,
                                    current_page: 0,
                                    total_pages: 0
                                });
                                showStatus(`인덱싱 실패: ${result.message}`, 'error');
                            }
                            eventSource.close();
                            resetIndexingUI();
                            
                        } else if (data.status === 'error') {
                            // 오류 처리
                            updateProgress({
                                message: `오류: ${data.message}`,
                                percentage: 0,
                                current_page: 0,
                                total_pages: 0
                            });
                            showStatus(`인덱싱 오류: ${data.message}`, 'error');
                            eventSource.close();
                            resetIndexingUI();
                            
                        } else {
                            // 진행상황 업데이트
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
                    resetIndexingUI();
                };
                
            } catch (error) {
                showStatus(`인덱싱 중 오류: ${error.message}`, 'error');
                resetIndexingUI();
            }
        });
        
        // 진행상황 업데이트 함수
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
        
        // 인덱싱 UI 리셋 함수
        function resetIndexingUI() {
            indexPdfBtn.disabled = false;
            indexPdfBtn.textContent = 'PDF 인덱싱하기';
            
            // 3초 후 진행상황 섹션 숨기기
            setTimeout(() => {
                progressSection.classList.add('hidden');
            }, 3000);
        }
        
        // 검색 처리
        searchBtn.addEventListener('click', handleSearch);
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSearch();
            }
        });
        
        async function handleSearch() {
            const query = queryInput.value.trim();
            if (!query) {
                alert('검색어를 입력하세요.');
                return;
            }
            
            showLoading(true);
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query, limit: 5 })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result);
                } else {
                    showStatus(`검색 실패: ${result.message}`, 'error');
                }
            } catch (error) {
                showStatus(`검색 중 오류 발생: ${error.message}`, 'error');
            } finally {
                showLoading(false);
            }
        }
        
        // 결과 표시
        function displayResults(result) {
            resultsSection.classList.remove('hidden');
            
            if (result.results.length === 0) {
                searchResults.innerHTML = '<p class="text-gray-600">검색 결과가 없습니다.</p>';
                return;
            }
            
            const resultsHTML = result.results.map((item, index) => `
                <div class="border rounded-lg p-4 mb-4">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="font-semibold">페이지 ${item.page_number}</h3>
                        <span class="text-sm text-gray-500">점수: ${item.score.toFixed(4)}</span>
                    </div>
                    <p class="text-sm text-gray-600 mb-2">문서: ${item.pdf_name}</p>
                    ${item.image_path ? `<img src="/images/${item.image_path}" alt="페이지 ${item.page_number}" class="max-w-full h-auto border rounded">` : ''}
                </div>
            `).join('');
            
            searchResults.innerHTML = `
                <p class="mb-4 text-sm text-gray-600">
                    검색어: "${result.query}" | 
                    검색 시간: ${result.search_time.toFixed(3)}초 | 
                    총 ${result.total_results}개 결과
                </p>
                ${resultsHTML}
            `;
        }
        
        // 유틸리티 함수들
        function showStatus(message, type) {
            uploadStatus.className = `mt-4 p-3 rounded-lg ${
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
    </script>
</body>
</html>
"""