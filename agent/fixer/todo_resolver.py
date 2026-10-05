# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import re
import sys
from typing import List, Dict, Any, Optional, Tuple
from agent.fixer.file_fixer import FileFixer
from agent.llm.skill_loader import load_skill
from agent.fixer.doc_helper import analyze_process_block, analyze_assign_statement

UNRESOLVED_PLACEHOLDER_PATTERN = re.compile(
    r"(?:TODO\s*(?:\[SVND\])?:?|(?<!\w)Description\s+for\s+|Add\s+description\s+for\s+|SystemVerilog\s+\w+\s+definition\s+for\s+|(?<!\w)definition\s+for\s+)",
    re.IGNORECASE,
)
TODO_SVND_PATTERN = UNRESOLVED_PLACEHOLDER_PATTERN


class TodoResolver:
    """Resolves 'TODO [SVND]:' and placeholder descriptions in SystemVerilog files using code context or LLM."""

    def __init__(self, provider: Any = None, agent_config: Dict[str, Any] = None):
        self.provider = provider
        self.agent_config = agent_config or {}

    def resolve_file(
        self,
        filepath: str,
        target_line: Optional[int] = None,
        backup_strategy: str = "auto",
        no_backup: bool = False,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Resolve TODO [SVND]: and placeholder markers in filepath.

        Args:
            filepath: Target file path.
            target_line: 1-indexed line number. If > 0, resolves marker at or nearest to this line.
                         If None or <= 0, resolves all markers in the file.
            backup_strategy: Backup strategy ('auto', 'always', 'none').
            no_backup: If True, do not create backups.
            dry_run: If True, don't write changes to disk.

        Returns:
            Dict containing status, resolved_count, and changes.
        """
        if not os.path.isfile(filepath):
            return {"status": "error", "message": f"File not found: {filepath}", "resolved_count": 0}

        file_fixer = FileFixer(backup_strategy=backup_strategy, no_backup=no_backup)
        source_lines = file_fixer.read_file_lines(filepath)

        # Identify candidate lines containing TODO [SVND] or placeholder description
        todo_indices = []
        for i, line in enumerate(source_lines):
            if UNRESOLVED_PLACEHOLDER_PATTERN.search(line):
                todo_indices.append(i)

        if not todo_indices:
            return {"status": "clean", "message": "No unresolved placeholder markers found.", "resolved_count": 0}

        # Select which line(s) to resolve
        indices_to_resolve = []
        if target_line is not None and target_line > 0:
            target_idx = target_line - 1
            if target_idx in todo_indices:
                indices_to_resolve.append(target_idx)
            else:
                # Search within +/- 5 lines
                nearest = min(todo_indices, key=lambda idx: abs(idx - target_idx))
                if abs(nearest - target_idx) <= 5:
                    indices_to_resolve.append(nearest)
                else:
                    return {
                        "status": "not_found",
                        "message": f"No placeholder marker found near line {target_line}.",
                        "resolved_count": 0,
                    }
        else:
            indices_to_resolve = list(todo_indices)

        changes = []
        # Sort reverse so line replacements don't shift earlier indices
        for idx in sorted(indices_to_resolve, reverse=True):
            orig_line = source_lines[idx]
            new_line, desc = self._resolve_single_line(source_lines, idx)
            if new_line != orig_line:
                source_lines[idx] = new_line
                changes.append({
                    "line": idx + 1,
                    "original": orig_line.strip(),
                    "resolved": new_line.strip(),
                    "description": desc,
                })

        if not changes:
            return {"status": "no_changes", "resolved_count": 0, "changes": []}

        if not dry_run:
            file_fixer.handle_backup(filepath)
            file_fixer.write_file_atomic(filepath, source_lines)

        return {
            "status": "success",
            "resolved_count": len(changes),
            "changes": changes,
            "dry_run": dry_run,
        }

    def _resolve_single_line(self, source_lines: List[str], idx: int) -> Tuple[str, str]:
        """Infer and generate replacement for a single line containing a placeholder marker."""
        line = source_lines[idx]
        indent = line[: len(line) - len(line.lstrip())]

        # 1. Parse kind and identifier from marker or surrounding lines
        kind = "element"
        name = "item"

        m = re.search(r"Add\s+description\s+for\s+(\w+)\s+'([^']+)'", line, re.IGNORECASE)
        if m:
            kind = m.group(1).lower()
            name = m.group(2)
        else:
            m2 = re.search(r"(?:description|definition)\s+for\s+(?:(\w+)\s+'([^']+)'|(\w+))", line, re.IGNORECASE)
            if m2:
                if m2.group(1) and m2.group(2):
                    kind = m2.group(1).lower()
                    name = m2.group(2)
                elif m2.group(3):
                    name = m2.group(3)

        # Check preceding lines (up to 3 lines above) for NaturalDocs keyword
        # Handles single-line (// Keyword:) and block comments (/* Keyword:, * Keyword:, Keyword:)
        for prev_idx in range(max(0, idx - 3), idx):
            km = re.search(
                r"(?:(?://|/\*|\*)\s*|^\s*)(Package|Class|Function|Task|Interface|Module|Define|Enum|Type|Variable|Modport|Clocking|Constraint|Property|Covergroup|Coverpoint|Process|Assign):\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
                source_lines[prev_idx],
                re.IGNORECASE,
            )
            if km:
                kind = km.group(1).lower()
                name = km.group(2)
                break

        # 2. Extract next code line
        next_code_line = ""
        proc_code_idx = idx + 1
        for ci in range(idx + 1, min(len(source_lines), idx + 12)):
            c_stripped = source_lines[ci].strip()
            if c_stripped and not c_stripped.startswith("//") and not c_stripped.startswith("/*") and not c_stripped.startswith("*"):
                next_code_line = c_stripped
                proc_code_idx = ci
                break

        # Infer kind from next code line if kind is still generic
        if kind in ("element", "item", "") and next_code_line:
            kw_m = re.search(r"\b(interface|class|module|package|function|task|covergroup|property)\b", next_code_line, re.IGNORECASE)
            if kw_m:
                kind = kw_m.group(1).lower()

        # Deep inspection for processes
        is_process = kind == "process" or (
            next_code_line and re.search(r"\b(initial|always|always_ff|always_comb|always_latch|final)\b", next_code_line)
        )
        if is_process:
            p_name, p_desc = analyze_process_block(source_lines, proc_code_idx)
            # If preceding line was `// Process: item`, fix it to `// Process: {p_name}`
            for prev_idx in range(max(0, idx - 3), idx):
                if re.search(r"//\s*Process:\s*item\b", source_lines[prev_idx], re.I):
                    p_indent = source_lines[prev_idx][: len(source_lines[prev_idx]) - len(source_lines[prev_idx].lstrip())]
                    source_lines[prev_idx] = f"{p_indent}// Process: {p_name}\n"
                    break
            return self._format_replacement(line, p_desc, indent), p_desc

        # Deep inspection for continuous assignments
        is_assign = kind in ("assignment", "assign") or (
            next_code_line and re.search(r"^\s*assign\b", next_code_line)
        )
        if is_assign:
            a_name, a_desc = analyze_assign_statement(source_lines, proc_code_idx)
            # If preceding line was `// Assign: tb_if` or `// Assign: item` and we have a more specific target, fix it
            for prev_idx in range(max(0, idx - 3), idx):
                prev_line = source_lines[prev_idx]
                if re.search(r"//\s*Assign:\s*(?:item|tb_if)\b", prev_line, re.I):
                    a_indent = prev_line[: len(prev_line) - len(prev_line.lstrip())]
                    source_lines[prev_idx] = f"{a_indent}// Assign: {a_name}\n"
                    break
            return self._format_replacement(line, a_desc, indent), a_desc

        # Fallback to extract real identifier from code line if name is still generic
        if name in ("item", "element", "") and next_code_line:
            id_m = re.search(r"\b(?:interface|class|module|package|function|task)\s+(?:void\s+|[\w:\[\]]+\s+)?([a-zA-Z_][a-zA-Z0-9_]*)", next_code_line, re.IGNORECASE)
            if id_m:
                name = id_m.group(1)
            else:
                id_m2 = re.search(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:;|=|\(|\[)", next_code_line)
                if id_m2:
                    cand = id_m2.group(1)
                    if cand not in ("function", "task", "class", "module", "interface", "rand", "int", "bit", "logic"):
                        name = cand

        # 3. Attempt LLM generation if provider is active
        if self.provider and getattr(self.provider, "is_available", False) and getattr(self.provider, "name", "none") != "none":
            try:
                system_prompt = load_skill("nd_comment", __file__)
                start_idx = max(0, idx - 10)
                end_idx = min(len(source_lines), idx + 20)
                context = "".join(source_lines[start_idx:end_idx])
                prompt = (
                    f"Given the following SystemVerilog context:\n```systemverilog\n{context}\n```\n"
                    f"Resolve the placeholder at line {idx + 1}: `{line.strip()}`.\n"
                    f"Generate a concise, professional 1-line description for {kind} '{name}'.\n"
                    f"CRITICAL RULE: Generic placeholders such as 'Description for ...' or 'TODO' are strictly UNACCEPTABLE. "
                    f"Output a true, informative description based on the SystemVerilog/UVM context.\n"
                    f"Output ONLY the description text without any markdown or formatting."
                )
                resp = self.provider.complete(prompt=prompt, system=system_prompt)
                if resp and resp.strip():
                    raw = resp.strip().splitlines()[0].strip()
                    clean_desc = re.sub(r"^(?://|/\*|\*)\s*", "", raw).rstrip("*/").strip()
                    if clean_desc and not re.match(r"^(?:TODO|description\s+for)\b", clean_desc, re.I):
                        return self._format_replacement(line, clean_desc, indent), clean_desc
            except Exception:
                pass

        # 4. Context-aware deterministic synthesis using agent knowledge
        desc = self._infer_deterministic_description(kind, name, next_code_line)
        return self._format_replacement(line, desc, indent), desc

    def _infer_deterministic_description(self, kind: str, name: str, next_code_line: str) -> str:
        clean_name = re.sub(r"^[mp]_", "", name)
        clean_words = clean_name.replace("_", " ")

        if kind == "variable":
            code_lower = next_code_line.lower()
            if "config" in code_lower or "cfg" in code_lower:
                return f"Configuration object for {clean_words}."
            elif "agent" in code_lower:
                return f"Instance of {clean_words} agent."
            elif "virtual" in code_lower or "vif" in code_lower:
                return f"Virtual interface handle for {clean_words}."
            elif "driver" in code_lower:
                return f"Driver component handle for {clean_words}."
            elif "monitor" in code_lower:
                return f"Monitor component handle for {clean_words}."
            elif "sequencer" in code_lower:
                return f"Sequencer component handle for {clean_words}."
            elif "coverage" in code_lower or "cov" in code_lower:
                return f"Coverage collector handle for {clean_words}."
            elif "scoreboard" in code_lower or "sb" in code_lower:
                return f"Scoreboard component handle for {clean_words}."
            elif any(t in next_code_line for t in ["bit", "logic", "int", "byte"]):
                return f"Control field or status flag for {clean_words}."
            else:
                parts = next_code_line.split(";")
                tokens = parts[0].replace("rand", "").split()
                if len(tokens) >= 2:
                    type_name = tokens[-2]
                    return f"Handle for {clean_words} of type {type_name}."
                return f"Verification member variable {clean_words}."

        elif kind in ("function", "task"):
            if name == "new":
                return f"Constructor creates and initializes {clean_words}."
            elif name == "build_phase":
                return "UVM build phase: constructs child components and retrieves configuration objects."
            elif name == "connect_phase":
                return "UVM connect phase: establishes connections between components."
            elif name == "end_of_elaboration_phase":
                return "UVM end of elaboration phase: prints topology and verifies configuration."
            elif name == "start_of_simulation_phase":
                return "UVM start of simulation phase: prepares stimulus generators."
            elif name == "run_phase":
                return "UVM run phase: executes main verification operations."
            elif name == "body":
                return "Main execution body for sequence stimulus."
            elif name.startswith("get_"):
                return f"Retrieves {clean_words[4:]}."
            elif name.startswith("set_"):
                return f"Configures {clean_words[4:]}."
            else:
                return f"Executes {clean_words} {kind} operation."

        elif kind == "class":
            n_lower = name.lower()
            if "test" in n_lower:
                return f"UVM test case for {clean_words}."
            elif "env" in n_lower:
                return f"UVM environment encapsulating verification components for {clean_words}."
            elif "vseq" in n_lower or "seq" in n_lower:
                return f"Sequence generating verification stimulus for {clean_words}."
            elif "cfg" in n_lower or "config" in n_lower:
                return f"Configuration object for {clean_words}."
            elif "driver" in n_lower:
                return f"UVM driver converting sequence items to pin-level signals."
            elif "monitor" in n_lower:
                return f"UVM monitor capturing interface activity."
            elif "agent" in n_lower:
                return f"UVM agent grouping driver, monitor, and sequencer for {clean_words}."
            else:
                return f"Class definition providing {clean_words} verification functionality."

        elif kind == "constraint":
            return f"Randomization constraint governing {clean_words} parameters."

        elif kind == "package":
            return f"Project package grouping definitions and components for {clean_words}."

        elif kind == "interface":
            n_lower = name.lower()
            if "link" in n_lower:
                return f"Link interface connecting testbench components and routing signals for {clean_words}."
            elif any(k in n_lower for k in ("container", "top_if", "tb_if", "template_if", "top_tb")) or (
                clean_name.endswith("_if") and ("tb" in n_lower or "top" in n_lower)
            ):
                return "Top-level project interface container bundling abstract agent pin and link interfaces."
            elif "agent" in n_lower:
                return f"Pin-level interface encapsulating physical protocol signals for {clean_words}."
            else:
                return f"Interface encapsulating signals and protocols for {clean_words}."

        elif kind == "module":
            return f"Hardware module implementation for {clean_words}."

        elif kind in ("enum", "type"):
            return f"Type definition representing {clean_words}."

        elif kind in ("covergroup", "coverpoint"):
            return f"Functional coverage metric tracking {clean_words}."

        elif kind == "property":
            return f"Assertion property verifying {clean_words} behavior."

        elif kind == "process":
            return "Process executing verification initialization and control logic."

        elif kind in ("assignment", "assign"):
            if "ready" in clean_name.lower():
                return f"Ties the {clean_words} ready handshake signal permanently high, indicating responder is always ready to receive transactions."
            elif "valid" in clean_name.lower():
                return f"Permanently asserts the {clean_words} valid signal high, indicating continuous data availability."
            elif "data" in clean_name.lower():
                return f"Mirrors captured transfer data onto {clean_words} bus for downstream observation."
            return f"Continuously drives {clean_words} according to interface dataflow."

        if clean_words.lower() in ("item", "element", ""):
            if kind == "process":
                return "Process executing verification initialization and control logic."
            elif kind == "constraint":
                return "Randomization constraint defining valid verification configurations."
            elif kind == "class":
                return "Verification component providing specialized testbench functionality."
            elif kind == "variable":
                return "Internal verification member variable."
            elif kind in ("function", "task"):
                return "Subroutine executing verification operations."
            else:
                return f"Verification {kind} providing testbench functionality."

        # Non-tautological fallback (NEVER use 'SystemVerilog <kind> definition for...')
        if kind in ("function", "task"):
            return f"Verification routine executing {clean_words} operations."
        elif kind == "class":
            return f"Verification component providing {clean_words} functionality."
        elif kind == "interface":
            return f"Interface encapsulating signals and protocol handshakes for {clean_words}."
        elif kind == "package":
            return f"Package grouping verification definitions and utilities for {clean_words}."
        elif kind == "module":
            return f"Hardware module implementing {clean_words} logic."
        elif kind == "variable":
            return f"Internal verification member tracking {clean_words} state."
        else:
            return f"Verification construct providing {clean_words} functionality."

    def _format_replacement(self, orig_line: str, desc: str, indent: str) -> str:
        stripped = orig_line.strip()
        # Handle inline comment: e.g. IDLE, /// TODO [SVND]: description for IDLE
        if "///" in orig_line:
            return re.sub(r"///\s*(?:TODO(?:\s*\[SVND\])?:?|description\s+for|SystemVerilog\s+\w+\s+definition\s+for|definition\s+for).*$", f"/// {desc}\n", orig_line, flags=re.I)
        if "//" in orig_line and not stripped.startswith("//"):
            return re.sub(r"//\s*(?:TODO(?:\s*\[SVND\])?:?|description\s+for|SystemVerilog\s+\w+\s+definition\s+for|definition\s+for).*$", f"// {desc}\n", orig_line, flags=re.I)

        # Standard dedicated NaturalDocs comment line
        # If line length exceeds 80 characters, wrap into multi-line comments below 80 characters
        import textwrap
        if stripped.startswith("//"):
            prefix = f"{indent}//   "
        elif stripped.startswith("*"):
            prefix = f"{indent}* "
        else:
            prefix = f"{indent}"

        full_line = f"{prefix}{desc}\n"
        if len(full_line) > 80:
            max_w = max(40, 78 - len(prefix))
            wrapped = textwrap.wrap(desc, width=max_w)
            if wrapped:
                return "".join(f"{prefix}{w}\n" for w in wrapped)
        return full_line
