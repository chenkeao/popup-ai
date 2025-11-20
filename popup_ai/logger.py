"""Centralized logging configuration for Popup AI."""

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


class PopupAILogger:
    """Centralized logger for Popup AI application."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logger singleton."""
        if self._initialized:
            return

        self.runtime_dir = Path(os.getenv("XDG_RUNTIME_DIR", f"/tmp/runtime-{os.getuid()}"))
        self.runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Log files
        self.log_file = self.runtime_dir / "popup-ai.log"
        self.ai_log_file = self.runtime_dir / "popup-ai-requests.log"

        # Setup loggers
        self._setup_main_logger()
        self._setup_ai_logger()

        self._initialized = True

    def _setup_main_logger(self):
        """Setup main application logger."""
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Console handler (INFO level)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)

        # File handler (DEBUG level) with rotation
        file_handler = RotatingFileHandler(
            self.log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"  # 5 MB
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    def _setup_ai_logger(self):
        """Setup AI request/response logger."""
        self.ai_logger = logging.getLogger("popup_ai.ai_requests")
        self.ai_logger.setLevel(logging.DEBUG)
        self.ai_logger.propagate = False  # Don't propagate to root logger

        # AI request file handler with rotation
        ai_handler = RotatingFileHandler(
            self.ai_log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10 MB
        )
        ai_handler.setLevel(logging.DEBUG)
        ai_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        ai_handler.setFormatter(ai_formatter)

        self.ai_logger.addHandler(ai_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance.

        Args:
            name: Logger name (usually __name__)

        Returns:
            Logger instance
        """
        return logging.getLogger(name)

    def get_ai_logger(self) -> logging.Logger:
        """Get AI request/response logger.

        Returns:
            AI logger instance
        """
        return self.ai_logger

    def log_ai_request(
        self,
        model: str,
        endpoint: str,
        messages: list,
        system_prompt: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Log an AI request.

        Args:
            model: Model name
            endpoint: API endpoint
            messages: Request messages
            system_prompt: System prompt if any
            metadata: Additional metadata
        """
        log_entry = {
            "type": "request",
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "endpoint": endpoint,
            "message_count": len(messages),
            "system_prompt": (
                system_prompt[:100] + "..."
                if system_prompt and len(system_prompt) > 100
                else system_prompt
            ),
            "last_user_message": self._get_last_user_message(messages),
        }

        if metadata:
            log_entry["metadata"] = metadata

        self.ai_logger.info(self._format_log_entry(log_entry))

    def log_ai_response(
        self,
        model: str,
        response: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Log an AI response.

        Args:
            model: Model name
            response: Response text (will be truncated for logging)
            duration: Request duration in seconds
            success: Whether the request was successful
            error: Error message if any
            metadata: Additional metadata
        """
        log_entry = {
            "type": "response",
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "success": success,
            "duration_seconds": round(duration, 2),
            "response_length": len(response) if response else 0,
            "response_preview": (
                response[:200] + "..." if response and len(response) > 200 else response
            ),
        }

        if error:
            log_entry["error"] = error

        if metadata:
            log_entry["metadata"] = metadata

        self.ai_logger.info(self._format_log_entry(log_entry))

    def log_ai_stream_chunk(self, model: str, chunk_num: int, chunk_size: int, total_size: int):
        """Log streaming progress.

        Args:
            model: Model name
            chunk_num: Chunk number
            chunk_size: Size of this chunk
            total_size: Total size so far
        """
        if chunk_num % 10 == 0:  # Log every 10th chunk to avoid spam
            log_entry = {
                "type": "stream_progress",
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "chunk_num": chunk_num,
                "chunk_size": chunk_size,
                "total_size": total_size,
            }
            self.ai_logger.debug(self._format_log_entry(log_entry))

    def _get_last_user_message(self, messages: list) -> Optional[str]:
        """Extract last user message from messages list.

        Args:
            messages: List of message dicts

        Returns:
            Last user message content or None
        """
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                return content[:100] + "..." if len(content) > 100 else content
        return None

    def _format_log_entry(self, entry: dict) -> str:
        """Format log entry as a readable string.

        Args:
            entry: Log entry dictionary

        Returns:
            Formatted string
        """
        import json

        return json.dumps(entry, ensure_ascii=False, indent=None)


# Global logger instance
_logger_instance = None


def setup_logging():
    """Setup logging for the application."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PopupAILogger()
    return _logger_instance


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    if _logger_instance is None:
        setup_logging()
    return _logger_instance.get_logger(name)


def get_ai_logger() -> logging.Logger:
    """Get AI request/response logger.

    Returns:
        AI logger instance
    """
    if _logger_instance is None:
        setup_logging()
    return _logger_instance.get_ai_logger()


def log_ai_request(*args, **kwargs):
    """Log an AI request."""
    if _logger_instance is None:
        setup_logging()
    _logger_instance.log_ai_request(*args, **kwargs)


def log_ai_response(*args, **kwargs):
    """Log an AI response."""
    if _logger_instance is None:
        setup_logging()
    _logger_instance.log_ai_response(*args, **kwargs)


def log_ai_stream_chunk(*args, **kwargs):
    """Log streaming chunk."""
    if _logger_instance is None:
        setup_logging()
    _logger_instance.log_ai_stream_chunk(*args, **kwargs)
