#!/usr/bin/env python3
# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

"""
SV ND Scribe - Standalone Linter Entry Point

This file is invoked directly by the VS Code extension as:
    python3 linter/linter.py <files...>

Because the filename 'linter.py' shadows the 'linter' package directory,
we cannot use 'from linter.__main__ import main'. Instead we load __main__.py
via importlib using its file path.
"""
import os
import sys
import importlib.util

# Ensure the parent directory is in sys.path so the 'linter' package is
# importable by __main__.py and all downstream modules.
_linter_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_linter_dir)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

# Load __main__.py by file path to avoid the name collision between this
# script ('linter.py') and the 'linter' package directory.
_main_path = os.path.join(_linter_dir, "__main__.py")
_spec = importlib.util.spec_from_file_location("linter.__main__", _main_path)
_main_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_main_mod)

if __name__ == "__main__":
    _main_mod.main()
