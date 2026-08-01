# SV ND Scribe - VS Code Extension ![](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)

![sv-nd-scribe Logo](scribe_logo.jpg)

Real-time SystemVerilog in-editor diagnostic feedback utilizing the **SV ND Scribe** static linter rules.

## Features

- Highlights NaturalDocs documentation violations (`[WKL-007]`).
- Highlights trailing whitespace (`[WKL-006]`), multiple trailing newlines (`[WKL-005]`), and other syntax formatting issues in real-time.
- Supports customizable linter configuration.

## Requirements

1. **Python 3**
2. **Verible** - specifically `verible-verilog-syntax` installed in your PATH.
3. The standalone `sv-nd-scribe` linter package downloaded to your machine.

## Configuration

You can configure this extension via VS Code Settings:

* `sv-nd-scribe.linterPath`: Absolute path to `linter.py`. If left blank, it automatically falls back to `$SVND_SCRIBE_HOME/linter/linter.py` (Default: `""`).
* `sv-nd-scribe.pythonPath`: Path to the python interpreter (Default: `python3`).
* `sv-nd-scribe.runOn`: Trigger execution on save (`onSave`) or when opening documents (`onOpen`).

## Commands

Use the VS Code Command Palette (`Ctrl+Shift+P`) to run:

- **`SV_Scribe: Lint`**: Manually lint the active file.
- **`SV_Scribe: Clear`**: Clear diagnostic outlines.
- **`SV_Scribe: Lint_All`**: Lint all open SystemVerilog documents.
- **`SV_Scribe: Status`** (alias: **`SV_Scribe: Verify linter installation`**): Check environment health and dependencies.

## Installation

Install the packaged `.vsix` file using the VS Code CLI or Extensions panel:

```bash
code --install-extension sv-nd-scribe-vscode-*.vsix
```

---

![img](https://raw.githubusercontent.com/xver/icecream_sv/main/doc/IcVerimeter_logo.png) [![img](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/xver)
Copyright (c) 2026 IC Verimeter
