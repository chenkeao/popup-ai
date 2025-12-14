"""Preferences window for managing settings."""

from typing import Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw

from src.config import Settings, ModelConfig, PromptTemplate
from src.logger import get_logger
from src.ui_strings import (
    DIALOG_DELETE_PROMPT_TITLE,
    DIALOG_DELETE_PROMPT_BODY,
    ERROR_NO_NAME,
    ERROR_NO_SYSTEM_PROMPT,
    ERROR_NAME_EXISTS,
    NEW_PROMPT_TITLE,
    EDIT_PROMPT_TITLE,
    LABEL_NAME,
    LABEL_DESCRIPTION,
    LABEL_SYSTEM_PROMPT,
    LABEL_DEFAULT_MODEL,
    BTN_SAVE,
    BTN_CANCEL,
    PLACEHOLDER_PROMPT_NAME,
    PLACEHOLDER_DESCRIPTION,
)
from src.constants import (
    MARGIN_MEDIUM,
    MARGIN_LARGE,
    SPACING_SMALL,
    SPACING_MEDIUM,
)

# Configure logging
logger = get_logger(__name__)


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

        # Prompts page
        self.build_prompts_page()

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

        # Perplexity settings
        perplexity_group = Adw.PreferencesGroup()
        perplexity_group.set_title("Perplexity AI")
        perplexity_group.set_description("Perplexity AI API configuration")
        api_page.add(perplexity_group)

        # Perplexity endpoint
        self.perplexity_endpoint_row = Adw.EntryRow()
        self.perplexity_endpoint_row.set_title("Endpoint")
        self.perplexity_endpoint_row.set_text(
            self.settings.get("perplexity_endpoint", "https://api.perplexity.ai")
        )
        self.perplexity_endpoint_row.connect(
            "changed", self.on_config_changed, "perplexity_endpoint"
        )
        perplexity_group.add(self.perplexity_endpoint_row)

        # Perplexity API key
        self.perplexity_api_key_row = Adw.PasswordEntryRow()
        self.perplexity_api_key_row.set_title("API Key")
        self.perplexity_api_key_row.set_text(self.settings.get("perplexity_api_key", ""))
        self.perplexity_api_key_row.connect("changed", self.on_config_changed, "perplexity_api_key")
        perplexity_group.add(self.perplexity_api_key_row)

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
        webview_font_group.set_description(
            "Fonts used in the conversation display (with fallback support)"
        )
        appearance_page.add(webview_font_group)

        # Font size setting
        self.webview_font_size_row = Adw.SpinRow()
        self.webview_font_size_row.set_title("Font Size")
        self.webview_font_size_row.set_subtitle("Base font size for conversation text")
        adjustment = Gtk.Adjustment(
            value=self.settings.get("webview_font_size", 14),
            lower=8,
            upper=32,
            step_increment=1,
            page_increment=2,
            page_size=0,
        )
        self.webview_font_size_row.set_adjustment(adjustment)
        self.webview_font_size_row.connect("changed", self.on_webview_font_size_changed)
        webview_font_group.add(self.webview_font_size_row)

        # Font families list
        self.webview_fonts_group = Adw.PreferencesGroup()
        self.webview_fonts_group.set_title("Font Families (Priority Order)")
        self.webview_fonts_group.set_description(
            "Fonts are used in order. If the first font is unavailable, the next one is used."
        )
        appearance_page.add(self.webview_fonts_group)

        # Add font button
        add_font_row = Adw.ActionRow()
        add_font_row.set_title("Add Font")
        add_font_btn = Gtk.Button()
        add_font_btn.set_icon_name("list-add-symbolic")
        add_font_btn.set_valign(Gtk.Align.CENTER)
        add_font_btn.add_css_class("flat")
        add_font_btn.connect("clicked", self.on_add_webview_font)
        add_font_row.add_suffix(add_font_btn)
        self.webview_fonts_group.add(add_font_row)

        # Track font rows
        self.webview_font_rows = []
        self.refresh_webview_fonts_list()

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
            "perplexity_endpoint",
            "perplexity_api_key",
            "custom_api_endpoint",
            "custom_api_key",
        ]:
            self.on_settings_changed()

    def on_delete_model(self, button, model_name):
        """Handle model deletion."""
        self.settings.remove_model(model_name)
        self.refresh_models_list()

        # Notify parent window
        if self.on_settings_changed:
            self.on_settings_changed()

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

    def build_prompts_page(self):
        """Build prompts management page."""
        prompts_page = Adw.PreferencesPage()
        prompts_page.set_title("Prompts")
        prompts_page.set_icon_name("text-x-generic-symbolic")
        self.add(prompts_page)

        self.prompts_group = Adw.PreferencesGroup()
        self.prompts_group.set_title("Prompt Templates")
        self.prompts_group.set_description("Manage your custom prompt templates")
        prompts_page.add(self.prompts_group)

        # Add new prompt button
        add_prompt_row = Adw.ActionRow()
        add_prompt_row.set_title("Add New Prompt")
        add_btn = Gtk.Button()
        add_btn.set_icon_name("list-add-symbolic")
        add_btn.set_valign(Gtk.Align.CENTER)
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self.on_add_prompt)
        add_prompt_row.add_suffix(add_btn)
        self.prompts_group.add(add_prompt_row)

        # Dictionary to track prompt rows
        self.prompt_rows = {}

        self.refresh_prompts_list()

    def refresh_prompts_list(self):
        """Refresh the prompts list display."""
        current_prompts = {p.name: p for p in self.settings.prompts}
        existing_names = set(self.prompt_rows.keys())
        new_names = set(current_prompts.keys())

        # Remove deleted prompts
        for name in existing_names - new_names:
            row = self.prompt_rows.pop(name)
            self.prompts_group.remove(row)

        # Add or update prompts
        for prompt in self.settings.prompts:
            if prompt.name in self.prompt_rows:
                # Update existing row
                row = self.prompt_rows[prompt.name]
                row.set_title(prompt.name)

                # Update subtitle
                subtitle_parts = []
                if prompt.description:
                    subtitle_parts.append(prompt.description)
                if prompt.default_model:
                    subtitle_parts.append(f"Default model: {prompt.default_model}")
                row.set_subtitle(" | ".join(subtitle_parts) if subtitle_parts else "")
            else:
                # Create new row
                row = self._create_prompt_row(prompt)
                self.prompt_rows[prompt.name] = row
                self.prompts_group.add(row)

    def _create_prompt_row(self, prompt):
        """Create a new prompt row widget."""
        prompt_row = Adw.ActionRow()
        prompt_row.set_title(prompt.name)

        # Create subtitle with description and default model
        subtitle_parts = []
        if prompt.description:
            subtitle_parts.append(prompt.description)
        if prompt.default_model:
            subtitle_parts.append(f"Default model: {prompt.default_model}")
        if subtitle_parts:
            prompt_row.set_subtitle(" | ".join(subtitle_parts))

        # Edit button
        edit_btn = Gtk.Button()
        edit_btn.set_icon_name("document-edit-symbolic")
        edit_btn.set_valign(Gtk.Align.CENTER)
        edit_btn.add_css_class("flat")
        edit_btn.set_tooltip_text("Edit Prompt")
        edit_btn.connect("clicked", self.on_edit_prompt, prompt.name)
        prompt_row.add_suffix(edit_btn)

        # Delete button
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.set_valign(Gtk.Align.CENTER)
        delete_btn.add_css_class("flat")
        delete_btn.set_tooltip_text("Delete Prompt")
        delete_btn.connect("clicked", self.on_delete_prompt, prompt.name)
        prompt_row.add_suffix(delete_btn)

        return prompt_row

    def on_add_prompt(self, button):
        """Handle add new prompt."""

        def on_save():
            self.refresh_prompts_list()
            if self.on_settings_changed:
                self.on_settings_changed()

        dialog = PromptEditDialog(self, self.settings, None, on_save_callback=on_save)
        dialog.present()

    def on_edit_prompt(self, button, prompt_name):
        """Handle edit prompt."""
        prompt = self.settings.get_prompt(prompt_name)
        if prompt:

            def on_save():
                self.refresh_prompts_list()
                if self.on_settings_changed:
                    self.on_settings_changed()

            dialog = PromptEditDialog(self, self.settings, prompt, on_save_callback=on_save)
            dialog.present()

    def on_delete_prompt(self, button, prompt_name):
        """Handle delete prompt."""
        # Show confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(DIALOG_DELETE_PROMPT_TITLE)
        dialog.set_body(DIALOG_DELETE_PROMPT_BODY.format(name=prompt_name))
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("delete", "Delete")
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def on_response(dlg, response):
            if response == "delete":
                self.settings.remove_prompt(prompt_name)
                self.refresh_prompts_list()
                # Notify parent to update UI
                if self.on_settings_changed:
                    self.on_settings_changed()

        dialog.connect("response", on_response)
        dialog.present()

    def on_ui_font_changed(self, font_button):
        """Handle UI font change."""
        font = font_button.get_font()
        self.settings.set("ui_font_family", font)

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_webview_font_size_changed(self, spin_row):
        """Handle webview font size change."""
        font_size = int(spin_row.get_value())
        self.settings.set("webview_font_size", font_size)

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def refresh_webview_fonts_list(self):
        """Refresh the webview fonts list display."""
        # Clear existing font rows (except the add button)
        for row in self.webview_font_rows:
            self.webview_fonts_group.remove(row)
        self.webview_font_rows.clear()

        # Get current font families
        font_families = self.settings.get("webview_font_families", ["Sans"])
        if not isinstance(font_families, list):
            font_families = [str(font_families)]

        # Add font rows
        for idx, font_family in enumerate(font_families):
            font_row = self._create_webview_font_row(font_family, idx, len(font_families))
            self.webview_font_rows.append(font_row)
            self.webview_fonts_group.add(font_row)

    def _create_webview_font_row(self, font_family: str, index: int, total: int):
        """Create a font row widget."""
        font_row = Adw.ActionRow()
        font_row.set_title(font_family)
        if index == 0:
            font_row.set_subtitle("Primary font")
        else:
            font_row.set_subtitle(f"Fallback {index}")

        # Button box for controls
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        button_box.set_valign(Gtk.Align.CENTER)

        # Move up button
        if index > 0:
            up_btn = Gtk.Button()
            up_btn.set_icon_name("go-up-symbolic")
            up_btn.add_css_class("flat")
            up_btn.set_tooltip_text("Move Up")
            up_btn.connect("clicked", self.on_move_font_up, index)
            button_box.append(up_btn)

        # Move down button
        if index < total - 1:
            down_btn = Gtk.Button()
            down_btn.set_icon_name("go-down-symbolic")
            down_btn.add_css_class("flat")
            down_btn.set_tooltip_text("Move Down")
            down_btn.connect("clicked", self.on_move_font_down, index)
            button_box.append(down_btn)

        # Delete button
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.add_css_class("flat")
        delete_btn.set_tooltip_text("Remove Font")
        delete_btn.connect("clicked", self.on_remove_webview_font, index)
        button_box.append(delete_btn)

        font_row.add_suffix(button_box)
        return font_row

    def on_add_webview_font(self, button):
        """Handle adding a new webview font."""
        dialog = Gtk.FontChooserDialog(title="Select Font", transient_for=self)
        dialog.set_modal(True)

        def on_response(dialog, response):
            if response == Gtk.ResponseType.OK:
                font_description = dialog.get_font_desc()
                if font_description:
                    font_family = font_description.get_family()

                    # Get current fonts
                    font_families = self.settings.get("webview_font_families", ["Sans"])
                    if not isinstance(font_families, list):
                        font_families = [str(font_families)]

                    # Add new font if not already in list
                    if font_family not in font_families:
                        font_families.append(font_family)
                        self.settings.set("webview_font_families", font_families)
                        self.refresh_webview_fonts_list()

                        # Notify parent to update UI
                        if self.on_settings_changed:
                            self.on_settings_changed()
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.show()

    def on_remove_webview_font(self, button, index: int):
        """Handle removing a webview font."""
        font_families = self.settings.get("webview_font_families", ["Sans"])
        if not isinstance(font_families, list):
            font_families = [str(font_families)]

        # Don't allow removing the last font
        if len(font_families) <= 1:
            self.show_error("At least one font must be configured")
            return

        # Remove font at index
        if 0 <= index < len(font_families):
            font_families.pop(index)
            self.settings.set("webview_font_families", font_families)
            self.refresh_webview_fonts_list()

            # Notify parent to update UI
            if self.on_settings_changed:
                self.on_settings_changed()

    def on_move_font_up(self, button, index: int):
        """Handle moving a font up in priority."""
        if index <= 0:
            return

        font_families = self.settings.get("webview_font_families", ["Sans"])
        if not isinstance(font_families, list):
            font_families = [str(font_families)]

        # Swap with previous
        font_families[index], font_families[index - 1] = (
            font_families[index - 1],
            font_families[index],
        )
        self.settings.set("webview_font_families", font_families)
        self.refresh_webview_fonts_list()

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_move_font_down(self, button, index: int):
        """Handle moving a font down in priority."""
        font_families = self.settings.get("webview_font_families", ["Sans"])
        if not isinstance(font_families, list):
            font_families = [str(font_families)]

        if index >= len(font_families) - 1:
            return

        # Swap with next
        font_families[index], font_families[index + 1] = (
            font_families[index + 1],
            font_families[index],
        )
        self.settings.set("webview_font_families", font_families)
        self.refresh_webview_fonts_list()

        # Notify parent to update UI
        if self.on_settings_changed:
            self.on_settings_changed()

    def on_webview_font_changed(self, font_button):
        """Handle webview font change (legacy method for migration)."""
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

        self.settings.set("webview_font_families", [font_family])
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
        self.settings.set("webview_font_families", ["Sans"])
        self.settings.set("webview_font_size", 14)
        self.webview_font_size_row.set_value(14)
        self.refresh_webview_fonts_list()

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


class PromptEditDialog(Adw.Window):
    """Dialog for editing or creating prompts."""

    def __init__(
        self,
        parent,
        settings: Settings,
        prompt: Optional[PromptTemplate] = None,
        on_save_callback=None,
    ):
        super().__init__(transient_for=parent, modal=True)

        self.settings = settings
        self.prompt = prompt
        self.is_edit = prompt is not None
        self.on_save_callback = on_save_callback

        self.set_title(EDIT_PROMPT_TITLE if self.is_edit else NEW_PROMPT_TITLE)
        self.set_default_size(500, 550)

        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Cancel button
        cancel_btn = Gtk.Button(label=BTN_CANCEL)
        cancel_btn.connect("clicked", self.on_cancel)
        header.pack_start(cancel_btn)

        # Save button
        save_btn = Gtk.Button(label=BTN_SAVE)
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self.on_save)
        header.pack_end(save_btn)

        # Scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        main_box.append(scrolled)

        # Content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_start(MARGIN_LARGE)
        content_box.set_margin_end(MARGIN_LARGE)
        content_box.set_margin_top(MARGIN_LARGE)
        content_box.set_margin_bottom(MARGIN_LARGE)
        content_box.set_spacing(SPACING_MEDIUM)
        scrolled.set_child(content_box)

        # Name entry
        name_label = Gtk.Label(label=LABEL_NAME)
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("heading")
        content_box.append(name_label)

        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text(PLACEHOLDER_PROMPT_NAME)
        if prompt:
            self.name_entry.set_text(prompt.name)
        content_box.append(self.name_entry)

        # Description entry
        desc_label = Gtk.Label(label=LABEL_DESCRIPTION)
        desc_label.set_halign(Gtk.Align.START)
        desc_label.add_css_class("heading")
        desc_label.set_margin_top(MARGIN_MEDIUM)
        content_box.append(desc_label)

        self.desc_entry = Gtk.Entry()
        self.desc_entry.set_placeholder_text(PLACEHOLDER_DESCRIPTION)
        if prompt and prompt.description:
            self.desc_entry.set_text(prompt.description)
        content_box.append(self.desc_entry)

        # Default model dropdown
        model_label = Gtk.Label(label=LABEL_DEFAULT_MODEL)
        model_label.set_halign(Gtk.Align.START)
        model_label.add_css_class("heading")
        model_label.set_margin_top(MARGIN_MEDIUM)
        content_box.append(model_label)

        model_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        model_box.set_spacing(SPACING_SMALL)
        content_box.append(model_box)

        self.model_dropdown = Gtk.DropDown()
        self.model_dropdown.set_hexpand(True)

        # Create model list with "None" option
        model_list = Gtk.StringList()
        model_list.append("(None)")

        selected_idx = 0
        if prompt and prompt.default_model:
            for i, model in enumerate(settings.models):
                model_list.append(model.name)
                if model.name == prompt.default_model:
                    selected_idx = i + 1  # +1 because of "(None)" option
        else:
            for model in settings.models:
                model_list.append(model.name)

        self.model_dropdown.set_model(model_list)
        self.model_dropdown.set_selected(selected_idx)
        model_box.append(self.model_dropdown)

        # System prompt
        prompt_label = Gtk.Label(label=LABEL_SYSTEM_PROMPT)
        prompt_label.set_halign(Gtk.Align.START)
        prompt_label.add_css_class("heading")
        prompt_label.set_margin_top(MARGIN_MEDIUM)
        content_box.append(prompt_label)

        # Text view for system prompt
        prompt_scroll = Gtk.ScrolledWindow()
        prompt_scroll.set_min_content_height(200)
        prompt_scroll.set_vexpand(True)
        content_box.append(prompt_scroll)

        self.prompt_text = Gtk.TextView()
        self.prompt_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.prompt_text.add_css_class("card")
        self.prompt_text.set_left_margin(MARGIN_MEDIUM)
        self.prompt_text.set_right_margin(MARGIN_MEDIUM)
        self.prompt_text.set_top_margin(MARGIN_MEDIUM)
        self.prompt_text.set_bottom_margin(MARGIN_MEDIUM)
        if prompt:
            self.prompt_text.get_buffer().set_text(prompt.system_prompt)
        prompt_scroll.set_child(self.prompt_text)

    def on_cancel(self, button):
        """Handle cancel button."""
        self.close()

    def on_save(self, button):
        """Handle save button."""
        name = self.name_entry.get_text().strip()
        if not name:
            self.show_error(ERROR_NO_NAME)
            return

        # Check if name already exists (and it's not the current prompt being edited)
        if self.prompt is None or name != self.prompt.name:
            if self.settings.get_prompt(name):
                self.show_error(ERROR_NAME_EXISTS.format(name=name))
                return

        buffer = self.prompt_text.get_buffer()
        system_prompt = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(), False
        ).strip()

        if not system_prompt:
            self.show_error(ERROR_NO_SYSTEM_PROMPT)
            return

        description = self.desc_entry.get_text().strip()
        if not description:
            description = None

        # Get selected model
        selected_idx = self.model_dropdown.get_selected()
        default_model = None
        if selected_idx > 0:  # 0 is "(None)"
            default_model = self.settings.models[selected_idx - 1].name

        # Create or update prompt
        new_prompt = PromptTemplate(
            name=name,
            system_prompt=system_prompt,
            description=description,
            default_model=default_model,
        )

        # If editing and name changed, remove old prompt
        if self.prompt is not None and name != self.prompt.name:
            self.settings.remove_prompt(self.prompt.name)

        self.settings.add_prompt(new_prompt)

        # Call callback if provided
        if self.on_save_callback:
            self.on_save_callback()

        self.close()

    def show_error(self, message: str):
        """Show an error dialog."""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.present()
