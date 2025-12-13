"""Main entry point for popup-ai application."""

import sys
import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib
from popup_ai.application import PopupAIApplication


def is_app_running():
    """Check if app is already running via D-Bus."""
    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            connection,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            None,
        )
        names = proxy.call_sync(
            "ListNames",
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        return "io.github.chenkeao.PopupAI" in names[0]
    except Exception:
        return False


def send_show_window(text):
    """Send ShowWindow message to running instance."""
    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        message = Gio.DBusMessage.new_method_call(
            "io.github.chenkeao.PopupAI",
            "/io/github/chenkeao/PopupAI",
            "io.github.chenkeao.PopupAI",
            "ShowWindow",
        )
        message.set_body(GLib.Variant("(s)", (text,)))
        connection.send_message(message, Gio.DBusSendMessageFlags.NONE)
        connection.flush_sync(None)
        return True
    except Exception as e:
        print(f"Failed to send message: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Handle daemon control commands
    if len(args) > 0:
        if args[0] == "--status":
            if is_app_running():
                print("Application is running")
                return 0
            else:
                print("Application is not running")
                return 1
        elif args[0] == "--start":
            if is_app_running():
                print("Application is already running")
                return 0
            # Fall through to start the app
        elif args[0] == "--stop":
            if not is_app_running():
                print("Application is not running")
                return 0
            try:
                connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                # Call the quit action via org.gtk.Actions
                message = Gio.DBusMessage.new_method_call(
                    "io.github.chenkeao.PopupAI",
                    "/io/github/chenkeao/PopupAI",
                    "org.gtk.Actions",
                    "Activate",
                )
                # Parameters: action_name, parameter array, platform_data
                message.set_body(GLib.Variant("(sava{sv})", ("quit", [], {})))
                connection.send_message(message, Gio.DBusSendMessageFlags.NONE)
                connection.flush_sync(None)

                # Wait for app to actually quit
                import time

                for _ in range(20):  # Wait up to 2 seconds
                    time.sleep(0.1)
                    if not is_app_running():
                        break

                print("Application stopped")
                return 0
            except Exception as e:
                print(f"Failed to stop application: {e}")
                return 1
        elif args[0] == "--restart":
            # Stop if running
            if is_app_running():
                try:
                    connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                    # Call the quit action via org.gtk.Actions
                    message = Gio.DBusMessage.new_method_call(
                        "io.github.chenkeao.PopupAI",
                        "/io/github/chenkeao/PopupAI",
                        "org.gtk.Actions",
                        "Activate",
                    )
                    message.set_body(GLib.Variant("(sava{sv})", ("quit", [], {})))
                    connection.send_message(message, Gio.DBusSendMessageFlags.NONE)
                    connection.flush_sync(None)
                    import time

                    time.sleep(0.5)
                except Exception:
                    pass
            # Fall through to start the app

    # Extract text arguments (non-option args)
    text_args = [arg for arg in args if not arg.startswith("--")]
    initial_text = " ".join(text_args) if text_args else ""

    # If app is already running, send message and exit immediately
    if is_app_running():
        if initial_text or not args:  # Send message if there's text or no args (just activate)
            send_show_window(initial_text)
        return 0

    # App is not running - start it in background using subprocess
    import subprocess

    # Start a new detached process
    subprocess.Popen(
        [sys.executable, "-m", "popup_ai.main", "--background-start"]
        + ([initial_text] if initial_text else []),
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return 0


if __name__ == "__main__":
    # Special internal flag to actually run the app (used by subprocess)
    if len(sys.argv) > 1 and sys.argv[1] == "--background-start":
        # Remove the flag and get the initial text
        text_args = [arg for arg in sys.argv[2:] if not arg.startswith("--")]
        initial_text = " ".join(text_args) if text_args else ""
        app = PopupAIApplication(initial_text=initial_text)
        sys.exit(app.run(None))
    else:
        sys.exit(main())
