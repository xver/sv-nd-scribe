# Copyright (c) 2026 IC Verimeter. All rights reserved.
import os
import re
from datetime import date
from typing import List, Dict, Any, Optional
from agent.fixer.base_fixer import BaseFixer, FixProposal


class FixNd001(BaseFixer):
    """Insert or replace file header comment block using header_defaults or custom header_template.sv."""

    def propose(
        self,
        violation: Dict[str, Any],
        source_lines: List[str],
        config: Dict[str, Any] = None, **kwargs,
    ) -> Optional[FixProposal]:
        agent_cfg = (config or {}).get("agent", config or {})
        cfg = agent_cfg.get("header_defaults", {})
        filename = os.path.basename(violation["file"])
        company = cfg.get("company", agent_cfg.get("header_company", "TODO_COMPANY"))
        author = cfg.get("author", agent_cfg.get("header_author", "TODO_AUTHOR"))
        legal = cfg.get("legal", agent_cfg.get("header_legal", "TODO_LEGAL"))

        msg = violation.get("message", "")

        # If the violation is specifically about an unresolved placeholder (TODO_COMPANY, TODO_AUTHOR, TODO_LEGAL)
        # and the user's config has not provided a real non-TODO value, do NOT propose a redundant/duplicate fix.
        if "contains unresolved placeholder" in msg:
            if "TODO_COMPANY" in msg and ("TODO" in company):
                return None
            if "TODO_AUTHOR" in msg and ("TODO" in author):
                return None
            if "TODO_LEGAL" in msg and ("TODO" in legal):
                return None

        today = date.today()
        try:
            date_str = today.strftime("%B %-d, %Y")
        except ValueError:
            date_str = today.strftime("%B %#d, %Y")

        custom_tmpl = agent_cfg.get("custom_header_template") or agent_cfg.get("header_template")
        
        # Auto-detect template file candidates in workspace/project root if not in config
        if not custom_tmpl:
            candidates = ["header_template.sv", ".sv_header_template.sv", "template/header_template.sv"]
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

        if custom_tmpl:
            tmpl_text = custom_tmpl
            if os.path.exists(custom_tmpl):
                try:
                    with open(custom_tmpl, "r", encoding="utf-8") as tf:
                        tmpl_text = tf.read()
                except Exception:
                    pass
            
            tmpl_text = tmpl_text.replace("${filename}", filename).replace("{{filename}}", filename)
            tmpl_text = tmpl_text.replace("${company}", company).replace("{{company}}", company)
            tmpl_text = tmpl_text.replace("${author}", author).replace("{{author}}", author)
            tmpl_text = tmpl_text.replace("${date}", date_str).replace("{{date}}", date_str)
            tmpl_text = tmpl_text.replace("${year}", str(today.year)).replace("{{year}}", str(today.year))
            tmpl_text = tmpl_text.replace("${legal}", legal).replace("{{legal}}", legal)

            header_block = [line + "\n" for line in tmpl_text.splitlines()]
            if not header_block:
                header_block = ["/* Custom Header */\n"]
        else:
            # Search for existing header in top 100 lines to preserve Created & Description
            start_idx = -1
            end_idx = -1
            for idx, l_str in enumerate(source_lines[:100]):
                stripped = l_str.strip()
                if start_idx == -1:
                    if stripped.startswith("/*"):
                        start_idx = idx
                        if "*/" in stripped[2:]:
                            end_idx = idx
                            break
                else:
                    if "*/" in stripped:
                        end_idx = idx
                        break

            created_val = f"{date_str} ({author})"
            updated_val = f"{date_str} ({author})"
            desc_text = f"Description: SystemVerilog component — {filename}"

            if start_idx != -1 and end_idx != -1:
                orig_text = "".join(source_lines[start_idx:end_idx + 1])
                c_m = re.search(r"^\s*\*\s*Created:\s*(.*)", orig_text, re.MULTILINE)
                if c_m and "TODO" not in c_m.group(1):
                    created_val = c_m.group(1).strip()

                d_m = re.search(r"^\s*\*\s*Description:\s*(.*)", orig_text, re.MULTILINE)
                if d_m and "TODO" not in d_m.group(1):
                    desc_text = f"Description: {d_m.group(1).strip()}"

            header_block = [
                "/******************************************************************************\n",
                f" * File:        {filename}\n",
                " *\n",
                f" * Company:     {company}\n",
                " *\n",
                f" * Author:      {author}\n",
                " *\n",
                f" * {desc_text}\n",
                " *\n",
                f" * Created:     {created_val}\n",
                " *\n",
                f" * Updated:     {updated_val}\n",
                " *\n",
                f" * Copyright (c) {today.year} {company}\n",
                f" * {legal}\n",
                " ******************************************************************************/\n",
            ]
        
        # Determine replace_range or insertion
        start_idx = -1
        end_idx = -1
        for idx, l_str in enumerate(source_lines[:100]):
            stripped = l_str.strip()
            if start_idx == -1:
                if stripped.startswith("/*"):
                    start_idx = idx
                    if "*/" in stripped[2:]:
                        end_idx = idx
                        break
            else:
                if "*/" in stripped:
                    end_idx = idx
                    break

        if start_idx != -1:
            if end_idx == -1:
                end_idx = min(start_idx + len(header_block) - 1, len(source_lines) - 1)

            orig_lines = source_lines[start_idx:end_idx + 1]
            orig_text = "".join(orig_lines)
            new_text = "".join(header_block)

            if orig_text.strip() == new_text.strip():
                return None

            return FixProposal(
                rule_id="ND-001",
                file=violation["file"],
                line=start_idx + 1,
                description="Replace file header comment block",
                patch_lines=header_block,
                replace_range=(start_idx + 1, end_idx + 1),
                is_safe=True,
            )

        # If no block comment was found but the violation is NOT 'Missing block comment...',
        # do not insert a duplicate header.
        if "Missing block comment file header" not in msg and "File header" in msg:
            return None

        return FixProposal(
            rule_id="ND-001",
            file=violation["file"],
            line=1,
            description="Insert file header comment block",
            patch_lines=header_block,
            replace_line=None,
            is_safe=True,
        )
