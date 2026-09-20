# Copyright (c) 2026 IC Verimeter. All rights reserved.
import os
import re
from datetime import date
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal
from agent.fixer.doc_helper import resolve_author, resolve_company, resolve_legal
import sys


class FixNd001(BaseFixer):
    """Insert, update specific field, or overwrite file header comment block."""

    def _render_full_template(
        self,
        filename: str,
        company: str,
        author: str,
        legal: str,
        date_str: str,
        today: date,
        agent_cfg: Dict[str, Any],
        violation: Dict[str, Any],
        source_lines: Optional[List[str]] = None,
    ) -> List[str]:
        custom_tmpl = agent_cfg.get("custom_header_template") or agent_cfg.get("header_template.txt") or agent_cfg.get("header_template")
        
        # Auto-detect template file candidates
        if not custom_tmpl or not os.path.exists(custom_tmpl):
            candidates = [
                ".sv-nd-scribe/header_template.txt",
                ".sv-nd-scribe/header_template",
                "header_template.txt",
                "header_template",
                "template/header_template.txt",
                "template/header_template",
            ]
            file_dir = os.path.dirname(os.path.abspath(violation.get("file", "")))
            curr = file_dir
            for _ in range(10):
                for cand in candidates:
                    cand_path = os.path.join(curr, cand)
                    if os.path.exists(cand_path):
                        custom_tmpl = cand_path
                        break
                if custom_tmpl:
                    break
                parent = os.path.dirname(curr)
                if parent == curr:
                    break
                curr = parent

        if not custom_tmpl or not os.path.exists(custom_tmpl):
            agent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            default_cand = os.path.join(agent_dir, "templates", "header_template.txt")
            if os.path.exists(default_cand):
                custom_tmpl = default_cand

        if custom_tmpl and os.path.exists(custom_tmpl):
            try:
                with open(custom_tmpl, "r", encoding="utf-8") as tf:
                    tmpl_text = tf.read()
            except Exception:
                tmpl_text = ""

            # Extract author from template if present and not a placeholder
            tmpl_author_match = re.search(r"^\s*\*\s*Author:\s*(.+)$", tmpl_text, re.MULTILINE | re.IGNORECASE)
            effective_author = author
            if tmpl_author_match:
                found_auth = tmpl_author_match.group(1).strip()
                if found_auth and not found_auth.startswith("${") and not found_auth.startswith("{{") and "TODO" not in found_auth:
                    effective_author = found_auth

            if effective_author and "TODO" not in effective_author:
                updated_str = f"{date_str} ({effective_author})"
                created_str = f"{date_str} ({effective_author})"
            else:
                updated_str = date_str
                created_str = date_str

            # Check if source_lines has an existing description or created date
            existing_desc = f"SystemVerilog component — {filename}"
            existing_created = created_str
            if source_lines:
                for line in source_lines[:50]:
                    d_m = re.search(r"^\s*\*\s*Description:\s*(.*)", line, re.IGNORECASE)
                    if d_m and "TODO" not in d_m.group(1):
                        existing_desc = d_m.group(1).strip()
                    c_m = re.search(r"^\s*\*\s*Created:\s*(.*)", line, re.IGNORECASE)
                    if c_m and "TODO" not in c_m.group(1):
                        existing_created = c_m.group(1).strip()

            tmpl_text = tmpl_text.replace("${filename}", filename).replace("{{filename}}", filename)
            tmpl_text = tmpl_text.replace("${company}", company).replace("{{company}}", company)
            author_val = effective_author if "TODO" not in effective_author else author
            tmpl_text = tmpl_text.replace("${author}", author_val).replace("{{author}}", author_val)
            tmpl_text = tmpl_text.replace("${description}", existing_desc).replace("{{description}}", existing_desc)
            tmpl_text = tmpl_text.replace("${created}", existing_created).replace("{{created}}", existing_created)
            tmpl_text = tmpl_text.replace("${updated}", updated_str).replace("{{updated}}", updated_str)
            tmpl_text = tmpl_text.replace("${date}", date_str).replace("{{date}}", date_str)
            tmpl_text = tmpl_text.replace("${year}", str(today.year)).replace("{{year}}", str(today.year))
            tmpl_text = tmpl_text.replace("${legal}", legal).replace("{{legal}}", legal)

            header_block = [line + "\n" for line in tmpl_text.splitlines()]
            if header_block:
                return header_block

        # Fallback standard template
        author_val = author if "TODO" not in author else ""
        date_author = f"{date_str} ({author})" if author_val else date_str
        return [
            "/******************************************************************************\n",
            f" * File:        {filename}\n",
            " *\n",
            f" * Company:     {company}\n",
            " *\n",
            f" * Author:      {author}\n",
            " *\n",
            f" * Description: SystemVerilog component — {filename}\n",
            " *\n",
            f" * Created:     {date_author}\n",
            " *\n",
            f" * Updated:     {date_author}\n",
            " *\n",
            f" * Copyright (c) {today.year} {company}\n",
            f" * {legal}\n",
            " ******************************************************************************/\n",
        ]

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None,
        **kwargs,
    ) -> Optional[FixProposal]:
        agent_cfg = (config or {}).get("agent", config or {})
        cfg = agent_cfg.get("header_defaults", {})
        filename = os.path.basename(violation["file"])
        company, company_source = resolve_company(file_path=violation.get("file"), config=config)
        author, author_source = resolve_author(file_path=violation.get("file"), config=config)
        legal, legal_source = resolve_legal(file_path=violation.get("file"), config=config)

        if author == "TODO_AUTHOR":
            print(
                "[agent] Notice: Author is not configured; using 'TODO_AUTHOR'.\n"
                "Configure 'sv-nd-scribe.author' in VS Code settings, 'agent.header_defaults.author' in agent_config.json,\n"
                "or set your Git identity:\n"
                "  git config --global user.name \"Your Name\"\n"
                "  git config --global user.email \"your_email@example.com\"",
                file=sys.stderr,
            )

        msg = violation.get("message", "")
        viol_line = violation.get("line", 1)
        force_overwrite = kwargs.get("overwrite_header", False) or violation.get("force_overwrite", False)

        today = date.today()
        try:
            date_str = today.strftime("%B %-d, %Y")
        except ValueError:
            date_str = today.strftime("%B %#d, %Y")

        is_missing_header = "Missing block comment file header" in msg

        # Find existing header block at the beginning of source_lines
        start_idx = -1
        end_idx = -1
        if not is_missing_header:
            in_block = False
            for idx, l_str in enumerate(source_lines[:100]):
                stripped = l_str.strip()
                if start_idx == -1:
                    if not stripped:
                        continue
                    if stripped.startswith("/*"):
                        start_idx = idx
                        end_idx = idx
                        if not ("*/" in stripped and stripped.find("*/") > stripped.find("/*")):
                            in_block = True
                    elif stripped.startswith("//"):
                        start_idx = idx
                        end_idx = idx
                    else:
                        # Non-empty line before /* or // means there is no header at top of file
                        break
                else:
                    if in_block:
                        end_idx = idx
                        if "*/" in stripped:
                            in_block = False
                    else:
                        if not stripped:
                            break
                        if stripped.startswith("/*"):
                            end_idx = idx
                            if not ("*/" in stripped and stripped.find("*/") > stripped.find("/*")):
                                in_block = True
                        elif stripped.startswith("//"):
                            end_idx = idx
                        else:
                            break

        has_existing_header = (start_idx != -1)

        # MODE 1: Force overwrite of the entire header from template
        if force_overwrite:
            header_block = self._render_full_template(filename, company, author, legal, date_str, today, agent_cfg, violation, source_lines)
            if has_existing_header:
                if end_idx == -1:
                    end_idx = min(start_idx + len(header_block) - 1, len(source_lines) - 1)
                return FixProposal(
                    rule_id="ND-001",
                    file=violation["file"],
                    line=start_idx + 1,
                    description="Overwrite file header from template",
                    patch_lines=header_block,
                    replace_range=(start_idx + 1, end_idx + 1),
                    is_safe=True,
                )
            else:
                first_non_empty = 0
                while first_non_empty < len(source_lines) and not source_lines[first_non_empty].strip():
                    first_non_empty += 1
                if not header_block[-1].endswith("\n\n") and (not source_lines or source_lines[first_non_empty:first_non_empty+1]):
                    header_block.append("\n")
                return FixProposal(
                    rule_id="ND-001",
                    file=violation["file"],
                    line=1,
                    description="Insert file header comment block from template",
                    patch_lines=header_block,
                    replace_range=(1, first_non_empty) if first_non_empty > 0 else None,
                    replace_line=None,
                    is_safe=True,
                )

        # MODE 2: Completely missing header comment (no /* */ found at top of file)
        if not has_existing_header or is_missing_header:
            header_block = self._render_full_template(filename, company, author, legal, date_str, today, agent_cfg, violation, source_lines)
            first_non_empty = 0
            while first_non_empty < len(source_lines) and not source_lines[first_non_empty].strip():
                first_non_empty += 1
            if not header_block[-1].endswith("\n\n") and (not source_lines or source_lines[first_non_empty:first_non_empty+1]):
                header_block.append("\n")
            return FixProposal(
                rule_id="ND-001",
                file=violation["file"],
                line=1,
                description="Insert file header comment block from template",
                patch_lines=header_block,
                replace_range=(1, first_non_empty) if first_non_empty > 0 else None,
                replace_line=None,
                is_safe=True,
            )

        # MODE 3: Specific field error/warning in an existing header -> ONLY fix the targeted field/line!
        if 0 <= viol_line - 1 < len(source_lines):
            target_line_text = source_lines[viol_line - 1]
        else:
            target_line_text = ""

        # Case 3a: File keyword mismatch or missing
        if "does not match actual filename" in msg:
            if re.search(r"^\s*(?:\*|//|/\*|)\s*File:", target_line_text):
                new_line = re.sub(r"(^\s*(?:\*|//|/\*|)\s*File:\s*).*$", rf"\g<1>{filename}", target_line_text)
                if not new_line.endswith("\n"):
                    new_line += "\n"
            else:
                new_line = f" * File:        {filename}\n"

            return FixProposal(
                rule_id="ND-001",
                file=violation["file"],
                line=viol_line,
                description=f"Fix File header filename to '{filename}'",
                patch_lines=[new_line],
                replace_range=(viol_line, viol_line),
                is_safe=True,
            )

        if "missing 'File:' NaturalDocs keyword" in msg:
            insert_line_idx = start_idx + 1
            new_line = f" * File:        {filename}\n"
            return FixProposal(
                rule_id="ND-001",
                file=violation["file"],
                line=insert_line_idx + 1,
                description=f"Insert 'File: {filename}' into file header",
                patch_lines=[new_line],
                replace_line=None,
                is_safe=True,
            )

        # Case 3b: Placeholder in a specific line (e.g. TODO_COMPANY, TODO_AUTHOR, TODO_LEGAL)
        if "contains unresolved placeholder" in msg or "TODO" in target_line_text:
            new_line = target_line_text
            if "TODO_COMPANY" in target_line_text or "TODO COMPANY" in target_line_text:
                if company != "TODO_COMPANY":
                    new_line = new_line.replace("TODO_COMPANY", company).replace("TODO COMPANY", company)
            if "TODO_AUTHOR" in target_line_text or "TODO AUTHOR" in target_line_text:
                if author != "TODO_AUTHOR":
                    new_line = new_line.replace("TODO_AUTHOR", author).replace("TODO AUTHOR", author)
            if "TODO_LEGAL" in target_line_text or "TODO LEGAL" in target_line_text:
                if legal != "TODO_LEGAL":
                    new_line = new_line.replace("TODO_LEGAL", legal).replace("TODO LEGAL", legal)

            if new_line != target_line_text:
                return FixProposal(
                    rule_id="ND-001",
                    file=violation["file"],
                    line=viol_line,
                    description=f"Update placeholder in file header (line {viol_line})",
                    patch_lines=[new_line],
                    replace_range=(viol_line, viol_line),
                    is_safe=True,
                )

        # Case 3c: Author format warning (should contain email)
        if "valid email address" in msg and "Author:" in target_line_text:
            if "TODO" not in author and author and author != "TODO_AUTHOR":
                new_line = re.sub(r"(^\s*(?:\*|//|/\*|)\s*Author:\s*).*$", rf"\g<1>{author}", target_line_text)
                if not new_line.endswith("\n"):
                    new_line += "\n"
                if new_line != target_line_text:
                    return FixProposal(
                        rule_id="ND-001",
                        file=violation["file"],
                        line=viol_line,
                        description=f"Update Author email in file header",
                        patch_lines=[new_line],
                        replace_range=(viol_line, viol_line),
                        is_safe=True,
                    )

        return None
