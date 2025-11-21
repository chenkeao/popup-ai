"""Main application window."""

import time
import uuid
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")

from gi.repository import Gtk, Adw, GLib, Gdk, Gio, WebKit

from popup_ai.config import Settings, Conversation, ConversationMessage, ModelConfig
from popup_ai.ai_service import create_ai_service, AIService, fetch_available_models
from popup_ai.preferences import PreferencesWindow
from popup_ai.html_template import generate_html_template
from popup_ai.logger import get_logger
from popup_ai.constants import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    SIDEBAR_WIDTH,
    INPUT_MAX_HEIGHT,
    STREAMING_UPDATE_INTERVAL,
    MAX_CONTEXT_MESSAGES,
    ASYNC_EXECUTOR_MAX_WORKERS,
    ASYNC_EXECUTOR_THREAD_PREFIX,
    AUTO_FETCH_DELAY_MS,
    MARGIN_SMALL,
    MARGIN_MEDIUM,
    CSS_CLASS_SIDEBAR,
    CSS_CLASS_NAVIGATION_SIDEBAR,
    CSS_CLASS_CARD,
    CSS_CLASS_TITLE_4,
    CSS_CLASS_HEADING,
    CSS_CLASS_CAPTION,
    CSS_CLASS_DIM_LABEL,
    CSS_CLASS_SUGGESTED_ACTION,
    CSS_CLASS_DESTRUCTIVE_ACTION,
    CSS_CLASS_FLAT,
    ICON_TRASH,
    ICON_ADD,
    ICON_MENU,
    ICON_CLEAR,
    ICON_SIDEBAR_SHOW,
    ICON_SIDEBAR_HIDE,
    ICON_REFRESH,
)
from popup_ai.ui_strings import (
    WINDOW_TITLE,
    BTN_SEND,
    BTN_STOP,
    TOOLTIP_NEW_CONVERSATION,
    TOOLTIP_CLEAR_CONVERSATION,
    TOOLTIP_CLEAR_ALL_HISTORY,
    TOOLTIP_TOGGLE_SIDEBAR,
    TOOLTIP_SELECT_MODEL,
    TOOLTIP_SELECT_PROMPT,
    TOOLTIP_DELETE_CONVERSATION,
    TOOLTIP_REFRESH_MODELS,
    SECTION_HISTORY,
    MENU_PREFERENCES,
    MENU_ABOUT,
    MENU_QUIT,
    MSG_MESSAGES_COUNT,
    MSG_NEW_CONVERSATION,
    DIALOG_CLEAR_ALL_TITLE,
    DIALOG_CLEAR_ALL_BODY,
    ERROR_NO_MODEL,
    ERROR_NO_AI_SERVICE,
    ERROR_INIT_AI_SERVICE,
    ERROR_GENERATE_RESPONSE,
)

# Configure logging
logger = get_logger(__name__)


class AsyncExecutor:
    """Shared async executor for running async tasks in background threads."""

    _instance = None
    _executor = None

    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize executor."""
        if AsyncExecutor._executor is None:
            AsyncExecutor._executor = ThreadPoolExecutor(
                max_workers=ASYNC_EXECUTOR_MAX_WORKERS,
                thread_name_prefix=ASYNC_EXECUTOR_THREAD_PREFIX,
            )

    def run_async(self, coro):
        """Run a coroutine in a background thread with proper cleanup."""

        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception as e:
                    logger.error(f"Error cleaning up event loop: {e}")
                finally:
                    loop.close()

        return self._executor.submit(run_in_thread)

    @classmethod
    def shutdown(cls):
        """Shutdown the executor."""
        if cls._executor:
            cls._executor.shutdown(wait=False)
            cls._executor = None


class PopupAIWindow(Adw.ApplicationWindow):
    """Main application window."""

    def __init__(self, application, settings: Settings, service_mode: bool = False):
        super().__init__(application=application, title=WINDOW_TITLE)

        logger.info(f"Initializing PopupAI window (service_mode={service_mode})")

        self.settings = settings
        self.service_mode = service_mode
        self.ai_service: Optional[AIService] = None
        self.current_conversation: Optional[Conversation] = None
        self.is_generating = False
        self.user_scrolled = False  # Track if user manually scrolled during generation
        self.async_executor = AsyncExecutor.get_instance()
        self._last_html_hash = None  # Cache for HTML to avoid unnecessary redraws

        # Load custom CSS
        self._load_css()

        # Set default window size
        self.set_default_size(
            self.settings.get("window_width", DEFAULT_WINDOW_WIDTH),
            self.settings.get("window_height", DEFAULT_WINDOW_HEIGHT),
        )

        # Build UI
        self.build_ui()

        # Load initial state
        self.load_state()

        # Connect window close handler
        self.connect("close-request", self.on_close_request)

        # Listen for theme changes to update WebView
        style_manager = Adw.StyleManager.get_default()
        style_manager.connect("notify::dark", self.on_theme_changed)

    def _load_css(self):
        """Load custom CSS styles."""
        try:
            from pathlib import Path

            # Load custom CSS file if exists
            css_file = Path(__file__).parent / "style.css"
            if css_file.exists():
                css_provider = Gtk.CssProvider()
                css_provider.load_from_path(str(css_file))
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )

            # Apply UI font settings
            self._apply_ui_font()
        except Exception as e:
            logger.warning(f"Failed to load CSS: {e}")

    def _apply_ui_font(self):
        """Apply UI font settings."""
        try:
            # Get UI font settings
            ui_font = self.settings.get("ui_font_family", "Sans 11")

            # Create dynamic CSS for UI font
            css_data = f"""
            window {{
                font-family: {ui_font};
            }}
            """

            # Create or update the font CSS provider
            if not hasattr(self, "_font_css_provider"):
                self._font_css_provider = Gtk.CssProvider()

            self._font_css_provider.load_from_data(css_data.encode())
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self._font_css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
            )
        except Exception as e:
            logger.warning(f"Failed to apply UI font: {e}")

    def build_ui(self):
        """Build the user interface."""
        # Use Paned for resizable sidebar
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(self.settings.get("sidebar_width", SIDEBAR_WIDTH))
        self.paned.set_shrink_start_child(False)
        self.paned.set_shrink_end_child(False)
        self.paned.set_resize_start_child(False)
        self.paned.set_resize_end_child(True)
        self.set_content(self.paned)

        # Sidebar for conversation history
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sidebar.set_size_request(200, -1)  # Minimum width
        self.sidebar.add_css_class(CSS_CLASS_SIDEBAR)
        self.paned.set_start_child(self.sidebar)

        # Sidebar header
        sidebar_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sidebar_header.set_spacing(MARGIN_SMALL)
        sidebar_header.set_margin_start(MARGIN_MEDIUM)
        sidebar_header.set_margin_end(MARGIN_MEDIUM)
        sidebar_header.set_margin_top(MARGIN_MEDIUM)
        sidebar_header.set_margin_bottom(MARGIN_MEDIUM)
        self.sidebar.append(sidebar_header)

        sidebar_label = Gtk.Label(label=SECTION_HISTORY)
        sidebar_label.set_halign(Gtk.Align.START)
        sidebar_label.set_hexpand(True)
        sidebar_label.add_css_class(CSS_CLASS_TITLE_4)
        sidebar_header.append(sidebar_label)

        # Clear all history button
        clear_all_btn = Gtk.Button.new_from_icon_name(ICON_TRASH)
        clear_all_btn.set_tooltip_text(TOOLTIP_CLEAR_ALL_HISTORY)
        clear_all_btn.connect("clicked", self.on_clear_all_history)
        sidebar_header.append(clear_all_btn)

        # New conversation button
        new_conv_btn = Gtk.Button.new_from_icon_name(ICON_ADD)
        new_conv_btn.set_tooltip_text(TOOLTIP_NEW_CONVERSATION)
        new_conv_btn.connect("clicked", lambda _: self.on_clear_conversation(None))
        sidebar_header.append(new_conv_btn)

        # Toggle sidebar button
        self.toggle_sidebar_btn = Gtk.Button.new_from_icon_name(ICON_SIDEBAR_SHOW)
        self.toggle_sidebar_btn.set_tooltip_text(TOOLTIP_TOGGLE_SIDEBAR)
        self.toggle_sidebar_btn.connect("clicked", self.on_toggle_sidebar)
        self.sidebar_visible = True

        # Scrolled window for conversation list
        conv_scroll = Gtk.ScrolledWindow()
        conv_scroll.set_vexpand(True)
        conv_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar.append(conv_scroll)

        # Conversation list
        self.conv_list_box = Gtk.ListBox()
        self.conv_list_box.add_css_class(CSS_CLASS_NAVIGATION_SIDEBAR)
        self.conv_list_box.connect("row-activated", self.on_conversation_selected)
        conv_scroll.set_child(self.conv_list_box)

        # Main content box
        content_wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_wrapper.set_hexpand(True)
        self.paned.set_end_child(content_wrapper)

        # Header bar
        header = Adw.HeaderBar()
        content_wrapper.append(header)

        # Add toggle sidebar button to header
        header.pack_start(self.toggle_sidebar_btn)

        # Prompt selector
        self.prompt_dropdown = Gtk.DropDown()
        self.prompt_dropdown.set_tooltip_text(TOOLTIP_SELECT_PROMPT)
        self.update_prompt_list()
        self.prompt_dropdown.connect("notify::selected-item", self.on_prompt_changed)
        header.pack_start(self.prompt_dropdown)

        # Model selector with fixed width container
        model_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        model_box.set_spacing(MARGIN_SMALL)
        model_box.set_size_request(150, -1)  # Fixed width

        self.model_dropdown = Gtk.DropDown()
        self.model_dropdown.set_tooltip_text(TOOLTIP_SELECT_MODEL)
        self.model_dropdown.set_hexpand(True)
        # Enable ellipsizing for long model names
        self.model_dropdown.set_enable_search(True)
        self.update_model_list()
        self.model_dropdown.connect("notify::selected-item", self.on_model_changed)
        model_box.append(self.model_dropdown)

        # Refresh models button
        refresh_models_btn = Gtk.Button.new_from_icon_name(ICON_REFRESH)
        refresh_models_btn.set_tooltip_text(TOOLTIP_REFRESH_MODELS)
        refresh_models_btn.connect("clicked", self.on_refresh_models)
        model_box.append(refresh_models_btn)

        header.pack_start(model_box)

        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name(ICON_MENU)
        menu = Gio.Menu()
        menu.append(MENU_PREFERENCES, "app.preferences")
        menu.append(MENU_ABOUT, "app.about")
        menu.append(MENU_QUIT, "app.quit")
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)

        # Clear conversation button
        clear_btn = Gtk.Button.new_from_icon_name(ICON_CLEAR)
        clear_btn.set_tooltip_text(TOOLTIP_CLEAR_CONVERSATION)
        clear_btn.connect("clicked", self.on_clear_conversation)
        header.pack_end(clear_btn)

        # Main content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_start(MARGIN_MEDIUM)
        content_box.set_margin_end(MARGIN_MEDIUM)
        content_box.set_margin_top(MARGIN_MEDIUM)
        content_box.set_margin_bottom(MARGIN_MEDIUM)
        content_box.set_spacing(MARGIN_MEDIUM)
        content_wrapper.append(content_box)

        # Scrolled window for conversation
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        content_box.append(scrolled)

        # WebView for conversation
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)

        # Optimize WebKit settings for better performance
        webkit_settings = self.webview.get_settings()
        webkit_settings.set_enable_write_console_messages_to_stdout(
            False
        )  # Disable console logging for performance
        webkit_settings.set_enable_developer_extras(False)
        webkit_settings.set_hardware_acceleration_policy(
            WebKit.HardwareAccelerationPolicy.ALWAYS
        )  # Enable hardware acceleration
        webkit_settings.set_enable_page_cache(False)  # Disable page cache to avoid stale content
        webkit_settings.set_enable_smooth_scrolling(True)  # Enable smooth scrolling
        webkit_settings.set_javascript_can_access_clipboard(
            True
        )  # Allow clipboard access for copy functionality

        # Set background color to support transparency
        self.webview.set_background_color(Gdk.RGBA(0, 0, 0, 0))

        # Disable context menu (right-click menu)
        self.webview.connect("context-menu", lambda *args: True)

        # Set up script message handler for scroll detection
        content_manager = self.webview.get_user_content_manager()
        content_manager.register_script_message_handler("scrolled")
        content_manager.connect("script-message-received::scrolled", self._on_user_scrolled)

        scrolled.set_child(self.webview)

        # Pre-load initial HTML template to avoid delay
        initial_html = self._generate_html()
        self.webview.load_html(initial_html, "file:///")
        self._last_html_hash = hash(initial_html)

        # Input area
        input_frame = Adw.Clamp()
        input_frame.set_maximum_size(800)
        content_box.append(input_frame)

        # Main horizontal box for input and buttons
        input_main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        input_main_box.set_spacing(MARGIN_SMALL)
        input_frame.set_child(input_main_box)

        # Text input (expandable)
        input_scroll = Gtk.ScrolledWindow()
        input_scroll.set_max_content_height(self.settings.get("input_max_height", INPUT_MAX_HEIGHT))
        input_scroll.set_propagate_natural_height(True)
        input_scroll.set_hexpand(True)
        input_main_box.append(input_scroll)

        self.input_text = Gtk.TextView()
        self.input_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.input_text.add_css_class(CSS_CLASS_CARD)
        self.input_text.set_left_margin(MARGIN_MEDIUM)
        self.input_text.set_right_margin(MARGIN_MEDIUM)
        self.input_text.set_top_margin(MARGIN_MEDIUM)
        self.input_text.set_bottom_margin(MARGIN_MEDIUM)
        input_scroll.set_child(self.input_text)

        # Button box (vertical to stack buttons if needed)
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        button_box.set_spacing(MARGIN_SMALL)
        button_box.set_valign(Gtk.Align.CENTER)
        input_main_box.append(button_box)

        # Stop button
        self.stop_btn = Gtk.Button(label=BTN_STOP)
        self.stop_btn.add_css_class(CSS_CLASS_DESTRUCTIVE_ACTION)
        self.stop_btn.connect("clicked", self.on_stop)
        self.stop_btn.set_visible(False)
        button_box.append(self.stop_btn)

        # Send button
        self.send_btn = Gtk.Button(label=BTN_SEND)
        self.send_btn.add_css_class(CSS_CLASS_SUGGESTED_ACTION)
        self.send_btn.connect("clicked", self.on_send)
        button_box.append(self.send_btn)

        # Keyboard shortcut for sending
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.input_text.add_controller(key_controller)

    def update_model_list(self):
        """Update the model dropdown list."""
        model_list = Gtk.StringList()
        for model in self.settings.models:
            model_list.append(model.name)
        self.model_dropdown.set_model(model_list)

        # Always use default model on startup (not selected_model)
        default_model = self.settings.get("default_model", "")

        selected_index = -1
        if default_model:
            for i, model in enumerate(self.settings.models):
                if model.name == default_model:
                    selected_index = i
                    break

        if selected_index >= 0:
            self.model_dropdown.set_selected(selected_index)
        elif self.settings.models:
            # Select first if no default
            self.model_dropdown.set_selected(0)
            selected_index = 0

        # Initialize AI service with selected model
        if selected_index >= 0:
            self.initialize_ai_service()

    def update_prompt_list(self):
        """Update the prompt dropdown list."""
        prompt_list = Gtk.StringList()
        for prompt in self.settings.prompts:
            prompt_list.append(prompt.name)
        self.prompt_dropdown.set_model(prompt_list)

        # Select saved prompt
        selected_prompt = self.settings.get("selected_prompt", "")
        if selected_prompt:
            for i, prompt in enumerate(self.settings.prompts):
                if prompt.name == selected_prompt:
                    self.prompt_dropdown.set_selected(i)
                    break
        else:
            # Select first by default
            if self.settings.prompts:
                self.prompt_dropdown.set_selected(0)

    def on_refresh_models(self, button):
        """Handle refresh models button click."""
        # Run auto-fetch in background
        self.async_executor.run_async(self.auto_fetch_models())

    def on_model_changed(self, dropdown, param):
        """Handle model selection change."""
        selected_idx = dropdown.get_selected()
        if selected_idx < len(self.settings.models):
            # Don't save to config - just switch in current session
            self.initialize_ai_service()

    def on_prompt_changed(self, dropdown, param):
        """Handle prompt selection change."""
        selected_idx = dropdown.get_selected()
        if selected_idx < len(self.settings.prompts):
            prompt = self.settings.prompts[selected_idx]
            self.settings.set("selected_prompt", prompt.name)

            # If the prompt has a default model, switch to it
            if prompt.default_model:
                for i, model in enumerate(self.settings.models):
                    if model.name == prompt.default_model:
                        self.model_dropdown.set_selected(i)
                        break

    def initialize_ai_service(self):
        """Initialize AI service based on selected model."""
        selected_idx = self.model_dropdown.get_selected()
        if selected_idx >= len(self.settings.models):
            return

        model_config = self.settings.models[selected_idx]

        logger.info(f"Initializing AI service: {model_config.type} - {model_config.name}")

        try:
            self.ai_service = create_ai_service(
                model_type=model_config.type,
                endpoint=model_config.endpoint or "",
                model=model_config.model_id,
                api_key=model_config.api_key,
            )
            logger.info(f"AI service initialized successfully: {model_config.name}")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}", exc_info=True)
            self.show_error(ERROR_INIT_AI_SERVICE.format(error=e))

    def load_state(self):
        """Load initial state."""
        # Load conversation history
        self.load_conversation_history()

        # Load the most recent conversation, or create new one if none exists
        conversations = self.settings.load_conversations()
        if conversations:
            # Load the most recent conversation (already sorted by updated_at)
            self.current_conversation = conversations[0]
            self._last_html_hash = None
            self._update_webview(force=True)

            # Select the first row in the conversation list (most recent)
            first_row = self.conv_list_box.get_row_at_index(0)
            if first_row:
                self.conv_list_box.select_row(first_row)
        else:
            # Create new conversation if no history exists
            self.start_new_conversation()

        # Auto-fetch models from configured endpoints (delayed to allow event loop)
        if self.settings.get("auto_fetch_models", True):
            GLib.timeout_add(AUTO_FETCH_DELAY_MS, self._start_auto_fetch)

    def _start_auto_fetch(self):
        """Start auto-fetch using shared executor."""
        self.async_executor.run_async(self.auto_fetch_models())
        return False  # Don't repeat

    async def auto_fetch_models(self):
        """Automatically fetch models from configured endpoints."""
        fetched_any = False

        # Clear existing models before fetching new ones
        # This ensures old/filtered models are removed
        self.settings.models = []

        # Fetch from Ollama
        ollama_endpoint = self.settings.get("ollama_endpoint", "http://localhost:11434")
        if ollama_endpoint:
            try:
                model_ids = await fetch_available_models("ollama", ollama_endpoint)
                for model_id in model_ids:
                    model_config = ModelConfig(
                        name=f"{model_id}",
                        type="ollama",
                        endpoint=ollama_endpoint,
                        model_id=model_id,
                    )
                    self.settings.add_model(model_config)
                    fetched_any = True
            except Exception as e:
                logger.error(f"Failed to fetch Ollama models: {e}")

        # Fetch from OpenAI if API key is configured
        openai_endpoint = self.settings.get("openai_endpoint", "")
        openai_api_key = self.settings.get("openai_api_key", "")
        if openai_endpoint and openai_api_key:
            try:
                model_ids = await fetch_available_models("api", openai_endpoint, openai_api_key)
                for model_id in model_ids:
                    model_config = ModelConfig(
                        name=f"{model_id}",
                        type="api",
                        endpoint=openai_endpoint,
                        api_key=openai_api_key,
                        model_id=model_id,
                    )
                    self.settings.add_model(model_config)
                    fetched_any = True
            except Exception as e:
                logger.error(f"Failed to fetch OpenAI models: {e}")

        # Fetch from custom API if configured
        custom_endpoint = self.settings.get("custom_api_endpoint", "")
        custom_api_key = self.settings.get("custom_api_key", "")
        if custom_endpoint:
            try:
                model_ids = await fetch_available_models("api", custom_endpoint, custom_api_key)
                for model_id in model_ids:
                    model_config = ModelConfig(
                        name=f"{model_id}",
                        type="api",
                        endpoint=custom_endpoint,
                        api_key=custom_api_key if custom_api_key else None,
                        model_id=model_id,
                    )
                    self.settings.add_model(model_config)
                    fetched_any = True
            except Exception as e:
                logger.error(f"Failed to fetch custom API models: {e}")

        # Update UI on main thread
        if fetched_any:
            GLib.idle_add(self.update_model_list)
            # update_model_list will call initialize_ai_service

    def load_conversation_history(self):
        """Load conversation history into sidebar."""
        # Clear existing items
        child = self.conv_list_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.conv_list_box.remove(child)
            child = next_child

        # Load conversations
        conversations = self.settings.load_conversations()

        # Add to list
        for conv in conversations:
            self.add_conversation_to_list(conv)

    def add_conversation_to_list(self, conversation: Conversation):
        """Add a conversation to the sidebar list."""
        row = Gtk.ListBoxRow()
        row.conversation_id = conversation.id

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_spacing(MARGIN_SMALL)
        box.set_margin_start(MARGIN_MEDIUM)
        box.set_margin_end(MARGIN_MEDIUM)
        box.set_margin_top(8)
        box.set_margin_bottom(8)

        # Title and preview
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        text_box.set_spacing(2)
        text_box.set_hexpand(True)

        title_label = Gtk.Label(label=conversation.title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(3)  # ELLIPSIZE_END
        title_label.add_css_class(CSS_CLASS_HEADING)
        text_box.append(title_label)

        # Show message count
        msg_count = len(conversation.messages)
        preview_label = Gtk.Label(label=MSG_MESSAGES_COUNT.format(count=msg_count))
        preview_label.set_halign(Gtk.Align.START)
        preview_label.add_css_class(CSS_CLASS_DIM_LABEL)
        preview_label.add_css_class(CSS_CLASS_CAPTION)
        text_box.append(preview_label)

        box.append(text_box)

        # Delete button
        delete_btn = Gtk.Button.new_from_icon_name(ICON_TRASH)
        delete_btn.set_valign(Gtk.Align.CENTER)
        delete_btn.add_css_class(CSS_CLASS_FLAT)
        delete_btn.set_tooltip_text(TOOLTIP_DELETE_CONVERSATION)
        delete_btn.connect("clicked", self.on_delete_conversation, conversation.id)
        box.append(delete_btn)

        row.set_child(box)
        self.conv_list_box.append(row)

    def on_conversation_selected(self, list_box, row):
        """Handle conversation selection from sidebar."""
        if not hasattr(row, "conversation_id"):
            return

        # Load the selected conversation
        conversations = self.settings.load_conversations()
        for conv in conversations:
            if conv.id == row.conversation_id:
                self.current_conversation = conv
                self._last_html_hash = None
                self._update_webview(force=True)
                # Ensure the row is selected
                self.conv_list_box.select_row(row)
                break

    def on_delete_conversation(self, button, conversation_id: str):
        """Handle conversation deletion."""
        # Delete from storage
        self.settings.delete_conversation(conversation_id)

        # If it's the current conversation, start a new one
        if self.current_conversation and self.current_conversation.id == conversation_id:
            self.start_new_conversation()

        # Reload history
        self.load_conversation_history()

    def on_clear_all_history(self, button):
        """Handle clearing all conversation history."""
        # Show confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(DIALOG_CLEAR_ALL_TITLE)
        dialog.set_body(DIALOG_CLEAR_ALL_BODY)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Clear All")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self.on_clear_all_history_response)
        dialog.present()

    def on_clear_all_history_response(self, dialog, response):
        """Handle confirmation dialog response."""
        if response == "delete":
            # Get all conversations
            conversations = self.settings.load_conversations()

            # Delete each conversation
            for conv in conversations:
                self.settings.delete_conversation(conv.id)

            # Start a new conversation
            self.start_new_conversation()

            # Reload history (will be empty now)
            self.load_conversation_history()

    def on_toggle_sidebar(self, button):
        """Toggle sidebar visibility."""
        self.sidebar_visible = not self.sidebar_visible
        self.sidebar.set_visible(self.sidebar_visible)

        # Update button icon
        if self.sidebar_visible:
            button.set_icon_name(ICON_SIDEBAR_SHOW)
        else:
            button.set_icon_name(ICON_SIDEBAR_HIDE)

    def start_new_conversation(self):
        """Start a new conversation."""
        self.current_conversation = Conversation(
            id=str(uuid.uuid4()),
            title=MSG_NEW_CONVERSATION,
            messages=[],
            created_at=time.time(),
            updated_at=time.time(),
        )
        self._last_html_hash = None  # Reset HTML cache
        self._update_webview()

    def _on_user_scrolled(self, content_manager, result):
        """Handle user scroll event from JavaScript."""
        if self.is_generating:
            self.user_scrolled = True

    def _update_webview(self, force=False):
        """Update the webview with current conversation.

        Args:
            force: Force update even if HTML hasn't changed
        """
        html = self._generate_html()

        # Only update if HTML changed or forced
        html_hash = hash(html)
        if force or html_hash != self._last_html_hash:
            self._last_html_hash = html_hash
            self.webview.load_html(html, "file:///")

    def _update_streaming_content(self, content: str):
        """Update streaming content via JavaScript without reloading page.

        Args:
            content: The new content to display
        """
        import markdown
        import json

        # Convert markdown to HTML
        content_html = markdown.markdown(
            content, extensions=["fenced_code", "codehilite", "tables"]
        )

        # Use JSON.stringify to properly escape the strings
        escaped_content = json.dumps(content_html)
        escaped_raw = json.dumps(content)

        # JavaScript to update the last message
        js_code = f"""
        (function() {{
            var messages = document.querySelectorAll('.message-content');
            if (messages.length > 0) {{
                var lastMessage = messages[messages.length - 1];
                lastMessage.innerHTML = {escaped_content};
                lastMessage.setAttribute('data-raw', {escaped_raw});
                
                // Re-render MathJax if available (debounced)
                if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {{
                    if (window.mathJaxTimeout) clearTimeout(window.mathJaxTimeout);
                    window.mathJaxTimeout = setTimeout(function() {{
                        MathJax.typesetPromise([lastMessage]).catch(function(err) {{
                            console.error('MathJax error:', err);
                        }});
                    }}, 100);
                }}
                
                // Auto-scroll if user hasn't scrolled manually
                var userScrolledFlag = {str(self.user_scrolled).lower()};
                if (!userScrolledFlag) {{
                    var anchor = document.getElementById('scroll-anchor');
                    if (anchor) {{
                        anchor.scrollIntoView({{block: 'end', behavior: 'auto'}});
                    }}
                }}
            }}
        }})();
        """

        try:
            self.webview.evaluate_javascript(js_code, -1, None, None, None)
        except Exception as e:
            logger.warning(f"Failed to update streaming content via JS: {e}")

    def _generate_html(self) -> str:
        """Generate HTML for the conversation."""
        import html
        import markdown
        from popup_ai.ui_strings import CONV_ROLE_USER, CONV_ROLE_ASSISTANT, TOOLTIP_COPY_SOURCE

        # Detect dark mode
        style_manager = Adw.StyleManager.get_default()
        is_dark = style_manager.get_dark()

        # Get font settings
        font_family = self.settings.get("webview_font_family", "Sans")
        font_size = self.settings.get("webview_font_size", 14)

        messages_html = ""

        # Show welcome message if no messages
        if not self.current_conversation or not self.current_conversation.messages:
            welcome_color = "rgba(255, 255, 255, 0.5)" if is_dark else "rgba(0, 0, 0, 0.3)"
            messages_html = f"""
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 60vh;
                text-align: center;
                color: {welcome_color};
                font-size: {font_size + 6}px;
                font-weight: 300;
                padding: 40px;
            ">
                <div>
                    <div style="font-size: {font_size + 20}px; margin-bottom: 20px;">💬</div>
                    <div>Popup AI</div>
                </div>
            </div>
            """
        elif self.current_conversation and self.current_conversation.messages:
            for idx, msg in enumerate(self.current_conversation.messages):
                role_class = "user" if msg.role == "user" else "assistant"
                # Escape the raw content for data attribute
                raw_content = html.escape(msg.content, quote=True)

                # Convert markdown to HTML for assistant messages
                if msg.role == "assistant":
                    content_html = markdown.markdown(
                        msg.content, extensions=["fenced_code", "codehilite", "tables"]
                    )
                else:
                    content_html = html.escape(msg.content).replace("\n", "<br>")

                role_display = CONV_ROLE_USER if msg.role == "user" else CONV_ROLE_ASSISTANT

                # Build token info display
                token_info_html = ""
                if msg.tokens_input is not None or msg.tokens_output is not None:
                    token_parts = []
                    if msg.tokens_input is not None:
                        token_parts.append(f"输入: {msg.tokens_input:,}")
                    if msg.tokens_output is not None:
                        token_parts.append(f"输出: {msg.tokens_output:,}")
                    if msg.tokens_input is not None and msg.tokens_output is not None:
                        total = msg.tokens_input + msg.tokens_output
                        token_parts.append(f"总计: {total:,}")
                    token_info_html = (
                        f'<span class="token-info">🎫 {" | ".join(token_parts)}</span>'
                    )

                messages_html += f"""
                <div class="message {role_class}">
                    <div class="message-header">
                        <span>{role_display} {token_info_html}</span>
                        <button class="copy-btn" onclick="copyMessage('{idx}')" title="{TOOLTIP_COPY_SOURCE}">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2Z"/>
                                <path d="M2 5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1v1a3 3 0 0 1-3 3H2a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3h1v1H2Z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="message-content" data-raw="{raw_content}">{content_html}</div>
                </div>
                """

        return generate_html_template(
            messages_html=messages_html,
            font_family=font_family,
            font_size=font_size,
            is_dark=is_dark,
            user_scrolled=self.user_scrolled,
        )

    def clear_conversation_view(self):
        """Clear the conversation view."""
        self._update_webview()

    def add_message_to_conversation(self, role: str, content: str):
        """Add a message to the current conversation."""
        if not self.current_conversation:
            self.start_new_conversation()

        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time(),
        )
        self.current_conversation.messages.append(message)
        self.current_conversation.updated_at = time.time()

        # Update title based on first user message
        if role == "user" and len(self.current_conversation.messages) == 1:
            self.current_conversation.title = content[:50] + ("..." if len(content) > 50 else "")

        # Force update to ensure new message is displayed immediately
        self._update_webview(force=True)

    def on_send(self, button):
        """Handle send button click."""
        if self.is_generating:
            return

        buffer = self.input_text.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        text = buffer.get_text(start_iter, end_iter, False).strip()

        if not text:
            return

        # Check if AI service is initialized
        if not self.ai_service:
            logger.warning("Send attempted without AI service initialized")
            self.show_error(ERROR_NO_MODEL)
            return

        logger.info(f"User message sent: {text[:100]}{'...' if len(text) > 100 else ''}")

        # Clear input
        buffer.set_text("")

        # Reset scroll flag for new message
        self.user_scrolled = False

        # Clear saved scroll position in browser
        try:
            self.webview.evaluate_javascript(
                "sessionStorage.removeItem('scrollPos');", -1, None, None, None
            )
        except Exception as e:
            logger.warning(f"Failed to clear scroll position: {e}")

        # Add user message
        self.add_message_to_conversation("user", text)

        # Generate response
        self.generate_response()

    def generate_response(self):
        """Generate AI response."""
        if not self.ai_service:
            logger.error("Generate response called without AI service")
            self.show_error(ERROR_NO_AI_SERVICE)
            return

        if not self.current_conversation or not self.current_conversation.messages:
            logger.warning("Generate response called without conversation or messages")
            return

        logger.info("Starting AI response generation")

        # Show stop button, hide send button
        self.is_generating = True
        self.send_btn.set_sensitive(False)
        self.stop_btn.set_visible(True)

        # Get selected prompt
        selected_idx = self.prompt_dropdown.get_selected()
        system_prompt = None
        if selected_idx < len(self.settings.prompts):
            system_prompt = self.settings.prompts[selected_idx].system_prompt

        # Prepare messages with context limit
        all_messages = self.current_conversation.messages

        if len(all_messages) > MAX_CONTEXT_MESSAGES:
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in all_messages[-MAX_CONTEXT_MESSAGES:]
            ]
        else:
            messages = [{"role": msg.role, "content": msg.content} for msg in all_messages]

        # Add placeholder for streaming message
        self.streaming_content = ""
        placeholder_msg = ConversationMessage(
            role="assistant",
            content="...",  # Add loading indicator
            timestamp=time.time(),
        )
        self.current_conversation.messages.append(placeholder_msg)
        # Force update to show user message and placeholder immediately
        self._update_webview(force=True)

        # Run async task using shared executor
        self.async_executor.run_async(self.stream_response(messages, system_prompt))

    async def stream_response(self, messages, system_prompt):
        """Stream AI response."""
        full_response = ""
        chunk_count = 0
        update_frequency = 3  # Update every N chunks instead of time-based

        # Reset scroll flag for new generation
        self.user_scrolled = False

        try:
            async for chunk in self.ai_service.stream_completion(messages, system_prompt):
                if not self.is_generating:
                    break

                full_response += chunk
                chunk_count += 1

                # Update UI every N chunks for consistent performance
                if chunk_count >= update_frequency:
                    # Update the last message in conversation
                    if self.current_conversation and self.current_conversation.messages:
                        self.current_conversation.messages[-1].content = full_response
                        # Use JavaScript to update content without reloading entire page
                        GLib.idle_add(self._update_streaming_content, full_response)
                    chunk_count = 0

            # Final update with complete response
            if full_response and self.current_conversation:
                # Get token usage from AI service
                tokens_input, tokens_output = self.ai_service.get_last_token_usage()

                # Update the assistant message with content and token info
                self.current_conversation.messages[-1].content = full_response
                self.current_conversation.messages[-1].tokens_input = tokens_input
                self.current_conversation.messages[-1].tokens_output = tokens_output

                # Also update the user message with input tokens (it was part of the prompt)
                if len(self.current_conversation.messages) >= 2:
                    # The user message is second to last
                    self.current_conversation.messages[-2].tokens_input = tokens_input

                self.current_conversation.updated_at = time.time()

                logger.info(
                    f"Response completed. Tokens: input={tokens_input}, output={tokens_output}"
                )

                # Force reload to show token info
                GLib.idle_add(self._update_webview, True)

                # Save conversation
                self.settings.save_conversation(self.current_conversation)

                # Update conversation list in sidebar
                GLib.idle_add(self.load_conversation_history)

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            GLib.idle_add(self.show_error, ERROR_GENERATE_RESPONSE.format(error=e))

        finally:
            GLib.idle_add(self.reset_ui_state)

    def reset_ui_state(self):
        """Reset UI state after generation."""
        self.is_generating = False
        self.send_btn.set_sensitive(True)
        self.stop_btn.set_visible(False)

    def on_stop(self, button):
        """Handle stop button click."""
        if self.ai_service and hasattr(self.ai_service, "cancel"):
            self.ai_service.cancel()
        self.is_generating = False
        self.reset_ui_state()

    def on_clear_conversation(self, button):
        """Handle clear conversation button click."""
        # Save current conversation if it has messages
        if self.current_conversation and self.current_conversation.messages:
            self.settings.save_conversation(self.current_conversation)
            self.load_conversation_history()

        # Start new conversation
        self.start_new_conversation()

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press in input area."""
        # Ctrl+Enter to send
        if keyval == Gdk.KEY_Return and state & Gdk.ModifierType.CONTROL_MASK:
            self.on_send(None)
            return True
        return False

    def _clean_input_text(self, text: str) -> str:
        """Clean input text by normalizing whitespace.

        - Replace newlines with spaces
        - Replace tabs with spaces
        - Collapse multiple spaces into one
        - Strip leading and trailing whitespace
        """
        import re

        # Replace newlines and tabs with spaces
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        # Collapse multiple spaces into one
        text = re.sub(r" +", " ", text)
        # Strip leading and trailing whitespace
        text = text.strip()
        return text

    def set_initial_text(self, text: str):
        """Set initial text in the input area."""
        if text:
            # Clean the text before setting it
            cleaned_text = self._clean_input_text(text)
            if cleaned_text:
                buffer = self.input_text.get_buffer()
                buffer.set_text(cleaned_text)
                # Force the TextView to recalculate its size
                self.input_text.queue_resize()
                # Also trigger resize on the parent ScrolledWindow
                input_scroll = self.input_text.get_parent()
                if input_scroll:
                    # Use idle_add to ensure this happens after the text is rendered
                    GLib.idle_add(input_scroll.queue_resize)

    def focus_input(self):
        """Focus on the input text area."""
        self.input_text.grab_focus()

    def show_preferences(self):
        """Show preferences window."""
        prefs = PreferencesWindow(self, self.settings, self.on_settings_changed)
        prefs.present()

    def on_settings_changed(self):
        """Handle settings changes from preferences window."""
        # Update prompt list
        self.update_prompt_list()

        # Update model list
        self.update_model_list()

        # Apply UI font changes
        self._apply_ui_font()

        # Update input max height if changed
        if hasattr(self, "input_text"):
            input_scroll = self.input_text.get_parent()
            if input_scroll:
                input_scroll.set_max_content_height(
                    self.settings.get("input_max_height", INPUT_MAX_HEIGHT)
                )

        # Refresh webview with new font settings
        self._last_html_hash = None  # Clear cache to force redraw
        self._update_webview(force=True)

    def on_theme_changed(self, style_manager, param):
        """Handle system theme changes (light/dark mode)."""
        # Clear HTML cache and force WebView update to use new theme colors
        self._last_html_hash = None
        self._update_webview(force=True)

    def show_error(self, message: str):
        """Show an error dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()

    def on_close_request(self, window):
        """Handle window close request."""
        # Save window size
        width, height = self.get_default_size()
        self.settings.set("window_width", width)
        self.settings.set("window_height", height)

        # Save sidebar width
        sidebar_width = self.paned.get_position()
        self.settings.set("sidebar_width", sidebar_width)

        # Save current conversation
        if self.current_conversation and self.current_conversation.messages:
            self.settings.save_conversation(self.current_conversation)

        # In service mode, destroy the window to free resources
        # The service will recreate it on next activation
        if self.service_mode:
            # Stop any ongoing generation
            if self.is_generating:
                self.on_stop(None)
            # Allow the window to be destroyed
            return False
        else:
            # In normal mode, hide the window instead of destroying it
            self.set_visible(False)
            return True  # Prevent the default handler (which would destroy the window)
