"""Main GTK application."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Adw, Gio, GLib, Gdk
from popup_ai.window import PopupAIWindow
from popup_ai.config import Settings
from popup_ai.logger import setup_logging, get_logger
from popup_ai.constants import (
    APP_ID,
    APP_NAME,
    APP_VERSION,
    DEVELOPER_NAME,
    WEBSITE,
    ISSUE_URL,
    SHORTCUT_QUIT,
    SHORTCUT_PREFERENCES,
)

# D-Bus interface XML for our custom methods
DBUS_INTERFACE = """
<node>
    <interface name="io.github.chenkeao.PopupAI">
        <method name="ShowWindow">
            <arg type="s" name="initial_text" direction="in"/>
        </method>
    </interface>
</node>
"""

# Initialize logger
logger = get_logger(__name__)


class PopupAIApplication(Adw.Application):
    """Main application class."""

    def __init__(self, initial_text=None):
        # Use DEFAULT_FLAGS which enables single-instance by default
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        # Setup logging first
        setup_logging()
        logger.info(f"Initializing {APP_NAME} v{APP_VERSION}")

        self.initial_text = initial_text
        self.window = None
        self.settings = Settings()
        self._dbus_id = None

        # Connect to activate signal
        self.connect("activate", self.on_activate)

    def show_window(self, initial_text=""):
        """Show the window, restoring or creating as needed."""
        if self.window is not None:
            try:
                if self.window.get_surface() is None:
                    self.window = None
                else:
                    self.window.unminimize()
                    self.window.preset()
                    # self.window.present_with_time(GLib.get_monotonic_time() // 1000)

                    if initial_text:
                        self.window.set_initial_text(initial_text)

                    self.window.focus_input()
                    return
            except Exception:
                old_window = self.window
                if (
                    hasattr(old_window, "current_conversation")
                    and old_window is not None
                    and old_window.current_conversation
                ):
                    if old_window.current_conversation.messages:
                        old_window.settings.save_conversation(old_window.current_conversation)

                try:
                    old_window.destroy() if old_window is not None else None
                except Exception:
                    pass
                self.window = None

        self.window = PopupAIWindow(application=self, settings=self.settings)
        self.window.connect("destroy", self._on_window_destroyed)

        self.window.set_visible(True)
        self.window.present()
        self.window.present_with_time(GLib.get_monotonic_time() // 1000)

        if initial_text:
            self.window.set_initial_text(initial_text)

        self.window.focus_input()

    def _on_window_destroyed(self, window):
        """Handle window destruction."""
        self.window = None

    def on_activate(self, app):
        """Called when the application is activated."""
        # Show window with initial text
        self.show_window(self.initial_text or "")

    def _on_dbus_method_call(
        self, connection, sender, object_path, interface_name, method_name, parameters, invocation
    ):
        """Handle D-Bus method calls."""
        if method_name == "ShowWindow":
            initial_text = parameters[0]
            # Update the window with new text
            GLib.idle_add(self.show_window, initial_text)
            invocation.return_value(None)
        else:
            invocation.return_error_literal(
                Gio.dbus_error_quark(),
                Gio.DBusError.UNKNOWN_METHOD,
                f"Unknown method: {method_name}",
            )

    def do_startup(self):
        """Called when the application starts."""
        Adw.Application.do_startup(self)
        Gtk.Window.set_default_icon_name(APP_ID)
        self.setup_actions()

        # Register custom D-Bus interface
        self._register_dbus_interface()

    def _register_dbus_interface(self):
        """Register custom D-Bus interface for receiving ShowWindow calls."""
        try:
            node_info = Gio.DBusNodeInfo.new_for_xml(DBUS_INTERFACE)
            interface_info = node_info.interfaces[0]
            connection = self.get_dbus_connection()
            if connection:
                self._dbus_id = connection.register_object(
                    "/io/github/chenkeao/PopupAI",
                    interface_info,
                    self._on_dbus_method_call,
                    None,
                    None,
                )
        except Exception as e:
            logger.error(f"Failed to register D-Bus interface: {e}")

    def setup_actions(self):
        """Setup application actions."""
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", [SHORTCUT_QUIT])

        # Preferences action
        prefs_action = Gio.SimpleAction.new("preferences", None)
        prefs_action.connect("activate", self.on_preferences)
        self.add_action(prefs_action)
        self.set_accels_for_action("app.preferences", [SHORTCUT_PREFERENCES])

        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)

    def on_preferences(self, action, param):
        """Show preferences dialog."""
        if self.window:
            self.window.show_preferences()

    def on_about(self, action, param):
        """Show about dialog."""
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name=APP_NAME,
            application_icon=APP_ID,
            developer_name=DEVELOPER_NAME,
            version=APP_VERSION,
            website=WEBSITE,
            issue_url=ISSUE_URL,
            license_type=Gtk.License.GPL_3_0,
            copyright=f"© 2025 {DEVELOPER_NAME}",
        )
        about.present()
