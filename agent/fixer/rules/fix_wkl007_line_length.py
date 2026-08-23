# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal


class FixWkl007(BaseFixer):
    """Report line length violations (unsafe to auto-fix)."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None,
        **kwargs,
    ) -> Optional[FixProposal]:
        # These rules are structurally complex or require semantic renaming.
        # It is unsafe to auto-fix them blindly without an AST/Language Server.
        return FixProposal(
            rule_id="WKL-007",
            file=violation["file"],
            line=violation.get("line", 1),
            description="[Report-Only] Report line length violations (unsafe to auto-fix). Manual intervention required.",
            patch_lines=[],  # No automatic patch proposed
            replace_line=None,
            is_safe=False,
            llm_generated=False,
        )
