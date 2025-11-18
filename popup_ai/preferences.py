"""Preferences window for managing settings."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from popup_ai.config import Settings, ModelConfig, PromptTemplate
from popup_ai.constants import (
    MARGIN_SMALL,
    MARGIN_MEDIUM,
    MARGIN_LARGE,
    SPACING_SMALL,
    SPACING_MEDIUM,
    SPACING_LARGE,
    CSS_CLASS_HEADING,
    CSS_CLASS_SUGGESTED_ACTION,
    CSS_CLASS_DESTRUCTIVE_ACTION,
    CSS_CLASS_FLAT,
    ICON_EDIT,
    ICON_TRASH,
    ICON_ADD,
    ICON_NETWORK,
    ICON_SCIENCE,
    ICON_SYSTEM,
    ICON_GRAPHICS,
    DEFAULT_UI_FONT,
    DEFAULT_WEBVIEW_FONT_FAMILY,
    DEFAULT_WEBVIEW_FONT_SIZE,
)


class PreferencesWindow(Adw.PreferencesWindow):
    """Preferences window."""

    def __init__(self, parent, settings: Settings, on_settings_changed=None):
        super().__init__(transient_for=parent, modal=True)

        self.settings = settings
        self.on_settings_changed = on_settings_changed
        self.set_default_size(700, 600)

        # General Settings page
        self.build_general_settings_page()

        # API Settings page
        self.build_api_settings_page()

        # Models page
        self.build_models_page()

        # Appearance page
        self.build_appearance_page()

    def build_api_settings_page(self):
        """Build API settings page."""
        api_page = Adw.PreferencesPage()
        api_page.set_title("API Settings")
        api_page.set_icon_name("network-server-symbolic")
        self.add(api_page)

        # Ollama settings
        ollama_group = Adw.PreferencesGroup()
        ollama_group.set_title("Ollama")
        ollama_group.set_description("Local Ollama server configuration")
        api_page.add(ollama_group)

        # Ollama endpoint
        self.ollama_endpoint_row = Adw.EntryRow()
        self.ollama_endpoint_row.set_title("Endpoint")
        self.ollama_endpoint_row.set_text(
            self.settings.get("ollama_endpoint", "http://localhost:11434")
        )
        self.ollama_endpoint_row.connect("changed", self.on_config_changed, "ollama_endpoint")
        ollama_group.add(self.ollama_endpoint_row)

        # OpenAI settings
        openai_group = Adw.PreferencesGroup()
        openai_group.set_title("OpenAI / Custom API")
        openai_group.set_description("OpenAI or OpenAI-compatible API configuration")
        api_page.add(openai_group)

        # OpenAI endpoint
        self.openai_endpoint_row = Adw.EntryRow()
        self.openai_endpoint_row.set_title("Endpoint")
        self.openai_endpoint_row.set_text(
            self.settings.get("openai_endpoint", "https://api.openai.com")
        )
        self.openai_endpoint_row.connect("changed", self.on_config_changed, "openai_endpoint")
        openai_group.add(self.openai_endpoint_row)

        # OpenAI API key
        self.openai_api_key_row = Adw.PasswordEntryRow()
        self.openai_api_key_row.set_title("API Key")
        self.openai_api_key_row.set_text(self.settings.get("openai_api_key", ""))
        self.openai_api_key_row.connect("changed", self.on_config_changed, "openai_api_key")
        openai_group.add(self.openai_api_key_row)

        # Custom API settings
        custom_group = Adw.PreferencesGroup()
        custom_group.set_title("Custom API")
        custom_group.set_description("Additional OpenAI-compatible API configuration")
        api_page.add(custom_group)

        # Custom API endpoint
        self.custom_endpoint_row = Adw.EntryRow()
        self.custom_endpoint_row.set_title("Endpoint")
        self.custom_endpoint_row.set_text(self.settings.get("custom_api_endpoint", ""))
        self.custom_endpoint_row.connect("changed", self.on_config_changed, "custom_api_endpoint")
        custom_group.add(self.custom_endpoint_row)

        # Custom API key
        self.custom_api_key_row = Adw.PasswordEntryRow()
        self.custom_api_key_row.set_title("API Key")
        self.custom_api_key_row.set_text(self.settings.get("custom_api_key", ""))
        self.custom_api_key_row.connect("changed", self.on_config_changed, "custom_api_key")
        custom_group.add(self.custom_api_key_row)

    def build_models_page(self):
        """Build models page."""
        models_page = Adw.PreferencesPage()
        models_page.set_title("Models")
        models_page.set_icon_name("applications-science-symbolic")
        self.add(models_page)

        self.models_group = Adw.PreferencesGroup()
        self.models_group.set_title("AI Models")
        self.models_group.set_description("Configured AI models")
        models_page.add(self.models_group)

        self.refresh_models_list()

    def refresh_models_list(self):
        """Refresh the models list display."""
        # Clear existing rows
        child = self.models_group.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.models_group.remove(child)
            child = next_child

        # Add model rows
        for model in self.settings.models:
            model_row = Adw.ActionRow()
            model_row.set_title(model.name)
            model_row.set_subtitle(f"{model.type}: {model.model_id}")

            # Delete button
            delete_btn = Gtk.Button()
            delete_btn.set_icon_name("user-trash-symbolic")
            delete_btn.set_valign(Gtk.Align.CENTER)
            delete_btn.add_css_class("flat")
            delete_btn.connect("clicked", self.on_delete_model, model.name)
            model_row.add_suffix(delete_btn)

            self.models_group.add(model_row)

    def build_general_settings_page(self):
        """Build general settings page."""
        general_page = Adw.PreferencesPage()
        general_page.set_title("General")
        general_page.set_icon_name("preferences-system-symbolic")
        self.add(general_page)

        # Model settings
        model_group = Adw.PreferencesGroup()
        model_group.set_title("Default Settings")
        general_page.add(model_group)

        # Default model dropdown
        default_model_row = Adw.ComboRow()
        default_model_row.set_title("Default Model")
        default_model_row.set_subtitle("Model to use when starting a new conversation")

        # Create model list
        model_list = Gtk.StringList()
        selected_idx = 0
        selected_model = self.settings.get("default_model", "")

        for i, model in enumerate(self.settings.models):
            model_list.append(model.name)
            if model.name == selected_model:
                selected_idx = i

        default_model_row.set_model(model_list)
        default_model_row.set_selected(selected_idx)
        default_model_row.connect("notify::selected", self.on_default_model_changed)
        model_group.add(default_model_row)
        self.default_model_row = default_model_row

        # Auto-fetch models
        auto_fetch_row = Adw.SwitchRow()
        auto_fetch_row.set_title("Auto-fetch Models")
        auto_fetch_row.set_subtitle("Automatically fetch available models on startup")
        auto_fetch_row.set_active(self.settings.get("auto_fetch_models", True))
        auto_fetch_row.connect("notify::active", self.on_auto_fetch_changed)
        model_group.add(auto_fetch_row)

        # Window settings
        window_group = Adw.PreferencesGroup()
        window_group.set_title("Window")
        window_group.set_description("Window size and behavior settings")
        general_page.add(window_group)

        # Default window width
        width_row = Adw.SpinRow.new_with_range(400, 2000, 50)
        width_row.set_title("Default Width")
        width_row.set_subtitle("Window width in pixels")
        width_row.set_value(self.settings.get("window_width", 800))
        width_row.connect("changed", self.on_window_width_changed)
        window_group.add(width_row)

        # Default window height
        height_row = Adw.SpinRow.new_with_range(300, 1500, 50)
        height_row.set_title("Default Height")
        height_row.set_subtitle("Window height in pixels")
        height_row.set_value(self.settings.get("window_height", 600))
        height_row.connect("changed", self.on_window_height_changed)
        window_group.add(height_row)

        # Input max height
        input_height_row = Adw.SpinRow.new_with_range(50, 500, 10)
        input_height_row.set_title("Input Max Height")
        input_height_row.set_subtitle("Maximum height of input area in pixels")
        input_height_row.set_value(self.settings.get("input_max_height", 150))
        input_height_row.connect("changed", self.on_input_height_changed)
        window_group.add(input_height_row)

        # History settings
        history_group = Adw.PreferencesGroup()
        history_group.set_title("History")
        history_group.set_description("Conversation history settings")
        general_page.add(history_group)

        # Max history
        max_history_row = Adw.SpinRow.new_with_range(10, 200, 10)
        max_history_row.set_title("Maximum Conversations")
        max_history_row.set_subtitle("Maximum number of conversations to keep")
        max_history_row.set_value(self.settings.get("max_history", 50))
        max_history_row.connect("changed", self.on_max_history_changed)
        history_group.add(max_history_row)

    def build_appearance_page(self):
        """Build appearance settings page."""
        appearance_page = Adw.PreferencesPage()
        appearance_page.set_title("Appearance")
        appearance_page.set_icon_name("applications-graphics-symbolic")
        self.add(appearance_page)

        # UI Font settings
        ui_font_group = Adw.PreferencesGroup()
        ui_font_group.set_title("Interface Font")
        ui_font_group.set_description("Font used in the application interface")
        appearance_page.add(ui_font_group)

        # UI Font
        ui_font_row = Adw.ActionRow()
        ui_font_row.set_title("UI Font")
        ui_font_row.set_subtitle("Font for buttons, menus, and controls")

        self.ui_font_button = Gtk.FontButton()
        current_ui_font = self.settings.get("ui_font_family", "Sans 11")
        self.ui_font_button.set_font(current_ui_font)
        self.ui_font_button.set_use_font(True)
        self.ui_font_button.set_use_size(True)
        self.ui_font_button.set_valign(Gtk.Align.CENTER)
        self.ui_font_button.connect("font-set", self.on_ui_font_changed)
        ui_font_row.add_suffix(self.ui_font_button)

        ui_font_group.add(ui_font_row)

        # Webview Font settings
        webview_font_group = Adw.PreferencesGroup()
        webview_font_group.set_title("Conversation Font")
        webview_font_group.set_description("Font used in the conversation display")
        appearance_page.add(webview_font_group)

        # Webview Font
        webview_font_row = Adw.ActionRow()
        webview_font_row.set_title("Conversation Font")
        webview_font_row.set_subtitle("Font for chat messages and content")

        self.webview_font_button = Gtk.FontButton()
        # Construct font string from family and size
        webview_font_family = self.settings.get("webview_font_family", "Sans")
        webview_font_size = self.settings.get("webview_font_size", 14)
        current_webview_font = f"{webview_font_family} {webview_font_size}"
        self.webview_font_button.set_font(current_webview_font)
        self.webview_font_button.set_use_font(True)
        self.webview_font_button.set_use_size(True)
        self.webview_font_button.set_valign(Gtk.Align.CENTER)
        self.webview_font_button.connect("font-set", self.on_webview_font_changed)
        webview_font_row.add_suffix(self.webview_font_button)

        webview_font_group.add(webview_font_row)

        # Reset buttons
        reset_group = Adw.PreferencesGroup()
        reset_group.set_title("Reset")
        appearance_page.add(reset_group)

        # Reset UI font
        reset_ui_row = Adw.ActionRow()
        reset_ui_row.set_title("Reset Interface Font")
        reset_ui_btn = Gtk.Button(label="Reset")
        reset_ui_btn.set_valign(Gtk.Align.CENTER)
        reset_ui_btn.connect("clicked", self.on_reset_ui_font)
        reset_ui_row.add_suffix(reset_ui_btn)
        reset_group.add(reset_ui_row)

        # Reset webview font
        reset_webview_row = Adw.ActionRow()
        reset_webview_row.set_title("Reset Conversation Font")
        reset_webview_btn = Gtk.Button(label="Reset")
        reset_webview_btn.set_valign(Gtk.Align.CENTER)
        reset_webview_btn.connect("clicked", self.on_reset_webview_font)
        reset_webview_row.add_suffix(reset_webview_btn)
        reset_group.add(reset_webview_row)

    def on_config_changed(self, entry, config_key):
        """Handle configuration change."""
        value = entry.get_text()
        self.settings.set(config_key, value)

        # Trigger model refetch in parent window
        if self.on_settings_changed and config_key in [
            "ollama_endpoint",
            "openai_endpoint",
            "openai_api_key",
            "custom_api_endpoint",
            "custom_api_key",
        ]:
            self.on_settings_changed()

    def on_delete_model(self, button, model_name):
        """Handle model deletion."""
        self.settings.remove_model(model_name)
        self.refresh_models_list()
        self.refresh_default_model_list()

        # Notify parent window
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_default_model_changed(self, combo_row, param):
        """Handle default model selection change."""
        selected_idx = combo_row.get_selected()
        if selected_idx < len(self.settings.models):
            model = self.settings.models[selected_idx]
            self.settings.set("default_model", model.name)

    def on_auto_fetch_changed(self, switch_row, param):
        """Handle auto-fetch models toggle."""
        self.settings.set("auto_fetch_models", switch_row.get_active())

    def on_window_width_changed(self, spin_row):
        """Handle window width change."""
        self.settings.set("window_width", int(spin_row.get_value()))

    def on_window_height_changed(self, spin_row):
        """Handle window height change."""
        self.settings.set("window_height", int(spin_row.get_value()))

    def on_input_height_changed(self, spin_row):
        """Handle input max height change."""
        self.settings.set("input_max_height", int(spin_row.get_value()))
        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_max_history_changed(self, spin_row):
        """Handle max history change."""
        self.settings.set("max_history", int(spin_row.get_value()))

    def refresh_default_model_list(self):
        """Refresh the default model dropdown."""
        if not hasattr(self, "default_model_row"):
            return

        model_list = Gtk.StringList()
        selected_idx = 0
        selected_model = self.settings.get("default_model", "")

        for i, model in enumerate(self.settings.models):
            model_list.append(model.name)
            if model.name == selected_model:
                selected_idx = i

        self.default_model_row.set_model(model_list)
        self.default_model_row.set_selected(selected_idx)

    def on_ui_font_changed(self, font_button):
        """Handle UI font change."""
        font = font_button.get_font()
        self.settings.set("ui_font_family", font)

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_webview_font_changed(self, font_button):
        """Handle webview font change."""
        font = font_button.get_font()
        # Parse font string to extract family and size
        # Font string format: "Family Name Size"
        parts = font.rsplit(" ", 1)
        if len(parts) == 2:
            font_family = parts[0]
            try:
                font_size = int(parts[1])
            except ValueError:
                font_size = 14
        else:
            font_family = font
            font_size = 14

        self.settings.set("webview_font_family", font_family)
        self.settings.set("webview_font_size", font_size)

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_reset_ui_font(self, button):
        """Reset UI font to default."""
        default_font = "Sans 11"
        self.settings.set("ui_font_family", default_font)
        self.ui_font_button.set_font(default_font)

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_reset_webview_font(self, button):
        """Reset webview font to default."""
        default_font = "Sans 14"
        self.settings.set("webview_font_family", "Sans")
        self.settings.set("webview_font_size", 14)
        self.webview_font_button.set_font(default_font)

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def show_error(self, message: str):
        """Show an error dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()
