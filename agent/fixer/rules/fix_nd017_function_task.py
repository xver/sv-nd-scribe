# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.
import re
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import (
    build_naturaldocs_comment,
    extract_name_from_violation,
    extract_function_params,
    build_parameters_block,
    infer_param_description,
)

_SIG_RE = re.compile(
    r'\b(?:extern\s+|external\s+)?(?:pure\s+virtual\s+|virtual\s+|protected\s+|local\s+|static\s+)*(function|task)(?:\s+automatic)?(?:\s+(?:void|(?:[\w:<>\$]+(?:\s*\[[^\]]+\])*)|\s*(?:\[[^\]]+\])))?\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\(|;)',
    re.IGNORECASE,
)


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

        # 1. Determine function/task name and signature context
        name = extract_name_from_violation(violation)
        msg = violation.get("message", "")

        # Collect signature text strictly up to statement boundary (; or begin or { or endclass)
        sig_lines = []
        for i in range(line_idx, min(len(source_lines), line_idx + 10)):
            sig_lines.append(source_lines[i])
            if any(term in source_lines[i] for term in (";", "begin", "{", "endclass")):
                break
        sig_text = " ".join([l.strip() for l in sig_lines])
        m = _SIG_RE.search(line) or _SIG_RE.search(sig_text)
        if not name or name == "item":
            name = m.group(2) if m else "item"

        # 2. Determine kw (Function vs Task)
        # CRITICAL:
        # - If the signature statement contains 'task', it is strictly 'Task'.
        # - If the signature statement contains 'function' or name is 'new', it is strictly 'Function'.
        # - Never let "Function/Task '...'" in violation message falsely match 'Task'!
        kw = None
        if re.search(r'\btask\b', sig_text, re.IGNORECASE):
            kw = "Task"
        elif re.search(r'\bfunction\b', sig_text, re.IGNORECASE) or (name and name.lower() == "new"):
            kw = "Function"
        elif msg:
            m_msg = re.search(r"(?<!/)\b(Function|Task)\s+'([^']+)'", msg, re.IGNORECASE)
            if m_msg:
                kw = m_msg.group(1).capitalize()
                if not name or name == "item":
                    name = m_msg.group(2)

        if not kw:
            kw = m.group(1).capitalize() if m else "Function"

        if name and name.lower() == "new":
            kw = "Function"

        params = extract_function_params(line, source_lines, line_idx)
        param_lines = build_parameters_block(params, indent)

        # 3. Check for existing comment block preceding line_idx
        # Scan backward from line_idx - 1 skipping blank lines
        k = line_idx - 1
        while k >= 0 and source_lines[k].strip() == "":
            k -= 1

        if k >= 0:
            prev_line = source_lines[k].strip()

            # Case A: Preceding block comment /* ... */
            if prev_line.endswith("*/"):
                comment_end_idx = k
                comment_start_idx = -1
                for j in range(k, -1, -1):
                    if "/*" in source_lines[j]:
                        comment_start_idx = j
                        break
                    if k - j > 50:
                        break

                if comment_start_idx != -1:
                    block_slice = source_lines[comment_start_idx : comment_end_idx + 1]
                    block_content = "".join(block_slice)
                    # Check if this block comment contains Function: / Task:
                    if re.search(r'\b(Function|Task)\s*:', block_content, re.IGNORECASE):
                        uses_asterisk = any(
                            re.match(r"^\s*\*", source_lines[idx])
                            for idx in range(comment_start_idx + 1, comment_end_idx)
                        )
                        inner_indent = indent + "  "
                        for idx in range(comment_start_idx + 1, comment_end_idx):
                            line_content = source_lines[idx]
                            if line_content.strip():
                                inner_indent = line_content[: len(line_content) - len(line_content.lstrip())]
                                break

                        new_lines = []
                        skip_empty_params = False

                        for idx, b_line in enumerate(block_slice):
                            b_stripped = b_line.strip()

                            # 1. Update tag line if it's Function: / Task:
                            if re.search(r'\b(Function|Task)\s*:', b_line, re.IGNORECASE):
                                updated_line = re.sub(r'\b(Function|Task)\s*:', f'{kw}:', b_line, flags=re.IGNORECASE)
                                if not re.search(rf'\b{kw}:\s*{re.escape(name)}\b', updated_line, re.IGNORECASE):
                                    updated_line = re.sub(rf'\b{kw}:.*$', f'{kw}: {name}\n', updated_line)
                                new_lines.append(updated_line)
                                continue

                            # 2. Update description line if it mentions "function '<name>'" or "task '<name>'"
                            if ("description for" in b_line.lower() or "definition for" in b_line.lower()) and name.lower() in b_line.lower():
                                updated_line = re.sub(
                                    r'\b(function|task)\s*\'?' + re.escape(name) + r'\'?',
                                    f"{kw.lower()} '{name}'",
                                    b_line,
                                    flags=re.IGNORECASE
                                )
                                new_lines.append(updated_line)
                                continue

                            # 3. Handle Parameters: section
                            if b_stripped.startswith("Parameters:"):
                                if len(params) == 0:
                                    skip_empty_params = True
                                    continue

                            if skip_empty_params:
                                if b_stripped == "" or b_stripped == "*" or b_stripped.startswith("-") or re.match(r'^\w+\s*-', b_stripped):
                                    continue
                                elif "*/" in b_line:
                                    skip_empty_params = False
                                else:
                                    skip_empty_params = False

                            new_lines.append(b_line)

                        if len(params) > 0:
                            has_params = any("parameters:" in l.lower() for l in new_lines)
                            has_param_items = any(re.search(r'-\s*\S+', l) for l in new_lines)
                            if not has_params or not has_param_items:
                                if uses_asterisk:
                                    block_param_lines = [f"{indent} *\n", f"{indent} * Parameters:\n"]
                                    for p in params:
                                        desc = infer_param_description(p)
                                        block_param_lines.append(f"{indent} *   {p} - {desc}\n")
                                else:
                                    block_param_lines = [f"\n", f"{inner_indent}Parameters:\n"]
                                    for p in params:
                                        desc = infer_param_description(p)
                                        block_param_lines.append(f"{inner_indent}  {p} - {desc}\n")

                                if has_params and not has_param_items:
                                    new_lines = [l for l in new_lines if not l.strip().startswith("Parameters:")]

                                end_star_idx = len(new_lines) - 1
                                while end_star_idx >= 0 and "*/" not in new_lines[end_star_idx]:
                                    end_star_idx -= 1
                                if end_star_idx >= 0:
                                    if end_star_idx > 0 and new_lines[end_star_idx - 1].strip() == "" and block_param_lines[0] == "\n":
                                        block_param_lines = block_param_lines[1:]
                                    new_lines[end_star_idx:end_star_idx] = block_param_lines
                        else:
                            end_star_idx = len(new_lines) - 1
                            while end_star_idx >= 0 and "*/" not in new_lines[end_star_idx]:
                                end_star_idx -= 1
                            if end_star_idx > 0 and new_lines[end_star_idx - 1].strip() == "":
                                del new_lines[end_star_idx - 1]

                        if new_lines != block_slice:
                            return FixProposal(
                                rule_id="ND-017",
                                file=violation["file"],
                                line=comment_start_idx + 1,
                                description=f"Update documentation for {kw.lower()} '{name}'",
                                patch_lines=new_lines,
                                replace_line=None,
                                replace_range=(comment_start_idx + 1, comment_end_idx + 1),
                                is_safe=True,
                                llm_generated=False,
                            )
                        return None

            # Case B: Preceding single-line comment block // ...
            elif prev_line.startswith("//"):
                comment_end_idx = k
                line_comment_start_idx = k
                for j in range(k, -1, -1):
                    if source_lines[j].strip().startswith("//"):
                        line_comment_start_idx = j
                    else:
                        break

                comment_slice = source_lines[line_comment_start_idx : comment_end_idx + 1]
                comment_content = "".join(comment_slice)
                if re.search(r'//\s*(Function|Task)\s*:', comment_content, re.IGNORECASE):
                    new_lines = []
                    for c_line in comment_slice:
                        c_stripped = c_line.strip()
                        if re.search(r'//\s*(Function|Task)\s*:', c_line, re.IGNORECASE):
                            updated_line = re.sub(r'(//\s*)(Function|Task)\s*:', rf'\1{kw}:', c_line, flags=re.IGNORECASE)
                            if not re.search(rf'//\s*{kw}:\s*{re.escape(name)}\b', updated_line, re.IGNORECASE):
                                updated_line = re.sub(rf'//\s*{kw}:.*$', f'// {kw}: {name}\n', updated_line)
                            new_lines.append(updated_line)
                            continue

                        if ("description for" in c_line.lower() or "definition for" in c_line.lower()) and name.lower() in c_line.lower():
                            updated_line = re.sub(
                                r'\b(function|task)\s*\'?' + re.escape(name) + r'\'?',
                                f"{kw.lower()} '{name}'",
                                c_line,
                                flags=re.IGNORECASE
                            )
                            new_lines.append(updated_line)
                            continue

                        new_lines.append(c_line)

                    if len(params) == 0:
                        filtered = []
                        skip_param = False
                        for c_line in new_lines:
                            c_stripped = c_line.strip()
                            if c_stripped.startswith("// Parameters:"):
                                skip_param = True
                                continue
                            if skip_param:
                                if c_stripped in ("//", "") or re.match(r"^//\s*(?:-|\w+\s*-)", c_stripped):
                                    continue
                                else:
                                    skip_param = False
                            filtered.append(c_line)
                        while filtered and filtered[-1].strip() == "//":
                            filtered.pop()
                        new_lines = filtered
                    else:
                        has_params = any("parameters:" in l.lower() for l in new_lines)
                        has_param_items = any(re.search(r'-\s*\S+', l) for l in new_lines)
                        if not has_params or not has_param_items:
                            if has_params and not has_param_items:
                                new_lines = [l for l in new_lines if not l.strip().startswith("// Parameters:")]
                            param_block = build_parameters_block(params, indent)
                            if new_lines and new_lines[-1].strip() == "//" and param_block and param_block[0].strip() == "//":
                                param_block = param_block[1:]
                            new_lines.extend(param_block)

                    if new_lines != comment_slice:
                        return FixProposal(
                            rule_id="ND-017",
                            file=violation["file"],
                            line=line_comment_start_idx + 1,
                            description=f"Update documentation for {kw.lower()} '{name}'",
                            patch_lines=new_lines,
                            replace_line=None,
                            replace_range=(line_comment_start_idx + 1, comment_end_idx + 1),
                            is_safe=True,
                            llm_generated=False,
                        )
                    return None

        # Case C: No existing comment block found above line_idx -> Generate new comment block
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
