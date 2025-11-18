"""Main entry point for popup-ai application."""

import sys
import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib


def main():
    """Main entry point."""
    # Check if running as service
    if "--service" in sys.argv:
        # Run as background service
        from popup_ai.application import PopupAIApplication

        sys.argv = [arg for arg in sys.argv if arg != "--service"]
        app = PopupAIApplication(service_mode=True)
        return app.run(sys.argv)

    # Client mode: send D-Bus notification and exit immediately
    app_id = "io.github.chenkeao.PopupAI"

    try:
        # Connect to session bus
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)

        # Check if service is running by introspecting the bus name
        try:
            result = connection.call_sync(
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                "GetNameOwner",
                GLib.Variant("(s)", (app_id,)),
                GLib.VariantType("(s)"),
                Gio.DBusCallFlags.NONE,
                1000,  # 1 second timeout
                None,
            )
        except GLib.Error as e:
            print(
                f"✗ Background service is not running. Please start it with: systemctl --user start popup-ai.service",
                file=sys.stderr,
            )
            return 1

        # Get command line arguments (skip program name)
        args = sys.argv[1:]
        initial_text = " ".join(args) if args else ""

        # Call our custom ShowWindow method with initial text
        connection.call_sync(
            app_id,
            "/io/github/chenkeao/PopupAI",
            "io.github.chenkeao.PopupAI",
            "ShowWindow",
            GLib.Variant("(s)", (initial_text,)),
            None,  # No return value expected
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

        return 0
    except GLib.Error as e:
        print(f"✗ Failed to communicate with background service: {e.message}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
