# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import Dict, Any, Optional, IO
from ..base_llm import BaseLLMProvider
from ..llm_registry import register_llm

@register_llm("mock")
class MockProvider(BaseLLMProvider):
    """Mock provider for predictable CI testing."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @property
    def name(self) -> str:
        return "mock"

    def complete(self, prompt: str, system: str = "", timeout: int = 30, debug_log: Optional[IO] = None) -> str:
        return "// Mock LLM description for construct"

    @property
    def is_available(self) -> bool:
        return True
