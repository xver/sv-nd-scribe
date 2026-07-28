# Copyright (c) 2026 IC Verimeter. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for details.

#!/usr/bin/env python3
"""
SV ND Scribe - Standalone Linter Entry Point
"""
import os
import sys

# Ensure the parent directory is in sys.path so we can import 'linter' package
_linter_dir = os.path.dirname(os.path.abspath(__file__))
_project_dir = os.path.dirname(_linter_dir)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from linter.__main__ import main

if __name__ == "__main__":
    main()
