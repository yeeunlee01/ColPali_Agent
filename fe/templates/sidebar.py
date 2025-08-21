"""사이드바 컴포넌트 템플릿"""

def get_sidebar_template():
    """사이드바 HTML 구조 반환"""
    return """
    <!-- 사이드바 헤더 -->
    <div class="sidebar-header py-4 px-4 border-b border-gray-200 flex-shrink-0 flex items-center h-[72px]">
        <h2 class="text-lg font-semibold text-gray-800">PDF 문서 관리</h2>
    </div>

    <!-- PDF 관리 섹션 -->
    <div class="sidebar-content flex flex-col flex-1 min-h-0">
        <div class="p-4 border-b border-gray-200 flex-shrink-0">
            <button id="loadPdfBtn" class="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm">
                <i class="fas fa-sync-alt mr-2"></i>PDF 목록 새로고침
            </button>
        </div>
        
        <!-- PDF 목록 -->
        <div id="pdfList" class="space-y-2 flex-1 overflow-y-auto p-4 min-h-0">
            <!-- PDF 아이템들이 동적으로 추가됩니다 -->
        </div>
    </div>

    <!-- 진행 상황 섹션 -->
    <div id="progressSection" class="hidden p-4 border-t border-gray-200 flex-shrink-0">
        <div class="mb-2">
            <div class="flex justify-between items-center mb-1">
                <span class="text-sm font-medium text-gray-700">진행 상황</span>
                <span id="progressPercentage" class="text-sm text-gray-600">0%</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
                <div id="progressBar" class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
            </div>
        </div>
        <div id="progressMessage" class="text-xs text-gray-600">준비 중...</div>
        <div id="progressPages" class="text-xs text-gray-500 mt-1"></div>
    </div>

    <!-- 상태 메시지 -->
    <div id="uploadStatus" class="hidden mx-4 mb-4 p-2 rounded text-sm flex-shrink-0"></div>
    """

def get_pdf_item_template(pdf_name, pdf_path, pdf_size, is_indexed=False):
    """개별 PDF 아이템 템플릿"""
    status_class = "indexed" if is_indexed else ""
    button_text = "선택됨" if is_indexed else "선택"
    button_class = "bg-green-600 cursor-not-allowed" if is_indexed else "bg-blue-600 hover:bg-blue-700"
    button_disabled = "disabled" if is_indexed else ""
    
    return f"""
    <div class="reference-item {status_class} p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors" 
         data-pdf-path="{pdf_path}">
        <div class="flex items-center justify-between">
            <div class="flex-1">
                <div class="font-medium text-gray-800 text-sm">{pdf_name}</div>
                <div class="text-xs text-gray-500">{pdf_size} MB</div>
            </div>
            <button class="index-btn px-2 py-1 {button_class} text-white text-xs rounded" {button_disabled}>
                {button_text}
            </button>
        </div>
    </div>
    """