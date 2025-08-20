"""채팅 영역 컴포넌트 템플릿"""

def get_chat_template():
    """채팅 영역 HTML 구조 반환"""
    return """
    <div class="h-full flex flex-col">
        <!-- 채팅 메시지 영역 -->
        <div id="chatMessages" class="flex-1 overflow-y-auto p-4 space-y-4">
            <!-- 환영 메시지 -->
            <div class="text-center py-12">
                <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                    <i class="fas fa-comments text-blue-600 text-xl"></i>
                </div>
                <h3 class="text-lg font-semibold text-gray-800 mb-2">ColPali Agent에 오신 것을 환영합니다!</h3>
                <p class="text-gray-600 mb-4">PDF 문서와 대화를 시작해보세요.</p>
                <p class="text-sm text-gray-500">먼저 사이드바에서 PDF를 선택하고 인덱싱해주세요.</p>
            </div>
        </div>

        <!-- 타이핑 인디케이터 -->
        <div id="typingIndicator" class="hidden px-4 pb-2">
            <div class="flex items-center space-x-2 text-gray-500">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
                <span class="text-sm">Assistant가 답변을 작성하고 있습니다...</span>
            </div>
        </div>

        <!-- 메시지 입력 영역 -->
        <div class="p-4 bg-white border-t border-gray-200">
            <div class="flex items-end space-x-3">
                <div class="flex-1 relative">
                    <textarea 
                        id="messageInput" 
                        placeholder="PDF 내용에 대해 질문해보세요..." 
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[50px] max-h-32"
                        rows="1"
                    ></textarea>
                </div>
                <button 
                    id="sendBtn" 
                    class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
            <div class="text-xs text-gray-500 mt-2">
                Enter: 전송 | Shift + Enter: 줄바꿈
            </div>
        </div>
    </div>
    """