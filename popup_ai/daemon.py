"""Daemon process management for Popup AI."""

import os
import sys
import time
import signal
import atexit
import fcntl
from pathlib import Path
from typing import Optional


class DaemonManager:
    """Manage background daemon process."""

    def __init__(self, app_id: str = "popup-ai"):
        """Initialize daemon manager.

        Args:
            app_id: Application identifier
        """
        self.app_id = app_id
        self.runtime_dir = Path(os.getenv("XDG_RUNTIME_DIR", f"/tmp/runtime-{os.getuid()}"))
        self.runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        self.pid_file = self.runtime_dir / f"{app_id}.pid"
        self.lock_file = self.runtime_dir / f"{app_id}.lock"
        self.log_file = self.runtime_dir / f"{app_id}.log"

    def is_running(self) -> bool:
        """Check if daemon is running.

        Returns:
            True if daemon is running, False otherwise
        """
        if not self.pid_file.exists():
            return False

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            # Check if process exists
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError, PermissionError):
            # PID file is stale, remove it
            self._cleanup_pid_file()
            return False

    def get_pid(self) -> Optional[int]:
        """Get daemon PID if running.

        Returns:
            PID if daemon is running, None otherwise
        """
        if not self.is_running():
            return None

        try:
            with open(self.pid_file, "r") as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            return None

    def start(self, target_func, *args, **kwargs) -> bool:
        """Start daemon process.

        Args:
            target_func: Function to run in daemon
            *args: Arguments for target function
            **kwargs: Keyword arguments for target function

        Returns:
            True if daemon started successfully, False if already running
        """
        if self.is_running():
            return False

        # Fork first time
        pid = os.fork()
        if pid > 0:
            # Parent process - wait a bit and verify daemon started
            time.sleep(0.5)
            return self.is_running()

        # First child - decouple from parent
        os.setsid()
        os.umask(0)

        # Fork second time
        pid = os.fork()
        if pid > 0:
            # Exit first child
            sys.exit(0)

        # Second child - this is the daemon
        self._setup_daemon()

        # Write PID file
        with open(self.pid_file, "w") as f:
            f.write(str(os.getpid()))

        # Register cleanup
        atexit.register(self._cleanup_pid_file)

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()

        # Redirect stdin to /dev/null
        devnull = open(os.devnull, "r")
        os.dup2(devnull.fileno(), sys.stdin.fileno())

        # Redirect stdout and stderr to log file
        log_fd = open(self.log_file, "a")
        os.dup2(log_fd.fileno(), sys.stdout.fileno())
        os.dup2(log_fd.fileno(), sys.stderr.fileno())

        # Run the target function
        try:
            target_func(*args, **kwargs)
        except Exception as e:
            print(f"Daemon error: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            self._cleanup_pid_file()

    def stop(self, timeout: int = 5) -> bool:
        """Stop daemon process.

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if daemon stopped, False if not running
        """
        pid = self.get_pid()
        if pid is None:
            return False

        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)

            # Wait for process to exit
            for _ in range(timeout * 10):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    # Process has exited
                    self._cleanup_pid_file()
                    return True

            # Process still running, force kill
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.2)
            self._cleanup_pid_file()
            return True

        except ProcessLookupError:
            # Process already dead
            self._cleanup_pid_file()
            return True
        except PermissionError:
            print(f"Permission denied to stop daemon (PID {pid})", file=sys.stderr)
            return False

    def restart(self, target_func, *args, **kwargs) -> bool:
        """Restart daemon process.

        Args:
            target_func: Function to run in daemon
            *args: Arguments for target function
            **kwargs: Keyword arguments for target function

        Returns:
            True if daemon restarted successfully
        """
        self.stop()
        time.sleep(0.5)
        return self.start(target_func, *args, **kwargs)

    def _setup_daemon(self):
        """Setup daemon environment."""
        # Change to root directory to avoid keeping any directory in use
        os.chdir("/")

    def _cleanup_pid_file(self):
        """Remove PID file."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass

    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        self._cleanup_pid_file()
        sys.exit(0)


class FileLock:
    """Simple file-based lock for IPC."""

    def __init__(self, lock_file: Path):
        """Initialize file lock.

        Args:
            lock_file: Path to lock file
        """
        self.lock_file = lock_file
        self.fd = None

    def acquire(self, timeout: float = 0) -> bool:
        """Acquire lock.

        Args:
            timeout: Seconds to wait for lock (0 = non-blocking)

        Returns:
            True if lock acquired, False otherwise
        """
        try:
            self.fd = open(self.lock_file, "w")

            if timeout == 0:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                end_time = time.time() + timeout
                while True:
                    try:
                        fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except BlockingIOError:
                        if time.time() >= end_time:
                            return False
                        time.sleep(0.1)

            return True
        except (OSError, IOError):
            return False

    def release(self):
        """Release lock."""
        if self.fd:
            try:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass
            finally:
                self.fd = None

    def __enter__(self):
        """Context manager entry."""
        self.acquire(timeout=5)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
