# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import build_naturaldocs_comment

_SIG_RE = re.compile(
    r'\b(function|task)\s+(?:automatic\s+)?(?:\w+\s+)?(\w+)\s*[;(]',
    re.IGNORECASE,
)
_PARAM_RE = re.compile(r'\(([^)]*)\)')


def _extract_params(line: str) -> List[str]:
    """Extract parameter names from a single-line signature."""
    m = _PARAM_RE.search(line)
    if not m or not m.group(1).strip():
        return []
    params = []
    for part in m.group(1).split(','):
        part = part.strip()
        if not part:
            continue
        tokens = re.split(r'[\s=]', part)
        tokens = [t for t in tokens if t]
        if tokens:
            params.append(tokens[-1])
    return params


class FixNd017(BaseFixer):
    """Insert NaturalDocs Function/Task comment with Parameters block for ND-017."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None,
        **kwargs,
    ) -> Optional[FixProposal]:
        line_idx = violation["line"] - 1
        if not (0 <= line_idx < len(source_lines)):
            return None

        line = source_lines[line_idx]
        indent = line[: len(line) - len(line.lstrip())]

        m = _SIG_RE.search(line)
        kw = m.group(1).capitalize() if m else "Function"
        name = m.group(2) if m else "item"

        # Try to parse parameters from same line or next if unclosed
        sig_line = line
        if '(' in line and ')' not in line:
            for extra_idx in range(line_idx + 1, min(line_idx + 10, len(source_lines))):
                sig_line += source_lines[extra_idx]
                if ')' in source_lines[extra_idx]:
                    break

        params = _extract_params(sig_line)
        param_lines = []
        if params:
            param_lines.append(f"{indent}//\n")
            param_lines.append(f"{indent}// Parameters:\n")
            for p in params:
                param_lines.append(f"{indent}//   {p} - <description>\n")

        doc_comment, llm_generated = build_naturaldocs_comment(
            tag=kw,
            name=name,
            indent=indent,
            source_lines=source_lines,
            line_idx=line_idx,
            kind_label=kw.lower(),
            provider=kwargs.get("provider"),
            skill_name="function_task",
            extra_lines=param_lines,
        )

        return FixProposal(
            rule_id="ND-017",
            file=violation["file"],
            line=violation["line"],
            description=f"Insert // {kw}: {name} documentation comment",
            patch_lines=[doc_comment],
            replace_line=None,
            is_safe=True,
            llm_generated=llm_generated,
        )
