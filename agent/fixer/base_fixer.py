# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from agent.llm.base_llm import BaseLLMProvider


class LinterError(Exception):
    """Raised when the linter subprocess fails or returns unparseable output."""
    pass


@dataclass
class FixProposal:
    """Represents a proposed fix for a single linter violation."""
    rule_id: str
    file: str
    line: int
    description: str
    patch_lines: List[str]                  # Lines to insert or replacement block
    replace_line: Optional[str] = None      # Exact line to replace, if not insertion
    replace_range: Optional[Tuple[int, int]] = None  # (start_line, end_line) 1-indexed inclusive for multi-line replacement
    is_safe: bool = True                    # Safe vs Interactive vs Unsafe
    llm_generated: bool = False             # LLM vs deterministic origin
    confidence: float = 1.0                 # Confidence score (0.0 to 1.0)
    inferred_fields: Dict[str, Any] = field(default_factory=dict)


class BaseFixer(ABC):
    """Abstract base class for rule fixers."""

    def __init__(self, rule_config: Dict[str, Any] = None):
        self.rule_config = rule_config or {}

    @abstractmethod
    def propose(self, violation: Dict[str, Any], source_lines: List[str], config: Dict[str, Any] = None, provider: Optional[BaseLLMProvider] = None) -> Optional[FixProposal]:
        """
        Analyze violation + surrounding source lines and return a FixProposal, or None if unfixable.
        
        Args:
            violation: Dict representing rule violation (file, line, column, rule_id, message)
            source_lines: Full line array of the file being fixed (0-indexed array, 1-indexed violation lines)
            config: General agent/linter config dictionary (e.g. tab_width, header_defaults)
            provider: Configured LLM provider instance for rules requiring generation
        """
        pass
