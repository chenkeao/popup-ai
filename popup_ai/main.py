"""Main entry point for popup-ai application."""

import sys
import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib
from popup_ai.daemon import DaemonManager


def run_daemon():
    """Run the application as a daemon service."""
    import os

    # Force Wayland backend for layer-shell support
    os.environ["GDK_BACKEND"] = "wayland"

    from popup_ai.application import PopupAIApplication

    app = PopupAIApplication(service_mode=True)
    return app.run([])


def main():
    """Main entry point."""
    daemon = DaemonManager(app_id="popup-ai")

    # Handle daemon control commands
    if len(sys.argv) > 1 and sys.argv[1] in ["--daemon", "--start-daemon", "start"]:
        if daemon.is_running():
            print("Daemon is already running", file=sys.stderr)
            return 0

        print("Starting daemon...", file=sys.stderr)
        if daemon.start(run_daemon):
            print("Daemon started successfully", file=sys.stderr)
            return 0
        else:
            print("Failed to start daemon", file=sys.stderr)
            return 1

    elif len(sys.argv) > 1 and sys.argv[1] in ["--stop-daemon", "stop"]:
        if not daemon.is_running():
            print("Daemon is not running", file=sys.stderr)
            return 0

        print("Stopping daemon...", file=sys.stderr)
        if daemon.stop():
            print("Daemon stopped successfully", file=sys.stderr)
            return 0
        else:
            print("Failed to stop daemon", file=sys.stderr)
            return 1

    elif len(sys.argv) > 1 and sys.argv[1] in ["--restart-daemon", "restart"]:
        print("Restarting daemon...", file=sys.stderr)
        if daemon.restart(run_daemon):
            print("Daemon restarted successfully", file=sys.stderr)
            return 0
        else:
            print("Failed to restart daemon", file=sys.stderr)
            return 1

    elif len(sys.argv) > 1 and sys.argv[1] in ["--status", "status"]:
        if daemon.is_running():
            pid = daemon.get_pid()
            print(f"Daemon is running (PID: {pid})", file=sys.stderr)
            return 0
        else:
            print("Daemon is not running", file=sys.stderr)
            return 1

    # Check if running as service (for backward compatibility)
    if "--service" in sys.argv:
        return run_daemon()

    # Client mode: send D-Bus notification to daemon
    app_id = "io.github.chenkeao.PopupAI"

    # Ensure daemon is running
    if not daemon.is_running():
        # Start daemon in background, don't wait
        daemon.start(run_daemon)
        # Exit immediately after starting daemon
        # The daemon will handle the window creation
        return 0

    try:
        # Connect to session bus
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)

        # Get command line arguments (skip program name and daemon control commands)
        args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
        initial_text = " ".join(args) if args else ""

        # Send D-Bus message asynchronously (fire and forget)
        message = Gio.DBusMessage.new_method_call(
            app_id, "/io/github/chenkeao/PopupAI", "io.github.chenkeao.PopupAI", "ShowWindow"
        )
        message.set_body(GLib.Variant("(s)", (initial_text,)))

        # Send the message without waiting for reply
        connection.send_message(message, Gio.DBusSendMessageFlags.NONE)

        # Flush to ensure message is sent immediately
        connection.flush_sync(None)

        return 0
    except Exception:
        # If D-Bus connection fails, daemon might not be ready
        return 0


if __name__ == "__main__":
    sys.exit(main())
