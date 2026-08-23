# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from typing import Dict, Any, Optional, IO
from ..base_llm import BaseLLMProvider
from ..llm_registry import register_llm

@register_llm("none")
class NoneProvider(BaseLLMProvider):
    """Deterministic fallback provider — returns empty text for LLM calls so template output is used."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @property
    def name(self) -> str:
        return "none"

    def complete(self, prompt: str, system: str = "", timeout: int = 30, debug_log: Optional[IO] = None) -> str:
        return ""

    @property
    def is_available(self) -> bool:
        return True
