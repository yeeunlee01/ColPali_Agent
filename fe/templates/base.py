"""기본 HTML 구조 템플릿"""

def get_base_template(title="ColPali Agent", body_content=""):
    """기본 HTML 구조 반환"""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    {{{{CSS_PLACEHOLDER}}}}
</head>
<body class="bg-gray-50">
    {body_content}
    {{{{JAVASCRIPT_PLACEHOLDER}}}}
</body>
</html>"""

def get_main_layout(sidebar_content="", chat_content=""):
    """메인 레이아웃 구조 반환"""
    return f"""
    <!-- 사이드바 -->
    <div id="sidebar" class="fixed left-0 top-0 h-full w-80 bg-white shadow-lg z-10 transition-transform duration-300 flex flex-col">
        {sidebar_content}
    </div>
    
    <!-- 메인 콘텐츠 -->
    <div id="mainContent" class="transition-all duration-300 h-screen flex flex-col ml-80">
        <!-- 헤더 -->
        <div class="bg-white shadow-sm p-4 flex items-center justify-between w-full">
            <div class="flex items-center space-x-3">
                <button id="sidebarToggle" class="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors">
                    <i class="fas fa-chevron-left text-gray-600 transition-transform duration-300"></i>
                </button>
                <h1 class="text-xl font-semibold text-gray-800">ColPali Agent</h1>
            </div>
        </div>
        
        <!-- 채팅 영역 -->
        <div class="flex-1 overflow-hidden w-full">
            {chat_content}
        </div>
    </div>
    
    <!-- 로딩 오버레이 -->
    <div id="loading" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl">
            <div class="flex items-center space-x-4">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p class="text-gray-700">처리 중...</p>
            </div>
        </div>
    </div>"""