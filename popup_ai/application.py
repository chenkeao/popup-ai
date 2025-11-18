"""Main GTK application."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")

from gi.repository import Gtk, Adw, Gio, GLib, Gdk
from popup_ai.window import PopupAIWindow
from popup_ai.config import Settings
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


class PopupAIApplication(Adw.Application):
    """Main application class."""

    def __init__(self, initial_text=None, service_mode=False):
        super().__init__(
            application_id=APP_ID,
            flags=(
                Gio.ApplicationFlags.FLAGS_NONE
                if service_mode
                else Gio.ApplicationFlags.HANDLES_COMMAND_LINE
            ),
        )
        self.initial_text = initial_text
        self.window = None
        self.settings = Settings()
        self.service_mode = service_mode
        self._dbus_id = None

        # In service mode, hold the application to prevent auto-exit
        if self.service_mode:
            self.hold()

    def show_window(self, initial_text=""):
        """Show the window, destroying and recreating if necessary."""
        import sys

        print("=== SHOW WINDOW CALLED ===", file=sys.stderr, flush=True)

        # Strategy for Wayland: Destroy and recreate window if it exists
        # This is the most reliable way to restore a minimized window on Wayland
        if self.window is not None:
            print(f"Window exists, destroying it", file=sys.stderr, flush=True)
            # Save the current conversation state before destroying
            old_window = self.window
            if hasattr(old_window, "current_conversation") and old_window.current_conversation:
                if old_window.current_conversation.messages:
                    old_window.settings.save_conversation(old_window.current_conversation)
            # Destroy the old window
            old_window.destroy()
            self.window = None

        # Create new window
        print("Creating new window", file=sys.stderr, flush=True)
        self.window = PopupAIWindow(
            application=self, settings=self.settings, service_mode=self.service_mode
        )
        print(f"Window created: {self.window}", file=sys.stderr, flush=True)

        # Show and present window
        print("Showing and presenting window", file=sys.stderr, flush=True)
        self.window.set_visible(True)
        self.window.present()
        self.window.present_with_time(GLib.get_monotonic_time() // 1000)

        # Set initial text if provided (before focus to avoid race condition)
        if initial_text:
            print(f"Setting initial text: {initial_text}", file=sys.stderr, flush=True)
            self.window.set_initial_text(initial_text)

        # Force focus on input area
        self.window.focus_input()

        print("=== SHOW WINDOW DONE ===", file=sys.stderr, flush=True)

    def _on_dbus_method_call(
        self, connection, sender, object_path, interface_name, method_name, parameters, invocation
    ):
        """Handle D-Bus method calls."""
        if method_name == "ShowWindow":
            initial_text = parameters[0]
            # Show window on main thread
            GLib.idle_add(self.show_window, initial_text)
            # Return immediately
            invocation.return_value(None)
        else:
            invocation.return_error_literal(
                Gio.dbus_error_quark(),
                Gio.DBusError.UNKNOWN_METHOD,
                f"Unknown method: {method_name}",
            )

    def do_activate(self):
        """Called when the application is activated."""
        # In service mode, do nothing on activate - wait for D-Bus calls
        # In normal mode, this would show the window
        if not self.service_mode:
            self.show_window(self.initial_text or "")

    def do_command_line(self, command_line):
        """Handle command line arguments (only in non-service mode)."""
        args = command_line.get_arguments()[1:]  # Skip program name

        # Store initial text from command line (filter out options)
        text_args = [arg for arg in args if not arg.startswith("--")]
        if text_args:
            self.initial_text = " ".join(text_args)

        self.activate()
        return 0

    def do_startup(self):
        """Called when the application starts."""
        Adw.Application.do_startup(self)

        # Set default window icon
        Gtk.Window.set_default_icon_name(APP_ID)

        # Setup actions
        self.setup_actions()

        # Register D-Bus interface in service mode
        if self.service_mode:
            self._register_dbus_interface()

    def _register_dbus_interface(self):
        """Register custom D-Bus interface for the service."""
        import sys

        try:
            # Parse the interface XML
            node_info = Gio.DBusNodeInfo.new_for_xml(DBUS_INTERFACE)
            interface_info = node_info.interfaces[0]

            # Get the session bus connection
            connection = self.get_dbus_connection()
            if not connection:
                print("Failed to get D-Bus connection", file=sys.stderr)
                return

            # Register the interface
            self._dbus_id = connection.register_object(
                "/io/github/chenkeao/PopupAI",
                interface_info,
                self._on_dbus_method_call,
                None,  # get_property
                None,  # set_property
            )

            print(f"D-Bus interface registered with ID: {self._dbus_id}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to register D-Bus interface: {e}", file=sys.stderr)

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
