# SV ND Scribe - VS Code Extension ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

Real-time SystemVerilog in-editor diagnostic feedback utilizing the **SV ND Scribe** static linter rules.

## Features

- Real-time diagnostics for NaturalDocs documentation and SystemVerilog style guidelines.
- **Quick Fix (`Ctrl+.` / `Cmd+.` / 💡)**: Apply automated fixes directly from inline error and warning markers.
- **Batch Auto-Fix**: Automatically fix all safe issues across the current file in one click (`SV_Scribe: Fix all auto-fixable issues in file`).
- Highlights trailing whitespace (`[WKL-006]`), multiple trailing newlines (`[WKL-005]`), missing headers (`[ND-001]`), include guards (`[ND-002]`), and construct doc blocks.
- Supports customizable linter and agent configuration.

## Requirements

1. **Python 3**
2. **Verible** - specifically `verible-verilog-syntax` installed in your PATH.
3. The standalone `sv-nd-scribe` linter & agent package downloaded to your machine.

## Configuration

You can configure this extension via VS Code Settings:

* `sv-nd-scribe.linterPath`: Absolute path to `linter.py`. If left blank, it automatically falls back to `$SVND_SCRIBE_HOME/linter/linter.py` (Default: `""`).
* `sv-nd-scribe.agentPath`: Absolute path to the `agent` module or `agent.py`. If left blank, it automatically falls back to `$SVND_SCRIBE_HOME/agent` (Default: `""`).
* `sv-nd-scribe.pythonPath`: Path to the python interpreter (Default: `python3`).
* `sv-nd-scribe.enableQuickFix`: Enable or disable Quick Fix (Code Action) suggestions (Default: `true`).
* `sv-nd-scribe.runOn`: Trigger execution on save (`onSave`) or when opening documents (`onOpen`).

## Commands

Use the VS Code Command Palette (`Ctrl+Shift+P`) to run:

- **`SV_Scribe: Fix all auto-fixable issues in file`**: Run batch fixer on active file.
- **`SV_Scribe: Fix specific rule in file`**: Fix a specific rule violation in the active file.
- **`SV_Scribe: Lint`**: Manually lint the active file.
- **`SV_Scribe: Clear`**: Clear diagnostic outlines.
- **`SV_Scribe: Lint_All`**: Lint all open SystemVerilog documents.
- **`SV_Scribe: Status`** (alias: **`SV_Scribe: Verify linter installation`**): Check environment health and dependencies.

## Installation

Install the packaged `.vsix` file using the VS Code CLI or Extensions panel:

```bash
code --install-extension sv-nd-scribe-vscode-*.vsix
```

## Support

For assistance with integration or customization, contact us at [icshunt.help@gmail.com](mailto:icshunt.help@gmail.com).

Report bugs to [Issues](https://github.com/xver/sv-nd-scribe/issues).

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
