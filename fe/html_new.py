"""
메인 HTML 템플릿 조합 파일
모든 컴포넌트를 조합하여 최종 HTML을 생성합니다.
"""

from fe.templates.base import get_base_template, get_main_layout
from fe.templates.sidebar import get_sidebar_template
from fe.templates.chat import get_chat_template
from fe.static.css.styles import get_styles
from fe.static.js.api import get_api_functions
from fe.static.js.ui import get_ui_functions
from fe.static.js.events import get_event_handlers

class HtmlTemplate:
    """HTML 템플릿 관리 클래스"""
    
    @staticmethod
    def get_complete_html():
        """완전한 HTML 문서 반환"""
        # 컴포넌트들 조합
        sidebar_content = get_sidebar_template()
        chat_content = get_chat_template()
        main_layout = get_main_layout(sidebar_content, chat_content)
        
        # JavaScript 조합
        javascript = '\n'.join([
            get_api_functions(),
            get_ui_functions(), 
            get_event_handlers()
        ])
        
        # 기본 템플릿에 모든 내용 조합
        html = get_base_template("ColPali Agent", main_layout)
        
        # 플레이스홀더 치환
        html = html.replace('{{CSS_PLACEHOLDER}}', get_styles())
        html = html.replace('{{JAVASCRIPT_PLACEHOLDER}}', javascript)
        
        return html

# 기존 호환성을 위한 함수
def get_html():
    """기존 코드와의 호환성을 위한 함수"""
    return HtmlTemplate.get_complete_html()

# 메인 HTML 문자열 (기존 방식)
html_content = HtmlTemplate.get_complete_html()

# be/api/frontend.py와의 호환성을 위한 상수
HTML_TEMPLATE = html_content