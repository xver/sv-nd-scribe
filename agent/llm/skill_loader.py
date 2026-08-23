# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

import os

def load_skill(skill_name: str, fallback_file: str = __file__, include_references: bool = False) -> str:
    """
    Load a SKILL.md file and return its content as a system prompt string.
    
    Args:
        skill_name:          Skill directory name (e.g. 'nd_comment', 'function_task')
        fallback_file:       File path to resolve project/agent root from if SVND_SCRIBE_HOME is unset
        include_references:  If True, also append content from references/ subdir files
    Returns:
        Full skill content string, or empty string if skill not found.
    """
    root = _resolve_root(fallback_file)
    
    # Try <root>/skills/<name>/SKILL.md then <root>/agent/skills/<name>/SKILL.md
    skill_path = os.path.join(root, "skills", skill_name, "SKILL.md")
    if not os.path.exists(skill_path):
        skill_path = os.path.join(root, "agent", "skills", skill_name, "SKILL.md")
        
    content = ""
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    
    if include_references and os.path.exists(skill_path):
        ref_dir = os.path.join(os.path.dirname(skill_path), "references")
        if os.path.isdir(ref_dir):
            for fname in sorted(os.listdir(ref_dir)):
                ref_path = os.path.join(ref_dir, fname)
                if os.path.isfile(ref_path):
                    with open(ref_path, "r", encoding="utf-8") as f:
                        content += f"\n\n---\n{f.read()}"
    
    return content


def _resolve_root(fallback_file: str) -> str:
    if "SVND_SCRIBE_HOME" in os.environ and os.path.exists(os.environ["SVND_SCRIBE_HOME"]):
        return os.environ["SVND_SCRIBE_HOME"]
    path = os.path.abspath(fallback_file)
    for _ in range(6):
        path = os.path.dirname(path)
        if os.path.exists(os.path.join(path, "plugin.json")):
            return path
    return os.path.dirname(os.path.abspath(fallback_file))
