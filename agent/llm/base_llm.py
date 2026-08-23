# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from abc import ABC, abstractmethod
from typing import Optional, IO

class BaseLLMProvider(ABC):
    """Abstract base class for LLM provider backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name key (e.g., 'none', 'openai', 'ollama', 'mock')."""
        pass

    @abstractmethod
    def complete(self, prompt: str, system: str = "", timeout: int = 30, debug_log: Optional[IO] = None) -> str:
        """
        Send prompt and system instruction to the LLM backend.
        Return text response, or empty string on failure.

        Args:
            prompt: User prompt text
            system: System instruction text
            timeout: Request timeout in seconds
            debug_log: Optional writable file handle for logging prompts/responses
        """
        pass

    @property
    def is_available(self) -> bool:
        """Return True if required API keys / endpoints / local services are reachable."""
        return True
