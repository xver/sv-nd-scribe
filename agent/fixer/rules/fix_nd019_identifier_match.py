# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal

_MSG_RE = re.compile(r"Documented identifier '([^']+)' does not match code identifier '([^']+)'")


class FixNd019(BaseFixer):
    """Fixer for mismatch between NaturalDocs comment identifier and code identifier."""

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

        msg = violation.get("message", "")
        m = _MSG_RE.search(msg)
        if not m:
            return None

        doc_name, code_name = m.group(1), m.group(2)

        # Scan backwards from line_idx, allowing blank lines between declaration and comment block
        curr = line_idx - 1
        while curr >= 0 and source_lines[curr].strip() == "":
            curr -= 1

        end_idx = curr
        in_block_comment = False
        lines_scanned = 0
        while curr >= 0 and lines_scanned < 200:
            lines_scanned += 1
            l_str = source_lines[curr].strip()
            if in_block_comment:
                if "/*" in l_str:
                    in_block_comment = False
                curr -= 1
            else:
                if l_str.endswith("*/") and "/*" not in l_str:
                    in_block_comment = True
                    curr -= 1
                elif l_str.startswith("/*") and l_str.endswith("*/"):
                    curr -= 1
                elif l_str.startswith("//") or l_str.startswith("*"):
                    curr -= 1
                else:
                    break
        start_idx = curr + 1

        # Collect lines in comment block that contain doc_name
        affected_indices = [
            i for i in range(start_idx, end_idx + 1)
            if doc_name in source_lines[i]
        ]

        if not affected_indices:
            # If no preceding comments match, check if line_idx itself contains doc_name in an inline comment
            line_str = source_lines[line_idx]
            if ("//" in line_str and doc_name in line_str.split("//", 1)[1]) or \
               ("/*" in line_str and doc_name in line_str):
                affected_indices = [line_idx]
            else:
                return None

        patch_start = min(affected_indices)
        patch_end = max(affected_indices)

        patch_lines = []
        for i in range(patch_start, patch_end + 1):
            orig = source_lines[i]
            if i == line_idx:
                if "//" in orig:
                    code_part, comment_part = orig.split("//", 1)
                    updated_comment = re.sub(r'\b' + re.escape(doc_name) + r'\b', code_name, comment_part)
                    if updated_comment == comment_part and doc_name in comment_part:
                        updated_comment = comment_part.replace(doc_name, code_name)
                    updated = code_part + "//" + updated_comment
                elif "/*" in orig and "*/" in orig:
                    before_c, rest = orig.split("/*", 1)
                    comment_part, after_c = rest.split("*/", 1)
                    updated_comment = re.sub(r'\b' + re.escape(doc_name) + r'\b', code_name, comment_part)
                    if updated_comment == comment_part and doc_name in comment_part:
                        updated_comment = comment_part.replace(doc_name, code_name)
                    updated = before_c + "/*" + updated_comment + "*/" + after_c
                else:
                    updated = re.sub(r'\b' + re.escape(doc_name) + r'\b', code_name, orig)
                    if updated == orig and doc_name in orig:
                        updated = orig.replace(doc_name, code_name)
            else:
                # If this is a NaturalDocs keyword line, cleanly replace the documented identifier
                kw_m = re.match(r'^(\s*(?://|\*|\/\*)?\s*(?:Class|Function|Task|Interface|Module|Package|Define|Macro|Enum|Type|Typedef|Struct|Union|Variable|Port|Signal|Field|Modport|Clocking|Constraint|Property|Sequence|Checker|Covergroup|Coverpoint|Process|Assign)\s*:\s*)(\S+)(.*)$', orig, re.I)
                if kw_m:
                    prefix = kw_m.group(1)
                    suffix = kw_m.group(3)
                    updated = f"{prefix}{code_name}{suffix}"
                else:
                    updated = re.sub(r'\b' + re.escape(doc_name) + r'\b', code_name, orig)
                    if updated == orig and doc_name in orig:
                        updated = orig.replace(doc_name, code_name)
            if not updated.endswith("\n"):
                updated += "\n"
            patch_lines.append(updated)

        return FixProposal(
            rule_id="ND-019",
            file=violation["file"],
            line=patch_start + 1,
            description=f"Update documented identifier '{doc_name}' to match code '{code_name}'",
            patch_lines=patch_lines,
            replace_line=None,
            replace_range=(patch_start + 1, patch_end + 1),
            is_safe=True,
        )
