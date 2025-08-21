"""UI 조작 관련 JavaScript 함수들"""

def get_ui_functions():
    """모든 UI 조작 함수들 반환"""
    return """
    <script>
        /**
         * 로딩 오버레이 표시/숨김
         */
        function showLoading(show) {
            const loading = document.getElementById('loading');
            loading.classList.toggle('hidden', !show);
        }
        
        /**
         * 메시지 추가
         */
        function addMessage(type, content, references = null) {
            const chatMessages = document.getElementById('chatMessages');
            
            // 환영 메시지 제거
            const welcomeMessage = chatMessages.querySelector('.text-center.py-12');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            
            if (type === 'user') {
                messageDiv.innerHTML = `
                    <div class="user-message text-white p-4 rounded-lg max-w-3xl ml-auto">
                        <div class="text-white">${content}</div>
                    </div>
                `;
            } else if (type === 'assistant') {
                messageDiv.innerHTML = `
                    <div class="assistant-message p-4 rounded-lg max-w-3xl">
                        <div class="text-gray-800">${content}</div>
                    </div>
                `;
            } else if (type === 'system') {
                messageDiv.innerHTML = `
                    <div class="bg-yellow-100 border-l-4 border-yellow-400 p-4 rounded-lg max-w-3xl">
                        <div class="text-gray-800">${content}</div>
                    </div>
                `;
            }
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        /**
         * PDF 목록 표시 (미리보기 이미지 포함)
         */
        async function displayPdfList(pdfFiles) {
            const pdfList = document.getElementById('pdfList');
            pdfList.innerHTML = '';
            
            if (!pdfFiles || pdfFiles.length === 0) {
                pdfList.innerHTML = '<div class="text-center text-gray-500 py-4">PDF 파일이 없습니다.</div>';
                return;
            }
            
            for (const pdf of pdfFiles) {
                const pdfPath = pdf.path;
                const pdfName = pdf.name;
                const pdfSize = pdf.size_mb;
                const isIndexed = indexedPdfs.has(pdfPath);
                
                // PDF 미리보기 조회
                const previewResult = await fetchPdfPreview(pdfPath);
                
                // 미리보기 이미지 HTML
                let previewImageHtml = '';
                if (previewResult.success && previewResult.image_name) {
                    previewImageHtml = `
                        <img src="/images/${previewResult.image_name}" 
                             alt="${pdfName} 미리보기" 
                             class="w-full h-40 object-cover object-top bg-white rounded mb-2 border"
                             style="image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div style="display: none;" class="w-full h-40 bg-gray-100 rounded mb-2 flex items-center justify-center">
                            <i class="fas fa-file-pdf text-gray-400 text-2xl"></i>
                        </div>
                    `;
                } else {
                    previewImageHtml = `
                        <div class="w-full h-40 bg-gray-100 rounded mb-2 flex items-center justify-center">
                            <i class="fas fa-file-pdf text-gray-400 text-2xl"></i>
                        </div>
                    `;
                }
                
                const pdfItem = document.createElement('div');
                pdfItem.className = `reference-item p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${isIndexed ? 'indexed' : ''}`;
                pdfItem.setAttribute('data-pdf-path', pdfPath);
                
                const statusClass = isIndexed ? 'bg-green-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700';
                const buttonText = isIndexed ? '선택됨' : '선택';
                const buttonDisabled = isIndexed ? 'disabled' : '';
                
                pdfItem.innerHTML = `
                    ${previewImageHtml}
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="font-medium text-gray-800 text-sm">${pdfName}</div>
                            <div class="text-xs text-gray-500">${pdfSize} MB</div>
                        </div>
                        <button class="index-btn px-2 py-1 ${statusClass} text-white text-xs rounded" ${buttonDisabled}>
                            ${buttonText}
                        </button>
                    </div>
                `;
                
                pdfList.appendChild(pdfItem);
            }
        }
        
        /**
         * PDF 선택
         */
        function selectPdf(element) {
            document.querySelectorAll('.reference-item').forEach(item => {
                item.classList.remove('active');
            });
            
            element.classList.add('active');
            selectedPdfPath = element.getAttribute('data-pdf-path');
        }
    </script>
    """