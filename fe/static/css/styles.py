"""CSS 스타일 정의"""

def get_styles():
    """모든 CSS 스타일 반환"""
    return """
    <style>
        /* 기본 스타일 */
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 0;
            height: 100vh;
            overflow: hidden;
        }
        
        /* 사이드바 스타일 */
        #sidebar.collapsed {
            width: 60px;
        }
        
        /* PDF 아이템 스타일 */
        .reference-item {
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .reference-item:hover {
            background-color: #f8fafc;
            border-color: #3b82f6;
        }
        
        .reference-item.active {
            background-color: #eff6ff;
            border-color: #3b82f6;
        }
        
        .reference-item.indexed {
            background-color: #f0fdf4;
            border-color: #16a34a;
        }
        
        /* 채팅 메시지 스타일 */
        .message {
            margin-bottom: 1rem;
        }
        
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin-left: auto;
            max-width: 80%;
        }
        
        .assistant-message {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            max-width: 90%;
        }
        
        /* 메시지 입력 영역 */
        #messageInput {
            resize: none;
        }
        
        /* 진행 상황 바 */
        #progressBar {
            transition: width 0.3s ease;
        }
        
        /* 스크롤바 스타일 */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
    </style>
    """