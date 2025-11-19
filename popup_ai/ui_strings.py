"""UI text strings for internationalization support."""

# Window Titles
WINDOW_TITLE = "Popup AI"
PREFERENCES_TITLE = "Preferences"
NEW_PROMPT_TITLE = "New Prompt"
EDIT_PROMPT_TITLE = "Edit Prompt"

# Menu Items
MENU_PREFERENCES = "Preferences"
MENU_ABOUT = "About"
MENU_QUIT = "Quit"

# Button Labels
BTN_SEND = "Send"
BTN_STOP = "Stop"
BTN_CANCEL = "Cancel"
BTN_SAVE = "Save"
BTN_DELETE = "Delete"
BTN_CLEAR_ALL = "Clear All"
BTN_RESET = "Reset"
BTN_OK = "OK"

# Tooltips
TOOLTIP_NEW_CONVERSATION = "New Conversation"
TOOLTIP_CLEAR_CONVERSATION = "Clear Conversation"
TOOLTIP_CLEAR_ALL_HISTORY = "Clear All History"
TOOLTIP_TOGGLE_SIDEBAR = "Toggle Sidebar"
TOOLTIP_SELECT_MODEL = "Select AI Model"
TOOLTIP_SELECT_PROMPT = "Select Prompt Template"
TOOLTIP_DELETE_CONVERSATION = "Delete Conversation"
TOOLTIP_REFRESH_MODELS = "Refresh Model List"
TOOLTIP_COPY_SOURCE = "Copy Source"
TOOLTIP_EDIT_PROMPT = "Edit Prompt"
TOOLTIP_DELETE_PROMPT = "Delete Prompt"

# Section Titles
SECTION_HISTORY = "History"
SECTION_MODELS = "AI Models"
SECTION_PROMPTS = "Prompt Templates"
SECTION_API_SETTINGS = "API Settings"
SECTION_GENERAL = "General"
SECTION_APPEARANCE = "Appearance"

# Field Labels
LABEL_NAME = "Name"
LABEL_DESCRIPTION = "Description (optional)"
LABEL_SYSTEM_PROMPT = "System Prompt"
LABEL_ENDPOINT = "Endpoint"
LABEL_API_KEY = "API Key"
LABEL_DEFAULT_MODEL = "Default Model"
LABEL_AUTO_FETCH = "Auto-fetch Models"
LABEL_UI_FONT = "UI Font"
LABEL_FONT_FAMILY = "Font Family"
LABEL_FONT_SIZE = "Font Size"
LABEL_ADD_NEW_PROMPT = "Add New Prompt"

# Messages
MSG_NO_MESSAGES = ""
MSG_MESSAGES_COUNT = "{count} messages"
MSG_NEW_CONVERSATION = "New Conversation"
MSG_GENERATING = "Generating..."

# Placeholders
PLACEHOLDER_PROMPT_NAME = "Enter prompt name"
PLACEHOLDER_DESCRIPTION = "Brief description"

# Dialog Messages
DIALOG_CLEAR_ALL_TITLE = "Clear All History?"
DIALOG_CLEAR_ALL_BODY = (
    "This will permanently delete all conversation history. This action cannot be undone."
)
DIALOG_DELETE_PROMPT_TITLE = "Delete Prompt?"
DIALOG_DELETE_PROMPT_BODY = "Are you sure you want to delete '{name}'?"
DIALOG_ERROR_TITLE = "Error"

# Error Messages
ERROR_NO_MODEL = "Please select a model first"
ERROR_NO_AI_SERVICE = "No AI service configured"
ERROR_INIT_AI_SERVICE = "Failed to initialize AI service: {error}"
ERROR_GENERATE_RESPONSE = "Error generating response: {error}"
ERROR_NO_NAME = "Please enter a prompt name"
ERROR_NO_SYSTEM_PROMPT = "Please enter a system prompt"
ERROR_NAME_EXISTS = "A prompt with name '{name}' already exists"

# Descriptions
DESC_OLLAMA = "Local Ollama server configuration"
DESC_OPENAI = "OpenAI or OpenAI-compatible API configuration"
DESC_CONFIGURED_MODELS = "Configured AI models"
DESC_MANAGE_PROMPTS = "Manage your custom prompt templates"
DESC_DEFAULT_MODEL = "Model to use when starting a new conversation"
DESC_AUTO_FETCH_MODELS = "Automatically fetch available models on startup"
DESC_UI_FONT = "Font used in the application interface"
DESC_CONVERSATION_FONT = "Font used in the conversation display"
DESC_UI_FONT_SUB = "Font for buttons, menus, and controls"
DESC_CONVERSATION_FONT_SUB = "Font for chat messages"
DESC_FONT_SIZE_SUB = "Size in pixels"

# Preferences Pages
PAGE_GENERAL = "General"
PAGE_API_SETTINGS = "API Settings"
PAGE_MODELS = "Models"
PAGE_PROMPTS = "Prompts"
PAGE_APPEARANCE = "Appearance"

# Preference Groups
GROUP_OLLAMA = "Ollama"
GROUP_OPENAI = "OpenAI / Custom API"
GROUP_DEFAULT_SETTINGS = "Default Settings"
GROUP_UI_FONT = "Interface Font"
GROUP_CONVERSATION_FONT = "Conversation Font"
GROUP_RESET = "Reset"

# Action Rows
ACTION_RESET_UI_FONT = "Reset Interface Font"
ACTION_RESET_CONVERSATION_FONT = "Reset Conversation Font"

# Model Info
MODEL_INFO_FORMAT = "{type}: {model_id}"

# Conversation Display
CONV_ROLE_USER = "User"
CONV_ROLE_ASSISTANT = "Assistant"

# Default Prompt Templates
DEFAULT_PROMPTS = [
    {
        "name": "Default",
        "system_prompt": "You are a helpful AI assistant.",
        "description": "General purpose assistant",
        "default_model": None,
    },
    {
        "name": "Code Expert",
        "system_prompt": "You are an expert programmer. Provide clear, concise, and well-documented code solutions.",
        "description": "For programming questions",
        "default_model": None,
    },
    {
        "name": "Writer",
        "system_prompt": "You are a professional writer. Help with writing, editing, and improving text.",
        "description": "For writing assistance",
        "default_model": None,
    },
    {
        "name": "Translator",
        "system_prompt": "You are a professional translator. Translate text accurately while preserving meaning and tone.",
        "description": "For translation tasks",
        "default_model": None,
    },
]
