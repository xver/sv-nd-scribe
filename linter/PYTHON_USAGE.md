# Usage in Python

You can easily integrate the linter into your own Python scripts:

```python
import os
import sys

# Ensure sv-nd-scribe is in your path
sys.path.insert(0, '/path/to/sv-nd-scribe')

from linter.core.linter_registry import get_registry
from linter.core.config_manager import ConfigManager

# Load configuration (optional)
config_mgr = ConfigManager(config_file='configs/lint_config.json')
linter_config = config_mgr.get_linter_config("naturaldoc_linter")

# Get the registry and NaturalDoc linter instance
registry = get_registry()
linter = registry.get_linter("naturaldoc_linter", config=linter_config)

if not linter:
    print("Error: Linter unavailable. Check your Verible installation.")
    sys.exit(1)

# Lint a single file or a list of files
result = linter.lint_file('my_design.sv')
# result = linter.lint_files(['file1.sv', 'file2.sv'])

# 1. Print formatted text report
print(result.format_report())

# 2. Export as JSON string
print(result.format_json())

# 3. Access structured dictionary / violation objects
res_dict = result.to_dict()
print(f"Total errors: {result.error_count}, warnings: {result.warning_count}")

if result.violations:
    for v in result.violations:
        print(f"Line {v.line}: [{v.rule_id}] {v.message}")
```
