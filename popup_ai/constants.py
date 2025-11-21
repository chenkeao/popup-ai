"""Application constants and default values."""

# Application Information
APP_ID = "io.github.chenkeao.PopupAI"
APP_NAME = "Popup AI"
APP_VERSION = "0.1.0"
DEVELOPER_NAME = "Kyle Chen"
WEBSITE = "https://github.com/chenkeao/popup-ai"
ISSUE_URL = "https://github.com/chenkeao/popup-ai/issues"

# Window Settings
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600
SIDEBAR_WIDTH = 250
INPUT_MAX_HEIGHT = 150

# UI Settings
DEFAULT_UI_FONT = "Sans 11"
DEFAULT_WEBVIEW_FONT_FAMILY = "Sans"
DEFAULT_WEBVIEW_FONT_SIZE = 14

# API Endpoints
DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"
DEFAULT_OPENAI_ENDPOINT = "https://api.openai.com"
DEFAULT_PERPLEXITY_ENDPOINT = "https://api.perplexity.ai"

# Network Settings
HTTP_TIMEOUT = 120.0
MAX_KEEPALIVE_CONNECTIONS = 5
MAX_CONNECTIONS = 10

# Conversation Settings
MAX_HISTORY = 50
MAX_CONTEXT_MESSAGES = 1  # Maximum number of messages to send as context
STREAMING_UPDATE_INTERVAL = 0.05  # 50ms for smoother streaming

# Thread Pool Settings
ASYNC_EXECUTOR_MAX_WORKERS = 3
ASYNC_EXECUTOR_THREAD_PREFIX = "async-exec"

# UI Layout Settings
MARGIN_SMALL = 6
MARGIN_MEDIUM = 12
MARGIN_LARGE = 24
SPACING_SMALL = 6
SPACING_MEDIUM = 12
SPACING_LARGE = 18

# CSS Classes
CSS_CLASS_SIDEBAR = "sidebar"
CSS_CLASS_NAVIGATION_SIDEBAR = "navigation-sidebar"
CSS_CLASS_CARD = "card"
CSS_CLASS_TITLE_4 = "title-4"
CSS_CLASS_HEADING = "heading"
CSS_CLASS_CAPTION = "caption"
CSS_CLASS_DIM_LABEL = "dim-label"
CSS_CLASS_SUGGESTED_ACTION = "suggested-action"
CSS_CLASS_DESTRUCTIVE_ACTION = "destructive-action"
CSS_CLASS_FLAT = "flat"

# Icon Names
ICON_TRASH = "user-trash-symbolic"
ICON_ADD = "list-add-symbolic"
ICON_MENU = "open-menu-symbolic"
ICON_CLEAR = "edit-clear-all-symbolic"
ICON_SIDEBAR_SHOW = "sidebar-show-symbolic"
ICON_SIDEBAR_HIDE = "sidebar-hide-symbolic"
ICON_EDIT = "document-edit-symbolic"
ICON_REFRESH = "view-refresh-symbolic"
ICON_NETWORK = "network-server-symbolic"
ICON_SCIENCE = "applications-science-symbolic"
ICON_SYSTEM = "preferences-system-symbolic"
ICON_GRAPHICS = "applications-graphics-symbolic"

# File Paths (relative to user home)
CONFIG_DIR_NAME = ".config/popup-ai"
DATA_DIR_NAME = ".local/share/popup-ai"
CONFIG_FILE_NAME = "config.json"
PROMPTS_FILE_NAME = "prompts.json"
MODELS_FILE_NAME = "models.json"
CONVERSATIONS_DIR_NAME = "conversations"

# Logging
LOG_LEVEL = "INFO"

# Auto-fetch Settings
AUTO_FETCH_MODELS_DEFAULT = True
AUTO_FETCH_DELAY_MS = 500  # Delay before auto-fetching models

# Message Roles
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"

# Model Types
MODEL_TYPE_OLLAMA = "ollama"
MODEL_TYPE_API = "api"

# MathJax CDN
MATHJAX_CDN_URL = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"

# Keyboard Shortcuts
SHORTCUT_QUIT = "<Ctrl>Q"
SHORTCUT_PREFERENCES = "<Ctrl>comma"
