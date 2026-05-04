import markdown
import bleach

# 允许的HTML标签
ALLOWED_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr',
    'strong', 'em', 'b', 'i', 'u', 'del', 'ins',
    'ul', 'ol', 'li',
    'a', 'img',
    'code', 'pre',
    'blockquote',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'div', 'span'
]

# 允许的属性
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title'],
    'code': ['class'],
    'pre': ['class'],
    '*': ['class', 'id']
}

def markdown_to_html(md_text: str) -> str:
    """将Markdown转换为HTML"""
    if not md_text:
        return ""
    
    # 转换为HTML
    html = markdown.markdown(
        md_text,
        extensions=[
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code'
        ]
    )
    
    # 清理不安全的标签
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    return clean_html

def html_to_plain_text(html_text: str) -> str:
    """将HTML转换为纯文本（用于搜索）"""
    if not html_text:
        return ""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text()