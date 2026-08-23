# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
Centralized NaturalDocs comment builder and description extractor for fixer rules.
Ensures all NaturalDocs comment insertions comply with ND-012 (non-empty description line).
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from agent.llm.skill_loader import load_skill

_ND_KEYWORD_RE = re.compile(
    r'^(?:Class|Module|Package|Interface|Function|Task|Checker|Program|Property|'
    r'Covergroup|Coverpoint|Constraint|Variable|Enum|Type|Typedef|Define|Macro|'
    r'Modport|Clocking|Bind|Assign|Section|Group|File|About|Topic)\s*:',
    re.IGNORECASE,
)

def extract_comment_from_context(
    source_lines: List[str],
    line_idx: int,
) -> Optional[str]:
    """
    Try to extract an existing human-written comment from the line or adjacent context.
    - Checks trailing line comment `// ...` or `/* ... */` on the same line.
    - Checks previous non-empty line if it is a plain comment (and not a file header or ND keyword).
    """
    if not (0 <= line_idx < len(source_lines)):
        return None

    line = source_lines[line_idx].strip()

    # 1. Check trailing line comment on the same line (e.g., `int m_timeout; // Timeout counter`)
    if "//" in line:
        code_part, comment_part = line.split("//", 1)
        comment_clean = comment_part.strip().rstrip("*/").strip()
        if comment_clean and not _ND_KEYWORD_RE.match(comment_clean):
            # Exclude compiler/lint directives
            if not comment_clean.lower().startswith(("verilator", "synopsys", "synthesis", "pragma")):
                return comment_clean

    # 2. Check inline block comment `/* ... */` on the same line
    m_block = re.search(r'/\*\s*(.*?)\s*\*/', line)
    if m_block:
        comment_clean = m_block.group(1).strip()
        if comment_clean and not _ND_KEYWORD_RE.match(comment_clean):
            if not comment_clean.lower().startswith(("verilator", "synopsys", "synthesis", "pragma")):
                return comment_clean

    # 3. Check previous non-empty line if it was a plain comment (and not a header / ND keyword)
    prev_idx = line_idx - 1
    while prev_idx >= 0 and source_lines[prev_idx].strip() == "":
        prev_idx -= 1
    if prev_idx >= 0:
        prev_line = source_lines[prev_idx].strip()
        if prev_line.startswith("//") and not prev_line.startswith("///"):
            comment_clean = prev_line.lstrip("/ \t").rstrip("*/").strip()
            if comment_clean and not _ND_KEYWORD_RE.match(comment_clean):
                if not comment_clean.startswith(("****", "====", "----", "####")):
                    return comment_clean

    return None

def build_naturaldocs_comment(
    tag: str,
    name: str,
    indent: str,
    source_lines: List[str],
    line_idx: int,
    kind_label: Optional[str] = None,
    provider: Any = None,
    skill_name: Optional[str] = None,
    extra_lines: Optional[List[str]] = None,
) -> Tuple[str, bool]:
    """
    Builds a standard NaturalDocs comment block:
      // <Tag>: <name>
      // <description or TODO: Add description for <kind> '<name>'>
      [extra lines, e.g. Parameters...]

    Order of description resolution:
      1. Extract human-written comment from code context in file.
      2. If LLM provider is active, infer concise description from surrounding code.
      3. Deterministic fallback: '// TODO: Add description for <kind> '<name>''.
    """
    kind = kind_label or tag.lower()

    # 1. Try to extract existing description from source file
    extracted_desc = extract_comment_from_context(source_lines, line_idx)
    if extracted_desc:
        desc_line = f"{indent}// {extracted_desc}\n"
        doc_comment = f"{indent}// {tag}: {name}\n{desc_line}"
        if extra_lines:
            doc_comment += "".join(extra_lines)
        return doc_comment, False

    # 2. Try LLM provider if available
    llm_generated = False
    if provider and getattr(provider, "is_available", False) and getattr(provider, "name", "none") != "none":
        try:
            skill = load_skill(skill_name or "nd_comment", __file__) if skill_name else load_skill("nd_comment", __file__)
            start_idx = max(0, line_idx - 5)
            end_idx = min(len(source_lines), line_idx + 15)
            context = "".join(source_lines[start_idx:end_idx])

            prompt = f"""Given the following SystemVerilog context:
```systemverilog
{context}
```
Generate a NaturalDocs comment block for the `{kind}` named `{name}`.
Format must strictly be:
// {tag}: {name}
// <concise description of what this {kind} does based on the code context>

Output ONLY the NaturalDocs comment lines starting with `//`. Do not include markdown block markers or explanations."""

            response = provider.complete(prompt=prompt, system=skill)
            if response:
                lines = [l.strip() for l in response.strip().splitlines() if l.strip().startswith("//")]
                if lines:
                    doc_comment = "".join(f"{indent}{l}\n" for l in lines)
                    if not doc_comment.endswith("\n"):
                        doc_comment += "\n"
                    if extra_lines:
                        doc_comment += "".join(extra_lines)
                    return doc_comment, True
        except Exception:
            pass

    # 3. Fallback: Add TODO description
    doc_comment = f"{indent}// {tag}: {name}\n{indent}// TODO: Add description for {kind} '{name}'\n"
    if extra_lines:
        doc_comment += "".join(extra_lines)
    return doc_comment, False
