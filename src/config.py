"""Configuration and settings management."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.constants import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    INPUT_MAX_HEIGHT,
    MAX_HISTORY,
    DEFAULT_OLLAMA_ENDPOINT,
    DEFAULT_OPENAI_ENDPOINT,
    DEFAULT_PERPLEXITY_ENDPOINT,
    DEFAULT_UI_FONT,
    DEFAULT_WEBVIEW_FONT_FAMILY,
    DEFAULT_WEBVIEW_FONT_SIZE,
    AUTO_FETCH_MODELS_DEFAULT,
    APP_SUBDIR,
    CONFIG_FILE_NAME,
    PROMPTS_FILE_NAME,
    MODELS_FILE_NAME,
    CONVERSATIONS_DIR_NAME,
)
from src.ui_strings import DEFAULT_PROMPTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """AI model configuration."""

    name: str
    type: str  # "ollama" or "api"
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model_id: str  # e.g., "llama2", "gpt-4"


class PromptTemplate(BaseModel):
    """Prompt template configuration."""

    name: str
    system_prompt: str
    description: Optional[str] = None
    default_model: Optional[str] = None


class ConversationMessage(BaseModel):
    """A single message in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    tokens_input: Optional[int] = None  # Tokens used for input (prompt)
    tokens_output: Optional[int] = None  # Tokens used for output (completion)


class Conversation(BaseModel):
    """A conversation history."""

    id: str
    title: str
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: float
    updated_at: float


class Settings:
    """Application settings manager."""

    def __init__(self):
        # Use XDG base directories (respects Flatpak sandbox)
        import os

        xdg_config_home = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        xdg_data_home = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))

        self.config_dir = Path(xdg_config_home) / APP_SUBDIR
        self.data_dir = Path(xdg_data_home) / APP_SUBDIR
        self.config_file = self.config_dir / CONFIG_FILE_NAME
        self.prompts_file = self.config_dir / PROMPTS_FILE_NAME
        self.models_file = self.config_dir / MODELS_FILE_NAME
        self.conversations_dir = self.data_dir / CONVERSATIONS_DIR_NAME

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

        # Load or create default config
        self.config = self._load_config()
        self.models = self._load_models()
        self.prompts = self._load_prompts()

    def _load_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        default_config = {
            "selected_model": "",
            "selected_prompt": "",
            "default_model": "",
            "window_width": DEFAULT_WINDOW_WIDTH,
            "window_height": DEFAULT_WINDOW_HEIGHT,
            "input_max_height": INPUT_MAX_HEIGHT,
            "max_history": MAX_HISTORY,
            "ollama_endpoint": DEFAULT_OLLAMA_ENDPOINT,
            "openai_endpoint": DEFAULT_OPENAI_ENDPOINT,
            "openai_api_key": "",
            "perplexity_endpoint": DEFAULT_PERPLEXITY_ENDPOINT,
            "perplexity_api_key": "",
            "custom_api_endpoint": "",
            "custom_api_key": "",
            "auto_fetch_models": AUTO_FETCH_MODELS_DEFAULT,
            "ui_font_family": DEFAULT_UI_FONT,
            "webview_font_family": DEFAULT_WEBVIEW_FONT_FAMILY,
            "webview_font_size": DEFAULT_WEBVIEW_FONT_SIZE,
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    return {**default_config, **loaded_config}
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Save default config
        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict[str, Any]):
        """Save application configuration."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _load_models(self) -> List[ModelConfig]:
        """Load model configurations."""
        if self.models_file.exists():
            try:
                with open(self.models_file, "r", encoding="utf-8") as f:
                    models_data = json.load(f)
                    return [ModelConfig(**m) for m in models_data]
            except Exception as e:
                logger.error(f"Failed to load models: {e}")

        # Return empty list, let app auto-fetch models on startup
        return []

    def save_models(self, models: List[ModelConfig]):
        """Save model configurations."""
        try:
            with open(self.models_file, "w", encoding="utf-8") as f:
                json.dump([m.model_dump() for m in models], f, indent=2)
            self.models = models
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def _load_prompts(self) -> List[PromptTemplate]:
        """Load prompt templates."""
        default_prompts = [PromptTemplate(**prompt_data) for prompt_data in DEFAULT_PROMPTS]

        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, "r", encoding="utf-8") as f:
                    prompts_data = json.load(f)
                    return [PromptTemplate(**p) for p in prompts_data]
            except Exception as e:
                logger.error(f"Failed to load prompts: {e}")

        # Save default prompts
        self.save_prompts(default_prompts)
        return default_prompts

    def save_prompts(self, prompts: List[PromptTemplate]):
        """Save prompt templates."""
        try:
            with open(self.prompts_file, "w", encoding="utf-8") as f:
                json.dump([p.model_dump() for p in prompts], f, indent=2)
            self.prompts = prompts
        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self.config[key] = value
        self._save_config(self.config)

    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get a model by name."""
        for model in self.models:
            if model.name == name:
                return model
        return None

    def add_model(self, model: ModelConfig):
        """Add a new model configuration."""
        # Check if model with same name exists and update it
        for i, existing_model in enumerate(self.models):
            if existing_model.name == model.name:
                self.models[i] = model
                self.save_models(self.models)
                return

        # Add new model
        self.models.append(model)
        self.save_models(self.models)

    def remove_model(self, name: str):
        """Remove a model configuration."""
        self.models = [m for m in self.models if m.name != name]
        self.save_models(self.models)

    def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        for prompt in self.prompts:
            if prompt.name == name:
                return prompt
        return None

    def add_prompt(self, prompt: PromptTemplate):
        """Add a new prompt template."""
        # Check if prompt with same name exists and update it
        for i, existing_prompt in enumerate(self.prompts):
            if existing_prompt.name == prompt.name:
                self.prompts[i] = prompt
                self.save_prompts(self.prompts)
                return

        # Add new prompt
        self.prompts.append(prompt)
        self.save_prompts(self.prompts)

    def remove_prompt(self, name: str):
        """Remove a prompt template."""
        self.prompts = [p for p in self.prompts if p.name != name]
        self.save_prompts(self.prompts)

    def save_conversation(self, conversation: Conversation):
        """Save a conversation to disk."""
        try:
            conv_file = self.conversations_dir / f"{conversation.id}.json"
            with open(conv_file, "w", encoding="utf-8") as f:
                json.dump(conversation.model_dump(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

    def load_conversations(self) -> List[Conversation]:
        """Load all conversations."""
        conversations = []
        for conv_file in self.conversations_dir.glob("*.json"):
            try:
                with open(conv_file, "r", encoding="utf-8") as f:
                    conv_data = json.load(f)
                    conversations.append(Conversation(**conv_data))
            except Exception as e:
                logger.error(f"Failed to load conversation {conv_file}: {e}")

        # Sort by updated_at descending
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str):
        """Delete a conversation."""
        try:
            conv_file = self.conversations_dir / f"{conversation_id}.json"
            if conv_file.exists():
                conv_file.unlink()
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation_id}: {e}")
