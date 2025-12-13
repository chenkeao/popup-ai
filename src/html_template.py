"""HTML template for conversation display."""

from src.constants import MATHJAX_CDN_URL


def get_mathjax_config() -> str:
    """Get MathJax configuration JavaScript."""
    return r"""
    window.MathJax = {
        tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']],
            processEscapes: true,
            processEnvironments: true,
            tags: 'ams'
        },
        options: {
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
            ignoreHtmlClass: 'no-mathjax',
            renderActions: {
                addMenu: []  // Disable MathJax context menu for better performance
            }
        },
        startup: {
            ready: () => {
                MathJax.startup.defaultReady();
            },
            pageReady: () => {
                return MathJax.startup.defaultPageReady();
            }
        }
    };
    """


def get_css_variables(is_dark: bool) -> dict:
    """Get CSS variables based on theme."""
    if is_dark:
        return {
            "bg_color": "#1e1e1e",
            "text_color": "#e0e0e0",
            "user_bg": "#2563eb",
            "user_header_bg": "#1e40af",
            "assistant_bg": "#262626",
            "assistant_header_bg": "#333333",
            "code_bg": "#1a1a1a",
            "pre_bg": "#1a1a1a",
            "pre_text": "#d4d4d4",
            "border_color": "#404040",
            "table_header_bg": "#1a1a1a",
            "shadow": "0 2px 8px rgba(0, 0, 0, 0.8)",
            "quote_border": "rgba(255, 255, 255, 0.4)",
            "quote_text": "rgba(255, 255, 255, 0.85)",
            "link_color": "#60a5fa",
            "link_hover_color": "#93c5fd",
        }
    else:
        return {
            "bg_color": "#ffffff",
            "text_color": "#2e3436",
            "user_bg": "#3584e4",
            "user_header_bg": "#1c71d8",
            "assistant_bg": "#ffffff",
            "assistant_header_bg": "rgba(0, 0, 0, 0.05)",
            "code_bg": "rgba(0, 0, 0, 0.05)",
            "pre_bg": "#f6f8fa",
            "pre_text": "#2e3436",
            "border_color": "#ddd",
            "table_header_bg": "#f6f8fa",
            "shadow": "0 1px 3px rgba(0, 0, 0, 0.1)",
            "quote_border": "rgba(0, 0, 0, 0.2)",
            "quote_text": "rgba(0, 0, 0, 0.7)",
            "link_color": "#1a73e8",
            "link_hover_color": "#1557b0",
        }


def get_conversation_styles(font_family: str, font_size: int, css_vars: dict) -> str:
    """Get conversation styles CSS."""
    return f"""
        :root {{
            --bg-color: {css_vars['bg_color']};
            --text-color: {css_vars['text_color']};
            --user-bg: {css_vars['user_bg']};
            --user-header-bg: {css_vars['user_header_bg']};
            --assistant-bg: {css_vars['assistant_bg']};
            --assistant-header-bg: {css_vars['assistant_header_bg']};
            --code-bg: {css_vars['code_bg']};
            --pre-bg: {css_vars['pre_bg']};
            --pre-text: {css_vars['pre_text']};
            --border-color: {css_vars['border_color']};
            --table-header-bg: {css_vars['table_header_bg']};
            --shadow: {css_vars['shadow']};
            --quote-border: {css_vars['quote_border']};
            --quote-text: {css_vars['quote_text']};
            --link-color: {css_vars['link_color']};
            --link-hover-color: {css_vars['link_hover_color']};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        ::selection {{
            background-color: rgba(100, 150, 255, 0.3);
        }}
        
        body {{
            font-family: {font_family}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: {font_size}px;
            padding: 16px;
            background: transparent;
            color: var(--text-color);
        }}
        .message {{
            margin-bottom: 16px;
            max-width: 85%;
        }}
        .message.user {{
            margin-left: auto;
        }}
        .message.assistant {{
            margin-right: auto;
        }}
        .message-header {{
            font-weight: 600;
            font-size: 0.85em;
            padding: 8px 12px;
            background: var(--assistant-header-bg);
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .token-info {{
            font-weight: 400;
            font-size: 0.9em;
            opacity: 0.7;
            margin-left: 8px;
        }}
        .copy-btn {{
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
            opacity: 0.6;
            transition: opacity 0.2s;
            display: flex;
            align-items: center;
        }}
        .copy-btn:hover {{
            opacity: 1;
        }}
        .copy-btn svg {{
            width: 16px;
            height: 16px;
        }}
        .message.user .copy-btn {{
            color: white;
        }}
        .message-content {{
            padding: 12px;
            background: var(--assistant-bg);
            border-radius: 0 0 8px 8px;
            box-shadow: var(--shadow);
            line-height: 1.6;
            word-wrap: break-word;
            overflow-wrap: break-word;
            overflow: hidden;
        }}
        .message.user .message-content {{
            background: var(--user-bg);
            color: #ffffff;
        }}
        .message.user .message-content ::selection {{
            background-color: rgba(255, 255, 255, 0.3);
        }}
        .message.user .message-header {{
            background: var(--user-header-bg);
            color: #ffffff;
        }}
        .message-content p {{
            margin-bottom: 0.5em;
        }}
        .message-content p:last-child {{
            margin-bottom: 0;
        }}
        .message-content ul,
        .message-content ol {{
            margin: 8px 0;
            padding-left: 24px;
            overflow: hidden;
        }}
        .message-content li {{
            margin-bottom: 4px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .message-content code {{
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Fira Code", "Courier New", monospace;
            font-size: 0.9em;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        .message.user .message-content code {{
            background: rgba(255, 255, 255, 0.2);
        }}
        .message-content pre {{
            background: var(--pre-bg);
            color: var(--pre-text);
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 8px 0;
            max-width: 100%;
        }}
        .message-content pre code {{
            background: none;
            color: inherit;
            padding: 0;
            white-space: pre;
        }}
        .message-content .MathJax,
        .message-content mjx-container {{
            max-width: 100%;
            overflow-x: auto;
            overflow-y: hidden;
            display: block;
            margin: 8px 0;
        }}
        .message-content mjx-container[display="true"] {{
            overflow-x: auto;
            overflow-y: hidden;
        }}
        .message-content mjx-container:not([display="true"]) {{
            display: inline-block;
            max-width: 100%;
            overflow-x: auto;
            vertical-align: middle;
        }}
        .message-content table {{
            border-collapse: collapse;
            width: 100%;
            margin: 8px 0;
            display: block;
            overflow-x: auto;
            max-width: 100%;
        }}
        .message-content th, .message-content td {{
            border: 1px solid var(--border-color);
            padding: 8px;
            text-align: left;
        }}
        .message-content th {{
            background: var(--table-header-bg);
            font-weight: 600;
        }}
        .message-content blockquote {{
            border-left: 4px solid var(--quote-border);
            padding-left: 12px;
            margin: 8px 0;
            color: var(--quote-text);
        }}
        .message.user .message-content blockquote {{
            border-left-color: rgba(255, 255, 255, 0.5);
            color: rgba(255, 255, 255, 0.9);
        }}
        .message-content a {{
            color: var(--link-color);
            text-decoration: none;
        }}
        .message-content a:hover {{
            color: var(--link-hover-color);
            text-decoration: underline;
        }}
        .message.user .message-content a {{
            color: #a8d5ff;
        }}
    """


def get_conversation_scripts(user_scrolled: bool) -> str:
    """Get conversation JavaScript code."""
    return f"""
        // Copy message source code
        function copyMessage(idx) {{
            var messages = document.querySelectorAll('.message-content');
            if (idx < messages.length) {{
                var rawContent = messages[idx].getAttribute('data-raw');
                if (rawContent) {{
                    // Decode HTML entities
                    var textarea = document.createElement('textarea');
                    textarea.innerHTML = rawContent;
                    var decodedContent = textarea.value;
                    
                    // Copy to clipboard
                    navigator.clipboard.writeText(decodedContent).then(function() {{
                        // Show feedback
                        var btn = event.target.closest('.copy-btn');
                        if (btn) {{
                            var originalHTML = btn.innerHTML;
                            btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M13.5 2.5l-8 8-3-3"/></svg>';
                            setTimeout(function() {{
                                btn.innerHTML = originalHTML;
                            }}, 1000);
                        }}
                    }}).catch(function(err) {{
                        console.error('Copy failed:', err);
                    }});
                }}
            }}
        }}
        
        // Debounced MathJax typesetting
        var mathJaxPending = false;
        function triggerMathJax() {{
            if (typeof MathJax !== 'undefined' && MathJax.typesetPromise && !mathJaxPending) {{
                mathJaxPending = true;
                MathJax.typesetPromise().catch(function(err) {{
                    console.error('MathJax error:', err);
                }}).finally(function() {{
                    mathJaxPending = false;
                }});
            }}
        }}
        
        // Trigger MathJax after DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', triggerMathJax);
        }} else {{
            triggerMathJax();
        }}
        
        // Save scroll position
        var scrollPos = sessionStorage.getItem('scrollPos');
        var userScrolledFlag = {str(user_scrolled).lower()};
        
        // Notify Python when user manually scrolls (throttled)
        var scrollTimeout;
        window.addEventListener('scroll', function() {{
            sessionStorage.setItem('scrollPos', window.scrollY);
            
            if (scrollTimeout) clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(function() {{
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.scrolled) {{
                    window.webkit.messageHandlers.scrolled.postMessage('scroll');
                }}
            }}, 150);
        }}, {{ passive: true }});
        
        // Restore position or auto-scroll
        if (userScrolledFlag && scrollPos !== null) {{
            window.scrollTo(0, parseInt(scrollPos));
        }} else {{
            var anchor = document.getElementById('scroll-anchor');
            if (anchor) {{
                anchor.scrollIntoView({{block: 'end'}});
            }}
            sessionStorage.setItem('scrollPos', window.scrollY);
        }}
    """


def generate_html_template(
    messages_html: str, font_family: str, font_size: int, is_dark: bool, user_scrolled: bool
) -> str:
    """Generate complete HTML template for conversation display.

    Args:
        messages_html: HTML string containing all messages
        font_family: Font family to use
        font_size: Font size in pixels
        is_dark: Whether dark mode is active
        user_scrolled: Whether user has manually scrolled

    Returns:
        Complete HTML document as string
    """
    css_vars = get_css_variables(is_dark)
    styles = get_conversation_styles(font_family, font_size, css_vars)
    scripts = get_conversation_scripts(user_scrolled)
    mathjax_config = get_mathjax_config()

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- MathJax configuration -->
    <script>
    {mathjax_config}
    </script>
    <!-- Load MathJax asynchronously for better performance -->
    <script async src="{MATHJAX_CDN_URL}"></script>
    <style>
        {styles}
    </style>
</head>
<body>
    {messages_html}
    <div id="scroll-anchor"></div>
    <script>
        {scripts}
    </script>
</body>
</html>
"""
