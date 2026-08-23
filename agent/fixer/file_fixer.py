# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple
from .base_fixer import FixProposal

class FileFixer:
    """Handles safe in-memory line buffer mutation, atomic disk writes, and backup strategy."""

    # Class-level cache for git root lookups (shared across instances within one process)
    _git_root_cache: Dict[str, Optional[str]] = {}

    def __init__(self, backup_strategy: str = "auto", no_backup: bool = False):
        """
        Args:
            backup_strategy: 'auto', 'always', or 'never'
            no_backup: If True, forces backup_strategy = 'never'
        """
        if no_backup:
            self.backup_strategy = "never"
        else:
            self.backup_strategy = backup_strategy

    def read_file_lines(self, filepath: str) -> List[str]:
        """Read text file and return list of lines with newline characters preserved."""
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()

    def apply_proposals_in_memory(self, lines: List[str], proposals: List[FixProposal]) -> List[str]:
        """
        Apply proposals to in-memory line array.
        Supports three modes per proposal:
          - replace_range set: delete lines [start..end] and insert patch_lines
          - replace_line set: replace a single line at p.line with patch_lines
          - neither set: insert patch_lines before p.line
        Precondition: Proposals are sorted internally (descending by effective end line).
        """
        modified_lines = list(lines)
        
        rule_priority_map = {
            "ND-001": 1,
            "ND-002": 2,
            "ND-008": 3,
            "ND-009": 3,
            "ND-010": 3,
            "ND-013": 3,
            "ND-014": 3,
            "ND-017": 3,
            "ND-004": 4,
            "ND-012": 4,
        }

        def sort_key(p):
            # Use the highest affected line for sorting (descending).
            # For replace_range, use the end line; otherwise use p.line.
            if p.replace_range:
                effective_line = p.replace_range[1]
            else:
                effective_line = p.line
            return (effective_line, rule_priority_map.get(p.rule_id, 5))

        # Sort proposals descending by effective line, using rule priority for tie-breaking
        sorted_proposals = sorted(proposals, key=sort_key, reverse=True)

        for p in sorted_proposals:
            if p.replace_range is not None:
                # Multi-line replacement: delete lines [start..end] and insert patch_lines
                start_idx = p.replace_range[0] - 1  # 1-indexed to 0-indexed
                end_idx = p.replace_range[1]         # 1-indexed end, exclusive in slice
                if start_idx < 0:
                    start_idx = 0
                if end_idx > len(modified_lines):
                    end_idx = len(modified_lines)

                # Build replacement block with proper newlines
                replacement = []
                for entry in p.patch_lines:
                    if not entry.endswith("\n"):
                        entry += "\n"
                    replacement.append(entry)

                modified_lines[start_idx:end_idx] = replacement

            elif p.replace_line is not None:
                # Single-line replacement of target line
                line_idx = p.line - 1  # 1-indexed to 0-indexed
                if line_idx < 0 or line_idx >= len(modified_lines):
                    continue
                replacement_text = "".join(p.patch_lines)
                if not replacement_text.endswith("\n"):
                    replacement_text += "\n"
                modified_lines[line_idx] = replacement_text

            else:
                # Insertion immediately before violation line
                line_idx = p.line - 1  # 1-indexed to 0-indexed
                if line_idx < 0 or line_idx > len(modified_lines):
                    continue
                insertion_text = []
                for entry in p.patch_lines:
                    if not entry.endswith("\n"):
                        entry += "\n"
                    insertion_text.append(entry)
                modified_lines[line_idx:line_idx] = insertion_text
                
        return modified_lines

    def handle_backup(self, filepath: str) -> bool:
        """
        Perform backup according to Tier 1 / 2 / 3 rules.
        Returns True if a .bak file was created, False otherwise.
        """
        if self.backup_strategy == "never":
            return False

        if self.backup_strategy == "always":
            self._create_bak_copy(filepath)
            return True

        # strategy == 'auto'
        if self._is_clean_git_repo(filepath):
            # Tier 1: Git repo clean, no .bak file needed
            return False
        else:
            # Tier 2: Write .bak file
            self._create_bak_copy(filepath)
            return True

    def write_file_atomic(self, filepath: str, lines: List[str]) -> None:
        """
        Atomically write lines to filepath via a sibling temporary file (<filepath>.tmp).
        Uses try...finally to ensure temporary file cleanup on any interrupt or error.
        """
        tmp_filepath = f"{filepath}.tmp"
        try:
            with open(tmp_filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
            os.replace(tmp_filepath, filepath)
        finally:
            if os.path.exists(tmp_filepath):
                try:
                    os.remove(tmp_filepath)
                except OSError:
                    pass

    def _create_bak_copy(self, filepath: str) -> None:
        bak_filepath = f"{filepath}.bak"
        shutil.copy2(filepath, bak_filepath)

    def _get_git_root(self, dir_path: str) -> Optional[str]:
        """Get the git repository root for a directory, using a class-level cache."""
        if dir_path in FileFixer._git_root_cache:
            return FileFixer._git_root_cache[dir_path]

        try:
            # Check if in git repo
            git_dir = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=dir_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if git_dir.returncode != 0 or git_dir.stdout.strip() != "true":
                FileFixer._git_root_cache[dir_path] = None
                return None

            # Get git root
            git_root_result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=dir_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            root = git_root_result.stdout.strip() if git_root_result.returncode == 0 else None
            FileFixer._git_root_cache[dir_path] = root
            return root
        except Exception:
            FileFixer._git_root_cache[dir_path] = None
            return None

    def _is_clean_git_repo(self, filepath: str) -> bool:
        """Check if file is inside a git repository with no unstaged changes."""
        dir_path = os.path.dirname(os.path.abspath(filepath))
        git_root = self._get_git_root(dir_path)
        if not git_root:
            return False

        try:
            rel_path = os.path.relpath(os.path.abspath(filepath), git_root)

            # Check status of specific file using its repo-relative path
            git_status = subprocess.run(
                ["git", "status", "--porcelain", rel_path],
                cwd=git_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if git_status.returncode == 0 and git_status.stdout.strip() == "":
                return True
        except Exception:
            pass
        return False
